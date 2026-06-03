#!/usr/bin/env python3
"""Minimal API E2E smoke test for the strict learning flow.

Runs against a live server (default http://127.0.0.1:8000) and validates
the main state-machine path through HTTP + SSE without a browser.

Coverage:
  1. POST /api/sessions          — create session placeholder
  2. POST /api/start             — start with a topic
  3. GET  /api/stream            — consume SSE until session.end
  4. POST /api/confirm_topic     — confirm the proposed topic
  5. POST /api/assessment_answer — answer assessment questions one by one
  6. POST /api/answer            — submit post_lesson_choice (start_test / temporary_question)
  7. POST /api/answer            — submit objective_test_answers
  8. POST /api/answer            — submit continue_or_homework_choice
  9. POST /api/sessions/{id}/resume — test session resume
 10. Temporary question flow     — submit free-form question, get answer, return to post_lesson_choice

Usage:
  python scripts/smoke_strict_learning_flow.py --base-url http://127.0.0.1:8000

Requirements:
  - Server must be running with LLM configured
  - pip install httpx sseclient-py  (or use built-in SSE parsing)
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from typing import Any, Dict, List, Optional

try:
    import httpx
except ImportError:
    print("ERROR: httpx is required. Install with: pip install httpx")
    sys.exit(1)


# ── SSE event parser (no external dependency) ──────────────────────────────
class SSEEvent:
    """Parsed server-sent event."""

    def __init__(self, event_type: str, data: str):
        self.type = event_type
        self.data = data
        self.parsed: Optional[Dict[str, Any]] = None
        try:
            self.parsed = json.loads(data)
        except (json.JSONDecodeError, TypeError):
            pass

    def __repr__(self) -> str:
        return f"SSEEvent(type={self.type!r}, data_len={len(self.data)})"


def parse_sse_stream(text: str) -> List[SSEEvent]:
    """Parse raw SSE text into a list of SSEEvent objects."""
    events: List[SSEEvent] = []
    current_event = ""
    current_data = ""
    for line in text.split("\n"):
        if line.startswith("event: "):
            current_event = line[7:].strip()
        elif line.startswith("data: "):
            current_data = line[6:].strip()
        elif line == "" and current_event:
            events.append(SSEEvent(current_event, current_data))
            current_event = ""
            current_data = ""
    # Flush last event if stream ended without trailing blank line
    if current_event:
        events.append(SSEEvent(current_event, current_data))
    return events


# ── Smoke test runner ──────────────────────────────────────────────────────
class SmokeRunner:
    """Orchestrates a single end-to-end learning flow through the API."""

    def __init__(self, base_url: str, timeout: float = 120.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.thread_id = f"smoke-{uuid.uuid4().hex[:8]}"
        self.client = httpx.Client(base_url=self.base_url, timeout=timeout)
        self.steps_passed = 0
        self.steps_failed = 0
        self.errors: List[str] = []

    def close(self):
        self.client.close()

    # ── helpers ────────────────────────────────────────────────────────────
    def _log(self, step: str, status: str, detail: str = ""):
        icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "ℹ️"
        msg = f"  {icon} [{step}] {status}"
        if detail:
            msg += f" — {detail}"
        print(msg)

    def _record_pass(self, step: str, detail: str = ""):
        self.steps_passed += 1
        self._log(step, "PASS", detail)

    def _record_fail(self, step: str, detail: str = ""):
        self.steps_failed += 1
        self.errors.append(f"{step}: {detail}")
        self._log(step, "FAIL", detail)

    def _post(self, path: str, data: dict) -> httpx.Response:
        resp = self.client.post(path, json=data)
        return resp

    def _consume_sse(self, thread_id: str, timeout: float = 60.0) -> List[SSEEvent]:
        """Consume SSE stream until session.end or timeout."""
        import queue
        import threading

        events: List[SSEEvent] = []
        url = f"{self.base_url}/api/stream?thread_id={thread_id}"

        # Use streaming request
        with httpx.stream("GET", url, timeout=timeout) as response:
            buffer = ""
            for chunk in response.iter_text():
                buffer += chunk
                while "\n\n" in buffer:
                    raw_event, buffer = buffer.split("\n\n", 1)
                    event = self._parse_single_sse(raw_event)
                    if event:
                        events.append(event)
                        if event.type == "session.end":
                            return events
        return events

    def _parse_single_sse(self, raw: str) -> Optional[SSEEvent]:
        """Parse a single SSE block."""
        event_type = ""
        data = ""
        for line in raw.split("\n"):
            if line.startswith("event: "):
                event_type = line[7:].strip()
            elif line.startswith("data: "):
                data = line[6:].strip()
        if event_type:
            return SSEEvent(event_type, data)
        return None

    def _wait_for_flow_status(
        self, thread_id: str, target_statuses: set, timeout: float = 60.0
    ) -> List[SSEEvent]:
        """Consume SSE until we see a session.end with matching flow_status."""
        events = self._consume_sse(thread_id, timeout=timeout)
        for evt in events:
            if evt.type == "session.end" and evt.parsed:
                data = evt.parsed.get("data", {})
                fs = data.get("flow_status", "")
                if fs in target_statuses:
                    return events
        return events

    def _collect_event_types(self, events: List[SSEEvent]) -> List[str]:
        return [e.type for e in events]

    # ── test steps ─────────────────────────────────────────────────────────
    def step_health(self) -> bool:
        """Step 0: Check server health."""
        step = "health"
        try:
            resp = self.client.get("/api/health")
            if resp.status_code == 200 and resp.json().get("status") == "ok":
                self._record_pass(step, f"thread_id={self.thread_id}")
                return True
            self._record_fail(step, f"status={resp.status_code}")
            return False
        except Exception as exc:
            self._record_fail(step, str(exc))
            return False

    def step_create_session(self) -> bool:
        """Step 1: Create session placeholder."""
        step = "create_session"
        try:
            resp = self._post("/api/sessions", {"thread_id": self.thread_id})
            data = resp.json()
            if resp.status_code == 200 and data.get("status") in ("created", "exists"):
                self._record_pass(step, f"status={data['status']}")
                return True
            self._record_fail(step, f"status={resp.status_code}, body={data}")
            return False
        except Exception as exc:
            self._record_fail(step, str(exc))
            return False

    def step_start_topic(self) -> bool:
        """Step 2: Start a learning session with a topic."""
        step = "start_topic"
        topic = "自动控制原理中的根轨迹法"
        try:
            resp = self._post("/api/start", {
                "thread_id": self.thread_id,
                "topic": topic,
            })
            data = resp.json()
            if resp.status_code == 200 and data.get("status") in ("started", "running"):
                self._record_pass(step, f"topic={topic!r}, status={data['status']}")
                return True
            self._record_fail(step, f"status={resp.status_code}, body={data}")
            return False
        except Exception as exc:
            self._record_fail(step, str(exc))
            return False

    def step_consume_initial_stream(self) -> tuple:
        """Step 3: Consume SSE until topic confirmation or assessment."""
        step = "initial_stream"
        try:
            events = self._consume_sse(self.thread_id, timeout=90.0)
            event_types = self._collect_event_types(events)

            # Look for session.end with topic confirmation or assessment
            end_events = [e for e in events if e.type == "session.end"]
            if not end_events:
                self._record_fail(step, f"No session.end event. Got: {event_types}")
                return False, events

            end_data = end_events[-1].parsed or {}
            flow_status = end_data.get("data", {}).get("flow_status", "")

            # After initial start, we expect either topic confirmation or assessment
            # The flow should be in a state waiting for user input
            has_token = any(e.type == "session.token" for e in events)
            has_info = any(e.type == "session.info" for e in events)

            self._record_pass(
                step,
                f"events={len(events)}, types={set(event_types)}, "
                f"flow_status={flow_status!r}, has_token={has_token}"
            )
            return True, events
        except Exception as exc:
            self._record_fail(step, str(exc))
            return False, []

    def step_confirm_topic(self, start_mode: str = "assessment") -> bool:
        """Step 4: Confirm the proposed topic."""
        step = "confirm_topic"
        try:
            resp = self._post("/api/confirm_topic", {
                "thread_id": self.thread_id,
                "confirmed": True,
                "start_mode": start_mode,
            })
            data = resp.json()
            if resp.status_code == 200 and data.get("status") == "ok":
                self._record_pass(step, f"start_mode={start_mode}")
                return True
            self._record_fail(step, f"status={resp.status_code}, body={data}")
            return False
        except Exception as exc:
            self._record_fail(step, str(exc))
            return False

    def step_consume_post_confirm(self) -> tuple:
        """Step 5: Consume SSE after topic confirmation."""
        step = "post_confirm_stream"
        try:
            events = self._consume_sse(self.thread_id, timeout=90.0)
            event_types = self._collect_event_types(events)
            end_events = [e for e in events if e.type == "session.end"]

            if not end_events:
                self._record_fail(step, f"No session.end. Got: {event_types}")
                return False, events

            end_data = end_events[-1].parsed or {}
            flow_status = end_data.get("data", {}).get("flow_status", "")
            self._record_pass(
                step,
                f"events={len(events)}, flow_status={flow_status!r}"
            )
            return True, events
        except Exception as exc:
            self._record_fail(step, str(exc))
            return False, []

    def step_submit_assessment_answer(self, answer: str = "A") -> bool:
        """Step 6: Submit a single assessment answer (dialog mode)."""
        step = "assessment_answer"
        try:
            resp = self._post("/api/assessment_answer", {
                "thread_id": self.thread_id,
                "answer": answer,
            })
            data = resp.json()
            if resp.status_code == 200 and data.get("status") == "ok":
                self._record_pass(step, f"answer={answer}")
                return True
            self._record_fail(step, f"status={resp.status_code}, body={data}")
            return False
        except Exception as exc:
            self._record_fail(step, str(exc))
            return False

    def step_consume_assessment_stream(self) -> tuple:
        """Step 7: Consume SSE after assessment answer."""
        step = "assessment_stream"
        try:
            events = self._consume_sse(self.thread_id, timeout=90.0)
            event_types = self._collect_event_types(events)
            end_events = [e for e in events if e.type == "session.end"]
            if not end_events:
                self._record_fail(step, f"No session.end. Got: {event_types}")
                return False, events

            end_data = end_events[-1].parsed or {}
            flow_status = end_data.get("data", {}).get("flow_status", "")
            pending_kind = end_data.get("data", {}).get("pending_interaction_kind", "")
            self._record_pass(
                step,
                f"flow_status={flow_status!r}, pending_kind={pending_kind!r}"
            )
            return True, events
        except Exception as exc:
            self._record_fail(step, str(exc))
            return False, []

    def step_submit_post_lesson_choice(self, choice: str = "start_test") -> bool:
        """Step 8: Submit post_lesson_choice (start_test or temporary_question)."""
        step = "post_lesson_choice"
        try:
            resp = self._post("/api/answer", {
                "thread_id": self.thread_id,
                "answer": choice,
            })
            data = resp.json()
            if resp.status_code == 200 and data.get("status") == "ok":
                self._record_pass(step, f"choice={choice}")
                return True
            self._record_fail(step, f"status={resp.status_code}, body={data}")
            return False
        except Exception as exc:
            self._record_fail(step, str(exc))
            return False

    def step_consume_post_lesson_stream(self) -> tuple:
        """Step 9: Consume SSE after post_lesson_choice."""
        step = "post_lesson_stream"
        try:
            events = self._consume_sse(self.thread_id, timeout=90.0)
            event_types = self._collect_event_types(events)
            end_events = [e for e in events if e.type == "session.end"]
            if not end_events:
                self._record_fail(step, f"No session.end. Got: {event_types}")
                return False, events

            end_data = end_events[-1].parsed or {}
            flow_status = end_data.get("data", {}).get("flow_status", "")
            pending_kind = end_data.get("data", {}).get("pending_interaction_kind", "")
            self._record_pass(
                step,
                f"flow_status={flow_status!r}, pending_kind={pending_kind!r}"
            )
            return True, events
        except Exception as exc:
            self._record_fail(step, str(exc))
            return False, []

    def step_submit_objective_answers(self, answers: str = "A B C D A B C D A B") -> bool:
        """Step 10: Submit objective test answers."""
        step = "objective_answers"
        try:
            resp = self._post("/api/answer", {
                "thread_id": self.thread_id,
                "answer": answers,
            })
            data = resp.json()
            if resp.status_code == 200 and data.get("status") == "ok":
                self._record_pass(step, f"answers={answers!r}")
                return True
            self._record_fail(step, f"status={resp.status_code}, body={data}")
            return False
        except Exception as exc:
            self._record_fail(step, str(exc))
            return False

    def step_consume_objective_stream(self) -> tuple:
        """Step 11: Consume SSE after objective test submission."""
        step = "objective_stream"
        try:
            events = self._consume_sse(self.thread_id, timeout=90.0)
            event_types = self._collect_event_types(events)
            end_events = [e for e in events if e.type == "session.end"]
            if not end_events:
                self._record_fail(step, f"No session.end. Got: {event_types}")
                return False, events

            end_data = end_events[-1].parsed or {}
            flow_status = end_data.get("data", {}).get("flow_status", "")
            pending_kind = end_data.get("data", {}).get("pending_interaction_kind", "")
            self._record_pass(
                step,
                f"flow_status={flow_status!r}, pending_kind={pending_kind!r}"
            )
            return True, events
        except Exception as exc:
            self._record_fail(step, str(exc))
            return False, []

    def step_submit_continue_or_homework(self, choice: str = "continue") -> bool:
        """Step 12: Submit continue_or_homework_choice."""
        step = "continue_or_homework"
        try:
            resp = self._post("/api/answer", {
                "thread_id": self.thread_id,
                "answer": choice,
            })
            data = resp.json()
            if resp.status_code == 200 and data.get("status") == "ok":
                self._record_pass(step, f"choice={choice}")
                return True
            self._record_fail(step, f"status={resp.status_code}, body={data}")
            return False
        except Exception as exc:
            self._record_fail(step, str(exc))
            return False

    def step_consume_continue_stream(self) -> tuple:
        """Step 13: Consume SSE after continue/homework choice."""
        step = "continue_stream"
        try:
            events = self._consume_sse(self.thread_id, timeout=90.0)
            event_types = self._collect_event_types(events)
            end_events = [e for e in events if e.type == "session.end"]
            if not end_events:
                self._record_fail(step, f"No session.end. Got: {event_types}")
                return False, events

            end_data = end_events[-1].parsed or {}
            flow_status = end_data.get("data", {}).get("flow_status", "")
            self._record_pass(
                step,
                f"flow_status={flow_status!r}"
            )
            return True, events
        except Exception as exc:
            self._record_fail(step, str(exc))
            return False, []

    def step_resume_session(self) -> bool:
        """Step 14: Test session resume via POST /api/sessions/{id}/resume."""
        step = "resume_session"
        try:
            resp = self._post(
                f"/api/sessions/{self.thread_id}/resume", {}
            )
            data = resp.json()
            if resp.status_code == 200 and data.get("status") in ("started", "running"):
                self._record_pass(step, f"status={data['status']}")
                return True
            self._record_fail(step, f"status={resp.status_code}, body={data}")
            return False
        except Exception as exc:
            self._record_fail(step, str(exc))
            return False

    def step_consume_resume_stream(self) -> tuple:
        """Step 15: Consume SSE after resume."""
        step = "resume_stream"
        try:
            events = self._consume_sse(self.thread_id, timeout=90.0)
            event_types = self._collect_event_types(events)
            end_events = [e for e in events if e.type == "session.end"]
            if not end_events:
                self._record_fail(step, f"No session.end. Got: {event_types}")
                return False, events

            end_data = end_events[-1].parsed or {}
            flow_status = end_data.get("data", {}).get("flow_status", "")
            self._record_pass(
                step,
                f"flow_status={flow_status!r}, events={len(events)}"
            )
            return True, events
        except Exception as exc:
            self._record_fail(step, str(exc))
            return False, []

    # ── main flow ──────────────────────────────────────────────────────────
    def run_full_flow(self) -> bool:
        """Run the complete strict learning flow smoke test."""
        print(f"\n{'='*60}")
        print(f"  AI Tutor Agent — Strict Learning Flow E2E Smoke")
        print(f"  Base URL: {self.base_url}")
        print(f"  Thread ID: {self.thread_id}")
        print(f"{'='*60}\n")

        # Step 0: Health check
        print("[Step 0] Health check")
        if not self.step_health():
            return self._finalize()

        # Step 1: Create session
        print("\n[Step 1] Create session placeholder")
        if not self.step_create_session():
            return self._finalize()

        # Step 2: Start with topic
        print("\n[Step 2] Start learning with topic")
        if not self.step_start_topic():
            return self._finalize()

        # Step 3: Consume initial stream (topic confirmation)
        print("\n[Step 3] Consume initial SSE stream")
        ok, events = self.step_consume_initial_stream()
        if not ok:
            return self._finalize()

        # Step 4: Confirm topic with assessment mode
        print("\n[Step 4] Confirm topic (assessment mode)")
        if not self.step_confirm_topic(start_mode="assessment"):
            return self._finalize()

        # Step 5: Consume post-confirm stream (assessment questions)
        print("\n[Step 5] Consume post-confirmation stream")
        ok, events = self.step_consume_post_confirm()
        if not ok:
            return self._finalize()

        # Step 6-7: Answer assessment questions (try a few rounds)
        print("\n[Step 6-7] Submit assessment answers (dialog mode)")
        for i in range(5):  # Try up to 5 questions
            if not self.step_submit_assessment_answer(answer="A"):
                break
            ok, events = self.step_consume_assessment_stream()
            if not ok:
                break
            # Check if we've moved past assessment
            end_events = [e for e in events if e.type == "session.end"]
            if end_events:
                end_data = end_events[-1].parsed or {}
                fs = end_data.get("data", {}).get("flow_status", "")
                if fs not in ("assessment_dialog", ""):
                    self._log("assessment_progress", "INFO", f"flow_status={fs!r} after Q{i+1}")
                    break

        # Step 8: Submit post_lesson_choice (start_test)
        print("\n[Step 8] Submit post_lesson_choice (start_test)")
        if not self.step_submit_post_lesson_choice(choice="start_test"):
            # Might not be at post_lesson_choice yet — try continuing
            self._log("post_lesson_choice", "INFO", "Not at post_lesson_choice, continuing...")

        # Step 9: Consume post_lesson stream
        print("\n[Step 9] Consume post-lesson stream")
        ok, events = self.step_consume_post_lesson_stream()
        if not ok:
            self._log("post_lesson_stream", "INFO", "Stream ended, continuing...")

        # Step 10: Submit objective answers
        print("\n[Step 10] Submit objective test answers")
        if not self.step_submit_objective_answers():
            self._log("objective_answers", "INFO", "Not at objective test, continuing...")

        # Step 11: Consume objective stream
        print("\n[Step 11] Consume objective test stream")
        ok, events = self.step_consume_objective_stream()
        if not ok:
            self._log("objective_stream", "INFO", "Stream ended, continuing...")

        # Step 12: Submit continue_or_homework_choice
        print("\n[Step 12] Submit continue_or_homework_choice")
        if not self.step_submit_continue_or_homework(choice="continue"):
            self._log("continue_choice", "INFO", "Not at continue/homework, continuing...")

        # Step 13: Consume continue stream
        print("\n[Step 13] Consume continue stream")
        ok, events = self.step_consume_continue_stream()
        if not ok:
            self._log("continue_stream", "INFO", "Stream ended, continuing...")

        # Step 14: Test session resume
        print("\n[Step 14] Test session resume")
        if not self.step_resume_session():
            self._log("resume", "INFO", "Resume failed, continuing...")

        # Step 15: Consume resume stream
        print("\n[Step 15] Consume resume stream")
        ok, events = self.step_consume_resume_stream()
        if not ok:
            self._log("resume_stream", "INFO", "Resume stream ended")

        return self._finalize()

    def run_temporary_question_flow(self) -> bool:
        """Run the temporary question flow smoke test."""
        print(f"\n{'='*60}")
        print(f"  AI Tutor Agent — Temporary Question Flow E2E Smoke")
        print(f"  Base URL: {self.base_url}")
        print(f"  Thread ID: {self.thread_id}")
        print(f"{'='*60}\n")

        # Steps 0-5: Same as full flow to get to post_lesson_choice
        print("[Step 0] Health check")
        if not self.step_health():
            return self._finalize()

        print("\n[Step 1] Create session placeholder")
        if not self.step_create_session():
            return self._finalize()

        print("\n[Step 2] Start learning with topic")
        if not self.step_start_topic():
            return self._finalize()

        print("\n[Step 3] Consume initial SSE stream")
        ok, events = self.step_consume_initial_stream()
        if not ok:
            return self._finalize()

        print("\n[Step 4] Confirm topic (assessment mode)")
        if not self.step_confirm_topic(start_mode="assessment"):
            return self._finalize()

        print("\n[Step 5] Consume post-confirmation stream")
        ok, events = self.step_consume_post_confirm()
        if not ok:
            return self._finalize()

        # Answer assessment questions
        print("\n[Step 6] Submit assessment answers")
        for i in range(5):
            if not self.step_submit_assessment_answer(answer="A"):
                break
            ok, events = self.step_consume_assessment_stream()
            if not ok:
                break
            end_events = [e for e in events if e.type == "session.end"]
            if end_events:
                end_data = end_events[-1].parsed or {}
                fs = end_data.get("data", {}).get("flow_status", "")
                if fs not in ("assessment_dialog", ""):
                    break

        # Now submit a free-form temporary question
        print("\n[Step 7] Submit temporary question (free-form)")
        if not self.step_submit_post_lesson_choice(
            choice="我还是不太理解根轨迹的分离点怎么求"
        ):
            self._log("temp_question", "INFO", "Not at post_lesson_choice")

        print("\n[Step 8] Consume temporary question stream")
        ok, events = self.step_consume_post_lesson_stream()
        if not ok:
            self._log("temp_stream", "INFO", "Stream ended")

        # After temporary question answer, should return to post_lesson_choice
        # Then submit start_test
        print("\n[Step 9] Submit start_test after temporary question")
        if not self.step_submit_post_lesson_choice(choice="start_test"):
            self._log("start_test", "INFO", "Not at post_lesson_choice")

        print("\n[Step 10] Consume start_test stream")
        ok, events = self.step_consume_post_lesson_stream()
        if not ok:
            self._log("start_test_stream", "INFO", "Stream ended")

        return self._finalize()

    def _finalize(self) -> bool:
        """Print summary and return success/failure."""
        print(f"\n{'='*60}")
        print(f"  SMOKE TEST SUMMARY")
        print(f"{'='*60}")
        print(f"  Thread ID: {self.thread_id}")
        print(f"  Steps passed: {self.steps_passed}")
        print(f"  Steps failed: {self.steps_failed}")

        if self.errors:
            print(f"\n  Errors:")
            for err in self.errors:
                print(f"    - {err}")

        success = self.steps_failed == 0 and self.steps_passed > 0
        if success:
            print(f"\n  ✅ ALL STEPS PASSED")
        else:
            print(f"\n  ❌ SMOKE TEST FAILED")

        print(f"{'='*60}\n")
        return success


# ── CLI ────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="AI Tutor Agent — Strict Learning Flow E2E Smoke Test"
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000",
        help="Base URL of the running server (default: http://127.0.0.1:8000)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=120.0,
        help="Request timeout in seconds (default: 120)",
    )
    parser.add_argument(
        "--flow",
        choices=["full", "temporary_question", "both"],
        default="full",
        help="Which flow to test (default: full)",
    )
    args = parser.parse_args()

    runner = SmokeRunner(base_url=args.base_url, timeout=args.timeout)

    try:
        if args.flow == "full":
            success = runner.run_full_flow()
        elif args.flow == "temporary_question":
            success = runner.run_temporary_question_flow()
        else:  # both
            success1 = runner.run_full_flow()
            # Reset for second run
            runner = SmokeRunner(base_url=args.base_url, timeout=args.timeout)
            success2 = runner.run_temporary_question_flow()
            success = success1 and success2
    finally:
        runner.close()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

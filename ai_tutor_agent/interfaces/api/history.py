from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from .runtime import get_runtime


router = APIRouter(prefix="/api/history", tags=["history"])
messages_router = APIRouter(prefix="/api/messages", tags=["history"])

PRE_TOPIC_FLOW_STATUSES = {"greeting", "topic_intake", "meta_qa", "smalltalk"}


def _serialize_state(values: dict[str, Any]) -> dict[str, Any]:
    return {
        "current_topic": values.get("current_topic", ""),
        "proposed_topic": values.get("proposed_topic", ""),
        "tutor_content": values.get("tutor_content", ""),
        "tester_question": values.get("tester_question", ""),
        "tester_question_type": values.get("tester_question_type", ""),
        "tester_question_template": values.get("tester_question_template", ""),
        "user_answer": values.get("user_answer", ""),
        "score": values.get("score", 0),
        "logic_score": values.get("logic_score", 0),
        "concept_score": values.get("concept_score", 0),
        "feedback": values.get("feedback", ""),
        "rubric_feedback": values.get("rubric_feedback", []),
        "model_answer": values.get("model_answer", ""),
        "misconceptions": values.get("misconceptions", []),
        "next_review_points": values.get("next_review_points", []),
        "is_correct_direction": values.get("is_correct_direction", True),
        "needs_hint": values.get("needs_hint", False),
        "difficulty_level": values.get("difficulty_level", 3),
        "attempt_count": values.get("attempt_count", 0),
        "score_history": values.get("score_history", []),
        "coach_content": values.get("coach_content", ""),
        "tutor_citations": values.get("tutor_citations", []),
        "skip_reason": values.get("skip_reason", ""),
        "interrupt_query": values.get("interrupt_query", ""),
        "resume_tester": values.get("resume_tester", False),
        "conversation_history": values.get("conversation_history", []),
        "assessment_questions": values.get("assessment_questions", []),
        "assessment_answers": values.get("assessment_answers", {}),
        "assessment_radar": values.get("assessment_radar", {}),
        "assessment_result": values.get("assessment_result", ""),
        "is_assessed": values.get("is_assessed", False),
        "flow_status": values.get("flow_status", "greeting"),
    }


def _checkpoint_summary(thread_id: str, checkpoint_tuple) -> dict[str, Any]:
    values = checkpoint_tuple.checkpoint.get("channel_values", {})
    flow_status = values.get("flow_status", "greeting")
    current_topic = values.get("current_topic", "")
    proposed_topic = values.get("proposed_topic", "")
    if flow_status == "awaiting_topic_confirmation" and proposed_topic:
        display_title = f"待确认：{proposed_topic}"
    elif flow_status in PRE_TOPIC_FLOW_STATUSES:
        display_title = "未确认主题"
    else:
        display_title = current_topic or thread_id
    return {
        "thread_id": thread_id,
        "current_topic": current_topic,
        "display_title": display_title,
        "flow_status": flow_status,
        "is_assessed": values.get("is_assessed", False),
        "score": values.get("score", 0),
        "updated_at": checkpoint_tuple.checkpoint.get("ts"),
        "checkpoint_id": checkpoint_tuple.checkpoint.get("id"),
    }


def _history_entries(checkpoint_store, thread_id: str, *, limit: int = 20) -> list[dict[str, Any]]:
    config = {"configurable": {"thread_id": thread_id}}
    entries = []
    for checkpoint_tuple in checkpoint_store.list(config, limit=limit):
        values = checkpoint_tuple.checkpoint.get("channel_values", {})
        entries.append(
            {
                "checkpoint_id": checkpoint_tuple.checkpoint.get("id"),
                "updated_at": checkpoint_tuple.checkpoint.get("ts"),
                "source": checkpoint_tuple.metadata.get("source"),
                "step": checkpoint_tuple.metadata.get("step"),
                "flow_status": values.get("flow_status", "greeting"),
                "current_topic": values.get("current_topic", ""),
                "score": values.get("score", 0),
            }
        )
    return entries


def _build_evaluator_card(values: dict[str, Any]) -> str:
    score = values.get("score", 0)
    logic = values.get("logic_score", 0)
    concept = values.get("concept_score", 0)
    feedback = values.get("feedback", "") or "这轮评估已完成。"
    lines = [
        "### 最近一轮评估",
        "",
        f"- 总分：**{score}**",
        f"- 逻辑：**{logic}**",
        f"- 概念：**{concept}**",
        "",
        f"简要诊断：{feedback}",
    ]

    rubric = values.get("rubric_feedback") or []
    if rubric:
        lines.append("")
        lines.append("量表依据：")
        lines.extend([f"- {item}" for item in rubric])

    return "\n".join(lines)


def _build_citations_card(citations: list[dict[str, Any]]) -> str:
    if not citations:
        return ""

    lines = ["### 参考来源"]
    seen: set[tuple[str, Any, Any]] = set()

    for index, item in enumerate(citations[:4], start=1):
        filename = str(item.get("filename", "")).strip()
        if not filename:
            continue

        page = item.get("page")
        chunk_index = item.get("chunk_index")
        key = (filename, page, chunk_index)
        if key in seen:
            continue
        seen.add(key)

        page_text = f"（第 {page} 页）" if isinstance(page, int) else ""
        chunk_text = f" · 片段 #{chunk_index}" if isinstance(chunk_index, int) else ""
        lines.append("")
        lines.append(f"{index}. {filename}{page_text}{chunk_text}")

        snippet = str(item.get("snippet", "")).strip()
        if snippet:
            one_line_snippet = " ".join(snippet.split())
            lines.append(f"> {one_line_snippet}")

    return "\n".join(lines)


def _reconstruct_messages(checkpoint_store, thread_id: str, *, limit: int = 240) -> list[dict[str, Any]]:
    config = {"configurable": {"thread_id": thread_id}}
    timeline: list[dict[str, Any]] = []

    for checkpoint_tuple in checkpoint_store.list(config, limit=limit):
        values = checkpoint_tuple.checkpoint.get("channel_values", {})
        timeline.append(
            {
                "updated_at": checkpoint_tuple.checkpoint.get("ts") or "",
                "values": values,
            }
        )

    if not timeline:
        return []

    timeline.sort(key=lambda item: item["updated_at"])
    messages: list[dict[str, Any]] = []
    previous_values: dict[str, Any] = {}

    def push(role: str, kind: str, content: str, updated_at: str, *, tone: str = "info") -> None:
        text = (content or "").strip()
        if not text:
            return
        messages.append(
            {
                "role": role,
                "kind": kind,
                "content": text,
                "updated_at": updated_at,
                "tone": tone,
            }
        )

    for item in timeline:
        updated_at = item["updated_at"]
        values = item["values"]

        assessment_result = values.get("assessment_result", "")
        if assessment_result and assessment_result != previous_values.get("assessment_result", ""):
            push("agent", "assessment_result", assessment_result, updated_at)

        tutor_content = values.get("tutor_content", "")
        if tutor_content and tutor_content != previous_values.get("tutor_content", ""):
            push("agent", "tutor", tutor_content, updated_at)

        tutor_citations = values.get("tutor_citations") or []
        if tutor_citations and tutor_citations != previous_values.get("tutor_citations", []):
            citations_card = _build_citations_card(tutor_citations)
            if citations_card:
                push("agent", "tutor_citations", citations_card, updated_at)

        coach_content = values.get("coach_content", "")
        if coach_content and coach_content != previous_values.get("coach_content", ""):
            push("agent", "coach", coach_content, updated_at)

        tester_question = values.get("tester_question", "")
        if tester_question and tester_question != previous_values.get("tester_question", ""):
            push("agent", "tester_question", tester_question, updated_at)

        user_answer = values.get("user_answer", "")
        if user_answer and user_answer != previous_values.get("user_answer", ""):
            push("user", "user_answer", user_answer, updated_at)

        feedback_changed = (
            values.get("score", 0) != previous_values.get("score", 0)
            or values.get("logic_score", 0) != previous_values.get("logic_score", 0)
            or values.get("concept_score", 0) != previous_values.get("concept_score", 0)
            or values.get("feedback", "") != previous_values.get("feedback", "")
            or values.get("rubric_feedback", []) != previous_values.get("rubric_feedback", [])
        )
        if feedback_changed and (values.get("score", 0) or values.get("feedback", "")):
            push("agent", "evaluator_card", _build_evaluator_card(values), updated_at)

        previous_values = values

    return messages


@router.get("")
async def get_history(request: Request):
    runtime = get_runtime(request)
    db_path = runtime.settings.memory_db_path
    checkpoint_store, saver_conn = runtime.checkpoint_factory(db_path)
    try:
        try:
            with sqlite3.connect(db_path) as conn:
                rows = conn.execute(
                    """
                    SELECT thread_id
                    FROM checkpoints
                    GROUP BY thread_id
                    ORDER BY MAX(rowid) DESC
                    LIMIT 50
                    """
                ).fetchall()
        except sqlite3.OperationalError:
            return {"threads": [], "items": []}

        items = []
        for (thread_id,) in rows:
            checkpoint_tuple = checkpoint_store.get_tuple({"configurable": {"thread_id": thread_id}})
            if checkpoint_tuple:
                items.append(_checkpoint_summary(thread_id, checkpoint_tuple))

        return {
            "threads": [item["thread_id"] for item in items],
            "items": items,
        }
    finally:
        saver_conn.close()


@router.get("/{thread_id}")
async def get_history_detail(thread_id: str, request: Request):
    runtime = get_runtime(request)
    session = runtime.session_manager.refresh_status(thread_id)
    db_path = runtime.settings.memory_db_path
    checkpoint_store, saver_conn = runtime.checkpoint_factory(db_path)
    try:
        checkpoint_tuple = checkpoint_store.get_tuple({"configurable": {"thread_id": thread_id}})
        if checkpoint_tuple is None:
            raise HTTPException(status_code=404, detail=f"Unknown thread_id: {thread_id}")

        values = checkpoint_tuple.checkpoint.get("channel_values", {})
        return {
            "thread_id": thread_id,
            "summary": _checkpoint_summary(thread_id, checkpoint_tuple),
            "state": _serialize_state(values),
            "runtime": {
                "is_running": bool(session.get("is_running")),
                "awaiting_input": bool(session.get("awaiting_input")),
            },
            "checkpoints": _history_entries(checkpoint_store, thread_id),
        }
    finally:
        saver_conn.close()


@router.delete("/{thread_id}")
async def delete_history(thread_id: str, request: Request):
    runtime = get_runtime(request)
    db_path = runtime.settings.memory_db_path
    checkpoint_store, saver_conn = runtime.checkpoint_factory(db_path)
    try:
        try:
            checkpoint_store.delete_thread(thread_id)
        except sqlite3.OperationalError:
            pass
        runtime.session_manager.remove(thread_id)
        return {"status": "success"}
    finally:
        saver_conn.close()


@messages_router.get("/{thread_id}")
async def get_messages(thread_id: str, request: Request):
    runtime = get_runtime(request)
    db_path = runtime.settings.memory_db_path
    checkpoint_store, saver_conn = runtime.checkpoint_factory(db_path)
    try:
        checkpoint_tuple = checkpoint_store.get_tuple({"configurable": {"thread_id": thread_id}})
        if checkpoint_tuple is None:
            raise HTTPException(status_code=404, detail=f"Unknown thread_id: {thread_id}")

        values = checkpoint_tuple.checkpoint.get("channel_values", {})
        return {
            "thread_id": thread_id,
            "items": _reconstruct_messages(checkpoint_store, thread_id),
            "state": _serialize_state(values),
        }
    finally:
        saver_conn.close()

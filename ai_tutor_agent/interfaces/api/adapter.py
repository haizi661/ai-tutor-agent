from __future__ import annotations

import queue
from typing import Any, Optional

from ...core.events import AgentEvent
from ...core.ports import AnswerProvider, EventSink

INPUT_WAIT_TIMEOUT_SECONDS = 120


class WebEventSink(EventSink):
    def __init__(self, q: queue.Queue):
        self.q = q

    def emit(self, event: AgentEvent) -> None:
        self.q.put(event)


class WebAnswerProvider(AnswerProvider):
    def __init__(self, q: queue.Queue, event_sink: EventSink, on_awaiting_input=None):
        self.q = q
        self.event_sink = event_sink
        self.on_awaiting_input = on_awaiting_input

    def get_answer(
        self,
        prompt: str,
        *,
        state: Optional[dict[str, Any]] = None,
    ) -> str:
        from ...core.events import make_event

        self.event_sink.emit(
            make_event("session.awaiting_input", "api", message=prompt, data=state)
        )
        if self.on_awaiting_input:
            self.on_awaiting_input(True, state or {})
        try:
            return self.q.get(timeout=INPUT_WAIT_TIMEOUT_SECONDS)
        except queue.Empty as exc:
            raise TimeoutError("Timed out while waiting for user input.") from exc
        finally:
            if self.on_awaiting_input:
                self.on_awaiting_input(False, None)

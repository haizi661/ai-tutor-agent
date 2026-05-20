from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Protocol

from .events import AgentEvent


class UserAbortError(Exception):
    """Raised when the user explicitly requests to stop the session."""


class EventSink(Protocol):
    def emit(self, event: AgentEvent) -> None:
        """Handle one structured runtime event."""


class AnswerProvider(Protocol):
    def get_answer(
        self,
        prompt: str,
        *,
        state: Optional[dict[str, Any]] = None,
    ) -> str:
        """Get one answer from the external interaction channel."""


class KnowledgeProvider(Protocol):
    def query(self, query: str, *, rewrite_request: Any | None = None) -> str:
        """Query external knowledge source."""


class QuestionBankProvider(Protocol):
    def get_objective_questions(self, node_id: str, k: int = 10) -> list[dict[str, Any]]:
        """Return objective questions bound to a graph node."""

    def get_variant_question(self, wrong_item: dict[str, Any]) -> dict[str, Any]:
        """Return one variant question for a wrong objective item."""

    def get_homework_questions(self, node_ids: list[str], k: int = 5) -> list[dict[str, Any]]:
        """Return homework questions for selected graph nodes."""

    def list_runtime_question_bank_items(self) -> list[dict[str, Any]]:
        """Return processed question-bank items imported from the workbook pipeline."""

    def get_assessment_questions(self, node_ids: list[str], k: int = 10) -> list[dict[str, Any]]:
        """Return pre-assessment subjective-choice questions for given graph node ids."""


class NoopEventSink:
    def emit(self, event: AgentEvent) -> None:
        del event


class MissingAnswerProvider:
    def get_answer(
        self,
        prompt: str,
        *,
        state: Optional[dict[str, Any]] = None,
    ) -> str:
        del prompt, state
        raise RuntimeError(
            "No AnswerProvider configured. Inject one from CLI, API, or tests."
        )


class NoopKnowledgeProvider:
    def query(self, query: str, *, rewrite_request: Any | None = None) -> str:
        del rewrite_request
        return ""


class BufferedEventSink:
    def __init__(self) -> None:
        self.events: list[AgentEvent] = []

    def emit(self, event: AgentEvent) -> None:
        self.events.append(event)


class CallbackEventSink:
    def __init__(self, handler: Callable[[AgentEvent], None]) -> None:
        self._handler = handler

    def emit(self, event: AgentEvent) -> None:
        self._handler(event)


@dataclass
class RuntimeContext:
    event_sink: EventSink = field(default_factory=NoopEventSink)
    answer_provider: AnswerProvider = field(default_factory=MissingAnswerProvider)
    knowledge_provider: KnowledgeProvider = field(default_factory=NoopKnowledgeProvider)
    settings: Any | None = None
    graph_rag_pipeline: Any | None = None
    student_state_store: Any | None = None
    question_bank_provider: Any | None = None

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
    def query(self, query: str) -> str:
        """Query external knowledge source."""


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
    def query(self, query: str) -> str:
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

from typing import Optional

from ..core.events import make_event
from ..core.ports import EventSink, NoopEventSink
from ..core.state import AgentState


def build_route_logic(pass_score: int, event_sink: Optional[EventSink] = None):
    sink = event_sink or NoopEventSink()

    def route_logic(state: AgentState) -> str:
        score = state["score"]
        decision = "pass" if score >= pass_score else "fail"
        sink.emit(
            make_event(
                "route.decision",
                "router",
                data={
                    "decision": decision,
                    "score": score,
                    "pass_score": pass_score,
                },
            )
        )

        return decision

    return route_logic

from typing import Optional

from ..core.events import make_event
from ..core.ports import EventSink, NoopEventSink
from ..core.state import AgentState


def build_route_logic(pass_score: int, event_sink: Optional[EventSink] = None):
    sink = event_sink or NoopEventSink()

    def route_logic(state: AgentState) -> str:
        score = state.get("score", 0)
        has_legacy_shape = (
            "logic_score" not in state
            and "concept_score" not in state
            and "attempt_count" not in state
            and "is_correct_direction" not in state
            and "needs_hint" not in state
        )

        if has_legacy_shape:
            decision = "pass" if score >= pass_score else "fail"
            sink.emit(
                make_event(
                    "route.decision",
                    "router",
                    data={"decision": decision, "score": score, "pass_score": pass_score},
                )
            )
            return decision

        logic_score = state.get("logic_score", 0)
        concept_score = state.get("concept_score", 0)
        is_correct_direction = state.get("is_correct_direction", False)
        needs_hint = state.get("needs_hint", False)
        attempt_count = state.get("attempt_count", 0)

        if score >= pass_score and logic_score >= 55 and concept_score >= 55:
            decision = "pass"
        elif needs_hint or (score >= pass_score - 20 and is_correct_direction) or (attempt_count >= 2 and score >= pass_score - 25):
            decision = "remediate"
        else:
            decision = "reteach"

        sink.emit(
            make_event(
                "route.decision",
                "router",
                data={
                    "decision": decision,
                    "score": score,
                    "logic_score": logic_score,
                    "concept_score": concept_score,
                    "is_correct_direction": is_correct_direction,
                    "needs_hint": needs_hint,
                    "attempt_count": attempt_count,
                    "pass_score": pass_score,
                },
            )
        )

        return decision

    return route_logic

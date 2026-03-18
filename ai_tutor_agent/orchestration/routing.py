from typing import Optional

from ..core.events import make_event
from ..core.ports import EventSink, NoopEventSink
from ..core.state import AgentState


def build_route_logic(pass_score: int, event_sink: Optional[EventSink] = None):
    sink = event_sink or NoopEventSink()
    skip_tokens = {"/skip", "/pass", "skip", "掌握", "已掌握", "跳过"}

    def route_logic(state: AgentState) -> str:
        # 支持用户跳过：如果 skip_reason 不为空，视为通过
        user_answer = str(state.get("user_answer", "")).strip().lower()
        if state.get("skip_reason") and user_answer in skip_tokens:
             decision = "pass"
             score = 100 # 视为满分
             sink.emit(
                make_event(
                    "route.decision",
                    "router",
                    data={
                        "decision": decision,
                        "skip_reason": state.get("skip_reason"),
                        "message": "User skipped assessment (mastered)."
                    },
                )
            )
             return decision

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

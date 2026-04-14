from ..core.events import make_event
from ..core.ports import EventSink
from ..core.state import AgentState


def build_topic_confirm_node(event_sink: EventSink):
    def node(state: AgentState) -> dict:
        proposed_topic = state.get("proposed_topic", "").strip()
        detail_summary = str(state.get("topic_detail_summary") or "").strip()
        topic_focus = str(state.get("topic_focus") or "").strip()
        topic_background = str(state.get("topic_background") or "").strip()
        starter_options = list(state.get("topic_starter_options") or [])
        clarify_rounds = int(state.get("topic_clarify_rounds") or 0)
        if not proposed_topic:
            event_sink.emit(
                make_event(
                    "session.warning",
                    "topic_confirmer",
                    message="未找到待确认主题，返回主题识别阶段。",
                )
            )
            return {"flow_status": "greeting"}

        event_sink.emit(
            make_event(
                "topic.confirmation_needed",
                "topic_confirmer",
                message=(
                    f"我先把这次方向收成【{proposed_topic}】。"
                    "如果重点没跑偏，我们就从这里切进去。"
                ),
                data={
                    "proposed_topic": proposed_topic,
                    "detail_summary": detail_summary,
                    "topic_focus": topic_focus,
                    "topic_background": topic_background,
                    "topic_starter_options": starter_options,
                    "clarify_rounds": clarify_rounds,
                },
            )
        )
        event_sink.emit(
            make_event(
                "node.complete",
                "topic_confirmer",
                message="主题和当前重点已经先替你收了一遍，等你确认。",
            )
        )
        return {
            "flow_status": "awaiting_topic_confirmation",
            "message_history": list(state.get("message_history", []))
            + [
                {
                    "role": "assistant",
                    "kind": "topic_confirmation_card",
                    "content": (
                        f"我先把这次方向收成【{proposed_topic}】。"
                        "如果重点没跑偏，我们就从这里切进去。"
                    ),
                    "data": {
                        "proposed_topic": proposed_topic,
                        "detail_summary": detail_summary,
                        "topic_focus": topic_focus,
                        "topic_background": topic_background,
                        "topic_starter_options": starter_options,
                        "clarify_rounds": clarify_rounds,
                    },
                }
            ],
        }

    return node

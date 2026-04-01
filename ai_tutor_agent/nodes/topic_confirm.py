from ..core.events import make_event
from ..core.ports import EventSink
from ..core.state import AgentState


def build_topic_confirm_node(event_sink: EventSink):
    def node(state: AgentState) -> dict:
        proposed_topic = state.get("proposed_topic", "").strip()
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
                message=f"我先把你的目标收成【{proposed_topic}】。如果这个表述对，就直接确认；如果你想改，我再跟着你调整。",
                data={"proposed_topic": proposed_topic},
            )
        )
        event_sink.emit(
            make_event(
                "node.complete",
                "topic_confirmer",
                message="主题已经整理出来了，等你点头确认。",
            )
        )
        return {"flow_status": "awaiting_topic_confirmation"}

    return node

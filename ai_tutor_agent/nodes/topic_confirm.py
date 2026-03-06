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
                message=f"我理解你想学的是【{proposed_topic}】。请确认或修改主题。",
                data={"proposed_topic": proposed_topic},
            )
        )
        event_sink.emit(
            make_event(
                "node.complete",
                "topic_confirmer",
                message="等待用户确认学习主题。",
            )
        )
        return {"flow_status": "awaiting_topic_confirmation"}

    return node

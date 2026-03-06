from ..core.events import make_event
from ..core.ports import AnswerProvider, EventSink
from ..core.state import AgentState


def _build_smalltalk_answer(user_text: str) -> str:
    normalized = user_text.strip()
    if any(token in normalized for token in ["谢谢", "辛苦"]):
        return "不客气。我可以陪你简单聊几句，不过我更擅长把知识点讲清楚。"
    if any(token in normalized for token in ["焦虑", "紧张", "烦", "心情不好"]):
        return "先别急，我们可以把目标拆小一点。我能陪你缓一缓，也能马上帮你把学习任务拆成更容易开始的第一步。"
    if any(token in normalized for token in ["在吗", "你好", "您好", "哈喽", "嗨"]):
        return "我在。除了陪你学习，我也能简单聊几句。"
    if "聊聊天" in normalized:
        return "可以短聊，但我会尽量把对话再拉回到学习和解决问题上。"
    return "可以先聊一句，不过我的主业还是伴学和讲解知识。"


def build_smalltalk_node(event_sink: EventSink, answer_provider: AnswerProvider):
    def node(state: AgentState) -> dict:
        user_text = state.get("current_topic", "").strip()
        answer = _build_smalltalk_answer(user_text)
        event_sink.emit(
            make_event(
                "node.start",
                "smalltalk",
                message="正在进行轻度闲聊...",
            )
        )
        event_sink.emit(
            make_event("node.stream", "smalltalk", data={"text": answer})
        )
        event_sink.emit(
            make_event(
                "node.complete",
                "smalltalk",
                message="轻聊完成，等待下一步输入。",
            )
        )
        next_input = answer_provider.get_answer(
            prompt="如果你想开始学习，直接告诉我主题；如果只是想再聊一句，也可以继续输入。",
            state=state,
        )
        return {
            "current_topic": next_input,
            "flow_status": "greeting",
        }

    return node

from langchain_core.messages import HumanMessage, SystemMessage

from ..core.events import make_event
from ..core.ports import AnswerProvider, EventSink
from ..core.state import AgentState
from ..core.text import content_to_text


_SMALLTALK_SYSTEM = """你是一位有温度、有个性的AI学习伴侣。你的主业是帮助学生学习，但你也是一个真正会聊天的伙伴。

闲聊原则：
1. 用自然、温暖的口吻回应，像朋友一样，不要用机器人腔调
2. 如果学生有情绪问题（焦虑、疲惫、烦恼），先共情，再轻轻引导回学习状态
3. 回应要简短（2~4句话），不要长篇大论
4. 自然地在结尾关心学生："现在状态怎么样？准备开始学点什么了吗？"——但不要每次都一样，要有变化
5. 禁止说空洞的客套话，比如"当然！""好的！""没问题！"

你的性格特点：真诚、耐心、偶尔带一点幽默感，但不油腻。"""


def build_smalltalk_node(llm, event_sink: EventSink, answer_provider: AnswerProvider):
    def node(state: AgentState) -> dict:
        user_text = state.get("current_topic", "").strip()

        event_sink.emit(
            make_event(
                "node.start",
                "smalltalk",
                message="我先陪你接一句，再看看要不要顺势进入学习。",
            )
        )

        system_msg = SystemMessage(content=_SMALLTALK_SYSTEM)
        human_msg = HumanMessage(content=user_text or "你好")

        full_response = ""
        for chunk in llm.stream([system_msg, human_msg]):
            chunk_text = content_to_text(chunk.content)
            full_response += chunk_text
            event_sink.emit(
                make_event("node.stream", "smalltalk", data={"text": chunk_text})
            )

        event_sink.emit(
            make_event(
                "node.complete",
                "smalltalk",
                message="这句我先接住了，等你决定下一步要聊还是要学。",
            )
        )

        next_input = answer_provider.get_answer(
            prompt="随时可以告诉我想学的主题，或者继续聊也行。你想开始时，我就顺着那个点带你进去。",
            state=state,
        )
        return {
            "current_topic": next_input,
            "flow_status": "greeting",
        }

    return node

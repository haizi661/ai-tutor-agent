from langchain_core.messages import HumanMessage, SystemMessage

from ..core.events import make_event
from ..core.ports import RuntimeContext
from ..core.state import AgentState
from ..core.text import content_to_text


def build_coach_node(llm, event_sink):
    """
    启发式教练节点：
    当学生答错时，不直接重讲，而是提供渐进式线索（Scaffolding）。
    """

    def node(state: AgentState):
        topic = state["current_topic"]
        question = state["tester_question"]
        user_answer = state["user_answer"]
        feedback = state["feedback"]
        
        event_sink.emit(
            make_event(
                "node.start",
                "coach",
                message="导师正在为你准备启发式提示...",
            )
        )

        system_msg = SystemMessage(
            content="""你是一位充满智慧的苏格拉底式助教。
            当学生在回答问题遇到困难时，你的任务不是直接给答案，也不是重读教材，而是：
            1. 肯定学生回答中正确的部分（哪怕只有一点点）。
            2. 针对他犯错的地方，给出一个不直接给答案的【关键提示】或【思考角度】。
            3. 抛出一个简单的引导性问题，鼓励他再试一次。
            
            语气要幽默、轻松，像个贴身学长。
            """
        )
        
        human_msg = HumanMessage(
            content=f"""
            学习主题：{topic}
            刚才的题目：{question}
            学生的回答：{user_answer}
            评估反馈：{feedback}
            
            请根据以上信息，给出一个启发式的提示。
            """
        )

        full_hint = ""
        for chunk in llm.stream([system_msg, human_msg]):
            text = content_to_text(chunk.content)
            full_hint += text
            event_sink.emit(
                make_event("node.stream", "coach", data={"text": text})
            )

        event_sink.emit(
            make_event(
                "node.complete",
                "coach",
                message="提示已发送，等待你再次尝试。",
            )
        )

        return {"feedback": full_hint} # 将提示作为新的反馈传回

    return node

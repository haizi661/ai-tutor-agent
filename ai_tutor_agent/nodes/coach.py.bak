from langchain_core.messages import HumanMessage, SystemMessage

from ..core.events import make_event
from ..core.ports import RuntimeContext
from ..core.state import AgentState
from ..core.teacher_voice import build_teacher_voice
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
                message="我不急着直接给答案，先帮你搭一个更容易继续往下想的抓手。",
            )
        )

        system_msg = SystemMessage(
            content=build_teacher_voice(
                """你现在不是重讲整段教材，而是在学生答错后给一个“还能继续想下去”的脚手架。

输出要求：
1. 先点出学生已经抓到的部分，哪怕只有半步
2. 再指出目前最关键的偏差或漏掉的判断点
3. 给一个不直接泄题的抓手，可以是判断标准、类比、观察顺序或拆题步骤
4. 最后丢一个很短的引导问题，邀请学生再试一次
5. 全文控制在 4 句以内，不要直接给完整标准答案"""
            )
        )
        
        human_msg = HumanMessage(
            content=f"""
            学习主题：{topic}
            刚才的题目：{question}
            学生的回答：{user_answer}
            评估反馈：{feedback}
            
            请根据以上信息，给出一个启发式提示，让学生感觉“差一点就能自己想出来了”。
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
                message="我先给到你一个抓手，等你带着它再试一次。",
            )
        )

        return {"coach_content": full_hint}

    return node

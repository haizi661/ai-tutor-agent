from langchain_core.messages import HumanMessage, SystemMessage

from ..core.events import make_event
from ..core.graph_service import GraphQueryService
from ..core.ports import RuntimeContext
from ..core.state import AgentState
from ..core.teacher_voice import build_teacher_voice
from ..core.text import content_to_text


def build_coach_node(llm, event_sink, knowledge_provider=None):
    """
    启发式教练节点：
    当学生答错时，不直接重讲，而是提供渐进式线索（Scaffolding）。
    现在会利用知识图谱的 common_errors 和 must_know 来提供更精准的脚手架。
    同时检测前驱节点缺口，在脚手架中引导学生补前置。
    """

    def node(state: AgentState):
        topic = state["current_topic"]
        question = state["tester_question"]
        user_answer = state["user_answer"]
        feedback = state["feedback"]
        misconceptions = state.get("misconceptions", [])
        graph_common_errors = state.get("graph_common_errors", [])
        graph_must_know = state.get("graph_must_know", [])

        event_sink.emit(
            make_event(
                "node.start",
                "coach",
                message="我不急着直接给答案，先帮你搭一个更容易继续往下想的抓手。",
            )
        )

        # 基于知识图谱构建精准脚手架提示
        graph_hint_parts = []
        if graph_common_errors:
            error_lines = []
            for err in graph_common_errors[:2]:
                if isinstance(err, dict):
                    error_lines.append(
                        f"- 常见误区：{err.get('error', '')}，纠偏：{err.get('correction', '')}"
                    )
            if error_lines:
                graph_hint_parts.append(
                    "\n【课程图谱已知误区】\n"
                    + "\n".join(error_lines)
                    + "\n请判断学生是否踩中了上述误区，如果是，针对性纠偏。"
                )
        if graph_must_know:
            graph_hint_parts.append(
                f"\n【核心必会点】{', '.join(str(m) for m in graph_must_know[:3])}"
                "\n请围绕这些必会点来搭脚手架。"
            )
        if misconceptions:
            graph_hint_parts.append(
                f"\n【本次识别到的误区】{', '.join(str(m) for m in misconceptions[:3])}"
            )

        # 前驱节点缺口检测
        _course_nodes = getattr(knowledge_provider, "course_graph_nodes", None) or {}
        graph_anchor = str(state.get("graph_anchor_title") or "").strip()
        if _course_nodes and graph_anchor:
            gqs = GraphQueryService(_course_nodes)
            user_kg = state.get("user_knowledge_graph") or {}
            gaps = gqs.detect_prerequisite_gaps(graph_anchor, user_kg, max_depth=2)
            if gaps:
                gap_names = [g["title"] for g in gaps[:2]]
                graph_hint_parts.append(
                    f"\n【前驱知识缺口】学生在前置节点{'、'.join(gap_names)}存在掌握缺口。"
                    "\n请在脚手架中自然地探测学生对这些前置概念的掌握情况，"
                    "如果确认前置薄弱，引导学生先回顾前置知识。"
                )

        graph_context_prompt = "".join(graph_hint_parts)

        system_msg = SystemMessage(
            content=build_teacher_voice(
                f"""你现在不是重讲整段教材，而是在学生答错后给一个"还能继续想下去"的脚手架。

输出要求：
1. 先点出学生已经抓到的部分，哪怕只有半步
2. 再指出目前最关键的偏差或漏掉的判断点
3. 给一个不直接泄题的抓手，可以是判断标准、类比、观察顺序或拆题步骤
4. 最后丢一个很短的引导问题，邀请学生再试一次
5. 全文控制在 4 句以内，不要直接给完整标准答案{graph_context_prompt}"""
            )
        )

        human_msg = HumanMessage(
            content=f"""
            学习主题：{topic}
            刚才的题目：{question}
            学生的回答：{user_answer}
            评估反馈：{feedback}
            
            请根据以上信息，给出一个启发式提示，让学生感觉"差一点就能自己想出来了"。
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

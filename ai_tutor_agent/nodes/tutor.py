from langchain_core.messages import HumanMessage, SystemMessage

from ..core.events import make_event
from ..core.ports import RuntimeContext
from ..core.state import AgentState
from ..core.text import content_to_text


def build_tutor_node(tutor_llm, runtime: RuntimeContext):
    def render_recent_history(state: AgentState, limit: int = 10) -> str:
        history = list(state.get("conversation_history", []))
        if not history:
            return "（暂无历史对话）"

        lines = []
        for item in history[-limit:]:
            role = "学生" if item.get("role") == "user" else "导师"
            content = str(item.get("content", "")).strip()
            if content:
                lines.append(f"{role}: {content}")
        return "\n".join(lines) if lines else "（暂无历史对话）"

    def tutor_node(state: AgentState):
        event_sink = runtime.event_sink
        knowledge_provider = runtime.knowledge_provider

        event_sink.emit(
            make_event(
                "node.start",
                "tutor",
                message="Tutor node started.",
                data={"topic": state["current_topic"]},
            )
        )

        # RAG: Query relevant knowledge
        context = knowledge_provider.query(state["current_topic"])
        knowledge_prompt = ""
        if context:
            knowledge_prompt = f"\n\n请参考以下检索到的专业知识进行讲解：\n{context}\n"

        system_msg = SystemMessage(
            content="你是一位拥有20年教龄的顶尖工科教授，性格极度耐心、温柔，最擅长把极其复杂的理论转化为通俗易懂的工程或生活案例。"
        )

        if state.get("feedback"):
            human_msg = HumanMessage(
                content=f"""
                学生在考核时失败了。
                错因反馈是：{state['feedback']}。
                学生当前卡在知识点：【{state['current_topic']}】。
                最近对话历史：
                {render_recent_history(state)}
                {knowledge_prompt}
                请针对该错因，结合上述专业知识（如果有），换一个完全不同、更具直观性的生活比喻，重新开导他。字数控制在400字左右。
                """
            )
        else:
            human_msg = HumanMessage(
                content=f"""
                请为学生详细讲解【{state['current_topic']}】的核心原理。
                最近对话历史：
                {render_recent_history(state)}
                {knowledge_prompt}
                要求逻辑严密，专业术语准确，并给出一个具体的实际应用场景。字数控制在400字左右。
                """
            )

        full_response = ""
        for chunk in tutor_llm.stream([system_msg, human_msg]):
            chunk_text = content_to_text(chunk.content)
            full_response += chunk_text
            event_sink.emit(
                make_event(
                    "node.stream",
                    "tutor",
                    data={"text": chunk_text},
                )
            )

        event_sink.emit(
            make_event(
                "node.complete",
                "tutor",
                message="Tutor node completed.",
                data={"content_length": len(full_response)},
            )
        )
        history = list(state.get("conversation_history", []))
        history.append(
            {
                "role": "assistant",
                "kind": "tutor",
                "content": full_response,
            }
        )
        return {"tutor_content": full_response, "conversation_history": history}

    return tutor_node

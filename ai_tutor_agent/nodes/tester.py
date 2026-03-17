from langchain_core.messages import HumanMessage, SystemMessage

from ..core.events import make_event
from ..core.ports import AnswerProvider, EventSink
from ..core.state import AgentState
from ..core.text import content_to_text


def build_tester_node(
    tester_llm,
    event_sink: EventSink,
    answer_provider: AnswerProvider,
):
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

    def tester_node(state: AgentState):
        event_sink.emit(
            make_event(
                "node.start",
                "tester",
                message="Tester node started.",
                data={"topic": state["current_topic"]},
            )
        )

        system_msg = SystemMessage(
            content="你是刁钻的高校助教。你的任务是基于教授刚讲过的教案，出一道且仅有一道极其刁钻的场景排错题或计算分析题。绝不输出除了题目以外的任何客套话。"
        )
        human_msg = HumanMessage(
            content=(
                f"这是教授刚才的教案：\n{state['tutor_content']}\n\n"
                f"这是最近对话历史（用于避免重复、保持连续性）：\n{render_recent_history(state)}"
            )
        )

        full_question = ""
        for chunk in tester_llm.stream([system_msg, human_msg]):
            chunk_text = content_to_text(chunk.content)
            full_question += chunk_text
            event_sink.emit(
                make_event(
                    "node.stream",
                    "tester",
                    data={"text": chunk_text},
                )
            )

        event_sink.emit(
            make_event(
                "node.complete",
                "tester",
                message="Tester node completed.",
                data={"question": full_question},
            )
        )

        user_input = answer_provider.get_answer(
            ">> 请输入你的解答 (输入 'quit' 退出): ",
            state={
                "current_topic": state["current_topic"],
                "tester_question": full_question,
            },
        ).strip()
        event_sink.emit(
            make_event(
                "answer.received",
                "tester",
                message="User answer received.",
                data={"answer_length": len(user_input)},
            )
        )

        history = list(state.get("conversation_history", []))
        history.append(
            {
                "role": "assistant",
                "kind": "tester_question",
                "content": full_question,
            }
        )
        history.append(
            {
                "role": "user",
                "kind": "tester_answer",
                "content": user_input,
            }
        )

        return {
            "tester_question": full_question,
            "user_answer": user_input,
            "conversation_history": history,
        }

    return tester_node

from langchain_core.messages import HumanMessage, SystemMessage
from ..core.events import make_event
from ..core.ports import RuntimeContext
from ..core.state import AgentState
from ..core.text import content_to_text

def build_tester_node(tester_llm, runtime: RuntimeContext):
    """
    重构后的 Tester 节点，统一接收 runtime 对象。
    """
    def tester_node(state: AgentState):
        # 从 runtime 中解构出需要的零件
        event_sink = runtime.event_sink
        answer_provider = runtime.answer_provider

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
        human_msg = HumanMessage(content=f"这是教授刚才的教案：\n{state['tutor_content']}")

        full_question = ""
        # 流式输出题目
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

        # 阻塞等待用户回答
        # 注意：这里我们通过 answer_provider 拿到用户的输入
        user_input = answer_provider.get_answer(
            ">> 请输入你的解答: ",
            state={
                "current_topic": state["current_topic"],
                "tester_question": full_question,
                "student_id": state.get("student_id", "default")
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

        return {"tester_question": full_question, "user_answer": user_input}

    return tester_node
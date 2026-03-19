from langchain_core.messages import HumanMessage, SystemMessage
from ..core.events import make_event
from ..core.ports import RuntimeContext
from ..core.state import AgentState
from ..core.text import content_to_text


ASK_PREFIXES = ("/ask", "问:", "问题:")
QUESTION_HINTS = (
    "为什么",
    "怎么",
    "如何",
    "请问",
    "是什么",
    "什么意思",
    "能不能",
    "可不可以",
    "请解释",
    "解释一下",
    "举个例子",
)


def _looks_like_interrupt_question(text: str) -> bool:
    cleaned = (text or "").strip()
    if not cleaned:
        return False

    lowered = cleaned.lower()
    if lowered in {"/skip", "/pass", "skip", "掌握", "已掌握", "跳过"}:
        return False

    if lowered.startswith(ASK_PREFIXES):
        return True

    if any(mark in cleaned for mark in ["?", "？"]):
        return True

    if any(hint in cleaned for hint in QUESTION_HINTS):
        return True

    # 短句且疑问式开头，优先当作临时提问处理
    starts = ("这题", "这个", "那题", "这里", "此处", "它为啥", "为啥")
    if len(cleaned) <= 40 and cleaned.startswith(starts):
        return True

    return False

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

        # 临时提问返回后，优先复用上一题，避免重复出新题打断主线。
        full_question = ""
        if state.get("resume_tester") and state.get("tester_question"):
            full_question = state.get("tester_question", "")
            event_sink.emit(
                make_event(
                    "node.stream",
                    "tester",
                    data={"text": f"回到主线，请继续回答上一题：\n{full_question}"},
                )
            )
        else:
            system_msg = SystemMessage(
                content="你是刁钻的高校助教。你的任务是基于教授刚讲过的教案，出一道且仅有一道极其刁钻的场景排错题或计算分析题。绝不输出除了题目以外的任何客套话。"
            )
            human_msg = HumanMessage(content=f"这是教授刚才的教案：\n{state['tutor_content']}")

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
            ">> 请输入你的解答 (或者输入 '/skip' 表示已掌握): ",
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

        # 临时提问: 用户可先问一个问题，系统回答后再回到本题。
        if _looks_like_interrupt_question(user_input):
            lowered = user_input.lower()
            if lowered.startswith(ASK_PREFIXES):
                interrupt_query = user_input.split(":", 1)[-1].strip() if ":" in user_input else user_input[4:].strip()
            else:
                interrupt_query = user_input.strip()
            if not interrupt_query:
                interrupt_query = "请解释这道题涉及的关键知识点。"
            history = list(state.get("conversation_history", []))
            history.append({"role": "user", "kind": "interruption_user", "content": interrupt_query})
            return {
                "tester_question": full_question,
                "user_answer": "",
                "interrupt_query": interrupt_query,
                "resume_tester": True,
                "skip_reason": "",
                "conversation_history": history,
            }

        return {
            "tester_question": full_question,
            "user_answer": user_input,
            "resume_tester": False,
            "interrupt_query": "",
            "skip_reason": "",
        }

    return tester_node
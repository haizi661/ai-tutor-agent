from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from ..core.events import make_event
from ..core.ports import RuntimeContext
from ..core.state import AgentState
from ..core.teacher_voice import build_teacher_voice
from ..core.text import content_to_text


def _build_recent_interrupt_context(history: list, limit: int = 6) -> str:
    interrupt_msgs = []
    for msg in history or []:
        kind = str(msg.get("kind", ""))
        if kind in {"interruption_user", "interruption"} or kind.startswith("interruption"):
            interrupt_msgs.append(msg)

    if not interrupt_msgs:
        return ""

    lines = []
    for item in interrupt_msgs[-limit:]:
        role = "用户" if str(item.get("role")) == "user" else "老师"
        content = str(item.get("content", "")).strip()
        if content:
            lines.append(f"{role}: {content}")
    return "\n".join(lines)


def build_interruption_node(tutor_llm, runtime: RuntimeContext):
    def node(state: AgentState) -> dict:
        event_sink = runtime.event_sink
        knowledge_provider = runtime.knowledge_provider

        query = str(state.get("interrupt_query", "")).strip()
        if not query:
            return {"resume_tester": bool(state.get("resume_tester", False))}

        history = list(state.get("conversation_history", []))
        recent_interrupt_context = _build_recent_interrupt_context(history)

        event_sink.emit(
            make_event(
                "node.start",
                "interruption_tutor",
                message="我先接住这个临时卡点，马上给你讲清楚。",
                data={"query": query},
            )
        )

        search_query = f"{state.get('current_topic', '')} {query}".strip()
        context = knowledge_provider.query(search_query)
        if not context and search_query != query:
            context = knowledge_provider.query(query)

        knowledge_prompt = ""
        if context:
            knowledge_prompt = (
                "\n\n【知识库参考】\n"
                "请优先依据以下知识库内容作答，确保术语与结论准确：\n"
                f"---\n{context}\n---\n"
            )

        system_msg = SystemMessage(
            content=build_teacher_voice(
                """你现在负责处理中途追问。

先接住用户当前卡住的点，用自然、具体、像面对面辅导的语气解释清楚；
如果适合，给一个很短的判断口诀、类比或下一步观察点。"""
            )
        )
        human_msg = HumanMessage(
            content=(
                f"当前学习主题：{state.get('current_topic', '')}\n"
                f"用户临时问题：{query}\n"
                f"{knowledge_prompt}\n"
                f"最近的临时会话上下文（用于连续对话）：\n{recent_interrupt_context or '无'}\n"
                "输出要求：\n"
                "1. 开头先点出用户卡住的是哪一层意思，不要空泛安慰\n"
                "2. 主体解释控制在 220 字以内\n"
                "3. 最后一句自然提醒：如果愿意，我们可以回到刚才那道题继续"
            )
        )

        full_response = ""
        for chunk in tutor_llm.stream([system_msg, human_msg]):
            chunk_text = content_to_text(chunk.content)
            full_response += chunk_text
            event_sink.emit(
                make_event(
                    "node.stream",
                    "interruption_tutor",
                    data={"text": chunk_text},
                )
            )

        event_sink.emit(
            make_event(
                "node.complete",
                "interruption_tutor",
                message="这个临时问题已经讲完了。",
            )
        )
        event_sink.emit(
            make_event(
                "interrupt.confirmation_needed",
                "interruption_tutor",
                message="如果这一步已经顺了，我们就回到刚才那道题；如果你还想追问，也可以继续问我。",
                data={"requires_confirmation": True},
            )
        )
        event_sink.emit(
            make_event(
                "session.info",
                "interruption_tutor",
                message="临时问题我先替你讲到这里。你决定一下：回到主线，还是继续追问。",
                data={"requires_interrupt_confirmation": True},
            )
        )

        history.append({"role": "assistant", "kind": "interruption", "content": full_response})

        return {
            "tutor_content": full_response,
            "interrupt_query": "",
            "resume_tester": bool(state.get("resume_tester", False)),
            "flow_status": "awaiting_interrupt_confirmation",
            "conversation_history": history,
        }

    return node

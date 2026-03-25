from langchain_core.messages import HumanMessage, SystemMessage
import sys

from ..core.events import make_event
from ..core.ports import RuntimeContext
from ..core.state import AgentState
from ..core.text import content_to_text


def _build_recent_interrupt_context(history: list, limit: int = 6) -> str:
    interrupt_msgs = []
    for msg in history or []:
        kind = str(msg.get("kind", ""))
        role = str(msg.get("role", ""))
        if kind in {"interruption_user", "interruption"}:
            interrupt_msgs.append(msg)
            continue
        if role in {"user", "assistant"} and kind.startswith("interruption"):
            interrupt_msgs.append(msg)

    if not interrupt_msgs:
        return ""

    clipped = interrupt_msgs[-limit:]
    lines = []
    for item in clipped:
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
            return {"resume_tester": False}

        history = list(state.get("conversation_history", []))
        recent_interrupt_context = _build_recent_interrupt_context(history)

        event_sink.emit(
            make_event(
                "node.start",
                "interruption_tutor",
                message="正在处理临时问题...",
                data={"query": query},
            )
        )

        search_query = f"{state.get('current_topic', '')} {query}".strip()
        rag_hybrid_enabled = bool(
            getattr(getattr(runtime, "settings", None), "rag_hybrid_enabled", False)
        )
        rag_mode = "hybrid" if rag_hybrid_enabled else "vector"
        sys.stderr.write(f"[RAG][node_query] node=interruption mode={rag_mode} query={search_query}\n")
        sys.stderr.flush()
        context = knowledge_provider.query(search_query)
        if not context:
            fallback_query = query
            sys.stderr.write(
                f"[RAG][node_query_fallback] node=interruption mode={rag_mode} query={fallback_query}\n"
            )
            sys.stderr.flush()
            context = knowledge_provider.query(fallback_query)
        knowledge_prompt = ""
        if context:
            knowledge_prompt = (
                "\n\n【知识库参考】\n"
                "请优先依据以下知识库内容作答，确保术语与结论准确：\n"
                f"---\n{context}\n---\n"
            )
            sys.stderr.write(f"[RAG][node_result] node=interruption hit=true context_len={len(context)}\n")
        else:
            sys.stderr.write("[RAG][node_result] node=interruption hit=false context_len=0\n")
        sys.stderr.flush()

        system_msg = SystemMessage(
            content="你是一位耐心、严谨的老师。请先解答用户的临时问题，再提醒其回到主线任务。"
        )
        human_msg = HumanMessage(
            content=(
                f"当前学习主题：{state.get('current_topic', '')}\n"
                f"用户临时问题：{query}\n"
                f"{knowledge_prompt}\n"
                f"最近的临时会话上下文（用于连续对话）：\n{recent_interrupt_context or '无'}\n"
                "请给出清晰解释，控制在 220 字以内，最后一句请提示“我们继续回到主线作答”。"
            )
        )

        full_response = ""
        for chunk in tutor_llm.stream([system_msg, human_msg]):
            chunk_text = content_to_text(chunk.content)
            full_response += chunk_text
            event_sink.emit(make_event("node.stream", "interruption_tutor", data={"text": chunk_text}))

        event_sink.emit(
            make_event(
                "node.complete",
                "interruption_tutor",
                message="临时问题解答完成。",
            )
        )
        event_sink.emit(
            make_event(
                "interrupt.confirmation_needed",
                "interruption_tutor",
                message="请输入“继续”或“回到主线”以恢复教学主线。",
                data={"requires_confirmation": True},
            )
        )
        event_sink.emit(
            make_event(
                "session.info",
                "interruption_tutor",
                message="临时问题已解答，请确认是否回到主线。",
                data={"requires_interrupt_confirmation": True},
            )
        )

        history.append({"role": "assistant", "kind": "interruption", "content": full_response})

        return {
            "tutor_content": full_response,
            "interrupt_query": "",
            "resume_tester": False,
            "flow_status": "awaiting_interrupt_confirmation",
            "conversation_history": history,
        }

    return node

from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from ..core.events import make_event
from ..core.ports import RuntimeContext
from ..core.state import AgentState
from ..core.teacher_voice import build_teacher_voice
from ..core.text import content_to_text
from ..infrastructure.retriever import RetrievalRewriteRequest


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


def _build_bridge_sentence(state: AgentState) -> str:
    """生成从临时追问回到主线的自然过渡语句。"""
    topic = str(state.get("current_topic") or "").strip()
    graph_anchor = str(state.get("graph_anchor_title") or "").strip()
    resume_tester = bool(state.get("resume_tester", False))
    tester_q = str(state.get("tester_question") or "").strip()

    main_subject = graph_anchor or topic or "之前的内容"

    if resume_tester and tester_q:
        return f"这个追问先讲到这里。刚才那道关于「{main_subject}」的练习题还在，要不要回去继续做？如果你还有疑惑，也可以继续追问。"
    elif topic:
        return f"好，这个卡点先处理完了。我们回到「{main_subject}」继续——你觉得这块现在理顺了吗，还是需要我再展开？"
    else:
        return "这个问题先讲到这里。如果你已经理清了，我们就接着刚才的进度走；还想追问也没问题。"


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
        rewrite_request = RetrievalRewriteRequest(
            channel="interruption",
            raw_query=query,
            current_topic=str(state.get("current_topic", "") or ""),
            teaching_strategy="interruption",
            conversation_hint=recent_interrupt_context,
        )
        try:
            if hasattr(knowledge_provider, "query_with_sources"):
                retrieval = knowledge_provider.query_with_sources(search_query, rewrite_request=rewrite_request)
                context = retrieval.get("context", "")
            else:
                context = knowledge_provider.query(search_query, rewrite_request=rewrite_request)
        except TypeError:
            if hasattr(knowledge_provider, "query_with_sources"):
                context = knowledge_provider.query_with_sources(search_query).get("context", "")
            else:
                context = knowledge_provider.query(search_query)
        if not context and search_query != query:
            try:
                if hasattr(knowledge_provider, "query_with_sources"):
                    context = knowledge_provider.query_with_sources(query, rewrite_request=rewrite_request).get("context", "")
                else:
                    context = knowledge_provider.query(query, rewrite_request=rewrite_request)
            except TypeError:
                if hasattr(knowledge_provider, "query_with_sources"):
                    context = knowledge_provider.query_with_sources(query).get("context", "")
                else:
                    context = knowledge_provider.query(query)

        knowledge_prompt = ""
        if context:
            knowledge_prompt = (
                "\n\n【知识库参考】\n"
                "请优先依据以下知识库内容作答，确保术语与结论准确：\n"
                f"---\n{context}\n---\n"
            )
        else:
            knowledge_prompt = (
                "\n\n【知识来源说明】当前知识库中未找到直接匹配的资料。"
                "请基于你的专业知识来回答，确保准确性。"
                "如有不确定之处，请明确告诉学生并建议查阅教材。\n"
            )

        system_msg = SystemMessage(
            content=build_teacher_voice(
                """你现在负责处理中途追问。

先接住用户当前卡住的点，用自然、具体、像面对面辅导的语气解释清楚；
如果适合，给一个很短的判断口诀、类比或下一步观察点。
即使当前知识库里没有直接匹配的资料，你也要基于你的专业知识给出有价值的回答，不要拒绝或推脱。"""
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

        # ── 生成桥接回主线的自然过渡 ──
        bridge_sentence = _build_bridge_sentence(state)

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
                message=bridge_sentence,
                data={"requires_confirmation": True},
            )
        )
        event_sink.emit(
            make_event(
                "session.info",
                "interruption_tutor",
                message=bridge_sentence,
                data={"requires_interrupt_confirmation": True},
            )
        )

        history.append({"role": "assistant", "kind": "interruption", "content": full_response})
        message_history = list(state.get("message_history", []))
        message_history.append({"role": "assistant", "kind": "interruption", "content": full_response})
        message_history.append(
            {
                "role": "assistant",
                "kind": "interrupt_confirmation_card",
                "content": bridge_sentence,
                "data": {"requires_confirmation": True},
            }
        )

        return {
            "tutor_content": full_response,
            "interrupt_query": "",
            "resume_tester": bool(state.get("resume_tester", False)),
            "flow_status": "awaiting_interrupt_confirmation",
            "conversation_history": history,
            "message_history": message_history,
        }

    return node

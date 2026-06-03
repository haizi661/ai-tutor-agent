from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage
from ai_tutor_agent.knowledge_map.debug_graph_rag import build_answer_media_html, build_learning_answer_html

from ..core.events import make_event
from ..core.learning_support import normalize_graph_answer, record_student_temporary_question, trim_message_history
from ..core.ports import RuntimeContext
from ..core.state import AgentState
from ..core.teacher_voice import build_teacher_voice
from ..core.text import content_to_text
from ..infrastructure.retriever import RetrievalRewriteRequest

logger = logging.getLogger(__name__)


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


def _build_interrupt_fallback(state: AgentState, query: str) -> str:
    topic = str(state.get("current_topic") or "").strip()
    graph_anchor = str(state.get("graph_anchor_title") or "").strip()
    main_subject = graph_anchor or topic or "当前节点"
    return (
        f"你这个临时问题先抓【{main_subject}】里和“{query}”最相关的一层："
        "先分清它在判断什么、再分清它不等于什么。"
        "如果你愿意，我们接下来就把这个点带回刚才那道题继续看。"
    )


def _invoke_llm_text(llm, messages: list[object]) -> str:
    response = llm.invoke(messages)
    return content_to_text(getattr(response, "content", response))


def _collect_interrupt_text_with_fallback(
    llm,
    messages: list[object],
    *,
    prefer_invoke: bool = False,
) -> tuple[str, bool]:
    if prefer_invoke:
        try:
            return _invoke_llm_text(llm, messages), False
        except Exception:
            logger.exception("interruption_tutor invoke failed while stream disabled")
            return "", False
    try:
        raw_response = ""
        for chunk in llm.stream(messages):
            raw_response += content_to_text(getattr(chunk, "content", chunk))
        return raw_response, False
    except Exception as stream_exc:
        logger.warning("interruption_tutor stream failed, retrying with invoke: %s", stream_exc)
        try:
            return _invoke_llm_text(llm, messages), True
        except Exception:
            logger.exception("interruption_tutor invoke fallback failed")
            return "", True


def _looks_like_graph_fallback(text: str, graph_result: dict | None = None) -> bool:
    lowered = text.lower()
    if "fallback" in lowered or "模板" in text or "回退" in text:
        return True
    if graph_result:
        plan = graph_result.get("plan") or {}
        if isinstance(plan, dict) and plan.get("used_llm") is False:
            return True
    return False


def _graph_rag_used_llm(graph_result: dict[str, object] | None) -> bool:
    if not graph_result:
        return False
    plan = graph_result.get("plan") or {}
    return isinstance(plan, dict) and plan.get("used_llm") is True


def _build_search_query(state: AgentState, query: str) -> str:
    parts = [
        str(state.get("current_topic") or "").strip(),
        str(state.get("graph_anchor_title") or state.get("current_node_name") or "").strip(),
        query,
    ]
    return " ".join(part for part in parts if part).strip()


def _resolve_temporary_question_node(state: AgentState, graph_result: dict[str, object] | None) -> tuple[str, str]:
    node_id = str(state.get("current_node_id") or state.get("graph_anchor_id") or "").strip()
    node_title = str(state.get("current_node_name") or state.get("graph_anchor_title") or "").strip()
    anchors = list((graph_result or {}).get("anchor_nodes") or [])
    if not node_id and anchors:
        first = anchors[0] if isinstance(anchors[0], dict) else {}
        node_id = str(first.get("node_id") or "").strip()
        node_title = node_title or str(first.get("name") or "").strip()
    return node_id, node_title or node_id


def _extract_temporary_question_refs(graph_result: dict[str, object] | None) -> list[str]:
    refs: list[str] = []

    def add_ref(value: object) -> None:
        ref = str(value or "").strip()
        if ref and ref not in refs:
            refs.append(ref)

    for item in list((graph_result or {}).get("evidence_items") or []):
        if isinstance(item, dict):
            add_ref(item.get("reference") or item.get("node_id") or item.get("node_name"))
    for item in list((graph_result or {}).get("media_items") or []):
        if isinstance(item, dict):
            add_ref(item.get("reference") or item.get("node_name"))
    for item in list((graph_result or {}).get("anchor_nodes") or []):
        if isinstance(item, dict):
            add_ref(item.get("node_id") or item.get("name"))
    return refs


def _build_graph_rag_answer_html(graph_result: dict[str, object], *, answer_override: str = "") -> str:
    payload = dict(graph_result or {})
    if answer_override:
        payload["answer"] = answer_override
    return build_learning_answer_html(payload, answer_context="temporary_question")


def _build_graph_rag_debug_answer_html(graph_result: dict[str, object], *, answer_override: str = "") -> str:
    payload = dict(graph_result or {})
    if answer_override:
        payload["answer"] = answer_override
    return build_answer_media_html(payload)


def _build_graph_rag_llm_messages(state: AgentState, query: str, graph_result: dict[str, object], recent_interrupt_context: str) -> list[object]:
    return [
        SystemMessage(
            content=build_teacher_voice(
                """你现在负责处理中途追问。图谱 RAG 已经完成节点检索与上下文构造，
你必须基于图谱结果重新组织成自然、准确、面向学生的解释；不要直接照搬检索模板或 fallback 文本。
如果图谱结果里有公式、图或表，不要压缩掉它们对应的解释，也不要把媒体引用全部堆到最后。"""
            )
        ),
        HumanMessage(
            content=(
                f"当前学习主题：{state.get('current_topic', '')}\n"
                f"用户临时问题：{query}\n"
                f"图谱检索答案草稿：\n{graph_result.get('answer') or ''}\n\n"
                f"图谱检索上下文：\n{graph_result.get('context_text') or ''}\n\n"
                f"相关节点摘要：\n{graph_result.get('node_summaries') or []}\n\n"
                f"相关公式/图表/表格：\n{graph_result.get('media_items') or []}\n\n"
                f"最近临时会话上下文：\n{recent_interrupt_context or '无'}\n\n"
                "输出要求：\n"
                "1. 必须回答用户问题本身，不要只说检索到了什么\n"
                "2. 根据问题复杂度自适应：短问短答可以 120 到 220 字；涉及公式、图或概念辨析时再展开到 300 到 500 字\n"
                "3. 若图谱草稿是 fallback/模板化内容，要用上下文重写成具体解释，但不要丢掉图谱中的公式、图表、表格线索\n"
                "4. 如果正文分析到某个媒体，请在相关段落后单独保留一行 [[MEDIA:媒体reference]]，每个媒体最多出现一次\n"
                "5. 已有媒体引用后不要再抄写同一个公式源码、图题、表格原文或 caption，前端会用媒体卡片展示\n"
                "6. 不要机械套固定的“结论 -> 分析 -> 举例 -> 拓展 -> 依据”模板；按学生追问自然组织，可以是直接解释、换个例子、指出误区或给判断抓手\n"
                "7. 不要输出裸数字引用、[KMxxx.summary]、'// 图...' 注释、手写的“相关公式与图表”区块或“依据”清单\n"
                "8. 不要引入图谱结果中没有出现的节点编号、资料编号或引用；如果需要引用媒体，只能使用上方媒体列表里的 exact reference\n"
                "9. 最后一句自然收束：可以继续追问，也可以回到刚才主线继续"
            )
        ),
    ]


def build_interruption_node(tutor_llm, runtime: RuntimeContext):
    def node(state: AgentState) -> dict:
        event_sink = runtime.event_sink
        knowledge_provider = runtime.knowledge_provider
        graph_rag_pipeline = getattr(runtime, "graph_rag_pipeline", None)
        llm_stream_disabled = bool(state.get("llm_stream_disabled", False))
        llm_stream_failures = int(state.get("llm_stream_failures") or 0)

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

        search_query = _build_search_query(state, query)
        graph_result = None
        full_response = ""
        response_kind = "interruption"
        response_data: dict[str, object] = {}
        if graph_rag_pipeline is not None:
            try:
                graph_result = graph_rag_pipeline.ask(search_query or query, traversal_mode="balanced")
            except Exception as exc:
                graph_result = None
                event_sink.emit(
                    make_event(
                        "session.warning",
                        "interruption_tutor",
                        message="图谱 2.2 临时问答失败，已回退到常规检索回答。",
                        data={"error": str(exc)},
                    )
                )

        if graph_result is not None:
            graph_answer = normalize_graph_answer(
                str(graph_result.get("answer") or ""),
                list(graph_result.get("media_items") or []),
            ).strip()
            graph_context = str(graph_result.get("context_text") or "").strip()
            graph_used_llm = _graph_rag_used_llm(graph_result)

            # ── 教学推理透明：解释临时问题分析 ──
            if state.get("thinking_mode", False):
                media_count = len(graph_result.get("media_items") or [])
                evidence_count = len(graph_result.get("evidence") or [])
                search_info = f"检索到 {evidence_count} 条证据" if evidence_count > 0 else "未找到直接证据，使用图谱上下文回答"
                media_info = f"、{media_count} 个图表/公式" if media_count > 0 else ""
                event_sink.emit(
                    make_event(
                        "thinking.step",
                        "interruption_tutor",
                        message=f"临时问题分析：「{query[:30]}{'...' if len(query) > 30 else ''}」→ {search_info}{media_info}",
                        data={
                            "category": "interruption_analysis",
                            "query": query,
                            "evidence_count": evidence_count,
                            "media_count": media_count,
                            "used_graph_rag": graph_used_llm is not None,
                        },
                    )
                )

            if graph_used_llm:
                full_response = _build_graph_rag_answer_html(graph_result).strip()
                response_kind = "graph_rag_answer"
                response_data = {"graph_rag_result": graph_result}
            else:
                should_polish = tutor_llm is not None and (graph_context or _looks_like_graph_fallback(graph_answer, graph_result))
                if should_polish:
                    full_response, stream_failed = _collect_interrupt_text_with_fallback(
                        tutor_llm,
                        _build_graph_rag_llm_messages(state, query, graph_result, recent_interrupt_context),
                        prefer_invoke=llm_stream_disabled,
                    )
                    if stream_failed:
                        llm_stream_disabled = True
                        llm_stream_failures += 1
                    full_response = full_response.strip()
                    if full_response and graph_result.get("media_items"):
                        full_response = _build_graph_rag_answer_html(graph_result, answer_override=full_response).strip()
                        response_kind = "graph_rag_answer"
                        response_data = {"graph_rag_result": graph_result}
                if not full_response:
                    if graph_result.get("media_items"):
                        full_response = _build_graph_rag_answer_html(graph_result).strip()
                        response_kind = "graph_rag_answer"
                        response_data = {"graph_rag_result": graph_result}
                    else:
                        full_response = graph_answer or graph_context or "我先把这个临时问题的关键主线收紧，再继续给你讲。"
            event_sink.emit(
                make_event(
                    "node.stream",
                    "interruption_tutor",
                    data={"text": full_response, "kind": response_kind},
                )
            )
        else:
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

            full_response, stream_failed = _collect_interrupt_text_with_fallback(
                tutor_llm,
                [system_msg, human_msg],
                prefer_invoke=llm_stream_disabled,
            )
            if stream_failed:
                llm_stream_disabled = True
                llm_stream_failures += 1
            full_response = full_response.strip()
            if not full_response:
                full_response = _build_interrupt_fallback(state, query)
            event_sink.emit(
                make_event(
                    "node.stream",
                    "interruption_tutor",
                    data={"text": full_response, "kind": response_kind},
                )
            )

        # ── 生成桥接回主线的自然过渡 ──
        bridge_sentence = _build_bridge_sentence(state)
        resume_tester = bool(state.get("resume_tester", False))
        from_post_lesson = str(state.get("learning_resume_target") or "").strip() in {
            "post_lesson_choice", "temporary_question_collector", "interruption_tutor",
        } and not resume_tester

        event_sink.emit(
            make_event(
                "node.complete",
                "interruption_tutor",
                message="这个临时问题已经讲完了。",
            )
        )

        history.append({"role": "assistant", "kind": response_kind, "content": full_response, "data": response_data})
        message_history = list(state.get("message_history", []))
        message_history.append({"role": "assistant", "kind": response_kind, "content": full_response, "data": response_data})
        student_id = str(state.get("student_id") or "default_student").strip() or "default_student"
        evidence_node_id, evidence_node_title = _resolve_temporary_question_node(state, graph_result)
        student_state_snapshot = record_student_temporary_question(
            getattr(runtime, "student_state_store", None),
            student_id=student_id,
            node_id=evidence_node_id,
            title=evidence_node_title,
            question=query,
            answer_kind=response_kind,
            references=_extract_temporary_question_refs(graph_result),
        )
        student_snapshot_patch = {"student_state_snapshot": student_state_snapshot} if student_state_snapshot else {}

        if from_post_lesson:
            # 临时问题来自讲解后选择，直接回到 post_lesson_choice，不显示中断确认卡片
            post_prompt = "这个问题先讲到这里。你可以继续追问、换个角度问，或者如果已经顺了就进入小测。"
            post_options = [
                {"value": "temporary_question", "label": "继续追问"},
                {"value": "start_test", "label": "我懂了，进入小测"},
            ]
            event_sink.emit(
                make_event(
                    "session.info",
                    "interruption_tutor",
                    message=post_prompt,
                    data={"options": post_options, "interaction_kind": "post_lesson_choice"},
                )
            )
            return {
                "interrupt_query": "",
                "resume_tester": False,
                "flow_status": "awaiting_post_lesson_choice",
                "learning_phase": "post_lesson_choice",
                "learning_resume_target": "post_lesson_choice",
                "learning_resume_reason": "interrupt_answered_back_to_choice",
                "pending_interaction_kind": "post_lesson_choice",
                "pending_interaction_prompt": post_prompt,
                "pending_interaction_options": post_options,
                "pending_interaction_recommended": "start_test",
                "pending_interaction_answer": "",
                "conversation_history": history,
                "message_history": trim_message_history(message_history),
                "llm_stream_disabled": llm_stream_disabled,
                "llm_stream_failures": llm_stream_failures,
                **student_snapshot_patch,
            }

        # 有 tester 待恢复或其他场景：显示中断确认卡片
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
        message_history.append(
            {
                "role": "assistant",
                "kind": "interrupt_confirmation_card",
                "content": bridge_sentence,
                "data": {"requires_confirmation": True},
            }
        )

        return {
            "interrupt_query": "",
            "resume_tester": resume_tester,
            "flow_status": "awaiting_interrupt_confirmation",
            "learning_phase": "node_temp_qna",
            "learning_resume_target": "interruption_tutor",
            "learning_resume_reason": "interrupt_answered_waiting_confirmation",
            "conversation_history": history,
            "message_history": trim_message_history(message_history),
            "llm_stream_disabled": llm_stream_disabled,
            "llm_stream_failures": llm_stream_failures,
            **student_snapshot_patch,
        }

    return node

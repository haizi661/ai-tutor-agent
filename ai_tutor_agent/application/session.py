from __future__ import annotations

from ..core.events import make_event
from ..core.learning_flow import build_learning_flow_scaffold
from ..core.learning_support import (
    assign_homework_items,
    build_graph_state_patch,
    build_homework_items,
    recommend_next_node,
)
from ..core.state import build_initial_state


PRE_TOPIC_FLOW_STATUSES = {
    "greeting",
    "topic_intake",
    "meta_qa",
    "smalltalk",
}
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

SKIP_COMMANDS = {"/skip", "/pass", "skip", "掌握", "已掌握", "跳过"}
RESUME_MAINLINE_COMMANDS = {
    "继续",
    "继续主线",
    "回到主线",
    "返回主线",
    "确认回主线",
    "ok",
    "yes",
    "y",
}
NEXT_NODE_COMMANDS = {
    "继续学习",
    "直接下一节点",
    "开始下一节点",
    "下一节点",
    "继续下一个节点",
}
CONSOLIDATE_COMMANDS = {
    "巩固",
    "巩固知识",
    "复习",
    "先巩固",
    "需要巩固",
}


def _is_skip_command(text: str) -> bool:
    return (text or "").strip().lower() in SKIP_COMMANDS


def _is_resume_mainline_command(text: str) -> bool:
    normalized = (text or "").strip().lower()
    if normalized in RESUME_MAINLINE_COMMANDS:
        return True
    return any(
        token in normalized
        for token in ["继续", "回到主线", "返回主线", "继续学习", "继续主线"]
    )


def _is_next_node_command(text: str) -> bool:
    normalized = (text or "").strip().lower()
    if normalized in NEXT_NODE_COMMANDS:
        return True
    return any(token in normalized for token in ["下一节点", "继续学习", "直接学", "开始学习"])


def _is_consolidate_command(text: str) -> bool:
    normalized = (text or "").strip().lower()
    if normalized in CONSOLIDATE_COMMANDS:
        return True
    return any(token in normalized for token in ["巩固", "复习", "回顾"])


def _format_homework_message(homework_items: list[dict]) -> str:
    lines = ["\n我找到你上次留下的作业了。"]
    if not homework_items:
        lines.append("当前没有可展示的题目明细，但系统仍记录了作业状态。")
        return "\n".join(lines)

    lines.append("先把今天要处理的题目列给你：")
    for index, item in enumerate(homework_items[:3], start=1):
        lines.append(f"{index}. {str(item.get('prompt') or '').strip()}")
    if len(homework_items) > 3:
        lines.append(f"另外还有 {len(homework_items) - 3} 道题已保存在本轮作业里。")
    lines.append("如果你想直接继续下一节点，输入“继续学习”或“下一节点”即可。")
    return "\n".join(lines)


def _resume_next_node_payload(state_values: dict, runtime_context=None) -> dict | None:
    graph_rag_pipeline = getattr(runtime_context, "graph_rag_pipeline", None) if runtime_context is not None else None
    next_node_id = str(state_values.get("next_node_candidate_id") or "").strip()
    next_node_name = str(state_values.get("next_node_candidate_name") or "").strip()

    if not next_node_id and graph_rag_pipeline is not None:
        next_candidate = recommend_next_node(
            graph_pipeline=graph_rag_pipeline,
            student_state_snapshot=state_values.get("student_state_snapshot"),
            current_node_id=str(state_values.get("current_node_id") or state_values.get("graph_anchor_id") or "").strip(),
        )
        next_node_id = str(next_candidate.get("node_id") or "").strip()
        next_node_name = str(next_candidate.get("name") or "").strip()

    if not next_node_id and not next_node_name:
        return None

    graph_state_patch = build_graph_state_patch(graph_rag_pipeline, next_node_id) if graph_rag_pipeline is not None else {}
    target_name = next_node_name or str(graph_state_patch.get("graph_anchor_title") or "").strip() or next_node_id
    return {
        "flow_status": "normal",
        "learning_phase": "node_selected",
        "learning_resume_target": "tutor",
        "learning_resume_reason": "resume_next_node",
        "current_user_goal": target_name or state_values.get("current_user_goal") or state_values.get("current_topic") or "",
        "turn_goal": target_name or state_values.get("turn_goal") or state_values.get("current_user_goal") or "",
        "topic_focus": target_name or state_values.get("topic_focus") or "",
        "current_node_status": "selected",
        "next_step_choice": "continue_deeper",
        "teaching_strategy": "explain",
        "next_node_candidate_id": next_node_id,
        "next_node_candidate_name": target_name,
        **graph_state_patch,
    }


def _build_consolidation_homework(state_values: dict, runtime_context=None) -> tuple[list[dict], dict]:
    graph_rag_pipeline = getattr(runtime_context, "graph_rag_pipeline", None) if runtime_context is not None else None
    student_state_store = getattr(runtime_context, "student_state_store", None) if runtime_context is not None else None
    student_id = str(state_values.get("student_id") or "default_student").strip() or "default_student"
    homework_items = build_homework_items(
        graph_pipeline=graph_rag_pipeline,
        student_state_snapshot=state_values.get("student_state_snapshot"),
        limit=5,
    )
    updated_snapshot = assign_homework_items(
        student_state_store,
        student_id=student_id,
        homework_items=homework_items,
    )
    return homework_items, updated_snapshot


def _append_interrupt_user_message(history: list, query: str) -> list:
    updated = list(history or [])
    updated.append({"role": "user", "kind": "interruption_user", "content": query})
    return updated


def _clear_interrupt_history(history: list) -> list:
    cleaned = []
    for msg in history or []:
        kind = str(msg.get("kind", ""))
        if kind in {"interruption", "interruption_user"}:
            continue
        if kind.startswith("interruption"):
            continue
        cleaned.append(msg)
    return cleaned


def _should_continue_with_new_turn(state_values: dict, topic: str) -> bool:
    if not state_values or not topic.strip():
        return False
    if state_values.get("is_assessed"):
        return False
    return state_values.get("flow_status") in PRE_TOPIC_FLOW_STATUSES


def _should_restart_with_new_topic(state_values: dict, topic: str) -> bool:
    if not state_values or not topic.strip():
        return False
    if not state_values.get("is_assessed"):
        return False
    if state_values.get("flow_status") == "awaiting_interrupt_confirmation":
        return False
    if _looks_like_interrupt_question(topic):
        return False
    existing_topic = (state_values.get("current_topic") or "").strip()
    if not existing_topic:
        return False
    return existing_topic != topic.strip()


def _looks_like_interrupt_question(text: str) -> bool:
    cleaned = (text or "").strip()
    if not cleaned:
        return False

    lowered = cleaned.lower()
    if lowered in SKIP_COMMANDS or _is_resume_mainline_command(cleaned):
        return True

    if lowered.startswith(ASK_PREFIXES):
        return True

    if any(mark in cleaned for mark in ["?", "？"]):
        return True

    if any(hint in cleaned for hint in QUESTION_HINTS):
        return True

    starts = ("这题", "这个", "那题", "这里", "此处", "它为啥", "为啥")
    if len(cleaned) <= 40 and cleaned.startswith(starts):
        return True

    return False


def run_learning_session(
    app,
    event_sink,
    *,
    thread_id: str,
    topic: str = "",
    current_state=None,
    runtime_context=None,
) -> None:
    thread_config = {"configurable": {"thread_id": thread_id}}
    state_snapshot = current_state or app.get_state(thread_config)

    if state_snapshot and state_snapshot.values:
        state_values = dict(state_snapshot.values)
        state_values.update(build_learning_flow_scaffold(state_values))
        homework_items = list(state_values.get("homework_items") or [])
        homework_status = str(state_values.get("homework_status") or "").strip()

        if homework_items and homework_status in {"assigned", "deferred", "in_progress"}:
            flow_status = str(state_values.get("flow_status") or "").strip()
            pending_kind = str(state_values.get("pending_interaction_kind") or "").strip()
            if not topic.strip():
                if flow_status in {"awaiting_homework_review_choice", "awaiting_homework_answers"} or pending_kind in {
                    "homework_review_choice",
                    "homework_answers",
                }:
                    event_sink.emit(
                        make_event(
                            "session.info",
                            "session",
                            message=_format_homework_message(homework_items),
                            data={"thread_id": thread_id, "homework_status": homework_status, "homework_count": len(homework_items)},
                        )
                    )
                    return

                if homework_status == "deferred":
                    event_sink.emit(
                        make_event(
                            "session.info",
                            "session",
                            message="\n我找到你上次暂缓的作业了。这次先按你上次的选择继续学习，作业仍保留在记录里。",
                            data={"thread_id": thread_id, "homework_status": homework_status, "homework_count": len(homework_items)},
                        )
                    )
                    app.invoke(None, config=thread_config)
                    return

                event_sink.emit(
                    make_event(
                        "session.info",
                        "session",
                        message=_format_homework_message(homework_items),
                        data={"thread_id": thread_id, "homework_status": homework_status, "homework_count": len(homework_items)},
                    )
                )
                app.invoke(
                    {
                        "flow_status": flow_status or "homework_assigned",
                        "learning_phase": "homework_resume",
                        "learning_resume_target": "session_resume_router",
                        "learning_resume_reason": "resume_existing_homework",
                    },
                    config=thread_config,
                )
                return

            if _is_next_node_command(topic):
                resume_payload = _resume_next_node_payload(state_values, runtime_context=runtime_context)
                if resume_payload is not None:
                    event_sink.emit(
                        make_event(
                            "session.info",
                            "session",
                            message="\n这次我先按你的选择跳过作业，直接接到下一个学习节点。",
                            data={"thread_id": thread_id},
                        )
                    )
                    app.invoke(
                        {
                            **resume_payload,
                            "homework_status": "deferred",
                        },
                        config=thread_config,
                    )
                    return

            event_sink.emit(
                make_event(
                    "session.info",
                    "session",
                    message=_format_homework_message(homework_items),
                    data={"thread_id": thread_id, "homework_status": homework_status, "homework_count": len(homework_items)},
                )
            )
            return

        if not homework_items and state_values.get("learning_phase") == "daily_wrapup":
            if not topic.strip():
                event_sink.emit(
                    make_event(
                        "session.info",
                        "session",
                        message="\n上次那轮已经收尾了。你如果想先巩固，可以直接回复“先巩固”或“复习”；如果想直接继续新节点，回复“继续学习”即可。",
                        data={"thread_id": thread_id},
                    )
                )
                return

            if _is_consolidate_command(topic):
                generated_homework, updated_snapshot = _build_consolidation_homework(
                    state_values,
                    runtime_context=runtime_context,
                )
                if generated_homework:
                    event_sink.emit(
                        make_event(
                            "session.info",
                            "session",
                            message="\n我已经按你之前学过的节点生成了一组巩固作业。",
                            data={"thread_id": thread_id, "homework_count": len(generated_homework)},
                        )
                    )
                    app.update_state(
                        thread_config,
                        {
                            "homework_items": generated_homework,
                            "homework_status": "assigned",
                            "student_state_snapshot": updated_snapshot or state_values.get("student_state_snapshot") or {},
                        },
                    )
                    event_sink.emit(
                        make_event(
                            "session.info",
                            "session",
                            message=_format_homework_message(generated_homework),
                            data={"thread_id": thread_id, "homework_status": "assigned", "homework_count": len(generated_homework)},
                        )
                    )
                    return

            if _is_next_node_command(topic):
                resume_payload = _resume_next_node_payload(state_values, runtime_context=runtime_context)
                if resume_payload is not None:
                    event_sink.emit(
                        make_event(
                            "session.info",
                            "session",
                            message="\n好，这次直接从下一个图谱节点继续。",
                            data={"thread_id": thread_id},
                        )
                    )
                    app.invoke(resume_payload, config=thread_config)
                    return

        if _should_restart_with_new_topic(state_values, topic):
            event_sink.emit(
                make_event(
                    "session.info",
                    "session",
                    message="\n我听出来你已经切到一个新主题了，系统将基于当前线程重启一轮完整学习流程。",
                    data={
                        "thread_id": thread_id,
                        "old_topic": state_values.get("current_topic", ""),
                        "new_topic": topic,
                    },
                )
            )
            app.invoke(build_initial_state(topic), config=thread_config)
            return

        if (
            state_values.get("is_assessed")
            and state_values.get("flow_status") == "awaiting_interrupt_confirmation"
        ):
            if not topic.strip():
                event_sink.emit(
                    make_event(
                        "session.info",
                        "session",
                        message="\n刚才那个临时问题已经解释完了。你可以输入“继续”或“回到主线”，也可以顺着这个点再追问一句。",
                        data={"thread_id": thread_id, "requires_interrupt_confirmation": True},
                    )
                )
                return

            if _is_resume_mainline_command(topic) or _is_skip_command(topic):
                cleaned_history = _clear_interrupt_history(
                    state_values.get("conversation_history", [])
                )
                resume_tester = bool(state_values.get("tester_question"))
                event_sink.emit(
                    make_event(
                        "session.info",
                        "session",
                        message="\n好，我们回到主线，继续刚才的教学和测评。",
                        data={"thread_id": thread_id},
                    )
                )
                app.invoke(
                    {
                        "flow_status": "normal",
                        "interrupt_query": "",
                        "resume_tester": resume_tester,
                        "learning_phase": "node_quiz_batch" if resume_tester else "post_lesson_choice",
                        "learning_resume_target": "tester" if resume_tester else "post_lesson_choice",
                        "learning_resume_reason": "interrupt_confirmed",
                        "skip_reason": "",
                        "user_answer": "",
                        "conversation_history": cleaned_history,
                    },
                    config=thread_config,
                )
                return

            query = topic.strip()
            if query.lower().startswith("/ask"):
                query = query[4:].strip() or topic.strip()
            history = _append_interrupt_user_message(
                state_values.get("conversation_history", []),
                query,
            )
            event_sink.emit(
                make_event(
                    "session.info",
                    "session",
                    message="\n这个追问我收到了。我先把眼前这个卡点讲清楚，讲完再陪你决定要不要回主线。",
                    data={"thread_id": thread_id, "query": query},
                )
            )
            app.invoke(
                {
                    "interrupt_query": query,
                    "learning_phase": "node_temp_qna",
                    "learning_resume_target": "interruption_tutor",
                    "learning_resume_reason": "interrupt_followup",
                    "resume_tester": bool(state_values.get("resume_tester", True)),
                    "skip_reason": "",
                    "user_answer": "",
                    "conversation_history": history,
                },
                config=thread_config,
            )
            return

        if state_values.get("is_assessed") and _is_skip_command(topic):
            event_sink.emit(
                make_event(
                    "session.info",
                    "session",
                    message="\n好，这一题先不死磕了，我们继续下一轮主线教学。",
                    data={"thread_id": thread_id},
                )
            )
            app.update_state(
                thread_config,
                {
                    "flow_status": "normal",
                    "interrupt_query": "",
                    "resume_tester": False,
                    "learning_phase": "node_teaching",
                    "learning_resume_target": "next_step_selector",
                    "learning_resume_reason": "skip_current_question",
                    "skip_reason": topic.strip(),
                    "user_answer": "",
                },
            )
            app.invoke(
                {
                    "flow_status": "normal",
                    "interrupt_query": "",
                    "resume_tester": False,
                    "learning_phase": "node_teaching",
                    "learning_resume_target": "next_step_selector",
                    "learning_resume_reason": "skip_current_question",
                    "skip_reason": topic.strip(),
                    "user_answer": "",
                },
                config=thread_config,
            )
            return

        if state_values.get("is_assessed") and topic.strip():
            query = topic.strip()
            # 只有用户明确提问（含问号、/ask 前缀、疑问词）才进入临时中断
            # 跳过/继续等指令不算提问，应走正常恢复流程
            is_question = (
                _looks_like_interrupt_question(query)
                and not _is_skip_command(query)
                and not _is_resume_mainline_command(query)
                and not _is_next_node_command(query)
            )
            if is_question:
                if query.lower().startswith("/ask"):
                    query = query[4:].strip() or topic.strip()
                history = _append_interrupt_user_message(
                    state_values.get("conversation_history", []),
                    query,
                )

                event_sink.emit(
                    make_event(
                        "session.info",
                        "session",
                        message="\n我先处理你这个临时问题，讲清楚后再把你带回主线。",
                        data={"thread_id": thread_id, "query": query},
                    )
                )
                app.invoke(
                    {
                        "interrupt_query": query,
                        "learning_phase": "node_temp_qna",
                        "learning_resume_target": "interruption_tutor",
                        "learning_resume_reason": "interrupt_from_mainline",
                        "resume_tester": bool(state_values.get("tester_question")),
                        "skip_reason": "",
                        "user_answer": "",
                        "conversation_history": history,
                    },
                    config=thread_config,
                )
                return

            # 非提问式输入：作为正常回复投递到当前流程节点
            event_sink.emit(
                make_event(
                    "session.info",
                    "session",
                    message="\n好，收到了你的回复。",
                    data={"thread_id": thread_id},
                )
            )
            app.update_state(
                thread_config,
                {
                    "user_answer": query,
                    "pending_interaction_answer": query,
                },
            )
            app.invoke(None, config=thread_config)
            return

        if _should_continue_with_new_turn(state_values, topic):
            event_sink.emit(
                make_event(
                    "session.info",
                    "session",
                    message="\n我找到你上次停下的位置了。这次会按你刚输入的新内容继续当前会话。",
                    data={"thread_id": thread_id, "topic": topic},
                )
            )
            app.invoke(build_initial_state(topic), config=thread_config)
            return

        if state_values.get("flow_status") in PRE_TOPIC_FLOW_STATUSES:
            event_sink.emit(
                make_event(
                    "session.info",
                    "session",
                    message="\n我找到这页旧记录了。当前还停在主题沟通阶段，你直接发下一条消息，我就顺着接。",
                    data={"thread_id": thread_id},
                )
            )
            return

        event_sink.emit(
            make_event(
                "session.info",
                "session",
                message="\n我找到你上次的学习进度了，系统将从上次进度继续。",
                data={"thread_id": thread_id},
            )
        )
        app.invoke(None, config=thread_config)
        return

    event_sink.emit(
        make_event(
            "session.info",
            "session",
            message="\n这是一个全新的学习页，我们从头把这轮内容理顺。",
            data={"thread_id": thread_id},
        )
    )
    app.invoke(build_initial_state(topic), config=thread_config)

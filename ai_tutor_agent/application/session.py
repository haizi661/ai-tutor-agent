from ..core.events import make_event
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
) -> None:
    thread_config = {"configurable": {"thread_id": thread_id}}
    state_snapshot = current_state or app.get_state(thread_config)

    if state_snapshot and state_snapshot.values:
        if _should_restart_with_new_topic(state_snapshot.values, topic):
            event_sink.emit(
                make_event(
                    "session.info",
                    "session",
                    message="\n我听出来你已经切到一个新主题了，系统将基于当前线程重启一轮完整学习流程。",
                    data={
                        "thread_id": thread_id,
                        "old_topic": state_snapshot.values.get("current_topic", ""),
                        "new_topic": topic,
                    },
                )
            )
            app.invoke(build_initial_state(topic), config=thread_config)
            return

        if (
            state_snapshot.values.get("is_assessed")
            and state_snapshot.values.get("flow_status") == "awaiting_interrupt_confirmation"
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
                    state_snapshot.values.get("conversation_history", [])
                )
                resume_tester = bool(state_snapshot.values.get("tester_question"))
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
                state_snapshot.values.get("conversation_history", []),
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
                    "resume_tester": bool(state_snapshot.values.get("resume_tester", True)),
                    "skip_reason": "",
                    "user_answer": "",
                    "conversation_history": history,
                },
                config=thread_config,
            )
            return

        if state_snapshot.values.get("is_assessed") and _is_skip_command(topic):
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
                    "skip_reason": topic.strip(),
                    "user_answer": "",
                },
            )
            app.invoke(
                {
                    "flow_status": "normal",
                    "interrupt_query": "",
                    "resume_tester": False,
                    "skip_reason": topic.strip(),
                    "user_answer": "",
                },
                config=thread_config,
            )
            return

        if state_snapshot.values.get("is_assessed") and topic.strip():
            query = topic.strip()
            if query.lower().startswith("/ask"):
                query = query[4:].strip() or topic.strip()
            history = _append_interrupt_user_message(
                state_snapshot.values.get("conversation_history", []),
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
                    "resume_tester": bool(state_snapshot.values.get("tester_question")),
                    "skip_reason": "",
                    "user_answer": "",
                    "conversation_history": history,
                },
                config=thread_config,
            )
            return

        if _should_continue_with_new_turn(state_snapshot.values, topic):
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

        if state_snapshot.values.get("flow_status") in PRE_TOPIC_FLOW_STATUSES:
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

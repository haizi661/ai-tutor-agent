from ..core.events import make_event
from ..core.state import build_initial_state


PRE_TOPIC_FLOW_STATUSES = {
    "greeting",
    "topic_intake",
    "meta_qa",
    "smalltalk",
}

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
    return any(token in normalized for token in ["继续", "回到主线", "返回主线", "继续学习", "继续主线"])


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
        if _should_continue_with_new_turn(state_snapshot.values, topic):
            event_sink.emit(
                make_event(
                    "session.info",
                    "session",
                    message="\n📂 检测到历史存档！本次将按你刚输入的新内容继续当前会话。",
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
                    message="\n📂 检测到历史存档！当前会话还停留在主题沟通阶段，请直接输入下一条消息继续。",
                    data={"thread_id": thread_id},
                )
            )
            return

        # 临时问答结束后，必须用户确认才回主线。
        if state_snapshot.values.get("is_assessed") and state_snapshot.values.get("flow_status") == "awaiting_interrupt_confirmation":
            if not topic.strip():
                event_sink.emit(
                    make_event(
                        "session.info",
                        "session",
                        message="\nℹ️ 已完成临时解答。请输入“继续”或“回到主线”以恢复教学主线。",
                        data={"thread_id": thread_id},
                    )
                )
                return

            if _is_resume_mainline_command(topic) or _is_skip_command(topic):
                cleaned_history = _clear_interrupt_history(state_snapshot.values.get("conversation_history", []))
                event_sink.emit(
                    make_event(
                        "session.info",
                        "session",
                        message="\n✅ 已确认，正在回到主线继续教学与测评。",
                        data={"thread_id": thread_id},
                    )
                )
                app.invoke(
                    {
                        "flow_status": "normal",
                        "interrupt_query": "",
                        "resume_tester": False,
                        "skip_reason": "",
                        "user_answer": "",
                        "conversation_history": cleaned_history,
                    },
                    config=thread_config,
                )
                return

            # Non-confirmation input in this stage is treated as another
            # temporary question, and we keep the same confirmation loop.
            query = topic.strip()
            if query.lower().startswith("/ask"):
                query = query[4:].strip() or topic.strip()
            history = _append_interrupt_user_message(state_snapshot.values.get("conversation_history", []), query)
            event_sink.emit(
                make_event(
                    "session.info",
                    "session",
                    message="\n💬 已收到新的临时问题，先解答后再确认是否回主线。",
                    data={"thread_id": thread_id, "query": query},
                )
            )
            app.invoke(
                {
                    "interrupt_query": query,
                    "resume_tester": False,
                    "skip_reason": "",
                    "user_answer": "",
                    "conversation_history": history,
                },
                config=thread_config,
            )
            return

        # 已测评状态下，skip 属于控制指令：继续主线，不当作临时提问。
        if state_snapshot.values.get("is_assessed") and _is_skip_command(topic):
            event_sink.emit(
                make_event(
                    "session.info",
                    "session",
                    message="\n✅ 已收到跳过指令，继续下一轮主线教学。",
                    data={"thread_id": thread_id},
                )
            )
            app.update_state(
                thread_config,
                {
                    "flow_status": "normal",
                    "interrupt_query": "",
                    "resume_tester": False,
                    "skip_reason": "",
                    "user_answer": "",
                },
            )
            app.invoke(
                {
                    "flow_status": "normal",
                    "interrupt_query": "",
                    "resume_tester": False,
                    "skip_reason": "",
                    "user_answer": "",
                },
                config=thread_config,
            )
            return

        if state_snapshot.values.get("is_assessed") and topic.strip():
            query = topic.strip()
            if query.lower().startswith("/ask"):
                query = query[4:].strip() or topic.strip()
            history = _append_interrupt_user_message(state_snapshot.values.get("conversation_history", []), query)

            event_sink.emit(
                make_event(
                    "session.info",
                    "session",
                    message="\n💬 收到临时问题，先解答后回到主线。",
                    data={"thread_id": thread_id, "query": query},
                )
            )
            # Use explicit input invoke to force entry-point re-routing.
            # This avoids accidentally continuing from a stale checkpoint edge.
            app.invoke(
                {
                    "interrupt_query": query,
                    "resume_tester": False,
                    "skip_reason": "",
                    "user_answer": "",
                    "conversation_history": history,
                },
                config=thread_config,
            )
            return

        event_sink.emit(
            make_event(
                "session.info",
                "session",
                message="\n📂 检测到历史存档！系统将从上次进度继续...",
                data={"thread_id": thread_id},
            )
        )
        app.invoke(None, config=thread_config)
        return

    event_sink.emit(
        make_event(
            "session.info",
            "session",
            message="\n🆕 这是一个全新的学习存档。",
            data={"thread_id": thread_id},
        )
    )
    app.invoke(build_initial_state(topic), config=thread_config)

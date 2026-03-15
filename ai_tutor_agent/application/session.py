from ..core.events import make_event
from ..core.state import build_initial_state


PRE_TOPIC_FLOW_STATUSES = {
    "greeting",
    "topic_intake",
    "meta_qa",
    "smalltalk",
}


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
    existing_topic = (state_values.get("current_topic") or "").strip()
    if not existing_topic:
        return False
    return existing_topic != topic.strip()


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
                    message="\n🔄 检测到你输入了新主题，系统将基于当前线程重启一轮完整学习流程。",
                    data={
                        "thread_id": thread_id,
                        "old_topic": state_snapshot.values.get("current_topic", ""),
                        "new_topic": topic,
                    },
                )
            )
            app.invoke(build_initial_state(topic), config=thread_config)
            return

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

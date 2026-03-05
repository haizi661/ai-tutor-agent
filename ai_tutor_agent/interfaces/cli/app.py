from ...application.session import run_learning_session
from ...config import get_settings
from ...core.events import make_event
from ...core.ports import RuntimeContext, UserAbortError
from ...orchestration.workflow import create_app_with_sqlite_checkpointer
from .adapter import CliAnswerProvider, CliEventSink


def run_cli() -> None:
    settings = get_settings()
    event_sink = CliEventSink()
    answer_provider = CliAnswerProvider()
    runtime = RuntimeContext(event_sink=event_sink, answer_provider=answer_provider)

    print("🚀 高阶动态伴学系统 v5.0 (流式交互+多维画像+持久化记忆版) 启动成功！")
    print("\n" + "*" * 50)
    print("欢迎来到专属伴学空间。")

    app, conn = create_app_with_sqlite_checkpointer(settings, runtime=runtime)

    try:
        thread_input = input(
            f"👉 请输入学习存档 thread_id (默认: {settings.default_thread_id})：\n>> "
        ).strip()
        thread_id = thread_input or settings.default_thread_id

        current_state = app.get_state({"configurable": {"thread_id": thread_id}})
        topic_input = ""
        if not (current_state and current_state.values):
            topic_input = input("👉 请输入你今天想深入学习的具体知识点：\n>> ").strip()
            while not topic_input:
                topic_input = input("知识点不能为空，请重新输入：\n>> ").strip()

        run_learning_session(
            app,
            event_sink,
            thread_id=thread_id,
            topic=topic_input,
            current_state=current_state,
        )
    except UserAbortError as exc:
        event_sink.emit(
            make_event(
                "session.info",
                "cli",
                message=str(exc),
            )
        )
    finally:
        conn.close()

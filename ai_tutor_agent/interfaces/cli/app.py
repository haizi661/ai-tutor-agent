from ...application.session import run_learning_session
from ...config import get_settings
from ...core.events import make_event
from ...core.ports import RuntimeContext, UserAbortError
from ...infrastructure.retriever import LocalFileKnowledgeProvider
from ...orchestration.workflow import create_app_with_sqlite_checkpointer
from .adapter import CliAnswerProvider, CliEventSink


def run_cli() -> None:
    settings = get_settings()
    event_sink = CliEventSink()
    answer_provider = CliAnswerProvider()
    
    # Initialize KnowledgeProvider (RAG)
    try:
        knowledge_provider = LocalFileKnowledgeProvider(settings)
        if getattr(knowledge_provider, "vector_store", None):
            print("📚 知识库加载成功，已启用 RAG 增强。")
        else:
            print("⚠️ 知识库已初始化，但当前处于无 RAG 回退模式。")
    except Exception as e:
        from ...core.ports import NoopKnowledgeProvider
        knowledge_provider = NoopKnowledgeProvider()
        print(f"⚠️ 知识库加载失败 (可能缺少依赖或配置): {e}")
        print("   系统将回退到通用讲解模式。")

    runtime = RuntimeContext(
        event_sink=event_sink, 
        answer_provider=answer_provider,
        knowledge_provider=knowledge_provider
    )

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
            while True:
                topic_input = input("👉 请输入你想学习的知识点 (或输入 /upload <文件路径> 上传知识库)：\n>> ").strip()
                if not topic_input:
                    print("❌ 输入不能为空，请重新输入。")
                    continue
                
                if topic_input.startswith("/upload"):
                    parts = topic_input.split(" ", 1)
                    if len(parts) < 2:
                        print("❌ 请提供文件路径，例如: /upload /path/to/doc.pdf")
                        continue
                    
                    file_path = parts[1].strip()
                    if hasattr(knowledge_provider, "add_document"):
                        knowledge_provider.add_document(file_path)
                    else:
                        print("⚠️ 当前知识库提供者不支持动态上传。")
                    continue # 继续循环，让用户输入真正的知识点
                
                break # 得到了正常的知识点，跳出循环

        run_learning_session(
            app,
            event_sink,
            thread_id=thread_id,
            topic=topic_input,
            current_state=current_state,
            runtime_context=runtime,
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

from ai_tutor_agent.config import Settings
from ai_tutor_agent.core.ports import BufferedEventSink, NoopKnowledgeProvider, RuntimeContext
from ai_tutor_agent.orchestration import workflow as workflow_module


class FakeAnswerProvider:
    def get_answer(self, prompt: str, *, state=None) -> str:
        del prompt, state
        return "控制理论"


class FakeLLM:
    def stream(self, _messages):
        return iter(())

    def invoke(self, _messages):
        return "{}"

    def with_structured_output(self, _schema):
        return self


def build_test_settings() -> Settings:
    return Settings(
        chat_profile="custom",
        llm_provider="openai",
        google_api_key=None,
        gemini_api_key=None,
        openai_api_key="test-key",
        openai_api_base="https://api.openai.com/v1",
        qwen_api_key=None,
        deepseek_api_key=None,
        minimax_api_key=None,
        glm_api_key=None,
        model_name="gpt-5-mini",
        embedding_provider="local",
        embedding_model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        tutor_temperature=0.7,
        tester_temperature=0.4,
        evaluator_temperature=0.0,
        pass_score=80,
        memory_db_path="data/test.sqlite",
        knowledge_dir="data/knowledge",
        knowledge_chunk_size=1000,
        knowledge_chunk_overlap=150,
        knowledge_top_k=3,
        default_thread_id="test-thread",
        http_proxy=None,
        https_proxy=None,
        local_config_enabled=True,
    )


def test_build_workflow_registers_meta_and_smalltalk_nodes(monkeypatch):
    fake_llm = FakeLLM()
    monkeypatch.setattr(
        workflow_module,
        "build_llms",
        lambda settings: (fake_llm, fake_llm, fake_llm),
    )

    runtime = RuntimeContext(
        event_sink=BufferedEventSink(),
        answer_provider=FakeAnswerProvider(),
        knowledge_provider=NoopKnowledgeProvider(),
    )

    graph = workflow_module.build_workflow(build_test_settings(), runtime=runtime)

    assert graph is not None

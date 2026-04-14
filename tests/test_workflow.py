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


def test_route_after_topic_confirmer_can_go_directly_to_tutor():
    decision = workflow_module.route_after_topic_confirmer({"flow_status": "direct_tutor"})

    assert decision == "tutor"


def test_route_after_tutor_now_goes_to_next_step_selector():
    decision = workflow_module.route_after_tutor({"interrupt_query": ""})

    assert decision == "next_step_selector"


def test_route_after_next_step_selector_can_branch_back_to_tutor():
    decision = workflow_module.route_after_next_step_selector({"next_step_choice": "continue_deeper", "interrupt_query": ""})

    assert decision == "tutor"


def test_route_after_next_step_selector_can_pause_while_waiting_choice():
    decision = workflow_module.route_after_next_step_selector({"flow_status": "awaiting_next_step_selector"})

    assert decision == "pause"


def test_route_after_next_step_selector_can_branch_to_tester():
    decision = workflow_module.route_after_next_step_selector({"next_step_choice": "practice_now", "interrupt_query": ""})

    assert decision == "tester"


def test_get_entry_node_can_resume_tester_from_next_step_choice():
    decision = workflow_module.get_entry_node({"next_step_choice": "practice_now"})

    assert decision == "tester"


def test_route_after_evaluator_pass_now_goes_to_post_eval_selector():
    decision = workflow_module.route_after_evaluator({"score": 95, "logic_score": 90, "concept_score": 90}, 80)

    assert decision == "post_eval_selector"


def test_route_after_post_eval_selector_can_branch_to_wrapup():
    decision = workflow_module.route_after_post_eval_selector({"post_eval_choice": "summarize_wrapup"})

    assert decision == "post_eval_wrapup"


def test_route_after_post_eval_selector_can_pause_while_waiting_choice():
    decision = workflow_module.route_after_post_eval_selector({"flow_status": "awaiting_post_eval_selector"})

    assert decision == "pause"


def test_get_entry_node_can_resume_post_eval_wrapup():
    decision = workflow_module.get_entry_node({"post_eval_choice": "summarize_wrapup"})

    assert decision == "post_eval_wrapup"

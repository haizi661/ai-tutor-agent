from ai_tutor_agent.config import Settings
from ai_tutor_agent.core.ports import BufferedEventSink
from ai_tutor_agent.nodes.intake import build_intake_router_node, classify_intent
from ai_tutor_agent.nodes.meta import build_meta_node
from ai_tutor_agent.nodes.smalltalk import build_smalltalk_node


class _Chunk:
    def __init__(self, content: str):
        self.content = content


class FakeLLM:
    def __init__(self, response_text: str):
        self.response_text = response_text

    def stream(self, _messages):
        yield _Chunk(self.response_text)


class FakeAnswerProvider:
    def __init__(self, answer: str):
        self.answer = answer
        self.prompts = []

    def get_answer(self, prompt: str, *, state=None) -> str:
        self.prompts.append(prompt)
        return self.answer


def build_test_settings() -> Settings:
    return Settings(
        chat_profile="gemini",
        llm_provider="openai",
        google_api_key=None,
        gemini_api_key=None,
        openai_api_key="google-compatible-key",
        openai_api_base="https://generativelanguage.googleapis.com/v1beta/openai/",
        qwen_api_key=None,
        deepseek_api_key=None,
        minimax_api_key=None,
        glm_api_key=None,
        model_name="gemini-2.5-pro",
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


def test_classify_intent_routes_meta_and_smalltalk_and_study():
    assert classify_intent("你好，你是什么模型呢") == "meta_qa"
    assert classify_intent("可以切换什么模型呢") == "meta_qa"
    assert classify_intent("当前支持哪些模型") == "meta_qa"
    assert classify_intent("你好") == "smalltalk"
    assert classify_intent("高等数学") == "study_topic"
    assert classify_intent("我想学 API 设计") == "study_topic"


def test_classify_intent_boundary_cases():
    assert classify_intent("你能做什么") == "meta_qa"
    assert classify_intent("这个项目支持哪些模型") == "meta_qa"
    assert classify_intent("谢谢你") == "smalltalk"
    assert classify_intent("在吗") == "smalltalk"
    assert classify_intent("讲讲控制理论的稳定性") == "study_topic"
    assert classify_intent("为什么 PID 会震荡") == "study_topic"


def test_intake_router_sets_meta_flow_status():
    sink = BufferedEventSink()
    node = build_intake_router_node(sink)

    result = node({"current_topic": "你是什么模型呢"})

    assert result["flow_status"] == "meta_qa"
    assert any(event.type == "intent.detected" for event in sink.events)


def test_meta_node_answers_and_requests_next_input():
    sink = BufferedEventSink()
    answer_provider = FakeAnswerProvider("高等数学")
    llm = FakeLLM("当前是 Gemini 档案，模型是 gemini-2.5-pro。你可以继续提问，或者直接开始学习主题。")
    node = build_meta_node(build_test_settings(), llm, sink, answer_provider)

    result = node({"current_topic": "你是什么模型呢"})

    assert result["current_topic"] == "高等数学"
    assert result["flow_status"] == "greeting"
    streamed = "".join(event.data.get("text", "") for event in sink.events if event.type == "node.stream")
    assert "gemini-2.5-pro" in streamed
    assert "Gemini" in streamed
    assert "准备开始学点什么" in answer_provider.prompts[0]


def test_smalltalk_node_answers_and_requests_next_input():
    sink = BufferedEventSink()
    answer_provider = FakeAnswerProvider("控制理论")
    llm = FakeLLM("我在这。你可以先说说今天最想弄懂哪一个点，我们一起拆开。")
    node = build_smalltalk_node(llm, sink, answer_provider)

    result = node({"current_topic": "你好"})

    assert result["current_topic"] == "控制理论"
    assert result["flow_status"] == "greeting"
    streamed = "".join(event.data.get("text", "") for event in sink.events if event.type == "node.stream")
    assert "我在" in streamed
    assert "随时可以告诉我想学的主题" in answer_provider.prompts[0]

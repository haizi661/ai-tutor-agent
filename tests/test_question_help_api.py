from types import SimpleNamespace

from langchain_core.messages import AIMessage

from ai_tutor_agent.config import Settings
from ai_tutor_agent.core.ports import NoopKnowledgeProvider
from ai_tutor_agent.interfaces.api.app import create_api_app
from ai_tutor_agent.interfaces.api import question_help as question_help_module
from ai_tutor_agent.knowledge_map.student_state import StudentStateStore
from tests.asgi_test_client import SyncASGITestClient


class FakeLLM:
    def __init__(self, answer: str = "这道题应先识别反馈通道，再判断比较点符号。"):
        self.answer = answer
        self.calls = []

    def invoke(self, messages):
        self.calls.append(messages)
        return AIMessage(content=self.answer)


def _client(tmp_path, llm=None):
    runtime = SimpleNamespace(
        settings=SimpleNamespace(),
        knowledge_provider=NoopKnowledgeProvider(),
        student_state_store=StudentStateStore(tmp_path / "student_states"),
        question_help_llm=llm or FakeLLM(),
    )
    app = create_api_app(runtime_factory=lambda: runtime)
    return SyncASGITestClient(app), runtime


def _deepseek_main_settings(tmp_path):
    return Settings(
        chat_profile="deepseek",
        llm_provider="openai",
        google_api_key=None,
        gemini_api_key=None,
        openai_api_key="deepseek-key",
        openai_api_base="https://api.deepseek.com/v1",
        qwen_api_key="qwen-key",
        deepseek_api_key="deepseek-key",
        minimax_api_key=None,
        glm_api_key=None,
        model_name="deepseek-v4-flash",
        embedding_provider="local",
        embedding_model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        tutor_temperature=0.7,
        tester_temperature=0.4,
        evaluator_temperature=0.0,
        pass_score=80,
        memory_db_path=str(tmp_path / "memory.sqlite"),
        knowledge_dir=str(tmp_path / "knowledge"),
        knowledge_chunk_size=1000,
        knowledge_chunk_overlap=150,
        knowledge_top_k=3,
        default_thread_id="test-thread",
        http_proxy=None,
        https_proxy=None,
        local_config_enabled=True,
    )


def test_question_help_accepts_text_and_image_and_keeps_answer_history(tmp_path):
    client, runtime = _client(tmp_path)

    with client:
        response = client.post(
            "/api/students/s1/question-help",
            data={"question_text": "这道负反馈题怎么判断？"},
            files={"images": ("feedback.png", b"fake-png", "image/png")},
        )
        assert response.status_code == 200
        payload = response.json()

        assert payload["record"]["question_text"] == "这道负反馈题怎么判断？"
        assert payload["record"]["answer"] == "这道题应先识别反馈通道，再判断比较点符号。"
        assert payload["record"]["images"][0]["filename"] == "feedback.png"
        assert payload["record"]["image_count"] == 1
        assert len(payload["records"]) == 1
        # Default: no node context
        assert payload["record"].get("node_id") == ""
        assert payload["record"].get("node_name") == ""

        history = client.get("/api/students/s1/question-help")
        assert history.status_code == 200
        assert history.json()["items"][0]["answer"] == payload["record"]["answer"]

    llm_content = runtime.question_help_llm.calls[0][1].content
    assert isinstance(llm_content, list)
    assert any(part.get("type") == "text" and "这道负反馈题怎么判断" in part.get("text", "") for part in llm_content)
    assert any(
        part.get("type") == "image_url"
        and part.get("image_url", {}).get("url", "").startswith("data:image/png;base64,")
        for part in llm_content
    )


def test_question_help_injects_node_context(tmp_path):
    client, runtime = _client(tmp_path)

    with client:
        response = client.post(
            "/api/students/s1/question-help",
            data={
                "question_text": "这个传递函数怎么化简？",
                "current_node_id": "KM003",
                "current_node_name": "传递函数与方块图",
            },
        )
        assert response.status_code == 200
        payload = response.json()

        assert payload["record"]["node_id"] == "KM003"
        assert payload["record"]["node_name"] == "传递函数与方块图"
        assert payload["record"]["question_text"] == "这个传递函数怎么化简？"

    # Verify node context appears in LLM prompt
    llm_content = runtime.question_help_llm.calls[0][1].content
    assert isinstance(llm_content, list)
    text = " ".join(
        part.get("text", "") for part in llm_content if isinstance(part, dict)
    )
    assert "KM003" in text
    assert "传递函数与方块图" in text


def test_question_help_prompt_requires_renderable_math_and_student_facing_structure(tmp_path):
    client, runtime = _client(tmp_path)

    with client:
        response = client.post(
            "/api/students/s1/question-help",
            data={"question_text": "传递函数 G(s)=C(s)/R(s) 怎么理解？"},
        )
        assert response.status_code == 200

    llm_content = runtime.question_help_llm.calls[0][1].content
    assert isinstance(llm_content, list)
    text = " ".join(part.get("text", "") for part in llm_content if isinstance(part, dict))
    assert "考点" in text
    assert "关键步骤" in text
    assert "最终答案" in text
    assert "公式必须使用 Markdown/LaTeX" in text
    assert "$$" in text


def test_question_help_prompt_requires_strict_sections_and_choice_analysis(tmp_path):
    client, runtime = _client(tmp_path)

    with client:
        response = client.post(
            "/api/students/s1/question-help",
            data={"question_text": "1. 下列哪项是负反馈？A. 输出回到输入端相减 B. 输出回到输入端相加"},
        )
        assert response.status_code == 200

    llm_content = runtime.question_help_llm.calls[0][1].content
    text = " ".join(part.get("text", "") for part in llm_content if isinstance(part, dict))
    assert "### 考点" in text
    assert "### 解题步骤" in text
    assert "### 最终答案" in text
    assert "### 易错提醒" in text
    assert "单段不要超过" in text
    assert "如果是选择题" in text
    assert "选项字母和选项原文" in text


def test_question_help_accepts_answer_mode_and_records_mode_label(tmp_path):
    client, runtime = _client(tmp_path)

    with client:
        response = client.post(
            "/api/students/s1/question-help",
            data={
                "question_text": "反馈系统稳定性怎么判断？",
                "answer_mode": "deep",
            },
        )
        assert response.status_code == 200
        payload = response.json()

    assert payload["record"]["answer_mode"] == "deep"
    assert payload["record"]["answer_mode_label"] == "深度解析"

    llm_content = runtime.question_help_llm.calls[0][1].content
    text = " ".join(part.get("text", "") for part in llm_content if isinstance(part, dict))
    assert "当前解答方式：深度解析" in text
    assert "推导" in text


def test_question_help_requires_text_or_image(tmp_path):
    client, _runtime = _client(tmp_path)

    with client:
        response = client.post("/api/students/s1/question-help", data={"question_text": ""})

    assert response.status_code == 400


def test_question_help_defaults_to_qwen_multimodal_model_independent_from_main_chat(tmp_path, monkeypatch):
    captured = []

    def fake_build_llms(settings):
        captured.append(settings)
        fake_llm = FakeLLM("题材答疑回答")
        return fake_llm, fake_llm, fake_llm

    monkeypatch.setattr(question_help_module, "build_llms", fake_build_llms)
    runtime = SimpleNamespace(
        settings=_deepseek_main_settings(tmp_path),
        knowledge_provider=NoopKnowledgeProvider(),
        student_state_store=StudentStateStore(tmp_path / "student_states"),
    )
    app = create_api_app(runtime_factory=lambda: runtime)
    client = SyncASGITestClient(app)

    with client:
        response = client.post(
            "/api/students/s1/question-help",
            data={"question_text": "什么是深度学习？"},
        )

    assert response.status_code == 200
    assert response.json()["record"]["answer"] == "题材答疑回答"
    # 纯文本题优先走主聊天模型（非 Qwen）
    main_settings = captured[0]
    assert main_settings.chat_profile == "deepseek"
    assert main_settings.llm_provider == "openai"
    assert main_settings.openai_api_key == "deepseek-key"

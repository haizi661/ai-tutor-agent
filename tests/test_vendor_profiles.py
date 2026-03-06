import ai_tutor_agent.config as config_module
from ai_tutor_agent.config import get_settings
from ai_tutor_agent.interfaces.api.runtime import CHAT_PROFILES, build_chat_profiles


def test_vendor_catalog_includes_minimax_and_glm():
    assert "minimax" in CHAT_PROFILES
    assert "glm" in CHAT_PROFILES
    assert any(model["id"] == "MiniMax-M2.5" for model in CHAT_PROFILES["minimax"]["models"])
    assert any(model["id"] == "glm-5" for model in CHAT_PROFILES["glm"]["models"])


def test_settings_support_minimax_profile(monkeypatch):
    monkeypatch.setattr(config_module, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setenv("CHAT_PROFILE", "minimax")
    monkeypatch.setenv("MINIMAX_API_KEY", "minimax-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("QWEN_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("GLM_API_KEY", raising=False)
    monkeypatch.delenv("MODEL_NAME", raising=False)
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.chat_profile == "minimax"
    assert settings.openai_api_base == "https://api.minimaxi.com/v1"
    assert settings.model_name == "MiniMax-M2.5"
    assert settings.openai_api_key == "minimax-key"
    get_settings.cache_clear()


def test_settings_support_glm_profile(monkeypatch):
    monkeypatch.setattr(config_module, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setenv("CHAT_PROFILE", "glm")
    monkeypatch.setenv("GLM_API_KEY", "glm-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("QWEN_API_KEY", raising=False)
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    monkeypatch.delenv("MODEL_NAME", raising=False)
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.chat_profile == "glm"
    assert settings.openai_api_base == "https://open.bigmodel.cn/api/paas/v4"
    assert settings.model_name == "glm-5"
    assert settings.openai_api_key == "glm-key"
    get_settings.cache_clear()


def test_google_compatible_key_does_not_mark_openai_vendor_configured(tmp_path):
    from ai_tutor_agent.config import Settings

    settings = Settings(
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
        embedding_model_name="sentence-transformers/all-MiniLM-L6-v2",
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

    profiles = {profile["id"]: profile for profile in build_chat_profiles(settings)}

    assert profiles["gemini"]["configured"] is True
    assert profiles["openai"]["configured"] is False

import ai_tutor_agent.config as config_module
from ai_tutor_agent.config import get_settings


def test_settings_default_to_local_embedding_provider(monkeypatch):
    monkeypatch.setattr(config_module, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.delenv("CHAT_PROFILE", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_BASE", raising=False)
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("MODEL_NAME", raising=False)
    monkeypatch.delenv("EMBEDDING_PROVIDER", raising=False)
    monkeypatch.delenv("EMBEDDING_MODEL_NAME", raising=False)
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    monkeypatch.delenv("GLM_API_KEY", raising=False)
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.llm_provider == "google"
    assert settings.embedding_provider == "local"
    assert settings.embedding_model_name == "sentence-transformers/all-MiniLM-L6-v2"
    get_settings.cache_clear()


def test_settings_default_google_embedding_model_when_embedding_provider_is_google(monkeypatch):
    monkeypatch.setattr(config_module, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.delenv("CHAT_PROFILE", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    monkeypatch.setenv("LLM_PROVIDER", "google")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "google")
    monkeypatch.delenv("EMBEDDING_MODEL_NAME", raising=False)
    monkeypatch.delenv("MINIMAX_API_KEY", raising=False)
    monkeypatch.delenv("GLM_API_KEY", raising=False)
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.embedding_provider == "google"
    assert settings.embedding_model_name == "models/text-embedding-004"
    get_settings.cache_clear()


def test_settings_dashscope_embedding_requires_key(monkeypatch):
    monkeypatch.setattr(config_module, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.delenv("CHAT_PROFILE", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "dashscope")
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    get_settings.cache_clear()

    try:
        get_settings()
        assert False, "Expected RuntimeError when DASHSCOPE_API_KEY is missing"
    except RuntimeError as exc:
        assert "DASHSCOPE_API_KEY" in str(exc)
    finally:
        get_settings.cache_clear()


def test_settings_dashscope_embedding_default_model(monkeypatch):
    monkeypatch.setattr(config_module, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.delenv("CHAT_PROFILE", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "dashscope")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "dashscope-key")
    monkeypatch.delenv("EMBEDDING_MODEL_NAME", raising=False)
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.embedding_provider == "dashscope"
    assert settings.embedding_model_name == "text-embedding-v2"
    get_settings.cache_clear()


def test_settings_rag_flags_and_mineru_token(monkeypatch):
    monkeypatch.setattr(config_module, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.delenv("CHAT_PROFILE", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "local")
    monkeypatch.setenv("RAG_HYBRID_ENABLED", "true")
    monkeypatch.setenv("RAG_MINERU_ENABLED", "true")
    monkeypatch.setenv("MINERU_API_TOKEN", "mineru-token")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.rag_hybrid_enabled is True
    assert settings.rag_mineru_enabled is True
    assert settings.mineru_api_token == "mineru-token"
    get_settings.cache_clear()


def test_settings_rag_flags_default_false(monkeypatch):
    monkeypatch.setattr(config_module, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.delenv("CHAT_PROFILE", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "local")
    monkeypatch.delenv("RAG_HYBRID_ENABLED", raising=False)
    monkeypatch.delenv("RAG_MINERU_ENABLED", raising=False)
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.rag_hybrid_enabled is False
    assert settings.rag_mineru_enabled is False
    get_settings.cache_clear()

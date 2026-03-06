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

import ai_tutor_agent.config as config_module
from ai_tutor_agent.config import get_settings


def _clear_runtime_env(monkeypatch):
    for key in [
        "CHAT_PROFILE",
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
        "OPENAI_API_KEY",
        "OPENAI_API_BASE",
        "LLM_PROVIDER",
        "MODEL_NAME",
        "EMBEDDING_PROVIDER",
        "EMBEDDING_MODEL_NAME",
        "MINIMAX_API_KEY",
        "GLM_API_KEY",
        "PDF_PARSE_BACKEND",
        "MINERU_PROXY_MODE",
        "MINERU_HTTP_PROXY",
        "MINERU_HTTPS_PROXY",
        "MINERU_PUBLIC_DNS_BYPASS_ENABLED",
        "MINERU_PUBLIC_DNS_SERVER",
        "MINERU_PUBLIC_DNS_PORT",
        "MINERU_PUBLIC_DNS_HOSTS",
        "RETRIEVAL_REWRITE_ENABLED",
        "RETRIEVAL_REWRITE_MODE",
        "RETRIEVAL_REWRITE_DEBUG",
        "VECTOR_STORE_DIR",
        "CHROMA_DIR",
        "HTTP_PROXY",
        "HTTPS_PROXY",
    ]:
        monkeypatch.delenv(key, raising=False)


def test_settings_default_to_local_embedding_provider(monkeypatch):
    monkeypatch.setattr(config_module, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setattr(config_module, "read_local_config_values", lambda: {})
    _clear_runtime_env(monkeypatch)
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.llm_provider == "google"
    assert settings.embedding_provider == "local"
    assert settings.embedding_model_name == "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    assert settings.course_primary_enabled is True
    assert settings.course_primary_dir == "a2-control-theory/source-notes"
    assert settings.pdf_parse_backend == "auto"
    get_settings.cache_clear()


def test_settings_default_google_embedding_model_when_embedding_provider_is_google(monkeypatch):
    monkeypatch.setattr(config_module, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setattr(config_module, "read_local_config_values", lambda: {})
    _clear_runtime_env(monkeypatch)
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    monkeypatch.setenv("LLM_PROVIDER", "google")
    monkeypatch.setenv("EMBEDDING_PROVIDER", "google")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.embedding_provider == "google"
    assert settings.embedding_model_name == "models/text-embedding-004"
    get_settings.cache_clear()


def test_settings_parse_mineru_proxy_overrides(monkeypatch):
    monkeypatch.setattr(config_module, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setattr(config_module, "read_local_config_values", lambda: {})
    _clear_runtime_env(monkeypatch)
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    monkeypatch.setenv("MINERU_PROXY_MODE", "direct")
    monkeypatch.setenv("MINERU_HTTP_PROXY", "http://127.0.0.1:7897")
    monkeypatch.setenv("MINERU_HTTPS_PROXY", "http://127.0.0.1:7897")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.mineru_proxy_mode == "direct"
    assert settings.mineru_http_proxy == "http://127.0.0.1:7897"
    assert settings.mineru_https_proxy == "http://127.0.0.1:7897"
    get_settings.cache_clear()


def test_settings_parse_mineru_public_dns_bypass_overrides(monkeypatch):
    monkeypatch.setattr(config_module, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setattr(config_module, "read_local_config_values", lambda: {})
    _clear_runtime_env(monkeypatch)
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    monkeypatch.setenv("MINERU_PUBLIC_DNS_BYPASS_ENABLED", "false")
    monkeypatch.setenv("MINERU_PUBLIC_DNS_SERVER", "1.1.1.1")
    monkeypatch.setenv("MINERU_PUBLIC_DNS_PORT", "5353")
    monkeypatch.setenv("MINERU_PUBLIC_DNS_HOSTS", "cdn-mineru.openxlab.org.cn,assets.example.com")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.mineru_public_dns_bypass_enabled is False
    assert settings.mineru_public_dns_server == "1.1.1.1"
    assert settings.mineru_public_dns_port == 5353
    assert settings.mineru_public_dns_hosts == "cdn-mineru.openxlab.org.cn,assets.example.com"
    get_settings.cache_clear()


def test_settings_parse_retrieval_rewrite_overrides(monkeypatch):
    monkeypatch.setattr(config_module, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setattr(config_module, "read_local_config_values", lambda: {})
    _clear_runtime_env(monkeypatch)
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    monkeypatch.setenv("RETRIEVAL_REWRITE_ENABLED", "true")
    monkeypatch.setenv("RETRIEVAL_REWRITE_MODE", "smart")
    monkeypatch.setenv("RETRIEVAL_REWRITE_DEBUG", "true")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.retrieval_rewrite_enabled is True
    assert settings.retrieval_rewrite_mode == "smart"
    assert settings.retrieval_rewrite_debug is True
    get_settings.cache_clear()


def test_settings_can_derive_proxy_from_proxy_port(monkeypatch):
    monkeypatch.setattr(config_module, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        config_module,
        "read_local_config_values",
        lambda: {
            "PROXY_HOST": "127.0.0.1",
            "PROXY_PORT": "7892",
            "PROXY_SCHEME": "http",
        },
    )
    _clear_runtime_env(monkeypatch)
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:7897")
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:7897")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.http_proxy == "http://127.0.0.1:7892"
    assert settings.https_proxy == "http://127.0.0.1:7892"
    get_settings.cache_clear()


def test_settings_use_chroma_dir_as_backward_compatible_vector_store_dir(monkeypatch):
    monkeypatch.setattr(config_module, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setattr(config_module, "read_local_config_values", lambda: {})
    _clear_runtime_env(monkeypatch)
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    monkeypatch.setenv("CHROMA_DIR", "/tmp/legacy-chroma")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.vector_store_dir == "/tmp/legacy-chroma"
    assert settings.chroma_dir == "/tmp/legacy-chroma"
    get_settings.cache_clear()

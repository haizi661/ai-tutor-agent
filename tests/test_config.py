import ai_tutor_agent.config as config_module
from ai_tutor_agent.config import apply_network_environment, get_settings, should_bypass_smart_proxy


def _clear_runtime_env(monkeypatch):
    for key in [
        "CHAT_PROFILE",
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
        "OPENAI_API_KEY",
        "OPENAI_API_BASE",
        "QWEN_API_KEY",
        "DEEPSEEK_API_KEY",
        "DASHSCOPE_API_KEY",
        "LLM_PROVIDER",
        "MODEL_NAME",
        "QUESTION_HELP_MODEL_NAME",
        "QUESTION_HELP_OPENAI_API_BASE",
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
        "GRAPH_RAG_ENABLE_LLM",
        "GRAPH_RAG_LLM_PROFILE",
        "VECTOR_STORE_DIR",
        "CHROMA_DIR",
        "PROXY_URL",
        "PROXY_HOST",
        "PROXY_PORT",
        "PROXY_SCHEME",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "NO_PROXY",
        "http_proxy",
        "https_proxy",
        "no_proxy",
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
    assert settings.course_primary_enabled is False
    assert settings.course_primary_dir == "data/knowledge_map_outputs"
    assert settings.default_course_id == "a2-control-theory"
    assert settings.pdf_parse_backend == "auto"
    get_settings.cache_clear()


def test_settings_default_question_help_to_qwen_multimodal(monkeypatch):
    monkeypatch.setattr(config_module, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setattr(config_module, "read_local_config_values", lambda: {})
    _clear_runtime_env(monkeypatch)
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.question_help_model_name == "qwen-vl-max-latest"
    assert settings.question_help_openai_api_base == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    get_settings.cache_clear()


def test_settings_allow_question_help_model_override(monkeypatch):
    monkeypatch.setattr(config_module, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setattr(config_module, "read_local_config_values", lambda: {})
    _clear_runtime_env(monkeypatch)
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    monkeypatch.setenv("QUESTION_HELP_MODEL_NAME", "qwen-vl-plus-latest")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.question_help_model_name == "qwen-vl-plus-latest"
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


def test_graph_rag_llm_defaults_to_enabled(monkeypatch):
    monkeypatch.setattr(config_module, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setattr(config_module, "read_local_config_values", lambda: {})
    _clear_runtime_env(monkeypatch)
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.graph_rag_enable_llm is True
    get_settings.cache_clear()


def test_env_file_can_disable_graph_rag_llm(monkeypatch, tmp_path):
    _clear_runtime_env(monkeypatch)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "GOOGLE_API_KEY=google-key\n"
        "GRAPH_RAG_ENABLE_LLM=false\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("AI_TUTOR_ENV_FILE", str(env_file))
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.graph_rag_enable_llm is False
    get_settings.cache_clear()


def test_shell_environment_overrides_graph_rag_llm_env_file_value(monkeypatch, tmp_path):
    _clear_runtime_env(monkeypatch)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "DEEPSEEK_API_KEY=deepseek-key\n"
        "CHAT_PROFILE=deepseek\n"
        "GRAPH_RAG_ENABLE_LLM=false\n"
        "GRAPH_RAG_LLM_PROFILE=qwen\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("AI_TUTOR_ENV_FILE", str(env_file))
    monkeypatch.setenv("GRAPH_RAG_ENABLE_LLM", "true")
    monkeypatch.setenv("GRAPH_RAG_LLM_PROFILE", "deepseek")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.graph_rag_enable_llm is True
    assert settings.graph_rag_llm_profile == "deepseek"
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
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.http_proxy == "http://127.0.0.1:7892"
    assert settings.https_proxy == "http://127.0.0.1:7892"
    assert "dashscope.aliyuncs.com" in settings.no_proxy
    assert "api.deepseek.com" in settings.no_proxy
    assert "hf-mirror.com" in settings.no_proxy
    assert "registry.npmmirror.com" in settings.no_proxy
    get_settings.cache_clear()


def test_shell_proxy_environment_overrides_env_file_proxy_values(monkeypatch):
    monkeypatch.setattr(config_module, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        config_module,
        "read_local_config_values",
        lambda: {
            "HTTP_PROXY": "http://127.0.0.1:7892",
            "HTTPS_PROXY": "http://127.0.0.1:7892",
            "PROXY_HOST": "127.0.0.1",
            "PROXY_PORT": "7893",
            "NO_PROXY": "file.local",
        },
    )
    _clear_runtime_env(monkeypatch)
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:7897")
    monkeypatch.setenv("HTTPS_PROXY", "http://127.0.0.1:7898")
    monkeypatch.setenv("NO_PROXY", "shell.local")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.http_proxy == "http://127.0.0.1:7897"
    assert settings.https_proxy == "http://127.0.0.1:7898"
    no_proxy_items = settings.no_proxy.split(",")
    assert no_proxy_items.index("shell.local") < no_proxy_items.index("file.local")
    get_settings.cache_clear()


def test_apply_network_environment_clears_stale_proxy_environment(monkeypatch):
    _clear_runtime_env(monkeypatch)
    monkeypatch.setenv("HTTP_PROXY", "http://old:1")
    monkeypatch.setenv("HTTPS_PROXY", "http://old:1")
    monkeypatch.setenv("NO_PROXY", "old.local")
    monkeypatch.setenv("http_proxy", "http://old:1")
    monkeypatch.setenv("https_proxy", "http://old:1")
    monkeypatch.setenv("no_proxy", "old.local")

    from dataclasses import replace

    monkeypatch.setattr(config_module, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setattr(config_module, "read_local_config_values", lambda: {})
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    get_settings.cache_clear()
    settings = replace(get_settings(), http_proxy=None, https_proxy=None, no_proxy="")

    apply_network_environment(settings)

    for key in ["HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "http_proxy", "https_proxy", "no_proxy"]:
        assert key not in config_module.os.environ
    get_settings.cache_clear()


def test_settings_preserves_explicit_no_proxy_and_merges_smart_direct_hosts(monkeypatch):
    monkeypatch.setattr(config_module, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        config_module,
        "read_local_config_values",
        lambda: {
            "PROXY_HOST": "127.0.0.1",
            "PROXY_PORT": "7897",
            "NO_PROXY": "custom.local,dashscope.aliyuncs.com",
        },
    )
    _clear_runtime_env(monkeypatch)
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    get_settings.cache_clear()

    settings = get_settings()
    no_proxy_items = settings.no_proxy.split(",")

    assert no_proxy_items.count("dashscope.aliyuncs.com") == 1
    assert "custom.local" in no_proxy_items
    assert ".aliyuncs.com" in no_proxy_items
    assert "api.deepseek.com" in no_proxy_items
    get_settings.cache_clear()


def test_explicit_no_proxy_is_not_expanded_when_proxy_is_disabled(monkeypatch):
    monkeypatch.setattr(config_module, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        config_module,
        "read_local_config_values",
        lambda: {"NO_PROXY": "custom.local"},
    )
    _clear_runtime_env(monkeypatch)
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    get_settings.cache_clear()

    settings = get_settings()

    assert settings.no_proxy == "custom.local"
    get_settings.cache_clear()


def test_apply_network_environment_exports_smart_proxy_policy(monkeypatch):
    monkeypatch.setattr(config_module, "load_dotenv", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        config_module,
        "read_local_config_values",
        lambda: {
            "PROXY_HOST": "127.0.0.1",
            "PROXY_PORT": "7897",
        },
    )
    _clear_runtime_env(monkeypatch)
    monkeypatch.setenv("GOOGLE_API_KEY", "google-key")
    get_settings.cache_clear()

    settings = get_settings()
    apply_network_environment(settings)

    assert config_module.os.environ["HTTP_PROXY"] == "http://127.0.0.1:7897"
    assert config_module.os.environ["HTTPS_PROXY"] == "http://127.0.0.1:7897"
    assert "open.bigmodel.cn" in config_module.os.environ["NO_PROXY"]
    get_settings.cache_clear()


def test_should_bypass_smart_proxy_matches_domestic_and_mirror_hosts():
    assert should_bypass_smart_proxy("https://dashscope.aliyuncs.com/compatible-mode/v1")
    assert should_bypass_smart_proxy("https://assets.openxlab.org.cn/resource")
    assert should_bypass_smart_proxy("registry.npmmirror.com")
    assert not should_bypass_smart_proxy("https://api.openai.com/v1")


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

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from dotenv import dotenv_values, load_dotenv


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def get_env_file_path() -> str:
    return os.getenv("AI_TUTOR_ENV_FILE", "").strip() or os.path.join(PROJECT_ROOT, ".env")


def _read_env_int(name: str, default: int) -> int:
    value = os.getenv(name, "").strip()
    if not value:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {name} must be an integer.") from exc


def _read_env_float(name: str, default: float) -> float:
    value = os.getenv(name, "").strip()
    if not value:
        return default
    try:
        return float(value)
    except ValueError as exc:
        raise RuntimeError(f"Environment variable {name} must be a float.") from exc


def _read_env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name, "").strip().lower()
    if not value:
        return default
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(f"Environment variable {name} must be a boolean.")


def _read_derived_proxy_url(values: Optional[dict[str, str]] = None) -> Optional[str]:
    source = values or os.environ

    proxy_url = (source.get("PROXY_URL", "") or "").strip()
    if proxy_url:
        return proxy_url

    proxy_port = (source.get("PROXY_PORT", "") or "").strip()
    if not proxy_port:
        return None
    if not proxy_port.isdigit():
        raise RuntimeError("Environment variable PROXY_PORT must be an integer.")

    proxy_host = (source.get("PROXY_HOST", "") or "").strip() or "127.0.0.1"
    proxy_scheme = (source.get("PROXY_SCHEME", "") or "").strip() or "http"
    return f"{proxy_scheme}://{proxy_host}:{proxy_port}"


@dataclass(frozen=True)
class Settings:
    chat_profile: str
    llm_provider: str
    google_api_key: Optional[str]
    gemini_api_key: Optional[str]
    openai_api_key: Optional[str]
    openai_api_base: Optional[str]
    qwen_api_key: Optional[str]
    deepseek_api_key: Optional[str]
    minimax_api_key: Optional[str]
    glm_api_key: Optional[str]
    model_name: str
    embedding_provider: str
    embedding_model_name: str
    tutor_temperature: float
    tester_temperature: float
    evaluator_temperature: float
    pass_score: int
    memory_db_path: str
    knowledge_dir: str
    knowledge_chunk_size: int
    knowledge_chunk_overlap: int
    knowledge_top_k: int
    default_thread_id: str
    http_proxy: Optional[str]
    https_proxy: Optional[str]
    local_config_enabled: bool
    course_primary_enabled: bool = True
    course_primary_dir: str = "a2-control-theory/source-notes"
    vector_store_backend: str = "chroma"
    vector_store_dir: str = "data/chroma_db"
    # RAG 2.0 新增字段
    dashscope_api_key: Optional[str] = None
    mineru_api_token: Optional[str] = None
    chroma_dir: str = "data/chroma_db"
    pdf_parse_backend: str = "auto"
    mineru_proxy_mode: str = "inherit"
    mineru_http_proxy: Optional[str] = None
    mineru_https_proxy: Optional[str] = None
    mineru_connect_timeout_seconds: int = 5
    mineru_public_dns_bypass_enabled: bool = True
    mineru_public_dns_server: str = "223.5.5.5"
    mineru_public_dns_port: int = 53
    mineru_public_dns_hosts: str = "cdn-mineru.openxlab.org.cn"
    retrieval_rewrite_enabled: bool = False
    retrieval_rewrite_mode: str = "smart"
    retrieval_rewrite_debug: bool = False
    web_search_enabled: bool = False
    web_search_provider: str = "tavily"
    tavily_api_key: Optional[str] = None
    web_search_max_results: int = 5


LOCAL_CONFIG_KEYS = [
    "CHAT_PROFILE",
    "GEMINI_API_KEY",
    "QWEN_API_KEY",
    "DEEPSEEK_API_KEY",
    "MINIMAX_API_KEY",
    "GLM_API_KEY",
    "DASHSCOPE_API_KEY",
    "LLM_PROVIDER",
    "GOOGLE_API_KEY",
    "OPENAI_API_KEY",
    "OPENAI_API_BASE",
    "MODEL_NAME",
    "EMBEDDING_PROVIDER",
    "EMBEDDING_MODEL_NAME",
    "PDF_PARSE_BACKEND",
    "MINERU_API_TOKEN",
    "COURSE_PRIMARY_ENABLED",
    "COURSE_PRIMARY_DIR",
    "KNOWLEDGE_CHUNK_SIZE",
    "KNOWLEDGE_CHUNK_OVERLAP",
    "KNOWLEDGE_TOP_K",
    "VECTOR_STORE_BACKEND",
    "VECTOR_STORE_DIR",
    "CHROMA_DIR",
    "PROXY_URL",
    "PROXY_HOST",
    "PROXY_PORT",
    "PROXY_SCHEME",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "MINERU_PROXY_MODE",
    "MINERU_HTTP_PROXY",
    "MINERU_HTTPS_PROXY",
    "MINERU_CONNECT_TIMEOUT_SECONDS",
    "MINERU_PUBLIC_DNS_BYPASS_ENABLED",
    "MINERU_PUBLIC_DNS_SERVER",
    "MINERU_PUBLIC_DNS_PORT",
    "MINERU_PUBLIC_DNS_HOSTS",
    "RETRIEVAL_REWRITE_ENABLED",
    "RETRIEVAL_REWRITE_MODE",
    "RETRIEVAL_REWRITE_DEBUG",
    "WEB_SEARCH_ENABLED",
    "WEB_SEARCH_PROVIDER",
    "TAVILY_API_KEY",
    "WEB_SEARCH_MAX_RESULTS",
    "LOCAL_CONFIG_ENABLED",
]


def read_local_config_values() -> dict[str, str]:
    env_path = get_env_file_path()
    if not os.path.exists(env_path):
        return {}
    raw_values = dotenv_values(env_path)
    return {key: (value or "") for key, value in raw_values.items() if key}


def update_env_file(updates: dict[str, str]) -> None:
    env_path = get_env_file_path()
    existing_lines: list[str] = []
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as file_obj:
            existing_lines = file_obj.readlines()

    normalized_updates = {
        key: str(value)
        for key, value in updates.items()
        if key in LOCAL_CONFIG_KEYS and value is not None
    }
    seen_keys = set()
    new_lines: list[str] = []

    for line in existing_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in line:
            new_lines.append(line)
            continue

        key = line.split("=", 1)[0].strip()
        if key in normalized_updates:
            new_lines.append(f"{key}={normalized_updates[key]}\n")
            seen_keys.add(key)
        else:
            new_lines.append(line)

    if new_lines and new_lines[-1] and not new_lines[-1].endswith("\n"):
        new_lines[-1] += "\n"

    for key, value in normalized_updates.items():
        if key not in seen_keys:
            new_lines.append(f"{key}={value}\n")

    with open(env_path, "w", encoding="utf-8") as file_obj:
        file_obj.writelines(new_lines)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    # Ensure we load the absolute latest from .env, ignoring cached system env vars
    load_dotenv(dotenv_path=get_env_file_path(), override=True)
    raw_values = read_local_config_values()

    # Determine provider dynamically
    google_api_key = os.getenv("GOOGLE_API_KEY", "").strip() or None
    gemini_api_key = (
        os.getenv("GEMINI_API_KEY", "").strip()
        or google_api_key
        or None
    )
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    openai_api_key = os.getenv("OPENAI_API_KEY", "").strip() or None
    openai_api_base = os.getenv("OPENAI_API_BASE", "").strip() or None
    qwen_api_key = os.getenv("QWEN_API_KEY", "").strip() or None
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "").strip() or None
    minimax_api_key = os.getenv("MINIMAX_API_KEY", "").strip() or None
    glm_api_key = os.getenv("GLM_API_KEY", "").strip() or None
    dashscope_api_key = os.getenv("DASHSCOPE_API_KEY", "").strip() or None
    mineru_api_token = os.getenv("MINERU_API_TOKEN", "").strip() or None
    pdf_parse_backend = os.getenv("PDF_PARSE_BACKEND", "auto").strip().lower() or "auto"
    mineru_proxy_mode = os.getenv("MINERU_PROXY_MODE", "inherit").strip().lower() or "inherit"
    mineru_http_proxy = os.getenv("MINERU_HTTP_PROXY", "").strip() or None
    mineru_https_proxy = os.getenv("MINERU_HTTPS_PROXY", "").strip() or None
    chat_profile = os.getenv("CHAT_PROFILE", "").strip().lower() or "custom"
    
    # Proxy settings
    derived_proxy_url_from_file = _read_derived_proxy_url(raw_values)
    derived_proxy_url = derived_proxy_url_from_file or _read_derived_proxy_url()
    http_proxy = (
        (raw_values.get("HTTP_PROXY", "") or "").strip()
        or derived_proxy_url_from_file
        or os.getenv("HTTP_PROXY", "").strip()
        or os.getenv("http_proxy", "").strip()
        or derived_proxy_url
        or None
    )
    https_proxy = (
        (raw_values.get("HTTPS_PROXY", "") or "").strip()
        or derived_proxy_url_from_file
        or os.getenv("HTTPS_PROXY", "").strip()
        or os.getenv("https_proxy", "").strip()
        or derived_proxy_url
        or None
    )

    if chat_profile == "gemini":
        provider = "openai"
        openai_api_base = "https://generativelanguage.googleapis.com/v1beta/openai/"
        openai_api_key = gemini_api_key or openai_api_key
        if not openai_api_key:
            raise RuntimeError("Gemini profile requires GEMINI_API_KEY or GOOGLE_API_KEY.")
    elif chat_profile == "qwen":
        provider = "openai"
        openai_api_base = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        openai_api_key = qwen_api_key
        if not openai_api_key:
            raise RuntimeError("Qwen profile requires QWEN_API_KEY.")
    elif chat_profile == "deepseek":
        provider = "openai"
        openai_api_base = "https://api.deepseek.com/v1"
        openai_api_key = deepseek_api_key
        if not openai_api_key:
            raise RuntimeError("DeepSeek profile requires DEEPSEEK_API_KEY.")
    elif chat_profile == "openai":
        provider = "openai"
        openai_api_base = openai_api_base or "https://api.openai.com/v1"
        if not openai_api_key:
            raise RuntimeError("OpenAI profile requires OPENAI_API_KEY.")
    elif chat_profile == "minimax":
        provider = "openai"
        openai_api_base = "https://api.minimaxi.com/v1"
        openai_api_key = minimax_api_key
        if not openai_api_key:
            raise RuntimeError("MiniMax profile requires MINIMAX_API_KEY.")
    elif chat_profile == "glm":
        provider = "openai"
        openai_api_base = "https://open.bigmodel.cn/api/paas/v4"
        openai_api_key = glm_api_key
        if not openai_api_key:
            raise RuntimeError("GLM profile requires GLM_API_KEY.")
    else:
        if not provider:
            if openai_api_key:
                provider = "openai"
            elif google_api_key:
                provider = "google"
            else:
                raise RuntimeError("Please set either GOOGLE_API_KEY or OPENAI_API_KEY in .env.")

    if provider == "google" and not google_api_key:
        raise RuntimeError("GOOGLE_API_KEY is required when using Google provider.")
    if provider == "openai" and not openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required when using OpenAI-compatible provider.")

    # Default model fallbacks based on provider / selected profile
    if chat_profile == "gemini":
        default_model = "gemini-2.5-pro"
    elif chat_profile == "qwen":
        default_model = "qwen-plus"
    elif chat_profile == "deepseek":
        default_model = "deepseek-chat"
    elif chat_profile == "openai":
        default_model = "gpt-5-mini"
    elif chat_profile == "minimax":
        default_model = "MiniMax-M2.5"
    elif chat_profile == "glm":
        default_model = "glm-5"
    else:
        if provider == "google":
            default_model = "gemini-2.5-pro"
        elif "generativelanguage" in str(openai_api_base):
            default_model = "gemini-2.5-pro"
        elif "dashscope" in str(openai_api_base):
            default_model = "qwen-plus"
        elif "deepseek" in str(openai_api_base):
            default_model = "deepseek-chat"
        elif "api.openai.com" in str(openai_api_base):
            default_model = "gpt-5-mini"
        elif "minimaxi" in str(openai_api_base):
            default_model = "MiniMax-M2.5"
        elif "bigmodel" in str(openai_api_base):
            default_model = "glm-5"
        else:
            default_model = "gpt-5-mini"

    embedding_provider = os.getenv("EMBEDDING_PROVIDER", "local").strip().lower() or "local"
    if embedding_provider not in {"local", "google", "openai", "dashscope"}:
        raise RuntimeError("EMBEDDING_PROVIDER must be one of: local, google, openai, dashscope.")
    if embedding_provider == "google" and not google_api_key:
        raise RuntimeError("GOOGLE_API_KEY is required when EMBEDDING_PROVIDER=google.")
    if embedding_provider == "openai" and not openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai.")
    if embedding_provider == "dashscope" and not dashscope_api_key:
        raise RuntimeError("DASHSCOPE_API_KEY is required when EMBEDDING_PROVIDER=dashscope.")

    vector_store_backend = os.getenv("VECTOR_STORE_BACKEND", "chroma").strip().lower() or "chroma"
    if vector_store_backend not in {"chroma", "inmemory"}:
        raise RuntimeError("VECTOR_STORE_BACKEND must be one of: chroma, inmemory.")
    if pdf_parse_backend not in {"auto", "mineru", "local"}:
        raise RuntimeError("PDF_PARSE_BACKEND must be one of: auto, mineru, local.")
    if mineru_proxy_mode not in {"inherit", "direct"}:
        raise RuntimeError("MINERU_PROXY_MODE must be one of: inherit, direct.")
    retrieval_rewrite_mode = os.getenv("RETRIEVAL_REWRITE_MODE", "smart").strip().lower() or "smart"
    if retrieval_rewrite_mode not in {"smart"}:
        raise RuntimeError("RETRIEVAL_REWRITE_MODE must be one of: smart.")
    web_search_provider = os.getenv("WEB_SEARCH_PROVIDER", "tavily").strip().lower() or "tavily"
    if web_search_provider not in {"tavily"}:
        raise RuntimeError("WEB_SEARCH_PROVIDER must be one of: tavily.")

    default_embedding_model = {
        "local": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "google": "models/text-embedding-004",
        "openai": "text-embedding-3-small",
        "dashscope": "text-embedding-v2",
    }[embedding_provider]

    # Explicitly check for MODEL_NAME
    env_model_name = os.getenv("MODEL_NAME", "").strip()
    model_name = env_model_name or default_model
    resolved_vector_store_dir = (
        os.getenv("VECTOR_STORE_DIR", "").strip()
        or os.getenv("CHROMA_DIR", "").strip()
        or os.path.join(PROJECT_ROOT, "data", "chroma_db")
    )

    return Settings(
        chat_profile=chat_profile,
        llm_provider=provider,
        google_api_key=google_api_key,
        gemini_api_key=gemini_api_key,
        openai_api_key=openai_api_key,
        openai_api_base=openai_api_base,
        qwen_api_key=qwen_api_key,
        deepseek_api_key=deepseek_api_key,
        minimax_api_key=minimax_api_key,
        glm_api_key=glm_api_key,
        model_name=model_name,
        embedding_provider=embedding_provider,
        embedding_model_name=(os.getenv("EMBEDDING_MODEL_NAME", "").strip() or default_embedding_model),
        tutor_temperature=_read_env_float("TUTOR_TEMPERATURE", 0.7),
        tester_temperature=_read_env_float("TESTER_TEMPERATURE", 0.4),
        evaluator_temperature=_read_env_float("EVALUATOR_TEMPERATURE", 0.0),
        pass_score=_read_env_int("PASS_SCORE", 80),
        memory_db_path=os.getenv("MEMORY_DB_PATH", "data/tutor_memory.db").strip() or "data/tutor_memory.db",
        knowledge_dir=os.getenv("KNOWLEDGE_DIR", "data/knowledge").strip() or "data/knowledge",
        course_primary_enabled=_read_env_bool("COURSE_PRIMARY_ENABLED", True),
        course_primary_dir=os.getenv("COURSE_PRIMARY_DIR", "a2-control-theory/source-notes").strip() or "a2-control-theory/source-notes",
        knowledge_chunk_size=_read_env_int("KNOWLEDGE_CHUNK_SIZE", 1000),
        knowledge_chunk_overlap=_read_env_int("KNOWLEDGE_CHUNK_OVERLAP", 150),
        knowledge_top_k=_read_env_int("KNOWLEDGE_TOP_K", 3),
        vector_store_backend=vector_store_backend,
        vector_store_dir=resolved_vector_store_dir,
        default_thread_id=os.getenv("DEFAULT_THREAD_ID", "haizi_master_01").strip() or "haizi_master_01",
        http_proxy=http_proxy,
        https_proxy=https_proxy,
        local_config_enabled=os.getenv("LOCAL_CONFIG_ENABLED", "true").strip().lower() != "false",
        dashscope_api_key=dashscope_api_key,
        mineru_api_token=mineru_api_token,
        chroma_dir=resolved_vector_store_dir,
        pdf_parse_backend=pdf_parse_backend,
        mineru_proxy_mode=mineru_proxy_mode,
        mineru_http_proxy=mineru_http_proxy,
        mineru_https_proxy=mineru_https_proxy,
        mineru_connect_timeout_seconds=_read_env_int("MINERU_CONNECT_TIMEOUT_SECONDS", 5),
        mineru_public_dns_bypass_enabled=_read_env_bool("MINERU_PUBLIC_DNS_BYPASS_ENABLED", True),
        mineru_public_dns_server=os.getenv("MINERU_PUBLIC_DNS_SERVER", "223.5.5.5").strip() or "223.5.5.5",
        mineru_public_dns_port=_read_env_int("MINERU_PUBLIC_DNS_PORT", 53),
        mineru_public_dns_hosts=os.getenv("MINERU_PUBLIC_DNS_HOSTS", "cdn-mineru.openxlab.org.cn").strip() or "cdn-mineru.openxlab.org.cn",
        retrieval_rewrite_enabled=_read_env_bool("RETRIEVAL_REWRITE_ENABLED", False),
        retrieval_rewrite_mode=retrieval_rewrite_mode,
        retrieval_rewrite_debug=_read_env_bool("RETRIEVAL_REWRITE_DEBUG", False),
        web_search_enabled=_read_env_bool("WEB_SEARCH_ENABLED", False),
        web_search_provider=web_search_provider,
        tavily_api_key=os.getenv("TAVILY_API_KEY", "").strip() or None,
        web_search_max_results=_read_env_int("WEB_SEARCH_MAX_RESULTS", 5),
    )

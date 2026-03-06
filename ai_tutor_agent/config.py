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


LOCAL_CONFIG_KEYS = [
    "CHAT_PROFILE",
    "GEMINI_API_KEY",
    "QWEN_API_KEY",
    "DEEPSEEK_API_KEY",
    "MINIMAX_API_KEY",
    "GLM_API_KEY",
    "LLM_PROVIDER",
    "GOOGLE_API_KEY",
    "OPENAI_API_KEY",
    "OPENAI_API_BASE",
    "MODEL_NAME",
    "EMBEDDING_PROVIDER",
    "EMBEDDING_MODEL_NAME",
    "KNOWLEDGE_CHUNK_SIZE",
    "KNOWLEDGE_CHUNK_OVERLAP",
    "KNOWLEDGE_TOP_K",
    "HTTP_PROXY",
    "HTTPS_PROXY",
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
    chat_profile = os.getenv("CHAT_PROFILE", "").strip().lower() or "custom"
    
    # Proxy settings
    http_proxy = os.getenv("HTTP_PROXY", "").strip() or os.getenv("http_proxy", "").strip() or None
    https_proxy = os.getenv("HTTPS_PROXY", "").strip() or os.getenv("https_proxy", "").strip() or None

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
    if embedding_provider not in {"local", "google", "openai"}:
        raise RuntimeError("EMBEDDING_PROVIDER must be one of: local, google, openai.")
    if embedding_provider == "google" and not google_api_key:
        raise RuntimeError("GOOGLE_API_KEY is required when EMBEDDING_PROVIDER=google.")
    if embedding_provider == "openai" and not openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is required when EMBEDDING_PROVIDER=openai.")

    default_embedding_model = {
        "local": "sentence-transformers/all-MiniLM-L6-v2",
        "google": "models/text-embedding-004",
        "openai": "text-embedding-3-small",
    }[embedding_provider]

    # Explicitly check for MODEL_NAME
    env_model_name = os.getenv("MODEL_NAME", "").strip()
    model_name = env_model_name or default_model

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
        knowledge_chunk_size=_read_env_int("KNOWLEDGE_CHUNK_SIZE", 1000),
        knowledge_chunk_overlap=_read_env_int("KNOWLEDGE_CHUNK_OVERLAP", 150),
        knowledge_top_k=_read_env_int("KNOWLEDGE_TOP_K", 3),
        default_thread_id=os.getenv("DEFAULT_THREAD_ID", "haizi_master_01").strip() or "haizi_master_01",
        http_proxy=http_proxy,
        https_proxy=https_proxy,
        local_config_enabled=os.getenv("LOCAL_CONFIG_ENABLED", "true").strip().lower() != "false",
    )

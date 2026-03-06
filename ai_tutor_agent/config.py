import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional

from dotenv import load_dotenv


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
    llm_provider: str
    google_api_key: Optional[str]
    openai_api_key: Optional[str]
    openai_api_base: Optional[str]
    model_name: str
    tutor_temperature: float
    tester_temperature: float
    evaluator_temperature: float
    pass_score: int
    memory_db_path: str
    knowledge_dir: str
    default_thread_id: str
    http_proxy: Optional[str]
    https_proxy: Optional[str]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_dotenv()

    # Determine provider dynamically
    provider = os.getenv("LLM_PROVIDER", "").strip().lower()
    google_api_key = os.getenv("GOOGLE_API_KEY", "").strip() or None
    openai_api_key = os.getenv("OPENAI_API_KEY", "").strip() or None
    openai_api_base = os.getenv("OPENAI_API_BASE", "").strip() or None
    
    # Proxy settings
    http_proxy = os.getenv("HTTP_PROXY", "").strip() or os.getenv("http_proxy", "").strip() or None
    https_proxy = os.getenv("HTTPS_PROXY", "").strip() or os.getenv("https_proxy", "").strip() or None

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

    # Default model fallbacks based on provider
    default_model = "gemini-2.5-pro" if provider == "google" else "qwen-plus"
    model_name = os.getenv("MODEL_NAME", "").strip() or os.getenv("GOOGLE_MODEL_NAME", "").strip() or default_model

    return Settings(
        llm_provider=provider,
        google_api_key=google_api_key,
        openai_api_key=openai_api_key,
        openai_api_base=openai_api_base,
        model_name=model_name,
        tutor_temperature=_read_env_float("TUTOR_TEMPERATURE", 0.7),
        tester_temperature=_read_env_float("TESTER_TEMPERATURE", 0.4),
        evaluator_temperature=_read_env_float("EVALUATOR_TEMPERATURE", 0.0),
        pass_score=_read_env_int("PASS_SCORE", 80),
        memory_db_path=os.getenv("MEMORY_DB_PATH", "data/tutor_memory.db").strip() or "data/tutor_memory.db",
        knowledge_dir=os.getenv("KNOWLEDGE_DIR", "data/knowledge").strip() or "data/knowledge",
        default_thread_id=os.getenv("DEFAULT_THREAD_ID", "haizi_master_01").strip() or "haizi_master_01",
        http_proxy=http_proxy,
        https_proxy=https_proxy,
    )

import os
from dataclasses import dataclass
from functools import lru_cache

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
    google_api_key: str
    model_name: str
    tutor_temperature: float
    tester_temperature: float
    evaluator_temperature: float
    pass_score: int
    memory_db_path: str
    default_thread_id: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    load_dotenv()

    google_api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not google_api_key:
        raise RuntimeError("GOOGLE_API_KEY is required. Please set it in .env.")

    return Settings(
        google_api_key=google_api_key,
        model_name=os.getenv("GOOGLE_MODEL_NAME", "gemini-2.5-pro").strip() or "gemini-2.5-pro",
        tutor_temperature=_read_env_float("TUTOR_TEMPERATURE", 0.7),
        tester_temperature=_read_env_float("TESTER_TEMPERATURE", 0.4),
        evaluator_temperature=_read_env_float("EVALUATOR_TEMPERATURE", 0.0),
        pass_score=_read_env_int("PASS_SCORE", 80),
        memory_db_path=os.getenv("MEMORY_DB_PATH", "data/tutor_memory.db").strip() or "data/tutor_memory.db",
        default_thread_id=os.getenv("DEFAULT_THREAD_ID", "haizi_master_01").strip() or "haizi_master_01",
    )

import os

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ...config import get_env_file_path, read_local_config_values, update_env_file
from .runtime import (
    CHAT_PROFILES,
    apply_chat_profile,
    build_vendor_catalogs,
    get_runtime,
    refresh_runtime,
    serialize_runtime_config,
)


router = APIRouter(prefix="/api/config", tags=["config"])


def _coerce_int(raw_value: str, fallback: int) -> int:
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return fallback


def _raw_base_matches(raw_values: dict[str, str], pattern: str) -> bool:
    return pattern in (raw_values.get("OPENAI_API_BASE", "") or "")


def _mask_secret(raw_value: str) -> str:
    if not raw_value:
        return ""
    if len(raw_value) <= 4:
        return "*" * len(raw_value)
    return f"****{raw_value[-4:]}"


class ConfigUpdateRequest(BaseModel):
    profile_id: str


class LocalConfigUpdateRequest(BaseModel):
    vendor_id: str = ""
    api_key: str = ""
    chat_profile: str = ""
    gemini_api_key: str = ""
    qwen_api_key: str = ""
    deepseek_api_key: str = ""
    minimax_api_key: str = ""
    glm_api_key: str = ""
    llm_provider: str = ""
    google_api_key: str = ""
    openai_api_key: str = ""
    openai_api_base: str = ""
    model_name: str = ""
    embedding_provider: str = "local"
    embedding_model_name: str = ""
    knowledge_chunk_size: int = 1000
    knowledge_chunk_overlap: int = 150
    knowledge_top_k: int = 3
    http_proxy: str = ""
    https_proxy: str = ""


@router.get("")
async def get_current_config(request: Request):
    runtime = get_runtime(request)
    return serialize_runtime_config(runtime.settings)


@router.post("")
async def update_current_config(req: ConfigUpdateRequest, request: Request):
    runtime = get_runtime(request)
    profile_id = req.profile_id.strip().lower()
    try:
        runtime.settings = apply_chat_profile(runtime.settings, profile_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return serialize_runtime_config(runtime.settings)


@router.get("/local")
async def get_local_config(request: Request):
    runtime = get_runtime(request)
    settings = runtime.settings
    raw_values = read_local_config_values()
    selected_vendor = settings.chat_profile if settings.chat_profile in CHAT_PROFILES else "custom"
    gemini_key = raw_values.get(
        "GEMINI_API_KEY",
        raw_values.get(
            "GOOGLE_API_KEY",
            raw_values.get("OPENAI_API_KEY", "") if _raw_base_matches(raw_values, "generativelanguage.googleapis.com") else "",
        ),
    )
    qwen_key = raw_values.get("QWEN_API_KEY", "")
    deepseek_key = raw_values.get("DEEPSEEK_API_KEY", "")
    minimax_key = raw_values.get("MINIMAX_API_KEY", "")
    glm_key = raw_values.get("GLM_API_KEY", "")
    google_key = raw_values.get("GOOGLE_API_KEY", "")
    openai_key = raw_values.get("OPENAI_API_KEY", "")
    return {
        "local_config_enabled": settings.local_config_enabled,
        "chat_profile": settings.chat_profile,
        "selected_vendor": selected_vendor,
        "selected_model": raw_values.get("MODEL_NAME", settings.model_name),
        "gemini_api_key": _mask_secret(gemini_key),
        "qwen_api_key": _mask_secret(qwen_key),
        "deepseek_api_key": _mask_secret(deepseek_key),
        "minimax_api_key": _mask_secret(minimax_key),
        "glm_api_key": _mask_secret(glm_key),
        "llm_provider": raw_values.get("LLM_PROVIDER", settings.llm_provider),
        "google_api_key": _mask_secret(google_key),
        "openai_api_key": _mask_secret(openai_key),
        "openai_api_base": raw_values.get("OPENAI_API_BASE", settings.openai_api_base or ""),
        "model_name": raw_values.get("MODEL_NAME", settings.model_name),
        "vendors": build_vendor_catalogs(settings),
        "has_gemini_api_key": bool(gemini_key),
        "has_qwen_api_key": bool(qwen_key),
        "has_deepseek_api_key": bool(deepseek_key),
        "has_minimax_api_key": bool(minimax_key),
        "has_glm_api_key": bool(glm_key),
        "has_google_api_key": bool(google_key),
        "has_openai_api_key": bool(openai_key),
        "embedding_provider": raw_values.get("EMBEDDING_PROVIDER", settings.embedding_provider),
        "embedding_model_name": raw_values.get("EMBEDDING_MODEL_NAME", settings.embedding_model_name),
        "knowledge_chunk_size": _coerce_int(raw_values.get("KNOWLEDGE_CHUNK_SIZE"), settings.knowledge_chunk_size),
        "knowledge_chunk_overlap": _coerce_int(raw_values.get("KNOWLEDGE_CHUNK_OVERLAP"), settings.knowledge_chunk_overlap),
        "knowledge_top_k": _coerce_int(raw_values.get("KNOWLEDGE_TOP_K"), settings.knowledge_top_k),
        "http_proxy": raw_values.get("HTTP_PROXY", settings.http_proxy or ""),
        "https_proxy": raw_values.get("HTTPS_PROXY", settings.https_proxy or ""),
    }


@router.post("/local")
async def update_local_config(req: LocalConfigUpdateRequest, request: Request):
    runtime = get_runtime(request)
    if not runtime.settings.local_config_enabled:
        raise HTTPException(status_code=403, detail="Local config editing is disabled.")

    env_path = get_env_file_path()
    old_content = None
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as file_obj:
            old_content = file_obj.read()

    raw_values = read_local_config_values()
    vendor_id = (req.vendor_id or req.chat_profile or "gemini").strip().lower()
    if vendor_id not in CHAT_PROFILES:
        raise HTTPException(status_code=400, detail=f"Unsupported vendor: {vendor_id}")

    updates = {
        "CHAT_PROFILE": vendor_id,
        "GEMINI_API_KEY": req.gemini_api_key.strip() or raw_values.get("GEMINI_API_KEY", raw_values.get("GOOGLE_API_KEY", "")),
        "QWEN_API_KEY": req.qwen_api_key.strip() or raw_values.get("QWEN_API_KEY", ""),
        "DEEPSEEK_API_KEY": req.deepseek_api_key.strip() or raw_values.get("DEEPSEEK_API_KEY", ""),
        "MINIMAX_API_KEY": req.minimax_api_key.strip() or raw_values.get("MINIMAX_API_KEY", ""),
        "GLM_API_KEY": req.glm_api_key.strip() or raw_values.get("GLM_API_KEY", ""),
        "LLM_PROVIDER": req.llm_provider.strip() or raw_values.get("LLM_PROVIDER", "openai"),
        "GOOGLE_API_KEY": req.google_api_key.strip() or raw_values.get("GOOGLE_API_KEY", ""),
        "OPENAI_API_KEY": req.openai_api_key.strip() or raw_values.get("OPENAI_API_KEY", ""),
        "OPENAI_API_BASE": req.openai_api_base.strip() or raw_values.get("OPENAI_API_BASE", ""),
        "MODEL_NAME": req.model_name.strip() or raw_values.get("MODEL_NAME", ""),
        "EMBEDDING_PROVIDER": req.embedding_provider.strip() or "local",
        "EMBEDDING_MODEL_NAME": req.embedding_model_name.strip(),
        "KNOWLEDGE_CHUNK_SIZE": str(req.knowledge_chunk_size),
        "KNOWLEDGE_CHUNK_OVERLAP": str(req.knowledge_chunk_overlap),
        "KNOWLEDGE_TOP_K": str(req.knowledge_top_k),
        "HTTP_PROXY": req.http_proxy.strip(),
        "HTTPS_PROXY": req.https_proxy.strip(),
    }

    selected_api_key = req.api_key.strip()
    if vendor_id == "custom":
        updates["LLM_PROVIDER"] = req.llm_provider.strip() or "openai"
        updates["OPENAI_API_BASE"] = req.openai_api_base.strip()
        updates["MODEL_NAME"] = req.model_name.strip()
        if updates["LLM_PROVIDER"] == "google":
            chosen_key = selected_api_key or req.google_api_key.strip() or raw_values.get("GOOGLE_API_KEY", "")
            updates["GOOGLE_API_KEY"] = chosen_key
            updates["GEMINI_API_KEY"] = req.gemini_api_key.strip() or raw_values.get("GEMINI_API_KEY", "")
        else:
            chosen_key = selected_api_key or req.openai_api_key.strip() or raw_values.get("OPENAI_API_KEY", "")
            updates["OPENAI_API_KEY"] = chosen_key
    else:
        vendor = CHAT_PROFILES[vendor_id]
        updates["LLM_PROVIDER"] = vendor["llm_provider"]
        updates["OPENAI_API_BASE"] = vendor["openai_api_base"]
        updates["MODEL_NAME"] = req.model_name.strip() or vendor["default_model"]

        if vendor_id == "gemini":
            chosen_key = selected_api_key or req.gemini_api_key.strip() or req.google_api_key.strip() or raw_values.get("GEMINI_API_KEY", raw_values.get("GOOGLE_API_KEY", ""))
            updates["GEMINI_API_KEY"] = chosen_key
            updates["GOOGLE_API_KEY"] = chosen_key
        elif vendor_id == "qwen":
            updates["QWEN_API_KEY"] = selected_api_key or req.qwen_api_key.strip() or raw_values.get("QWEN_API_KEY", "")
        elif vendor_id == "deepseek":
            updates["DEEPSEEK_API_KEY"] = selected_api_key or req.deepseek_api_key.strip() or raw_values.get("DEEPSEEK_API_KEY", "")
        elif vendor_id == "openai":
            updates["OPENAI_API_KEY"] = selected_api_key or req.openai_api_key.strip() or raw_values.get("OPENAI_API_KEY", "")
        elif vendor_id == "minimax":
            updates["MINIMAX_API_KEY"] = selected_api_key or req.minimax_api_key.strip() or raw_values.get("MINIMAX_API_KEY", "")
        elif vendor_id == "glm":
            updates["GLM_API_KEY"] = selected_api_key or req.glm_api_key.strip() or raw_values.get("GLM_API_KEY", "")

    try:
        update_env_file(updates)
        refresh_runtime(runtime)
    except Exception as exc:
        if old_content is None:
            if os.path.exists(env_path):
                os.remove(env_path)
        else:
            with open(env_path, "w", encoding="utf-8") as file_obj:
                file_obj.write(old_content)
        raise HTTPException(status_code=400, detail=f"Failed to apply local config: {exc}") from exc

    return {
        "status": "ok",
        "config": serialize_runtime_config(runtime.settings),
        "local": await get_local_config(request),
    }

from __future__ import annotations

import tempfile
import math
import numbers
import os
import mimetypes
from collections.abc import Mapping
from pathlib import Path, PureWindowsPath

from fastapi import APIRouter, File, Request, UploadFile

from .error_correction import get_error_correction_service
from .runtime import get_runtime


router = APIRouter(prefix="/api", tags=["knowledge"])


_GRAPH_NUMERIC_DEFAULTS = {
    "relation_strength": 0.5,
    "weight": 0.5,
    "strength": 0.5,
    "confidence": 0,
    "score": 0,
    "distance": 0,
    "mastery_threshold": 0,
}


def _graph_numeric_default(field_name: str | None) -> float | int | None:
    if not field_name:
        return None
    return _GRAPH_NUMERIC_DEFAULTS.get(str(field_name).strip().lower())


def _is_missing_scalar(value: object) -> bool:
    """Detect pandas.NA/pandas.NaT-like scalar values without importing pandas."""
    value_type = type(value)
    module = getattr(value_type, "__module__", "")
    name = getattr(value_type, "__name__", "")
    return module.startswith("pandas") and name in {"NAType", "NaTType"}


def _json_safe_graph_value(value: object, field_name: str | None = None) -> object:
    """Convert graph pipeline data to strict JSON-safe Python primitives.

    Starlette's JSONResponse is configured with allow_nan=False, so one NaN or
    Infinity anywhere in a nested node/edge record turns the whole endpoint into
    HTTP 500. Keep invalid graph metrics as None unless a field has a safe
    semantic default.
    """
    default = _graph_numeric_default(field_name)

    if value is None:
        return None
    if _is_missing_scalar(value):
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, numbers.Integral):
        return int(value)
    if isinstance(value, numbers.Real):
        number = float(value)
        if math.isfinite(number):
            return number
        return default
    if isinstance(value, Mapping):
        return {
            str(_json_safe_graph_value(key)): _json_safe_graph_value(item, str(key))
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_json_safe_graph_value(item, field_name) for item in value]
    if hasattr(value, "tolist") and callable(getattr(value, "tolist", None)):
        try:
            return _json_safe_graph_value(value.tolist(), field_name)
        except Exception:
            pass
    if hasattr(value, "item") and callable(getattr(value, "item", None)):
        try:
            return _json_safe_graph_value(value.item(), field_name)
        except Exception:
            pass
    if hasattr(value, "isoformat") and callable(getattr(value, "isoformat", None)):
        try:
            return value.isoformat()
        except Exception:
            pass
    return str(value)


def _sanitize_graph_record(record: object, *, edge: bool = False) -> dict:
    if not isinstance(record, Mapping):
        return {}
    sanitized = {
        str(_json_safe_graph_value(key)): _json_safe_graph_value(value, str(key))
        for key, value in record.items()
    }
    if edge:
        for key in ("relation_strength", "weight"):
            if key in sanitized and sanitized[key] is None:
                sanitized[key] = _graph_numeric_default(key)
    return sanitized


@router.get("/knowledge")
async def get_knowledge_status(request: Request):
    runtime = get_runtime(request)
    knowledge_provider = runtime.knowledge_provider
    files = knowledge_provider.list_documents() if hasattr(knowledge_provider, "list_documents") else []
    return {
        "enabled": bool(getattr(knowledge_provider, "vector_store", None)),
        "embedding_provider": runtime.settings.embedding_provider,
        "embedding_model_name": runtime.settings.embedding_model_name,
        "knowledge_dir": runtime.settings.knowledge_dir,
        "vector_store_backend": runtime.settings.vector_store_backend,
        "vector_store_dir": runtime.settings.vector_store_dir,
        "supports_upload": hasattr(knowledge_provider, "add_document"),
        "supports_delete": hasattr(knowledge_provider, "delete_document"),
        "files": files,
    }


@router.get("/knowledge/files")
async def list_knowledge_files(request: Request):
    runtime = get_runtime(request)
    knowledge_provider = runtime.knowledge_provider
    if not hasattr(knowledge_provider, "list_documents"):
        return {"items": []}
    return {"items": knowledge_provider.list_documents()}


@router.get("/knowledge/question-bank")
async def list_question_bank_items():
    service = get_error_correction_service()
    return {"items": service.list_question_bank()}


@router.post("/knowledge/question-bank")
async def save_question_bank_items(request: Request):
    payload = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    selected_ids = payload.get("selected_ids") or []
    source_files = payload.get("source_files") or []
    if selected_ids and not isinstance(selected_ids, list):
        return {"status": "error", "message": "selected_ids 必须是数组"}
    if source_files and not isinstance(source_files, list):
        return {"status": "error", "message": "source_files 必须是数组"}
    service = get_error_correction_service()
    try:
        result = service.save_questions_to_library(selected_ids=selected_ids, source_files=source_files)
        return {
            "status": "success",
            "message": f"已保存 {result['saved_count']} 道题到资料库题库",
            **result,
        }
    except RuntimeError as exc:
        return {"status": "error", "message": str(exc)}


@router.delete("/knowledge/question-bank")
async def clear_question_bank_items():
    service = get_error_correction_service()
    removed = service.clear_question_bank()
    return {"status": "success", "removed": removed}


@router.delete("/knowledge/question-bank/{library_id}")
async def delete_question_bank_item(library_id: str):
    service = get_error_correction_service()
    try:
        deleted = service.delete_question_bank_entry(library_id)
    except ValueError as exc:
        return {"status": "error", "message": str(exc)}
    if not deleted:
        return {"status": "error", "message": "题目不存在"}
    return {"status": "success", "library_id": library_id}


@router.post("/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    runtime = get_runtime(request)
    knowledge_provider = runtime.knowledge_provider
    if not hasattr(knowledge_provider, "add_document"):
        return {"status": "error", "message": "Knowledge provider does not support uploads."}

    raw_name = file.filename or ""
    safe_name = Path(PureWindowsPath(raw_name).name).name or "upload.bin"
    try:
        with tempfile.TemporaryDirectory(prefix="ai_tutor_upload_") as temp_dir:
            file_path = Path(temp_dir) / safe_name
            with file_path.open("wb") as buffer:
                content = await file.read()
                buffer.write(content)
            success = knowledge_provider.add_document(str(file_path))
        if success:
            return {"status": "success", "filename": safe_name}
        # File may have been stored even if indexing failed (unsupported type)
        knowledge_dir = getattr(knowledge_provider, "knowledge_dir", None)
        stored = knowledge_dir and (Path(knowledge_dir) / safe_name).exists()
        if stored:
            return {"status": "success", "filename": safe_name,
                    "message": "已保存到资料库（此格式仅支持查阅，暂不支持内容搜索）"}
        return {"status": "error", "filename": safe_name, "message": "上传失败，文件未能保存"}
    except Exception as exc:
        return {"status": "error", "filename": safe_name, "message": str(exc)}


@router.delete("/knowledge/files/{filename}")
async def delete_knowledge_file(filename: str, request: Request):
    runtime = get_runtime(request)
    knowledge_provider = runtime.knowledge_provider
    if not hasattr(knowledge_provider, "delete_document"):
        return {"status": "error", "message": "Knowledge provider does not support deletion."}

    safe_name = Path(filename).name
    success = knowledge_provider.delete_document(safe_name)
    if not success:
        return {"status": "error", "filename": safe_name, "message": "File not found or delete failed."}
    return {"status": "success", "filename": safe_name}


@router.get("/knowledge/file/{filename:path}")
async def get_knowledge_file(filename: str, request: Request):
    runtime = get_runtime(request)
    knowledge_provider = runtime.knowledge_provider
    if not hasattr(knowledge_provider, "knowledge_dir"):
        return {"status": "error", "message": "Knowledge provider not available"}

    knowledge_dir = Path(knowledge_provider.knowledge_dir)
    safe_name = Path(filename).name
    file_path = knowledge_dir / safe_name

    if not file_path.exists():
        return {"status": "error", "message": "File not found"}

    from fastapi.responses import FileResponse
    media_type, _ = mimetypes.guess_type(str(file_path))
    return FileResponse(
        file_path,
        media_type=media_type or "application/octet-stream",
        filename=safe_name,
    )


@router.get("/graph/b/data.json")
async def get_graph_b_data(request: Request):
    """Serve the runtime graph B JSON for the viewer."""
    runtime = get_runtime(request)
    pipeline = getattr(runtime, "graph_rag_pipeline", None)
    if pipeline is None:
        return {"nodes": [], "edges": [], "meta": {"error": "GraphRAGPipeline not loaded"}}
    nodes = [_sanitize_graph_record(node) for node in (pipeline.nodes or [])]
    edges = [_sanitize_graph_record(edge, edge=True) for edge in (pipeline.edges or [])]
    return {
        "nodes": nodes,
        "edges": edges,
        "meta": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "source": "auto_control_knowledge_map_v2",
        },
    }


@router.delete("/knowledge/files")
async def clear_knowledge_files(request: Request):
    runtime = get_runtime(request)
    knowledge_provider = runtime.knowledge_provider
    if not hasattr(knowledge_provider, "clear_documents"):
        return {"status": "error", "message": "Knowledge provider does not support clear operation."}

    removed = knowledge_provider.clear_documents()
    return {"status": "success", "removed": removed}

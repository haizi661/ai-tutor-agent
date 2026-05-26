from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from ...infrastructure.error_correction_bridge import ErrorCorrectionService
from .runtime import get_runtime


router = APIRouter(prefix="/api/error-correction", tags=["error-correction"])
_service = ErrorCorrectionService()


def get_error_correction_service() -> ErrorCorrectionService:
    return _service


def _error_response(message: str, *, status_code: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"status": "error", "message": message},
    )


@router.get("/status")
async def get_error_correction_status(request: Request):
    runtime = get_runtime(request)
    service = get_error_correction_service()
    return {"status": "success", **service.get_workspace_snapshot(runtime.settings)}


@router.get("/files")
async def list_error_correction_files():
    service = get_error_correction_service()
    return {"status": "success", "items": service.list_uploads()}


@router.post("/upload")
async def upload_error_correction_files(
    files: Annotated[list[UploadFile], File(...)],
):
    if not files:
        return _error_response("没有上传文件")
    prepared: list[tuple[str, bytes]] = []
    for upload in files:
        filename = Path(upload.filename or "").name
        if not filename:
            continue
        prepared.append((filename, await upload.read()))
    if not prepared:
        return _error_response("没有上传文件")

    try:
        service = get_error_correction_service()
        items = service.save_uploads(prepared)
        return {
            "status": "success",
            "items": items,
            "message": f"已加入 {len(prepared)} 份题库文件",
        }
    except ValueError as exc:
        return _error_response(str(exc))
    except Exception as exc:
        return _error_response(str(exc), status_code=500)


@router.delete("/files/{filename}")
async def delete_error_correction_file(filename: str):
    try:
        service = get_error_correction_service()
        deleted = service.delete_upload(filename)
    except ValueError as exc:
        return _error_response(str(exc))
    if not deleted:
        return _error_response("文件不存在", status_code=404)
    return {"status": "success", "message": f"已移除 {Path(filename).name}"}


@router.delete("/workspace")
async def clear_error_correction_workspace():
    service = get_error_correction_service()
    service.clear_workspace()
    return {"status": "success", "message": "已清空当前题库加工工作台"}


@router.get("/files/{filename:path}")
async def download_error_correction_file(filename: str):
    service = get_error_correction_service()
    try:
        file_path = service.resolve_upload_path(filename)
    except ValueError as exc:
        return _error_response(str(exc))
    except FileNotFoundError:
        return _error_response("文件不存在", status_code=404)

    media_type, _ = mimetypes.guess_type(str(file_path))
    return FileResponse(
        file_path,
        media_type=media_type or "application/octet-stream",
        filename=file_path.name,
    )


@router.get("/assets/{asset_path:path}")
async def download_error_correction_asset(asset_path: str):
    service = get_error_correction_service()
    try:
        file_path = service.resolve_asset_path(asset_path)
    except ValueError as exc:
        return _error_response(str(exc))
    except FileNotFoundError:
        return _error_response("资源不存在", status_code=404)

    media_type, _ = mimetypes.guess_type(str(file_path))
    return FileResponse(
        file_path,
        media_type=media_type or "application/octet-stream",
        filename=file_path.name,
    )


@router.post("/ocr")
async def run_error_correction_ocr(request: Request):
    runtime = get_runtime(request)
    service = get_error_correction_service()
    payload = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    selected_filename = str(payload.get("selected_filename") or "").strip()
    try:
        payload = service.run_ocr(runtime.settings, selected_filename=selected_filename)
        return {
            "status": "success",
            "message": f"OCR 完成，共 {len(payload.get('pages') or [])} 页",
            **payload,
        }
    except RuntimeError as exc:
        return _error_response(str(exc))
    except Exception as exc:
        return _error_response(str(exc), status_code=500)


@router.post("/split")
async def run_error_correction_split(request: Request):
    runtime = get_runtime(request)
    payload = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    confirmed_answer_layout = str(payload.get("confirmed_answer_layout") or "").strip()
    selected_filename = str(payload.get("selected_filename") or "").strip()
    selected_page_indices = payload.get("selected_page_indices") or []
    if selected_page_indices and not isinstance(selected_page_indices, list):
        return _error_response("selected_page_indices 必须是数组")

    service = get_error_correction_service()
    try:
        result = service.run_split(
            runtime.settings,
            confirmed_answer_layout=confirmed_answer_layout,
            selected_page_indices=selected_page_indices,
            selected_filename=selected_filename,
        )
        return {
            "status": "success",
            "message": f"成功分割 {len(result.get('questions') or [])} 道题目",
            **result,
        }
    except RuntimeError as exc:
        return _error_response(str(exc))
    except Exception as exc:
        return _error_response(str(exc), status_code=500)


@router.post("/export")
async def export_error_correction_questions(request: Request):
    payload = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    selected_ids = payload.get("selected_ids") or []
    if selected_ids and not isinstance(selected_ids, list):
        return _error_response("selected_ids 必须是数组")

    service = get_error_correction_service()
    try:
        result = service.export_questions(selected_ids=selected_ids)
        return {
            "status": "success",
            "message": "导出完成",
            **result,
        }
    except RuntimeError as exc:
        return _error_response(str(exc))
    except Exception as exc:
        return _error_response(str(exc), status_code=500)


@router.get("/exports/{filename:path}")
async def download_error_correction_export(filename: str):
    service = get_error_correction_service()
    try:
        file_path = service.resolve_export_path(filename)
    except ValueError as exc:
        return _error_response(str(exc))
    except FileNotFoundError:
        return _error_response("导出文件不存在", status_code=404)

    media_type, _ = mimetypes.guess_type(str(file_path))
    return FileResponse(
        file_path,
        media_type=media_type or "application/octet-stream",
        filename=file_path.name,
    )

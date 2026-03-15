import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, Request, UploadFile

from .runtime import get_runtime


router = APIRouter(prefix="/api", tags=["knowledge"])


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


@router.post("/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    runtime = get_runtime(request)
    knowledge_provider = runtime.knowledge_provider
    if not hasattr(knowledge_provider, "add_document"):
        return {"status": "error", "message": "Knowledge provider does not support uploads."}

    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, file.filename)
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    try:
        success = knowledge_provider.add_document(file_path)
        return {"status": "success" if success else "error", "filename": file.filename}
    finally:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            os.rmdir(temp_dir)
        except OSError:
            pass


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


@router.delete("/knowledge/files")
async def clear_knowledge_files(request: Request):
    runtime = get_runtime(request)
    knowledge_provider = runtime.knowledge_provider
    if not hasattr(knowledge_provider, "clear_documents"):
        return {"status": "error", "message": "Knowledge provider does not support clear operation."}

    removed = knowledge_provider.clear_documents()
    return {"status": "success", "removed": removed}

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
        if success:
            return {"status": "success", "filename": file.filename}
        # File may have been stored even if indexing failed (unsupported type)
        knowledge_dir = getattr(knowledge_provider, "knowledge_dir", None)
        stored = knowledge_dir and (Path(knowledge_dir) / Path(file.filename).name).exists()
        if stored:
            return {"status": "success", "filename": file.filename,
                    "message": "已保存到资料库（此格式仅支持查阅，暂不支持内容搜索）"}
        return {"status": "error", "filename": file.filename, "message": "上传失败，文件未能保存"}
    except Exception as exc:
        return {"status": "error", "filename": file.filename, "message": str(exc)}
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
    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=safe_name
    )


@router.delete("/knowledge/files")
async def clear_knowledge_files(request: Request):
    runtime = get_runtime(request)
    knowledge_provider = runtime.knowledge_provider
    if not hasattr(knowledge_provider, "clear_documents"):
        return {"status": "error", "message": "Knowledge provider does not support clear operation."}

    removed = knowledge_provider.clear_documents()
    return {"status": "success", "removed": removed}

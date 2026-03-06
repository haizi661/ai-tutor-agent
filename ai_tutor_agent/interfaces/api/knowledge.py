import os
import tempfile

from fastapi import APIRouter, File, Request, UploadFile

from .runtime import get_runtime


router = APIRouter(prefix="/api", tags=["knowledge"])


@router.get("/knowledge")
async def get_knowledge_status(request: Request):
    runtime = get_runtime(request)
    knowledge_provider = runtime.knowledge_provider
    return {
        "enabled": bool(getattr(knowledge_provider, "vector_store", None)),
        "embedding_provider": runtime.settings.embedding_provider,
        "embedding_model_name": runtime.settings.embedding_model_name,
        "knowledge_dir": runtime.settings.knowledge_dir,
        "supports_upload": hasattr(knowledge_provider, "add_document"),
    }


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

    success = knowledge_provider.add_document(file_path)
    return {"status": "success" if success else "error", "filename": file.filename}

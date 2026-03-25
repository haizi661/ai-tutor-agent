import os
import tempfile

from fastapi import APIRouter, File, Request, UploadFile

from .runtime import get_runtime

router = APIRouter(prefix="/api", tags=["knowledge"])


@router.get("/knowledge")
async def get_knowledge_status(request: Request):
    runtime = get_runtime(request)
    knowledge_provider = runtime.knowledge_provider
    hybrid_enabled = bool(getattr(runtime.settings, "rag_hybrid_enabled", False))
    mineru_enabled = bool(getattr(runtime.settings, "rag_mineru_enabled", False))
    mineru_token_value = getattr(runtime.settings, "mineru_api_token", "") or ""
    mineru_token = bool(mineru_token_value.strip())
    parser_backend = "mineru" if mineru_enabled and mineru_token else "pymupdf"
    bm25_ready = bool(getattr(knowledge_provider, "bm25", None))
    return {
        "enabled": bool(getattr(knowledge_provider, "vector_store", None)),
        "embedding_provider": runtime.settings.embedding_provider,
        "embedding_model_name": runtime.settings.embedding_model_name,
        "knowledge_dir": runtime.settings.knowledge_dir,
        "supports_upload": hasattr(knowledge_provider, "add_document"),
        "retrieval_mode": "hybrid" if hybrid_enabled else "vector",
        "bm25_ready": bm25_ready,
        "rag_mineru_enabled": mineru_enabled,
        "rag_mineru_token_configured": mineru_token,
        "pdf_parse_backend": parser_backend,
        "pdf_parse_notice": "当前 PDF 解析器：MinerU（云解析）" if parser_backend == "mineru" else "当前 PDF 解析器：PyMuPDF（本地解析）",
    }


@router.post("/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    runtime = get_runtime(request)
    knowledge_provider = runtime.knowledge_provider
    print(
        f"[RAG][api_upload_start] filename={file.filename} supports_upload={hasattr(knowledge_provider, 'add_document')}",
        flush=True,
    )

    if not hasattr(knowledge_provider, "add_document"):
        print("[RAG][api_upload_error] reason=provider_not_uploadable", flush=True)
        return {"status": "error", "message": "Knowledge provider does not support uploads."}

    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, file.filename)
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)

    result = knowledge_provider.add_document(file_path)
    print(f"[RAG][api_upload_result] filename={file.filename} result={result}", flush=True)

    # 兼容旧版返回 bool 的情况
    if isinstance(result, bool):
        return {"status": "success" if result else "error", "filename": file.filename}

    payload = {
        "status": "success" if result["success"] else "error",
        "filename": result["filename"],
        "chunks": result.get("chunks", 0),
        "message": result.get("message", ""),
    }
    if "parse_backend" in result:
        payload["parse_backend"] = result["parse_backend"]
    if "bm25_rebuilt" in result:
        payload["bm25_rebuilt"] = result["bm25_rebuilt"]
    return payload
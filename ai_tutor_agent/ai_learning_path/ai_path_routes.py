from fastapi import APIRouter
from pydantic import BaseModel

from ai_tutor_agent.ai_learning_path.ai_path_service import get_ai_path_service

router = APIRouter(prefix="/api/ai-path", tags=["ai-path"])


class ChatRequest(BaseModel):
    thread_id: str = "default_ai_path_thread"
    message: str = ""
    choice: str = ""


@router.get("/status")
async def ai_path_status():
    return get_ai_path_service().get_status()


@router.post("/reload")
async def ai_path_reload():
    service = get_ai_path_service()
    service.reload()
    return {"status": "success", "message": "AI路径图谱已重新加载"}


@router.post("/chat")
async def ai_path_chat(payload: ChatRequest):
    return get_ai_path_service().chat(
        thread_id=payload.thread_id,
        message=payload.message,
        choice=payload.choice,
    )


@router.get("/node/{node_id}")
async def ai_path_node(node_id: str):
    return get_ai_path_service().get_node(node_id)

@router.post("/teach")
async def ai_path_teach(payload: ChatRequest):
    return get_ai_path_service().teach_current_node(payload.thread_id)

@router.post("/next")
async def ai_path_next(payload: ChatRequest):
    return get_ai_path_service().advance_to_next_node(payload.thread_id)


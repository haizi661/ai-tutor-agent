from typing import Any

from fastapi import APIRouter, Request
from pydantic import BaseModel

from ai_tutor_agent.ai_learning_path.ai_path_service import get_ai_path_service

router = APIRouter(prefix="/api/ai-path", tags=["ai-path"])


class ChatRequest(BaseModel):
    thread_id: str = "default_ai_path_thread"
    message: str = ""
    choice: str = ""


def _thread_config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def _checkpoint_values(thread_id: str, request: Request) -> dict[str, Any]:
    from ai_tutor_agent.interfaces.api.runtime import get_runtime

    runtime = get_runtime(request)
    checkpoint_store, saver_conn = runtime.checkpoint_factory(runtime.settings.memory_db_path)
    try:
        checkpoint_tuple = checkpoint_store.get_tuple(_thread_config(thread_id))
        if not checkpoint_tuple:
            return {}
        return dict(checkpoint_tuple.checkpoint.get("channel_values") or {})
    finally:
        saver_conn.close()


def _response_message(response: dict[str, Any]) -> str:
    text = str(response.get("message") or "").strip()
    if text:
        return text
    response_type = str(response.get("type") or "").strip()
    if response_type == "plan":
        summary = response.get("summary") if isinstance(response.get("summary"), dict) else {}
        goal = str(summary.get("goal") or "").strip()
        return f"已生成{goal or '人工智能'}学习路径。"
    if response_type == "complete":
        return "这条人工智能学习路径已经完成。"
    return ""


def _persist_ai_path_history(request: Request, payload: ChatRequest, response: dict[str, Any]) -> None:
    from ai_tutor_agent.interfaces.api.runtime import get_runtime
    from ai_tutor_agent.interfaces.api.session import _checkpoint_state_patch

    thread_id = (payload.thread_id or "default_ai_path_thread").strip()
    if not thread_id:
        return

    runtime = get_runtime(request)
    values = _checkpoint_values(thread_id, request)
    history = list(values.get("message_history") or [])
    user_text = (payload.message or payload.choice or "").strip()
    if user_text:
        history.append({
            "role": "user",
            "kind": "ai_path_user",
            "content": user_text,
        })

    assistant_text = _response_message(response)
    if assistant_text:
        history.append({
            "role": "assistant",
            "kind": f"ai_path_{response.get('type') or 'message'}",
            "content": assistant_text,
            "data": {
                "response_type": response.get("type", ""),
                "path": response.get("path", []),
                "current_node": response.get("current_node", ""),
            },
        })

    node = response.get("node") if isinstance(response.get("node"), dict) else {}
    current_node_id = str(response.get("current_node") or node.get("node_id") or "").strip()
    current_node_name = str(node.get("name") or "").strip()
    current_goal = values.get("current_user_goal", "")
    if user_text and not current_goal:
        current_goal = user_text

    _checkpoint_state_patch(
        thread_id,
        runtime,
        {
            "active_course": "artificial_intelligence",
            "ai_path_mode": True,
            "flow_status": "ai_path",
            "current_topic": "人工智能学习路径",
            "current_user_goal": current_goal,
            "message_history": history[-80:],
            "current_node_id": current_node_id,
            "current_node_name": current_node_name or values.get("current_node_name", ""),
            "current_node_status": "in_progress" if current_node_id else values.get("current_node_status", ""),
            "is_assessed": True,
        },
    )


@router.get("/status")
async def ai_path_status():
    return get_ai_path_service().get_status()


@router.post("/reload")
async def ai_path_reload():
    service = get_ai_path_service()
    service.reload()
    return {"status": "success", "message": "AI路径图谱已重新加载"}


@router.post("/chat")
async def ai_path_chat(payload: ChatRequest, request: Request):
    response = get_ai_path_service().chat(
        thread_id=payload.thread_id,
        message=payload.message,
        choice=payload.choice,
    )
    _persist_ai_path_history(request, payload, response)
    return response


@router.get("/node/{node_id}")
async def ai_path_node(node_id: str):
    return get_ai_path_service().get_node(node_id)

@router.post("/teach")
async def ai_path_teach(payload: ChatRequest, request: Request):
    response = get_ai_path_service().teach_current_node(payload.thread_id)
    _persist_ai_path_history(request, payload, response)
    return response

@router.post("/next")
async def ai_path_next(payload: ChatRequest, request: Request):
    response = get_ai_path_service().advance_to_next_node(payload.thread_id)
    _persist_ai_path_history(request, payload, response)
    return response


from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from ...knowledge_map.student_state import StudentStateStore
from .runtime import get_runtime


router = APIRouter(prefix="/api", tags=["wrong_questions"])


class MasterRequest(BaseModel):
    mastered: bool = True


WrongBookItem = dict[str, Any]


def _load_store(request: Request) -> StudentStateStore:
    runtime = get_runtime(request)
    store = getattr(runtime, "student_state_store", None)
    if store is None:
        raise HTTPException(status_code=503, detail="Student state store not available")
    return store


@router.get("/students/{student_id}/wrong-questions")
async def list_wrong_questions(
    student_id: str,
    request: Request,
    node_id: Optional[str] = None,
    mastered: Optional[bool] = None,
    page: int = 1,
    page_size: int = 50,
    sort: str = "latest",
):
    """列出错题本，支持按节点和已掌握状态筛选。"""
    store = _load_store(request)
    try:
        state = store.load(student_id)
    except Exception:
        return {
            "items": [],
            "total": 0,
            "total_all": 0,
            "total_unmastered": 0,
            "total_mastered": 0,
            "page": page,
        }

    items: list[WrongBookItem] = list(state.wrong_question_book or [])

    # Filter by node_id
    if node_id:
        items = [it for it in items if it.get("node_id") == node_id]

    total_all = len(items)
    total_unmastered = sum(1 for it in items if not it.get("mastered"))
    total_mastered = total_all - total_unmastered

    # Filter by mastered status
    if mastered is not None:
        items = [it for it in items if bool(it.get("mastered")) == mastered]

    sort_key = str(sort or "latest").strip()
    if sort_key == "wrong_count":
        items = sorted(
            items,
            key=lambda it: (int(it.get("wrong_count") or 0), str(it.get("time_latest") or "")),
            reverse=True,
        )
    elif sort_key == "reviewed":
        items = sorted(
            items,
            key=lambda it: str(it.get("last_reviewed") or it.get("time_latest") or ""),
        )
    else:
        items = sorted(
            items,
            key=lambda it: (str(it.get("time_latest") or it.get("time_wrong") or ""), int(it.get("wrong_count") or 0)),
            reverse=True,
        )
        items = sorted(
            items,
            key=lambda it: 1 if it.get("mastered") else 0,
        )

    total = len(items)

    # Paginate
    start = (page - 1) * page_size
    paged = items[start:start + page_size]

    return {
        "items": paged,
        "total": total,
        "total_all": total_all,
        "total_unmastered": total_unmastered,
        "total_mastered": total_mastered,
        "page": page,
        "page_size": page_size,
    }


@router.post("/students/{student_id}/wrong-questions/{question_id}/review")
async def mark_reviewed(student_id: str, question_id: str, request: Request):
    """标记错题已复习。"""
    store = _load_store(request)
    updated = False

    def mark(state):
        nonlocal updated
        updated = state.wb_mark_reviewed(question_id)
        return state

    state = store.update(student_id, mark)
    if not updated:
        raise HTTPException(status_code=404, detail="Wrong question not found")
    return {"status": "ok", "question_id": question_id}


@router.post("/students/{student_id}/wrong-questions/{question_id}/master")
async def toggle_mastered(student_id: str, question_id: str, req: MasterRequest, request: Request):
    """标记错题已掌握/未掌握。"""
    store = _load_store(request)
    updated = False

    def mark(state):
        nonlocal updated
        updated = state.wb_mark_mastered(question_id, req.mastered)
        return state

    state = store.update(student_id, mark)
    if not updated:
        raise HTTPException(status_code=404, detail="Wrong question not found")
    return {"status": "ok", "question_id": question_id, "mastered": req.mastered}

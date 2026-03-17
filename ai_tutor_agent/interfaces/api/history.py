import sqlite3
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from .auth import (
    ensure_thread_access,
    get_current_user,
    list_user_thread_ids,
    remove_thread_owner,
)
from .runtime import get_runtime


router = APIRouter(prefix="/api/history", tags=["history"])

PRE_TOPIC_FLOW_STATUSES = {"greeting", "topic_intake", "meta_qa", "smalltalk"}


def _serialize_state(values: dict[str, Any]) -> dict[str, Any]:
    return {
        "current_topic": values.get("current_topic", ""),
        "proposed_topic": values.get("proposed_topic", ""),
        "tutor_content": values.get("tutor_content", ""),
        "tester_question": values.get("tester_question", ""),
        "user_answer": values.get("user_answer", ""),
        "score": values.get("score", 0),
        "logic_score": values.get("logic_score", 0),
        "concept_score": values.get("concept_score", 0),
        "feedback": values.get("feedback", ""),
        "assessment_questions": values.get("assessment_questions", []),
        "assessment_answers": values.get("assessment_answers", {}),
        "assessment_radar": values.get("assessment_radar", {}),
        "assessment_result": values.get("assessment_result", ""),
        "is_assessed": values.get("is_assessed", False),
        "flow_status": values.get("flow_status", "greeting"),
        "conversation_history": values.get("conversation_history", []),
    }


def _checkpoint_summary(thread_id: str, checkpoint_tuple) -> dict[str, Any]:
    values = checkpoint_tuple.checkpoint.get("channel_values", {})
    flow_status = values.get("flow_status", "greeting")
    current_topic = values.get("current_topic", "")
    proposed_topic = values.get("proposed_topic", "")
    if flow_status == "awaiting_topic_confirmation" and proposed_topic:
        display_title = f"待确认：{proposed_topic}"
    elif flow_status in PRE_TOPIC_FLOW_STATUSES:
        display_title = "未确认主题"
    else:
        display_title = current_topic or thread_id
    return {
        "thread_id": thread_id,
        "current_topic": current_topic,
        "display_title": display_title,
        "flow_status": flow_status,
        "is_assessed": values.get("is_assessed", False),
        "score": values.get("score", 0),
        "updated_at": checkpoint_tuple.checkpoint.get("ts"),
        "checkpoint_id": checkpoint_tuple.checkpoint.get("id"),
    }


def _history_entries(checkpoint_store, thread_id: str, *, limit: int = 20) -> list[dict[str, Any]]:
    config = {"configurable": {"thread_id": thread_id}}
    entries = []
    for checkpoint_tuple in checkpoint_store.list(config, limit=limit):
        values = checkpoint_tuple.checkpoint.get("channel_values", {})
        entries.append(
            {
                "checkpoint_id": checkpoint_tuple.checkpoint.get("id"),
                "updated_at": checkpoint_tuple.checkpoint.get("ts"),
                "source": checkpoint_tuple.metadata.get("source"),
                "step": checkpoint_tuple.metadata.get("step"),
                "flow_status": values.get("flow_status", "greeting"),
                "current_topic": values.get("current_topic", ""),
                "score": values.get("score", 0),
            }
        )
    return entries


@router.get("")
async def get_history(request: Request):
    runtime = get_runtime(request)
    user = get_current_user(request)
    db_path = runtime.settings.memory_db_path
    checkpoint_store, saver_conn = runtime.checkpoint_factory(db_path)
    try:
        try:
            thread_ids = list_user_thread_ids(request, user["id"], limit=50)
        except sqlite3.OperationalError:
            return {"threads": [], "items": []}

        items = []
        for thread_id in thread_ids:
            checkpoint_tuple = checkpoint_store.get_tuple({"configurable": {"thread_id": thread_id}})
            if checkpoint_tuple:
                items.append(_checkpoint_summary(thread_id, checkpoint_tuple))

        return {
            "threads": [item["thread_id"] for item in items],
            "items": items,
        }
    finally:
        saver_conn.close()


@router.get("/{thread_id}")
async def get_history_detail(thread_id: str, request: Request):
    runtime = get_runtime(request)
    user = get_current_user(request)
    ensure_thread_access(request, user["id"], thread_id, auto_bind=False)
    session = runtime.session_manager.refresh_status(thread_id)
    db_path = runtime.settings.memory_db_path
    checkpoint_store, saver_conn = runtime.checkpoint_factory(db_path)
    try:
        checkpoint_tuple = checkpoint_store.get_tuple({"configurable": {"thread_id": thread_id}})
        if checkpoint_tuple is None:
            raise HTTPException(status_code=404, detail=f"Unknown thread_id: {thread_id}")

        values = checkpoint_tuple.checkpoint.get("channel_values", {})
        return {
            "thread_id": thread_id,
            "summary": _checkpoint_summary(thread_id, checkpoint_tuple),
            "state": _serialize_state(values),
            "runtime": {
                "is_running": bool(session.get("is_running")),
                "awaiting_input": bool(session.get("awaiting_input")),
            },
            "checkpoints": _history_entries(checkpoint_store, thread_id),
        }
    finally:
        saver_conn.close()


@router.delete("/{thread_id}")
async def delete_history(thread_id: str, request: Request):
    runtime = get_runtime(request)
    user = get_current_user(request)
    ensure_thread_access(request, user["id"], thread_id, auto_bind=False)
    db_path = runtime.settings.memory_db_path
    checkpoint_store, saver_conn = runtime.checkpoint_factory(db_path)
    try:
        try:
            checkpoint_store.delete_thread(thread_id)
        except sqlite3.OperationalError:
            pass
        runtime.session_manager.remove(thread_id)
        remove_thread_owner(request, thread_id)
        return {"status": "success"}
    finally:
        saver_conn.close()

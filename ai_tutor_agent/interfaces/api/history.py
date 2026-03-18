import sqlite3
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from .runtime import get_runtime


router = APIRouter(prefix="/api/history", tags=["history"])

PRE_TOPIC_FLOW_STATUSES = {"greeting", "topic_intake", "meta_qa", "smalltalk"}


def _serialize_state(values: dict[str, Any]) -> dict[str, Any]:
    return {
        "student_id": values.get("student_id", "default_student"), # 新增学生id相关
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
    db_path = runtime.settings.memory_db_path
    checkpoint_store, saver_conn = runtime.checkpoint_factory(db_path)
    try:
        try:
            with sqlite3.connect(db_path) as conn:
                rows = conn.execute(
                    """
                    SELECT thread_id
                    FROM checkpoints
                    GROUP BY thread_id
                    ORDER BY MAX(rowid) DESC
                    LIMIT 50
                    """
                ).fetchall()
        except sqlite3.OperationalError:
            return {"threads": [], "items": []}

        items = []
        for (thread_id,) in rows:
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
    db_path = runtime.settings.memory_db_path
    checkpoint_store, saver_conn = runtime.checkpoint_factory(db_path)
    try:
        try:
            checkpoint_store.delete_thread(thread_id)
        except sqlite3.OperationalError:
            pass
        runtime.session_manager.remove(thread_id)
        return {"status": "success"}
    finally:
        saver_conn.close()
#加一个监听器，实现10轮之前的对话被冷处理
async def check_and_trigger_cold_memory(thread_id: str, student_id: str, runtime):
    """检查是否达到10轮，触发冷处理总结"""
    db_path = runtime.settings.memory_db_path
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. 统计当前 thread_id 在 LangGraph 里的 checkpoints 数量
    # 这里简化处理：每当整除 10 时触发一次总结
    cursor.execute("SELECT COUNT(*) FROM checkpoints WHERE thread_id = ?", (thread_id,))
    count = cursor.fetchone()[0]
    
    # 把 if count > 0 and count % 10 == 0: 
# 临时改为：
    if count >= 0: 
        print("📢 正在执行强制总结测试...")

        print(f"检测到第 {count} 轮对话，启动冷处理摘要...")
        # 这里以后会调用 LLM 总结并存入 long_term_memory 表
        # 暂时先打个日志，确保逻辑能跑通
    conn.close()
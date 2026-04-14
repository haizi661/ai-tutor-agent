from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from .runtime import get_runtime


router = APIRouter(prefix="/api/history", tags=["history"])
messages_router = APIRouter(prefix="/api/messages", tags=["history"])

PRE_TOPIC_FLOW_STATUSES = {"greeting", "topic_intake", "meta_qa", "smalltalk"}


class ThreadTitlePayload(BaseModel):
    title: str = ""


def _ensure_custom_title_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS history_custom_titles (
            thread_id TEXT PRIMARY KEY,
            custom_title TEXT NOT NULL,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


def _normalize_custom_title(value: str) -> str:
    return " ".join(str(value or "").split()).strip()


def _load_custom_titles(conn: sqlite3.Connection) -> dict[str, str]:
    _ensure_custom_title_table(conn)
    rows = conn.execute("SELECT thread_id, custom_title FROM history_custom_titles").fetchall()
    return {
        str(thread_id): str(title).strip()
        for thread_id, title in rows
        if str(thread_id).strip() and str(title).strip()
    }


def _get_custom_title(conn: sqlite3.Connection, thread_id: str) -> str:
    _ensure_custom_title_table(conn)
    row = conn.execute(
        "SELECT custom_title FROM history_custom_titles WHERE thread_id = ?",
        (thread_id,),
    ).fetchone()
    return str(row[0]).strip() if row and str(row[0]).strip() else ""


def _set_custom_title(conn: sqlite3.Connection, thread_id: str, custom_title: str) -> str:
    _ensure_custom_title_table(conn)
    normalized = _normalize_custom_title(custom_title)
    if normalized:
        conn.execute("DELETE FROM history_custom_titles WHERE thread_id = ?", (thread_id,))
        conn.execute(
            """
            INSERT INTO history_custom_titles(thread_id, custom_title, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            """,
            (thread_id, normalized),
        )
    else:
        conn.execute("DELETE FROM history_custom_titles WHERE thread_id = ?", (thread_id,))
    conn.commit()
    return normalized


def _delete_custom_title(conn: sqlite3.Connection, thread_id: str) -> None:
    _ensure_custom_title_table(conn)
    conn.execute("DELETE FROM history_custom_titles WHERE thread_id = ?", (thread_id,))
    conn.commit()


def replay_graph_markers(values: dict[str, Any]) -> list[dict[str, Any]]:
    """从已保存的状态中重建 UKG graph.node_update 事件列表，
    供前端恢复会话时一次性重放。"""
    ukg = values.get("user_knowledge_graph") or {}
    markers: list[dict[str, Any]] = []
    for title, entry in ukg.items():
        if not isinstance(entry, dict):
            continue
        status = str(entry.get("status") or "not_started").strip()
        if status == "not_started":
            continue
        markers.append({
            "title": title,
            "status": status,
            "turn_count": int(entry.get("turn_count") or 0),
        })
    return markers


def _serialize_state(values: dict[str, Any]) -> dict[str, Any]:
    return {
        "current_topic": values.get("current_topic", ""),
        "current_user_goal": values.get("current_user_goal", ""),
        "session_goal": values.get("session_goal", ""),
        "turn_goal": values.get("turn_goal", ""),
        "proposed_topic": values.get("proposed_topic", ""),
        "topic_focus": values.get("topic_focus", ""),
        "topic_background": values.get("topic_background", ""),
        "topic_detail_summary": values.get("topic_detail_summary", ""),
        "topic_starter_options": values.get("topic_starter_options", []),
        "topic_clarify_rounds": values.get("topic_clarify_rounds", 0),
        "tutor_content": values.get("tutor_content", ""),
        "tester_question": values.get("tester_question", ""),
        "tester_question_type": values.get("tester_question_type", ""),
        "tester_question_template": values.get("tester_question_template", ""),
        "user_answer": values.get("user_answer", ""),
        "score": values.get("score", 0),
        "logic_score": values.get("logic_score", 0),
        "concept_score": values.get("concept_score", 0),
        "feedback": values.get("feedback", ""),
        "rubric_feedback": values.get("rubric_feedback", []),
        "model_answer": values.get("model_answer", ""),
        "misconceptions": values.get("misconceptions", []),
        "next_review_points": values.get("next_review_points", []),
        "is_correct_direction": values.get("is_correct_direction", True),
        "needs_hint": values.get("needs_hint", False),
        "difficulty_level": values.get("difficulty_level", 3),
        "attempt_count": values.get("attempt_count", 0),
        "score_history": values.get("score_history", []),
        "post_eval_choice": values.get("post_eval_choice", ""),
        "practice_generation_mode": values.get("practice_generation_mode", ""),
        "pending_interaction_kind": values.get("pending_interaction_kind", ""),
        "pending_interaction_prompt": values.get("pending_interaction_prompt", ""),
        "pending_interaction_options": values.get("pending_interaction_options", []),
        "pending_interaction_recommended": values.get("pending_interaction_recommended", ""),
        "coach_content": values.get("coach_content", ""),
        "tutor_citations": values.get("tutor_citations", []),
        "tutor_evidence": values.get("tutor_evidence", []),
        "graph_anchor_id": values.get("graph_anchor_id", ""),
        "graph_anchor_title": values.get("graph_anchor_title", ""),
        "graph_anchor_filename": values.get("graph_anchor_filename", ""),
        "graph_prerequisites": values.get("graph_prerequisites", []),
        "graph_neighbors": values.get("graph_neighbors", []),
        "graph_learning_objectives": values.get("graph_learning_objectives", []),
        "graph_must_know": values.get("graph_must_know", []),
        "graph_common_errors": values.get("graph_common_errors", []),
        "graph_target_mastery_level": values.get("graph_target_mastery_level", ""),
        "graph_difficulty": values.get("graph_difficulty", ""),
        "graph_next_steps": values.get("graph_next_steps", []),
        "skip_reason": values.get("skip_reason", ""),
        "interrupt_query": values.get("interrupt_query", ""),
        "resume_tester": values.get("resume_tester", False),
        "conversation_history": values.get("conversation_history", []),
        "message_history": values.get("message_history", []),
        "assessment_questions": values.get("assessment_questions", []),
        "assessment_answers": values.get("assessment_answers", {}),
        "assessment_radar": values.get("assessment_radar", {}),
        "assessment_result": values.get("assessment_result", ""),
        "assessment_concept_gaps": values.get("assessment_concept_gaps", {}),
        "assessment_state": values.get("assessment_state", {}),
        "user_knowledge_graph": values.get("user_knowledge_graph", {}),
        "is_assessed": values.get("is_assessed", False),
        "flow_status": values.get("flow_status", "greeting"),
    }


def _checkpoint_summary(thread_id: str, checkpoint_tuple, alias_title: str = "") -> dict[str, Any]:
    values = checkpoint_tuple.checkpoint.get("channel_values", {})
    flow_status = values.get("flow_status", "greeting")
    current_topic = values.get("current_topic", "")
    proposed_topic = values.get("proposed_topic", "")
    custom_title = _normalize_custom_title(alias_title)
    if custom_title:
        display_title = custom_title
    elif flow_status == "awaiting_topic_confirmation" and proposed_topic:
        display_title = f"待确认：{proposed_topic}"
    elif flow_status in PRE_TOPIC_FLOW_STATUSES:
        display_title = "未确认主题"
    else:
        display_title = current_topic or thread_id
    return {
        "thread_id": thread_id,
        "current_topic": current_topic,
        "display_title": display_title,
        "custom_title": custom_title,
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


def _build_evaluator_card(values: dict[str, Any]) -> str:
    score = values.get("score", 0)
    logic = values.get("logic_score", 0)
    concept = values.get("concept_score", 0)
    feedback = values.get("feedback", "") or "这轮评估已完成。"
    lines = [
        "### 最近一轮评估",
        "",
        f"- 总分：**{score}**",
        f"- 逻辑：**{logic}**",
        f"- 概念：**{concept}**",
        "",
        f"简要诊断：{feedback}",
    ]

    rubric = values.get("rubric_feedback") or []
    if rubric:
        lines.append("")
        lines.append("量表依据：")
        lines.extend([f"- {item}" for item in rubric])

    next_review_points = values.get("next_review_points") or []
    if next_review_points:
        lines.append("")
        lines.append("建议复习：")
        lines.extend([f"- {item}" for item in next_review_points])
    if values.get("needs_hint"):
        lines.append("")
        lines.append("下一步：先看提示。")

    return "\n".join(lines)


def _build_evidence_panel(evidence: list[dict[str, Any]]) -> str:
    if not evidence:
        return ""

    lines = ["### 证据来源"]
    seen: set[tuple[str, str]] = set()
    current_group = ""

    for item in evidence[:4]:
        rank = item.get("rank")
        label = str(item.get("display_label") or item.get("filename") or item.get("title") or "").strip()
        if not label:
            continue

        key = (str(item.get("source_type", "")), label)
        if key in seen:
            continue
        seen.add(key)

        source_type = str(item.get("source_type", "")).strip()
        source_scope = str(item.get("source_scope", "")).strip()
        group_label = "外部检索" if source_type == "web_search" else ("课程图谱" if source_scope == "course_primary" else "上传资料")
        if group_label != current_group:
            current_group = group_label
            lines.append("")
            lines.append(f"**{group_label}**")

        url = str(item.get("url", "")).strip()
        prefix = f"[{rank}] " if rank else ""
        lines.append("")
        lines.append(f"{prefix}{label}")
        if url:
            lines.append(f"<{url}>")

        snippet = str(item.get("snippet", "")).strip()
        if snippet:
            one_line_snippet = " ".join(snippet.split())
            lines.append(f"> {one_line_snippet}")

    return "\n".join(lines)


def _reconstruct_messages(checkpoint_store, thread_id: str, *, limit: int = 240) -> list[dict[str, Any]]:
    config = {"configurable": {"thread_id": thread_id}}
    timeline: list[dict[str, Any]] = []

    for checkpoint_tuple in checkpoint_store.list(config, limit=limit):
        values = checkpoint_tuple.checkpoint.get("channel_values", {})
        timeline.append(
            {
                "updated_at": checkpoint_tuple.checkpoint.get("ts") or "",
                "values": values,
            }
        )

    if not timeline:
        return []

    timeline.sort(key=lambda item: item["updated_at"])
    messages: list[dict[str, Any]] = []
    previous_values: dict[str, Any] = {}

    def push(role: str, kind: str, content: str, updated_at: str, *, tone: str = "info", data: Any = None) -> None:
        normalized_role = "agent" if role == "assistant" else role
        text = (content or "").strip()
        if not text:
            return
        if messages:
            last = messages[-1]
            if last["role"] == normalized_role and last["kind"] == kind and last["content"] == text:
                return
        messages.append(
            {
                "role": normalized_role,
                "kind": kind,
                "content": text,
                "updated_at": updated_at,
                "tone": tone,
                "data": data,
            }
        )

    for item in timeline:
        updated_at = item["updated_at"]
        values = item["values"]

        current_message_history = values.get("message_history") or []
        previous_message_history = previous_values.get("message_history") or []
        if len(current_message_history) > len(previous_message_history):
            for entry in current_message_history[len(previous_message_history) :]:
                push(
                    str(entry.get("role", "user")) or "user",
                    str(entry.get("kind", "user_message")) or "user_message",
                    str(entry.get("content", "")),
                    updated_at,
                    data=entry.get("data"),
                )

        assessment_questions = values.get("assessment_questions") or []
        previous_assessment_questions = previous_values.get("assessment_questions") or []
        if assessment_questions and assessment_questions != previous_assessment_questions:
            push(
                "agent",
                "assessment_form",
                "学前小测已经准备好了。你先做完这一轮，我再按你的起点来调讲解深度。",
                updated_at,
                data={"questions": assessment_questions},
            )

        awaiting_topic_confirmation = values.get("flow_status") == "awaiting_topic_confirmation"
        previous_awaiting_topic_confirmation = previous_values.get("flow_status") == "awaiting_topic_confirmation"
        proposed_topic = str(values.get("proposed_topic", "") or "").strip()
        if proposed_topic and (
            not previous_awaiting_topic_confirmation
            or proposed_topic != str(previous_values.get("proposed_topic", "") or "").strip()
        ):
            push(
                "agent",
                "topic_confirmation_card",
                (
                    f"我先把这次主题收成【{proposed_topic}】。"
                    "如果我理解的重点没跑偏，你再决定这次怎么开始。"
                ),
                updated_at,
                data={
                    "proposed_topic": proposed_topic,
                    "detail_summary": values.get("topic_detail_summary", ""),
                    "topic_focus": values.get("topic_focus", ""),
                    "topic_background": values.get("topic_background", ""),
                    "topic_starter_options": values.get("topic_starter_options", []),
                    "clarify_rounds": values.get("topic_clarify_rounds", 0),
                },
            )

        assessment_result = values.get("assessment_result", "")
        if assessment_result and assessment_result != previous_values.get("assessment_result", ""):
            push("agent", "assessment_result", assessment_result, updated_at)

        tutor_content = values.get("tutor_content", "")
        if tutor_content and tutor_content != previous_values.get("tutor_content", ""):
            push("agent", "tutor", tutor_content, updated_at)

        tutor_evidence = values.get("tutor_evidence") or []
        if tutor_evidence and tutor_evidence != previous_values.get("tutor_evidence", []):
            evidence_panel = _build_evidence_panel(tutor_evidence)
            if evidence_panel:
                push("system", "tutor_evidence", evidence_panel, updated_at, data={"evidence": tutor_evidence})

        coach_content = values.get("coach_content", "")
        if coach_content and coach_content != previous_values.get("coach_content", ""):
            push("agent", "coach", coach_content, updated_at)

        tester_question = values.get("tester_question", "")
        if tester_question and tester_question != previous_values.get("tester_question", ""):
            push("agent", "tester_question", tester_question, updated_at)

        user_answer = values.get("user_answer", "")
        if user_answer and user_answer != previous_values.get("user_answer", ""):
            push("user", "user_answer", user_answer, updated_at)

        feedback_changed = (
            values.get("score", 0) != previous_values.get("score", 0)
            or values.get("logic_score", 0) != previous_values.get("logic_score", 0)
            or values.get("concept_score", 0) != previous_values.get("concept_score", 0)
            or values.get("feedback", "") != previous_values.get("feedback", "")
            or values.get("rubric_feedback", []) != previous_values.get("rubric_feedback", [])
        )
        if feedback_changed and (values.get("score", 0) or values.get("feedback", "")):
            push("agent", "evaluator_card", _build_evaluator_card(values), updated_at)

        awaiting_interrupt_confirmation = values.get("flow_status") == "awaiting_interrupt_confirmation"
        previous_awaiting_interrupt_confirmation = previous_values.get("flow_status") == "awaiting_interrupt_confirmation"
        if awaiting_interrupt_confirmation and not previous_awaiting_interrupt_confirmation:
            push(
                "agent",
                "interrupt_confirmation_card",
                "如果这一步已经顺了，我们就回到刚才那道题；如果你还想追问，也可以继续问我。",
                updated_at,
                data={"requires_confirmation": True},
            )

        previous_values = values

    if not any(item["role"] == "user" for item in messages):
        latest_values = timeline[-1]["values"]
        fallback_user_text = (
            str(latest_values.get("current_user_goal", "") or "").strip()
            or str(latest_values.get("proposed_topic", "") or "").strip()
            or str(latest_values.get("current_topic", "") or "").strip()
        )
        if fallback_user_text:
            messages.insert(
                0,
                {
                    "role": "user",
                    "kind": "topic_input",
                    "content": fallback_user_text,
                    "updated_at": timeline[0]["updated_at"],
                    "tone": "info",
                    "data": None,
                },
            )

    return messages


@router.get("")
async def get_history(request: Request):
    runtime = get_runtime(request)
    db_path = runtime.settings.memory_db_path
    checkpoint_store, saver_conn = runtime.checkpoint_factory(db_path)
    try:
        try:
            with sqlite3.connect(db_path) as conn:
                alias_by_thread = _load_custom_titles(conn)
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
                items.append(
                    _checkpoint_summary(
                        thread_id,
                        checkpoint_tuple,
                        alias_title=alias_by_thread.get(str(thread_id), ""),
                    )
                )

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
        with sqlite3.connect(db_path) as conn:
            alias_title = _get_custom_title(conn, thread_id)
        return {
            "thread_id": thread_id,
            "summary": _checkpoint_summary(thread_id, checkpoint_tuple, alias_title=alias_title),
            "state": _serialize_state(values),
            "graph_markers_replay": replay_graph_markers(values),
            "runtime": {
                "is_running": bool(session.get("is_running")),
                "awaiting_input": bool(session.get("awaiting_input")),
                "awaiting_input_state": session.get("awaiting_input_state"),
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
        with sqlite3.connect(db_path) as conn:
            _delete_custom_title(conn, thread_id)
        runtime.session_manager.remove(thread_id)
        return {"status": "success"}
    finally:
        saver_conn.close()


@router.put("/{thread_id}/title")
async def update_history_title(thread_id: str, payload: ThreadTitlePayload, request: Request):
    runtime = get_runtime(request)
    db_path = runtime.settings.memory_db_path
    checkpoint_store, saver_conn = runtime.checkpoint_factory(db_path)
    try:
        checkpoint_tuple = checkpoint_store.get_tuple({"configurable": {"thread_id": thread_id}})
        if checkpoint_tuple is None:
            raise HTTPException(status_code=404, detail=f"Unknown thread_id: {thread_id}")

        normalized = _normalize_custom_title(payload.title)
        if len(normalized) > 48:
            raise HTTPException(status_code=400, detail="目录名请控制在 48 个字符以内")

        with sqlite3.connect(db_path) as conn:
            custom_title = _set_custom_title(conn, thread_id, normalized)

        return {
            "thread_id": thread_id,
            "custom_title": custom_title,
            "summary": _checkpoint_summary(thread_id, checkpoint_tuple, alias_title=custom_title),
        }
    finally:
        saver_conn.close()


@messages_router.get("/{thread_id}")
async def get_messages(thread_id: str, request: Request):
    runtime = get_runtime(request)
    db_path = runtime.settings.memory_db_path
    checkpoint_store, saver_conn = runtime.checkpoint_factory(db_path)
    try:
        checkpoint_tuple = checkpoint_store.get_tuple({"configurable": {"thread_id": thread_id}})
        if checkpoint_tuple is None:
            raise HTTPException(status_code=404, detail=f"Unknown thread_id: {thread_id}")

        values = checkpoint_tuple.checkpoint.get("channel_values", {})
        return {
            "thread_id": thread_id,
            "items": _reconstruct_messages(checkpoint_store, thread_id),
            "state": _serialize_state(values),
        }
    finally:
        saver_conn.close()

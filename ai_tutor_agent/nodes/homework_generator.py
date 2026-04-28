from __future__ import annotations

from typing import Any

from ..core.events import make_event
from ..core.learning_support import assign_homework_items, build_homework_items
from ..core.ports import RuntimeContext
from ..core.state import AgentState


def _string_list(values: Any) -> list[str]:
    if isinstance(values, list):
        return [str(item).strip() for item in values if str(item).strip()]
    return []


def _node_name(node: dict[str, Any], node_id: str) -> str:
    return str(node.get("name") or node.get("title") or node_id).strip()


def _build_fallback_homework_item(graph_pipeline: Any, state: AgentState) -> list[dict[str, Any]]:
    node_id = str(state.get("current_node_id") or state.get("graph_anchor_id") or "").strip()
    if not node_id:
        return []
    node_map = dict(getattr(graph_pipeline, "node_map", {}) or {})
    node = node_map.get(node_id) or {}
    title = _node_name(node, node_id) or str(state.get("current_node_name") or state.get("graph_anchor_title") or node_id).strip()
    must_know = _string_list(node.get("core_concepts")) or _string_list(state.get("graph_must_know"))
    focus = "、".join(must_know[:2]) if must_know else title
    return [
        {
            "question_id": f"HW-{node_id}",
            "node_id": node_id,
            "title": title,
            "type": "subjective_review",
            "source": "ai_generated_template",
            "prompt": f"围绕“{title}”完成一道复习题，说明 {focus} 的核心概念、关键判断依据，并结合一个具体情境展开说明。",
            "reference_answer": f"参考答案应覆盖：{focus}；说明它在“{title}”中的作用；最后给出一个情境化判断步骤。",
            "rubric": ["概念定义准确", "能说明判断依据", "能结合具体情境", "表达有步骤"],
            "covered_node_ids": [node_id],
        }
    ]


def _enrich_homework_items(items: list[dict[str, Any]], graph_pipeline: Any) -> list[dict[str, Any]]:
    node_map = dict(getattr(graph_pipeline, "node_map", {}) or {})
    enriched: list[dict[str, Any]] = []
    for item in items:
        normalized = dict(item)
        node_id = str(normalized.get("node_id") or "").strip()
        node = node_map.get(node_id) or {}
        title = str(normalized.get("title") or _node_name(node, node_id) or node_id).strip()
        must_know = _string_list(node.get("core_concepts"))
        focus = "、".join(must_know[:2]) if must_know else title
        normalized.setdefault("source", "ai_generated_template")
        normalized.setdefault("reference_answer", f"参考答案应覆盖：{focus}；说明该节点的核心概念、判断依据，并能结合具体情境展开。")
        normalized.setdefault("rubric", ["概念定义准确", "判断依据清楚", "能结合情境", "表达有层次"])
        normalized.setdefault("covered_node_ids", [node_id] if node_id else [])
        enriched.append(normalized)
    return enriched


def _format_homework_content(items: list[dict[str, Any]]) -> str:
    if not items:
        return "### 今日作业\n当前没有生成有效作业，请下次继续从图谱节点学习。"
    lines = ["### 今日作业"]
    for index, item in enumerate(items, start=1):
        lines.append(f"{index}. {item.get('prompt')}")
        reference = str(item.get("reference_answer") or "").strip()
        if reference:
            lines.append(f"   参考答案要点：{reference}")
        rubric = _string_list(item.get("rubric"))
        if rubric:
            lines.append(f"   评分要点：{'；'.join(rubric)}")
    return "\n".join(lines)


def _collect_relevant_node_ids(state: AgentState, snapshot: dict[str, Any]) -> list[str]:
    node_ids: list[str] = []
    current = str(state.get("current_node_id") or state.get("graph_anchor_id") or "").strip()
    if current:
        node_ids.append(current)
    for nid in list(snapshot.get("visited_nodes") or []):
        nid_str = str(nid).strip()
        if nid_str and nid_str not in node_ids:
            node_ids.append(nid_str)
    daily = dict(snapshot.get("daily_learning_records") or {})
    for day_nodes in daily.values():
        for nid in list(day_nodes or []):
            nid_str = str(nid).strip()
            if nid_str and nid_str not in node_ids:
                node_ids.append(nid_str)
    return node_ids


def build_homework_generator_node(runtime: RuntimeContext):
    event_sink = runtime.event_sink

    def node(state: AgentState) -> dict:
        graph_pipeline = getattr(runtime, "graph_rag_pipeline", None)
        student_state_store = getattr(runtime, "student_state_store", None)
        question_bank = getattr(runtime, "question_bank_provider", None)
        student_id = str(state.get("student_id") or "default_student").strip() or "default_student"
        snapshot = dict(state.get("student_state_snapshot") or {})

        event_sink.emit(
            make_event(
                "node.start",
                "homework_generator",
                message="开始根据今天和此前的图谱学习记录生成作业。",
                data={"student_id": student_id, "current_node_id": state.get("current_node_id", "")},
            )
        )

        homework_items: list[dict[str, Any]] = []
        # 优先从题库取大题
        if question_bank is not None and hasattr(question_bank, "get_homework_questions"):
            relevant_nodes = _collect_relevant_node_ids(state, snapshot)
            if relevant_nodes:
                homework_items = question_bank.get_homework_questions(relevant_nodes, k=5)
        # 题库不足时，用图谱生成补充
        if not homework_items:
            homework_items = build_homework_items(
                graph_pipeline=graph_pipeline,
                student_state_snapshot=snapshot,
                limit=5,
            )
        if not homework_items:
            homework_items = _build_fallback_homework_item(graph_pipeline, state)
        homework_items = _enrich_homework_items(homework_items, graph_pipeline)

        updated_snapshot = assign_homework_items(
            student_state_store,
            student_id=student_id,
            homework_items=homework_items,
        )
        if updated_snapshot:
            snapshot = updated_snapshot

        tutor_content = _format_homework_content(homework_items)
        event_sink.emit(
            make_event(
                "node.stream",
                "homework_generator",
                data={"text": tutor_content},
            )
        )
        event_sink.emit(
            make_event(
                "node.complete",
                "homework_generator",
                message="今日作业已生成并写入学生记录。" if homework_items else "当前没有可生成的作业。",
                data={"homework_count": len(homework_items)},
            )
        )
        return {
            "tutor_content": tutor_content,
            "flow_status": "homework_assigned" if homework_items else "normal",
            "homework_items": homework_items,
            "homework_status": "assigned" if homework_items else "none",
            "student_state_snapshot": snapshot,
            "learning_phase": "daily_wrapup",
            "learning_resume_target": "session_resume_router",
            "learning_resume_reason": "homework_assigned" if homework_items else "homework_generation_empty",
            "pending_interaction_kind": "",
            "pending_interaction_prompt": "",
            "pending_interaction_options": [],
            "pending_interaction_recommended": "",
            "pending_interaction_answer": "",
        }

    return node

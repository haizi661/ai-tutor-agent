from __future__ import annotations

import re
from typing import Any

from ai_tutor_agent.knowledge_map.student_state import StudentState, StudentStateStore, now_ts


MEDIA_MARKER_RE = re.compile(r"\[\[MEDIA:([^\]]+)\]\]")

# Maximum message_history entries to keep. Oldest entries are dropped first.
MAX_MESSAGE_HISTORY = 200


def trim_message_history(history: list[dict[str, Any]], limit: int = MAX_MESSAGE_HISTORY) -> list[dict[str, Any]]:
    """Keep only the most recent *limit* entries to prevent checkpoint bloat."""
    if len(history) <= limit:
        return history
    return history[-limit:]


def _string_list(values: Any) -> list[str]:
    if isinstance(values, list):
        return [str(item).strip() for item in values if str(item).strip()]
    if isinstance(values, tuple):
        return [str(item).strip() for item in values if str(item).strip()]
    text = str(values or "").strip()
    if not text:
        return []
    if text.startswith("[") and text.endswith("]"):
        text = text[1:-1]
    parts = re.split(r"[;；\n,，、]+", text)
    return [part.strip().strip("'\"") for part in parts if part.strip().strip("'\"")]
    return []


def _node_name(node_map: dict[str, dict[str, Any]], node_id: str) -> str:
    node = node_map.get(str(node_id or "").strip()) or {}
    return str(node.get("name") or "").strip()


def _resolve_node_refs(node_map: dict[str, dict[str, Any]], refs: Any) -> list[str]:
    titles: list[str] = []
    for ref in _string_list(refs):
        title = _node_name(node_map, ref)
        titles.append(title or ref)
    return titles


def normalize_graph_answer(answer: str, media_items: list[dict[str, Any]] | None = None) -> str:
    text = str(answer or "").strip()
    if not text:
        return ""
    labels_by_ref = {
        str(item.get("reference") or "").strip(): str(item.get("display_label") or "相关图表").strip()
        for item in (media_items or [])
        if str(item.get("reference") or "").strip()
    }

    def replace(match: re.Match[str]) -> str:
        ref = match.group(1).strip()
        label = labels_by_ref.get(ref, "相关图表")
        return f"（可结合{label}理解）"

    return MEDIA_MARKER_RE.sub(replace, text)


def build_graph_citation_plan(graph_result: dict[str, Any], *, limit: int = 4) -> list[dict[str, Any]]:
    items = list(graph_result.get("evidence_items") or [])
    plan: list[dict[str, Any]] = []
    for rank, item in enumerate(items[:limit], start=1):
        snippet = str(item.get("text") or "").strip()
        if not snippet:
            continue
        plan.append(
            {
                "rank": rank,
                "filename": str(item.get("node_name") or item.get("node_id") or "图谱证据").strip(),
                "page": None,
                "section": str(item.get("attribute") or "").strip(),
                "chunk_index": None,
                "source_scope": "knowledge_map",
                "sources": ["graph_rag"],
                "rrf_score": float(limit - rank + 1),
                "snippet": snippet,
                "source_type": "graph_rag",
                "display_label": f"{item.get('node_name') or item.get('node_id') or '图谱'} · {item.get('attribute') or 'evidence'}",
                "url": "",
                "domain": "",
                "title": str(item.get("reference") or "").strip(),
                "published_date": "",
            }
        )
    return plan


def build_graph_guidance_from_result(graph_result: dict[str, Any]) -> str:
    roles = dict(graph_result.get("subgraph_roles") or {})
    lines: list[str] = []

    for item in list(roles.get("primary_nodes") or [])[:1]:
        name = str(item.get("name") or "").strip()
        reason = str(item.get("reason") or "").strip()
        if name:
            lines.append(f"- 节点：{name}；定位：当前主讲节点{f'；说明：{reason}' if reason else ''}")

    prerequisite_names = [str(item.get("name") or "").strip() for item in (roles.get("prerequisite_nodes") or []) if str(item.get("name") or "").strip()]
    supporting_names = [str(item.get("name") or "").strip() for item in (roles.get("supporting_nodes") or []) if str(item.get("name") or "").strip()]
    comparison_names = [str(item.get("name") or "").strip() for item in (roles.get("comparison_nodes") or []) if str(item.get("name") or "").strip()]

    if prerequisite_names:
        lines.append(f"- 前置：{'；'.join(prerequisite_names[:3])}")
    if supporting_names:
        lines.append(f"- 支撑：{'；'.join(supporting_names[:3])}")
    if comparison_names:
        lines.append(f"- 对照：{'；'.join(comparison_names[:3])}")

    return "\n".join(lines)


def build_graph_context_from_result(
    graph_pipeline: Any,
    graph_result: dict[str, Any],
    *,
    fallback_query: str = "",
) -> dict[str, Any]:
    anchor_nodes = list(graph_result.get("anchor_nodes") or [])
    anchor_id = str(anchor_nodes[0].get("node_id") or "").strip() if anchor_nodes else ""
    node_map = dict(getattr(graph_pipeline, "node_map", {}) or {})
    anchor = node_map.get(anchor_id) or {}

    anchor_title = str(anchor.get("name") or (anchor_nodes[0].get("name") if anchor_nodes else "") or fallback_query).strip()
    prerequisites = _resolve_node_refs(node_map, anchor.get("prerequisite_nodes"))
    related_nodes = _resolve_node_refs(node_map, anchor.get("related_nodes"))
    next_nodes = _resolve_node_refs(node_map, anchor.get("recommended_next_nodes") or anchor.get("next_nodes"))
    must_know = _string_list(anchor.get("core_concepts")) or _string_list(anchor.get("key_points"))[:3]
    learning_objectives = _string_list(anchor.get("key_points"))[:3] or must_know[:]
    common_errors = _string_list((anchor.get("extra") or {}).get("common_errors"))

    next_steps = []
    for node_id in _string_list(anchor.get("recommended_next_nodes") or anchor.get("next_nodes")):
        next_steps.append(
            {
                "id": node_id,
                "target": _node_name(node_map, node_id) or node_id,
                "title": _node_name(node_map, node_id) or node_id,
            }
        )

    return {
        "anchor_id": anchor_id or anchor_title,
        "anchor_title": anchor_title,
        "anchor_filename": str(anchor.get("chapter") or "").strip(),
        "prerequisites": prerequisites,
        "neighbors": related_nodes,
        "learning_objectives": learning_objectives,
        "must_know": must_know,
        "common_errors": common_errors,
        "target_mastery_level": str(anchor.get("requirement_level") or anchor.get("mastery_threshold") or "").strip(),
        "difficulty": str(anchor.get("importance_level") or "").strip(),
        "next_steps": next_steps,
        "recommended_next_nodes": next_nodes,
    }


def build_graph_state_patch(
    graph_pipeline: Any | None,
    node_id: str,
) -> dict[str, Any]:
    if graph_pipeline is None or not str(node_id or "").strip():
        return {}

    node_map = dict(getattr(graph_pipeline, "node_map", {}) or {})
    resolved_id = str(node_id or "").strip()
    node = node_map.get(resolved_id) or {}
    if not node:
        return {}

    prerequisites = _resolve_node_refs(node_map, node.get("prerequisite_nodes"))
    related_nodes = _resolve_node_refs(node_map, node.get("related_nodes"))
    next_node_ids = _string_list(node.get("recommended_next_nodes") or node.get("next_nodes"))
    next_steps = [
        {
            "id": next_id,
            "target": _node_name(node_map, next_id) or next_id,
            "title": _node_name(node_map, next_id) or next_id,
        }
        for next_id in next_node_ids
    ]

    must_know = _string_list(node.get("core_concepts")) or _string_list(node.get("key_points"))[:3]
    learning_objectives = _string_list(node.get("key_points"))[:3] or must_know[:]
    common_errors = _string_list((node.get("extra") or {}).get("common_errors"))
    node_name = str(node.get("name") or resolved_id).strip()

    return {
        "graph_anchor_id": resolved_id,
        "graph_anchor_title": node_name,
        "graph_anchor_filename": str(node.get("chapter") or "").strip(),
        "graph_prerequisites": prerequisites,
        "graph_neighbors": related_nodes,
        "graph_learning_objectives": learning_objectives,
        "graph_must_know": must_know,
        "graph_common_errors": common_errors,
        "graph_target_mastery_level": str(node.get("requirement_level") or node.get("mastery_threshold") or "").strip(),
        "graph_difficulty": str(node.get("importance_level") or "").strip(),
        "graph_next_steps": next_steps,
        "current_node_id": resolved_id,
        "current_node_name": node_name,
    }


def load_student_state_snapshot(
    student_state_store: StudentStateStore | None,
    student_id: str,
) -> tuple[StudentState | None, dict[str, Any]]:
    if student_state_store is None or not student_id:
        return None, {}
    student_state = student_state_store.load(student_id)
    return student_state, student_state.to_dict()


def save_student_state_snapshot(
    student_state_store: StudentStateStore | None,
    student_state: StudentState | None,
) -> dict[str, Any]:
    if student_state_store is None or student_state is None:
        return {}
    student_state_store.save(student_state)
    return student_state.to_dict()


def mark_student_node_started(
    student_state_store: StudentStateStore | None,
    *,
    student_id: str,
    node_id: str,
    question: str,
    title: str = "",
) -> dict[str, Any]:
    student_state, _ = load_student_state_snapshot(student_state_store, student_id)
    if student_state is None or not node_id:
        return {}
    student_state.current_node_id = node_id
    student_state.last_question = str(question or "").strip()
    student_state.mark_node_started(node_id)
    # Register node in knowledge_graph (学了才加进去)
    student_state.kg_register_node(node_id, title)
    return save_student_state_snapshot(student_state_store, student_state)


def update_student_state_after_evaluation(
    student_state_store: StudentStateStore | None,
    *,
    student_id: str,
    node_id: str,
    score: float,
    passed: bool,
    teaching_strategy: str = "",
    difficulty_level: int = 0,
    wrong_items: list[dict[str, Any]] | None = None,
    node_title: str = "",
) -> dict[str, Any]:
    student_state, _ = load_student_state_snapshot(student_state_store, student_id)
    if student_state is None or not node_id:
        return {}

    student_state.current_node_id = node_id
    student_state.update_mastery(node_id, score)
    # Sync teaching strategy and difficulty from AgentState
    if teaching_strategy:
        student_state.teaching_strategy = teaching_strategy
    if difficulty_level:
        student_state.difficulty_level = difficulty_level
    # Evidence is recorded per-node via kg_update_score below (single source of truth).
    if passed:
        student_state.mark_node_completed(node_id)
        if node_id not in student_state.visited_nodes:
            student_state.visited_nodes.append(node_id)
        if node_id in student_state.wrong_nodes:
            student_state.wrong_nodes.remove(node_id)
    else:
        if node_id not in student_state.wrong_nodes:
            student_state.wrong_nodes.append(node_id)
        student_state.mark_node_started(node_id)
    today = now_ts()[:10]
    if hasattr(student_state, "daily_learning_records"):
        learned_today = list(student_state.daily_learning_records.get(today, []) or [])
        if node_id and node_id not in learned_today:
            learned_today.append(node_id)
        student_state.daily_learning_records[today] = learned_today
    if hasattr(student_state, "last_learning_at"):
        student_state.last_learning_at = now_ts()
    # Update knowledge_graph (score, wrong_questions, evidence)
    student_state.kg_update_score(
        node_id, int(round(score)), passed=passed,
        wrong_items=wrong_items, source="quiz", title=node_title,
    )
    return save_student_state_snapshot(student_state_store, student_state)


def recommend_next_node(
    *,
    graph_pipeline: Any | None,
    student_state_snapshot: dict[str, Any] | None,
    current_node_id: str,
) -> dict[str, str]:
    if graph_pipeline is None:
        return {}

    node_map = dict(getattr(graph_pipeline, "node_map", {}) or {})
    current_id = str(current_node_id or "").strip()
    current_node = node_map.get(current_id) or {}
    visited = set(_string_list((student_state_snapshot or {}).get("visited_nodes")))

    candidate_ids = _string_list(current_node.get("recommended_next_nodes")) or _string_list(current_node.get("next_nodes"))
    candidate_ids += [node_id for node_id in _string_list(current_node.get("related_nodes")) if node_id not in candidate_ids]

    def numeric_key(node_id: str) -> tuple[int, str]:
        digits = "".join(ch for ch in node_id if ch.isdigit())
        return (int(digits) if digits else 999999, node_id)

    for node_id in candidate_ids:
        if node_id == current_id or node_id in visited or node_id not in node_map:
            continue
        return {
            "node_id": node_id,
            "name": _node_name(node_map, node_id) or node_id,
            "reason": "related_unvisited",
        }

    remaining = sorted((node_id for node_id in node_map if node_id not in visited and node_id != current_id), key=numeric_key)
    if not remaining:
        return {}
    node_id = remaining[0]
    return {
        "node_id": node_id,
        "name": _node_name(node_map, node_id) or node_id,
        "reason": "smallest_unvisited",
    }


def build_homework_items(
    *,
    graph_pipeline: Any | None,
    student_state_snapshot: dict[str, Any] | None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    if graph_pipeline is None:
        return []

    snapshot = dict(student_state_snapshot or {})
    node_map = dict(getattr(graph_pipeline, "node_map", {}) or {})
    wrong_nodes = _string_list(snapshot.get("wrong_nodes"))
    visited_nodes = _string_list(snapshot.get("visited_nodes"))

    ordered_ids: list[str] = []
    for node_id in wrong_nodes + visited_nodes[::-1]:
        if node_id and node_id not in ordered_ids:
            ordered_ids.append(node_id)

    items: list[dict[str, Any]] = []
    for node_id in ordered_ids[:limit]:
        node = node_map.get(node_id) or {}
        title = str(node.get("name") or node_id).strip()
        must_know = _string_list(node.get("core_concepts"))[:2]
        key_points = _string_list(node.get("key_points"))[:2]
        formulas = _string_list(node.get("formulas"))[:2]
        examples = _string_list(node.get("examples"))[:1]
        source_refs = _string_list(node.get("page_refs"))[:3]
        focus = "、".join(must_know) if must_know else title
        key_point_text = "；".join(key_points) if key_points else "节点中的关键判断步骤"
        formula_text = f"；必要时结合公式：{'；'.join(formulas)}" if formulas else ""
        example_text = f"；可参考情境：{'；'.join(examples)}" if examples else ""
        items.append(
            {
                "question_id": f"HW-{node_id}",
                "node_id": node_id,
                "graph_node_id": node_id,
                "node_title": title,
                "title": title,
                "type": "subjective_review",
                "prompt": (
                    f"围绕“{title}”完成一道复习题：先说明 {focus} 的核心概念，"
                    f"再解释 {key_point_text}{formula_text}{example_text}，最后给出一个具体判断过程。"
                ),
                "reference_answer": (
                    f"答案应覆盖 {focus}；说明 {key_point_text}"
                    f"{formula_text}；并能把结论落到一个具体情境或判断步骤中。"
                ),
                "rubric": ["概念准确", "节点关键点覆盖", "推理步骤清楚", "能结合情境或公式"],
                "source_refs": source_refs,
                "media_refs": [],
                "covered_node_ids": [node_id],
            }
        )
    return items


def assign_homework_items(
    student_state_store: StudentStateStore | None,
    *,
    student_id: str,
    homework_items: list[dict[str, Any]] | None,
) -> dict[str, Any]:
    student_state, _ = load_student_state_snapshot(student_state_store, student_id)
    if student_state is None:
        return {}

    student_state.homework = []
    assignment_items: list[dict[str, Any]] = []
    for item in homework_items or []:
        question_id = str(item.get("question_id") or "").strip()
        if question_id:
            student_state.add_homework(question_id)
            assignment_items.append(dict(item))
    assignment_id = f"HW-{student_id}-{now_ts()}"
    assigned_at = now_ts()
    if hasattr(student_state, "homework_assignments"):
        student_state.homework_assignments = [
            {
                "assignment_id": assignment_id,
                "status": "assigned",
                "assigned_at": assigned_at,
                "items": assignment_items,
            }
        ] if assignment_items else []
    return save_student_state_snapshot(student_state_store, student_state)

from __future__ import annotations

from typing import Any

from ..core.events import make_event
from ..core.learning_support import build_graph_state_patch
from ..core.ports import RuntimeContext
from ..core.state import AgentState


def _string_list(values: Any) -> list[str]:
    if isinstance(values, list):
        return [str(item).strip() for item in values if str(item).strip()]
    return []


def _node_name(node: dict[str, Any], node_id: str) -> str:
    return str(node.get("name") or node.get("title") or node.get("concept") or node_id).strip()


def _common_errors(node: dict[str, Any]) -> list[str]:
    extra = node.get("extra") if isinstance(node.get("extra"), dict) else {}
    return _string_list(extra.get("common_errors")) or _string_list(node.get("common_errors"))


PEDAGOGICAL_EVIDENCE_ATTRIBUTES = {
    "summary",
    "definition",
    "key_points",
    "core_concepts",
    "must_know",
    "learning_objectives",
    "common_errors",
    "prerequisite_nodes",
}


def _looks_like_relation_path_text(text: str) -> bool:
    value = str(text or "").strip()
    if not value:
        return False
    lowered = value.lower()
    return (
        "--[" in value
        or "relation_path" in lowered
        or "parallel_to" in lowered
        or "related_to" in lowered
        or ("关系强度" in value and "边权重" in value)
        or ("方向：" in value and "证据：" in value and "--[" in value)
    )


def _filter_pedagogical_evidence(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for item in items or []:
        attribute = str(item.get("attribute") or "").strip().lower()
        text = str(item.get("text") or "").strip()
        if attribute not in PEDAGOGICAL_EVIDENCE_ATTRIBUTES:
            continue
        if _looks_like_relation_path_text(text):
            continue
        filtered.append(dict(item))
    return filtered


def _build_structured_context(node_id: str, node: dict[str, Any]) -> str:
    name = _node_name(node, node_id)
    objectives = _string_list(node.get("learning_objectives")) or _string_list(node.get("key_points"))
    must_know = _string_list(node.get("core_concepts")) or _string_list(node.get("must_know"))
    common_errors = _common_errors(node)
    prerequisites = _string_list(node.get("prerequisite_nodes"))
    next_nodes = _string_list(node.get("recommended_next_nodes") or node.get("next_nodes"))
    lines = [f"当前图谱节点：{name}（{node_id}）"]
    if prerequisites:
        lines.append(f"前置节点：{'；'.join(prerequisites)}")
    if objectives:
        lines.append(f"学习目标：{'；'.join(objectives)}")
    if must_know:
        lines.append(f"必会要点：{'；'.join(must_know)}")
    if common_errors:
        lines.append(f"常见误区：{'；'.join(common_errors)}")
    if next_nodes:
        lines.append(f"后续推荐节点：{'；'.join(next_nodes)}")
    return "\n".join(lines)


def _teacher_explanation(node: dict[str, Any]) -> str:
    """Return the prebuilt node teaching text used by the main learning flow.

    主流程中，节点选定后的教学内容只允许来自节点内已沉淀的
    explanation_teacher_style 字段；不再调用图谱搜索/路径检索来拼接讲解正文。
    """
    return str(node.get("explanation_teacher_style") or "").strip()


def build_node_content_loader_node(runtime: RuntimeContext):
    event_sink = runtime.event_sink

    def node(state: AgentState) -> dict:
        graph_pipeline = getattr(runtime, "graph_rag_pipeline", None)
        node_map = dict(getattr(graph_pipeline, "node_map", {}) or {})
        node_id = str(state.get("current_node_id") or state.get("graph_anchor_id") or "").strip()
        node = node_map.get(node_id) or {}
        node_name = _node_name(node, node_id) or str(state.get("current_node_name") or state.get("graph_anchor_title") or node_id).strip()
        topic = str(state.get("current_topic") or state.get("current_user_goal") or "").strip()

        graph_patch = build_graph_state_patch(graph_pipeline, node_id) if node_id else {}
        teacher_explanation = _teacher_explanation(node) if node else ""
        structured_context = _build_structured_context(node_id, node) if node else ""
        node_content_context = teacher_explanation or structured_context
        citations: list[dict[str, Any]] = []
        evidence: list[dict[str, Any]] = []

        event_sink.emit(
            make_event(
                "node.complete",
                "node_content_loader",
                message=f"已抽取图谱节点【{node_name or node_id}】的讲解材料。",
                data={
                    "node_id": node_id,
                    "node_name": node_name,
                    "has_teacher_explanation": bool(teacher_explanation),
                    "teaching_source": "explanation_teacher_style" if teacher_explanation else "structured_node_context",
                },
            )
        )
        if node_id and node_name:
            event_sink.emit(
                make_event(
                    "graph.node_update",
                    "node_content_loader",
                    message=f"当前节点：{node_name}",
                    data={"title": node_name, "id": node_id, "status": "content_loaded", "type": "current"},
                )
            )

        return {
            **graph_patch,
            "current_node_id": node_id,
            "current_node_name": node_name,
            "current_node_status": "content_loaded" if node_id else state.get("current_node_status", ""),
            "node_content_context": node_content_context,
            "tutor_citations": citations,
            "tutor_evidence": evidence,
            "learning_phase": "node_content_loaded",
            "learning_resume_target": "tutor",
            "learning_resume_reason": "node_content_loaded",
            "turn_goal": node_name or state.get("turn_goal", "") or topic,
            "topic_focus": node_name or state.get("topic_focus", ""),
        }

    return node

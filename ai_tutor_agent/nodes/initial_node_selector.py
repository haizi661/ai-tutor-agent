from __future__ import annotations

from typing import Any

from ..core.events import make_event
from ..core.learning_support import build_graph_state_patch, graph_node_sort_key
from ..core.ports import RuntimeContext
from ..core.state import AgentState


def _string_list(values: Any) -> list[str]:
    if isinstance(values, list):
        return [str(item).strip() for item in values if str(item).strip()]
    return []


def _node_numeric_key(node_id: str) -> tuple[int, str]:
    return graph_node_sort_key(node_id)


def _node_name(node: dict[str, Any], node_id: str) -> str:
    return str(node.get("name") or node.get("title") or node.get("concept") or node_id).strip()


def _node_source_type(node: dict[str, Any]) -> str:
    return str(node.get("source_type") or "").strip().lower()


def _node_extra(node: dict[str, Any]) -> dict[str, Any]:
    extra = node.get("extra") or {}
    return dict(extra) if isinstance(extra, dict) else {}


def _is_chapter_anchor(node: dict[str, Any]) -> bool:
    source_type = _node_source_type(node)
    extra = _node_extra(node)
    node_role = str(extra.get("node_role") or "").strip().lower()
    return "chapter_anchor" in source_type or node_role == "chapter_anchor"


def _has_no_prerequisites(node: dict[str, Any]) -> bool:
    prerequisites = _string_list(node.get("prerequisite_nodes"))
    return not prerequisites


def _select_initial_root_node(node_map: dict[str, dict[str, Any]], visited: set[str]) -> tuple[str, str]:
    candidates: list[str] = []
    for node_id, node in node_map.items():
        cleaned_id = str(node_id).strip()
        if not cleaned_id or cleaned_id in visited:
            continue
        if _has_no_prerequisites(node):
            candidates.append(cleaned_id)
    if not candidates:
        return "", ""

    def root_key(node_id: str) -> tuple[int, int, tuple[int, str]]:
        node = node_map.get(node_id) or {}
        name = _node_name(node, node_id)
        is_general_intro = 0 if "一般概念" in name else 1
        is_anchor = 0 if _is_chapter_anchor(node) else 1
        return (is_general_intro, is_anchor, _node_numeric_key(node_id))

    ordered = sorted(candidates, key=root_key)
    return ordered[0], "course_root_start"


def _find_node_by_title(node_map: dict[str, dict[str, Any]], title: str) -> str:
    target = str(title or "").strip()
    if not target:
        return ""
    for node_id, node in node_map.items():
        if target in {str(node.get("name") or "").strip(), str(node.get("title") or "").strip()}:
            return str(node_id).strip()
    return ""


def _select_from_gaps(
    *,
    concept_gaps: dict[str, Any],
    node_map: dict[str, dict[str, Any]],
    visited: set[str],
) -> tuple[str, str]:
    candidates: list[tuple[float, tuple[int, str], str]] = []
    for concept_title, raw_gap in (concept_gaps or {}).items():
        gap = dict(raw_gap or {}) if isinstance(raw_gap, dict) else {}
        node_id = str(gap.get("concept_id") or gap.get("node_id") or "").strip()
        if not node_id or node_id not in node_map:
            node_id = _find_node_by_title(node_map, str(gap.get("concept_title") or concept_title))
        if not node_id or node_id not in node_map or node_id in visited:
            continue
        calibrated = gap.get("calibrated")
        try:
            score = float(calibrated)
        except (TypeError, ValueError):
            score = 50.0
        # 分数越低越优先；同分按节点序号最小。
        candidates.append((score, _node_numeric_key(node_id), node_id))
    if not candidates:
        return "", ""
    candidates.sort(key=lambda item: (item[0], item[1]))
    return candidates[0][2], "lowest_gap_unvisited"


def _select_smallest_unvisited(node_map: dict[str, dict[str, Any]], visited: set[str]) -> tuple[str, str]:
    remaining = [str(node_id).strip() for node_id in node_map if str(node_id).strip() and str(node_id).strip() not in visited]
    if not remaining:
        return "", ""
    return sorted(remaining, key=_node_numeric_key)[0], "smallest_unvisited"


def build_initial_node_selector_node(runtime: RuntimeContext):
    event_sink = runtime.event_sink

    def node(state: AgentState) -> dict:
        graph_pipeline = getattr(runtime, "graph_rag_pipeline", None)
        node_map = dict(getattr(graph_pipeline, "node_map", {}) or {})
        snapshot = dict(state.get("student_state_snapshot") or {})
        visited = set(_string_list(snapshot.get("visited_nodes")))

        selected_id, reason = _select_initial_root_node(node_map, visited)
        if not selected_id:
            selected_id, reason = _select_smallest_unvisited(node_map, visited)

        selected_node = node_map.get(selected_id) or {}
        selected_name = _node_name(selected_node, selected_id) if selected_id else ""
        graph_patch = build_graph_state_patch(graph_pipeline, selected_id) if selected_id else {}

        event_sink.emit(
            make_event(
                "node.complete",
                "initial_node_selector",
                message=(
                    f"知识图谱已定位到课程起点【{selected_name}】，接下来从这里正式开始讲解。"
                    if selected_id
                    else "暂时没有找到可用图谱节点，将保留当前主题进入讲解。"
                ),
                data={"node_id": selected_id, "node_name": selected_name, "reason": reason},
            )
        )
        if selected_id and selected_name:
            event_sink.emit(
                make_event(
                    "graph.node_update",
                    "initial_node_selector",
                    message=f"当前节点：{selected_name}",
                    data={"title": selected_name, "id": selected_id, "status": "selected", "type": "current"},
                )
            )

            # ── 教学推理透明：解释节点选择原因 ──
            if state.get("thinking_mode", False):
                reason_explain = {
                    "course_root_start": "选择课程起点：无前置依赖的入门章节，适合作为学习起点",
                    "lowest_gap_unvisited": "根据前测薄弱点：该概念在前测中得分最低，优先补齐",
                    "smallest_unvisited": "选择最小未学节点：按图谱顺序推进，从最基础的未学节点开始",
                }.get(reason, f"选择原因：{reason}")
                prereq_count = len(_string_list(selected_node.get("prerequisite_nodes")))
                prereq_note = f"；该节点有 {prereq_count} 个前置知识" if prereq_count > 0 else "；无前置依赖，可直接学习"
                event_sink.emit(
                    make_event(
                        "thinking.step",
                        "initial_node_selector",
                        message=f"节点选择：{reason_explain}【{selected_name}】{prereq_note}",
                        data={
                            "category": "node_selection",
                            "node_id": selected_id,
                            "node_name": selected_name,
                            "reason": reason,
                            "prerequisite_count": prereq_count,
                        },
                    )
                )

        return {
            "current_node_id": selected_id,
            "current_node_name": selected_name,
            "current_node_status": "selected" if selected_id else "",
            "next_node_candidate_reason": reason,
            "learning_phase": "node_selected",
            "learning_resume_target": "node_content_loader" if selected_id else "tutor",
            "learning_resume_reason": "initial_node_selected" if selected_id else "initial_node_missing",
            "turn_goal": selected_name or state.get("turn_goal", "") or state.get("current_topic", ""),
            "topic_focus": selected_name or state.get("topic_focus", ""),
            **graph_patch,
        }

    return node

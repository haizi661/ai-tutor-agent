from __future__ import annotations

from typing import Any

from ..core.events import make_event
from ..core.learning_support import build_graph_state_patch
from ..core.ports import RuntimeContext
from ..core.state import AgentState


def _string_list(values: Any) -> list[str]:
    if isinstance(values, list):
        return [str(item).strip() for item in values if str(item).strip()]
    if isinstance(values, tuple):
        return [str(item).strip() for item in values if str(item).strip()]
    value = str(values or "").strip()
    if not value or value in {"[]", "None", "none", "null", "无"}:
        return []
    for sep in ("||", ";", "；", ",", "，", "、"):
        if sep in value:
            return [item.strip() for item in value.split(sep) if item.strip()]
    return [value]


def _node_name(node: dict[str, Any], node_id: str) -> str:
    return str(node.get("name") or node.get("title") or node.get("concept") or node_id).strip()


def _common_errors(node: dict[str, Any]) -> list[str]:
    extra = node.get("extra") if isinstance(node.get("extra"), dict) else {}
    return _string_list(extra.get("common_errors")) or _string_list(node.get("common_errors"))


def _compact_text(value: Any, *, max_len: int = 360) -> str:
    text = " ".join(str(value or "").replace("\n", " ").split()).strip()
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def _dedupe_texts(values: Any, *, limit: int = 6, max_len: int = 360) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in _string_list(values):
        text = _compact_text(value, max_len=max_len)
        if not text:
            continue
        key = text[:80]
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(text)
        if len(cleaned) >= limit:
            break
    return cleaned


def _format_section(title: str, values: Any, *, limit: int = 6, max_len: int = 360) -> list[str]:
    items = _dedupe_texts(values, limit=limit, max_len=max_len)
    if not items:
        return []
    lines = [f"## {title}"]
    for idx, item in enumerate(items, start=1):
        lines.append(f"{idx}. {item}")
    return lines


def _resolve_node_names(node_ids: Any, node_map: dict[str, dict[str, Any]]) -> list[str]:
    resolved: list[str] = []
    for node_id in _string_list(node_ids):
        node = node_map.get(node_id) or {}
        name = _node_name(node, node_id) if node else node_id
        if node_id and name and node_id != name:
            resolved.append(f"{node_id}（{name}）")
        elif node_id:
            resolved.append(node_id)
    return resolved


def _format_figures(figures: Any, *, limit: int = 8) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    for value in _string_list(figures):
        text = _compact_text(value, max_len=260)
        if not text or text in seen:
            continue
        seen.add(text)
        items.append(text)
        if len(items) >= limit:
            break
    if not items:
        return []
    lines = ["## figures_refs（图表引用，讲解时只在必要处提及）"]
    for idx, item in enumerate(items, start=1):
        lines.append(f"{idx}. {item}")
    return lines


def _build_rich_teaching_context(
    *,
    node_id: str,
    node: dict[str, Any],
    node_map: dict[str, dict[str, Any]],
) -> str:
    """把当前节点的所有可教学字段压成一个稳定的 LLM 输入包。

    注意：这里不改知识图谱字段，只改变主流程传给 tutor LLM 的上下文。
    """
    name = _node_name(node, node_id)
    extra = node.get("extra") if isinstance(node.get("extra"), dict) else {}

    lines: list[str] = [
        "# 当前图谱节点综合讲授素材包",
        f"节点：{name}（{node_id}）",
    ]

    chapter = str(node.get("chapter") or "").strip()
    summary = _compact_text(node.get("summary"), max_len=420)
    requirement = str(node.get("requirement_level") or "").strip()
    importance = str(node.get("importance_level") or "").strip()
    focus = str(node.get("assessment_focus") or "").strip()
    threshold = node.get("mastery_threshold")
    page_refs = _string_list(node.get("page_refs"))
    refined_pages = _string_list(extra.get("page_refs_refined"))

    basic_parts = []
    if chapter:
        basic_parts.append(f"章节：{chapter}")
    if requirement:
        basic_parts.append(f"课程要求：{requirement}")
    if importance:
        basic_parts.append(f"重要程度：{importance}")
    if focus:
        basic_parts.append(f"考查重点：{focus}")
    if threshold not in (None, ""):
        basic_parts.append(f"建议掌握门槛：{threshold}")
    if refined_pages:
        basic_parts.append(f"精炼页码：{', '.join(refined_pages[:8])}")
    elif page_refs:
        basic_parts.append(f"页码范围：{', '.join(page_refs[:8])}")
    if basic_parts:
        lines.append("## 节点基本信息")
        lines.extend(f"- {item}" for item in basic_parts)
    if summary:
        lines.append("## summary")
        lines.append(summary)

    prerequisites = _resolve_node_names(node.get("prerequisite_nodes"), node_map)
    next_nodes = _resolve_node_names(node.get("recommended_next_nodes") or node.get("next_nodes"), node_map)
    related = _resolve_node_names(node.get("related_nodes"), node_map)
    if prerequisites or next_nodes or related:
        lines.append("## 图谱关系提示")
        if prerequisites:
            lines.append(f"- 前置节点：{'；'.join(prerequisites[:6])}")
        if next_nodes:
            lines.append(f"- 推荐下一节点：{'；'.join(next_nodes[:4])}")
        if related:
            lines.append(f"- 相关节点：{'；'.join(related[:6])}")

    teacher_text = _compact_text(node.get("explanation_teacher_style"), max_len=1400)
    raw_text = _compact_text(node.get("explanation_raw"), max_len=1000)
    if teacher_text:
        lines.append("## explanation_teacher_style（原始教师风格讲解，可作为主线但不要原样照搬）")
        lines.append(teacher_text)
    if raw_text and raw_text != teacher_text:
        lines.append("## explanation_raw（教材原始解释材料）")
        lines.append(raw_text)

    for title, field, limit, max_len in [
        ("core_concepts", "core_concepts", 10, 220),
        ("key_points", "key_points", 12, 520),
        ("formulas", "formulas", 16, 420),
        ("examples", "examples", 12, 760),
        ("definition_candidates", "definition_candidates", 10, 620),
        ("key_point_candidates", "key_point_candidates", 14, 620),
        ("formula_candidates", "formula_candidates", 16, 420),
        ("example_candidates", "example_candidates", 12, 760),
    ]:
        lines.extend(_format_section(title, node.get(field), limit=limit, max_len=max_len))

    lines.extend(_format_figures(node.get("figures_refs"), limit=8))

    common_errors = _common_errors(node)
    if common_errors:
        lines.extend(_format_section("common_errors", common_errors, limit=5, max_len=240))

    lines.append("## 讲授生成要求")
    lines.extend(
        [
            "- 必须综合上面的多个字段组织讲解，不能只复述 explanation_teacher_style。",
            "- 讲授要详实，优先形成完整教学单元：主线、定义、关键点、公式、例子、图表、常见误区都要尽量覆盖。",
            "- 公式和图表可以交叉使用：公式讲定量关系，图表讲结构/趋势/直观现象，例子负责落地。",
            "- 如果材料中有多个公式或例子，不要全部罗列，要挑最能支撑当前节点的内容串联讲。",
            "- 输出面向学生，避免输出字段名、CSV 痕迹、调试信息和 raw id。",
            "- 讲完后保留课后停顿，由后续 post_lesson_choice 接管。",
        ]
    )
    return "\n".join(lines).strip()


def _build_structured_context(node_id: str, node: dict[str, Any], node_map: dict[str, dict[str, Any]]) -> str:
    # 兼容兜底：如果节点字段非常少，也至少给 tutor 一个结构化上下文。
    name = _node_name(node, node_id)
    objectives = _string_list(node.get("learning_objectives")) or _string_list(node.get("key_points"))
    must_know = _string_list(node.get("core_concepts")) or _string_list(node.get("must_know"))
    common_errors = _common_errors(node)
    prerequisites = _resolve_node_names(node.get("prerequisite_nodes"), node_map)
    next_nodes = _resolve_node_names(node.get("recommended_next_nodes") or node.get("next_nodes"), node_map)
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
    """Return the prebuilt node teaching text used by the main learning flow."""
    return str(node.get("explanation_teacher_style") or "").strip()


_CONTRACT_EXIT_CRITERIA = [
    "节点客观题总分达到 80 分",
    "关键目标正确率达到 70%",
    "常见误区题不能连续错 2 次",
]

_ASSESSMENT_FOCUS_CYCLE = ("概念辨析", "判断依据", "常见误区", "应用迁移")


def _build_node_teaching_contract(node_id: str, node: dict[str, Any], node_name: str) -> dict[str, Any]:
    objectives = _string_list(node.get("learning_objectives")) or _string_list(node.get("key_points"))
    must_know = _string_list(node.get("core_concepts")) or _string_list(node.get("must_know"))
    common_errors = _common_errors(node)
    prerequisites = _string_list(node.get("prerequisite_nodes"))
    examples = _string_list(node.get("examples"))

    learning_goal = objectives[0] if objectives else (must_know[0] if must_know else f"理解{node_name or node_id}的核心概念")
    target_seeds = must_know + [item for item in objectives if item not in must_know]
    if not target_seeds:
        target_seeds = [learning_goal]

    assessment_targets: list[dict[str, Any]] = []
    for index, target in enumerate(target_seeds):
        misconception = common_errors[index % len(common_errors)] if common_errors else "混淆题干条件与当前节点的核心判断依据"
        assessment_targets.append(
            {
                "target_objective": target,
                "assessment_focus": _ASSESSMENT_FOCUS_CYCLE[index % len(_ASSESSMENT_FOCUS_CYCLE)],
                "misconception": misconception,
                "required": index < max(1, min(2, len(must_know) or len(target_seeds))),
            }
        )

    return {
        "node_id": node_id,
        "node_name": node_name or node_id,
        "learning_goal": learning_goal,
        "prerequisites": prerequisites,
        "must_know": must_know,
        "common_misconceptions": common_errors,
        "worked_example": examples[0] if examples else "",
        "assessment_targets": assessment_targets,
        "exit_criteria": list(_CONTRACT_EXIT_CRITERIA),
    }



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
        rich_context = _build_rich_teaching_context(node_id=node_id, node=node, node_map=node_map) if node else ""
        structured_context = _build_structured_context(node_id, node, node_map) if node else ""
        teaching_contract = _build_node_teaching_contract(node_id, node, node_name) if node else {}
        node_content_context = rich_context or structured_context
        citations: list[dict[str, Any]] = []
        evidence: list[dict[str, Any]] = []

        event_sink.emit(
            make_event(
                "node.complete",
                "node_content_loader",
                message=f"已抽取图谱节点【{node_name or node_id}】的综合讲授素材包。",
                data={
                    "node_id": node_id,
                    "node_name": node_name,
                    "has_teacher_explanation": bool(node.get("explanation_teacher_style")) if node else False,
                    "teaching_source": "rich_node_teaching_context" if rich_context else "structured_node_context",
                    "context_length": len(node_content_context),
                    "has_figures_refs": bool(_string_list(node.get("figures_refs"))) if node else False,
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
            "current_entry_mode": state.get("current_entry_mode", ""),
            "node_quiz_kind": "",  # clear stale quiz kind from previous node
            "current_node_status": "content_loaded" if node_id else state.get("current_node_status", ""),
            "node_content_context": node_content_context,
            "node_content_source": "rich_node_material" if rich_context else "structured_node_context",
            "node_teaching_contract": teaching_contract,
            "tutor_citations": citations,
            "tutor_evidence": evidence,
            "learning_phase": "node_content_loaded",
            "learning_resume_target": "tutor",
            "learning_resume_reason": "node_content_loaded",
            "turn_goal": node_name or state.get("turn_goal", "") or topic,
            "topic_focus": node_name or state.get("topic_focus", ""),
        }

    return node

from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from ..core.events import make_event
from ..core.output_format import parse_json_object
from ..core.text import content_to_text
from ..core.learning_support import mutate_student_state_snapshot, update_student_state_after_evaluation, trim_message_history
from ..core.ports import RuntimeContext
from ..core.state import AgentState
from ..knowledge_map.student_state import now_ts


def _question_id(item: dict[str, Any], index: int) -> str:
    return str(item.get("question_id") or item.get("id") or f"Q{index}").strip()


def _answer_key(item: dict[str, Any]) -> str:
    return str(item.get("answer_key") or item.get("answer") or "").strip().upper()


def _normalize_answer(value: Any) -> str:
    return str(value or "").strip().upper()


def _normalize_options(options: Any) -> dict[str, str]:
    if isinstance(options, dict):
        normalized = {str(key).strip().upper(): str(value).strip() for key, value in options.items() if str(key).strip()}
        return {key: normalized[key] for key in ("A", "B", "C", "D") if key in normalized}
    if isinstance(options, list):
        result: dict[str, str] = {}
        for raw in options:
            text = str(raw).strip()
            if not text:
                continue
            key = text[:1].upper()
            if key in {"A", "B", "C", "D"}:
                result[key] = text[1:].lstrip(".．、:： ").strip() or text
        return result
    return {}


def _normalize_question(raw: dict[str, Any], index: int, node_id: str) -> dict[str, Any] | None:
    stem = str(raw.get("stem") or raw.get("question") or "").strip()
    answer_key = _normalize_answer(raw.get("answer_key") or raw.get("correct_answer") or raw.get("correct"))
    options = _normalize_options(raw.get("options"))
    if not stem or answer_key not in {"A", "B", "C", "D"} or answer_key not in options:
        return None
    return {
        "question_id": str(raw.get("question_id") or raw.get("id") or f"AI-Q{index}").strip(),
        "node_id": str(raw.get("node_id") or node_id).strip(),
        "node_name": str(raw.get("node_name") or "").strip(),
        "stem": stem,
        "options": options,
        "answer_key": answer_key,
        "explanation": str(raw.get("explanation") or raw.get("analysis") or "").strip(),
        "wrong_option_analysis": raw.get("wrong_option_analysis") or {},
        "assessment_focus": str(raw.get("assessment_focus") or "").strip(),
        "target_objective": str(raw.get("target_objective") or raw.get("objective") or "").strip(),
        "misconception": str(raw.get("misconception") or raw.get("common_error") or "").strip(),
        "difficulty": raw.get("difficulty") or raw.get("difficulty_level") or "",
        "source": str(raw.get("source") or "ai_generated").strip(),
    }


def _extract_question_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        for key in ("questions", "items", "objective_questions"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def _string_list(values: Any) -> list[str]:
    if isinstance(values, list):
        return [str(item).strip() for item in values if str(item).strip()]
    if isinstance(values, tuple):
        return [str(item).strip() for item in values if str(item).strip()]
    value = str(values or "").strip()
    return [value] if value else []


def _join_list(values: Any, *, limit: int = 6) -> str:
    return "；".join(_string_list(values)[:limit])


def _teaching_contract(state: AgentState | dict[str, Any]) -> dict[str, Any]:
    contract = state.get("node_teaching_contract") if isinstance(state, dict) else {}
    return dict(contract or {}) if isinstance(contract, dict) else {}


def _contract_assessment_targets(state: AgentState | dict[str, Any]) -> list[dict[str, Any]]:
    contract = _teaching_contract(state)
    targets = contract.get("assessment_targets")
    if not isinstance(targets, list):
        return []
    normalized: list[dict[str, Any]] = []
    for raw in targets:
        if not isinstance(raw, dict):
            continue
        target = str(raw.get("target_objective") or raw.get("objective") or "").strip()
        if not target or _is_unsuitable_focus_text(target):
            continue
        normalized.append(
            {
                "target_objective": _clip_text(target, limit=70),
                "assessment_focus": str(raw.get("assessment_focus") or "").strip(),
                "misconception": _clip_text(str(raw.get("misconception") or "").strip(), limit=70),
                "required": bool(raw.get("required")),
            }
        )
    return normalized


def _contract_required_targets(state: AgentState | dict[str, Any]) -> list[str]:
    required: list[str] = []
    for item in _contract_assessment_targets(state):
        target = str(item.get("target_objective") or "").strip()
        if item.get("required") and target and target not in required:
            required.append(target)
    return required


def _first_nonempty(values: Any, *, fallback: str = "") -> str:
    for value in _string_list(values):
        if value:
            return value
    return fallback


def _default_assessment_focus(state: AgentState | dict[str, Any], index: int = 1) -> str:
    focuses = ["概念辨析", "判断依据", "常见误区", "应用迁移"]
    targets = _contract_assessment_targets(state)
    if targets:
        focus = str(targets[(max(index, 1) - 1) % len(targets)].get("assessment_focus") or "").strip()
        if focus:
            return focus
    explicit = str(state.get("assessment_focus") or state.get("graph_assessment_focus") or "").strip()
    return explicit or focuses[(max(index, 1) - 1) % len(focuses)]


def _default_target_objective(
    state: AgentState | dict[str, Any],
    *,
    node_name: str = "",
    concept: str = "",
    index: int = 1,
) -> str:
    targets = _contract_assessment_targets(state)
    if targets:
        return str(targets[(max(index, 1) - 1) % len(targets)]["target_objective"])
    must_know = _clean_focus_candidates(state.get("graph_must_know"), limit=70)
    if must_know:
        return must_know[(max(index, 1) - 1) % len(must_know)]
    objectives = _clean_focus_candidates(state.get("graph_learning_objectives"), limit=70)
    if objectives:
        return objectives[(max(index, 1) - 1) % len(objectives)]
    if concept and not _is_unsuitable_focus_text(concept):
        return _clip_text(str(concept), limit=70)
    return _FALLBACK_TARGET_OBJECTIVES[(max(index, 1) - 1) % len(_FALLBACK_TARGET_OBJECTIVES)]


def _default_misconception(
    state: AgentState | dict[str, Any],
    *,
    fallback: str = "",
    index: int = 1,
) -> str:
    targets = _contract_assessment_targets(state)
    if targets:
        misconception = str(targets[(max(index, 1) - 1) % len(targets)].get("misconception") or "").strip()
        if misconception and not _is_unsuitable_focus_text(misconception):
            return _clip_text(misconception, limit=70)
    contract_errors = _clean_focus_candidates(_teaching_contract(state).get("common_misconceptions"), limit=70)
    if contract_errors:
        return contract_errors[(max(index, 1) - 1) % len(contract_errors)]
    errors = _clean_focus_candidates(state.get("graph_common_errors"), limit=70)
    if errors:
        return errors[(max(index, 1) - 1) % len(errors)]
    if fallback and not _is_unsuitable_focus_text(fallback):
        return _clip_text(fallback, limit=70)
    return "混淆题干条件与当前节点的核心判断依据"


def _question_difficulty(state: AgentState | dict[str, Any], index: int = 1) -> int:
    raw = state.get("difficulty_level") or state.get("difficulty") or 3
    try:
        base = int(raw)
    except (TypeError, ValueError):
        base = 3
    # 同一批题轻微错开难度，避免全部同质。
    return max(1, min(5, base + ((max(index, 1) - 1) % 3) - 1))


def _enrich_question_metadata(
    item: dict[str, Any],
    *,
    state: AgentState | dict[str, Any],
    index: int,
    node_id: str,
    node_name: str,
) -> dict[str, Any]:
    enriched = dict(item)
    options = _normalize_options(enriched.get("options"))
    if options:
        enriched["options"] = options
    concept = _first_nonempty(
        _clean_focus_candidates(state.get("graph_must_know"), limit=70),
        fallback=str(enriched.get("target_objective") or ""),
    )
    explicit_target = str(enriched.get("target_objective") or "").strip()
    if _is_unsuitable_focus_text(explicit_target):
        explicit_target = ""
    explicit_misconception = str(enriched.get("misconception") or "").strip()
    if _is_unsuitable_focus_text(explicit_misconception):
        explicit_misconception = ""
    enriched.setdefault("node_id", node_id)
    enriched.setdefault("node_name", node_name)
    enriched["assessment_focus"] = str(enriched.get("assessment_focus") or _default_assessment_focus(state, index)).strip()
    enriched["target_objective"] = _clip_text(str(
        explicit_target
        or _default_target_objective(state, node_name=node_name, concept=concept, index=index)
    ).strip(), limit=82)
    enriched["misconception"] = _clip_text(str(
        explicit_misconception
        or _default_misconception(state, fallback=str(enriched.get("explanation") or ""), index=index)
    ).strip(), limit=82)
    enriched["difficulty"] = _question_difficulty({**dict(state), **enriched}, index)
    enriched["wrong_option_analysis"] = dict(enriched.get("wrong_option_analysis") or {})
    answer_key = _answer_key(enriched)
    for key in ("A", "B", "C", "D"):
        if key == answer_key or key in enriched["wrong_option_analysis"]:
            continue
        if key in options:
            enriched["wrong_option_analysis"][key] = _build_actionable_wrong_option_analysis(
                focus=enriched["target_objective"],
                misconception=enriched["misconception"],
                option_text=options.get(key, ""),
            )
    return enriched


_PLACEHOLDER_TERMS = {
    "实例",
    "示例",
    "系统示例",
    "自动控制",
    "一般概念",
    "反馈控制系统",
    "核心概念",
    "核心判断",
    "本节点",
    "节点要点",
}

_LOW_QUALITY_PHRASES = (
    "符合本节点",
    "围绕“",
    "结论方向和节点要点相反",
    "本节点要求掌握的",
    "第 1 个核心判断",
    "第 2 个核心判断",
    "第 3 个核心判断",
    "第 4 个核心判断",
)

_MATERIAL_COPY_MARKERS = (
    "由各种结构不同的元部件组成",
    "从完成自动控制这一功能来看",
    "具有一定功能的各种基本元件",
    "图1-5",
    "图 1-5",
    "通常加到反馈控制系统上的外作用",
)

_FALLBACK_TARGET_OBJECTIVES = (
    "区分被控对象与控制装置",
    "识别给定量、输出量与扰动",
    "判断反馈信号是否参与比较",
    "说明比较元件如何形成偏差信号",
    "判断前向通路与主反馈通路",
)


def _clip_text(value: str, *, limit: int = 82) -> str:
    text = " ".join(str(value or "").replace("\n", " ").split()).strip(" ；;。")
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip("，、；;。 ") + "…"


def _build_actionable_explanation(*, focus: str, misconception: str, correct_text: str = "") -> str:
    target = _clip_text(focus or "当前节点的核心判断关系", limit=58)
    trap = _clip_text(misconception or "只看表面元件名称，忽略题干给出的输入、输出和反馈关系", limit=58)
    answer = _clip_text(correct_text, limit=60)
    correct_part = f"正确理解：应先确定{target}"
    if answer:
        correct_part += f"，所以正确项是“{answer}”"
    return _clip_text(
        f"判断依据：从题干中的对象、信号方向和反馈/比较关系入手，而不是只看部件名称。"
        f"{correct_part}。"
        f"易错点：{trap}。",
        limit=190,
    )


def _build_actionable_wrong_option_analysis(*, focus: str, misconception: str, option_text: str = "") -> str:
    target = _clip_text(focus or "当前节点的核心判断关系", limit=52)
    trap = _clip_text(misconception or "把题干表面描述当成判断依据", limit=48)
    option = _clip_text(option_text, limit=44)
    prefix = f"这个选项把“{option}”当成结论，" if option else "这个选项的问题在于"
    return _clip_text(
        f"{prefix}没有按{target}来判断；容易对应的误区是：{trap}。",
        limit=96,
    )


def _is_unsuitable_focus_text(value: Any) -> bool:
    text = " ".join(str(value or "").replace("\n", " ").split()).strip(" ；;。")
    if not text or len(text) < 3:
        return True
    normalized = text.strip("“”\"'：:，,。；; ")
    if normalized in _PLACEHOLDER_TERMS:
        return True
    if _has_low_quality_marker(text):
        return True
    if any(marker in text for marker in _MATERIAL_COPY_MARKERS):
        return True
    punctuation_count = sum(text.count(mark) for mark in ("，", "。", "；", ";", ","))
    if len(text) > 72 and punctuation_count >= 2:
        return True
    return False


def _clean_focus_candidates(values: Any, *, limit: int = 70) -> list[str]:
    cleaned: list[str] = []
    for raw in _string_list(values):
        if _is_unsuitable_focus_text(raw):
            continue
        text = _clip_text(raw, limit=limit)
        if _is_unsuitable_focus_text(text):
            continue
        if text not in cleaned:
            cleaned.append(text)
    return cleaned


def _has_low_quality_marker(text: str) -> bool:
    return any(phrase in text for phrase in _LOW_QUALITY_PHRASES)


def _looks_like_placeholder_question(item: dict[str, Any]) -> bool:
    stem = str(item.get("stem") or "")
    options = _normalize_options(item.get("options"))
    option_values = [str(value or "") for value in options.values()]
    combined = "\n".join([stem] + option_values)
    if _has_low_quality_marker(combined):
        return True
    if "哪一项最能体现本节点要求掌握的" in stem:
        return True
    if any(len(option) > 110 for option in option_values):
        return True
    if len(set(option_values)) < 4:
        return True
    short_correct = str(options.get(_normalize_answer(item.get("answer_key")), "")).strip(" 。")
    if short_correct in {f"符合本节点：{term}" for term in _PLACEHOLDER_TERMS}:
        return True
    generic_hits = sum(1 for term in _PLACEHOLDER_TERMS if f"“{term}”" in combined or term in short_correct)
    return generic_hits >= 3 and not any(keyword in combined for keyword in ("比较元件", "反馈", "扰动", "前向通路", "测量", "被控"))


def _question_quality_errors(item: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    stem = str(item.get("stem") or "").strip()
    options = _normalize_options(item.get("options"))
    answer_key = _answer_key(item)
    option_values = [str(value or "").strip() for value in options.values()]
    if not stem:
        errors.append("missing_stem")
    if set(options.keys()) != {"A", "B", "C", "D"}:
        errors.append("invalid_options")
    if answer_key not in options:
        errors.append("invalid_answer_key")
    if len(set(option_values)) < len(option_values):
        errors.append("duplicate_options")
    if any(len(value) > 95 for value in option_values):
        errors.append("option_too_long")
    if _looks_like_placeholder_question(item):
        errors.append("placeholder_or_template_text")
    return errors


def _extract_teaching_points(tutor_content: str) -> list[str]:
    """从 tutor 讲解输出中提取关键教学点。

    按优先级从以下来源提取:
    1. #### 关键要点 / #### 核心要点 / #### 掌握要点 小节下的条目
    2. #### 核心讲解 小节中的第一句核心陈述
    3. #### 公式讲解 小节中的公式名称(括号前文字)
    4. #### 常见误区 小节中的条目
    """
    points: list[str] = []
    seen: set[str] = set()

    # 1) 提取 关键要点/核心要点/掌握要点 小节中的行
    for section_header in ("关键要点", "核心要点", "掌握要点", "核心总结"):
        pattern = re.compile(
            rf'####\s*{section_header}\s*\n(.*?)(?=\n####\s|\Z)',
            re.DOTALL,
        )
        for m in pattern.finditer(tutor_content):
            section_text = m.group(1).strip()
            for line in section_text.split("\n"):
                text = re.sub(r'^\s*[-*\d.、]+\s*', '', line).strip()
                if text and len(text) > 8 and text not in seen:
                    seen.add(text)
                    points.append(text)

    # 2) 提取 核心讲解 小节首句
    core_match = re.search(
        r'####\s*核心讲解\s*\n(.{20,200}?)(?:[。！？\n])',
        tutor_content,
        re.DOTALL,
    )
    if core_match:
        text = core_match.group(1).strip()
        if text and text not in seen:
            seen.add(text)
            points.append(text)

    # 3) 提取 公式讲解 中的公式名称
    formula_section = re.search(
        r'####\s*公式讲解\s*\n(.*?)(?=\n####\s|\Z)',
        tutor_content,
        re.DOTALL,
    )
    if formula_section:
        for line in formula_section.group(1).split("\n"):
            clean = line.strip()
            # 匹配 "**变量名**：..." 或 "变量名（符号）" 格式
            name_match = re.match(r'\*\*([^*]+)\*\*', clean)
            if name_match:
                text = name_match.group(1).strip()
                if text and text not in seen:
                    seen.add(text)
                    points.append(text)

    # 4) 提取 常见误区 中的条目
    errors = _extract_section_items(tutor_content, "常见误区")
    for err in errors:
        if err not in seen:
            seen.add(err)
            points.append(f"【误区】{err}")

    return points[:8]


def _extract_section_items(content: str, section_title: str) -> list[str]:
    """从 Markdown 小节中提取列表项。"""
    pattern = re.compile(
        rf'####\s*{section_title}\s*\n(.*?)(?=\n####\s|\Z)',
        re.DOTALL,
    )
    m = pattern.search(content)
    if not m:
        return []
    items: list[str] = []
    for line in m.group(1).split("\n"):
        text = re.sub(r'^\s*[-*\d.、]+\s*', '', line).strip()
        if text and len(text) > 4:
            items.append(text)
    return items[:6]


def _build_objective_generation_context(state: AgentState, node_id: str, node_name: str) -> str:
    content = str(
        state.get("node_content_context")
        or state.get("tutor_content")
        or state.get("teaching_content")
        or state.get("last_tutor_response")
        or ""
    ).strip()[:4000]
    lines = [
        f"节点 ID：{node_id or '未指定'}",
        f"节点名称：{node_name or '当前节点'}",
    ]
    field_specs = [
        ("学习目标", state.get("graph_learning_objectives")),
        ("必会要点", state.get("graph_must_know")),
        ("常见误区", state.get("graph_common_errors")),
        ("前置节点", state.get("graph_prerequisites")),
        ("相邻/对照节点", state.get("graph_neighbors")),
    ]
    for label, values in field_specs:
        joined = _join_list(values)
        if joined:
            lines.append(f"{label}：{joined}")
    target_level = str(state.get("graph_target_mastery_level") or "").strip()
    difficulty = str(state.get("graph_difficulty") or "").strip()
    if target_level:
        lines.append(f"目标掌握层级：{target_level}")
    if difficulty:
        lines.append(f"难度标签：{difficulty}")
    contract = _teaching_contract(state)
    if contract:
        lines.append("节点教学契约：")
        goal = str(contract.get("learning_goal") or "").strip()
        if goal:
            lines.append(f"契约目标：{goal}")
        must_know = _join_list(contract.get("must_know"))
        if must_know:
            lines.append(f"契约必会：{must_know}")
        misconceptions = _join_list(contract.get("common_misconceptions"))
        if misconceptions:
            lines.append(f"契约误区：{misconceptions}")
        exit_criteria = _join_list(contract.get("exit_criteria"))
        if exit_criteria:
            lines.append(f"退出条件：{exit_criteria}")
    if content:
        lines.append(f"节点讲解/检索内容摘要：\n{content}")
    # 从 tutor 输出提取关键教学点作为显式出题约束
    tutor_content_raw = str(state.get("tutor_content") or "").strip()
    if tutor_content_raw:
        teaching_points = _extract_teaching_points(tutor_content_raw)
        if teaching_points:
            lines.append("\n【已讲解的关键要点——出题时必须覆盖至少 3 项】")
            for i, pt in enumerate(teaching_points, 1):
                lines.append(f"{i}. {pt}")
    return "\n".join(lines)


def _build_question_blueprints(state: AgentState, node_id: str, node_name: str, count: int, *, start_index: int = 1) -> list[dict[str, Any]]:
    contract_targets = _contract_assessment_targets(state)
    must_know = _clean_focus_candidates(state.get("graph_must_know"), limit=70)
    objectives = _clean_focus_candidates(state.get("graph_learning_objectives"), limit=70)
    common_errors = _clean_focus_candidates(state.get("graph_common_errors"), limit=70)
    concepts = must_know or objectives or list(_FALLBACK_TARGET_OBJECTIVES)
    errors = common_errors or ["混淆题干条件与当前节点的核心判断依据"]
    answer_keys = ("A", "B", "C", "D")
    blueprints: list[dict[str, Any]] = []
    for offset in range(max(0, count)):
        index = start_index + offset
        contract_target = contract_targets[offset % len(contract_targets)] if contract_targets else {}
        concept = str(contract_target.get("target_objective") or concepts[offset % len(concepts)]).strip()
        misconception = str(contract_target.get("misconception") or errors[offset % len(errors)]).strip()
        blueprints.append(
            {
                "question_id": f"AI-Q{index}",
                "assessment_focus": str(contract_target.get("assessment_focus") or _default_assessment_focus(state, index)).strip(),
                "target_objective": _default_target_objective(state, node_name=node_name, concept=concept, index=index),
                "misconception": _default_misconception(state, fallback=misconception, index=index),
                "difficulty": _question_difficulty(state, index),
                "answer_key": answer_keys[(index - 1) % len(answer_keys)],
                "required": bool(contract_target.get("required")),
            }
        )
    return blueprints


def _format_question_blueprints(blueprints: list[dict[str, Any]]) -> str:
    return json.dumps(blueprints, ensure_ascii=False, indent=2)


def _normalize_ai_question_batch(
    raw_questions: list[dict[str, Any]],
    *,
    state: AgentState,
    node_id: str,
    node_name: str,
    start_index: int = 1,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for offset, raw in enumerate(raw_questions, start=0):
        index = start_index + offset
        item = _normalize_question(raw, index, node_id)
        if item is None:
            rejected.append({"index": index, "question_id": str(raw.get("question_id") or f"AI-Q{index}"), "errors": ["invalid_schema"]})
            continue
        enriched = _enrich_question_metadata(item, state=state, index=index, node_id=node_id, node_name=node_name)
        errors = _question_quality_errors(enriched)
        if errors:
            rejected.append({"index": index, "question_id": enriched.get("question_id") or f"AI-Q{index}", "errors": errors})
            continue
        accepted.append(enriched)
    return accepted, rejected


def _build_objective_generation_messages(
    *,
    topic: str,
    node_context: str,
    node_id: str,
    count: int,
    blueprints: list[dict[str, Any]],
    repair_rejections: list[dict[str, Any]] | None = None,
) -> list[object]:
    system_msg = SystemMessage(
        content=(
            "你是严谨的课程测评出题专家。请只输出合法 JSON，不要 Markdown。"
            "你生成的是节点学习后的客观选择题，不是学前自评题。"
            "题目必须紧扣当前节点字段，检验学习者是否理解本节点的具体概念、条件、因果关系和常见误区。"
        )
    )
    repair_note = ""
    if repair_rejections:
        repair_note = (
            "\n\n【上一轮被拒绝的题目】\n"
            + json.dumps(repair_rejections, ensure_ascii=False, indent=2)
            + "\n请只补这些缺口，不要复用被拒绝题目的题干或选项。"
        )
    human_msg = HumanMessage(
        content=f"""请为当前知识图谱节点生成 {count} 道四选一客观题。
主题：{topic or '未指定'}
当前节点结构化字段：
{node_context or '无'}

【出题蓝图】
下面每一项就是一道题的命题约束。必须逐条遵守 assessment_focus、target_objective、misconception、difficulty 和 answer_key；尤其 answer_key 不能自行改成全 A。
{_format_question_blueprints(blueprints)}
{repair_note}

要求：
1. 每题必须是 A/B/C/D 四选一。
2. 每题必须包含 answer_key，值只能是 A/B/C/D。
3. answer_key 是后续程序确定性评分的唯一依据，所以必须明确可靠。
4. 题干必须包含本节点的具体对象、条件、判断或应用场景，不要写成泛化模板。
5. 每个选项必须是 1 个明确判断，长度不超过 90 个汉字；禁止把整段讲解材料复制进选项。
6. 正确项要给出可判断的具体事实/关系，不能写“符合本节点：实例/示例/自动控制”这类占位文本。
7. 干扰项要对应真实误区，且与正确项只差一个关键条件；禁止“结论方向相反”“与本节点无关”这类万能干扰项。
8. 至少优先覆盖“学习目标”“必会要点”和“常见误区”。
9. 禁止生成“第 1 个核心判断”这类占位题，禁止所有题目的正确选项固定为 A。
10. 输出 JSON Schema：
{{
  "questions": [
    {{
      "question_id": "AI-Q1",
      "node_id": "{node_id}",
      "stem": "题干",
      "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
      "answer_key": "A",
      "assessment_focus": "概念辨析/判断依据/常见误区/应用迁移之一",
      "target_objective": "本题检验的具体学习目标或必会点",
      "misconception": "本题主要针对的常见误区",
      "difficulty": 1-5,
      "explanation": "为什么正确答案成立",
      "wrong_option_analysis": {{"A":"若 A 错，说明错在哪里", "B":"...", "C":"...", "D":"..."}}
    }}
  ]
}}
""",
    )
    return [system_msg, human_msg]


def _generate_ai_questions(llm: Any, state: AgentState, node_id: str, node_name: str, count: int) -> list[dict[str, Any]]:
    if llm is None:
        return []
    topic = str(state.get("current_topic") or state.get("turn_goal") or "").strip()
    node_context = _build_objective_generation_context(state, node_id, node_name)
    blueprints = _build_question_blueprints(state, node_id, node_name, count)
    messages = _build_objective_generation_messages(
        topic=topic,
        node_context=node_context,
        node_id=node_id,
        count=count,
        blueprints=blueprints,
    )
    try:
        response = llm.invoke(messages)
    except Exception:
        return []
    response_text = content_to_text(getattr(response, "content", response))
    parsed = parse_json_object(response_text)
    normalized, rejected = _normalize_ai_question_batch(
        _extract_question_list(parsed),
        state=state,
        node_id=node_id,
        node_name=node_name,
        start_index=1,
    )
    if rejected and len(normalized) < count:
        repair_count = count - len(normalized)
        repair_blueprints = _build_question_blueprints(
            state,
            node_id,
            node_name,
            repair_count,
            start_index=len(normalized) + 1,
        )
        repair_messages = _build_objective_generation_messages(
            topic=topic,
            node_context=node_context,
            node_id=node_id,
            count=repair_count,
            blueprints=repair_blueprints,
            repair_rejections=rejected,
        )
        try:
            repair_response = llm.invoke(repair_messages)
        except Exception:
            repair_response = None
        if repair_response is not None:
            repair_text = content_to_text(getattr(repair_response, "content", repair_response))
            repair_parsed = parse_json_object(repair_text)
            repaired, _repair_rejected = _normalize_ai_question_batch(
                _extract_question_list(repair_parsed),
                state=state,
                node_id=node_id,
                node_name=node_name,
                start_index=len(normalized) + 1,
            )
            normalized.extend(repaired)
    return normalized[:count]


def _fallback_questions(node_id: str, node_name: str, k: int = 10, state: AgentState | None = None) -> list[dict[str, Any]]:
    state = state or {}
    title = node_name or node_id or "当前节点"
    objectives = _clean_focus_candidates(state.get("graph_learning_objectives"), limit=46)
    must_know = _clean_focus_candidates(state.get("graph_must_know"), limit=46)
    common_errors = _clean_focus_candidates(state.get("graph_common_errors"), limit=46)

    has_explicit_focuses = bool(must_know or objectives)
    focuses = must_know or objectives
    if not focuses:
        focuses = list(_FALLBACK_TARGET_OBJECTIVES)
    errors = common_errors or [
        "只看外部动作，忽略测量反馈",
        "把开环控制误认为闭环控制",
        "把扰动当成有用输入",
        "忽略比较元件形成偏差信号的作用",
        "只按元件名称判断，不分析信号通路",
    ]

    templates = [
        {
            "focus": "区分被控对象与控制装置",
            "stem": "分析一个恒温箱自动调温系统时，哪一项最准确地区分了被控对象和控制装置？",
            "correct": "恒温箱内温度变化过程是被控对象，温控器和执行加热机构属于控制装置",
            "distractors": [
                "设定温度是被控对象，箱体材料是控制装置",
                "只要能发热的部件都是被控对象，传感器不参与控制",
                "外界气温扰动越大，被控对象和控制装置就可以互换",
            ],
        },
        {
            "focus": "识别输入、输出与扰动",
            "stem": "在水箱液位控制系统中，下列哪组对应关系最合理？",
            "correct": "期望液位是给定输入，实际液位是输出，进水压力波动可视为扰动",
            "distractors": [
                "实际液位是给定输入，期望液位是扰动",
                "只要水泵工作，系统就没有输出量",
                "进水压力波动是有用输入，不会影响控制效果",
            ],
        },
        {
            "focus": "判断反馈是否参与比较",
            "stem": "判断一个速度控制系统是否属于反馈控制时，最关键的依据是什么？",
            "correct": "是否测量实际速度，并将测量结果送回与给定速度比较",
            "distractors": [
                "是否使用了电动机作为执行元件",
                "是否存在人为设定的目标速度，但不关心实际速度",
                "是否控制器名称中出现“自动”二字",
            ],
        },
        {
            "focus": "理解偏差信号",
            "stem": "典型负反馈控制中，比较元件的主要作用是什么？",
            "correct": "比较给定量与反馈量，形成用于调节控制器的偏差信号",
            "distractors": [
                "直接放大输出量，使输出越大越稳定",
                "只记录扰动大小，不影响控制器动作",
                "把传感器信号完全丢弃，避免影响输入",
            ],
        },
        {
            "focus": "判断闭环控制特征",
            "stem": "下列哪种描述最能体现闭环控制区别于开环控制的特点？",
            "correct": "控制动作会根据输出测量结果与目标值之间的偏差不断调整",
            "distractors": [
                "控制器只按预设时间表动作，不需要检测输出",
                "系统越复杂就一定是闭环控制",
                "只要存在扰动，系统就自动成为闭环控制",
            ],
        },
        {
            "focus": "识别测量元件作用",
            "stem": "在电机转速自动调节系统中，测速发电机或编码器的核心作用是什么？",
            "correct": "测量实际转速，并把测量结果作为反馈信号送回比较环节",
            "distractors": [
                "直接产生目标转速，不需要控制器参与",
                "只负责提供电源，和转速调节无关",
                "把负载扰动完全消除，因此系统不再需要反馈",
            ],
        },
        {
            "focus": "区分有用输入与扰动",
            "stem": "在室温控制系统中，哪一项最准确地区分了有用输入和扰动？",
            "correct": "设定温度是有用输入，室外温度突然变化可视为扰动",
            "distractors": [
                "室外温度变化是有用输入，设定温度是扰动",
                "只要空调能运行，系统就不存在扰动",
                "扰动只会作用在输入端，不可能影响被控对象",
            ],
        },
        {
            "focus": "理解前向通路",
            "stem": "在典型反馈系统方框图中，前向通路通常指什么？",
            "correct": "信号从输入端经过控制装置到达输出端的传输路径",
            "distractors": [
                "输出信号经测量元件回到输入端的路径",
                "只包含扰动进入系统的路径",
                "只要有箭头的线都称为前向通路",
            ],
        },
        {
            "focus": "理解主反馈通路",
            "stem": "一个系统的输出经测量元件送回输入端参与比较，这条路径通常称为什么？",
            "correct": "主反馈通路",
            "distractors": [
                "前向通路",
                "有用输入通路",
                "扰动补偿通路",
            ],
        },
        {
            "focus": "判断负反馈方向",
            "stem": "如果实际温度高于设定温度，负反馈温控系统通常应如何调节加热功率？",
            "correct": "降低加热功率，使温度逐步回到设定值附近",
            "distractors": [
                "继续增大加热功率，使温度更快升高",
                "完全忽略实际温度，只按固定功率加热",
                "把设定温度改成当前实际温度，避免产生偏差",
            ],
        },
    ]

    def template_match_score(template: dict[str, Any], focus: str) -> int:
        focus_text = str(focus or "")
        if not focus_text:
            return 0
        template_text = " ".join(
            [
                str(template.get("focus") or ""),
                str(template.get("stem") or ""),
                str(template.get("correct") or ""),
                *(str(item) for item in template.get("distractors", [])),
            ]
        )
        keywords = (
            "被控对象",
            "控制装置",
            "给定",
            "输入",
            "输出",
            "扰动",
            "反馈",
            "测量",
            "比较",
            "偏差",
            "闭环",
            "开环",
            "前向通路",
            "主反馈",
            "负反馈",
            "控制器",
            "执行",
        )
        return sum(1 for keyword in keywords if keyword in focus_text and keyword in template_text)

    used_templates: set[int] = set()

    def choose_template(focus: str, fallback_index: int) -> tuple[int, dict[str, Any]]:
        scored = [
            (
                template_match_score(template, focus),
                0 if index not in used_templates else -1,
                -abs(index - fallback_index),
                index,
            )
            for index, template in enumerate(templates)
        ]
        scored.sort(reverse=True)
        best_score, _unused_bonus, _distance, best_index = scored[0]
        best_template = templates[best_index]
        if best_score <= 0:
            best_index = fallback_index % len(templates)
            best_template = templates[best_index]
        used_templates.add(best_index)
        if len(used_templates) >= len(templates):
            used_templates.clear()
        return best_index, best_template

    questions: list[dict[str, Any]] = []
    for i in range(1, k + 1):
        focus_seed = focuses[(i - 1) % len(focuses)] if focuses else ""
        if has_explicit_focuses:
            _template_index, base = choose_template(focus_seed, i - 1)
            focus = focus_seed if template_match_score(base, focus_seed) > 0 else base["focus"]
        else:
            base = templates[(i - 1) % len(templates)]
            focus = base["focus"]
        error_seed = errors[(i - 1) % len(errors)]
        correct_key = ("A", "B", "C", "D")[(i - 1) % 4]
        # 学生可见选项必须是自然答案；不要把“关键在于/典型误区是”等命题元信息写进选项。
        correct_text = _clip_text(str(base["correct"]), limit=88)
        distractors = [_clip_text(text, limit=88) for text in base["distractors"]]
        option_keys = ["A", "B", "C", "D"]
        options: dict[str, str] = {}
        distractor_iter = iter(distractors)
        for key in option_keys:
            options[key] = correct_text if key == correct_key else next(distractor_iter)
        questions.append(
            {
                "question_id": f"AUTO-{node_id or 'NODE'}-{i}",
                "node_id": node_id,
                "stem": _clip_text(str(base["stem"]), limit=96),
                "options": options,
                "answer_key": correct_key,
                "assessment_focus": _default_assessment_focus(state, i),
                "target_objective": _default_target_objective(state, node_name=title, concept=focus, index=i),
                "misconception": _default_misconception(state, fallback=error_seed, index=i),
                "difficulty": _question_difficulty(state, i),
                "explanation": _build_actionable_explanation(
                    focus=focus,
                    misconception=error_seed,
                    correct_text=correct_text,
                ),
                "wrong_option_analysis": {
                    key: _build_actionable_wrong_option_analysis(
                        focus=focus,
                        misconception=error_seed,
                        option_text=options.get(key, ""),
                    )
                    for key in ("A", "B", "C", "D")
                    if key != correct_key
                },
                "source": "contextual_fallback",
            }
        )
    return questions


def _parse_answers(raw: Any) -> dict[str, str]:
    if isinstance(raw, dict):
        return {str(k): _normalize_answer(v) for k, v in raw.items()}
    if isinstance(raw, str):
        # Try JSON first (frontend sends '{"AI-Q1":"A","AI-Q2":"B",...}')
        trimmed = raw.strip()
        if trimmed.startswith("{"):
            try:
                parsed = json.loads(trimmed)
                if isinstance(parsed, dict):
                    return {str(k): _normalize_answer(v) for k, v in parsed.items()}
            except (json.JSONDecodeError, ValueError):
                pass
        # Accept compact forms like "A B C D" for simple CLI/manual tests.
        parts = [part.strip() for part in raw.replace(",", " ").split() if part.strip()]
        return {f"Q{idx}": _normalize_answer(part) for idx, part in enumerate(parts, start=1)}
    return {}


def _format_quiz_review_message(
    *,
    title: str,
    items: list[dict[str, Any]],
    answers: dict[str, str],
    score: int,
    passed: bool,
) -> str:
    lines = [f"{title}批改", f"得分：{score} 分，{'已通过' if passed else '需要订正'}。"]
    for index, item in enumerate(items, start=1):
        qid = _question_id(item, index)
        expected = _answer_key(item)
        user_answer = _normalize_answer(answers.get(qid) or answers.get(str(index)) or answers.get(f"Q{index}"))
        stem = str(item.get("stem") or item.get("question") or f"第 {index} 题").strip()
        marker = "✓" if expected and user_answer == expected else "✗"
        lines.extend(
            [
                "",
                f"{marker} {qid}. {stem}",
                f"你的答案：{user_answer or '未作答'}；正确答案：{expected or '未提供'}",
            ]
        )
        explanation = str(item.get("explanation") or "").strip()
        if explanation:
            lines.append(f"解析：{explanation}")
    return "\n".join(lines)


def _quiz_review_history_entry(
    *,
    title: str,
    kind: str,
    items: list[dict[str, Any]],
    answers: dict[str, str],
    score: int,
    passed: bool,
    pass_score: int = 80,
    node_id: str = "",
    node_name: str = "",
) -> dict[str, Any]:
    reviewed_items: list[dict[str, Any]] = []
    correct_count = 0
    for index, item in enumerate(items, start=1):
        qid = _question_id(item, index)
        expected = _answer_key(item)
        user_answer = _normalize_answer(answers.get(qid) or answers.get(str(index)) or answers.get(f"Q{index}"))
        is_correct = bool(expected) and user_answer == expected
        if is_correct:
            correct_count += 1
        reviewed_items.append(
            {
                **item,
                "question_id": qid,
                "display_index": index,
                "chosen_answer": user_answer,
                "correct_answer": expected,
                "is_correct": is_correct,
                "locked": True,
                "submitted": True,
                "explanation_ready": bool(item.get("explanation")),
            }
        )
    question_count = len(items)
    wrong_count = max(0, question_count - correct_count)
    return {
        "role": "assistant",
        "kind": "objective_quiz_review",
        "content": _format_quiz_review_message(
            title=title,
            items=items,
            answers=answers,
            score=score,
            passed=passed,
        ),
        "data": {
            "kind": kind,
            "title": title,
            "quiz_id": f"{kind}-{node_id or 'node'}-{now_ts()}",
            "quiz_kind": kind,
            "node_id": node_id,
            "node_name": node_name,
            "submitted_at": now_ts(),
            "questions": reviewed_items,
            "answers": answers,
            "score": score,
            "pass_score": pass_score,
            "passed": passed,
            "question_count": question_count,
            "correct_count": correct_count,
            "wrong_count": wrong_count,
            "locked": True,
            "review_state": "graded",
        },
    }


def _build_objective_mastery_summary(
    *,
    items: list[dict[str, Any]],
    answers: dict[str, str],
    required_targets: list[str],
) -> dict[str, Any]:
    stats: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(items, start=1):
        target = str(item.get("target_objective") or "").strip() or "未分类目标"
        qid = _question_id(item, index)
        expected = _answer_key(item)
        user_answer = _normalize_answer(answers.get(qid) or answers.get(str(index)) or answers.get(f"Q{index}"))
        bucket = stats.setdefault(target, {"target_objective": target, "total": 0, "correct": 0, "accuracy": 0.0})
        bucket["total"] += 1
        if expected and user_answer == expected:
            bucket["correct"] += 1

    for bucket in stats.values():
        total = int(bucket.get("total") or 0)
        correct = int(bucket.get("correct") or 0)
        bucket["accuracy"] = round(correct / total, 3) if total else 0.0

    required_failed: list[str] = []
    for target in required_targets:
        bucket = stats.get(target)
        if not bucket or float(bucket.get("accuracy") or 0) < 0.7:
            required_failed.append(target)

    return {
        "target_stats": list(stats.values()),
        "required_targets": required_targets,
        "required_failed_targets": required_failed,
        "required_target_threshold": 0.7,
    }


def build_objective_test_generator_node(runtime: RuntimeContext, llm: Any | None = None, *, count: int = 10):
    event_sink = runtime.event_sink

    def node(state: AgentState) -> dict:
        node_id = str(state.get("current_node_id") or state.get("graph_anchor_id") or "").strip()
        node_name = str(state.get("current_node_name") or state.get("graph_anchor_title") or "").strip()
        quiz_kind = str(state.get("node_quiz_kind") or "").strip()
        # 首次测验统一 10 题；复测（node_retest）5 题
        effective_count = 5 if quiz_kind == "node_retest" else count
        coverage_plan = _build_question_blueprints(state, node_id, node_name, effective_count)
        provider = getattr(runtime, "question_bank_provider", None)
        questions: list[dict[str, Any]] = []
        if provider is not None and hasattr(provider, "get_objective_questions"):
            questions = list(provider.get_objective_questions(node_id, k=effective_count) or [])
        if not questions:
            questions = _generate_ai_questions(llm, state, node_id, node_name, effective_count)
        if not questions:
            event_sink.emit(
                make_event(
                    "node.error",
                    "objective_test_generator",
                    message=f"节点【{node_name or node_id}】出题失败：题库和 AI 生成均未产出题目。",
                    data={"node_id": node_id, "node_name": node_name, "quiz_kind": quiz_kind},
                )
            )
            raise RuntimeError(
                f"节点【{node_name or node_id}】出题失败：题库无此题且 AI 生成返回空。"
                f"请检查题库配置或 LLM 服务状态。"
            )
        questions = [
            _enrich_question_metadata(dict(item), state=state, index=index, node_id=node_id, node_name=node_name)
            for index, item in enumerate(questions[:effective_count], start=1)
            if isinstance(item, dict)
        ]

        prompt = f"请完成节点【{node_name or node_id}】的 {len(questions)} 道客观选择题。"
        event_sink.emit(
            make_event(
                "node.start",
                "objective_test_generator",
                message=prompt,
                data={"questions": questions, "coverage_plan": coverage_plan, "requires_input": True},
            )
        )
        used_kind = "objective_test_answers" if quiz_kind != "node_retest" else "node_retest"
        return {
            "node_quiz_items": questions,
            "node_quiz_coverage_plan": coverage_plan,
            "node_quiz_answers": {},
            "node_quiz_wrong_items": [],
            "node_quiz_score": 0,
            "node_quiz_kind": used_kind,
            "variant_questions": [],
            "flow_status": "awaiting_objective_answers",
            "learning_phase": "node_quiz_retest" if quiz_kind == "node_retest" else "node_quiz_batch",
            "learning_resume_target": "objective_test_scorer",
            "learning_resume_reason": "retest_questions_generated" if quiz_kind == "node_retest" else "objective_questions_generated",
            "pending_interaction_kind": "objective_test_answers",
            "pending_interaction_prompt": prompt,
            "pending_interaction_options": questions,
            "pending_interaction_recommended": "",
            "pending_interaction_answer": "",
            "current_node_status": "quizzing",
        }

    return node


def build_objective_test_scorer_node(runtime: RuntimeContext, *, pass_score: int = 80):
    event_sink = runtime.event_sink

    def _record_question_attempts(state: AgentState, items: list[dict[str, Any]], answers: dict[str, str], score: int, passed: bool) -> dict[str, Any]:
        store = getattr(runtime, "student_state_store", None)
        if store is None or not hasattr(store, "load") or not hasattr(store, "save"):
            return {}
        student_id = str(state.get("student_id") or "default_student").strip() or "default_student"
        node_id = str(state.get("current_node_id") or state.get("graph_anchor_id") or "").strip()

        def apply_patch(student_state) -> None:
            attempts = list(getattr(student_state, "question_attempts", []) or [])
            for index, item in enumerate(items, start=1):
                qid = _question_id(item, index)
                answer = answers.get(qid) or answers.get(str(index)) or answers.get(f"Q{index}") or ""
                attempts.append(
                    {
                        "question_id": qid,
                        "node_id": node_id,
                        "answer": answer,
                        "expected": _answer_key(item),
                        "quiz_score": score,
                        "quiz_passed": passed,
                        "created_at": now_ts(),
                    }
                )
            student_state.question_attempts = attempts[-200:]

        return mutate_student_state_snapshot(store, student_id, apply_patch)

    def node(state: AgentState) -> dict:
        raw_items = [item for item in list(state.get("node_quiz_items") or []) if isinstance(item, dict)]
        node_id = str(state.get("current_node_id") or state.get("graph_anchor_id") or "").strip()
        node_name = str(state.get("current_node_name") or state.get("graph_anchor_title") or "").strip()
        items = [
            _enrich_question_metadata(dict(item), state=state, index=index, node_id=node_id, node_name=node_name)
            for index, item in enumerate(raw_items, start=1)
        ]
        answers = dict(state.get("node_quiz_answers") or {})
        pending_answer = state.get("pending_interaction_answer")
        if pending_answer and not answers:
            answers = _parse_answers(pending_answer)
        total = len(items)
        correct = 0
        wrong_items: list[dict[str, Any]] = []

        for index, item in enumerate(items, start=1):
            qid = _question_id(item, index)
            expected = _answer_key(item)
            user_answer = _normalize_answer(answers.get(qid) or answers.get(str(index)) or answers.get(f"Q{index}"))
            is_correct = bool(expected) and user_answer == expected
            if is_correct:
                correct += 1
            else:
                wrong_items.append(
                    {
                        **item,
                        "question_id": qid,
                        "user_answer": user_answer,
                        "answer_key": expected,
                        "is_correct": False,
                    }
                )

        score = int(round((correct / total) * 100)) if total else 0
        objective_mastery_summary = _build_objective_mastery_summary(
            items=items,
            answers=answers,
            required_targets=_contract_required_targets(state),
        )
        contract_failed_targets = list(objective_mastery_summary.get("required_failed_targets") or [])
        score_passed = score >= pass_score
        passed = score_passed and not contract_failed_targets
        student_id = str(state.get("student_id") or "default_student").strip() or "default_student"
        updated_snapshot = update_student_state_after_evaluation(
            getattr(runtime, "student_state_store", None),
            student_id=student_id,
            node_id=node_id,
            score=score,
            passed=passed,
            teaching_strategy=str(state.get("teaching_strategy") or "").strip(),
            difficulty_level=int(state.get("difficulty_level") or 0),
            wrong_items=wrong_items,
            node_title=str(state.get("graph_anchor_title") or state.get("current_node_name") or "").strip(),
        )
        attempt_snapshot = _record_question_attempts(state, items, answers, score, passed)
        if attempt_snapshot:
            updated_snapshot = {**updated_snapshot, "question_attempts": attempt_snapshot.get("question_attempts", [])}

        quiz_kind = str(
            state.get("node_quiz_kind")
            or state.get("pending_interaction_kind")
            or "objective_test_answers"
        ).strip() or "objective_test_answers"
        review_title = "变式练习" if quiz_kind == "variant_test_answers" else "客观测评"
        review_entry = _quiz_review_history_entry(
            title=review_title,
            kind=quiz_kind,
            items=items,
            answers=answers,
            score=score,
            passed=passed,
            pass_score=pass_score,
            node_id=node_id,
            node_name=node_name,
        )
        event_sink.emit(
            make_event(
                "node.complete",
                "objective_test_scorer",
                message=f"本节点客观题得分 {score} 分，{'已通过' if passed else '需要订正后再验证'}。",
                data={
                    "score": score,
                    "passed": passed,
                    "wrong_count": len(wrong_items),
                    "objective_mastery_summary": objective_mastery_summary,
                    "review": review_entry.get("data", {}),
                    "review_content": review_entry.get("content", ""),
                },
            )
        )
        message_history = list(state.get("message_history", []))
        message_history.append(review_entry)

        # ── Update user_knowledge_graph based on quiz result ──
        user_kg = dict(state.get("user_knowledge_graph") or {})
        if node_id:
            for _concept, entry in user_kg.items():
                entry_id = str(entry.get("id") or "").strip()
                if entry_id == node_id:
                    if passed:
                        entry["status"] = "mastered"
                    else:
                        entry["status"] = "in_progress"
                    entry["turn_count"] = int(entry.get("turn_count") or 0) + 1
                    break

        # ── 根据 quiz_kind 和分数设定补救状态 ──
        is_variant = quiz_kind == "variant_test_answers"
        is_retest = quiz_kind == "node_retest"
        current_remediation = dict(state.get("node_remediation_state") or {})
        if not passed:
            if is_variant:
                # 变式未通过：递增轮次和额外题数
                current_remediation["variant_rounds"] = current_remediation.get("variant_rounds", 0) + 1
                current_remediation["extra_remediation_question_count"] = current_remediation.get(
                    "extra_remediation_question_count", 0
                ) + len(wrong_items)
                current_remediation["status"] = "variant_failed"
            elif is_retest:
                # 短复测未通过 → 回到补救决策
                current_remediation["status"] = "retest_failed"
                return {
                    "node_quiz_answers": answers,
                    "node_quiz_wrong_items": wrong_items,
                    "node_quiz_score": score,
                    "score": score,
                    "feedback": (
                        f"短复测得分 {score}，关键目标未达标：{'、'.join(contract_failed_targets)}。需返回补救决策。"
                        if contract_failed_targets
                        else f"短复测得分 {score}，未达到 80 分。需返回补救决策。"
                    ),
                    "wrong_question_explanations": [],
                    "variant_questions": [],
                    "objective_mastery_summary": objective_mastery_summary,
                    "flow_status": "normal",
                    "learning_phase": "node_quiz_retry",
                    "learning_resume_target": "remediation_decision",
                    "learning_resume_reason": "retest_failed",
                    "pending_interaction_kind": "",
                    "pending_interaction_prompt": "",
                    "pending_interaction_options": [],
                    "pending_interaction_recommended": "",
                    "pending_interaction_answer": "",
                    "node_quiz_kind": "",
                    "current_node_status": "quizzing",
                    "student_state_snapshot": updated_snapshot or state.get("student_state_snapshot") or {},
                    "user_knowledge_graph": user_kg,
                    "node_remediation_state": current_remediation,
                    "message_history": trim_message_history(message_history),
                }
            else:
                # 原始测试未通过：记录原始分数
                current_remediation["original_score"] = score
                current_remediation["extra_remediation_question_count"] = current_remediation.get(
                    "extra_remediation_question_count", 0
                ) + len(wrong_items)
                current_remediation["status"] = "scored"

            if is_variant:
                # 变式未通过 → 回到补救决策（不再重复讲解）
                feedback = f"变式得分 {score}，未达到 {pass_score}。已记录变式失败，将决定是否继续补救或暂停。"
                if contract_failed_targets:
                    feedback = f"变式得分 {score}，但关键目标未达标：{'、'.join(contract_failed_targets)}。将决定是否继续补救或暂停。"
                return {
                    "node_quiz_answers": answers,
                    "node_quiz_wrong_items": wrong_items,
                    "node_quiz_score": score,
                    "score": score,
                    "feedback": feedback,
                    "wrong_question_explanations": [],
                    "variant_questions": [],
                    "objective_mastery_summary": objective_mastery_summary,
                    "flow_status": "normal",
                    "learning_phase": "node_quiz_variant_retry",
                    "learning_resume_target": "remediation_decision",
                    "learning_resume_reason": "variant_quiz_failed",
                    "pending_interaction_kind": "",
                    "pending_interaction_prompt": "",
                    "pending_interaction_options": [],
                    "pending_interaction_recommended": "",
                    "pending_interaction_answer": "",
                    "node_quiz_kind": "",
                    "current_node_status": "quizzing",
                    "student_state_snapshot": updated_snapshot or state.get("student_state_snapshot") or {},
                    "user_knowledge_graph": user_kg,
                    "node_remediation_state": current_remediation,
                    "message_history": trim_message_history(message_history),
                }

            return {
                "node_quiz_answers": answers,
                "node_quiz_wrong_items": wrong_items,
                "node_quiz_score": score,
                "score": score,
                "feedback": (
                    f"本轮得分 {score}，但关键目标未达标：{'、'.join(contract_failed_targets)}，需要先订正错题并完成变式。"
                    if contract_failed_targets
                    else f"本轮得分 {score}，未达到 {pass_score}，需要先订正错题并完成变式。"
                ),
                "wrong_question_explanations": [],
                "variant_questions": [],
                "objective_mastery_summary": objective_mastery_summary,
                "flow_status": "normal",
                "learning_phase": "node_quiz_remediation",
                "learning_resume_target": "wrong_question_explainer",
                "learning_resume_reason": "objective_quiz_failed_needs_remediation",
                "pending_interaction_kind": "",
                "pending_interaction_prompt": "",
                "pending_interaction_options": [],
                "pending_interaction_recommended": "",
                "pending_interaction_answer": "",
                "node_quiz_kind": "",
                "current_node_status": "quizzing",
                "student_state_snapshot": updated_snapshot or state.get("student_state_snapshot") or {},
                "user_knowledge_graph": user_kg,
                "node_remediation_state": current_remediation,
                "message_history": trim_message_history(message_history),
            }

        # ── 测验通过 ──
        if is_variant:
            # 变式通过 → 检查原始分数决定是否短复测
            original_score = current_remediation.get("original_score", state.get("node_quiz_score", 0))
            current_remediation["status"] = "passed_after_remediation"
            if original_score >= 70:
                feedback = f"变式得分 {score}，通过。原测验 {original_score} 分 >= 70，可以进入下一节点。"
                next_target = "next_node_planner"
                next_reason = "variant_passed_next_node"
            else:
                feedback = f"变式得分 {score}，通过。但原测验 {original_score} 分 < 70，需完成 5 题短复测。"
                next_target = "objective_test_generator"
                next_reason = "variant_passed_needs_retest"
            return {
                "node_quiz_answers": answers,
                "node_quiz_wrong_items": wrong_items,
                "node_quiz_score": score,
                "score": score,
                "feedback": feedback,
                "variant_questions": [],
                "objective_mastery_summary": objective_mastery_summary,
                "flow_status": "normal",
                "learning_phase": "node_passed" if original_score >= 70 else "node_quiz_retest",
                "learning_resume_target": next_target,
                "learning_resume_reason": next_reason,
                "pending_interaction_kind": "",
                "pending_interaction_prompt": "",
                "pending_interaction_options": [],
                "pending_interaction_recommended": "",
                "pending_interaction_answer": "",
                "node_quiz_kind": "node_retest" if original_score < 70 else "",
                "current_node_status": "passed" if original_score >= 70 else "quizzing",
                "student_state_snapshot": updated_snapshot or state.get("student_state_snapshot") or {},
                "user_knowledge_graph": user_kg,
                "node_remediation_state": current_remediation,
                "message_history": trim_message_history(message_history),
            }

        if is_retest:
            # 短复测通过 → 允许进入下一节点
            current_remediation["status"] = "passed_after_retest"
            feedback = f"短复测得分 {score}，通过。可以进入下一节点。"
            return {
                "node_quiz_answers": answers,
                "node_quiz_wrong_items": wrong_items,
                "node_quiz_score": score,
                "score": score,
                "feedback": feedback,
                "variant_questions": [],
                "objective_mastery_summary": objective_mastery_summary,
                "flow_status": "normal",
                "learning_phase": "node_passed",
                "learning_resume_target": "next_node_planner",
                "learning_resume_reason": "retest_passed",
                "pending_interaction_kind": "",
                "pending_interaction_prompt": "",
                "pending_interaction_options": [],
                "pending_interaction_recommended": "",
                "pending_interaction_answer": "",
                "node_quiz_kind": "",
                "current_node_status": "passed",
                "student_state_snapshot": updated_snapshot or state.get("student_state_snapshot") or {},
                "user_knowledge_graph": user_kg,
                "node_remediation_state": current_remediation,
                "message_history": trim_message_history(message_history),
            }

        # 原始测验通过
        return {
            "node_quiz_answers": answers,
            "node_quiz_wrong_items": wrong_items,
            "node_quiz_score": score,
            "score": score,
            "feedback": f"本轮得分 {score}，已达到 {pass_score}，可以进入下一节点决策。",
            "variant_questions": [],
            "objective_mastery_summary": objective_mastery_summary,
            "flow_status": "normal",
            "learning_phase": "node_passed",
            "learning_resume_target": "next_node_planner",
            "learning_resume_reason": "objective_quiz_passed",
            "pending_interaction_kind": "",
            "pending_interaction_prompt": "",
            "pending_interaction_options": [],
            "pending_interaction_recommended": "",
            "pending_interaction_answer": "",
            "node_quiz_kind": "",
            "current_node_status": "passed",
            "student_state_snapshot": updated_snapshot or state.get("student_state_snapshot") or {},
            "user_knowledge_graph": user_kg,
            "message_history": trim_message_history(message_history),
        }

    return node

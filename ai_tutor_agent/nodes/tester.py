from __future__ import annotations

import re

from langchain_core.messages import HumanMessage, SystemMessage

from ..core.events import make_event
from ..core.output_format import collapse_blank_lines, parse_json_object, split_sentences, stream_text_chunks
from ..core.ports import EventSink, RuntimeContext
from ..core.state import AgentState
from ..core.teacher_voice import build_teacher_voice
from ..core.text import content_to_text

ASK_PREFIXES = ("/ask", "问:", "问题:")
QUESTION_HINTS = (
    "为什么",
    "怎么",
    "如何",
    "请问",
    "是什么",
    "什么意思",
    "能不能",
    "可不可以",
    "请解释",
    "解释一下",
    "举个例子",
)
SKIP_COMMANDS = {"/skip", "/pass", "skip", "掌握", "已掌握", "跳过"}

QUESTION_TYPE_SPECS = {
    "concept_distinction": {
        "key": "concept_distinction",
        "label": "概念辨析题",
    },
    "scenario_judgment": {
        "key": "scenario_judgment",
        "label": "场景判断题",
    },
    "calculation_analysis": {
        "key": "calculation_analysis",
        "label": "计算分析题",
    },
}

QUESTION_TEMPLATE_SPECS = {
    "definition_distinction": {
        "key": "definition_distinction",
        "question_type": "concept_distinction",
        "label": "定义辨析",
        "goal": "确认学生能不能把核心定义、判断对象和易混概念边界说清楚。",
        "fallback_focus": "这题主要看你能不能把核心概念的定义和边界说稳。",
        "fallback_question": "请先说清题目里的核心概念，再指出它和一个容易混淆概念的关键区别，最后说明为什么不能把它们混在一起。",
        "fallback_hint": "先回答“它是什么”，再回答“它不是什么”，最后补一句二者差在哪。",
        "prompt_rules": (
            "题目必须围绕一个核心概念和一个易混概念展开，让学生先界定、再辨析。"
            "不要写成大而空的论述题，也不要同时追两个独立概念。"
        ),
    },
    "counterexample_distinction": {
        "key": "counterexample_distinction",
        "question_type": "concept_distinction",
        "label": "反例辨析",
        "goal": "确认学生能不能识别错误说法、反例或边界条件，而不是只会背正确定义。",
        "fallback_focus": "这题主要看你能不能识别一个说法为什么不成立，或者它为什么不属于这个概念。",
        "fallback_question": "请判断题目中的说法或例子是否成立；如果不成立，请指出它错在哪里，并给出更准确的表述。",
        "fallback_hint": "先判断“它算不算”，再指出不成立的关键原因。",
        "prompt_rules": (
            "题目必须给一个常见误区、错误说法或反例，让学生先判断，再指出错因。"
            "不要只让学生复述标准答案，要让他真正碰到边界。"
        ),
    },
    "engineering_scenario_judgment": {
        "key": "engineering_scenario_judgment",
        "question_type": "scenario_judgment",
        "label": "工程场景判断",
        "goal": "确认学生能不能把判断标准放回一个具体工程场景里使用。",
        "fallback_focus": "这题主要看你能不能把刚讲的判断标准放进具体场景里用出来。",
        "fallback_question": "请结合一个具体工程场景做出判断，并说明你是抓住了哪个关键信号或条件才这样判断的。",
        "fallback_hint": "先给判断，再回头说你是看到了哪个关键信号。",
        "prompt_rules": (
            "题目必须给一个具体、可信的工程场景，让学生做出一个明确判断并解释依据。"
            "不要只问定义，也不要变成开放式闲聊。"
        ),
    },
    "strategy_selection_judgment": {
        "key": "strategy_selection_judgment",
        "question_type": "scenario_judgment",
        "label": "方案选择判断",
        "goal": "确认学生能不能在多种可选方案里做出取舍，并说清权衡理由。",
        "fallback_focus": "这题主要看你能不能在两个或多个方案里做出选择，并说清为什么。",
        "fallback_question": "请根据题目场景在可选方案中做出选择，说明你优先考虑了什么，并补一句为什么另一种方案不更合适。",
        "fallback_hint": "先说你选哪个，再说你最看重的那个取舍条件。",
        "prompt_rules": (
            "题目必须包含至少两个候选方案或策略，让学生做选择并解释取舍。"
            "不要把选择条件藏起来，也不要出成只有唯一术语解释的题。"
        ),
    },
    "numeric_calculation_analysis": {
        "key": "numeric_calculation_analysis",
        "question_type": "calculation_analysis",
        "label": "带数值的计算分析",
        "goal": "确认学生能不能根据明确已知条件完成关键计算，并解释结果含义。",
        "fallback_focus": "这题主要看你能不能把已知数值、公式和关键步骤真正串起来。",
        "fallback_question": "请根据题目给出的数值条件，写出关键关系或公式，完成必要的计算，并给出最终结论。",
        "fallback_hint": "先列已知和公式，再一步一步算，不要跳到最后。",
        "prompt_rules": (
            "题目必须给出明确数值或参数，让学生完成一个主线清晰的计算或分析。"
            "不要把条件写残，也不要一次塞多个独立小问。"
        ),
    },
    "relation_derivation_analysis": {
        "key": "relation_derivation_analysis",
        "question_type": "calculation_analysis",
        "label": "关系推导分析",
        "goal": "确认学生能不能不靠具体数值，也把变量关系、趋势和推导主线说清楚。",
        "fallback_focus": "这题主要看你能不能把变量关系、变化趋势和推导主线说清楚。",
        "fallback_question": "请根据题目给出的条件，写出关键关系，分析各变量如何影响结果，并给出最终判断。",
        "fallback_hint": "先写关键关系，再说哪个量变大或变小时结果会怎么变。",
        "prompt_rules": (
            "题目可以不带具体数值，但必须有清晰的变量关系或推导主线。"
            "不要只问背公式，要让学生解释关系是怎么推出来或怎么用的。"
        ),
    },
}

_CONCEPT_BOUNDARY_HINTS = (
    "区别",
    "联系与区别",
    "混淆",
    "分不清",
    "辨析",
    "概念",
    "定义",
    "边界",
    "误区",
    "不成立",
    "不属于",
    "不要把",
    "不是",
    "分别",
    "各自",
)
_COUNTEREXAMPLE_HINTS = (
    "反例",
    "错误说法",
    "误区",
    "不属于",
    "不成立",
    "例外",
    "边界条件",
    "常见误解",
    "为什么错",
)
_QUANTITATIVE_HINTS = (
    "计算",
    "推导",
    "公式",
    "方程",
    "数值",
    "参数",
    "斜率",
    "概率",
    "矩阵",
    "积分",
    "导数",
    "误差",
    "频率",
    "增益",
    "阻尼",
    "超调",
    "响应时间",
    "传递函数",
    "pid",
    "采样",
    "电压",
    "电流",
)
_STRATEGY_SELECTION_HINTS = (
    "策略",
    "方案",
    "选型",
    "取舍",
    "优先",
    "更适合",
    "应该用哪个",
    "如何选择",
    "选择",
)
_BROAD_QUESTION_HINTS = (
    "谈谈",
    "说说",
    "聊聊",
    "简述",
    "论述",
    "展开说明",
    "自由发挥",
    "你的理解和感受",
    "你的看法",
)
_SCENARIO_CLUES = (
    "某",
    "一个",
    "系统",
    "接口",
    "场景",
    "项目",
    "设备",
    "扰动",
    "高并发",
    "请求",
    "工程",
    "控制器",
    "电路",
    "模块",
    "如果",
    "当",
)
_RELATION_CLUES = (
    "关系",
    "趋势",
    "影响",
    "随着",
    "增大",
    "减小",
    "变化",
    "如何影响",
    "怎样影响",
)
_MULTI_QUESTION_CONNECTORS = (
    "另外",
    "同时再",
    "再回答",
    "再补充",
    "并进一步",
    "并再",
    "然后再",
    "除此之外",
)


def _looks_like_interrupt_question(text: str) -> bool:
    cleaned = (text or "").strip()
    if not cleaned:
        return False

    lowered = cleaned.lower()
    if lowered in SKIP_COMMANDS:
        return False

    if lowered.startswith(ASK_PREFIXES):
        return True

    if any(mark in cleaned for mark in ["?", "？"]):
        return True

    if any(hint in cleaned for hint in QUESTION_HINTS):
        return True

    starts = ("这题", "这个", "那题", "这里", "此处", "它为啥", "为啥")
    if len(cleaned) <= 40 and cleaned.startswith(starts):
        return True

    return False


def _resolve_runtime_parts(
    runtime_or_event_sink: RuntimeContext | EventSink,
    answer_provider=None,
):
    if isinstance(runtime_or_event_sink, RuntimeContext):
        return runtime_or_event_sink.event_sink, runtime_or_event_sink.answer_provider
    return runtime_or_event_sink, answer_provider


def _clean_line(text: str) -> str:
    cleaned = re.sub(r"^[#>\-\d\.\)\s]+", "", (text or "").strip())
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip("：: ")


def _get_question_type_spec(question_type: str | None) -> dict:
    normalized = (question_type or "").strip()
    for spec in QUESTION_TYPE_SPECS.values():
        if normalized in {spec["key"], spec["label"]}:
            return spec
    return QUESTION_TYPE_SPECS["scenario_judgment"]


def _get_question_template_spec(question_template: str | None, *, question_type: str | None = None) -> dict:
    normalized = (question_template or "").strip()
    for spec in QUESTION_TEMPLATE_SPECS.values():
        if normalized in {spec["key"], spec["label"]}:
            return spec

    question_type_spec = _get_question_type_spec(question_type)
    fallback_map = {
        "concept_distinction": "definition_distinction",
        "scenario_judgment": "engineering_scenario_judgment",
        "calculation_analysis": "numeric_calculation_analysis",
    }
    return QUESTION_TEMPLATE_SPECS[fallback_map[question_type_spec["key"]]]


def _contains_any(text: str, patterns: tuple[str, ...]) -> bool:
    lowered = (text or "").lower()
    return any(pattern.lower() in lowered for pattern in patterns)


def _looks_boundary_issue(text: str) -> bool:
    return _contains_any(text, _CONCEPT_BOUNDARY_HINTS)


def _looks_quantitative_context(text: str) -> bool:
    lowered = (text or "").lower()
    if _contains_any(lowered, _QUANTITATIVE_HINTS):
        return True
    if re.search(r"\d+\s*[%xX*/+\-=]", lowered):
        return True
    if re.search(r"[=≈<>≤≥]\s*\d", lowered):
        return True
    return False


def _has_explicit_numeric_clues(text: str) -> bool:
    lowered = (text or "").lower()
    if re.search(r"\d", lowered):
        return True
    if re.search(r"[=≈<>≤≥/*+\-]", lowered):
        return True
    return False


def _select_question_type(state: AgentState) -> dict:
    difficulty_level = int(state.get("difficulty_level", 3) or 3)
    teaching_strategy = str(state.get("teaching_strategy", "") or "").strip()
    attempt_count = int(state.get("attempt_count", 0) or 0)

    misconceptions = " ".join(state.get("misconceptions", []) or [])
    next_review_points = " ".join(state.get("next_review_points", []) or [])
    context = "\n".join(
        [
            str(state.get("current_topic", "") or ""),
            str(state.get("tutor_content", "") or ""),
            str(state.get("coach_content", "") or ""),
            str(state.get("feedback", "") or ""),
            misconceptions,
            next_review_points,
            str(state.get("tester_question", "") or ""),
        ]
    )

    remedial = (
        bool((state.get("coach_content", "") or "").strip())
        or bool(misconceptions.strip())
        or bool(state.get("needs_hint"))
        or attempt_count > 0
    )
    boundary_issue = _looks_boundary_issue(
        "\n".join(
            [
                misconceptions,
                next_review_points,
                str(state.get("feedback", "") or ""),
                str(state.get("coach_content", "") or ""),
            ]
        )
    )
    quantitative = _looks_quantitative_context(context)

    if boundary_issue:
        spec = QUESTION_TYPE_SPECS["concept_distinction"]
        reason = "上一轮暴露的是概念边界或易混点，先用辨析题把核心定义拎清。"
    elif quantitative and (difficulty_level >= 4 or teaching_strategy == "stepbystep" or remedial):
        spec = QUESTION_TYPE_SPECS["calculation_analysis"]
        reason = "当前内容更依赖条件、公式或步骤衔接，适合用计算分析题看学生能不能真正推下来。"
    elif difficulty_level <= 2:
        spec = QUESTION_TYPE_SPECS["concept_distinction"]
        reason = "当前难度偏基础，先确认学生把核心概念和边界说稳更合适。"
    elif quantitative and difficulty_level >= 3:
        spec = QUESTION_TYPE_SPECS["calculation_analysis"]
        reason = "当前主题有明显的定量分析特征，中等以上难度时直接看步骤和结论更有效。"
    else:
        spec = QUESTION_TYPE_SPECS["scenario_judgment"]
        if remedial:
            reason = "上一轮主要需要把判断标准放回具体情境里再练一遍，场景判断题更贴近真实应用。"
        else:
            reason = "当前更适合用具体情境检验学生能不能把刚讲的判断标准真正用出来。"

    return {**spec, "reason": reason}


def _select_question_template(state: AgentState, question_type_spec: dict) -> dict:
    difficulty_level = int(state.get("difficulty_level", 3) or 3)
    attempt_count = int(state.get("attempt_count", 0) or 0)
    context = "\n".join(
        [
            str(state.get("current_topic", "") or ""),
            str(state.get("tutor_content", "") or ""),
            str(state.get("coach_content", "") or ""),
            str(state.get("feedback", "") or ""),
            " ".join(state.get("misconceptions", []) or []),
            " ".join(state.get("next_review_points", []) or []),
        ]
    )

    if question_type_spec["key"] == "concept_distinction":
        if _contains_any(context, _COUNTEREXAMPLE_HINTS) or (difficulty_level >= 4 and attempt_count > 0):
            template = QUESTION_TEMPLATE_SPECS["counterexample_distinction"]
            reason = "当前更适合让学生直接识别错误说法或反例，检查他是不是真懂边界。"
        else:
            template = QUESTION_TEMPLATE_SPECS["definition_distinction"]
            reason = "当前先把定义和易混概念边界说稳，比直接上反例更合适。"
        return {**template, "reason": reason}

    if question_type_spec["key"] == "scenario_judgment":
        if _contains_any(context, _STRATEGY_SELECTION_HINTS):
            template = QUESTION_TEMPLATE_SPECS["strategy_selection_judgment"]
            reason = "这轮更像方案取舍题，适合让学生在多个策略间做选择并说清权衡。"
        else:
            template = QUESTION_TEMPLATE_SPECS["engineering_scenario_judgment"]
            reason = "这轮更适合把判断标准放回具体工程场景里，看学生能不能真正落地。"
        return {**template, "reason": reason}

    if _has_explicit_numeric_clues(context):
        template = QUESTION_TEMPLATE_SPECS["numeric_calculation_analysis"]
        reason = "当前已有明确数值或公式线索，直接看学生能不能把计算主线走通。"
    else:
        template = QUESTION_TEMPLATE_SPECS["relation_derivation_analysis"]
        reason = "当前更适合检查变量关系和推导主线，而不是只做代数代入。"
    return {**template, "reason": reason}


def _question_identity_label(question_type_spec: dict, question_template_spec: dict) -> str:
    return f"{question_type_spec['label']} · {question_template_spec['label']}"


def _question_prompt_count(text: str) -> int:
    cleaned = collapse_blank_lines(text)
    if not cleaned:
        return 0

    count = cleaned.count("?") + cleaned.count("？")
    sentences = [segment.strip() for segment in re.split(r"[。；;\n]+", cleaned) if segment.strip()]
    if len(sentences) > 1:
        count += len(sentences) - 1
    return count


def _looks_like_multi_part_question(text: str) -> bool:
    cleaned = collapse_blank_lines(text)
    if not cleaned:
        return False
    if _question_prompt_count(cleaned) >= 2:
        return True
    return any(connector in cleaned for connector in _MULTI_QUESTION_CONNECTORS)


def _looks_too_broad_question(text: str, question_template_spec: dict) -> bool:
    cleaned = _clean_line(text)
    if not cleaned:
        return True
    if any(token in cleaned for token in _BROAD_QUESTION_HINTS):
        return True
    if len(cleaned) < 12:
        return True
    if question_template_spec["key"] in {"engineering_scenario_judgment", "strategy_selection_judgment"}:
        if "场景" in cleaned and len(cleaned) < 18:
            return True
    return False


def _template_has_required_context(question: str, question_template_spec: dict) -> bool:
    cleaned = collapse_blank_lines(question)
    template_key = question_template_spec["key"]

    if template_key == "definition_distinction":
        return _contains_any(cleaned, ("区别", "定义", "边界", "混淆", "不是", "联系"))
    if template_key == "counterexample_distinction":
        return _contains_any(cleaned, ("说法", "例子", "成立", "错误", "不属于", "为什么错", "误区"))
    if template_key == "engineering_scenario_judgment":
        return _contains_any(cleaned, _SCENARIO_CLUES)
    if template_key == "strategy_selection_judgment":
        return _contains_any(cleaned, ("还是", "或", "方案", "策略", "选择", "取舍"))
    if template_key == "numeric_calculation_analysis":
        return _has_explicit_numeric_clues(cleaned)
    return _contains_any(cleaned, _RELATION_CLUES)


def _requirements_are_too_generic(requirements: list[str]) -> bool:
    if not requirements:
        return True
    generic_count = 0
    for item in requirements:
        cleaned = _clean_line(item)
        if not cleaned:
            generic_count += 1
            continue
        if any(token in cleaned for token in ("自由发挥", "自行理解", "任意", "不限", "都可以")):
            generic_count += 1
    return generic_count > 0


def _question_guardrail_violations(question: str, requirements: list[str], question_template_spec: dict) -> list[str]:
    violations = []
    if _looks_like_multi_part_question(question):
        violations.append("double_prompt")
    if _looks_too_broad_question(question, question_template_spec):
        violations.append("too_broad")
    if not _template_has_required_context(question, question_template_spec):
        violations.append("missing_context")
    if _requirements_are_too_generic(requirements):
        violations.append("generic_requirements")
    return violations


def _apply_question_guardrails(
    payload: dict,
    *,
    difficulty_level: int,
    coach_content: str,
    question_template_spec: dict,
) -> tuple[dict, list[str]]:
    normalized_payload = dict(payload or {})
    focus = _clean_line(normalized_payload.get("focus", "")) or question_template_spec["fallback_focus"]
    question = _clean_line(normalized_payload.get("question", "")) or question_template_spec["fallback_question"]
    requirements = _normalize_requirements(
        normalized_payload.get("requirements", []),
        difficulty_level,
        question_template_spec["key"],
    )
    hint = _clean_line(normalized_payload.get("hint", "")) or question_template_spec["fallback_hint"]

    violations = _question_guardrail_violations(question, requirements, question_template_spec)
    if not violations:
        return {
            "focus": focus,
            "question": question,
            "requirements": requirements,
            "hint": hint,
        }, []

    fallback = _fallback_question_payload("", difficulty_level, coach_content, question_template_spec)
    return {
        "focus": fallback["focus"],
        "question": fallback["question"],
        "requirements": fallback["requirements"],
        "hint": hint or fallback["hint"],
    }, violations


def _default_requirements(difficulty_level: int, question_template: str) -> list[str]:
    if question_template == "definition_distinction":
        requirements = [
            "先直接说出你的判断或定义，不要只写模糊感觉。",
            "再点出它和容易混淆概念的关键区别，最好说清“为什么不能混在一起”。",
        ]
        if difficulty_level >= 4:
            requirements.append("最后补一句边界条件：在什么情况下这个判断最容易说错。")
        else:
            requirements.append("如果你一时拿不准，可以先回答“它是什么”，再回答“它不是什么”。")
        return requirements

    if question_template == "counterexample_distinction":
        requirements = [
            "先判断题目里的说法、例子或结论是否成立。",
            "再指出它错在哪里，或者它为什么不属于这个概念。",
        ]
        if difficulty_level >= 4:
            requirements.append("最后给出一个更准确的改写，顺手点明边界条件。")
        else:
            requirements.append("最后把正确说法补完整，不要只说“它不对”。")
        return requirements

    if question_template == "strategy_selection_judgment":
        requirements = [
            "先明确写出你选哪一种方案或策略。",
            "再说明你最看重的取舍条件是什么，以及它为什么更合适。",
        ]
        if difficulty_level >= 4:
            requirements.append("最后补一句为什么另一种常见方案在这里不是更优。")
        else:
            requirements.append("最后补一句你没有选另一种方案的主要原因。")
        return requirements

    if question_template == "engineering_scenario_judgment":
        requirements = [
            "先直接写出你的判断或结论，不要只写感觉。",
            "再说明你这样判断的依据，尽量点到对应概念、条件或关键信号。",
        ]
        if difficulty_level >= 4:
            requirements.append("如果有多种可能，请顺手说明为什么你排除了其他选择。")
        else:
            requirements.append("如果你不确定，可以先写最关键的一步判断。")
        return requirements

    if question_template == "numeric_calculation_analysis":
        requirements = [
            "先列出你准备用到的已知条件、关键关系或公式。",
            "再按顺序写出关键计算或分析步骤，不要只给最后答案。",
        ]
        if difficulty_level >= 4:
            requirements.append("最后给出结论，并说明这个结果在题目里代表什么。")
        else:
            requirements.append("最后写出结论，并简单说明你为什么这样判断。")
        return requirements

    requirements = [
        "先写出你准备用到的关键关系、判断式或推导起点。",
        "再按顺序说明各变量或条件是怎样影响结果的。",
    ]
    if difficulty_level >= 4:
        requirements.append("最后给出结论，并补一句这个关系在边界情况下会怎么变。")
    else:
        requirements.append("最后给出结论，并简单说明你为什么会得到这个趋势。")
    return requirements


def _normalize_requirements(value, difficulty_level: int, question_template: str) -> list[str]:
    if isinstance(value, list):
        candidates = value
    elif isinstance(value, str):
        candidates = re.split(r"[;\n。！？!?]", value)
    else:
        candidates = []

    requirements = [_clean_line(item) for item in candidates if _clean_line(item)]
    return requirements[:3] or _default_requirements(difficulty_level, question_template)


def _fallback_question_payload(raw_text: str, difficulty_level: int, coach_content: str, question_template_spec: dict) -> dict:
    cleaned = collapse_blank_lines(raw_text)
    paragraphs = [segment.strip() for segment in cleaned.split("\n\n") if segment.strip()]
    hint = ""
    for paragraph in paragraphs:
        if "思路提示" in paragraph or paragraph.startswith("💡") or "提示" in paragraph[:8]:
            hint = _clean_line(paragraph.replace("💡", "").replace("思路提示", ""))
            break

    question_parts = []
    for paragraph in paragraphs:
        normalized = _clean_line(paragraph)
        if not normalized:
            continue
        if "提示" in normalized[:8]:
            continue
        if normalized.startswith("现在这题考什么") or normalized.startswith("作答要求"):
            continue
        question_parts.append(normalized)

    question = " ".join(question_parts).strip()
    if not question:
        sentences = split_sentences(cleaned)
        question = " ".join(sentences[:2]).strip()
    if not question:
        question = question_template_spec["fallback_question"]

    focus = ""
    sentences = split_sentences(question)
    if sentences:
        focus = sentences[0]
    if not focus:
        focus = question_template_spec["fallback_focus"]

    if not hint and coach_content:
        hint = split_sentences(coach_content)[0] if split_sentences(coach_content) else coach_content.strip()
    if not hint:
        hint = question_template_spec["fallback_hint"]

    return {
        "focus": _clean_line(focus),
        "question": _clean_line(question),
        "requirements": _default_requirements(difficulty_level, question_template_spec["key"]),
        "hint": _clean_line(hint),
    }


def _format_question_markdown(
    payload: dict,
    difficulty_level: int,
    coach_content: str,
    question_type_spec: dict,
    question_template_spec: dict,
) -> str:
    normalized_payload = payload or {}
    focus = _clean_line(normalized_payload.get("focus", "")) or question_template_spec["fallback_focus"]
    question = _clean_line(normalized_payload.get("question", "")) or question_template_spec["fallback_question"]
    requirements = _normalize_requirements(
        normalized_payload.get("requirements", []),
        difficulty_level,
        question_template_spec["key"],
    )
    hint = _clean_line(normalized_payload.get("hint", "")) or _fallback_question_payload(
        "",
        difficulty_level,
        coach_content,
        question_template_spec,
    )["hint"]

    lines = [
        "### 这次题型",
        _question_identity_label(question_type_spec, question_template_spec),
        "",
        "### 现在这题考什么",
        focus,
        "",
        "### 题目",
        question,
        "",
        "### 作答要求",
    ]
    lines.extend([f"{index}. {item}" for index, item in enumerate(requirements[:3], start=1)])
    if hint:
        lines.extend(["", "### 如果你卡住了", f"💡 思路提示：{hint}"])
    return collapse_blank_lines("\n".join(lines))


def _ensure_question_markdown(
    stored_question: str,
    *,
    difficulty_level: int,
    coach_content: str,
    question_type_spec: dict,
    question_template_spec: dict,
) -> str:
    stripped = (stored_question or "").lstrip()
    if stripped.startswith("### "):
        if "### 这次题型" in stripped:
            return collapse_blank_lines(stored_question)
        return collapse_blank_lines(
            "\n".join(
                [
                    "### 这次题型",
                    _question_identity_label(question_type_spec, question_template_spec),
                    "",
                    stored_question,
                ]
            )
        )

    return _format_question_markdown(
        _fallback_question_payload(stored_question, difficulty_level, coach_content, question_template_spec),
        difficulty_level,
        coach_content,
        question_type_spec,
        question_template_spec,
    )


def build_tester_node(
    tester_llm,
    runtime_or_event_sink: RuntimeContext | EventSink,
    answer_provider=None,
):
    event_sink, answer_provider = _resolve_runtime_parts(runtime_or_event_sink, answer_provider)

    def tester_node(state: AgentState):
        event_sink.emit(
            make_event(
                "node.start",
                "tester",
                message="我来出一道贴着刚才讲解的题，看看你现在掌握到哪一步了。",
                data={"topic": state["current_topic"]},
            )
        )

        tutor_content = state.get("tutor_content", "")
        coach_content = state.get("coach_content", "").strip()
        difficulty_level = state.get("difficulty_level", 3)
        question_type_spec = _select_question_type(state)
        question_template_spec = _select_question_template(state, question_type_spec)
        question_type_label = question_type_spec["label"]
        question_template_label = question_template_spec["label"]
        question_identity_label = _question_identity_label(question_type_spec, question_template_spec)

        full_question = ""
        guardrail_repairs: list[str] = []
        if state.get("resume_tester") and state.get("tester_question"):
            stored_question = state.get("tester_question", "")
            if state.get("tester_question_type"):
                question_type_spec = _get_question_type_spec(state.get("tester_question_type"))
                question_type_label = question_type_spec["label"]
            if state.get("tester_question_template"):
                question_template_spec = _get_question_template_spec(
                    state.get("tester_question_template"),
                    question_type=question_type_spec["key"],
                )
                question_template_label = question_template_spec["label"]
            elif question_template_spec.get("question_type") != question_type_spec["key"]:
                question_template_spec = _get_question_template_spec(None, question_type=question_type_spec["key"])
                question_template_label = question_template_spec["label"]
            question_identity_label = _question_identity_label(question_type_spec, question_template_spec)
            full_question = _ensure_question_markdown(
                stored_question,
                difficulty_level=difficulty_level,
                coach_content=coach_content,
                question_type_spec=question_type_spec,
                question_template_spec=question_template_spec,
            )
            event_sink.emit(
                make_event(
                    "node.stream",
                    "tester",
                    data={"text": f"回到主线，请继续回答上一题：\n{full_question}"},
                )
            )
        else:
            system_msg = SystemMessage(
                content=build_teacher_voice(
                    """你现在负责出题，但题目必须规范、边界清楚、只考一个核心点。

出题要求：
1. 只能出一道题，不要同时问两个大问题
2. 题干必须完整，学生一眼能看懂“到底要答什么”
3. 作答要求要明确，不能让学生自己猜边界
4. 允许给一条很短的思路提示，但不能直接把答案泄露出去
5. 绝不输出客套话，也不要输出解析和答案

禁止项：
- 禁止双重追问，题干里只能有一条主线任务
- 禁止大而空的题干，例如“谈谈你的理解”“展开论述”
- 禁止条件不全，凡是场景题、选择题、计算题，都必须把判断或分析所需条件交代清楚"""
                )
            )

            if coach_content:
                human_content = (
                    f"这是教授刚才的教案：\n{tutor_content}\n\n"
                    f"补救教练刚给出的纠偏卡片：\n{coach_content}\n\n"
                    f"当前难度级别：{difficulty_level}\n"
                    f"本轮题型已确定：{question_type_label}\n"
                    f"本轮子模板已确定：{question_template_label}\n"
                    f"选择原因：{question_type_spec['reason']}\n"
                    f"子模板原因：{question_template_spec['reason']}\n"
                    f"题型目标：{question_template_spec['goal']}\n"
                    "请围绕学生刚才出错的点重新出一道题。\n"
                    f"你只能输出【{question_identity_label}】这一种题型，要求如下：{question_template_spec['prompt_rules']}\n"
                    "必须严格输出 JSON，不要输出 JSON 以外的内容：\n"
                    "{\n"
                    '  "focus": "一句话说明这题到底考什么",\n'
                    '  "question": "完整题干，不要编号，不要拆成多个大问",\n'
                    '  "requirements": ["要求1", "要求2", "要求3"],\n'
                    '  "hint": "可选，一句很短的思路提示"\n'
                    "}\n"
                    "题目边界必须清晰，让学生知道先答什么、再答什么。\n"
                    "禁止双重追问，禁止大而空题干，禁止条件不全。"
                )
            else:
                human_content = (
                    f"这是教授刚才的教案：\n{tutor_content}\n\n"
                    f"当前难度级别：{difficulty_level}\n"
                    f"本轮题型已确定：{question_type_label}\n"
                    f"本轮子模板已确定：{question_template_label}\n"
                    f"选择原因：{question_type_spec['reason']}\n"
                    f"子模板原因：{question_template_spec['reason']}\n"
                    f"题型目标：{question_template_spec['goal']}\n"
                    "请基于教案内容直接出题。\n"
                    f"你只能输出【{question_identity_label}】这一种题型，要求如下：{question_template_spec['prompt_rules']}\n"
                    "必须严格输出 JSON，不要输出 JSON 以外的内容：\n"
                    "{\n"
                    '  "focus": "一句话说明这题到底考什么",\n'
                    '  "question": "完整题干，不要编号，不要拆成多个大问",\n'
                    '  "requirements": ["要求1", "要求2", "要求3"],\n'
                    '  "hint": "可选，一句很短的思路提示"\n'
                    "}\n"
                    "题目边界必须清晰，让学生知道先答什么、再答什么。\n"
                    "禁止双重追问，禁止大而空题干，禁止条件不全。"
                )

            human_msg = HumanMessage(content=human_content)

            raw_question = ""
            for chunk in tester_llm.stream([system_msg, human_msg]):
                chunk_text = content_to_text(chunk.content)
                raw_question += chunk_text

            structured = parse_json_object(raw_question)
            if structured is None:
                structured = _fallback_question_payload(
                    raw_question,
                    difficulty_level,
                    coach_content,
                    question_template_spec,
                )
            structured, guardrail_repairs = _apply_question_guardrails(
                structured,
                difficulty_level=difficulty_level,
                coach_content=coach_content,
                question_template_spec=question_template_spec,
            )
            if guardrail_repairs:
                event_sink.emit(
                    make_event(
                        "session.warning",
                        "tester",
                        message="模型出的题我已经自动收紧了一次，避免出现双重追问、题干过空或条件不全。",
                        data={"guardrail_repairs": guardrail_repairs},
                    )
                )

            full_question = _format_question_markdown(
                structured,
                difficulty_level,
                coach_content,
                question_type_spec,
                question_template_spec,
            )
            stream_text_chunks(event_sink, "tester", full_question)

        event_sink.emit(
            make_event(
                "node.complete",
                "tester",
                message="题目已经整理好了，等你作答。",
                data={
                    "question": full_question,
                    "question_type": question_type_label,
                    "question_template": question_template_label,
                    "guardrail_repairs": guardrail_repairs,
                },
            )
        )

        user_input = answer_provider.get_answer(
            ">> 请输入你的解答（也可以先追问一个临时问题）: ",
            state={
                "current_topic": state["current_topic"],
                "tester_question": full_question,
                "tester_question_type": question_type_label,
                "tester_question_template": question_template_label,
                "student_id": state.get("student_id", "default"),
            },
        ).strip()

        event_sink.emit(
            make_event(
                "answer.received",
                "tester",
                message="我收到你的作答了，正在看你是卡在理解、步骤还是表达上。",
                data={"answer_length": len(user_input)},
            )
        )

        if _looks_like_interrupt_question(user_input):
            lowered = user_input.lower()
            if lowered.startswith(ASK_PREFIXES):
                if ":" in user_input:
                    interrupt_query = user_input.split(":", 1)[-1].strip()
                else:
                    interrupt_query = user_input[4:].strip()
            else:
                interrupt_query = user_input.strip()
            if not interrupt_query:
                interrupt_query = "请解释这道题涉及的关键知识点。"
            history = list(state.get("conversation_history", []))
            history.append(
                {"role": "user", "kind": "interruption_user", "content": interrupt_query}
            )
            return {
                "tester_question": full_question,
                "tester_question_type": question_type_label,
                "tester_question_template": question_template_label,
                "user_answer": "",
                "interrupt_query": interrupt_query,
                "resume_tester": True,
                "skip_reason": "",
                "conversation_history": history,
            }

        return {
            "tester_question": full_question,
            "tester_question_type": question_type_label,
            "tester_question_template": question_template_label,
            "user_answer": user_input,
            "coach_content": "",
            "resume_tester": False,
            "interrupt_query": "",
            "skip_reason": "",
        }

    return tester_node

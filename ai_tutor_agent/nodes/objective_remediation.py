from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from ..core.events import make_event
from ..core.learning_support import enrich_wrong_question_book
from ..core.output_format import parse_json_object
from ..core.ports import RuntimeContext
from ..core.state import AgentState
from ..core.text import content_to_text
from .objective_test import _answer_key, _normalize_options, _parse_answers, _question_id


def _option_text(options: Any, key: str) -> str:
    if isinstance(options, dict):
        return str(options.get(key) or options.get(key.upper()) or "").strip()
    return ""


def _string_list(values: Any) -> list[str]:
    if isinstance(values, list):
        return [str(item).strip() for item in values if str(item).strip()]
    if isinstance(values, tuple):
        return [str(item).strip() for item in values if str(item).strip()]
    text = str(values or "").strip()
    return [text] if text else []


def _infer_wrong_reason(wrong: dict[str, Any], explanation: str = "") -> str:
    explicit = str(wrong.get("wrong_reason") or wrong.get("error_type") or "").strip()
    if explicit:
        return explicit
    combined = " ".join(
        str(value or "")
        for value in [wrong.get("misconception"), wrong.get("target_objective"), explanation, wrong.get("explanation")]
    )
    if any(token in combined for token in ["公式", "代入", "计算", "推导"]):
        return "formula_misuse"
    if any(token in combined for token in ["条件", "前提", "适用", "忽略"]):
        return "condition_missing"
    if any(token in combined for token in ["前置", "基础", "先复习"]):
        return "graph_relation_gap"
    if any(token in combined for token in ["读错", "题干", "看成"]):
        return "reading_misread"
    return "concept_confusion"


def _recommended_review(wrong: dict[str, Any], state: AgentState) -> dict[str, Any]:
    node_id = str(wrong.get("node_id") or state.get("current_node_id") or state.get("graph_anchor_id") or "").strip()
    node_name = str(
        wrong.get("node_name")
        or state.get("current_node_name")
        or state.get("graph_anchor_title")
        or "当前节点"
    ).strip()
    target = str(wrong.get("target_objective") or "").strip()
    if not target:
        must_know = _string_list(state.get("graph_must_know"))
        target = must_know[0] if must_know else f"回看{node_name}的核心判断依据"
    prerequisites = _string_list(state.get("graph_prerequisites"))
    return {
        "node_id": node_id,
        "node_name": node_name,
        "target_objective": target,
        "suggestion": f"回看【{node_name}】中“{target}”这一点，再做 1 道同错因变式题。",
        "prerequisite_hint": prerequisites[0] if prerequisites else "",
    }


def _fallback_variant(wrong: dict[str, Any], index: int, node_id: str, state: AgentState | None = None) -> dict[str, Any]:
    state = state or {}
    qid = _question_id(wrong, index)
    answer_key = _answer_key(wrong) or "A"
    user_answer = str(wrong.get("user_answer") or "").strip().upper()
    options = wrong.get("options") or {}
    correct_text = _option_text(options, answer_key) or "正确理解反馈关系"
    user_text = _option_text(options, user_answer) or "常见错误判断"
    node_name = str(state.get("current_node_name") or state.get("graph_anchor_title") or wrong.get("node_name") or "当前节点").strip()
    must_know = [str(item).strip() for item in (state.get("graph_must_know") or []) if str(item).strip()]
    common_errors = [str(item).strip() for item in (state.get("graph_common_errors") or []) if str(item).strip()]
    concept = must_know[(index - 1) % len(must_know)] if must_know else correct_text
    misconception = common_errors[(index - 1) % len(common_errors)] if common_errors else user_text
    variant_options = {
        "A": f"比较给定量与反馈量后，让偏差信号朝减小方向作用：{concept}",
        "B": f"忽略比较点的合成关系，只按表面符号或元件名称下结论：{misconception}",
        "C": "把传感器测量值只当成记录数据，不参与控制器调整",
        "D": f"认为只要系统名称含有“{node_name}”，就不需要分析输入、输出和反馈通道",
    }
    variant_options[answer_key] = f"根据反馈量与给定量的比较结果调整执行环节，使偏差逐步减小：{concept}"
    return {
        "question_id": f"VAR-{qid}",
        "node_id": wrong.get("node_id") or node_id,
        "source_question_id": qid,
        "stem": f"某恒温箱把目标温度作为给定量，并用传感器持续测量箱内温度。若测得温度高于目标值，控制器应如何利用反馈信号调节加热功率？",
        "options": variant_options,
        "answer_key": answer_key,
        "explanation": f"题目换到恒温控制场景，但考查点仍是 {node_name} 中的反馈比较关系：{concept}。需要避免的误解是：{misconception}。",
        "source": "contextual_fallback_variant",
    }


def _build_variant_question_prompt(
    wrong_items: list[dict[str, Any]],
    state: AgentState,
    repair_rejections: list[dict[str, Any]] | None = None,
) -> list[object]:
    lines: list[str] = []
    for index, wrong in enumerate(wrong_items, start=1):
        qid = _question_id(wrong, index)
        options = wrong.get("options") or {}
        answer_key = _answer_key(wrong)
        user_answer = str(wrong.get("user_answer") or "").strip().upper()
        lines.append(
            "\n".join(
                [
                    f"题号：{qid}",
                    f"原题题干：{wrong.get('stem') or wrong.get('question') or ''}",
                    "原题选项：" + json.dumps(options, ensure_ascii=False),
                    f"用户选择：{user_answer}（{_option_text(options, user_answer)}）",
                    f"正确答案：{answer_key}（{_option_text(options, answer_key)}）",
                    f"原题解析：{wrong.get('explanation') or ''}",
                ]
            )
        )
    node_context = "\n".join(
        str(item).strip()
        for item in [
            state.get("current_node_name") or state.get("graph_anchor_title"),
            "；".join(str(x) for x in (state.get("graph_must_know") or [])),
            "；".join(str(x) for x in (state.get("graph_common_errors") or [])),
            state.get("node_content_context"),
        ]
        if str(item or "").strip()
    )[:4000]
    repair_note = ""
    if repair_rejections:
        repair_note = (
            "\n上一轮被拒绝的原因如下，请针对这些问题重新生成，不要重复被拒绝题目的题干或选项：\n"
            + json.dumps(repair_rejections, ensure_ascii=False)
            + "\n"
        )
    return [
        SystemMessage(content="你是严谨的自动控制课程命题老师。只输出合法 JSON，不要 Markdown。"),
        HumanMessage(
            content=(
                "请为每道错题生成 1 道新的四选一客观题，用于错题后的补救练习。\n"
                "依据：必须参考原题题干、原题选项、用户选择、正确答案和当前节点材料，找出用户误区；"
                "但题目不必机械复刻原题，可以重新设计应用场景，充分使用你的学科知识储备，让题目自然、具体、有教学价值。\n"
                "要求：1) 新题应考查同一核心辨析或相近迁移能力；2) 题干和选项必须像正常测验题，不能出现命题说明或教学策略；"
                "3) 不要把这些生成策略写进题干或选项，例如不要出现“变式验证”“换成另一个”“抓住关键关系”“在新情境中仍能判断”“沿用原错因”等元话语；"
                "4) 选项应是学生可见的自然答案，干扰项要对应真实常见误解；5) 每题必须给出 answer_key。\n"
                f"{repair_note}"
                f"当前节点材料：\n{node_context or '无'}\n\n"
                "错题列表：\n"
                + "\n---\n".join(lines)
                + "\n\n输出 JSON Schema：{\"questions\":[{\"question_id\":\"V-Q1\",\"source_question_id\":\"Q1\",\"stem\":\"...\",\"options\":{\"A\":\"...\",\"B\":\"...\",\"C\":\"...\",\"D\":\"...\"},\"answer_key\":\"A\",\"explanation\":\"...\"}]}"
            )
        ),
    ]


def _has_visible_variant_meta_text(question: dict[str, Any]) -> bool:
    text = " ".join([str(question.get("stem") or ""), *(str(v) for v in (question.get("options") or {}).values())])
    return any(token in text for token in ["变式验证", "换成另一个", "抓住关键关系", "在新情境中仍能判断", "沿用原错因"])


def _variant_quality_errors(question: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    stem = str(question.get("stem") or "").strip()
    options = question.get("options")
    answer_key = str(question.get("answer_key") or "").strip().upper()
    if not stem:
        errors.append("missing_stem")
    if not isinstance(options, dict) or set(options.keys()) != {"A", "B", "C", "D"} or any(
        not str(value or "").strip() for value in (options or {}).values()
    ):
        errors.append("invalid_options")
        option_values: list[str] = []
    else:
        option_values = [str(options[key] or "").strip() for key in ("A", "B", "C", "D")]
    if answer_key not in {"A", "B", "C", "D"} or (isinstance(options, dict) and answer_key not in options):
        errors.append("invalid_answer_key")
    if option_values and len(set(option_values)) < len(option_values):
        errors.append("duplicate_options")
    if any(len(value) > 95 for value in option_values):
        errors.append("option_too_long")
    if _has_visible_variant_meta_text(question):
        errors.append("visible_generation_meta_text")
    return errors


def _normalize_llm_variant_batch(
    raw_questions: list[Any],
    *,
    wrong_items: list[dict[str, Any]],
    node_id: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for index, item in enumerate(raw_questions, start=1):
        wrong = wrong_items[min(index - 1, len(wrong_items) - 1)] if wrong_items else {}
        source_question_id = _question_id(wrong, index)
        if not isinstance(item, dict):
            rejected.append(
                {
                    "index": index,
                    "source_question_id": source_question_id,
                    "question_id": f"V-{source_question_id}",
                    "errors": ["invalid_schema"],
                }
            )
            continue
        options = _normalize_options(item.get("options"))
        question = {
            "question_id": str(item.get("question_id") or f"V-{source_question_id}").strip(),
            "node_id": item.get("node_id") or node_id,
            "source_question_id": str(item.get("source_question_id") or source_question_id).strip(),
            "stem": str(item.get("stem") or item.get("question") or "").strip(),
            "options": options,
            "answer_key": str(item.get("answer_key") or item.get("answer") or item.get("correct_answer") or "").strip().upper(),
            "explanation": str(item.get("explanation") or item.get("analysis") or "").strip(),
            "source": "ai_generated_variant",
        }
        errors = _variant_quality_errors(question)
        if errors:
            rejected.append(
                {
                    "index": index,
                    "source_question_id": question["source_question_id"],
                    "question_id": question["question_id"],
                    "errors": errors,
                    "stem": question["stem"][:120],
                }
            )
            continue
        accepted.append(question)
    return accepted, rejected


def _generate_llm_variants(llm: Any, wrong_items: list[dict[str, Any]], state: AgentState, node_id: str) -> list[dict[str, Any]]:
    if llm is None or not wrong_items:
        return []
    try:
        response = llm.invoke(_build_variant_question_prompt(wrong_items, state))
    except Exception:
        return []
    parsed = parse_json_object(content_to_text(getattr(response, "content", response)))
    raw_questions = parsed.get("questions") if isinstance(parsed, dict) else None
    if not isinstance(raw_questions, list):
        return []
    questions, rejected = _normalize_llm_variant_batch(raw_questions, wrong_items=wrong_items, node_id=node_id)
    if rejected and len(questions) < len(wrong_items):
        accepted_sources = {str(question.get("source_question_id") or "").strip() for question in questions}
        remaining_wrong_items = [
            wrong
            for index, wrong in enumerate(wrong_items, start=1)
            if _question_id(wrong, index) not in accepted_sources
        ]
        try:
            repair_response = llm.invoke(
                _build_variant_question_prompt(remaining_wrong_items, state, repair_rejections=rejected)
            )
        except Exception:
            return questions
        repair_parsed = parse_json_object(content_to_text(getattr(repair_response, "content", repair_response)))
        repair_raw = repair_parsed.get("questions") if isinstance(repair_parsed, dict) else None
        if isinstance(repair_raw, list):
            repaired, _ = _normalize_llm_variant_batch(repair_raw, wrong_items=remaining_wrong_items, node_id=node_id)
            questions.extend(repaired)
    return questions


def _build_wrong_question_prompt(wrong_items: list[dict[str, Any]], state: AgentState) -> list[object]:
    lines = []
    for index, wrong in enumerate(wrong_items, start=1):
        qid = _question_id(wrong, index)
        options = wrong.get("options") or {}
        answer_key = _answer_key(wrong)
        user_answer = str(wrong.get("user_answer") or "").strip().upper()
        lines.append(
            "\n".join(
                [
                    f"题号：{qid}",
                    f"题干：{wrong.get('stem') or wrong.get('question') or ''}",
                    "选项：" + json.dumps(options, ensure_ascii=False),
                    f"用户选择：{user_answer}（{_option_text(options, user_answer)}）",
                    f"正确答案：{answer_key}（{_option_text(options, answer_key)}）",
                    f"原始解析：{wrong.get('explanation') or ''}",
                ]
            )
        )
    node_context = "\n".join(
        str(item).strip()
        for item in [
            state.get("current_node_name") or state.get("graph_anchor_title"),
            "；".join(str(x) for x in (state.get("graph_must_know") or [])),
            "；".join(str(x) for x in (state.get("graph_common_errors") or [])),
            state.get("node_content_context"),
        ]
        if str(item or "").strip()
    )[:3000]
    return [
        SystemMessage(content="你是严谨的错题订正老师。只输出合法 JSON，不要 Markdown。"),
        HumanMessage(
            content=(
                "请根据每道错题的题干、选项、用户选择、正确答案，生成面向学生的结构化订正讲解。\n"
                "要求：指出用户错在什么判断层，解释为什么正确答案成立，并说明用户所选项为什么不成立。\n"
                "请把讲解拆成 why_user_wrong（用户为什么错）、why_correct（正确答案为什么成立）、key_rule（下次判断依据）、review_action（下一步复习动作）。\n"
                "wrong_reason 只能从 concept_confusion/formula_misuse/condition_missing/calculation_error/graph_relation_gap/reading_misread 中选择。\n"
                f"当前节点上下文：\n{node_context or '无'}\n\n"
                "错题列表：\n"
                + "\n---\n".join(lines)
                + "\n\n输出 JSON Schema：{\"explanations\":[{\"question_id\":\"Q1\",\"wrong_reason\":\"concept_confusion\",\"target_objective\":\"...\",\"misconception\":\"...\",\"why_user_wrong\":\"...\",\"why_correct\":\"...\",\"key_rule\":\"...\",\"review_action\":\"...\",\"explanation\":\"...\",\"wrong_option_analysis\":{\"B\":\"用户所选项为什么错\"},\"recommended_review\":{\"suggestion\":\"建议回看...\"}}]}"
            )
        ),
    ]


def _generate_llm_explanations(llm: Any, wrong_items: list[dict[str, Any]], state: AgentState) -> dict[str, dict[str, Any]]:
    if llm is None or not wrong_items:
        return {}
    try:
        response = llm.invoke(_build_wrong_question_prompt(wrong_items, state))
    except Exception:
        return {}
    parsed = parse_json_object(content_to_text(getattr(response, "content", response)))
    result: dict[str, dict[str, Any]] = {}
    if isinstance(parsed, dict) and isinstance(parsed.get("explanations"), list):
        for item in parsed["explanations"]:
            if isinstance(item, dict):
                qid = str(item.get("question_id") or "").strip()
                explanation = str(item.get("explanation") or "").strip()
                if qid and explanation:
                    result[qid] = dict(item)
    return result


def build_wrong_question_explainer_node(runtime: RuntimeContext, llm: Any | None = None):
    event_sink = runtime.event_sink

    def node(state: AgentState) -> dict:
        wrong_items = list(state.get("node_quiz_wrong_items") or [])
        llm_explanations = _generate_llm_explanations(llm, wrong_items, state)
        explanations: list[dict[str, Any]] = []
        for index, wrong in enumerate(wrong_items, start=1):
            qid = _question_id(wrong, index)
            llm_item = dict(llm_explanations.get(qid) or {})
            explanation = str(
                llm_item.get("explanation")
                or wrong.get("explanation")
                or "这道题暴露了当前节点的概念边界问题：需要重新对照题干条件、用户选项和正确答案，分清本节点的判断依据。"
            ).strip()
            user_answer = str(wrong.get("user_answer") or "").strip().upper()
            answer_key = _answer_key(wrong)
            wrong_option_analysis = dict(wrong.get("wrong_option_analysis") or {})
            wrong_option_analysis.update(dict(llm_item.get("wrong_option_analysis") or {}))
            target_objective = str(llm_item.get("target_objective") or wrong.get("target_objective") or "").strip()
            misconception = str(llm_item.get("misconception") or wrong.get("misconception") or "").strip()
            wrong_reason = str(llm_item.get("wrong_reason") or _infer_wrong_reason({**wrong, "misconception": misconception}, explanation)).strip()
            recommended_review = _recommended_review({**wrong, "target_objective": target_objective}, state)
            if isinstance(llm_item.get("recommended_review"), dict):
                recommended_review = {**recommended_review, **dict(llm_item.get("recommended_review") or {})}
            why_user_wrong = str(
                llm_item.get("why_user_wrong")
                or wrong.get("why_user_wrong")
                or f"你选择 {user_answer or '这个答案'}，说明还没有把题干条件和本节点的关键判断依据对应起来。"
            ).strip()
            why_correct = str(
                llm_item.get("why_correct")
                or wrong.get("why_correct")
                or f"正确答案 {answer_key or '成立'} 更符合题干条件和当前节点的核心概念。"
            ).strip()
            key_rule = str(
                llm_item.get("key_rule")
                or wrong.get("key_rule")
                or f"先抓题干条件，再对照考察点：{target_objective or recommended_review.get('target_objective') or '当前节点核心判断依据'}。"
            ).strip()
            review_action = str(
                llm_item.get("review_action")
                or wrong.get("review_action")
                or recommended_review.get("suggestion")
                or "回看当前节点的核心概念，再完成 1 道同错因变式题。"
            ).strip()
            explanations.append(
                {
                    "question_id": qid,
                    "stem": wrong.get("stem") or "",
                    "user_answer": user_answer,
                    "answer_key": answer_key,
                    "target_objective": target_objective or recommended_review.get("target_objective", ""),
                    "misconception": misconception,
                    "wrong_reason": wrong_reason,
                    "why_user_wrong": why_user_wrong,
                    "why_correct": why_correct,
                    "key_rule": key_rule,
                    "review_action": review_action,
                    "explanation": explanation,
                    "wrong_option_analysis": wrong_option_analysis,
                    "recommended_review": recommended_review,
                    "review_state": "explained",
                    "next_action_type": "remediation_decision",
                    "locked": True,
                }
            )

        event_sink.emit(
            make_event(
                "node.complete",
                "wrong_question_explainer",
                message=f"已生成 {len(explanations)} 道错题的订正讲解。",
                data={
                    "wrong_count": len(wrong_items),
                    "explanations": explanations,
                    "review_state": "explained",
                    "next_resume_target": "remediation_decision",
                    "locked": True,
                },
            )
        )
        # 回写错题本富字段
        if explanations:
            enrich_wrong_question_book(
                getattr(runtime, "student_state_store", None),
                student_id=str(state.get("student_id") or "default_student").strip(),
                explanations=explanations,
            )
        explanation_lines = ["错题订正讲解"]
        for index, item in enumerate(explanations, start=1):
            qid = str(item.get("question_id") or f"Q{index}").strip()
            stem = str(item.get("stem") or "").strip()
            user_answer = str(item.get("user_answer") or "").strip().upper()
            answer_key = str(item.get("answer_key") or "").strip().upper()
            explanation = str(item.get("explanation") or "").strip()
            wrong_reason = str(item.get("wrong_reason") or "").strip()
            target_objective = str(item.get("target_objective") or "").strip()
            recommended_review = dict(item.get("recommended_review") or {})
            why_user_wrong = str(item.get("why_user_wrong") or "").strip()
            why_correct = str(item.get("why_correct") or "").strip()
            key_rule = str(item.get("key_rule") or "").strip()
            review_action = str(item.get("review_action") or recommended_review.get("suggestion") or "").strip()
            explanation_lines.extend(
                [
                    "",
                    f"{qid}. {stem}" if stem else f"{qid}.",
                    f"你的答案：{user_answer or '未作答'}；正确答案：{answer_key or '未提供'}",
                    f"错因类型：{wrong_reason}" if wrong_reason else "",
                    f"考察点：{target_objective}" if target_objective else "",
                    f"你错在：{why_user_wrong}" if why_user_wrong else "",
                    f"正确理解：{why_correct}" if why_correct else "",
                    f"判断依据：{key_rule}" if key_rule else "",
                    explanation or "这题需要回到题干中的关键条件，重新区分正确概念与误区。",
                    f"下一步：{review_action}" if review_action else "",
                ]
            )
        explanation_lines = [line for line in explanation_lines if line]
        message_history = list(state.get("message_history", []))
        message_history.append(
            {
                "role": "assistant",
                "kind": "wrong_question_explanations",
                "content": "\n".join(explanation_lines),
                "data": {"explanations": explanations, "review_state": "explained", "locked": True},
            }
        )
        return {
            "wrong_question_explanations": explanations,
            "message_history": message_history,
            "flow_status": "normal",
            "learning_phase": "node_quiz_remediation_explaining",
            "learning_resume_target": "remediation_decision",
            "learning_resume_reason": "wrong_questions_explained",
            "current_node_status": "quizzing",
        }

    return node


def build_variant_question_generator_node(runtime: RuntimeContext, llm: Any | None = None):
    event_sink = runtime.event_sink

    def node(state: AgentState) -> dict:
        wrong_items = list(state.get("node_quiz_wrong_items") or [])
        node_id = str(state.get("current_node_id") or state.get("graph_anchor_id") or "").strip()
        provider = getattr(runtime, "question_bank_provider", None)
        variant_questions: list[dict[str, Any]] = []
        if provider is not None and hasattr(provider, "get_variant_question"):
            for wrong in wrong_items:
                variant = provider.get_variant_question(wrong)
                if variant:
                    variant_questions.append(dict(variant))
        if not variant_questions:
            variant_questions = _generate_llm_variants(llm, wrong_items, state, node_id)
        if not variant_questions:
            variant_questions = [_fallback_variant(wrong, index, node_id, state) for index, wrong in enumerate(wrong_items, start=1)]

        prompt = "请完成错题对应的变式验证题。"
        event_sink.emit(
            make_event(
                "node.start",
                "variant_question_generator",
                message=prompt,
                data={"questions": variant_questions, "requires_input": True},
            )
        )
        return {
            "variant_questions": variant_questions,
            "node_quiz_items": variant_questions,
            "node_quiz_answers": {},
            "node_quiz_kind": "variant_test_answers",
            "flow_status": "awaiting_variant_answers",
            "learning_phase": "node_quiz_variant_testing",
            "learning_resume_target": "variant_test_answer_dialog",
            "learning_resume_reason": "variant_questions_generated",
            "pending_interaction_kind": "variant_test_answers",
            "pending_interaction_prompt": prompt,
            "pending_interaction_options": variant_questions,
            "pending_interaction_recommended": "",
            "pending_interaction_answer": "",
            "current_node_status": "quizzing",
        }

    return node


def build_variant_test_answer_dialog_node(runtime: RuntimeContext):
    event_sink = runtime.event_sink

    def node(state: AgentState) -> dict:
        variant_questions = list(state.get("variant_questions") or state.get("node_quiz_items") or [])
        pending_answer = state.get("pending_interaction_answer")
        if not pending_answer:
            prompt = "请提交变式验证题答案。"
            event_sink.emit(
                make_event(
                    "node.start",
                    "variant_test_answer_dialog",
                    message=prompt,
                    data={"questions": variant_questions, "requires_input": True},
                )
            )
            return {
                "flow_status": "awaiting_variant_answers",
                "learning_phase": "node_quiz_variant_testing",
                "learning_resume_target": "variant_test_answer_dialog",
                "learning_resume_reason": "awaiting_variant_answers",
                "pending_interaction_kind": "variant_test_answers",
                "pending_interaction_prompt": prompt,
                "pending_interaction_options": variant_questions,
                "pending_interaction_answer": "",
                "current_node_status": "quizzing",
            }

        answers = _parse_answers(pending_answer)
        event_sink.emit(
            make_event(
                "node.complete",
                "variant_test_answer_dialog",
                message="已收到变式验证题答案，将进入确定性评分。",
                data={"answer_count": len(answers)},
            )
        )
        return {
            "node_quiz_items": variant_questions,
            "node_quiz_answers": answers,
            "node_quiz_kind": "variant_test_answers",
            "message_history": list(state.get("message_history", [])),
            "flow_status": "normal",
            "learning_phase": "node_quiz_variant_scoring",
            "learning_resume_target": "objective_test_scorer",
            "learning_resume_reason": "variant_answers_collected",
            "pending_interaction_kind": "",
            "pending_interaction_prompt": "",
            "pending_interaction_options": [],
            "pending_interaction_recommended": "",
            "pending_interaction_answer": "",
            "current_node_status": "quizzing",
        }

    return node

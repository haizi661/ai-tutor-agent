from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from ..core.events import make_event
from ..core.output_format import parse_json_object
from ..core.ports import RuntimeContext
from ..core.state import AgentState
from ..core.text import content_to_text
from .objective_test import _answer_key, _parse_answers, _question_id, _quiz_review_history_entry


def _option_text(options: Any, key: str) -> str:
    if isinstance(options, dict):
        return str(options.get(key) or options.get(key.upper()) or "").strip()
    return ""


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


def _build_variant_question_prompt(wrong_items: list[dict[str, Any]], state: AgentState) -> list[object]:
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
    questions: list[dict[str, Any]] = []
    for index, item in enumerate(raw_questions, start=1):
        if not isinstance(item, dict):
            continue
        options = item.get("options")
        answer_key = str(item.get("answer_key") or "").strip().upper()
        stem = str(item.get("stem") or "").strip()
        if not stem or not isinstance(options, dict) or answer_key not in {"A", "B", "C", "D"} or answer_key not in options:
            continue
        question = {
            "question_id": str(item.get("question_id") or f"V-{_question_id(wrong_items[index - 1], index)}").strip(),
            "node_id": item.get("node_id") or node_id,
            "source_question_id": str(item.get("source_question_id") or _question_id(wrong_items[index - 1], index)).strip(),
            "stem": stem,
            "options": {key: str(options.get(key) or "").strip() for key in ["A", "B", "C", "D"] if str(options.get(key) or "").strip()},
            "answer_key": answer_key,
            "explanation": str(item.get("explanation") or "").strip(),
            "source": "ai_generated_variant",
        }
        if len(question["options"]) == 4 and not _has_visible_variant_meta_text(question):
            questions.append(question)
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
                "请根据每道错题的题干、选项、用户选择、正确答案，生成面向学生的订正讲解。\n"
                "要求：指出用户错在什么判断层，解释为什么正确答案成立，并说明用户所选项为什么不成立。\n"
                f"当前节点上下文：\n{node_context or '无'}\n\n"
                "错题列表：\n"
                + "\n---\n".join(lines)
                + "\n\n输出 JSON Schema：{\"explanations\":[{\"question_id\":\"Q1\",\"explanation\":\"...\"}]}"
            )
        ),
    ]


def _generate_llm_explanations(llm: Any, wrong_items: list[dict[str, Any]], state: AgentState) -> dict[str, str]:
    if llm is None or not wrong_items:
        return {}
    try:
        response = llm.invoke(_build_wrong_question_prompt(wrong_items, state))
    except Exception:
        return {}
    parsed = parse_json_object(content_to_text(getattr(response, "content", response)))
    result: dict[str, str] = {}
    if isinstance(parsed, dict) and isinstance(parsed.get("explanations"), list):
        for item in parsed["explanations"]:
            if isinstance(item, dict):
                qid = str(item.get("question_id") or "").strip()
                explanation = str(item.get("explanation") or "").strip()
                if qid and explanation:
                    result[qid] = explanation
    return result


def build_wrong_question_explainer_node(runtime: RuntimeContext, llm: Any | None = None):
    event_sink = runtime.event_sink

    def node(state: AgentState) -> dict:
        wrong_items = list(state.get("node_quiz_wrong_items") or [])
        llm_explanations = _generate_llm_explanations(llm, wrong_items, state)
        explanations: list[dict[str, Any]] = []
        for index, wrong in enumerate(wrong_items, start=1):
            qid = _question_id(wrong, index)
            explanation = str(
                llm_explanations.get(qid)
                or wrong.get("explanation")
                or "这道题暴露了当前节点的概念边界问题：需要重新对照题干条件、用户选项和正确答案，分清本节点的判断依据。"
            ).strip()
            user_answer = str(wrong.get("user_answer") or "").strip().upper()
            answer_key = _answer_key(wrong)
            explanations.append(
                {
                    "question_id": qid,
                    "stem": wrong.get("stem") or "",
                    "user_answer": user_answer,
                    "answer_key": answer_key,
                    "explanation": explanation,
                    "wrong_option_analysis": wrong.get("wrong_option_analysis") or {},
                }
            )

        event_sink.emit(
            make_event(
                "node.complete",
                "wrong_question_explainer",
                message=f"已生成 {len(explanations)} 道错题的订正讲解。",
                data={"wrong_count": len(wrong_items), "explanations": explanations},
            )
        )
        explanation_lines = ["错题订正讲解"]
        for index, item in enumerate(explanations, start=1):
            qid = str(item.get("question_id") or f"Q{index}").strip()
            stem = str(item.get("stem") or "").strip()
            user_answer = str(item.get("user_answer") or "").strip().upper()
            answer_key = str(item.get("answer_key") or "").strip().upper()
            explanation = str(item.get("explanation") or "").strip()
            explanation_lines.extend(
                [
                    "",
                    f"{qid}. {stem}" if stem else f"{qid}.",
                    f"你的答案：{user_answer or '未作答'}；正确答案：{answer_key or '未提供'}",
                    explanation or "这题需要回到题干中的关键条件，重新区分正确概念与误区。",
                ]
            )
        message_history = list(state.get("message_history", []))
        message_history.append(
            {
                "role": "assistant",
                "kind": "wrong_question_explanations",
                "content": "\n".join(explanation_lines),
                "data": {"explanations": explanations},
            }
        )
        return {
            "wrong_question_explanations": explanations,
            "message_history": message_history,
            "flow_status": "normal",
            "learning_phase": "node_quiz_remediation_explaining",
            "learning_resume_target": "variant_question_generator",
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
        message_history = list(state.get("message_history", []))
        score_total = len(variant_questions)
        correct = 0
        for index, item in enumerate(variant_questions, start=1):
            qid = _question_id(item, index)
            expected = _answer_key(item)
            user_answer = str(answers.get(qid) or answers.get(str(index)) or answers.get(f"Q{index}") or "").strip().upper()
            if expected and user_answer == expected:
                correct += 1
        score = int(round((correct / score_total) * 100)) if score_total else 0
        message_history.append(
            _quiz_review_history_entry(
                title="变式练习",
                kind="variant_test_answers",
                items=variant_questions,
                answers=answers,
                score=score,
                passed=correct == score_total if score_total else False,
            )
        )
        return {
            "node_quiz_items": variant_questions,
            "node_quiz_answers": answers,
            "message_history": message_history,
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

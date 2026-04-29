from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from ..core.events import make_event
from ..core.output_format import parse_json_object
from ..core.text import content_to_text
from ..core.learning_support import update_student_state_after_evaluation
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
        "stem": stem,
        "options": options,
        "answer_key": answer_key,
        "explanation": str(raw.get("explanation") or raw.get("analysis") or "").strip(),
        "wrong_option_analysis": raw.get("wrong_option_analysis") or {},
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


_PLACEHOLDER_TERMS = {
    "实例",
    "示例",
    "系统示例",
    "自动控制",
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


def _clip_text(value: str, *, limit: int = 82) -> str:
    text = " ".join(str(value or "").replace("\n", " ").split()).strip(" ；;。")
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip("，、；;。 ") + "…"


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
    if content:
        lines.append(f"节点讲解/检索内容摘要：\n{content}")
    return "\n".join(lines)


def _generate_ai_questions(llm: Any, state: AgentState, node_id: str, node_name: str, count: int) -> list[dict[str, Any]]:
    if llm is None:
        return []
    topic = str(state.get("current_topic") or state.get("turn_goal") or "").strip()
    node_context = _build_objective_generation_context(state, node_id, node_name)
    system_msg = SystemMessage(
        content=(
            "你是严谨的课程测评出题专家。请只输出合法 JSON，不要 Markdown。"
            "你生成的是节点学习后的客观选择题，不是学前自评题。"
            "题目必须紧扣当前节点字段，检验学习者是否理解本节点的具体概念、条件、因果关系和常见误区。"
        )
    )
    human_msg = HumanMessage(
        content=f"""请为当前知识图谱节点生成 {count} 道四选一客观题。
主题：{topic or '未指定'}
当前节点结构化字段：
{node_context or '无'}

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
      "explanation": "为什么正确答案成立，以及各干扰项对应的常见误区"
    }}
  ]
}}
""",
    )
    try:
        response = llm.invoke([system_msg, human_msg])
    except Exception:
        return []
    response_text = content_to_text(getattr(response, "content", response))
    parsed = parse_json_object(response_text)
    normalized: list[dict[str, Any]] = []
    for index, raw in enumerate(_extract_question_list(parsed), start=1):
        item = _normalize_question(raw, index, node_id)
        if item and not _looks_like_placeholder_question(item):
            normalized.append(item)
    return normalized[:count]


def _fallback_questions(node_id: str, node_name: str, k: int = 10, state: AgentState | None = None) -> list[dict[str, Any]]:
    state = state or {}
    title = node_name or node_id or "当前节点"
    objectives = [_clip_text(item, limit=72) for item in _string_list(state.get("graph_learning_objectives"))]
    must_know = [_clip_text(item, limit=76) for item in _string_list(state.get("graph_must_know"))]
    common_errors = [_clip_text(item, limit=76) for item in _string_list(state.get("graph_common_errors"))]
    content = str(state.get("node_content_context") or "").strip()
    content_sentences = [
        _clip_text(part, limit=76)
        for part in content.replace("；", "。").replace(";", "。").split("。")
        if _clip_text(part, limit=76)
    ]

    seeds = must_know or objectives or content_sentences or [f"识别{title}中的关键反馈关系"]
    objectives = objectives or [f"能依据材料判断{title}的组成关系"]
    common_errors = common_errors or ["只看外部动作，忽略测量反馈和比较环节"]
    context_a = content_sentences[0] if content_sentences else seeds[0]
    context_b = content_sentences[1] if len(content_sentences) > 1 else objectives[0]

    questions: list[dict[str, Any]] = []
    for i in range(1, k + 1):
        concept = seeds[(i - 1) % len(seeds)]
        objective = objectives[(i - 1) % len(objectives)]
        error_seed = common_errors[(i - 1) % len(common_errors)]
        correct_key = ("A", "B", "C", "D")[(i - 1) % 4]
        correct_text = _clip_text(f"{concept}，这是判断{title}是否成立的关键关系", limit=88)
        distractors = [
            _clip_text(f"只保留外部动作描述，忽略{error_seed}", limit=88),
            _clip_text(f"把目标任务说成{objective}，但没有说明{concept}", limit=88),
            _clip_text(f"把{context_b}当作唯一依据，遗漏{concept}这一判据", limit=88),
        ]
        option_keys = ["A", "B", "C", "D"]
        options: dict[str, str] = {}
        distractor_iter = iter(distractors)
        for key in option_keys:
            options[key] = correct_text if key == correct_key else next(distractor_iter)
        questions.append(
            {
                "question_id": f"AUTO-{node_id or 'NODE'}-{i}",
                "node_id": node_id,
                "stem": _clip_text(f"根据{title}的材料，下列哪项最准确体现“{concept}”？", limit=90),
                "options": options,
                "answer_key": correct_key,
                "explanation": _clip_text(f"正确项点明了{concept}。本题易错点是{error_seed}。材料依据：{context_a}", limit=150),
                "wrong_option_analysis": {
                    key: _clip_text(f"该项缺少或误用了“{concept}”这一判断条件。", limit=80)
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
) -> dict[str, Any]:
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
            "questions": items,
            "answers": answers,
            "score": score,
            "passed": passed,
        },
    }


def build_objective_test_generator_node(runtime: RuntimeContext, llm: Any | None = None, *, count: int = 10):
    event_sink = runtime.event_sink

    def node(state: AgentState) -> dict:
        node_id = str(state.get("current_node_id") or state.get("graph_anchor_id") or "").strip()
        node_name = str(state.get("current_node_name") or state.get("graph_anchor_title") or "").strip()
        provider = getattr(runtime, "question_bank_provider", None)
        questions: list[dict[str, Any]] = []
        if provider is not None and hasattr(provider, "get_objective_questions"):
            questions = list(provider.get_objective_questions(node_id, k=count) or [])
        if not questions:
            questions = _generate_ai_questions(llm, state, node_id, node_name, count)
        if not questions:
            questions = _fallback_questions(node_id, node_name, count, state)
        questions = questions[:count]

        prompt = f"请完成节点【{node_name or node_id}】的 {len(questions)} 道客观选择题。"
        event_sink.emit(
            make_event(
                "node.start",
                "objective_test_generator",
                message=prompt,
                data={"questions": questions, "requires_input": True},
            )
        )
        return {
            "node_quiz_items": questions,
            "node_quiz_answers": {},
            "node_quiz_wrong_items": [],
            "node_quiz_score": 0,
            "variant_questions": [],
            "flow_status": "awaiting_objective_answers",
            "learning_phase": "node_quiz_batch",
            "learning_resume_target": "objective_test_scorer",
            "learning_resume_reason": "objective_questions_generated",
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
        student_state = store.load(student_id)
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
        try:
            student_state.question_attempts = attempts[-200:]
        except Exception:
            return {}
        store.save(student_state)
        if hasattr(student_state, "to_dict"):
            return dict(student_state.to_dict() or {})
        return {}

    def node(state: AgentState) -> dict:
        items = list(state.get("node_quiz_items") or [])
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
        passed = score >= pass_score
        node_id = str(state.get("current_node_id") or state.get("graph_anchor_id") or "").strip()
        student_id = str(state.get("student_id") or "default_student").strip() or "default_student"
        updated_snapshot = update_student_state_after_evaluation(
            getattr(runtime, "student_state_store", None),
            student_id=student_id,
            node_id=node_id,
            score=score,
            passed=passed,
        )
        attempt_snapshot = _record_question_attempts(state, items, answers, score, passed)
        if attempt_snapshot:
            updated_snapshot = {**updated_snapshot, "question_attempts": attempt_snapshot.get("question_attempts", [])}

        event_sink.emit(
            make_event(
                "node.complete",
                "objective_test_scorer",
                message=f"本节点客观题得分 {score} 分，{'已通过' if passed else '需要订正后再验证'}。",
                data={"score": score, "passed": passed, "wrong_count": len(wrong_items)},
            )
        )
        quiz_kind = str(state.get("pending_interaction_kind") or "objective_test_answers").strip() or "objective_test_answers"
        review_title = "变式练习" if quiz_kind == "variant_test_answers" else "客观测评"
        message_history = list(state.get("message_history", []))
        message_history.append(
            _quiz_review_history_entry(
                title=review_title,
                kind=quiz_kind,
                items=items,
                answers=answers,
                score=score,
                passed=passed,
            )
        )
        if not passed:
            return {
                "node_quiz_answers": answers,
                "node_quiz_wrong_items": wrong_items,
                "node_quiz_score": score,
                "score": score,
                "feedback": f"本轮得分 {score}，未达到 {pass_score}，需要先订正错题并完成变式。",
                "wrong_question_explanations": [],
                "variant_questions": [],
                "flow_status": "normal",
                "learning_phase": "node_quiz_remediation",
                "learning_resume_target": "wrong_question_explainer",
                "learning_resume_reason": "objective_quiz_failed_needs_remediation",
                "pending_interaction_kind": "",
                "pending_interaction_prompt": "",
                "pending_interaction_options": [],
                "pending_interaction_answer": "",
                "current_node_status": "quizzing",
                "student_state_snapshot": updated_snapshot or state.get("student_state_snapshot") or {},
                "message_history": message_history,
            }

        return {
            "node_quiz_answers": answers,
            "node_quiz_wrong_items": wrong_items,
            "node_quiz_score": score,
            "score": score,
            "feedback": f"本轮得分 {score}，已达到 {pass_score}，可以进入下一节点决策。",
            "variant_questions": [],
            "flow_status": "normal",
            "learning_phase": "node_passed",
            "learning_resume_target": "next_node_planner",
            "learning_resume_reason": "objective_quiz_passed",
            "current_node_status": "passed",
            "student_state_snapshot": updated_snapshot or state.get("student_state_snapshot") or {},
            "message_history": message_history,
        }

    return node

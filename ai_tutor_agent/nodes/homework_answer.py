from __future__ import annotations

import html
import json
import re
from typing import Any

from ..core.events import make_event
from ..core.ports import RuntimeContext
from ..core.state import AgentState
from ..core.text import content_to_text


def _question_id(item: dict[str, Any], index: int) -> str:
    return str(item.get("question_id") or item.get("id") or f"HW-{index}").strip()


def _normalize_answer(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return str(value).strip()


def _parse_answers(raw: Any, homework_items: list[dict[str, Any]]) -> dict[str, str]:
    if isinstance(raw, dict):
        return {str(key).strip(): _normalize_answer(value) for key, value in raw.items() if str(key).strip()}
    text = _normalize_answer(raw)
    if not text:
        return {}
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return {str(key).strip(): _normalize_answer(value) for key, value in parsed.items() if str(key).strip()}
    except json.JSONDecodeError:
        pass

    answers: dict[str, str] = {}
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    id_set = {_question_id(item, index) for index, item in enumerate(homework_items, start=1)}
    for line in lines:
        match = re.match(r"^(?P<key>[A-Za-z0-9_\-]+|\d+)\s*[:：.)、]\s*(?P<value>.+)$", line)
        if not match:
            continue
        key = match.group("key").strip()
        value = match.group("value").strip()
        if key.isdigit():
            index = int(key) - 1
            if 0 <= index < len(homework_items):
                key = _question_id(homework_items[index], index + 1)
        if key in id_set and value:
            answers[key] = value
    if answers:
        return answers
    if len(homework_items) == 1:
        return {_question_id(homework_items[0], 1): text}
    return {}


def _format_answer_prompt(homework_items: list[dict[str, Any]]) -> str:
    lines = ["请提交上次作业答案。可以使用 JSON，也可以按题号逐行提交。"]
    for index, item in enumerate(homework_items, start=1):
        lines.append(f"{index}. [{_question_id(item, index)}] {item.get('prompt', '')}")
    return "\n".join(lines)


def _normalize_choice_answer(answer: Any) -> str:
    text = _normalize_answer(answer).strip().upper()
    if len(text) > 1:
        match = re.search(r"\b([A-D])\b", text)
        if match:
            return match.group(1)
    return text[:1]


def _rubric_terms(item: dict[str, Any]) -> list[str]:
    terms: list[str] = []
    for value in item.get("rubric") or []:
        term = str(value).strip()
        if term:
            terms.append(term)
    if terms:
        return terms
    reference = str(item.get("reference_answer") or "").strip()
    if not reference:
        return []
    tokens = re.findall(r"[\u4e00-\u9fffA-Za-z0-9]{2,}", reference)
    seen: list[str] = []
    for token in tokens:
        if token not in seen:
            seen.append(token)
    return seen[:8]


def _score_subjective(item: dict[str, Any], answer: str) -> dict[str, Any]:
    """Fallback keyword-based scoring when LLM is unavailable."""
    terms = _rubric_terms(item)
    if not terms:
        is_correct = bool(answer.strip())
        score = 100 if is_correct else 0
        matched: list[str] = []
    else:
        matched = [term for term in terms if term and term in answer]
        score = round(100 * len(matched) / len(terms)) if terms else 0
        is_correct = score >= 60
    missing = [term for term in terms if term not in matched]
    return {
        "score": score,
        "is_correct": is_correct,
        "matched_terms": matched,
        "missing_terms": missing,
        "expected": str(item.get("reference_answer") or "；".join(terms)).strip(),
        "feedback": "覆盖主要要点。" if is_correct else f"还缺少这些要点：{'；'.join(missing[:4]) or '答案不够完整'}。",
    }


_SCORING_SYSTEM_PROMPT = (
    "你是一位自动控制原理课程的作业批改助手。"
    "根据评分标准（rubric）和参考答案要点，对学生作答进行评分。"
    "只返回 JSON，不要解释。格式：\n"
    '{"score": 0-100整数, "is_correct": true/false, '
    '"matched_points": ["已覆盖的要点"], "missing_points": ["缺失的要点"], '
    '"feedback": "一句话批改意见"}'
)


def _llm_score_subjective(
    llm: Any,
    item: dict[str, Any],
    answer: str,
) -> dict[str, Any] | None:
    """Use LLM to score a subjective homework answer. Returns None on failure."""
    prompt_parts = [
        f"题目：{item.get('prompt', '')}",
        f"参考答案要点：{item.get('reference_answer', '')}",
    ]
    rubric = _string_list(item.get("rubric"))
    if rubric:
        prompt_parts.append(f"评分标准：{'；'.join(rubric)}")
    prompt_parts.append(f"学生作答：{answer}")
    user_prompt = "\n".join(prompt_parts)

    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        resp = llm.invoke([
            SystemMessage(content=_SCORING_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ])
        text = content_to_text(resp).strip()
        # Extract JSON from possible markdown fences
        json_match = re.search(r"\{[^{}]*\}", text)
        if not json_match:
            return None
        data = json.loads(json_match.group())
        score = int(data.get("score", 0))
        score = max(0, min(100, score))
        return {
            "score": score,
            "is_correct": bool(data.get("is_correct", score >= 60)),
            "matched_points": list(data.get("matched_points") or []),
            "missing_points": list(data.get("missing_points") or []),
            "expected": str(item.get("reference_answer") or "").strip(),
            "feedback": str(data.get("feedback") or "评分完成。").strip(),
            "scored_by": "llm",
        }
    except Exception:
        return None


def _score_item(item: dict[str, Any], answer: str, index: int, *, llm: Any = None) -> dict[str, Any]:
    qid = _question_id(item, index)
    answer_key = str(item.get("answer_key") or "").strip().upper()
    if answer_key:
        normalized = _normalize_choice_answer(answer)
        expected = answer_key[:1]
        is_correct = normalized == expected
        score = 100 if is_correct else 0
        feedback = "选择正确。" if is_correct else f"应选择 {expected}。"
        return {
            "question_id": qid,
            "node_id": item.get("node_id", ""),
            "type": "objective",
            "answer": normalized,
            "expected": expected,
            "score": score,
            "is_correct": is_correct,
            "feedback": feedback,
        }

    # Subjective: try LLM scoring first, fall back to keyword matching
    if llm is not None:
        llm_result = _llm_score_subjective(llm, item, answer)
        if llm_result is not None:
            return {
                "question_id": qid,
                "node_id": item.get("node_id", ""),
                "type": "subjective_review",
                "answer": answer,
                **llm_result,
            }

    subjective = _score_subjective(item, answer)
    return {
        "question_id": qid,
        "node_id": item.get("node_id", ""),
        "type": "subjective_review",
        "answer": answer,
        **subjective,
    }


def _persist_homework_result(runtime: RuntimeContext, state: AgentState, patch: dict[str, Any]) -> dict[str, Any]:
    store = getattr(runtime, "student_state_store", None)
    if store is None:
        return {}
    student_id = str(state.get("student_id") or "default_student").strip() or "default_student"
    if not (hasattr(store, "load") and hasattr(store, "save")):
        return {}
    student_state = store.load(student_id)
    if student_state is None:
        return {}
    if hasattr(student_state, "homework"):
        student_state.homework = []
    history = list(getattr(student_state, "homework_history", []) or [])
    history.append(
        {
            "items": patch["homework_items"],
            "answers": patch["homework_answers"],
            "score": patch["homework_score"],
            "results": patch["homework_results"],
        }
    )
    try:
        setattr(student_state, "homework_history", history)
    except Exception:
        pass
    # Blend homework scores into mastery (70% existing + 30% homework)
    # and update knowledge_graph per node (evidence recorded per-node via kg_update_score)
    for result in (patch.get("homework_results") or []):
        nid = str(result.get("node_id") or "").strip()
        if not nid:
            continue
        hw_score = float(result.get("score") or 0)
        old_mastery = float(student_state.mastery_scores.get(nid, 0))
        blended = round(0.7 * old_mastery + 0.3 * hw_score, 1)
        student_state.update_mastery(nid, blended)
        # Collect wrong homework items for knowledge_graph
        hw_wrong = []
        if not result.get("is_correct"):
            hw_wrong.append({
                "question_id": str(result.get("question_id") or ""),
                "stem": str(result.get("prompt") or "")[:200],
                "student_answer": str(result.get("answer") or ""),
                "correct_answer": str(result.get("expected") or ""),
                "feedback": str(result.get("feedback") or "")[:200],
            })
        student_state.kg_update_score(
            nid, int(round(hw_score)),
            passed=bool(result.get("is_correct")),
            wrong_items=hw_wrong or None,
            source="homework",
        )
    store.save(student_state)
    if hasattr(student_state, "to_dict"):
        return dict(student_state.to_dict() or {})
    return {}


def build_homework_answer_dialog_node(runtime: RuntimeContext):
    event_sink = runtime.event_sink
    answer_provider = runtime.answer_provider

    def node(state: AgentState) -> dict:
        homework_items = list(state.get("homework_items") or [])
        raw_answer = state.get("pending_interaction_answer")
        if not raw_answer:
            try:
                raw_answer = answer_provider.get_answer(
                    _format_answer_prompt(homework_items),
                    state={"interaction_kind": "homework_answers", "homework_items": homework_items},
                )
            except RuntimeError:
                raw_answer = ""
        answers = _parse_answers(raw_answer, homework_items)
        if not answers:
            prompt = _format_answer_prompt(homework_items)
            event_sink.emit(
                make_event(
                    "node.start",
                    "homework_answer_dialog",
                    message=prompt,
                    data={"homework_count": len(homework_items)},
                )
            )
            return {
                "flow_status": "awaiting_homework_answers",
                "homework_status": "in_progress",
                "learning_phase": "homework_answering",
                "learning_resume_target": "homework_answer_dialog",
                "learning_resume_reason": "homework_answers_required",
                "pending_interaction_kind": "homework_answers",
                "pending_interaction_prompt": prompt,
                "pending_interaction_options": [],
                "pending_interaction_recommended": "",
                "pending_interaction_answer": "",
            }

        event_sink.emit(make_event("node.complete", "homework_answer_dialog", message="已收到作业答案，开始评分。"))
        answer_content = _normalize_answer(raw_answer)
        return {
            "flow_status": "normal",
            "homework_status": "submitted",
            "homework_answers": answers,
            "learning_phase": "homework_scoring",
            "learning_resume_target": "homework_scorer",
            "learning_resume_reason": "homework_answers_collected",
            "pending_interaction_kind": "",
            "pending_interaction_prompt": "",
            "pending_interaction_options": [],
            "pending_interaction_recommended": "",
            "pending_interaction_answer": "",
            "message_history": list(state.get("message_history", []))[-199:]
            + [
                {
                    "role": "user",
                    "kind": "homework_answers",
                    "content": answer_content,
                    "data": {"answers": answers},
                }
            ],
        }

    return node


def build_homework_scorer_node(runtime: RuntimeContext, llm: Any = None):
    event_sink = runtime.event_sink

    def node(state: AgentState) -> dict:
        homework_items = list(state.get("homework_items") or [])
        homework_answers = dict(state.get("homework_answers") or {})
        results = [
            _score_item(item, homework_answers.get(_question_id(item, index), ""), index, llm=llm)
            for index, item in enumerate(homework_items, start=1)
        ]
        homework_score = round(sum(item["score"] for item in results) / len(results)) if results else 0
        patch = {
            "homework_items": homework_items,
            "homework_answers": homework_answers,
            "homework_results": results,
            "homework_score": homework_score,
        }
        snapshot = _persist_homework_result(runtime, state, patch) or dict(state.get("student_state_snapshot") or {})
        event_sink.emit(
            make_event(
                "node.complete",
                "homework_scorer",
                message=f"作业评分完成：{homework_score} 分。",
                data={"homework_score": homework_score, "wrong_count": len([item for item in results if not item.get("is_correct")])},
            )
        )
        return {
            **patch,
            "student_state_snapshot": snapshot,
            "homework_status": "scored",
            "flow_status": "normal",
            "learning_phase": "homework_explanation",
            "learning_resume_target": "homework_explainer",
            "learning_resume_reason": "homework_scored",
        }

    return node


def _html_escape(value: Any) -> str:
    return html.escape(str(value or "").strip())


def build_homework_feedback_html(results: list[dict[str, Any]], score: int) -> str:
    badge_tone = "good" if score >= 80 else "warn" if score >= 60 else "danger"
    cards: list[str] = []
    for index, item in enumerate(results, start=1):
        qid = _html_escape(item.get("question_id") or f"HW-{index}")
        status = "正确" if item.get("is_correct") else "需要修正"
        feedback = _html_escape(item.get("feedback"))
        expected = _html_escape(item.get("expected"))
        answer = _html_escape(item.get("answer"))
        expected_html = f'<div class="homework-reference"><strong>参考要点：</strong>{expected}</div>' if expected and not item.get("is_correct") else ""
        answer_html = f'<div class="homework-answer-line"><strong>你的答案：</strong>{answer}</div>' if answer else ""
        cards.append(
            f'<article class="homework-result-card" data-result="{"correct" if item.get("is_correct") else "wrong"}">'
            f'<div class="homework-item-meta"><span class="homework-item-index">{index}</span><span class="homework-item-id">{qid}</span><span>{status}</span></div>'
            '<div class="homework-answer-viewport">'
            f'{answer_html}'
            f'<div class="homework-feedback-text">{feedback}</div>'
            f'{expected_html}'
            '</div>'
            '</article>'
        )
    return (
        '<div class="learning-answer-content homework-answer-content">'
        '<section class="homework-feedback-card">'
        '<div class="learning-block-header">'
        '<div class="learning-block-title">作业讲解</div>'
        f'<div class="homework-score-badge homework-score-badge--{badge_tone}">本次得分：{score} 分</div>'
        '</div>'
        '<div class="homework-item-list">'
        + "".join(cards)
        + '</div></section></div>'
    )


def _format_explanation(results: list[dict[str, Any]], score: int) -> str:
    lines = [f"### 作业讲解\n本次作业得分：{score} 分。"]
    for item in results:
        qid = item.get("question_id", "")
        status = "正确" if item.get("is_correct") else "需要修正"
        lines.append(f"- {qid}：{status}。{item.get('feedback', '')}")
        expected = str(item.get("expected") or "").strip()
        if expected and not item.get("is_correct"):
            lines.append(f"  参考要点：{expected}")
    return "\n".join(lines)


def _llm_explain_homework(llm: Any, results: list[dict[str, Any]], state: AgentState) -> str:
    """Generate LLM deep explanations for wrong homework answers."""
    wrong = [r for r in results if not r.get("is_correct")]
    if not wrong or llm is None:
        return ""
    topic = str(state.get("current_topic") or "").strip()
    items_text = ""
    for i, r in enumerate(wrong, 1):
        prompt_text = str(r.get("prompt") or r.get("question") or "").strip()
        answer_text = str(r.get("answer") or "").strip()
        expected_text = str(r.get("expected") or "").strip()
        feedback_text = str(r.get("feedback") or "").strip()
        items_text += (
            f"\n题目{i}: {prompt_text}\n"
            f"学生答案: {answer_text}\n"
            f"参考要点: {expected_text}\n"
            f"初步反馈: {feedback_text}\n"
        )
    system_prompt = (
        "你是一位自动控制理论的辅导老师。学生完成了作业，以下是他答错的题目。"
        "请针对每道错题给出深度讲解，包括：\n"
        "1. 错误根源分析（概念误解还是计算失误）\n"
        "2. 正确的解题思路（分步骤）\n"
        "3. 相关知识点的简要回顾\n"
        "4. 避免类似错误的建议\n\n"
        "用中文回答，语言简洁清晰，适合学生阅读。"
        "直接输出讲解内容，不要重复题目本身。"
    )
    if topic:
        system_prompt += f"\n当前学习主题：{topic}"
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        messages = [SystemMessage(content=system_prompt), HumanMessage(content=items_text.strip())]
        response = llm.invoke(messages)
        return content_to_text(getattr(response, "content", response)).strip()
    except Exception:
        return ""


def build_homework_explainer_node(runtime: RuntimeContext, llm: Any = None):
    event_sink = runtime.event_sink

    def node(state: AgentState) -> dict:
        results = list(state.get("homework_results") or [])
        score = int(state.get("homework_score") or 0)
        tutor_content = build_homework_feedback_html(results, score)
        # LLM deep explanation for wrong answers
        llm_explanation = _llm_explain_homework(llm, results, state)
        if llm_explanation:
            escaped = _html_escape(llm_explanation).replace("\n", "<br>")
            tutor_content += (
                '<section class="homework-llm-explanation">'
                '<h3>📖 深度讲解</h3>'
                f'<div class="homework-explanation-body">{escaped}</div>'
                '</section>'
            )
        event_sink.emit(
            make_event(
                "node.complete",
                "homework_explainer",
                message="作业讲解完成，作业已归档。",
                data={"homework_score": score, "has_llm_explanation": bool(llm_explanation)},
            )
        )
        return {
            "tutor_content": tutor_content,
            "homework_status": "completed",
            "homework_items": [],
            "homework_answers": {},
            "flow_status": "normal",
            "learning_phase": "homework_completed",
            "learning_resume_target": "session_resume_router",
            "learning_resume_reason": "homework_completed",
            "pending_interaction_kind": "",
            "pending_interaction_prompt": "",
            "pending_interaction_options": [],
            "pending_interaction_recommended": "",
            "pending_interaction_answer": "",
        }

    return node

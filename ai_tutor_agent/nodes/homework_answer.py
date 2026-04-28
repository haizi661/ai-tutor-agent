from __future__ import annotations

import json
import re
from typing import Any

from ..core.events import make_event
from ..core.ports import RuntimeContext
from ..core.state import AgentState


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


def _score_item(item: dict[str, Any], answer: str, index: int) -> dict[str, Any]:
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
    if hasattr(store, "record_homework_result"):
        result = store.record_homework_result(
            student_id,
            homework_items=patch["homework_items"],
            homework_answers=patch["homework_answers"],
            homework_score=patch["homework_score"],
            homework_results=patch["homework_results"],
        )
        return dict(result or {})
    if hasattr(store, "load") and hasattr(store, "save"):
        student_state = store.load(student_id)
        if student_state is not None:
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
        }

    return node


def build_homework_scorer_node(runtime: RuntimeContext):
    event_sink = runtime.event_sink

    def node(state: AgentState) -> dict:
        homework_items = list(state.get("homework_items") or [])
        homework_answers = dict(state.get("homework_answers") or {})
        results = [
            _score_item(item, homework_answers.get(_question_id(item, index), ""), index)
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


def build_homework_explainer_node(runtime: RuntimeContext):
    event_sink = runtime.event_sink

    def node(state: AgentState) -> dict:
        results = list(state.get("homework_results") or [])
        score = int(state.get("homework_score") or 0)
        tutor_content = _format_explanation(results, score)
        event_sink.emit(
            make_event(
                "node.complete",
                "homework_explainer",
                message="作业讲解完成，作业已归档。",
                data={"homework_score": score},
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

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from ..core.events import make_event
from ..core.learning_support import update_student_state_after_evaluation
from ..core.ports import EventSink, RuntimeContext
from ..core.state import AgentState
from ..core.teacher_voice import build_teacher_voice
from ..core.text import content_to_text


_LOW_CONFIDENCE_PATTERNS = ("我不会", "不会", "不知道", "不清楚", "没思路", "不会做", "不懂")


class EvaluationResult(BaseModel):
    total_score: int = Field(default=60)
    logic_score: int = Field(default=60)
    concept_score: int = Field(default=60)
    is_correct_direction: bool = Field(default=False)
    misconceptions: list[str] = Field(default_factory=list)
    rubric_feedback: list[str] = Field(default_factory=list)
    model_answer: str = Field(default="")
    encouragement: str = Field(default="")
    next_review_points: list[str] = Field(default_factory=list)
    needs_hint: bool = Field(default=False)


def _resolve_runtime_parts(
    runtime_or_event_sink: RuntimeContext | EventSink,
    configured_pass_score: int | None = None,
) -> tuple[EventSink, int, object | None]:
    if isinstance(runtime_or_event_sink, RuntimeContext):
        runtime = runtime_or_event_sink
        runtime_settings = getattr(runtime, "settings", None)
        resolved_pass_score = configured_pass_score or (
            runtime_settings.pass_score if runtime_settings is not None else None
        )
        return runtime.event_sink, resolved_pass_score or 80, getattr(runtime, "student_state_store", None)

    return runtime_or_event_sink, configured_pass_score or 80, None


def _should_cap_score(user_answer: str) -> bool:
    normalized = (user_answer or "").strip()
    return any(token in normalized for token in _LOW_CONFIDENCE_PATTERNS)


def _fallback_encouragement(
    *,
    total_score: int,
    is_correct_direction: bool,
    misconceptions: list[str],
    next_review_points: list[str],
    needs_hint: bool,
) -> str:
    focus = misconceptions[0] if misconceptions else ""
    review = next_review_points[0] if next_review_points else ""

    if total_score >= 80:
        if review:
            return f"你的主线已经答对了，说明核心判断是稳的。接下来只要把「{review}」再说得更完整一点，这道题就会更漂亮。"
        return "你的主线已经答对了，说明核心判断是稳的。接下来只要把关键概念之间的关系说得更完整一点，就很扎实。"

    if is_correct_direction:
        if focus:
            return f"你的方向基本是对的，现在主要卡在「{focus}」这里。先把这一处单独拎清，再回头看整题，答案会顺很多。"
        return "你的方向基本是对的，只是中间有一个关键判断还没落稳。先把那一步单独想清，再回头串整题会更顺。"

    if needs_hint and review:
        return f"这一步先别急着全推出来，先抓住「{review}」这个支点。把它想顺以后，你会更容易把后面的判断接起来。"

    if focus:
        return f"这次还没有抓到题目的主线，最先要补的是「{focus}」。先把这个点稳住，我们再往下推。"
    return "这次还没有抓到题目的主线，不过没关系，我们先把最关键的一步稳住，再继续往下推。"


def _manual_eval(llm, system_msg, human_msg, event_sink: EventSink):
    prompt = (
        f"{system_msg.content}\n\n"
        "请强制以 JSON 格式输出结果，字段必须包含："
        "total_score, logic_score, concept_score, is_correct_direction, misconceptions, "
        "rubric_feedback, model_answer, encouragement, next_review_points, needs_hint。\n\n"
        f"{human_msg.content}"
    )
    response = llm.invoke(prompt)
    full_evaluation = content_to_text(getattr(response, "content", response)).strip()

    try:
        if "```json" in full_evaluation:
            full_evaluation = full_evaluation.split("```json", 1)[1].split("```", 1)[0].strip()
        elif "```" in full_evaluation:
            full_evaluation = full_evaluation.split("```", 1)[1].split("```", 1)[0].strip()

        result = json.loads(full_evaluation)
        return EvaluationResult(
            total_score=int(result.get("total_score", 60)),
            logic_score=int(result.get("logic_score", 60)),
            concept_score=int(result.get("concept_score", 60)),
            is_correct_direction=bool(result.get("is_correct_direction", False)),
            misconceptions=list(result.get("misconceptions", [])),
            rubric_feedback=list(result.get("rubric_feedback", [])),
            model_answer=str(result.get("model_answer", "")),
            encouragement=str(result.get("encouragement", result.get("feedback", "解析成功但内容缺失。"))),
            next_review_points=list(result.get("next_review_points", [])),
            needs_hint=bool(result.get("needs_hint", False)),
        )
    except Exception:
        event_sink.emit(make_event("session.warning", "evaluator", message="JSON 解析失败，使用默认评分。"))
        return EvaluationResult(encouragement="系统解析失败，请检查模型输出。")


def build_evaluator_node(
    evaluator_llm,
    runtime_or_event_sink: RuntimeContext | EventSink,
    pass_score: int | None = None,
):
    event_sink, resolved_pass_score, student_state_store = _resolve_runtime_parts(runtime_or_event_sink, pass_score)

    structured_llm = None
    if hasattr(evaluator_llm, "with_structured_output"):
        try:
            structured_llm = evaluator_llm.with_structured_output(EvaluationResult)
        except Exception:
            structured_llm = None

    def evaluator_node(state: AgentState):
        topic = state["current_topic"]
        question = state["tester_question"]
        user_answer = state["user_answer"]
        graph_learning_objectives = [str(item).strip() for item in (state.get("graph_learning_objectives") or []) if str(item).strip()]
        graph_common_errors = [str(item).strip() for item in (state.get("graph_common_errors") or []) if str(item).strip()]
        graph_must_know = [str(item).strip() for item in (state.get("graph_must_know") or []) if str(item).strip()]

        event_sink.emit(
            make_event(
                "node.start",
                "evaluator",
                message="我来帮你对一遍这道题，看看已经想对了多少。",
                data={"topic": topic},
            )
        )

        system_msg = SystemMessage(
            content=build_teacher_voice(
                """你现在负责阅卷，但不能只有“判对错”的机器感。

请评估学生作答，并输出总分、逻辑分、概念分、误区、下一步复习点、参考答案，以及是否需要先给提示再重试。

其中 `encouragement` 字段必须满足：
1. 先指出学生已经做对的一点，或者至少方向上没偏的地方
2. 再点出最关键的缺口，不要泛泛而谈
3. 最后给一个下一步动作，让学生知道接下来该补哪一步
4. 控制在 2~4 句，像老师批完题后当面给反馈，而不是系统公告"""
            )
        )
        human_msg = HumanMessage(
            content=(
                f"当前考核主题：{topic}\n"
                f"测试题：{question}\n"
                f"学生作答：{user_answer}\n"
                f"该节点学习目标：{'；'.join(graph_learning_objectives) if graph_learning_objectives else '未提供'}\n"
                f"该节点必会点：{'；'.join(graph_must_know) if graph_must_know else '未提供'}\n"
                f"该节点常见误区：{'；'.join(graph_common_errors) if graph_common_errors else '未提供'}\n"
                "请严格基于作答内容进行评估。"
            )
        )

        if structured_llm is not None:
            try:
                result = structured_llm.invoke([system_msg, human_msg])
            except Exception:
                result = _manual_eval(evaluator_llm, system_msg, human_msg, event_sink)
        else:
            result = _manual_eval(evaluator_llm, system_msg, human_msg, event_sink)

        total_score = int(getattr(result, "total_score", 60))
        logic_score = int(getattr(result, "logic_score", 60))
        concept_score = int(getattr(result, "concept_score", 60))
        is_correct_direction = bool(getattr(result, "is_correct_direction", False))
        misconceptions = list(getattr(result, "misconceptions", []) or [])
        rubric_feedback = list(getattr(result, "rubric_feedback", []) or [])
        model_answer = str(getattr(result, "model_answer", "") or "")
        encouragement = str(getattr(result, "encouragement", "") or "")
        next_review_points = list(getattr(result, "next_review_points", []) or [])
        needs_hint = bool(getattr(result, "needs_hint", False))

        if not next_review_points and graph_learning_objectives:
            next_review_points = graph_learning_objectives[:2]
        if not rubric_feedback and graph_common_errors:
            rubric_feedback = [f"图谱误区参考：{graph_common_errors[0]}"]

        if _should_cap_score(user_answer):
            total_score = min(total_score, 35)
        if not encouragement.strip():
            encouragement = _fallback_encouragement(
                total_score=total_score,
                is_correct_direction=is_correct_direction,
                misconceptions=misconceptions,
                next_review_points=next_review_points,
                needs_hint=needs_hint,
            )

        event_sink.emit(
            make_event(
                "node.stream",
                "evaluator",
                data={
                    "text": encouragement or "我先把这道题的关键判断点和你当前的落点整理一下。",
                },
            )
        )

        event_sink.emit(
            make_event(
                "assessment.result",
                "evaluator",
                data={
                    "total_score": total_score,
                    "logic_score": logic_score,
                    "concept_score": concept_score,
                    "feedback": encouragement,
                    "rubric_feedback": rubric_feedback,
                    "model_answer": model_answer,
                    "misconceptions": misconceptions,
                    "next_review_points": next_review_points,
                    "is_correct_direction": is_correct_direction,
                    "needs_hint": needs_hint,
                },
            )
        )

        event_sink.emit(make_event("node.complete", "evaluator", message="这轮评估已经整理好了。"))

        score_history = list(state.get("score_history", []))
        score_history.append((total_score, logic_score, concept_score, encouragement))

        passed = (
            total_score >= resolved_pass_score
            and logic_score >= 55
            and concept_score >= 55
        )
        attempt_count = 0 if passed else state.get("attempt_count", 0) + 1
        current_node_id = str(state.get("current_node_id") or state.get("graph_anchor_id") or "").strip()
        student_id = str(state.get("student_id") or "default_student").strip() or "default_student"
        student_state_snapshot = dict(state.get("student_state_snapshot") or {})
        updated_snapshot = update_student_state_after_evaluation(
            student_state_store,
            student_id=student_id,
            node_id=current_node_id,
            score=max(0.0, min(float(total_score) / 100.0, 1.0)),
            passed=passed,
        )
        if updated_snapshot:
            student_state_snapshot = updated_snapshot

        return {
            "score": total_score,
            "logic_score": logic_score,
            "concept_score": concept_score,
            "feedback": encouragement,
            "rubric_feedback": rubric_feedback,
            "model_answer": model_answer,
            "misconceptions": misconceptions,
            "next_review_points": next_review_points,
            "is_correct_direction": is_correct_direction,
            "needs_hint": needs_hint,
            "attempt_count": attempt_count,
            "score_history": score_history,
            "current_node_status": "passed" if passed else "quizzing",
            "student_state_snapshot": student_state_snapshot,
            "learning_phase": "node_passed" if passed else "node_quiz_remediation",
            "learning_resume_target": "post_eval_selector" if passed else "tester",
            "learning_resume_reason": "evaluation_passed" if passed else "evaluation_retry",
        }

    return evaluator_node

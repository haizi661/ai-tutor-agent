from __future__ import annotations

from typing import Any

from ..core.events import make_event
from ..core.ports import AnswerProvider, EventSink
from ..core.state import AgentState

# ── 硬界限 ──────────────────────────────────────────────
MAX_VARIANT_ROUNDS_PER_NODE = 2
MAX_SAME_OBJECTIVE_FAILURES = 2
MAX_EXTRA_REMEDIATION_QUESTIONS = 10

# ── 选项 ────────────────────────────────────────────────
VARIANT_OPTIONS = [
    {"value": "continue_variant", "label": "继续做变式训练"},
    {"value": "review_node", "label": "复习本节点"},
    {"value": "do_later", "label": "稍后复习，加入错题本"},
]

LOW_SCORE_OPTIONS = [
    {"value": "review_node", "label": "复习本节点"},
    {"value": "do_later", "label": "稍后复习，加入错题本"},
    {"value": "still_do_variant", "label": "仍然做变式训练"},
]

PAUSED_OPTIONS = [
    {"value": "review_node", "label": "复习本节点"},
    {"value": "do_later", "label": "稍后复习"},
]


def _build_remediation_state(state: AgentState) -> dict[str, Any]:
    """从 state 构建或更新 node_remediation_state 默认结构。"""
    existing = dict(state.get("node_remediation_state") or {})
    existing.setdefault("original_score", state.get("node_quiz_score", 0))
    existing.setdefault("variant_rounds", 0)
    existing.setdefault("same_objective_failures", {})
    existing.setdefault("extra_remediation_question_count", 0)
    existing.setdefault("status", "awaiting_remediation_decision")
    return existing


def _remediation_paused(remediation_state: dict[str, Any]) -> bool:
    """检查是否触发硬界限暂停。返回 True 表示需要暂停。"""
    if remediation_state.get("variant_rounds", 0) >= MAX_VARIANT_ROUNDS_PER_NODE:
        return True
    failures = remediation_state.get("same_objective_failures", {})
    if any(count >= MAX_SAME_OBJECTIVE_FAILURES for count in failures.values()):
        return True
    if remediation_state.get("extra_remediation_question_count", 0) > MAX_EXTRA_REMEDIATION_QUESTIONS:
        return True
    return False


def _score_tier(score: int) -> str:
    """返回分数档次: pass / partial / low"""
    if score >= 80:
        return "pass"
    if score >= 60:
        return "partial"
    return "low"


def _build_decision_data(
    state: AgentState,
    remediation_state: dict[str, Any],
    *,
    paused: bool = False,
) -> dict[str, Any]:
    """构建补救决策卡的结构化数据。"""
    score = remediation_state.get("original_score", state.get("node_quiz_score", 0))
    wrong_count = len(state.get("wrong_question_explanations", []) or state.get("node_quiz_wrong_items", []))
    tier = _score_tier(score)
    variant_rounds = remediation_state.get("variant_rounds", 0)
    failures = dict(remediation_state.get("same_objective_failures", {}))
    extra_count = remediation_state.get("extra_remediation_question_count", 0)

    data = {
        "score": score,
        "pass_score": 80,
        "passed": tier == "pass",
        "wrong_count": wrong_count,
        "tier": tier,
        "variant_rounds": variant_rounds,
        "max_variant_rounds": MAX_VARIANT_ROUNDS_PER_NODE,
        "same_objective_failures": failures,
        "extra_remediation_question_count": extra_count,
        "max_extra_questions": MAX_EXTRA_REMEDIATION_QUESTIONS,
        "paused": paused,
    }
    if paused:
        data["paused_reasons"] = _paused_reasons(remediation_state)
    return data


def _paused_reasons(remediation_state: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if remediation_state.get("variant_rounds", 0) >= MAX_VARIANT_ROUNDS_PER_NODE:
        reasons.append(f"已做 {remediation_state['variant_rounds']} 轮变式训练，达到上限 {MAX_VARIANT_ROUNDS_PER_NODE} 轮。")
    failures = remediation_state.get("same_objective_failures", {})
    for obj, count in failures.items():
        if count >= MAX_SAME_OBJECTIVE_FAILURES:
            reasons.append(f"考察点「{obj}」已连续错 {count} 次，继续刷题效果不高。")
    extra_count = remediation_state.get("extra_remediation_question_count", 0)
    if extra_count > MAX_EXTRA_REMEDIATION_QUESTIONS:
        reasons.append(f"额外补救题已达 {extra_count} 道，超过上限 {MAX_EXTRA_REMEDIATION_QUESTIONS} 道。")
    return reasons


def _normalize_choice(text: str) -> str:
    value = str(text or "").strip().lower()
    mapping = {
        "1": "continue_variant",
        "继续变式训练": "continue_variant",
        "变式训练": "continue_variant",
        "继续做题": "continue_variant",
        "continue_variant": "continue_variant",
        "2": "review_node",
        "复习本节点": "review_node",
        "复习": "review_node",
        "回看讲解": "review_node",
        "review_node": "review_node",
        "3": "do_later",
        "稍后复习": "do_later",
        "加入错题本": "do_later",
        "稍后": "do_later",
        "do_later": "do_later",
        "仍然做变式训练": "still_do_variant",
        "仍然做变式": "still_do_variant",
        "still_do_variant": "still_do_variant",
    }
    return mapping.get(value, value)


def build_remediation_decision_node(event_sink: EventSink, answer_provider: AnswerProvider):
    """补救决策节点：错题讲解完成后，根据分数和硬界限决定下一步。

    路由结果（通过 learning_resume_target）:
      - variant_question_generator → 继续做变式
      - node_content_loader → 复习本节点
      - continue_or_homework_selector → 稍后复习
      - remediation_paused → 达到界限暂停
    """

    def node(state: AgentState) -> dict:
        remediation_state = _build_remediation_state(state)
        awaiting = state.get("flow_status") == "awaiting_remediation_decision"
        current_node_name = str(
            state.get("current_node_name") or state.get("graph_anchor_title") or "当前节点"
        ).strip()
        score = remediation_state.get("original_score", state.get("node_quiz_score", 0))
        tier = _score_tier(score)
        paused = _remediation_paused(remediation_state)
        wrong_count = len(
            state.get("wrong_question_explanations", [])
            or state.get("node_quiz_wrong_items", [])
        )

        if not awaiting:
            # ── 首次进入：展示决策卡 ──
            if paused:
                reasons = _paused_reasons(remediation_state)
                prompt = (
                    f"本轮得分 {score}，未通过。\n"
                    + "\n".join(reasons)
                    + "\n\n建议先回到节点讲解重点复习，再做变式训练。"
                )
                options = PAUSED_OPTIONS
                decision_data = _build_decision_data(state, remediation_state, paused=True)
                event_sink.emit(
                    make_event("node.start", "remediation_decision", message=prompt,
                               data={**decision_data, "options": options, "requires_input": True})
                )
                return {
                    "flow_status": "awaiting_remediation_decision",
                    "remediation_decision": "",
                    "node_remediation_state": remediation_state,
                    "learning_phase": "remediation_paused",
                    "learning_resume_target": "remediation_decision",
                    "pending_interaction_kind": "remediation_decision",
                    "pending_interaction_prompt": prompt,
                    "pending_interaction_options": options,
                    "pending_interaction_recommended": "review_node",
                    "pending_interaction_answer": "",
                    "current_node_status": "quizzing",
                }

            if tier == "partial":
                prompt = (
                    f"你本轮得分 {score}，未达到 80 分。\n"
                    f"已为你整理 {wrong_count} 个错因。"
                )
                options = VARIANT_OPTIONS
                recommended = "continue_variant"
            else:  # low
                prompt = (
                    f"你本轮得分 {score}，说明当前节点基础理解还不稳。\n"
                    f"建议先回到节点讲解，再做变式题。"
                )
                options = LOW_SCORE_OPTIONS
                recommended = "review_node"

            decision_data = _build_decision_data(state, remediation_state)
            event_sink.emit(
                make_event("node.start", "remediation_decision", message=prompt,
                           data={**decision_data, "options": options, "requires_input": True})
            )
            return {
                "flow_status": "awaiting_remediation_decision",
                "remediation_decision": "",
                "node_remediation_state": remediation_state,
                "learning_phase": "remediation_decision",
                "learning_resume_target": "remediation_decision",
                "pending_interaction_kind": "remediation_decision",
                "pending_interaction_prompt": prompt,
                "pending_interaction_options": options,
                "pending_interaction_recommended": recommended,
                "pending_interaction_answer": "",
                "current_node_status": "quizzing",
            }

        # ── 用户已选择 ──
        choice = str(state.get("pending_interaction_answer") or "").strip()
        if not choice:
            choice = answer_provider.get_answer(
                str(state.get("pending_interaction_prompt") or ""),
                state={
                    "interaction_kind": "remediation_decision",
                    "options": state.get("pending_interaction_options") or VARIANT_OPTIONS,
                    "current_node_id": state.get("current_node_id") or "",
                },
            ).strip()
        normalized = _normalize_choice(choice)

        message_history = list(state.get("message_history", []))
        message_history.append({
            "role": "user",
            "kind": "remediation_decision",
            "content": choice or normalized,
            "data": {"selected_value": normalized},
        })

        # ── 根据选择路由 ──
        if normalized == "continue_variant":
            # 用户选择继续变式 → 更新状态中的 variant_rounds
            remediation_state["variant_rounds"] = remediation_state.get("variant_rounds", 0) + 1
            remediation_state["status"] = "variant_in_progress"
            event_sink.emit(make_event("node.complete", "remediation_decision",
                                       message="好，进入错题变式训练。"))
            return {
                "flow_status": "normal",
                "remediation_decision": normalized,
                "node_remediation_state": remediation_state,
                "learning_phase": "node_quiz_variant_generating",
                "learning_resume_target": "variant_question_generator",
                "learning_resume_reason": "remediation_continue_variant",
                "pending_interaction_kind": "",
                "pending_interaction_prompt": "",
                "pending_interaction_options": [],
                "pending_interaction_recommended": "",
                "pending_interaction_answer": "",
                "message_history": message_history,
            }

        if normalized == "review_node":
            remediation_state["status"] = "review_node"
            event_sink.emit(make_event("node.complete", "remediation_decision",
                                       message="好，回到本节点讲解重新学习。"))
            return {
                "flow_status": "normal",
                "remediation_decision": normalized,
                "node_remediation_state": remediation_state,
                "learning_phase": "node_teaching",
                "learning_resume_target": "node_content_loader",
                "learning_resume_reason": "remediation_review_node",
                "pending_interaction_kind": "",
                "pending_interaction_prompt": "",
                "pending_interaction_options": [],
                "pending_interaction_recommended": "",
                "pending_interaction_answer": "",
                "message_history": message_history,
                "current_node_status": "selected",
            }

        if normalized == "still_do_variant":
            remediation_state["variant_rounds"] = remediation_state.get("variant_rounds", 0) + 1
            remediation_state["status"] = "variant_in_progress"
            event_sink.emit(make_event("node.complete", "remediation_decision",
                                       message="好，尽管基础还不够稳，仍然做变式训练。注意做完变式后还要完成短复测。"))
            return {
                "flow_status": "normal",
                "remediation_decision": normalized,
                "node_remediation_state": remediation_state,
                "learning_phase": "node_quiz_variant_generating",
                "learning_resume_target": "variant_question_generator",
                "learning_resume_reason": "remediation_still_variant",
                "pending_interaction_kind": "",
                "pending_interaction_prompt": "",
                "pending_interaction_options": [],
                "pending_interaction_recommended": "",
                "pending_interaction_answer": "",
                "message_history": message_history,
            }

        # do_later → 进入 homework/continue 选择
        remediation_state["status"] = "deferred"
        event_sink.emit(make_event("node.complete", "remediation_decision",
                                   message="好，把当前节点加入待复习。"))
        return {
            "flow_status": "normal",
            "remediation_decision": normalized,
            "node_remediation_state": remediation_state,
            "learning_phase": "remediation_deferred",
            "learning_resume_target": "continue_or_homework_selector",
            "learning_resume_reason": "remediation_deferred",
            "pending_interaction_kind": "",
            "pending_interaction_prompt": "",
            "pending_interaction_options": [],
            "pending_interaction_recommended": "",
            "pending_interaction_answer": "",
            "message_history": message_history,
        }

    return node


def route_after_remediation_decision(state: AgentState) -> str:
    """根据 remediation_decision 值路由到下一个节点。"""
    normalized = str(state.get("remediation_decision") or "").strip()
    if normalized == "continue_variant":
        return "variant_question_generator"
    if normalized == "still_do_variant":
        return "variant_question_generator"
    if normalized == "review_node":
        return "node_content_loader"
    if normalized == "do_later":
        return "continue_or_homework_selector"
    # fallback: pause and wait
    return "pause"

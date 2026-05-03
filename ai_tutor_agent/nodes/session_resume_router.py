from __future__ import annotations

from ..core.events import make_event
from ..core.learning_flow import infer_resume_target, normalize_resume_target
from ..core.learning_support import build_graph_state_patch, recommend_next_node, trim_message_history
from ..core.ports import RuntimeContext
from ..core.state import AgentState

PENDING_FLOW_STATUSES = {
    "awaiting_post_lesson_choice",
    "awaiting_temporary_question",
    "awaiting_objective_answers",
    "awaiting_variant_answers",
    "awaiting_continue_or_homework_choice",
    "awaiting_homework_review_choice",
    "awaiting_homework_answers",
    "awaiting_interrupt_confirmation",
    "assessment_dialog",
    "profiling",
}

CONSOLIDATION_OPTIONS = [
    {"value": "consolidate", "label": "巩固复习（生成复习题）"},
    {"value": "continue_learning", "label": "直接开始下一节点"},
]


_TERMINAL_HOMEWORK_STATUSES = {"completed", "submitted", "deferred"}


def _has_homework(state: AgentState) -> bool:
    """有作业且状态为活跃（非终态、非暂缓）。状态缺失时默认视为 assigned。"""
    if not state.get("homework_items"):
        return False
    status = str(state.get("homework_status") or "").strip()
    if not status:
        return True  # 状态丢失，有 items 就当有作业
    return status not in _TERMINAL_HOMEWORK_STATUSES


def _has_deferred_homework(state: AgentState) -> bool:
    return bool(state.get("homework_items")) and str(state.get("homework_status") or "").strip() == "deferred"


def build_session_resume_router_node(runtime: RuntimeContext):
    event_sink = runtime.event_sink

    def node(state: AgentState) -> dict:
        flow_status = str(state.get("flow_status") or "").strip()
        event_sink.emit(
            make_event(
                "node.start",
                "session_resume_router",
                message="正在根据上次学习记录决定恢复入口。",
                data={"flow_status": flow_status, "homework_status": state.get("homework_status", "")},
            )
        )

        if flow_status in PENDING_FLOW_STATUSES and flow_status != "homework_assigned":
            target = infer_resume_target(state)
            event_sink.emit(
                make_event(
                    "node.complete",
                    "session_resume_router",
                    message=f"检测到上次有未完成交互，恢复到 {target}。",
                    data={"target": target},
                )
            )
            return {
                "learning_phase": state.get("learning_phase") or "homework_resume",
                "learning_resume_target": target,
                "learning_resume_reason": "resume_pending_interaction",
            }

        if _has_homework(state):
            event_sink.emit(
                make_event(
                    "node.complete",
                    "session_resume_router",
                    message="检测到上次留下的作业，先进入作业回顾。",
                    data={"homework_count": len(state.get("homework_items") or [])},
                )
            )
            return {
                "flow_status": "normal",
                "learning_phase": "homework_resume",
                "learning_resume_target": "homework_review",
                "learning_resume_reason": "existing_homework_found",
            }

        if _has_deferred_homework(state):
            target = normalize_resume_target(state.get("learning_resume_target", ""))
            if target in {"session_resume_router", "homework_review", "homework_answer_dialog", "homework_generator"}:
                target = ""
            next_target = target or ("node_content_loader" if state.get("next_node_candidate_id") else "next_node_planner")
            event_sink.emit(
                make_event(
                    "node.complete",
                    "session_resume_router",
                    message="检测到上次已选择暂缓作业，按原选择继续学习。",
                    data={"homework_count": len(state.get("homework_items") or []), "target": next_target},
                )
            )
            return {
                "flow_status": "normal",
                "learning_phase": state.get("learning_phase") or "node_selected",
                "learning_resume_target": next_target,
                "learning_resume_reason": "homework_deferred_continue_learning",
            }

        # ── 无作业：询问用户是否需要巩固复习 ──
        awaiting_consolidation = state.get("flow_status") == "awaiting_consolidation_choice"
        if not awaiting_consolidation:
            prompt = "上次没有留作业。你想先巩固复习已学内容，还是直接开始下一节点的学习？"
            event_sink.emit(
                make_event(
                    "node.start",
                    "session_resume_router",
                    message=prompt,
                    data={"options": CONSOLIDATION_OPTIONS, "requires_input": True},
                )
            )
            return {
                "flow_status": "awaiting_consolidation_choice",
                "learning_phase": "homework_resume",
                "learning_resume_target": "session_resume_router",
                "learning_resume_reason": "consolidation_choice_required",
                "pending_interaction_kind": "consolidation_choice",
                "pending_interaction_prompt": prompt,
                "pending_interaction_options": CONSOLIDATION_OPTIONS,
                "pending_interaction_recommended": "continue_learning",
                "pending_interaction_answer": "",
            }

        # ── 用户已选择 ──
        choice = str(state.get("pending_interaction_answer") or "").strip().lower()
        if not choice:
            prompt = str(state.get("pending_interaction_prompt") or "").strip() or "上次没有留作业。你想先巩固复习已学内容，还是直接开始下一节点的学习？"
            event_sink.emit(
                make_event(
                    "node.start",
                    "session_resume_router",
                    message=prompt,
                    data={"options": CONSOLIDATION_OPTIONS, "requires_input": True},
                )
            )
            return {
                "flow_status": "awaiting_consolidation_choice",
                "learning_phase": "homework_resume",
                "learning_resume_target": "session_resume_router",
                "learning_resume_reason": "consolidation_choice_required",
                "pending_interaction_kind": "consolidation_choice",
                "pending_interaction_prompt": prompt,
                "pending_interaction_options": state.get("pending_interaction_options") or CONSOLIDATION_OPTIONS,
                "pending_interaction_recommended": state.get("pending_interaction_recommended") or "continue_learning",
                "pending_interaction_answer": "",
            }
        consolidate_values = {"consolidate", "巩固", "先巩固", "需要巩固", "巩固复习", "复习", "生成复习题"}
        continue_values = {"continue_learning", "继续", "继续学习", "直接开始下一节点", "直接开始下一个节点", "下一节点"}
        normalized_choice = "consolidate" if choice in consolidate_values else "continue_learning"
        if choice and choice not in consolidate_values and choice not in continue_values:
            normalized_choice = "continue_learning"
        message_history = list(state.get("message_history", []))
        message_history.append(
            {
                "role": "user",
                "kind": "consolidation_choice",
                "content": str(state.get("pending_interaction_answer") or "").strip() or normalized_choice,
                "data": {"selected_value": normalized_choice},
            }
        )
        if choice in consolidate_values:
            event_sink.emit(
                make_event(
                    "node.complete",
                    "session_resume_router",
                    message="好，根据你已学记录生成复习题。",
                )
            )
            return {
                "flow_status": "normal",
                "learning_phase": "homework_generation_requested",
                "learning_resume_target": "homework_generator",
                "learning_resume_reason": "consolidation_homework_requested",
                "pending_interaction_kind": "",
                "pending_interaction_prompt": "",
                "pending_interaction_options": [],
                "pending_interaction_recommended": "",
                "pending_interaction_answer": "",
                "message_history": trim_message_history(message_history),
            }

        # 用户选择继续学习，找下一节点
        graph_pipeline = getattr(runtime, "graph_rag_pipeline", None)
        current_node_id = str(state.get("current_node_id") or state.get("graph_anchor_id") or "").strip()
        next_candidate = recommend_next_node(
            graph_pipeline=graph_pipeline,
            student_state_snapshot=state.get("student_state_snapshot"),
            current_node_id=current_node_id,
        )
        next_node_id = str(next_candidate.get("node_id") or state.get("next_node_candidate_id") or "").strip()
        next_node_name = str(next_candidate.get("name") or state.get("next_node_candidate_name") or "").strip()

        if next_node_id:
            graph_patch = build_graph_state_patch(graph_pipeline, next_node_id)
            event_sink.emit(
                make_event(
                    "node.complete",
                    "session_resume_router",
                    message=f"好，继续学习下一个图谱节点【{next_node_name or next_node_id}】。",
                    data={"next_node_id": next_node_id},
                )
            )
            return {
                "flow_status": "normal",
                "learning_phase": "next_node_planned",
                "learning_resume_target": "node_content_loader",
                "learning_resume_reason": "resume_continue_learning",
                "next_node_candidate_id": next_node_id,
                "next_node_candidate_name": next_node_name or next_node_id,
                "next_node_candidate_reason": str(next_candidate.get("reason") or "resume_next_node").strip(),
                "current_node_id": next_node_id,
                "current_node_name": next_node_name or next_node_id,
                "current_node_status": "selected",
                "current_user_goal": next_node_name or next_node_id,
                "turn_goal": next_node_name or next_node_id,
                "topic_focus": next_node_name or next_node_id,
                "pending_interaction_kind": "",
                "pending_interaction_prompt": "",
                "pending_interaction_options": [],
                "pending_interaction_recommended": "",
                "pending_interaction_answer": "",
                "message_history": trim_message_history(message_history),
                **graph_patch,
            }

        event_sink.emit(
            make_event(
                "node.complete",
                "session_resume_router",
                message="没有检测到可继续节点，回到当前节点讲解入口。",
            )
        )
        return {
            "flow_status": "normal",
            "learning_phase": "node_teaching",
            "learning_resume_target": "tutor",
            "learning_resume_reason": "resume_current_node_teaching",
            "pending_interaction_kind": "",
            "pending_interaction_prompt": "",
            "pending_interaction_options": [],
            "pending_interaction_recommended": "",
            "pending_interaction_answer": "",
            "message_history": trim_message_history(message_history),
        }

    return node

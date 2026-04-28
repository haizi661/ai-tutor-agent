from __future__ import annotations

from ..core.events import make_event
from ..core.learning_support import load_student_state_snapshot, recommend_next_node
from ..core.ports import RuntimeContext
from ..core.state import AgentState


def build_next_node_planner_node(runtime: RuntimeContext):
    event_sink = runtime.event_sink
    graph_rag_pipeline = getattr(runtime, "graph_rag_pipeline", None)
    student_state_store = getattr(runtime, "student_state_store", None)

    def node(state: AgentState) -> dict:
        student_id = str(state.get("student_id") or "default_student").strip() or "default_student"
        current_node_id = str(state.get("current_node_id") or state.get("graph_anchor_id") or "").strip()
        _, loaded_snapshot = load_student_state_snapshot(student_state_store, student_id)
        state_snapshot = loaded_snapshot or dict(state.get("student_state_snapshot") or {})

        next_candidate = recommend_next_node(
            graph_pipeline=graph_rag_pipeline,
            student_state_snapshot=state_snapshot,
            current_node_id=current_node_id,
        )
        next_node_id = str(next_candidate.get("node_id") or "").strip()
        next_node_name = str(next_candidate.get("name") or "").strip()
        reason = str(next_candidate.get("reason") or "").strip()

        message = (
            f"当前节点已通过。下一节点候选为【{next_node_name or next_node_id}】。"
            if next_node_id
            else "当前节点已通过。暂时没有找到未学习的下一节点，建议进入今日作业收束。"
        )
        event_sink.emit(
            make_event(
                "node.complete",
                "next_node_planner",
                message=message,
                data={"next_node_candidate": next_candidate, "reason": reason},
            )
        )

        return {
            "flow_status": "normal",
            "learning_phase": "next_node_planned",
            "learning_resume_target": "continue_or_homework_selector",
            "learning_resume_reason": "objective_test_passed_next_node_planned",
            "next_node_candidate_id": next_node_id,
            "next_node_candidate_name": next_node_name,
            "next_node_candidate_reason": reason,
            "student_state_snapshot": state_snapshot,
            "pending_interaction_kind": "",
            "pending_interaction_prompt": "",
            "pending_interaction_options": [],
            "pending_interaction_recommended": "",
            "pending_interaction_answer": "",
        }

    return node

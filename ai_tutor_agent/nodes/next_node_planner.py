from __future__ import annotations

from ..core.events import make_event
from ..core.learning_plan_builder import (
    find_next_node_in_step,
    find_current_step_progress,
    is_step_completed,
)
from ..core.learning_plan_v2 import LearningPlan
from ..core.learning_support import (
    _node_name,
    _string_list,
    graph_node_sort_key,
    load_student_state_snapshot,
    mutate_student_state_snapshot,
    recommend_next_node,
)
from ..core.ports import RuntimeContext
from ..core.state import AgentState
from ..knowledge_map.student_state import StudentState


def _sync_v2_plan_status(
    student_state: StudentState,
    plan_steps: list[dict],
) -> None:
    """Sync step statuses from AgentState plan back to v2 LearningPlan."""
    v2_raw = student_state.learning_plan_v2
    if not v2_raw or not v2_raw.get("steps"):
        return
    try:
        v2_plan = LearningPlan.from_dict(v2_raw)
        for idx, step in enumerate(plan_steps):
            if idx < len(v2_plan.steps):
                v2_plan.steps[idx].status = step.get("status", "pending")
        student_state.learning_plan_v2 = v2_plan.to_dict()
    except Exception:
        pass


def build_next_node_planner_node(runtime: RuntimeContext):
    event_sink = runtime.event_sink
    graph_rag_pipeline = getattr(runtime, "graph_rag_pipeline", None)
    student_state_store = getattr(runtime, "student_state_store", None)

    def node(state: AgentState) -> dict:
        student_id = str(state.get("student_id") or "default_student").strip() or "default_student"
        current_node_id = str(state.get("current_node_id") or state.get("graph_anchor_id") or "").strip()
        _, loaded_snapshot = load_student_state_snapshot(student_state_store, student_id)
        state_snapshot = loaded_snapshot or dict(state.get("student_state_snapshot") or {})

        visited = set(_string_list(state_snapshot.get("visited_nodes")))
        knowledge_graph = dict(state_snapshot.get("knowledge_graph") or {})
        # Also consider mastered nodes as visited
        for nid, entry in knowledge_graph.items():
            if isinstance(entry, dict) and entry.get("status") == "mastered":
                visited.add(nid)

        learning_plan = state.get("learning_plan") or state_snapshot.get("learning_plan") or []
        current_step_idx = int(state.get("learning_plan_current_step") or state_snapshot.get("learning_plan_current_step") or 0)

        next_node_id = ""
        next_node_name = ""
        reason = ""
        source = ""
        new_step_idx = current_step_idx

        # ── Try learning plan first ──
        if learning_plan and current_step_idx < len(learning_plan):
            current_step = learning_plan[current_step_idx]

            # 1. Find next unvisited node in current step
            candidate = find_next_node_in_step(current_step, visited, current_node_id)
            if candidate:
                next_node_id = candidate
                node_map = dict(getattr(graph_rag_pipeline, "node_map", {}) or {})
                next_node_name = _node_name(node_map, candidate)
                reason = "same_step"
                source = "learning_plan"
            else:
                # 2. Current step completed, advance to next step
                current_step["status"] = "completed"
                new_step_idx = current_step_idx + 1

                if new_step_idx < len(learning_plan):
                    next_step = learning_plan[new_step_idx]
                    next_step["status"] = "in_progress"
                    new_step_idx = new_step_idx

                    candidate = find_next_node_in_step(next_step, visited, "")
                    if candidate:
                        next_node_id = candidate
                        node_map = dict(getattr(graph_rag_pipeline, "node_map", {}) or {})
                        next_node_name = _node_name(node_map, candidate)
                        reason = "next_step"
                        source = "learning_plan"
                else:
                    # 3. All steps completed
                    source = "plan_completed"

        # ── Fallback: original recommend_next_node logic ──
        if not next_node_id and source != "plan_completed":
            next_candidate = recommend_next_node(
                graph_pipeline=graph_rag_pipeline,
                student_state_snapshot=state_snapshot,
                current_node_id=current_node_id,
            )
            next_node_id = str(next_candidate.get("node_id") or "").strip()
            next_node_name = str(next_candidate.get("name") or "").strip()
            reason = str(next_candidate.get("reason") or "").strip()
            source = "fallback"

        # ── Build message ──
        if source == "plan_completed":
            message = "学习路径中所有节点已学习完成，建议进入今日作业收束。"
        elif next_node_id:
            if reason == "same_step":
                step_progress = find_current_step_progress(learning_plan, visited)
                message = f"当前节点已通过。继续学习同一步骤中的【{next_node_name or next_node_id}】。"
                if step_progress[2] > 0:
                    message += f"（步骤进度：{step_progress[1]}/{step_progress[2]}）"
            elif reason == "next_step":
                step = learning_plan[new_step_idx] if new_step_idx < len(learning_plan) else {}
                step_name = step.get("step_name", "")
                message = f"当前步骤已完成。进入下一步：{step_name}，学习【{next_node_name or next_node_id}】。"
            else:
                message = f"当前节点已通过。下一节点候选为【{next_node_name or next_node_id}】。"
        else:
            message = "当前节点已通过。暂时没有找到未学习的下一节点，建议进入今日作业收束。"

        event_sink.emit(
            make_event(
                "node.complete",
                "next_node_planner",
                message=message,
                data={
                    "next_node_id": next_node_id,
                    "next_node_name": next_node_name,
                    "reason": reason,
                    "source": source,
                    "current_step": new_step_idx,
                    "total_steps": len(learning_plan),
                },
            )
        )

        # ── Emit learning plan progress event ──
        is_step_advance = False
        if learning_plan:
            step_progress = find_current_step_progress(learning_plan, visited)
            is_step_advance = reason == "next_step"
            event_sink.emit(
                make_event(
                    "learning_plan.progress",
                    "next_node_planner",
                    message=f"学习路径进度：第 {step_progress[0] + 1}/{len(learning_plan)} 步",
                    data={
                        "current_step": step_progress[0],
                        "total_steps": len(learning_plan),
                        "step_progress": f"{step_progress[1]}/{step_progress[2]}",
                        "next_node_in_step": next_node_id,
                        "step_completed": is_step_advance,
                    },
                )
            )

        # ── Session / step completion events ──
        if source == "plan_completed":
            session_index = state_snapshot.get("session_index", 0)
            event_sink.emit(
                make_event(
                    "learning_plan.session_completed",
                    "next_node_planner",
                    message=f"第 {session_index} 号学习路径全部完成。",
                    data={
                        "session_index": session_index,
                        "total_steps": len(learning_plan),
                        "plan_completed": True,
                    },
                )
            )
        elif is_step_advance:
            step = learning_plan[new_step_idx] if new_step_idx < len(learning_plan) else {}
            entry_modes = step.get("entry_modes", {}) if isinstance(step, dict) else {}
            if entry_modes:
                quick = sum(1 for m in entry_modes.values() if m == "quick_check")
                full = sum(1 for m in entry_modes.values() if m == "full_learning")
                event_sink.emit(
                    make_event(
                        "learning_plan.step_start",
                        "next_node_planner",
                        message=(
                            f"第 {new_step_idx + 1} 步："
                            f"{'快速检测' if quick > 0 else ''}"
                            f"{'完整学习' if full > 0 else ''}"
                            f"（{len(step.get('node_ids', []))} 个知识点）"
                        ),
                        data={"step_index": new_step_idx, "entry_modes": entry_modes},
                    )
                )

        # ── Persist step updates ──
        if learning_plan and new_step_idx != current_step_idx:
            def _update_step(student_state: StudentState) -> None:
                student_state.learning_plan = list(learning_plan)
                student_state.learning_plan_current_step = new_step_idx
                # Sync v2 plan step statuses so persistence stays consistent
                _sync_v2_plan_status(student_state, learning_plan)
            mutate_student_state_snapshot(student_state_store, student_id, _update_step)
            state_snapshot["learning_plan"] = list(learning_plan)
            state_snapshot["learning_plan_current_step"] = new_step_idx

        return {
            "flow_status": "normal",
            "learning_phase": "next_node_planned",
            "learning_resume_target": "continue_or_homework_selector",
            "learning_resume_reason": "objective_test_passed_next_node_planned",
            "next_node_candidate_id": next_node_id,
            "next_node_candidate_name": next_node_name,
            "next_node_candidate_reason": reason,
            "learning_plan": learning_plan,
            "learning_plan_current_step": new_step_idx,
            "learning_plan_source": "plan_completed" if source == "plan_completed" else state.get("learning_plan_source", ""),
            "student_state_snapshot": state_snapshot,
            "pending_interaction_kind": "",
            "pending_interaction_prompt": "",
            "pending_interaction_options": [],
            "pending_interaction_recommended": "",
            "pending_interaction_answer": "",
        }

    return node

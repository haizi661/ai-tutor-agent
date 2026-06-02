"""Learning Plan Generator v2 — generates adaptive learning paths.

This node runs after user_profiler (or session resume) and before
initial_node_selector.  It builds a StudentProfile from stored
concept_mastery (or cold-start default / self-assessment), calls
generate_learning_plan_v2(), and persists the result to both StudentState
and AgentState.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..core.events import make_event
from ..core.learning_support import (
    load_student_state_snapshot,
    mutate_student_state_snapshot,
)
from ..core.learning_plan_v2 import (
    LearningPlan,
    generate_learning_plan_v2,
    _refresh_previous_plan,
)
from ..core.ports import RuntimeContext
from ..core.state import AgentState
from ..core.student_profile import ConceptMastery, StudentProfile
from ..knowledge_map.student_state import StudentState


def _rebuild_profile(
    concept_mastery_raw: dict[str, Any],
    profile_id: str,
) -> StudentProfile | None:
    """Reconstruct StudentProfile from persisted concept_mastery dict."""
    if not concept_mastery_raw:
        return None
    profile = StudentProfile(profile_id=profile_id)
    try:
        for nid, cm_dict in concept_mastery_raw.items():
            if isinstance(cm_dict, dict):
                profile.concept_mastery[nid] = ConceptMastery.from_dict(cm_dict)
        profile.last_updated = profile.created_at
        return profile
    except Exception:
        return None


def _profile_to_cm_dict(profile: StudentProfile) -> dict[str, dict[str, Any]]:
    return {nid: cm.to_dict() for nid, cm in profile.concept_mastery.items()}


def _get_edges(graph_pipeline: Any) -> list[dict[str, Any]]:
    if graph_pipeline is None:
        return []
    return list(getattr(graph_pipeline, "edges", []) or [])


def build_learning_plan_generator_node(llm: Any, runtime: RuntimeContext):
    event_sink = runtime.event_sink
    graph_pipeline = getattr(runtime, "graph_rag_pipeline", None)
    student_state_store = getattr(runtime, "student_state_store", None)

    def node(state: AgentState) -> dict:
        student_id = (
            str(state.get("student_id") or "default_student").strip()
            or "default_student"
        )
        _, loaded_snapshot = load_student_state_snapshot(
            student_state_store, student_id
        )
        state_snapshot = loaded_snapshot or dict(
            state.get("student_state_snapshot") or {}
        )

        edges = _get_edges(graph_pipeline)

        # ── Step 1: Try resume v2 plan ────────────────────────────
        v2_plan_raw = state_snapshot.get("learning_plan_v2") or {}
        concept_mastery_raw = state_snapshot.get("concept_mastery") or {}

        if v2_plan_raw.get("steps"):
            plan = LearningPlan.from_dict(v2_plan_raw)
            if plan.resolve_status() == "in_progress":
                profile = _rebuild_profile(concept_mastery_raw, student_id)
                if profile:
                    # resume 路径:如果 step_name 看起来是老规则生成的(=首节点名),
                    # 用 LLM 重新命名一次(避免老 plan 永远是老名字)
                    _refresh_previous_plan(plan, profile, llm=llm)
                    steps_as_dicts = [s.to_dict() for s in plan.steps]
                    current_step = plan.get_current_step() or 0
                    event_sink.emit(
                        make_event(
                            "learning_plan.reused",
                            "learning_plan_generator",
                            message=(
                                f"续上学习路径：{len(plan.steps)} 步，"
                                f"{plan.total_nodes} 个知识点。"
                            ),
                            data={
                                "total_steps": len(plan.steps),
                                "total_nodes": plan.total_nodes,
                                "current_step": current_step,
                                "source": "resume_v2",
                                "session_index": plan.session_index + 1,
                                "plan": steps_as_dicts,
                            },
                        )
                    )

                    def _persist_resume(ss: StudentState) -> None:
                        ss.learning_plan_v2 = plan.to_dict()
                        ss.learning_plan = steps_as_dicts
                        ss.learning_plan_current_step = current_step
                        ss.learning_plan_source = "resume_v2"

                    mutate_student_state_snapshot(
                        student_state_store, student_id, _persist_resume
                    )

                    state_snapshot["learning_plan"] = steps_as_dicts
                    state_snapshot["learning_plan_current_step"] = current_step
                    state_snapshot["learning_plan_source"] = "resume_v2"

                    return {
                        "learning_plan": steps_as_dicts,
                        "learning_plan_current_step": current_step,
                        "learning_plan_generated_at": plan.generated_at,
                        "learning_plan_source": "resume_v2",
                        "student_state_snapshot": state_snapshot,
                        "learning_phase": "plan_generated",
                        "learning_resume_target": "initial_node_selector",
                        "learning_resume_reason": "learning_plan_v2_resumed",
                    }

        # ── Step 2: Build / rebuild student profile ───────────────
        self_scores = (
            state.get("self_assessment_scores")
            or state_snapshot.get("self_assessment_scores")
            or {}
        )
        skip = (
            state.get("skip_self_assessment")
            if state.get("skip_self_assessment") is not None
            else state_snapshot.get("skip_self_assessment", True)
        )

        # If self_scores exist, always use them regardless of skip flag.
        # skip=True only matters when there are NO self-assessment scores at all.
        use_default_only = bool(skip) and not bool(self_scores)

        profile = _rebuild_profile(concept_mastery_raw, student_id)
        if profile is None:
            profile = StudentProfile(profile_id=student_id)
            if use_default_only:
                profile.init_from_default()
                event_sink.emit(
                    make_event(
                        "learning_plan.profile_init",
                        "learning_plan_generator",
                        message="冷启动：使用默认画像初始化。",
                        data={"source": "default", "skip": bool(skip)},
                    )
                )
            else:
                n_written = profile.init_from_self_assessment(
                    dict(self_scores)
                )
                event_sink.emit(
                    make_event(
                        "learning_plan.profile_init",
                        "learning_plan_generator",
                        message=f"自评画像初始化完成（{n_written} 个概念）。",
                        data={"source": "self_assessment", "n_concepts": n_written},
                    )
                )

        # ── Step 3: Determine session index ───────────────────────
        session_index = int(state_snapshot.get("session_index", 0))

        # ── Step 4: Generate learning plan ────────────────────────
        # 把 llm 传进去,新生成路径时用它给 step 取更自然的中文主题名
        # (续上路径时不调 LLM,见 _refresh_previous_plan)
        plan = generate_learning_plan_v2(
            profile=profile,
            edges=edges,
            previous_plan=None,
            session_index=session_index,
            llm=llm,
        )

        steps_as_dicts = [s.to_dict() for s in plan.steps]
        now_iso = datetime.now(timezone.utc).isoformat()

        # ── Empty plan = all nodes mastered ───────────────────────
        if not plan.steps:
            event_sink.emit(
                make_event(
                    "learning_plan.generated",
                    "learning_plan_generator",
                    message="所有可学知识点已掌握，学习路径已完成。",
                    data={
                        "total_steps": 0,
                        "total_nodes": 0,
                        "source": "all_mastered",
                        "plan": [],
                    },
                )
            )

            def _persist_empty(ss: StudentState) -> None:
                ss.concept_mastery = _profile_to_cm_dict(profile)
                ss.learning_plan_v2 = plan.to_dict()
                ss.learning_plan = []
                ss.learning_plan_current_step = 0
                ss.learning_plan_generated_at = now_iso
                ss.learning_plan_source = "all_mastered"
                ss.session_index = session_index + 1
                ss.skip_self_assessment = bool(skip)
                ss.self_assessment_scores = dict(self_scores)

            mutate_student_state_snapshot(
                student_state_store, student_id, _persist_empty
            )

            return {
                "learning_plan": [],
                "learning_plan_current_step": 0,
                "learning_plan_generated_at": now_iso,
                "learning_plan_source": "all_mastered",
                "student_state_snapshot": state_snapshot,
                "learning_phase": "plan_generated",
                "learning_resume_target": "continue_or_homework_selector",
                "learning_resume_reason": "all_nodes_mastered",
            }

        # ── Step 5: Persist to StudentState ───────────────────────
        plan_source_label = "profile_based"  # backward-compat for router

        def _persist(ss: StudentState) -> None:
            ss.concept_mastery = _profile_to_cm_dict(profile)
            ss.learning_plan_v2 = plan.to_dict()
            ss.learning_plan = steps_as_dicts
            ss.learning_plan_current_step = 0
            ss.learning_plan_generated_at = now_iso
            ss.learning_plan_source = plan_source_label
            ss.session_index = session_index + 1
            ss.skip_self_assessment = bool(skip)
            ss.self_assessment_scores = dict(self_scores)

        mutate_student_state_snapshot(
            student_state_store, student_id, _persist
        )

        # ── Step 6: Update AgentState snapshot ────────────────────
        state_snapshot["concept_mastery"] = _profile_to_cm_dict(profile)
        state_snapshot["learning_plan_v2"] = plan.to_dict()
        state_snapshot["learning_plan"] = steps_as_dicts
        state_snapshot["learning_plan_current_step"] = 0
        state_snapshot["learning_plan_generated_at"] = now_iso
        state_snapshot["learning_plan_source"] = plan_source_label
        state_snapshot["session_index"] = session_index + 1
        state_snapshot["skip_self_assessment"] = bool(skip)
        state_snapshot["self_assessment_scores"] = dict(self_scores)

        # ── Step 7: Emit events ───────────────────────────────────
        total_nodes = plan.total_nodes
        event_sink.emit(
            make_event(
                "learning_plan.generated",
                "learning_plan_generator",
                message=(
                    f"已生成本次{session_index + 1}号路径："
                    f"{len(plan.steps)} 步，{total_nodes} 个知识点。"
                ),
                data={
                    "total_steps": len(plan.steps),
                    "total_nodes": total_nodes,
                    "source": plan.source,
                    "session_index": session_index + 1,
                    "plan": steps_as_dicts,
                    "plan_summary": [
                        {
                            "step_index": s["step_index"],
                            "step_name": s["step_name"],
                            "node_count": len(s.get("node_ids", [])),
                            "reason": s.get("reason", ""),
                        }
                        for s in steps_as_dicts
                    ],
                },
            )
        )

        if steps_as_dicts:
            first_step = steps_as_dicts[0]
            modes_summary = ", ".join(
                f"{nid}={mode}"
                for nid, mode in (first_step.get("entry_modes") or {}).items()
            )
            event_sink.emit(
                make_event(
                    "learning_plan.step_detail",
                    "learning_plan_generator",
                    message=(
                        f"第一步：{first_step['step_name']} "
                        f"（{len(first_step['node_ids'])} 个知识点）"
                    ),
                    data={
                        "step_index": 0,
                        "step_name": first_step["step_name"],
                        "node_ids": first_step["node_ids"],
                        "entry_modes": first_step.get("entry_modes", {}),
                        "reason": first_step.get("reason", ""),
                        "entry_modes_summary": modes_summary,
                    },
                )
            )

        return {
            "learning_plan": steps_as_dicts,
            "learning_plan_current_step": 0,
            "learning_plan_generated_at": now_iso,
            "learning_plan_source": plan_source_label,
            "student_state_snapshot": state_snapshot,
            "learning_phase": "plan_generated",
            "learning_resume_target": "initial_node_selector",
            "learning_resume_reason": "learning_plan_v2_generated",
        }

    return node

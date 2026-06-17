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

from ..core.ability_mapper import get_all_node_ids
from ..core.events import make_event
from ..core.learning_support import (
    load_student_state_snapshot,
    mutate_student_state_snapshot,
)
from ..core.learning_plan_v2 import (
    LearningPlan,
    compute_context_boost,
    compute_freshness_boost,
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


def _find_node_id_by_concept_name(
    concept_name: str,
    node_map: dict[str, dict],
) -> str:
    """通过概念名称在 node_map 中查找节点 ID（模糊匹配）。"""
    target = str(concept_name or "").strip()
    if not target:
        return ""
    for node_id, node in node_map.items():
        node_name = str(node.get("name") or node.get("title") or "").strip()
        if target == node_name:
            return str(node_id).strip()
    for node_id, node in node_map.items():
        node_name = str(node.get("name") or node.get("title") or "").strip()
        if target and node_name and (target in node_name or node_name in target):
            return str(node_id).strip()
    for node_id, node in node_map.items():
        node_concepts = str(node.get("concept") or node.get("concept_id") or node.get("tags") or "").strip()
        if target and target in node_concepts:
            return str(node_id).strip()
    return ""


def _merge_assessment_gaps(
    profile: StudentProfile,
    assessment_gaps: dict[str, dict],
    node_map: dict[str, dict] | None = None,
) -> tuple[int, list[str]]:
    """将 assessment 产出的 calibrated concept_gaps 合并入 profile。

    匹配策略（按优先级）:
    1. node_id 字段直接匹配 → 用 calibrated 更新 mastery
    2. concept_id 直接匹配 node_id
    3. concept_name 在 node_map 中名称匹配
    4. dimension 匹配 ability code → 提升该 ability 下所有节点的 confidence

    返回 (合并的节点数, 被合并的节点 ID 列表)。
    """
    from ..core.ability_mapper import (
        get_all_node_ids,
        get_node_primary_ability,
    )

    all_node_ids = set(get_all_node_ids())
    node_map = dict(node_map or {})
    merged_count = 0
    merged_ids: list[str] = []
    now = datetime.now(timezone.utc).isoformat()

    def _apply_mastery(target_id: str, cal: float) -> None:
        nonlocal merged_count, merged_ids
        cal_norm = max(0.0, min(1.0, cal / 100.0))
        old = profile.concept_mastery.get(target_id)
        if old:
            new_mastery = max(0.0, min(1.0, 0.7 * cal_norm + 0.3 * old.mastery))
            new_confidence = min(1.0, max(old.confidence, 0.7))
        else:
            new_mastery = cal_norm
            new_confidence = 0.7
        profile.concept_mastery[target_id] = ConceptMastery(
            mastery=round(new_mastery, 4),
            confidence=round(new_confidence, 4),
            source="merged",
            risk="low" if new_mastery >= 0.6 else "medium",
            failure_count=old.failure_count if old else 0,
            last_updated=now,
        )
        merged_count += 1
        if target_id not in merged_ids:
            merged_ids.append(target_id)

    for concept_name, gap_info in assessment_gaps.items():
        if not isinstance(gap_info, dict):
            continue
        concept_id = str(gap_info.get("concept_id", "")).strip()
        dimension = str(gap_info.get("dimension", "")).strip()
        calibrated = float(gap_info.get("calibrated", 50))
        node_id_from_gap = str(gap_info.get("node_id", "")).strip()

        # Strategy 1a: node_id 字段直接匹配
        if node_id_from_gap and node_id_from_gap in all_node_ids:
            _apply_mastery(node_id_from_gap, calibrated)
            continue

        # Strategy 1b: concept_id 直接匹配 node_id
        if concept_id and concept_id in all_node_ids:
            _apply_mastery(concept_id, calibrated)
            continue

        # Strategy 1c: concept_name 在 node_map 中名称匹配
        if node_map and concept_name:
            found = _find_node_id_by_concept_name(concept_name, node_map)
            if found and found in all_node_ids:
                _apply_mastery(found, calibrated)
                continue

        # Strategy 2: dimension → ability → boost confidence
        if dimension:
            for nid in all_node_ids:
                ab = get_node_primary_ability(nid)
                if ab == dimension:
                    entry = profile.concept_mastery.get(nid)
                    if entry and entry.confidence < 0.5:
                        cal_norm = max(0.0, min(1.0, calibrated / 100.0))
                        entry.mastery = round(max(0.0, min(1.0, 0.5 * cal_norm + 0.5 * entry.mastery)), 4)
                        entry.confidence = min(1.0, max(entry.confidence, 0.5))
                        entry.source = "merged"
                        entry.last_updated = now
                        merged_count += 1
                        if nid not in merged_ids:
                            merged_ids.append(nid)

    return merged_count, merged_ids


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
        # 优先使用 AgentState 中的 student_state_snapshot（含 update_state 注入的字段），
        # 若无则从持久化存储加载。允许 AgentState 注入空 learning_plan_v2 触发重新生成。
        state_snapshot = dict(state.get("student_state_snapshot") or {})
        if not state_snapshot and loaded_snapshot:
            state_snapshot = loaded_snapshot

        edges = _get_edges(graph_pipeline)

        # ── Step 1: Try resume v2 plan ────────────────────────────
        v2_plan_raw = state_snapshot.get("learning_plan_v2") or {}
        concept_mastery_raw = state_snapshot.get("concept_mastery") or {}

        # 自评后画像变了 → 强制重新生成学习路径，不续旧 plan
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
        has_fresh_self_assessment = bool(self_scores) and not bool(skip)

        if v2_plan_raw.get("steps") and not has_fresh_self_assessment:
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

        # ── Step 3.5: Compute context boost (错题本+临时提问) ─────
        wrong_question_book = state_snapshot.get("wrong_question_book") or []
        question_help_records = state_snapshot.get("question_help_records") or []
        ctx_boost = compute_context_boost(wrong_question_book, question_help_records)
        if ctx_boost:
            event_sink.emit(
                make_event(
                    "learning_plan.context_boost",
                    "learning_plan_generator",
                    message=f"错题/提问加成：{len(ctx_boost)} 个节点获得优先级提升。",
                    data={"boosted_nodes": list(ctx_boost.keys())[:10]},
                )
            )

        # ── 新鲜度加成：从未被规划过的节点获得优先级提升 ──
        previously_planned: set[str] = set()
        # 从历史 plan 中收集
        old_plan = state_snapshot.get("learning_plan_v2") or {}
        for step in old_plan.get("steps", []):
            for nid in step.get("node_ids", []):
                previously_planned.add(str(nid))
        # concept_mastery 中有记录的也视为已被规划过
        for nid in (concept_mastery_raw or {}):
            previously_planned.add(str(nid))
        fresh_boost = compute_freshness_boost(
            list(get_all_node_ids()), previously_planned,
            session_index=session_index,
        )
        if fresh_boost:
            event_sink.emit(
                make_event(
                    "learning_plan.freshness_boost",
                    "learning_plan_generator",
                    message=f"新鲜度加成：{len(fresh_boost)} 个从未规划的节点获得优先级提升。",
                    data={"fresh_nodes": list(fresh_boost.keys())[:10]},
                )
            )

        # ── Step 3.6: Feed assessment results into profile ──────
        # 将 assessment 产出的 calibrated concept_gaps 合并入 profile,
        # 让画像携带实测校准分而非仅靠自评/默认值。
        pipeline = getattr(runtime, "graph_rag_pipeline", None)
        node_map = dict(getattr(pipeline, "node_map", {}) or {})
        assessment_gaps = state.get("assessment_concept_gaps") or {}
        assessment_node_ids: list[str] = []
        if assessment_gaps:
            n_merged, merged_ids = _merge_assessment_gaps(profile, assessment_gaps, node_map=node_map)
            assessment_node_ids = merged_ids
            event_sink.emit(
                make_event(
                    "learning_plan.assessment_merged",
                    "learning_plan_generator",
                    message=f"已将测评校准分合并入画像（{n_merged}/{len(assessment_gaps)} 个概念）。",
                    data={"n_merged": n_merged, "total_gaps": len(assessment_gaps)},
                )
            )

        # ── Step 4: Generate learning plan ────────────────────────
        # 把 llm 传进去,新生成路径时用它给 step 取更自然的中文主题名
        # (续上路径时不调 LLM,见 _refresh_previous_plan)
        is_consolidation = state.get("continue_or_homework_choice") == "consolidate_weak"
        is_full_round = state.get("continue_or_homework_choice") == "start_full_round"
        plan = generate_learning_plan_v2(
            profile=profile,
            edges=edges,
            previous_plan=None,
            session_index=session_index,
            llm=llm,
            context_boost=ctx_boost,
            freshness_boost=fresh_boost,
            force_review=is_consolidation,
            include_all=is_full_round,
            assessment_node_ids=set(assessment_node_ids),
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

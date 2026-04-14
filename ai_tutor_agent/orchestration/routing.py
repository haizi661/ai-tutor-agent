from typing import Optional

from ..core.events import make_event
from ..core.graph_service import GraphQueryService
from ..core.ports import EventSink, NoopEventSink
from ..core.state import AgentState


def build_route_logic(
    pass_score: int,
    event_sink: Optional[EventSink] = None,
    knowledge_provider=None,
):
    sink = event_sink or NoopEventSink()

    def route_logic(state: AgentState) -> str:
        score = state.get("score", 0)
        has_legacy_shape = (
            "logic_score" not in state
            and "concept_score" not in state
            and "attempt_count" not in state
            and "is_correct_direction" not in state
            and "needs_hint" not in state
        )

        if has_legacy_shape:
            decision = "pass" if score >= pass_score else "fail"
            sink.emit(
                make_event(
                    "route.decision",
                    "router",
                    data={"decision": decision, "score": score, "pass_score": pass_score},
                )
            )
            return decision

        logic_score = state.get("logic_score", 0)
        concept_score = state.get("concept_score", 0)
        is_correct_direction = state.get("is_correct_direction", False)
        needs_hint = state.get("needs_hint", False)
        attempt_count = state.get("attempt_count", 0)
        difficulty_level = state.get("difficulty_level", 3)

        # 根据学生难度级别动态调整评分阈值
        # 低难度学生（初学者）给予更宽容的通过条件
        # 高难度学生（进阶者）保持严格标准
        logic_threshold = max(40, 55 - (3 - min(difficulty_level, 3)) * 8)
        concept_threshold = max(40, 55 - (3 - min(difficulty_level, 3)) * 8)
        remediate_margin = 20 + (difficulty_level - 3) * 5  # 难度越高，补救范围越宽
        max_reteach_attempts = max(2, 4 - difficulty_level + 3)  # 难度低时允许更多重学

        if score >= pass_score and logic_score >= logic_threshold and concept_score >= concept_threshold:
            decision = "pass"
        elif (
            needs_hint
            or (score >= pass_score - remediate_margin and is_correct_direction)
            or (attempt_count >= max_reteach_attempts and score >= pass_score - remediate_margin - 5)
        ):
            decision = "remediate"
        else:
            # 如果已经重教太多次（超过3次），强制进入补救而非继续重教
            if attempt_count >= 3:
                decision = "remediate"
            else:
                decision = "reteach"

        # ── 前驱节点缺口检测 ──
        # 当决策为 reteach 时，检查是否因前置知识缺口导致的卡点
        prerequisite_review_target = ""
        _course_nodes = getattr(knowledge_provider, "course_graph_nodes", None) or {}
        graph_anchor = str(state.get("graph_anchor_title") or "").strip()
        if decision == "reteach" and _course_nodes and graph_anchor:
            user_kg = state.get("user_knowledge_graph") or {}
            gqs = GraphQueryService(_course_nodes)
            review_target = gqs.recommend_review_target(graph_anchor, user_kg)
            if review_target:
                prerequisite_review_target = review_target
                sink.emit(
                    make_event(
                        "graph.prerequisite_review",
                        "router",
                        message=f"检测到前驱缺口，建议先复习：{review_target}",
                        data={
                            "review_target": review_target,
                            "current_node": graph_anchor,
                        },
                    )
                )

        sink.emit(
            make_event(
                "route.decision",
                "router",
                data={
                    "decision": decision,
                    "score": score,
                    "logic_score": logic_score,
                    "concept_score": concept_score,
                    "is_correct_direction": is_correct_direction,
                    "needs_hint": needs_hint,
                    "attempt_count": attempt_count,
                    "pass_score": pass_score,
                    "difficulty_level": difficulty_level,
                    "prerequisite_review_target": prerequisite_review_target,
                    "dynamic_thresholds": {
                        "logic": logic_threshold,
                        "concept": concept_threshold,
                        "remediate_margin": remediate_margin,
                    },
                },
            )
        )

        return decision

    return route_logic

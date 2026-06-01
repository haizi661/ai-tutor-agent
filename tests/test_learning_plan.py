"""Tests for the learning plan builder and learning plan integration."""
from __future__ import annotations

import pytest

from ai_tutor_agent.core.learning_plan_builder import (
    build_learning_plan,
    find_next_node_in_step,
    is_step_completed,
    find_current_step_progress,
    _compute_topo_layers,
)


# ── Minimal graph fixtures ──

def _make_node(node_id: str, name: str, chapter: str = "", prerequisite_nodes: str = "", **extra) -> dict:
    node = {
        "node_id": node_id,
        "name": name,
        "chapter": chapter,
        "prerequisite_nodes": prerequisite_nodes,
        "source_type": "",
    }
    node.update(extra)
    return node


def _make_edge(source: str, target: str, relation: str = "prerequisite_of") -> dict:
    return {"source": source, "target": target, "relation": relation}


def _linear_graph():
    """KM001 -> KM002 -> KM003"""
    nodes = [
        _make_node("KM001", "基础概念", "第一章"),
        _make_node("KM002", "数学模型", "第二章", prerequisite_nodes="KM001"),
        _make_node("KM003", "时域分析", "第三章", prerequisite_nodes="KM002"),
    ]
    edges = [
        _make_edge("KM001", "KM002"),
        _make_edge("KM002", "KM003"),
    ]
    node_map = {n["node_id"]: n for n in nodes}
    return node_map, edges


def _diamond_graph():
    """KM001 -> KM002, KM001 -> KM003, KM002 -> KM004, KM003 -> KM004"""
    nodes = [
        _make_node("KM001", "基础", "第一章"),
        _make_node("KM002", "分支A", "第二章", prerequisite_nodes="KM001"),
        _make_node("KM003", "分支B", "第二章", prerequisite_nodes="KM001"),
        _make_node("KM004", "综合", "第三章", prerequisite_nodes="KM002,KM003"),
    ]
    edges = [
        _make_edge("KM001", "KM002"),
        _make_edge("KM001", "KM003"),
        _make_edge("KM002", "KM004"),
        _make_edge("KM003", "KM004"),
    ]
    node_map = {n["node_id"]: n for n in nodes}
    return node_map, edges


# ── Topology tests ──

def test_topo_layers_linear():
    node_map, edges = _linear_graph()
    layers = _compute_topo_layers(node_map, edges)
    assert layers["KM001"] == 0
    assert layers["KM002"] == 1
    assert layers["KM003"] == 2


def test_topo_layers_diamond():
    node_map, edges = _diamond_graph()
    layers = _compute_topo_layers(node_map, edges)
    assert layers["KM001"] == 0
    assert layers["KM002"] == 1
    assert layers["KM003"] == 1
    assert layers["KM004"] == 2


# ── Plan generation tests ──

def test_linear_graph_produces_3_steps():
    node_map, edges = _linear_graph()
    plan = build_learning_plan(node_map=node_map, edges=edges)
    assert len(plan) == 3
    assert plan[0]["node_ids"] == ["KM001"]
    assert plan[1]["node_ids"] == ["KM002"]
    assert plan[2]["node_ids"] == ["KM003"]


def test_linear_graph_first_step_is_in_progress():
    node_map, edges = _linear_graph()
    plan = build_learning_plan(node_map=node_map, edges=edges)
    assert plan[0]["status"] == "in_progress"
    assert plan[1]["status"] == "pending"
    assert plan[2]["status"] == "pending"


def test_diamond_graph_groups_same_layer():
    node_map, edges = _diamond_graph()
    plan = build_learning_plan(node_map=node_map, edges=edges)
    # Layer 0: KM001, Layer 1: KM002+KM003, Layer 2: KM004
    assert len(plan) == 3
    assert plan[0]["node_ids"] == ["KM001"]
    assert set(plan[1]["node_ids"]) == {"KM002", "KM003"}
    assert plan[2]["node_ids"] == ["KM004"]


def test_mastered_nodes_are_skipped():
    node_map, edges = _linear_graph()
    knowledge_graph = {
        "KM001": {"status": "mastered", "score": 85},
    }
    plan = build_learning_plan(
        node_map=node_map,
        edges=edges,
        knowledge_graph=knowledge_graph,
    )
    # KM001 is mastered, so only KM002 and KM003 remain
    all_node_ids = [nid for step in plan for nid in step["node_ids"]]
    assert "KM001" not in all_node_ids
    assert "KM002" in all_node_ids
    assert "KM003" in all_node_ids


def test_concept_gaps_affect_priority():
    node_map, edges = _linear_graph()
    concept_gaps = {
        "数学模型": {"concept_id": "KM002", "calibrated": 20},
    }
    plan = build_learning_plan(
        node_map=node_map,
        edges=edges,
        concept_gaps=concept_gaps,
    )
    # KM002 should have a reason mentioning low score
    km002_step = next(s for s in plan if "KM002" in s["node_ids"])
    assert "较低" in km002_step["reason"] or "20" in km002_step["reason"]


def test_difficulty_level_affects_grouping():
    """Low difficulty (1) should group fewer nodes per step."""
    # Create a graph with 4 nodes in the same layer
    nodes = [
        _make_node("KM001", "基础", "第一章"),
        _make_node("KM002", "进阶A", "第二章", prerequisite_nodes="KM001"),
        _make_node("KM003", "进阶B", "第二章", prerequisite_nodes="KM001"),
        _make_node("KM004", "进阶C", "第二章", prerequisite_nodes="KM001"),
    ]
    edges = [
        _make_edge("KM001", "KM002"),
        _make_edge("KM001", "KM003"),
        _make_edge("KM001", "KM004"),
    ]
    node_map = {n["node_id"]: n for n in nodes}

    plan_fast = build_learning_plan(node_map=node_map, edges=edges, difficulty_level=5)
    plan_slow = build_learning_plan(node_map=node_map, edges=edges, difficulty_level=1)

    # Fast learner: fewer steps (more nodes per step)
    # Slow learner: more steps (fewer nodes per step)
    assert len(plan_fast) <= len(plan_slow)


def test_empty_graph_returns_empty_plan():
    plan = build_learning_plan(node_map={}, edges=[])
    assert plan == []


def test_all_mastered_returns_empty_plan():
    node_map, edges = _linear_graph()
    knowledge_graph = {
        "KM001": {"status": "mastered"},
        "KM002": {"status": "mastered"},
        "KM003": {"status": "mastered"},
    }
    plan = build_learning_plan(
        node_map=node_map,
        edges=edges,
        knowledge_graph=knowledge_graph,
    )
    assert plan == []


# ── Step navigation tests ──

def test_find_next_node_in_step():
    step = {"node_ids": ["KM001", "KM002", "KM003"]}
    visited = {"KM001"}
    assert find_next_node_in_step(step, visited, "KM001") == "KM002"


def test_find_next_node_in_step_skips_current():
    step = {"node_ids": ["KM001", "KM002", "KM003"]}
    visited = set()
    assert find_next_node_in_step(step, visited, "KM002") == "KM001"


def test_find_next_node_in_step_returns_empty_when_all_visited():
    step = {"node_ids": ["KM001", "KM002"]}
    visited = {"KM001", "KM002"}
    assert find_next_node_in_step(step, visited, "") == ""


def test_is_step_completed():
    step = {"node_ids": ["KM001", "KM002"]}
    assert is_step_completed(step, {"KM001", "KM002"}) is True
    assert is_step_completed(step, {"KM001"}) is False


def test_find_current_step_progress():
    plan = [
        {"node_ids": ["KM001"], "status": "completed"},
        {"node_ids": ["KM002", "KM003", "KM004"], "status": "in_progress"},
    ]
    visited = {"KM001", "KM002"}
    step_idx, completed, total = find_current_step_progress(plan, visited)
    assert step_idx == 1
    assert completed == 1
    assert total == 3


def test_find_current_step_progress_all_done():
    plan = [
        {"node_ids": ["KM001"], "status": "completed"},
        {"node_ids": ["KM002"], "status": "completed"},
    ]
    visited = {"KM001", "KM002"}
    step_idx, completed, total = find_current_step_progress(plan, visited)
    assert step_idx == 2  # past the end


# ── Prerequisite chain test ──

def test_target_node_pruning():
    """When target is KM003, only KM001 and KM002 should appear as prerequisites."""
    node_map, edges = _linear_graph()
    plan = build_learning_plan(
        node_map=node_map,
        edges=edges,
        target_node_id="KM003",
    )
    all_node_ids = [nid for step in plan for nid in step["node_ids"]]
    assert "KM003" in all_node_ids
    assert "KM002" in all_node_ids
    assert "KM001" in all_node_ids


# ── Integration: initial_node_selector with learning plan ──

def test_initial_node_selector_picks_from_learning_plan():
    from unittest.mock import MagicMock
    from ai_tutor_agent.nodes.initial_node_selector import build_initial_node_selector_node
    from ai_tutor_agent.core.ports import RuntimeContext
    from ai_tutor_agent.knowledge_map.student_state import StudentStateStore

    node_map, edges = _linear_graph()
    graph = MagicMock()
    graph.node_map = node_map
    graph.edges = edges

    sink = MagicMock()
    sink.emit = MagicMock()
    runtime = MagicMock(spec=RuntimeContext)
    runtime.event_sink = sink
    runtime.graph_rag_pipeline = graph
    runtime.student_state_store = MagicMock(spec=StudentStateStore)

    node_fn = build_initial_node_selector_node(runtime)
    state = {
        "student_id": "test",
        "student_state_snapshot": {},
        "learning_plan": [
            {"step_index": 0, "node_ids": ["KM001", "KM002"], "node_names": ["基础", "数学"]},
            {"step_index": 1, "node_ids": ["KM003"], "node_names": ["时域"]},
        ],
        "learning_plan_current_step": 0,
    }
    result = node_fn(state)
    assert result["current_node_id"] == "KM001"


# ── Integration: next_node_planner with learning plan ──

def test_next_node_planner_follows_learning_plan_steps():
    from unittest.mock import MagicMock
    from ai_tutor_agent.nodes.next_node_planner import build_next_node_planner_node
    from ai_tutor_agent.core.ports import RuntimeContext
    from ai_tutor_agent.knowledge_map.student_state import StudentStateStore

    node_map, edges = _linear_graph()
    graph = MagicMock()
    graph.node_map = node_map
    graph.edges = edges

    sink = MagicMock()
    sink.emit = MagicMock()
    runtime = MagicMock(spec=RuntimeContext)
    runtime.event_sink = sink
    runtime.graph_rag_pipeline = graph
    runtime.student_state_store = MagicMock(spec=StudentStateStore)

    # Mock load_student_state_snapshot to return a snapshot with visited KM001
    snapshot = {
        "visited_nodes": ["KM001"],
        "knowledge_graph": {"KM001": {"status": "mastered", "score": 80}},
    }
    runtime.student_state_store.load.return_value = MagicMock(
        to_dict=lambda: snapshot,
        learning_plan=[
            {"step_index": 0, "node_ids": ["KM001", "KM002"], "status": "in_progress"},
            {"step_index": 1, "node_ids": ["KM003"], "status": "pending"},
        ],
        learning_plan_current_step=0,
    )

    node_fn = build_next_node_planner_node(runtime)
    state = {
        "student_id": "test",
        "current_node_id": "KM001",
        "student_state_snapshot": snapshot,
        "learning_plan": [
            {"step_index": 0, "node_ids": ["KM001", "KM002"], "status": "in_progress"},
            {"step_index": 1, "node_ids": ["KM003"], "status": "pending"},
        ],
        "learning_plan_current_step": 0,
    }
    result = node_fn(state)
    # KM001 is visited, next should be KM002 (same step)
    assert result["next_node_candidate_id"] == "KM002"


# ── Topology-based plan builder tests ──

from ai_tutor_agent.core.learning_plan_builder import (
    _determine_mastered_from_assessment,
)


def _larger_graph():
    """10 nodes across 3 chapters with prerequisite chains."""
    nodes = [
        _make_node("KM001", "自动控制的一般概念", "第一章"),
        _make_node("KM002", "自动控制的基本原理", "第一章"),
        _make_node("KM003", "拉普拉斯变换", "第二章"),
        _make_node("KM004", "传递函数", "第二章"),
        _make_node("KM005", "方框图化简", "第二章"),
        _make_node("KM006", "时域分析基础", "第三章"),
        _make_node("KM007", "一阶系统响应", "第三章"),
        _make_node("KM008", "二阶系统响应", "第三章"),
        _make_node("KM009", "稳定性判据", "第三章"),
        _make_node("KM010", "稳态误差", "第三章"),
    ]
    edges = [
        _make_edge("KM001", "KM002"),
        _make_edge("KM002", "KM003"),
        _make_edge("KM003", "KM004"),
        _make_edge("KM004", "KM005"),
        _make_edge("KM004", "KM006"),
        _make_edge("KM006", "KM007"),
        _make_edge("KM006", "KM008"),
        _make_edge("KM008", "KM009"),
        _make_edge("KM009", "KM010"),
    ]
    node_map = {n["node_id"]: n for n in nodes}
    return node_map, edges


class TestDetermineMastered:
    def test_knowledge_graph_mastered(self):
        node_map, _ = _linear_graph()
        kg = {"KM001": {"status": "mastered"}}
        mastered = _determine_mastered_from_assessment(node_map, {}, kg)
        assert "KM001" in mastered

    def test_assessment_high_calibrated_mastered(self):
        node_map, _ = _linear_graph()
        gaps = {"基础概念": {"concept_id": "KM001", "calibrated": 75}}
        mastered = _determine_mastered_from_assessment(node_map, gaps, {})
        assert "KM001" in mastered

    def test_assessment_low_calibrated_not_mastered(self):
        node_map, _ = _linear_graph()
        gaps = {"基础概念": {"concept_id": "KM001", "calibrated": 40}}
        mastered = _determine_mastered_from_assessment(node_map, gaps, {})
        assert "KM001" not in mastered

    def test_assessment_threshold_boundary(self):
        node_map, _ = _linear_graph()
        gaps = {"基础概念": {"concept_id": "KM001", "calibrated": 60}}
        mastered = _determine_mastered_from_assessment(node_map, gaps, {})
        assert "KM001" in mastered

    def test_name_matching_fallback(self):
        node_map, _ = _linear_graph()
        gaps = {"基础概念": {"calibrated": 80, "concept_title": "基础概念"}}
        mastered = _determine_mastered_from_assessment(node_map, gaps, {})
        assert "KM001" in mastered


class TestBuildLearningPlan:
    def test_output_shape(self):
        node_map, edges = _linear_graph()
        plan = build_learning_plan(node_map=node_map, edges=edges)
        assert len(plan) >= 1
        step = plan[0]
        for key in ("step_index", "step_name", "node_ids", "node_names", "status", "reason", "estimated_difficulty", "prerequisite_steps"):
            assert key in step

    def test_first_step_in_progress(self):
        node_map, edges = _linear_graph()
        plan = build_learning_plan(node_map=node_map, edges=edges)
        assert plan[0]["status"] == "in_progress"
        for step in plan[1:]:
            assert step["status"] == "pending"

    def test_topological_ordering(self):
        node_map, edges = _larger_graph()
        plan = build_learning_plan(node_map=node_map, edges=edges)
        all_ids = [nid for step in plan for nid in step["node_ids"]]
        assert all_ids.index("KM001") < all_ids.index("KM002")
        assert all_ids.index("KM006") < all_ids.index("KM007")

    def test_mastered_nodes_skipped(self):
        node_map, edges = _linear_graph()
        kg = {"KM001": {"status": "mastered"}}
        plan = build_learning_plan(node_map=node_map, edges=edges, knowledge_graph=kg)
        all_ids = [nid for step in plan for nid in step["node_ids"]]
        assert "KM001" not in all_ids
        assert all_ids[0] == "KM002"

    def test_assessment_mastered_skipped(self):
        node_map, edges = _linear_graph()
        gaps = {"基础概念": {"concept_id": "KM001", "calibrated": 80}}
        plan = build_learning_plan(node_map=node_map, edges=edges, concept_gaps=gaps)
        all_ids = [nid for step in plan for nid in step["node_ids"]]
        assert "KM001" not in all_ids

    def test_branch_priority_low_calibrated_first(self):
        node_map, edges = _diamond_graph()
        kg = {"KM001": {"status": "mastered"}}
        # Both below 60 threshold so neither is mastered,
        # but KM003 has lower calibrated → higher priority
        gaps = {
            "分支A": {"concept_id": "KM002", "calibrated": 55},
            "分支B": {"concept_id": "KM003", "calibrated": 25},
        }
        plan = build_learning_plan(node_map=node_map, edges=edges, knowledge_graph=kg, concept_gaps=gaps)
        all_ids = [nid for step in plan for nid in step["node_ids"]]
        assert all_ids.index("KM003") < all_ids.index("KM002")

    def test_target_pruning(self):
        node_map, edges = _larger_graph()
        plan = build_learning_plan(node_map=node_map, edges=edges, target_node_id="KM007")
        all_ids = [nid for step in plan for nid in step["node_ids"]]
        assert "KM001" in all_ids
        assert "KM007" in all_ids
        assert "KM008" not in all_ids

    def test_empty_when_all_mastered(self):
        node_map, edges = _linear_graph()
        kg = {nid: {"status": "mastered"} for nid in node_map}
        plan = build_learning_plan(node_map=node_map, edges=edges, knowledge_graph=kg)
        assert plan == []

    def test_empty_graph_returns_empty(self):
        plan = build_learning_plan(node_map={}, edges=[])
        assert plan == []

    def test_same_chapter_grouped(self):
        nodes = [
            _make_node("KM001", "概念A", "第一章"),
            _make_node("KM002", "概念B", "第一章"),
            _make_node("KM003", "概念C", "第一章"),
        ]
        node_map = {n["node_id"]: n for n in nodes}
        plan = build_learning_plan(node_map=node_map, edges=[])
        assert len(plan) == 1
        assert len(plan[0]["node_ids"]) == 3

    def test_difficulty_affects_step_size(self):
        nodes = [_make_node(f"KM{i:03d}", f"Node{i}", "第一章") for i in range(1, 7)]
        node_map = {n["node_id"]: n for n in nodes}
        plan_slow = build_learning_plan(node_map=node_map, edges=[], difficulty_level=1)
        plan_fast = build_learning_plan(node_map=node_map, edges=[], difficulty_level=5)
        assert len(plan_slow) >= len(plan_fast)

    def test_step_size_is_capped_at_three_nodes_even_for_fast_learners(self):
        nodes = [_make_node(f"KM{i:03d}", f"Node{i}", "第一章") for i in range(1, 8)]
        node_map = {n["node_id"]: n for n in nodes}

        plan = build_learning_plan(node_map=node_map, edges=[], difficulty_level=5)

        assert max(len(step["node_ids"]) for step in plan) <= 3

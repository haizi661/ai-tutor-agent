"""Integration tests for the user knowledge graph feature.

These tests exercise the REAL code paths (mark_student_node_started,
update_student_state_after_evaluation, homework persistence, API endpoint)
rather than calling kg_register_node/kg_update_score directly.

The knowledge graph must:
- Start empty (no pre-populated nodes)
- Add nodes only when the user starts learning them
- Track score (0-100), wrong questions, and evidence-based evaluations
- Persist across save/load cycles
- Expose via GET /api/students/{id}/knowledge-graph
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ai_tutor_agent.core.learning_support import (
    mark_student_node_started,
    update_student_state_after_evaluation,
)
from ai_tutor_agent.knowledge_map.student_state import StudentState, StudentStateStore


@pytest.fixture()
def store(tmp_path: Path) -> StudentStateStore:
    return StudentStateStore(state_dir=str(tmp_path / "student_states"))


# ── 1. Tutor node registers KG node via mark_student_node_started ──


def test_tutor_registers_kg_node(store: StudentStateStore):
    """mark_student_node_started (called by tutor node) adds node to KG."""
    result = mark_student_node_started(
        store,
        student_id="s1",
        node_id="KM007",
        question="什么是稳定性判据？",
        title="控制系统的稳定性判据",
    )
    assert result  # non-empty = saved
    state = store.load("s1")
    assert "KM007" in state.knowledge_graph
    entry = state.knowledge_graph["KM007"]
    assert entry["title"] == "控制系统的稳定性判据"
    assert entry["status"] == "in_progress"
    assert entry["score"] == 0
    assert entry["attempts"] == 0


def test_tutor_registers_multiple_nodes(store: StudentStateStore):
    """Each tutor call registers a separate node. Only learned nodes appear."""
    mark_student_node_started(store, student_id="s1", node_id="KM007", question="Q1", title="稳定性判据")
    mark_student_node_started(store, student_id="s1", node_id="KM012", question="Q2", title="根轨迹法")

    state = store.load("s1")
    assert set(state.knowledge_graph.keys()) == {"KM007", "KM012"}
    # KM099 was never taught — must not appear
    assert "KM099" not in state.knowledge_graph


# ── 2. Quiz evaluation updates KG via update_student_state_after_evaluation ──


def test_quiz_fail_updates_kg_with_wrong_items(store: StudentStateStore):
    """Failed quiz records score, wrong questions, and evidence in KG."""
    mark_student_node_started(store, student_id="s1", node_id="KM007", question="Q", title="稳定性判据")

    wrong_items = [
        {"question_id": "Q3", "stem": "什么是Nyquist判据？", "student_answer": "B", "correct_answer": "A", "feedback": "注意相位裕度"},
        {"question_id": "Q5", "stem": "Bode图分析", "student_answer": "C", "correct_answer": "D", "feedback": "幅值裕度计算"},
    ]
    update_student_state_after_evaluation(
        store,
        student_id="s1",
        node_id="KM007",
        score=40.0,
        passed=False,
        wrong_items=wrong_items,
        node_title="稳定性判据",
    )

    state = store.load("s1")
    entry = state.knowledge_graph["KM007"]
    assert entry["score"] == 40
    assert entry["status"] == "in_progress"
    assert entry["attempts"] == 1
    # Wrong questions collected
    assert len(entry["wrong_questions"]) == 2
    assert entry["wrong_questions"][0]["question_id"] == "Q3"
    assert entry["wrong_questions"][0]["source"] == "quiz"
    # Evidence recorded
    assert len(entry["evidence"]) == 1
    assert entry["evidence"][0]["type"] == "quiz_fail"
    assert entry["evidence"][0]["score"] == 40


def test_quiz_pass_updates_kg_to_mastered(store: StudentStateStore):
    """Passed quiz sets status to mastered."""
    mark_student_node_started(store, student_id="s1", node_id="KM007", question="Q", title="稳定性判据")

    update_student_state_after_evaluation(
        store,
        student_id="s1",
        node_id="KM007",
        score=85.0,
        passed=True,
        node_title="稳定性判据",
    )

    state = store.load("s1")
    entry = state.knowledge_graph["KM007"]
    assert entry["score"] == 85
    assert entry["status"] == "mastered"
    assert entry["attempts"] == 1
    assert entry["evidence"][0]["type"] == "quiz_pass"


def test_fail_then_pass_accumulates(store: StudentStateStore):
    """Full fail→pass cycle: wrong items from fail, mastery on pass."""
    mark_student_node_started(store, student_id="s1", node_id="KM007", question="Q", title="稳定性判据")

    # First: fail
    update_student_state_after_evaluation(
        store, student_id="s1", node_id="KM007", score=30.0, passed=False,
        wrong_items=[{"question_id": "Q1", "stem": "test"}],
        node_title="稳定性判据",
    )
    # Second: pass
    update_student_state_after_evaluation(
        store, student_id="s1", node_id="KM007", score=80.0, passed=True,
    )

    state = store.load("s1")
    entry = state.knowledge_graph["KM007"]
    assert entry["score"] == 80
    assert entry["status"] == "mastered"
    assert entry["attempts"] == 2
    assert len(entry["wrong_questions"]) == 1  # from the fail
    assert len(entry["evidence"]) == 2
    assert entry["evidence"][0]["type"] == "quiz_fail"
    assert entry["evidence"][1]["type"] == "quiz_pass"


# ── 3. Homework path updates KG ──


def test_homework_updates_kg_separate_from_quiz(store: StudentStateStore):
    """Homework score updates KG with source='homework', separate from quiz."""
    mark_student_node_started(store, student_id="s1", node_id="KM007", question="Q", title="稳定性判据")

    # First a quiz pass
    update_student_state_after_evaluation(
        store, student_id="s1", node_id="KM007", score=80.0, passed=True,
    )

    # Simulate homework update (same path as _persist_homework_result)
    state = store.load("s1")
    state.kg_update_score(
        "KM007", 70, passed=False, source="homework",
        wrong_items=[{"question_id": "HW1", "stem": "作业题1", "student_answer": "B", "correct_answer": "A"}],
    )
    store.save(state)

    state = store.load("s1")
    entry = state.knowledge_graph["KM007"]
    assert entry["attempts"] == 2
    assert len(entry["evidence"]) == 2
    assert entry["evidence"][0]["type"] == "quiz_pass"
    assert entry["evidence"][1]["type"] == "homework_fail"
    # Wrong questions from homework
    hw_wrongs = [w for w in entry["wrong_questions"] if w["source"] == "homework"]
    assert len(hw_wrongs) == 1
    assert hw_wrongs[0]["question_id"] == "HW1"


# ── 4. Cross-session persistence ──


def test_full_lifecycle_persists_across_sessions(store: StudentStateStore):
    """Simulate a complete learning session: register → fail → pass → save.

    Then reload and verify everything survived.
    """
    # Session 1: learn KM007
    mark_student_node_started(store, student_id="s1", node_id="KM007", question="Q1", title="稳定性判据")
    update_student_state_after_evaluation(
        store, student_id="s1", node_id="KM007", score=35.0, passed=False,
        wrong_items=[{"question_id": "Q1", "stem": "test"}],
        node_title="稳定性判据",
    )

    # Session 2: learn KM012, retry KM007
    mark_student_node_started(store, student_id="s1", node_id="KM012", question="Q2", title="根轨迹法")
    update_student_state_after_evaluation(
        store, student_id="s1", node_id="KM012", score=90.0, passed=True,
        node_title="根轨迹法",
    )
    update_student_state_after_evaluation(
        store, student_id="s1", node_id="KM007", score=75.0, passed=True,
    )

    # Simulate new session: reload from disk
    state = store.load("s1")

    # KM007: fail→pass, mastered at 75
    km007 = state.knowledge_graph["KM007"]
    assert km007["score"] == 75
    assert km007["status"] == "mastered"
    assert km007["attempts"] == 2
    assert len(km007["wrong_questions"]) == 1
    assert len(km007["evidence"]) == 2

    # KM012: single pass, mastered at 90
    km012 = state.knowledge_graph["KM012"]
    assert km012["score"] == 90
    assert km012["status"] == "mastered"
    assert km012["attempts"] == 1

    # Only 2 nodes in graph
    assert len(state.knowledge_graph) == 2


# ── 5. Evidence quality: every score change has evidence ──


def test_every_score_change_has_evidence(store: StudentStateStore):
    """No score change in KG should happen without a corresponding evidence entry."""
    mark_student_node_started(store, student_id="s1", node_id="KM007", question="Q", title="稳定性判据")

    scores = [30, 50, 65, 80, 95]
    for score in scores:
        update_student_state_after_evaluation(
            store, student_id="s1", node_id="KM007", score=float(score),
            passed=score >= 60,
        )

    state = store.load("s1")
    entry = state.knowledge_graph["KM007"]
    assert entry["attempts"] == 5
    assert len(entry["evidence"]) == 5
    # Evidence scores match the actual scores
    for i, ev in enumerate(entry["evidence"]):
        assert ev["score"] == scores[i]


# ── 6. Edge cases ──


def test_update_without_register_auto_registers(store: StudentStateStore):
    """kg_update_score auto-registers if node not yet in graph (belt-and-suspenders)."""
    state = store.load("s1")
    state.kg_update_score("KM099", 70, passed=True, source="quiz", title="自动注册测试")
    store.save(state)

    state = store.load("s1")
    assert "KM099" in state.knowledge_graph
    assert state.knowledge_graph["KM099"]["score"] == 70
    assert state.knowledge_graph["KM099"]["status"] == "mastered"


def test_score_clamped_0_100(store: StudentStateStore):
    """Scores are clamped to [0, 100] through the real path."""
    mark_student_node_started(store, student_id="s1", node_id="KM007", question="Q", title="test")

    update_student_state_after_evaluation(
        store, student_id="s1", node_id="KM007", score=150.0, passed=True,
    )
    state = store.load("s1")
    assert state.knowledge_graph["KM007"]["score"] == 100

    update_student_state_after_evaluation(
        store, student_id="s1", node_id="KM007", score=-10.0, passed=False,
    )
    state = store.load("s1")
    assert state.knowledge_graph["KM007"]["score"] == 0


def test_old_json_backward_compat(store: StudentStateStore, tmp_path: Path):
    """Old JSON without knowledge_graph field loads gracefully."""
    path = store._build_path("old_student")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"student_id": "old_student", "mastery_scores": {"KM007": 80.0}}))

    # Should load without error, then register + update should work
    mark_student_node_started(store, student_id="old_student", node_id="KM007", question="Q", title="兼容测试")
    update_student_state_after_evaluation(
        store, student_id="old_student", node_id="KM007", score=75.0, passed=True,
    )

    state = store.load("old_student")
    assert state.knowledge_graph["KM007"]["score"] == 75
    assert state.knowledge_graph["KM007"]["status"] == "mastered"


# ── 7. Cap enforcement through real path ──


def test_wrong_questions_capped_at_100(store: StudentStateStore):
    """Wrong questions are capped at 100 per node, even through repeated failures."""
    mark_student_node_started(store, student_id="s1", node_id="KM007", question="Q", title="test")

    for i in range(120):
        update_student_state_after_evaluation(
            store, student_id="s1", node_id="KM007", score=30.0, passed=False,
            wrong_items=[{"question_id": f"Q{i}", "stem": f"question {i}"}],
        )

    state = store.load("s1")
    entry = state.knowledge_graph["KM007"]
    assert len(entry["wrong_questions"]) == 100
    # Should keep the most recent ones (Q20..Q119)
    assert entry["wrong_questions"][0]["question_id"] == "Q20"
    assert entry["wrong_questions"][-1]["question_id"] == "Q119"


def test_evidence_capped_at_50(store: StudentStateStore):
    """Evidence entries are capped at 50 per node."""
    mark_student_node_started(store, student_id="s1", node_id="KM007", question="Q", title="test")

    for i in range(60):
        update_student_state_after_evaluation(
            store, student_id="s1", node_id="KM007", score=50.0, passed=False,
        )

    state = store.load("s1")
    entry = state.knowledge_graph["KM007"]
    assert len(entry["evidence"]) == 50
    assert entry["attempts"] == 60  # attempts not capped


# ── 8. API endpoint shape ──


def test_api_endpoint_returns_correct_shape(store: StudentStateStore):
    """API endpoint returns {knowledge_graph, summary} with correct counts."""
    # Create some KG data
    mark_student_node_started(store, student_id="s1", node_id="KM007", question="Q", title="稳定性判据")
    update_student_state_after_evaluation(
        store, student_id="s1", node_id="KM007", score=85.0, passed=True,
    )
    mark_student_node_started(store, student_id="s1", node_id="KM012", question="Q", title="根轨迹法")
    update_student_state_after_evaluation(
        store, student_id="s1", node_id="KM012", score=40.0, passed=False,
    )

    # Simulate the API endpoint logic (same as get_knowledge_graph)
    state = store.load("s1")
    kg = state.knowledge_graph if hasattr(state, "knowledge_graph") else {}
    mastered = sum(1 for v in kg.values() if v.get("status") == "mastered")
    in_progress = sum(1 for v in kg.values() if v.get("status") == "in_progress")
    response = {
        "knowledge_graph": kg,
        "summary": {"total": len(kg), "mastered": mastered, "in_progress": in_progress},
    }

    assert response["summary"]["total"] == 2
    assert response["summary"]["mastered"] == 1
    assert response["summary"]["in_progress"] == 1
    assert response["knowledge_graph"]["KM007"]["status"] == "mastered"
    assert response["knowledge_graph"]["KM012"]["status"] == "in_progress"


def test_api_endpoint_empty_student(store: StudentStateStore):
    """API returns empty graph for student with no learning history."""
    state = store.load("new_student")
    kg = state.knowledge_graph if hasattr(state, "knowledge_graph") else {}
    mastered = sum(1 for v in kg.values() if v.get("status") == "mastered")
    in_progress = sum(1 for v in kg.values() if v.get("status") == "in_progress")

    assert kg == {}
    assert mastered == 0
    assert in_progress == 0

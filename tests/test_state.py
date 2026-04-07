from ai_tutor_agent.core.state import build_initial_state


def test_build_initial_state():
    state = build_initial_state("控制理论")
    assert state["current_topic"] == "控制理论"
    assert state["proposed_topic"] == ""
    assert state["score"] == 0
    assert state["logic_score"] == 0
    assert state["concept_score"] == 0
    assert state["feedback"] == ""
    assert state["assessment_radar"] == {}
    assert state["attempt_count"] == 0
    assert state["score_history"] == []
    assert state["tester_question_type"] == ""
    assert state["tester_question_template"] == ""
    assert state["needs_hint"] is False
    assert state["coach_content"] == ""
    assert state["interrupt_query"] == ""
    assert state["resume_tester"] is False
    assert state["conversation_history"] == []

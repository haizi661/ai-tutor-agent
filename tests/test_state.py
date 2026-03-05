from ai_tutor_agent.state import build_initial_state


def test_build_initial_state():
    state = build_initial_state("控制理论")
    assert state["current_topic"] == "控制理论"
    assert state["score"] == 0
    assert state["logic_score"] == 0
    assert state["concept_score"] == 0
    assert state["feedback"] == ""

from ai_tutor_agent.orchestration.workflow import route_after_evaluator
from ai_tutor_agent.core.ports import BufferedEventSink
from ai_tutor_agent.orchestration.routing import build_route_logic


def test_route_logic_pass():
    route_logic = build_route_logic(80)
    assert route_logic({"score": 80}) == "pass"


def test_route_logic_fail_for_legacy_shape():
    route_logic = build_route_logic(80)
    assert route_logic({"score": 79}) == "fail"


def test_route_logic_returns_remediate_when_hint_is_needed():
    route_logic = build_route_logic(80)
    decision = route_logic(
        {
            "score": 50,
            "logic_score": 52,
            "concept_score": 48,
            "attempt_count": 1,
            "is_correct_direction": True,
            "needs_hint": True,
        }
    )
    assert decision == "remediate"


def test_route_logic_returns_reteach_when_score_is_too_low_without_hint():
    route_logic = build_route_logic(80)
    decision = route_logic(
        {
            "score": 30,
            "logic_score": 35,
            "concept_score": 30,
            "attempt_count": 0,
            "is_correct_direction": False,
            "needs_hint": False,
        }
    )
    assert decision == "reteach"


def test_route_logic_emits_decision_event():
    sink = BufferedEventSink()
    route_logic = build_route_logic(80, sink)
    decision = route_logic({"score": 79})
    assert decision == "fail"
    assert len(sink.events) == 1
    assert sink.events[0].type == "route.decision"
    assert sink.events[0].data["score"] == 79


def test_route_after_evaluator_maps_remediate_to_coach_and_emits_route_event():
    sink = BufferedEventSink()
    destination = route_after_evaluator(
        {
            "score": 55,
            "logic_score": 58,
            "concept_score": 54,
            "attempt_count": 1,
            "is_correct_direction": True,
            "needs_hint": True,
        },
        80,
        sink,
    )

    assert destination == "coach"
    assert sink.events[0].type == "route.decision"
    assert sink.events[0].data["decision"] == "remediate"

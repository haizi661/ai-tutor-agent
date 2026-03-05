from ai_tutor_agent.ports import BufferedEventSink
from ai_tutor_agent.routing import build_route_logic


def test_route_logic_pass():
    route_logic = build_route_logic(80)
    assert route_logic({"score": 80}) == "pass"


def test_route_logic_fail():
    route_logic = build_route_logic(80)
    assert route_logic({"score": 79}) == "fail"


def test_route_logic_emits_decision_event():
    sink = BufferedEventSink()
    route_logic = build_route_logic(80, sink)
    decision = route_logic({"score": 79})
    assert decision == "fail"
    assert len(sink.events) == 1
    assert sink.events[0].type == "route.decision"
    assert sink.events[0].data["score"] == 79

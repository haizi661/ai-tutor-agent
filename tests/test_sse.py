import json

from ai_tutor_agent.events import make_event
from ai_tutor_agent.sse import format_sse


def test_format_sse_uses_event_name_and_json_payload():
    event = make_event(
        "node.start",
        "tutor",
        message="started",
        data={"topic": "控制理论"},
    )

    payload = format_sse(event)
    lines = payload.strip().splitlines()

    assert lines[0] == "event: node.start"
    assert lines[1].startswith("data: ")

    raw_data = lines[1].removeprefix("data: ")
    parsed = json.loads(raw_data)
    assert parsed["type"] == "node.start"
    assert parsed["source"] == "tutor"
    assert parsed["data"]["topic"] == "控制理论"

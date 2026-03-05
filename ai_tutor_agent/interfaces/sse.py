import json

from ..core.events import AgentEvent


def format_sse(event: AgentEvent) -> str:
    payload = json.dumps(event.to_dict(), ensure_ascii=False)
    return f"event: {event.type}\ndata: {payload}\n\n"

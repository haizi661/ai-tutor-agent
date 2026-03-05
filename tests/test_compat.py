from ai_tutor_agent.cli import run_cli as compat_run_cli
from ai_tutor_agent.events import make_event as compat_make_event
from ai_tutor_agent.interfaces.sse import format_sse as new_format_sse
from ai_tutor_agent.sse import format_sse as compat_format_sse


def test_compat_exports_match_new_paths():
    assert callable(compat_run_cli)
    assert compat_format_sse is new_format_sse


def test_compat_event_export_works():
    event = compat_make_event("session.info", "test", message="ok")
    payload = compat_format_sse(event)
    assert payload.startswith("event: session.info")

from importlib import import_module
import sys
from types import SimpleNamespace

import pytest


app_module = import_module("ai_tutor_agent.interfaces.api.app")


def test_ensure_api_port_available_accepts_free_fixed_port(monkeypatch):
    monkeypatch.setattr(app_module, "_is_port_available", lambda host, port: True)

    app_module._ensure_api_port_available("0.0.0.0", 8000)


def test_ensure_api_port_available_rejects_busy_fixed_port(monkeypatch):
    monkeypatch.setattr(app_module, "_is_port_available", lambda host, port: False)

    with pytest.raises(RuntimeError, match="端口 8000 已被占用"):
        app_module._ensure_api_port_available("0.0.0.0", 8000)


def test_run_api_uses_fixed_8000_even_when_port_envs_are_set(monkeypatch):
    calls = {}

    monkeypatch.setenv("AI_TUTOR_PORT", "8001")
    monkeypatch.setenv("PORT", "8001")
    monkeypatch.setattr(
        app_module,
        "_ensure_api_port_available",
        lambda host, port: calls.setdefault("ensure", (host, port)),
    )

    def fake_run(api_app, *, host, port, log_level):
        calls["run"] = (api_app, host, port, log_level)

    monkeypatch.setitem(sys.modules, "uvicorn", SimpleNamespace(run=fake_run))

    app_module.run_api()

    assert calls["ensure"] == ("0.0.0.0", 8000)
    assert calls["run"][2] == 8000

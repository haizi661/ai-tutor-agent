from types import SimpleNamespace

from agents.error_correction import agent as error_agent


class DummySchema:
    pass


def test_should_avoid_tool_strategy_for_deepseek_model():
    cfg = SimpleNamespace(
        model_name="deepseek-v4-flash",
        base_url="https://api.deepseek.com/v1",
        supports_function_calling=True,
    )

    assert error_agent._should_avoid_tool_strategy(
        provider="openai",
        model_name="deepseek-v4-flash",
        cfg=cfg,
    )


def test_invoke_structured_uses_json_mode_for_deepseek(monkeypatch):
    captured = {}

    class DummyStructuredRunner:
        def invoke(self, messages):
            captured["messages"] = messages
            return {"ok": True}

    class DummyModel:
        def with_structured_output(self, schema, method="json_schema", **kwargs):
            captured["schema"] = schema
            captured["method"] = method
            captured["kwargs"] = kwargs
            return DummyStructuredRunner()

    cfg = SimpleNamespace(
        model_name="deepseek-v4-flash",
        base_url="https://api.deepseek.com/v1",
        supports_function_calling=True,
    )

    monkeypatch.setattr(error_agent.settings, "get_provider", lambda provider: cfg)
    monkeypatch.setattr(error_agent, "_init_model", lambda **kwargs: DummyModel())

    result = error_agent._invoke_structured(
        prompt="hello",
        provider="openai",
        model_name="deepseek-v4-flash",
        temperature=0.1,
        schema=DummySchema,
        system_prompt_fallback="system",
        cache_key="split",
        agent_factory=lambda **kwargs: None,
    )

    assert result == {"ok": True}
    assert captured["method"] == "json_mode"


def test_invoke_structured_falls_back_to_json_mode_on_tool_choice_error(monkeypatch):
    captured = {"agent_called": 0}

    class DummyStructuredRunner:
        def invoke(self, messages):
            return {"ok": True}

    class DummyModel:
        def with_structured_output(self, schema, method="json_schema", **kwargs):
            captured["method"] = method
            return DummyStructuredRunner()

    class DummyAgent:
        def invoke(self, payload, config=None):
            captured["agent_called"] += 1
            raise RuntimeError("deepseek-reasoner does not support this tool_choice")

    cfg = SimpleNamespace(
        model_name="gpt-4o-mini",
        base_url="https://api.openai.com/v1",
        supports_function_calling=True,
    )

    monkeypatch.setattr(error_agent.settings, "get_provider", lambda provider: cfg)
    monkeypatch.setattr(error_agent, "_init_model", lambda **kwargs: DummyModel())
    monkeypatch.setattr(error_agent, "create_inner_split_agent", lambda **kwargs: DummyAgent())
    monkeypatch.setattr(error_agent, "_agent_cache", {})

    result = error_agent._invoke_structured(
        prompt="hello",
        provider="openai",
        model_name="gpt-4o-mini",
        temperature=0.1,
        schema=DummySchema,
        system_prompt_fallback="system",
        cache_key="split",
        agent_factory=error_agent.create_inner_split_agent,
    )

    assert result == {"ok": True}
    assert captured["agent_called"] == 1
    assert captured["method"] == "json_mode"

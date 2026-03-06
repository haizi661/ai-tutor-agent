from types import SimpleNamespace

from ai_tutor_agent.application.session import run_learning_session
from ai_tutor_agent.core.ports import BufferedEventSink


class FakeApp:
    def __init__(self, state_values):
        self.state_values = state_values
        self.updated = None
        self.invocations = []

    def get_state(self, config):
        del config
        return SimpleNamespace(values=self.state_values)

    def update_state(self, config, values):
        self.updated = (config, values)

    def invoke(self, payload, config):
        self.invocations.append((payload, config))


def test_run_learning_session_uses_new_turn_for_pre_topic_history():
    sink = BufferedEventSink()
    app = FakeApp(
        {
            "current_topic": "你好，你是什么模型呢",
            "flow_status": "greeting",
            "is_assessed": False,
        }
    )

    run_learning_session(
        app,
        sink,
        thread_id="thread-1",
        topic="你是什么模型",
        current_state=app.get_state({"configurable": {"thread_id": "thread-1"}}),
    )

    assert app.updated is None
    payload, config = app.invocations[0]
    assert payload["current_topic"] == "你是什么模型"
    assert payload["flow_status"] == "greeting"
    assert payload["proposed_topic"] == ""
    assert config == {"configurable": {"thread_id": "thread-1"}}
    assert any("按你刚输入的新内容继续" in event.message for event in sink.events)


def test_run_learning_session_keeps_normal_resume_for_existing_progress():
    sink = BufferedEventSink()
    app = FakeApp(
        {
            "current_topic": "控制理论",
            "flow_status": "awaiting_assessment",
            "is_assessed": False,
        }
    )

    run_learning_session(
        app,
        sink,
        thread_id="thread-2",
        topic="你是什么模型",
        current_state=app.get_state({"configurable": {"thread_id": "thread-2"}}),
    )

    assert app.updated is None
    assert app.invocations == [(None, {"configurable": {"thread_id": "thread-2"}})]
    assert any("系统将从上次进度继续" in event.message for event in sink.events)


def test_run_learning_session_does_not_resume_empty_pre_topic_history():
    sink = BufferedEventSink()
    app = FakeApp(
        {
            "current_topic": "你是什么模型",
            "flow_status": "meta_qa",
            "is_assessed": False,
        }
    )

    run_learning_session(
        app,
        sink,
        thread_id="thread-3",
        topic="",
        current_state=app.get_state({"configurable": {"thread_id": "thread-3"}}),
    )

    assert app.updated is None
    assert app.invocations == []
    assert any("主题沟通阶段" in event.message for event in sink.events)

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


def test_run_learning_session_interrupt_follow_up_keeps_context_history():
    sink = BufferedEventSink()
    app = FakeApp(
        {
            "current_topic": "控制理论",
            "flow_status": "awaiting_interrupt_confirmation",
            "is_assessed": True,
            "resume_tester": True,
            "conversation_history": [
                {"role": "user", "kind": "interruption_user", "content": "上一轮追问"},
                {"role": "assistant", "kind": "interruption", "content": "上一轮解答"},
            ],
        }
    )

    run_learning_session(
        app,
        sink,
        thread_id="thread-4",
        topic="那这个闭环怎么判断稳定？",
        current_state=app.get_state({"configurable": {"thread_id": "thread-4"}}),
    )

    assert app.updated is None
    payload, config = app.invocations[0]
    assert payload["interrupt_query"] == "那这个闭环怎么判断稳定？"
    assert payload["resume_tester"] is True
    assert payload["conversation_history"][-1] == {
        "role": "user",
        "kind": "interruption_user",
        "content": "那这个闭环怎么判断稳定？",
    }
    assert config == {"configurable": {"thread_id": "thread-4"}}


def test_run_learning_session_resume_mainline_clears_interrupt_history():
    sink = BufferedEventSink()
    app = FakeApp(
        {
            "current_topic": "控制理论",
            "flow_status": "awaiting_interrupt_confirmation",
            "is_assessed": True,
            "tester_question": "请继续分析闭环系统稳定性。",
            "conversation_history": [
                {"role": "user", "kind": "interruption_user", "content": "临时追问1"},
                {"role": "assistant", "kind": "interruption", "content": "临时解答1"},
                {"role": "assistant", "kind": "tutor", "content": "主线讲解"},
            ],
        }
    )

    run_learning_session(
        app,
        sink,
        thread_id="thread-5",
        topic="继续主线",
        current_state=app.get_state({"configurable": {"thread_id": "thread-5"}}),
    )

    assert app.updated is None
    payload, config = app.invocations[0]
    assert payload["flow_status"] == "normal"
    assert payload["interrupt_query"] == ""
    assert payload["resume_tester"] is True
    assert payload["conversation_history"] == [
        {"role": "assistant", "kind": "tutor", "content": "主线讲解"},
    ]
    assert config == {"configurable": {"thread_id": "thread-5"}}

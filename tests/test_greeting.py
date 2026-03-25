from types import SimpleNamespace

from ai_tutor_agent.core.ports import BufferedEventSink
from ai_tutor_agent.nodes.greeting import _looks_ambiguous, build_greeting_node
from ai_tutor_agent.nodes.topic_confirm import build_topic_confirm_node


class FakeLLM:
    def __init__(self, response_text: str):
        self.response_text = response_text
        self.calls = 0

    def stream(self, messages):
        del messages
        self.calls += 1
        yield SimpleNamespace(content=self.response_text)


class FakeAnswerProvider:
    def __init__(self, answer: str):
        self.answer = answer
        self.prompts = []

    def get_answer(self, prompt: str, *, state=None) -> str:
        del state
        self.prompts.append(prompt)
        return self.answer


def test_looks_ambiguous_filters_greetings_and_fillers():
    assert _looks_ambiguous("你好") is True
    assert _looks_ambiguous("额") is True
    assert _looks_ambiguous("在吗") is True
    assert _looks_ambiguous("控制理论") is False


def test_greeting_node_reasks_when_input_is_ambiguous():
    llm = FakeLLM('{"status":"confirmed","topic":"你好","assistant_reply":""}')
    sink = BufferedEventSink()
    answer_provider = FakeAnswerProvider("控制理论")
    node = build_greeting_node(llm, sink, answer_provider)

    result = node({"current_topic": "你好"})

    assert result["proposed_topic"] == "控制理论"
    assert result["flow_status"] == "topic_confirmation_pending"
    assert llm.calls == 0
    assert "明确主题" in answer_provider.prompts[0]


def test_greeting_node_confirms_explicit_topic():
    llm = FakeLLM('{"status":"confirmed","topic":"控制理论","assistant_reply":""}')
    sink = BufferedEventSink()
    answer_provider = FakeAnswerProvider("不会用到")
    node = build_greeting_node(llm, sink, answer_provider)

    result = node({"current_topic": "我想学控制理论"})

    assert result["proposed_topic"] == "控制理论"
    assert result["flow_status"] == "topic_confirmation_pending"
    assert llm.calls == 1


def test_topic_confirm_node_emits_confirmation_contract_event():
    sink = BufferedEventSink()
    node = build_topic_confirm_node(sink)

    result = node({"proposed_topic": "控制理论"})

    assert result == {"flow_status": "awaiting_topic_confirmation"}
    assert sink.events[0].type == "topic.confirmation_needed"
    assert sink.events[0].source == "topic_confirmer"
    assert sink.events[0].data == {"proposed_topic": "控制理论"}
    assert "控制理论" in (sink.events[0].message or "")
    assert sink.events[1].type == "node.complete"


def test_topic_confirm_node_warns_when_topic_missing():
    sink = BufferedEventSink()
    node = build_topic_confirm_node(sink)

    result = node({"proposed_topic": "   "})

    assert result == {"flow_status": "greeting"}
    assert len(sink.events) == 1
    assert sink.events[0].type == "session.warning"

from types import SimpleNamespace

from ai_tutor_agent.core.ports import BufferedEventSink
from ai_tutor_agent.nodes.greeting import _looks_ambiguous, build_greeting_node


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

    assert result["current_topic"] == "控制理论"
    assert result["flow_status"] == "greeting"
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

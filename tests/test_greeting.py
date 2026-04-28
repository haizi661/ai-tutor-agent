from types import SimpleNamespace

from ai_tutor_agent.core.ports import BufferedEventSink
from ai_tutor_agent.nodes.greeting import _looks_ambiguous, build_greeting_node
from ai_tutor_agent.nodes.topic_confirm import build_topic_confirm_node


class FakeLLM:
    def __init__(self, response_text):
        self.responses = response_text if isinstance(response_text, list) else [response_text]
        self.calls = 0

    def stream(self, messages):
        del messages
        if self.calls >= len(self.responses):
            raise AssertionError("FakeLLM called more times than expected")
        response_text = self.responses[self.calls]
        self.calls += 1
        yield SimpleNamespace(content=response_text)


class FakeAnswerProvider:
    def __init__(self, answer):
        self.answers = answer if isinstance(answer, list) else [answer]
        self.prompts = []
        self.states = []

    def get_answer(self, prompt: str, *, state=None) -> str:
        self.prompts.append(prompt)
        self.states.append(state or {})
        if not self.answers:
            raise AssertionError("FakeAnswerProvider ran out of answers")
        return self.answers.pop(0)


def test_looks_ambiguous_filters_greetings_and_fillers():
    assert _looks_ambiguous("你好") is True
    assert _looks_ambiguous("额") is True
    assert _looks_ambiguous("在吗") is True
    assert _looks_ambiguous("控制理论") is False


def test_greeting_node_reasks_when_input_is_ambiguous():
    llm = FakeLLM(
        '{"status":"confirmed","topic":"控制理论","goal":"控制理论","focus":"","background":"","detail_summary":"这次先从控制理论开始。","needs_follow_up":false,"assistant_reply":""}'
    )
    sink = BufferedEventSink()
    answer_provider = FakeAnswerProvider("控制理论")
    node = build_greeting_node(llm, sink, answer_provider)

    result = node({"current_topic": "你好"})

    assert result["proposed_topic"] == "控制理论"
    assert result["flow_status"] == "topic_confirmation_pending"
    assert llm.calls == 1
    assert "最想先学哪一块" in answer_provider.prompts[0]
    assert answer_provider.states[0]["interaction_kind"] == "topic_detail_prompt"


def test_greeting_node_confirms_explicit_topic():
    llm = FakeLLM(
        '{"status":"confirmed","topic":"控制理论","goal":"控制理论","focus":"","background":"","detail_summary":"这次先从控制理论开始。","needs_follow_up":false,"assistant_reply":""}'
    )
    sink = BufferedEventSink()
    answer_provider = FakeAnswerProvider("不会用到")
    node = build_greeting_node(llm, sink, answer_provider)

    result = node({"current_topic": "我想学控制理论"})

    assert result["proposed_topic"] == "控制理论"
    assert result["flow_status"] == "topic_confirmation_pending"
    assert llm.calls == 1


def test_greeting_node_refines_broad_topic_with_limited_follow_up():
    llm = FakeLLM(
        [
            '{"status":"confirmed","topic":"自动控制原理","goal":"","focus":"","background":"","detail_summary":"先从自动控制原理开始。","needs_follow_up":true,"follow_up_mode":"ask_user","suggested_options":[],"assistant_reply":"这次你更想先解决哪一块？"}',
        ]
    )
    sink = BufferedEventSink()
    answer_provider = FakeAnswerProvider("不会用到")
    node = build_greeting_node(llm, sink, answer_provider)

    result = node({"current_topic": "自动控制原理"})

    assert result["proposed_topic"] == "自动控制原理"
    assert result["current_user_goal"] == "自动控制原理"
    assert result["topic_focus"] == "自动控制原理"
    assert result["topic_background"] == ""
    assert result["topic_detail_summary"] == "先从自动控制原理开始。"
    assert result["topic_clarify_rounds"] == 0
    assert llm.calls == 1
    assert answer_provider.prompts == []


def test_greeting_node_gives_topic_specific_options_for_zero_base_user():
    llm = FakeLLM(
        [
            '{"status":"confirmed","topic":"控制原理","goal":"","focus":"","background":"","detail_summary":"先从控制原理开始。","needs_follow_up":true,"follow_up_mode":"ask_user","suggested_options":[],"assistant_reply":"你是零基础入门，还是备考/做作业遇到卡点？"}',
        ]
    )
    sink = BufferedEventSink()
    answer_provider = FakeAnswerProvider(["不会用到"])
    node = build_greeting_node(llm, sink, answer_provider)

    result = node({"current_topic": "我要学习控制原理"})

    assert result["proposed_topic"] == "控制原理"
    assert result["current_user_goal"] == "控制原理"
    assert result["topic_focus"] == "控制原理"
    assert result["topic_background"] == ""
    assert result["topic_starter_options"] == []
    assert result["topic_clarify_rounds"] == 0
    assert llm.calls == 1
    assert answer_provider.prompts == []


def test_greeting_node_stops_when_user_has_given_enough_context_even_if_llm_wants_more():
    llm = FakeLLM(
        [
            '{"status":"confirmed","topic":"控制原理","goal":"","focus":"","background":"","detail_summary":"先从控制原理开始。","needs_follow_up":true,"follow_up_mode":"ask_user","suggested_options":[],"assistant_reply":"你是零基础入门，还是备考/做作业遇到卡点？"}',
        ]
    )
    sink = BufferedEventSink()
    answer_provider = FakeAnswerProvider("不会用到")
    node = build_greeting_node(llm, sink, answer_provider)

    result = node({"current_topic": "我要学习控制原理"})

    assert result["proposed_topic"] == "控制原理"
    assert result["topic_background"] == ""
    assert result["current_user_goal"] == "控制原理"
    assert result["topic_clarify_rounds"] == 0
    assert llm.calls == 1
    assert answer_provider.prompts == []


def test_topic_confirm_node_emits_confirmation_contract_event():
    sink = BufferedEventSink()
    node = build_topic_confirm_node(sink)

    result = node(
        {
            "proposed_topic": "控制理论",
            "topic_detail_summary": "这次先抓稳定性判据，当前更像考前复习。",
            "topic_focus": "稳定性判据",
            "topic_background": "考前复习",
            "topic_starter_options": ["稳定性判据", "时域分析"],
            "topic_clarify_rounds": 1,
        }
    )

    assert result["flow_status"] == "awaiting_topic_confirmation"
    assert "message_history" in result
    assert sink.events[0].type == "topic.confirmation_needed"
    assert sink.events[0].source == "topic_confirmer"
    assert sink.events[0].data == {
        "proposed_topic": "控制理论",
        "detail_summary": "这次先抓稳定性判据，当前更像考前复习。",
        "topic_focus": "稳定性判据",
        "topic_background": "考前复习",
        "topic_starter_options": ["稳定性判据", "时域分析"],
        "clarify_rounds": 1,
    }
    assert "控制理论" in (sink.events[0].message or "")
    assert sink.events[1].type == "node.complete"


def test_topic_confirm_node_warns_when_topic_missing():
    sink = BufferedEventSink()
    node = build_topic_confirm_node(sink)

    result = node({"proposed_topic": "   "})

    assert result == {"flow_status": "greeting"}
    assert len(sink.events) == 1
    assert sink.events[0].type == "session.warning"

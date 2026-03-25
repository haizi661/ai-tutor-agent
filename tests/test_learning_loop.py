from types import SimpleNamespace

from ai_tutor_agent.core.ports import BufferedEventSink
from ai_tutor_agent.nodes.coach import build_coach_node
from ai_tutor_agent.nodes.evaluator import build_evaluator_node
from ai_tutor_agent.nodes.tester import build_tester_node
from ai_tutor_agent.orchestration.workflow import route_after_evaluator


class FakeStreamingLLM:
    def __init__(self, responses):
        if isinstance(responses, str):
            responses = [responses]
        self.responses = list(responses)
        self.messages = []

    def stream(self, messages):
        self.messages.append(messages)
        response = self.responses.pop(0)
        yield SimpleNamespace(content=response)


class FakeAnswerProvider:
    def __init__(self, answers):
        if isinstance(answers, str):
            answers = [answers]
        self.answers = list(answers)
        self.prompts = []

    def get_answer(self, prompt: str, *, state=None) -> str:
        self.prompts.append({"prompt": prompt, "state": state})
        return self.answers.pop(0)


class SequentialEvaluatorLLM:
    def __init__(self, results):
        self.results = list(results)

    def with_structured_output(self, _schema):
        return self

    def invoke(self, _messages):
        return self.results.pop(0)


def _evaluation_result(
    *,
    total_score,
    logic_score,
    concept_score,
    encouragement,
    needs_hint,
    misconceptions=None,
    rubric_feedback=None,
    next_review_points=None,
    model_answer="参考答案",
    is_correct_direction=True,
):
    return SimpleNamespace(
        total_score=total_score,
        logic_score=logic_score,
        concept_score=concept_score,
        is_correct_direction=is_correct_direction,
        misconceptions=misconceptions or [],
        rubric_feedback=rubric_feedback or [],
        model_answer=model_answer,
        encouragement=encouragement,
        next_review_points=next_review_points or [],
        needs_hint=needs_hint,
    )


def test_retry_loop_accumulates_history_then_resets_attempt_on_pass(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _seconds: None)

    sink = BufferedEventSink()
    evaluator_node = build_evaluator_node(
        SequentialEvaluatorLLM(
            [
                _evaluation_result(
                    total_score=58,
                    logic_score=60,
                    concept_score=55,
                    encouragement="第一次反馈",
                    needs_hint=True,
                    misconceptions=["混淆了稳定性与瞬态性能"],
                    rubric_feedback=["概念混淆（-12）"],
                    next_review_points=["稳定性定义"],
                    model_answer="稳定性关注是否回到平衡点。",
                ),
                _evaluation_result(
                    total_score=88,
                    logic_score=86,
                    concept_score=90,
                    encouragement="第二次反馈",
                    needs_hint=False,
                    model_answer="稳定性与瞬态性能需要分开描述。",
                ),
            ]
        ),
        sink,
        80,
    )
    coach_text = "先把稳定性的定义单独说清，再联系闭环。"
    coach_node = build_coach_node(FakeStreamingLLM(coach_text), sink)
    tester_llm = FakeStreamingLLM(
        "请重新解释稳定性，并说明它与瞬态性能的区别。\n\n💡 思路提示：先分开两个概念。"
    )
    answer_provider = FakeAnswerProvider("稳定性是回到平衡点，瞬态性能看响应过程。")
    tester_node = build_tester_node(tester_llm, sink, answer_provider)

    base_state = {
        "current_topic": "控制理论",
        "tutor_content": "本轮讲解聚焦稳定性与瞬态性能。",
        "tester_question": "什么是稳定性？",
        "difficulty_level": 3,
    }

    first_eval = evaluator_node(
        {
            **base_state,
            "user_answer": "我觉得稳定性就是系统表现好。",
            "attempt_count": 0,
            "score_history": [],
        }
    )
    assert first_eval["attempt_count"] == 1
    assert first_eval["score_history"] == [(58, 60, 55, "第一次反馈")]
    assert route_after_evaluator(first_eval, 80) == "coach"

    coached = coach_node({**base_state, **first_eval, "user_answer": "我觉得稳定性就是系统表现好。"})
    assert coached["coach_content"] == coach_text

    retry_question = tester_node({**base_state, **first_eval, **coached})
    assert retry_question["coach_content"] == ""
    assert retry_question["user_answer"] == "稳定性是回到平衡点，瞬态性能看响应过程。"
    assert coach_text in tester_llm.messages[0][1].content
    assert "补救教练刚给出的纠偏卡片" in tester_llm.messages[0][1].content

    second_eval = evaluator_node({**base_state, **first_eval, **retry_question})
    assert second_eval["attempt_count"] == 0
    assert second_eval["score_history"] == [
        (58, 60, 55, "第一次反馈"),
        (88, 86, 90, "第二次反馈"),
    ]
    assert route_after_evaluator(second_eval, 80) == "pass"


def test_tester_only_uses_coach_content_during_remediate_retry():
    sink = BufferedEventSink()
    tester_llm = FakeStreamingLLM(
        "请解释闭环稳定性的定义。\n\n💡 思路提示：先说最终是否收敛。"
    )
    answer_provider = FakeAnswerProvider("系统会回到平衡点。")
    tester_node = build_tester_node(tester_llm, sink, answer_provider)

    result = tester_node(
        {
            "current_topic": "控制理论",
            "tutor_content": "讲解了闭环稳定性的基本定义。",
            "difficulty_level": 3,
            "attempt_count": 0,
            "coach_content": "",
        }
    )

    assert result["coach_content"] == ""
    assert "补救教练刚给出的纠偏卡片" not in tester_llm.messages[0][1].content
    assert answer_provider.prompts[0]["state"]["current_topic"] == "控制理论"

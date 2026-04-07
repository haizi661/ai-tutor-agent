from types import SimpleNamespace

from ai_tutor_agent.core.ports import BufferedEventSink
from ai_tutor_agent.nodes.assessment import (
    ASSESSMENT_DIMENSIONS,
    _generate_radar_data,
)
from ai_tutor_agent.nodes.evaluator import build_evaluator_node


def test_generate_radar_data_uses_rule_based_scores():
    questions = [
        {
            "id": 1,
            "type": "self_eval",
            "dimension": "基础概念",
            "question": "你对基础概念的掌握如何？",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "",
        },
        {
            "id": 2,
            "type": "objective",
            "dimension": "基础概念",
            "question": "基础题",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "C",
        },
        {
            "id": 3,
            "type": "self_eval",
            "dimension": "逻辑推理",
            "question": "你对逻辑推理的掌握如何？",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "",
        },
        {
            "id": 4,
            "type": "objective",
            "dimension": "逻辑推理",
            "question": "逻辑题",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "A",
        },
    ]
    answers = {"1": "D", "2": "C", "3": "B", "4": "D"}

    radar = _generate_radar_data(BufferedEventSink(), "控制理论", questions, answers)

    assert radar["dimensions"] == ASSESSMENT_DIMENSIONS
    concept_index = ASSESSMENT_DIMENSIONS.index("基础概念")
    logic_index = ASSESSMENT_DIMENSIONS.index("逻辑推理")
    assert radar["self_scores"][concept_index] == 100
    assert radar["objective_scores"][concept_index] == 100
    assert radar["gap_scores"][concept_index] == 0
    assert radar["self_scores"][logic_index] == 50
    assert radar["objective_scores"][logic_index] == 0
    assert radar["gap_scores"][logic_index] == 50
    assert radar["breakdown"][concept_index]["objective_count"] == 1


def test_generate_radar_data_warns_when_objective_answer_key_missing():
    sink = BufferedEventSink()
    radar = _generate_radar_data(
        sink,
        "控制理论",
        [
            {
                "id": 1,
                "type": "objective",
                "dimension": "基础概念",
                "question": "缺少答案键",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "",
            }
        ],
        {"1": "A"},
    )

    assert radar["objective_scores"][0] == 50
    assert any("缺少 correct_answer" in event.message for event in sink.events)


class FakeEvaluatorLLM:
    def __init__(self, result):
        self.result = result

    def with_structured_output(self, _schema):
        return self

    def invoke(self, _messages):
        return self.result


def test_evaluator_emits_assessment_result_contract_and_updates_state(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _seconds: None)

    sink = BufferedEventSink()
    result = SimpleNamespace(
        total_score=52,
        logic_score=55,
        concept_score=49,
        is_correct_direction=True,
        misconceptions=["把闭环稳定性和瞬态性能混为一谈"],
        rubric_feedback=["概念: 混淆稳定性与性能指标（-12）"],
        model_answer="稳定性描述系统是否收敛，瞬态性能描述响应快慢与超调。",
        encouragement="你已经抓到部分关键点了，再把两个指标分清会更稳。",
        next_review_points=["稳定性", "瞬态性能"],
        needs_hint=True,
    )
    node = build_evaluator_node(FakeEvaluatorLLM(result), sink, 80)

    updated = node(
        {
            "current_topic": "控制理论",
            "tutor_content": "讲解内容",
            "tester_question": "什么是稳定性？",
            "user_answer": "我不会",
            "attempt_count": 1,
            "score_history": [(45, 40, 42, "上轮反馈")],
        }
    )

    assessment_event = next(event for event in sink.events if event.type == "assessment.result")
    assert assessment_event.source == "evaluator"
    assert assessment_event.data["total_score"] == 35
    assert assessment_event.data["logic_score"] == 55
    assert assessment_event.data["concept_score"] == 49
    assert assessment_event.data["needs_hint"] is True
    assert assessment_event.data["misconceptions"] == ["把闭环稳定性和瞬态性能混为一谈"]
    assert assessment_event.data["next_review_points"] == ["稳定性", "瞬态性能"]
    assert any(event.type == "node.stream" for event in sink.events)
    assert sink.events[-1].type == "node.complete"

    assert updated["score"] == 35
    assert updated["attempt_count"] == 2
    assert updated["needs_hint"] is True
    assert updated["score_history"][-1] == (35, 55, 49, "你已经抓到部分关键点了，再把两个指标分清会更稳。")
    assert updated["model_answer"] == "稳定性描述系统是否收敛，瞬态性能描述响应快慢与超调。"
    assert updated["misconceptions"] == ["把闭环稳定性和瞬态性能混为一谈"]
    assert updated["next_review_points"] == ["稳定性", "瞬态性能"]


def test_evaluator_builds_teacher_like_feedback_when_model_returns_empty_encouragement(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _seconds: None)

    sink = BufferedEventSink()
    result = SimpleNamespace(
        total_score=61,
        logic_score=66,
        concept_score=58,
        is_correct_direction=True,
        misconceptions=["把稳定性和瞬态性能混在一起了"],
        rubric_feedback=["概念边界不清（-10）"],
        model_answer="稳定性关注是否收敛，瞬态性能关注响应过程。",
        encouragement="",
        next_review_points=["先分开稳定性和瞬态性能"],
        needs_hint=True,
    )
    node = build_evaluator_node(FakeEvaluatorLLM(result), sink, 80)

    updated = node(
        {
            "current_topic": "控制理论",
            "tutor_content": "讲解内容",
            "tester_question": "什么是稳定性？",
            "user_answer": "稳定性和瞬态性能差不多吧。",
            "attempt_count": 0,
            "score_history": [],
        }
    )

    assert updated["feedback"]
    assert "方向基本是对的" in updated["feedback"]
    assert "稳定性和瞬态性能" in updated["feedback"]

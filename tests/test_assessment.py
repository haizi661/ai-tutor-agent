from ai_tutor_agent.core.ports import BufferedEventSink
from ai_tutor_agent.nodes.assessment import (
    ASSESSMENT_DIMENSIONS,
    _generate_radar_data,
)


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

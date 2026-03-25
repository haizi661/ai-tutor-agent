from types import SimpleNamespace

from ai_tutor_agent.interfaces.api.history import _reconstruct_messages, _serialize_state


class FakeCheckpointStore:
    def __init__(self, entries):
        self._entries = entries

    def list(self, config, limit=None):
        del config, limit
        return self._entries


def _checkpoint(values, ts):
    return SimpleNamespace(
        checkpoint={"channel_values": values, "ts": ts},
        metadata={},
        parent_config=None,
    )


def test_serialize_state_includes_closed_loop_fields():
    serialized = _serialize_state(
        {
            "current_topic": "控制理论",
            "flow_status": "normal",
            "model_answer": "参考答案",
            "misconceptions": ["误区1"],
            "next_review_points": ["复习点1"],
            "is_correct_direction": False,
            "needs_hint": True,
            "difficulty_level": 4,
            "attempt_count": 2,
            "score_history": [(45, 40, 42, "上轮反馈")],
            "coach_content": "先看闭环框图。",
        }
    )

    assert serialized["model_answer"] == "参考答案"
    assert serialized["misconceptions"] == ["误区1"]
    assert serialized["next_review_points"] == ["复习点1"]
    assert serialized["is_correct_direction"] is False
    assert serialized["needs_hint"] is True
    assert serialized["difficulty_level"] == 4
    assert serialized["attempt_count"] == 2
    assert serialized["score_history"] == [(45, 40, 42, "上轮反馈")]
    assert serialized["coach_content"] == "先看闭环框图。"


def test_reconstruct_messages_keeps_coach_turn_and_evaluator_summary():
    store = FakeCheckpointStore(
        [
            _checkpoint(
                {
                    "assessment_result": "## 画像",
                    "tutor_content": "先讲稳定性。",
                    "coach_content": "先看闭环框图。",
                    "tester_question": "什么是稳定性？",
                    "user_answer": "我不太会。",
                    "score": 35,
                    "logic_score": 40,
                    "concept_score": 32,
                    "feedback": "还需要重新区分几个核心概念。",
                    "rubric_feedback": ["概念混淆（-12）"],
                },
                "2026-03-18T10:00:00+00:00",
            )
        ]
    )

    items = _reconstruct_messages(store, "thread-1")
    kinds = [item["kind"] for item in items]

    assert "assessment_result" in kinds
    assert "tutor" in kinds
    assert "coach" in kinds
    assert "tester_question" in kinds
    assert "user_answer" in kinds
    assert "evaluator_card" in kinds
    coach_item = next(item for item in items if item["kind"] == "coach")
    evaluator_item = next(item for item in items if item["kind"] == "evaluator_card")
    assert coach_item["content"] == "先看闭环框图。"
    assert "总分：**35**" in evaluator_item["content"]
    assert "量表依据" in evaluator_item["content"]

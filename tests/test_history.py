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
            "current_user_goal": "稳定性怎么判断",
            "flow_status": "normal",
            "model_answer": "参考答案",
            "misconceptions": ["误区1"],
            "next_review_points": ["复习点1"],
            "is_correct_direction": False,
            "needs_hint": True,
            "difficulty_level": 4,
            "attempt_count": 2,
            "score_history": [(45, 40, 42, "上轮反馈")],
            "post_eval_choice": "same_type_practice",
            "practice_generation_mode": "same_type",
            "coach_content": "先看闭环框图。",
            "tester_question_type": "概念辨析题",
            "tester_question_template": "定义辨析",
            "tutor_evidence": [{"rank": 1, "display_label": "guide.pdf", "snippet": "证据片段"}],
            "message_history": [{"role": "user", "kind": "topic_input", "content": "我想学控制原理"}],
        }
    )

    assert serialized["current_user_goal"] == "稳定性怎么判断"
    assert serialized["model_answer"] == "参考答案"
    assert serialized["misconceptions"] == ["误区1"]
    assert serialized["next_review_points"] == ["复习点1"]
    assert serialized["is_correct_direction"] is False
    assert serialized["needs_hint"] is True
    assert serialized["difficulty_level"] == 4
    assert serialized["attempt_count"] == 2
    assert serialized["score_history"] == [(45, 40, 42, "上轮反馈")]
    assert serialized["post_eval_choice"] == "same_type_practice"
    assert serialized["practice_generation_mode"] == "same_type"
    assert serialized["coach_content"] == "先看闭环框图。"
    assert serialized["tester_question_type"] == "概念辨析题"
    assert serialized["tester_question_template"] == "定义辨析"
    assert serialized["tutor_evidence"][0]["display_label"] == "guide.pdf"
    assert serialized["message_history"][0]["content"] == "我想学控制原理"


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


def test_reconstruct_messages_includes_tutor_evidence_panel():
    store = FakeCheckpointStore(
        [
            _checkpoint(
                {
                    "tutor_content": "先讲闭环稳定性。",
                    "tutor_evidence": [
                        {
                            "rank": 1,
                            "display_label": "控制系统导论.pdf · 第 12 页",
                            "filename": "控制系统导论.pdf",
                            "page": 12,
                            "chunk_index": 3,
                            "snippet": "稳定性的核心判断是极点是否位于左半平面。",
                            "source_type": "local_kb",
                        }
                    ],
                },
                "2026-03-18T10:00:00+00:00",
            )
        ]
    )

    items = _reconstruct_messages(store, "thread-2")
    citation_item = next(item for item in items if item["kind"] == "tutor_evidence")

    assert "证据来源" in citation_item["content"]
    assert "上传资料" in citation_item["content"]
    assert "控制系统导论.pdf" in citation_item["content"]
    assert "稳定性的核心判断" in citation_item["content"]
    assert citation_item["data"]["evidence"][0]["rank"] == 1


def test_reconstruct_messages_groups_evidence_by_source_scope():
    store = FakeCheckpointStore(
        [
            _checkpoint(
                {
                    "tutor_evidence": [
                        {
                            "rank": 1,
                            "display_label": "[课程图谱] 反馈.md",
                            "snippet": "反馈把输出送回输入端。",
                            "source_type": "local_kb",
                            "source_scope": "course_primary",
                        },
                        {
                            "rank": 2,
                            "display_label": "[上传资料] lecture.pdf · 第 3 页",
                            "snippet": "上传讲义补充了扰动抑制。",
                            "source_type": "local_kb",
                            "source_scope": "supplemental",
                        },
                    ],
                },
                "2026-03-18T10:00:00+00:00",
            )
        ]
    )

    items = _reconstruct_messages(store, "thread-5")
    citation_item = next(item for item in items if item["kind"] == "tutor_evidence")

    assert "课程图谱" in citation_item["content"]
    assert "上传资料" in citation_item["content"]


def test_reconstruct_messages_replays_message_history_before_agent_output():
    store = FakeCheckpointStore(
        [
            _checkpoint(
                {
                    "message_history": [
                        {"role": "user", "kind": "topic_input", "content": "我要学习控制原理"},
                        {"role": "user", "kind": "topic_input", "content": "我是零基础入门"},
                    ],
                    "tutor_content": "我们先搭一个总框架。",
                },
                "2026-04-12T10:00:00+00:00",
            )
        ]
    )

    items = _reconstruct_messages(store, "thread-3")

    assert items[0]["role"] == "user"
    assert items[0]["content"] == "我要学习控制原理"
    assert items[1]["role"] == "user"
    assert items[1]["content"] == "我是零基础入门"
    assert items[2]["kind"] == "tutor"


def test_reconstruct_messages_includes_structured_cards():
    store = FakeCheckpointStore(
        [
            _checkpoint(
                {
                    "proposed_topic": "控制理论",
                    "topic_focus": "稳定性判据",
                    "topic_background": "零基础",
                    "topic_detail_summary": "先入门稳定性怎么判断",
                    "topic_starter_options": ["先看极点", "先看闭环"],
                    "topic_clarify_rounds": 1,
                    "flow_status": "awaiting_topic_confirmation",
                },
                "2026-04-12T10:00:00+00:00",
            ),
            _checkpoint(
                {
                    "assessment_questions": [
                        {"id": 1, "question": "Q1", "options": ["A", "B", "C", "D"]},
                    ],
                    "flow_status": "awaiting_assessment",
                },
                "2026-04-12T10:01:00+00:00",
            ),
            _checkpoint(
                {
                    "message_history": [
                        {"role": "assistant", "kind": "interruption", "content": "先看极点位置。"},
                        {
                            "role": "assistant",
                            "kind": "interrupt_confirmation_card",
                            "content": "回到主线还是继续追问？",
                            "data": {"requires_confirmation": True},
                        },
                    ],
                    "flow_status": "awaiting_interrupt_confirmation",
                },
                "2026-04-12T10:02:00+00:00",
            ),
        ]
    )

    items = _reconstruct_messages(store, "thread-4")
    kinds = [item["kind"] for item in items]

    assert "topic_confirmation_card" in kinds
    assert "assessment_form" in kinds
    assert "interrupt_confirmation_card" in kinds

    topic_item = next(item for item in items if item["kind"] == "topic_confirmation_card")
    assessment_item = next(item for item in items if item["kind"] == "assessment_form")
    interrupt_item = next(item for item in items if item["kind"] == "interrupt_confirmation_card")

    assert topic_item["data"]["proposed_topic"] == "控制理论"
    assert assessment_item["data"]["questions"][0]["id"] == 1
    assert interrupt_item["data"]["requires_confirmation"] is True

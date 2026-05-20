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
            "homework_items": [{"question_id": "HW-KM001", "prompt": "复习稳定性"}],
            "homework_answers": {"HW-KM001": "看极点"},
            "homework_results": [{"question_id": "HW-KM001", "score": 80}],
            "homework_score": 80,
            "homework_status": "assigned",
            "continue_or_homework_choice": "stop_today",
            "pending_interaction_answer": "answer_homework",
            "student_state_snapshot": {"visited_nodes": ["KM001"]},
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
    assert serialized["homework_items"][0]["question_id"] == "HW-KM001"
    assert serialized["homework_answers"]["HW-KM001"] == "看极点"
    assert serialized["homework_results"][0]["score"] == 80
    assert serialized["homework_score"] == 80
    assert serialized["homework_status"] == "assigned"
    assert serialized["continue_or_homework_choice"] == "stop_today"
    assert serialized["pending_interaction_answer"] == "answer_homework"
    assert serialized["student_state_snapshot"]["visited_nodes"] == ["KM001"]


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


def test_reconstruct_messages_keeps_objective_review_after_wrong_explanations():
    store = FakeCheckpointStore(
        [
            _checkpoint(
                {
                    "node_quiz_items": [
                        {"question_id": "Q1", "question": "反馈是什么？", "options": ["A", "B"], "answer_key": "A"},
                    ],
                    "pending_interaction_kind": "objective_test_answers",
                    "pending_interaction_answer": '{"Q1":"B"}',
                    "message_history": [
                        {
                            "role": "assistant",
                            "kind": "objective_quiz_review",
                            "content": "客观测评批改结果\n得分：0",
                            "data": {
                                "kind": "objective_test_answers",
                                "title": "客观测评",
                                "questions": [
                                    {"question_id": "Q1", "question": "反馈是什么？", "options": ["A", "B"], "answer_key": "A"},
                                ],
                                "answers": {"Q1": "B"},
                                "score": 0,
                                "passed": False,
                            },
                        }
                    ],
                },
                "2026-04-12T10:03:00+00:00",
            ),
            _checkpoint(
                {
                    "message_history": [
                        {
                            "role": "assistant",
                            "kind": "objective_quiz_review",
                            "content": "客观测评批改结果\n得分：0",
                            "data": {
                                "kind": "objective_test_answers",
                                "title": "客观测评",
                                "questions": [
                                    {"question_id": "Q1", "question": "反馈是什么？", "options": ["A", "B"], "answer_key": "A"},
                                ],
                                "answers": {"Q1": "B"},
                                "score": 0,
                                "passed": False,
                            },
                        },
                        {
                            "role": "assistant",
                            "kind": "wrong_question_explanations",
                            "content": "错题订正讲解\nQ1. 反馈需要看输出回送输入。",
                            "data": {"explanations": [{"question_id": "Q1", "explanation": "反馈需要看输出回送输入。"}]},
                        },
                    ],
                },
                "2026-04-12T10:04:00+00:00",
            ),
        ]
    )

    items = _reconstruct_messages(store, "thread-objective-review")
    kinds = [item["kind"] for item in items]

    assert kinds.count("objective_quiz_review") == 1
    assert "wrong_question_explanations" in kinds
    assert kinds.index("objective_quiz_review") < kinds.index("wrong_question_explanations")
    review_item = next(item for item in items if item["kind"] == "objective_quiz_review")
    assert review_item["data"]["answers"] == {"Q1": "B"}


def test_reconstruct_messages_locks_pending_choice_card_after_answer():
    store = FakeCheckpointStore(
        [
            _checkpoint(
                {
                    "flow_status": "awaiting_post_lesson_choice",
                    "pending_interaction_kind": "post_lesson_choice",
                    "pending_interaction_prompt": "节点讲完了，接下来做什么？",
                    "pending_interaction_options": [
                        {"value": "temporary_question", "label": "我还有临时问题"},
                        {"value": "start_test", "label": "没有问题，开始测试"},
                    ],
                },
                "2026-04-12T10:05:00+00:00",
            ),
            _checkpoint(
                {
                    "flow_status": "normal",
                    "pending_interaction_kind": "",
                    "pending_interaction_prompt": "",
                    "pending_interaction_options": [],
                    "message_history": [
                        {"role": "user", "kind": "post_lesson_choice", "content": "没有问题，开始测试"},
                    ],
                },
                "2026-04-12T10:06:00+00:00",
            ),
        ]
    )

    items = _reconstruct_messages(store, "thread-choice-lock")
    choice_item = next(item for item in items if item["kind"] == "post_lesson_choice_card")

    assert choice_item["data"]["locked"] is True
    assert choice_item["data"]["selectedLabel"] == "没有问题，开始测试"


def test_reconstruct_messages_locks_homework_choice_by_persisted_value():
    store = FakeCheckpointStore(
        [
            _checkpoint(
                {
                    "flow_status": "awaiting_homework_review_choice",
                    "pending_interaction_kind": "homework_review_choice",
                    "pending_interaction_prompt": "这份作业已按当前图谱节点保存。请选择。",
                    "pending_interaction_options": [
                        {"value": "answer_homework", "label": "现在做作业"},
                        {"value": "save_for_later", "label": "保存，下次再做"},
                        {"value": "continue_learning", "label": "保留作业，继续学习"},
                    ],
                },
                "2026-04-12T10:07:00+00:00",
            ),
            _checkpoint(
                {
                    "flow_status": "normal",
                    "homework_status": "deferred",
                    "pending_interaction_kind": "",
                    "pending_interaction_prompt": "",
                    "pending_interaction_options": [],
                    "message_history": [
                        {
                            "role": "user",
                            "kind": "homework_review_choice",
                            "content": "继续学习",
                            "data": {"selected_value": "continue_learning"},
                        },
                    ],
                },
                "2026-04-12T10:08:00+00:00",
            ),
        ]
    )

    items = _reconstruct_messages(store, "thread-homework-choice")
    choice_item = next(item for item in items if item["kind"] == "homework_review_choice_card")

    assert choice_item["data"]["locked"] is True
    assert choice_item["data"]["selectedValue"] == "continue_learning"
    assert choice_item["data"]["selectedLabel"] == "保留作业，继续学习"


def test_reconstruct_messages_restores_homework_answer_prompt_and_answer():
    store = FakeCheckpointStore(
        [
            _checkpoint(
                {
                    "flow_status": "awaiting_homework_answers",
                    "pending_interaction_kind": "homework_answers",
                    "pending_interaction_prompt": "请按题号提交你的作业答案。",
                    "homework_items": [{"question_id": "HW-KM001", "prompt": "复习稳定性。"}],
                },
                "2026-04-12T10:09:00+00:00",
            ),
            _checkpoint(
                {
                    "flow_status": "normal",
                    "pending_interaction_kind": "",
                    "message_history": [
                        {
                            "role": "user",
                            "kind": "homework_answers",
                            "content": '{"HW-KM001":"看闭环极点"}',
                            "data": {"answers": {"HW-KM001": "看闭环极点"}},
                        }
                    ],
                },
                "2026-04-12T10:10:00+00:00",
            ),
        ]
    )

    items = _reconstruct_messages(store, "thread-homework-answer")
    kinds = [item["kind"] for item in items]

    assert "homework_answer_prompt" in kinds
    assert "homework_answers" in kinds
    answer_item = next(item for item in items if item["kind"] == "homework_answers")
    assert answer_item["data"]["answers"]["HW-KM001"] == "看闭环极点"


def test_reconstruct_messages_locks_synthetic_assessment_form_after_skip():
    store = FakeCheckpointStore(
        [
            _checkpoint(
                {
                    "current_topic": "自动控制原理",
                    "current_user_goal": "自动控制原理",
                    "flow_status": "awaiting_assessment",
                    "assessment_questions": [
                        {"id": 1, "question": "Q1", "options": ["A", "B", "C", "D"]},
                    ],
                    "assessment_answers": {"1": "B"},
                },
                "2026-04-12T10:01:00+00:00",
            ),
            _checkpoint(
                {
                    "current_topic": "自动控制原理",
                    "current_user_goal": "自动控制原理",
                    "flow_status": "normal",
                    "assessment_questions": [],
                    "assessment_answers": {},
                    "assessment_state": {},
                    "message_history": [
                        {
                            "role": "assistant",
                            "kind": "topic_confirmation_locked",
                            "content": "学习主题【自动控制原理】已跳过摸底，直接开始。",
                            "data": {"topic": "自动控制原理", "label": "已跳过摸底，直接开始", "start_mode": "direct_tutor"},
                        }
                    ],
                },
                "2026-04-12T10:02:00+00:00",
            ),
        ]
    )

    items = _reconstruct_messages(store, "thread-skip-assessment")
    assessment_item = next(item for item in items if item["kind"] == "assessment_form")

    assert assessment_item["data"]["questions"][0]["id"] == 1
    assert assessment_item["data"]["answers"] == {"1": "B"}
    assert assessment_item["data"]["locked"] is True
    assert assessment_item["data"]["statusText"] == "已跳过学前测评，答案已固定"

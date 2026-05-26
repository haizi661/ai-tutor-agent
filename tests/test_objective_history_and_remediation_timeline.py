from __future__ import annotations

from ai_tutor_agent.core.ports import BufferedEventSink, RuntimeContext
from ai_tutor_agent.nodes.objective_remediation import build_wrong_question_explainer_node
from ai_tutor_agent.nodes.objective_test import build_objective_test_scorer_node


def _quiz_items():
    return [
        {
            "question_id": "Q1",
            "stem": "在恒温箱反馈控制中，比较点的作用是什么？",
            "options": {
                "A": "比较给定温度与反馈温度并形成偏差",
                "B": "只显示当前温度",
                "C": "直接改变执行机构材料",
                "D": "与反馈信号无关",
            },
            "answer_key": "A",
            "explanation": "比较点用于形成偏差信号。",
        },
        {
            "question_id": "Q2",
            "stem": "负反馈控制为什么有助于减小偏差？",
            "options": {
                "A": "反馈量与给定量同向叠加",
                "B": "反馈量参与比较，使控制作用朝减小偏差方向调整",
                "C": "反馈量只用于记录",
                "D": "控制器不需要被控量信息",
            },
            "answer_key": "B",
            "explanation": "负反馈根据偏差调整控制量。",
        },
    ]


def test_objective_scorer_appends_persistent_quiz_review_message_to_main_timeline():
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_objective_test_scorer_node(runtime, pass_score=80)

    result = node(
        {
            "node_quiz_items": _quiz_items(),
            "pending_interaction_answer": '{"Q1":"D","Q2":"B"}',
            "message_history": [{"role": "assistant", "kind": "objective_test_card", "content": "旧题卡"}],
            "current_node_id": "n1",
            "student_id": "s1",
        }
    )

    entries = result["message_history"]
    review_entries = [item for item in entries if item.get("kind") == "objective_quiz_review"]
    assert review_entries, "提交客观测评后应把作答与批改固化进主流程时间线，而不只保留临时 DOM 卡片"
    review = review_entries[-1]
    assert review["role"] == "assistant"
    assert "客观测评批改" in review["content"]
    assert "Q1" in review["content"]
    assert "你的答案：D" in review["content"]
    assert "正确答案：A" in review["content"]
    assert review["data"]["kind"] == "objective_test_answers"
    assert review["data"]["answers"] == {"Q1": "D", "Q2": "B"}
    assert len(review["data"]["questions"]) == 2


def test_wrong_question_explanations_are_persisted_before_variant_generation():
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_wrong_question_explainer_node(runtime)

    result = node(
        {
            "node_quiz_wrong_items": [
                {
                    "question_id": "Q1",
                    "stem": "比较点的作用是什么？",
                    "options": {"A": "形成偏差", "D": "与反馈无关"},
                    "answer_key": "A",
                    "user_answer": "D",
                    "explanation": "比较点把给定量与反馈量合成为偏差信号。",
                }
            ],
            "message_history": [
                {"role": "assistant", "kind": "objective_quiz_review", "content": "客观测评批改"}
            ],
            "current_node_name": "自动控制系统示例",
        }
    )

    entries = result["message_history"]
    kinds = [item.get("kind") for item in entries]
    assert "wrong_question_explanations" in kinds
    assert kinds.index("objective_quiz_review") < kinds.index("wrong_question_explanations")
    explanation_entry = entries[kinds.index("wrong_question_explanations")]
    assert "错题订正讲解" in explanation_entry["content"]
    assert "比较点" in explanation_entry["content"]
    assert result["learning_resume_target"] == "remediation_decision"

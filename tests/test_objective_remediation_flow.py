from ai_tutor_agent.core.ports import BufferedEventSink, RuntimeContext
from ai_tutor_agent.nodes.objective_remediation import (
    build_variant_question_generator_node,
    build_variant_test_answer_dialog_node,
    build_wrong_question_explainer_node,
)
from ai_tutor_agent.orchestration import workflow as workflow_module


class FakeAnswerProvider:
    def __init__(self, answer=""):
        self.answer = answer

    def get_answer(self, prompt, *, state=None):
        del prompt, state
        return self.answer


class FakeQuestionBank:
    def __init__(self):
        self.calls = []

    def get_variant_question(self, wrong_item):
        self.calls.append(wrong_item)
        return {
            "question_id": f"V-{wrong_item['question_id']}",
            "node_id": wrong_item.get("node_id", ""),
            "source_question_id": wrong_item["question_id"],
            "stem": f"变式：{wrong_item.get('stem', '')}",
            "options": wrong_item.get("options", {"A": "对", "B": "错"}),
            "answer_key": wrong_item.get("answer_key", "A"),
            "explanation": "变式解析",
        }


WRONG_ITEMS = [
    {
        "question_id": "Q1",
        "node_id": "KM001",
        "stem": "稳定性意味着什么？",
        "options": {"A": "回到平衡", "B": "持续发散"},
        "answer_key": "A",
        "user_answer": "B",
        "explanation": "稳定性强调扰动后回到或保持在平衡附近。",
    }
]


def test_wrong_question_explainer_creates_auditable_explanations_and_routes_to_variant_generator():
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_wrong_question_explainer_node(runtime)

    result = node({"node_quiz_wrong_items": WRONG_ITEMS, "node_quiz_score": 0})

    assert result["learning_phase"] == "node_quiz_remediation_explaining"
    assert result["learning_resume_target"] == "variant_question_generator"
    assert result["wrong_question_explanations"][0]["question_id"] == "Q1"
    assert "B" in result["wrong_question_explanations"][0]["user_answer"]
    assert "A" in result["wrong_question_explanations"][0]["answer_key"]


def test_variant_question_generator_uses_provider_and_pauses_for_variant_answers():
    provider = FakeQuestionBank()
    runtime = RuntimeContext(event_sink=BufferedEventSink(), question_bank_provider=provider)
    node = build_variant_question_generator_node(runtime)

    result = node({"current_node_id": "KM001", "node_quiz_wrong_items": WRONG_ITEMS})

    assert len(provider.calls) == 1
    assert result["variant_questions"][0]["question_id"] == "V-Q1"
    assert result["node_quiz_items"] == result["variant_questions"]
    assert result["flow_status"] == "awaiting_variant_answers"
    assert result["learning_resume_target"] == "variant_test_answer_dialog"
    assert result["pending_interaction_kind"] == "variant_test_answers"


def test_variant_test_answer_dialog_collects_answers_then_routes_to_objective_scorer():
    runtime = RuntimeContext(event_sink=BufferedEventSink(), answer_provider=FakeAnswerProvider("A"))
    node = build_variant_test_answer_dialog_node(runtime)
    variant_questions = [
        {"question_id": "V-Q1", "node_id": "KM001", "stem": "变式", "options": {"A": "对", "B": "错"}, "answer_key": "A"}
    ]

    first = node({"variant_questions": variant_questions})
    assert first["flow_status"] == "awaiting_variant_answers"
    assert first["learning_resume_target"] == "variant_test_answer_dialog"

    resumed = node(
        {
            "flow_status": "awaiting_variant_answers",
            "variant_questions": variant_questions,
            "pending_interaction_answer": {"V-Q1": "A"},
        }
    )
    assert resumed["flow_status"] == "normal"
    assert resumed["node_quiz_answers"] == {"V-Q1": "A"}
    assert resumed["node_quiz_items"] == variant_questions
    assert resumed["learning_resume_target"] == "objective_test_scorer"


def test_objective_scorer_failure_routes_to_wrong_question_explainer_not_inline_variant_loop():
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    from ai_tutor_agent.nodes.objective_test import build_objective_test_scorer_node

    node = build_objective_test_scorer_node(runtime, pass_score=80)
    result = node(
        {
            "current_node_id": "KM001",
            "node_quiz_items": WRONG_ITEMS,
            "node_quiz_answers": {"Q1": "B"},
        }
    )

    assert result["current_node_status"] == "quizzing"
    assert result["learning_resume_target"] == "wrong_question_explainer"
    assert result["flow_status"] == "normal"
    assert result["variant_questions"] == []


def test_workflow_routes_explicit_objective_remediation_nodes():
    assert workflow_module.get_entry_node({"learning_resume_target": "wrong_question_explainer"}) == "wrong_question_explainer"
    assert workflow_module.get_entry_node({"learning_resume_target": "variant_question_generator"}) == "variant_question_generator"
    assert workflow_module.get_entry_node({"flow_status": "awaiting_variant_answers"}) == "variant_test_answer_dialog"
    assert workflow_module.route_after_objective_test_scorer({"learning_resume_target": "wrong_question_explainer"}) == "wrong_question_explainer"
    assert workflow_module.route_after_wrong_question_explainer({"learning_resume_target": "variant_question_generator"}) == "variant_question_generator"
    assert workflow_module.route_after_variant_question_generator({"flow_status": "awaiting_variant_answers"}) == "pause"
    assert workflow_module.route_after_variant_test_answer_dialog({"learning_resume_target": "objective_test_scorer"}) == "objective_test_scorer"

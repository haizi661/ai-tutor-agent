from ai_tutor_agent.core.ports import BufferedEventSink, RuntimeContext
from ai_tutor_agent.nodes.homework_answer import (
    build_homework_answer_dialog_node,
    build_homework_explainer_node,
    build_homework_scorer_node,
)
from ai_tutor_agent.orchestration import workflow as workflow_module


class FakeAnswerProvider:
    def __init__(self, answer=""):
        self.answer = answer

    def get_answer(self, prompt, *, state=None):
        del prompt, state
        return self.answer


class FakeStudentStateStore:
    def __init__(self):
        self.saved = []

    def record_homework_result(self, student_id, *, homework_items, homework_answers, homework_score, homework_results):
        snapshot = {
            "student_id": student_id,
            "homework": [],
            "homework_history": [
                {
                    "items": homework_items,
                    "answers": homework_answers,
                    "score": homework_score,
                    "results": homework_results,
                }
            ],
        }
        self.saved.append(snapshot)
        return snapshot


HOMEWORK_ITEMS = [
    {
        "question_id": "HW-KM001",
        "node_id": "KM001",
        "prompt": "解释稳定性的核心判据。",
        "reference_answer": "稳定性要求系统受到扰动后能回到平衡状态，常用极点或李雅普诺夫方法判断。",
        "rubric": ["稳定性", "扰动", "平衡", "极点"],
    },
    {
        "question_id": "HW-KM002",
        "node_id": "KM002",
        "prompt": "负反馈为什么能改善鲁棒性？",
        "answer_key": "B",
        "options": {"A": "增强开环增益即可", "B": "抑制扰动和参数变化影响", "C": "取消动态环节", "D": "只改变传感器"},
    },
]


def test_homework_answer_dialog_pauses_when_no_answer_yet():
    runtime = RuntimeContext(event_sink=BufferedEventSink(), answer_provider=FakeAnswerProvider(""))
    node = build_homework_answer_dialog_node(runtime)

    result = node({"homework_items": HOMEWORK_ITEMS})

    assert result["flow_status"] == "awaiting_homework_answers"
    assert result["homework_status"] == "in_progress"
    assert result["learning_resume_target"] == "homework_answer_dialog"
    assert result["pending_interaction_kind"] == "homework_answers"


def test_homework_answer_dialog_collects_structured_answers_from_pending_answer():
    runtime = RuntimeContext(event_sink=BufferedEventSink(), answer_provider=FakeAnswerProvider(""))
    node = build_homework_answer_dialog_node(runtime)

    result = node(
        {
            "flow_status": "awaiting_homework_answers",
            "homework_items": HOMEWORK_ITEMS,
            "pending_interaction_answer": {"HW-KM001": "稳定性、扰动、平衡、极点", "HW-KM002": "B"},
        }
    )

    assert result["flow_status"] == "normal"
    assert result["learning_resume_target"] == "homework_scorer"
    assert result["homework_answers"]["HW-KM001"] == "稳定性、扰动、平衡、极点"
    assert result["homework_answers"]["HW-KM002"] == "B"


def test_homework_scorer_uses_answer_key_and_reference_terms_deterministically():
    store = FakeStudentStateStore()
    runtime = RuntimeContext(event_sink=BufferedEventSink(), student_state_store=store)
    node = build_homework_scorer_node(runtime)

    result = node(
        {
            "student_id": "stu-1",
            "homework_items": HOMEWORK_ITEMS,
            "homework_answers": {"HW-KM001": "稳定性 扰动 平衡 极点", "HW-KM002": "B"},
            "student_state_snapshot": {"homework": ["HW-KM001", "HW-KM002"]},
        }
    )

    assert result["homework_status"] == "scored"
    assert result["homework_score"] == 100
    assert all(item["is_correct"] for item in result["homework_results"])
    assert result["learning_resume_target"] == "homework_explainer"
    assert store.saved and store.saved[0]["homework"] == []


def test_homework_scorer_marks_wrong_objective_answer_without_llm_judgment():
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_homework_scorer_node(runtime)

    result = node(
        {
            "homework_items": HOMEWORK_ITEMS,
            "homework_answers": {"HW-KM001": "稳定性", "HW-KM002": "A"},
        }
    )

    objective_result = next(item for item in result["homework_results"] if item["question_id"] == "HW-KM002")
    assert objective_result["is_correct"] is False
    assert objective_result["expected"] == "B"
    assert result["homework_score"] < 100


def test_homework_explainer_archives_completed_homework_and_returns_to_resume_router():
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_homework_explainer_node(runtime)

    result = node(
        {
            "homework_items": HOMEWORK_ITEMS,
            "homework_results": [
                {"question_id": "HW-KM001", "is_correct": True, "feedback": "覆盖要点。"},
                {"question_id": "HW-KM002", "is_correct": False, "feedback": "应选择 B。"},
            ],
            "homework_score": 50,
        }
    )

    assert result["homework_status"] == "completed"
    assert result["homework_items"] == []
    assert result["homework_answers"] == {}
    assert result["learning_resume_target"] == "session_resume_router"
    assert "HW-KM002" in result["tutor_content"]


def test_workflow_routes_homework_answer_flow_nodes():
    assert workflow_module.get_entry_node({"flow_status": "awaiting_homework_answers"}) == "homework_answer_dialog"
    assert workflow_module.get_entry_node({"learning_resume_target": "homework_answer_dialog"}) == "homework_answer_dialog"
    assert workflow_module.get_entry_node({"learning_resume_target": "homework_scorer"}) == "homework_scorer"
    assert workflow_module.get_entry_node({"learning_resume_target": "homework_explainer"}) == "homework_explainer"
    assert workflow_module.route_after_homework_review({"flow_status": "awaiting_homework_answers"}) == "homework_answer_dialog"
    assert workflow_module.route_after_homework_answer_dialog({"learning_resume_target": "homework_scorer"}) == "homework_scorer"
    assert workflow_module.route_after_homework_answer_dialog({"flow_status": "awaiting_homework_answers"}) == "pause"
    assert workflow_module.route_after_homework_scorer({"learning_resume_target": "homework_explainer"}) == "homework_explainer"
    assert workflow_module.route_after_homework_explainer({"learning_resume_target": "session_resume_router"}) == "session_resume_router"

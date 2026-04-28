from ai_tutor_agent.core.ports import BufferedEventSink, RuntimeContext
from ai_tutor_agent.nodes.homework_review import build_homework_review_node
from ai_tutor_agent.nodes.session_resume_router import build_session_resume_router_node
from ai_tutor_agent.orchestration import workflow as workflow_module


class FakeGraphPipeline:
    def __init__(self):
        self.node_map = {
            "KM001": {"node_id": "KM001", "name": "稳定性", "recommended_next_nodes": ["KM002"]},
            "KM002": {"node_id": "KM002", "name": "负反馈", "recommended_next_nodes": []},
        }


class FakeAnswerProvider:
    def __init__(self, answer=""):
        self.answer = answer

    def get_answer(self, prompt, *, state=None):
        del prompt, state
        return self.answer


def test_session_resume_router_sends_existing_homework_to_homework_review():
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_session_resume_router_node(runtime)

    result = node(
        {
            "flow_status": "homework_assigned",
            "homework_status": "assigned",
            "homework_items": [{"question_id": "HW-KM001", "prompt": "复习稳定性。"}],
        }
    )

    assert result["flow_status"] == "normal"
    assert result["learning_phase"] == "homework_resume"
    assert result["learning_resume_target"] == "homework_review"
    assert result["learning_resume_reason"] == "existing_homework_found"


def test_session_resume_router_routes_pending_interaction_before_homework():
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_session_resume_router_node(runtime)

    result = node(
        {
            "flow_status": "awaiting_temporary_question",
            "homework_status": "assigned",
            "homework_items": [{"question_id": "HW-KM001", "prompt": "复习稳定性。"}],
        }
    )

    assert result["learning_resume_target"] == "temporary_question_collector"
    assert result["learning_resume_reason"] == "resume_pending_interaction"


def test_session_resume_router_without_homework_asks_consolidation_then_plans_next_node():
    runtime = RuntimeContext(event_sink=BufferedEventSink(), graph_rag_pipeline=FakeGraphPipeline())
    node = build_session_resume_router_node(runtime)

    # First call: no homework → asks consolidation choice
    result = node(
        {
            "student_state_snapshot": {"visited_nodes": ["KM001"], "wrong_nodes": []},
            "current_node_id": "KM001",
            "homework_items": [],
            "homework_status": "none",
        }
    )
    assert result["flow_status"] == "awaiting_consolidation_choice"
    assert result["pending_interaction_kind"] == "consolidation_choice"

    # Second call: user chose continue_learning → finds next node
    result2 = node(
        {
            "student_state_snapshot": {"visited_nodes": ["KM001"], "wrong_nodes": []},
            "current_node_id": "KM001",
            "homework_items": [],
            "homework_status": "none",
            "flow_status": "awaiting_consolidation_choice",
            "pending_interaction_answer": "continue_learning",
        }
    )
    assert result2["learning_phase"] == "next_node_planned"
    assert result2["learning_resume_target"] == "node_content_loader"
    assert result2["current_node_id"] == "KM002"
    assert result2["current_node_name"] == "负反馈"


def test_homework_review_pauses_and_waits_for_student_decision():
    runtime = RuntimeContext(event_sink=BufferedEventSink(), answer_provider=FakeAnswerProvider(""))
    node = build_homework_review_node(runtime)

    result = node({"homework_items": [{"question_id": "HW-KM001", "prompt": "复习稳定性。"}]})

    assert result["flow_status"] == "awaiting_homework_review_choice"
    assert result["learning_phase"] == "homework_resume"
    assert result["learning_resume_target"] == "homework_review"
    assert result["pending_interaction_kind"] == "homework_review_choice"


def test_homework_review_can_defer_homework_and_continue_learning():
    runtime = RuntimeContext(event_sink=BufferedEventSink(), answer_provider=FakeAnswerProvider("继续学习"))
    node = build_homework_review_node(runtime)

    result = node(
        {
            "flow_status": "awaiting_homework_review_choice",
            "pending_interaction_answer": "继续学习",
            "next_node_candidate_id": "KM002",
            "next_node_candidate_name": "负反馈",
            "homework_items": [{"question_id": "HW-KM001", "prompt": "复习稳定性。"}],
        }
    )

    assert result["homework_status"] == "deferred"
    assert result["learning_resume_target"] == "node_content_loader"
    assert result["current_node_id"] == "KM002"
    assert result["current_node_name"] == "负反馈"


def test_workflow_routes_session_resume_router_and_homework_review():
    assert workflow_module.get_entry_node({"learning_resume_target": "session_resume_router"}) == "session_resume_router"
    assert workflow_module.get_entry_node({"flow_status": "awaiting_homework_review_choice"}) == "homework_review"
    assert workflow_module.route_after_session_resume_router({"learning_resume_target": "homework_review"}) == "homework_review"
    assert workflow_module.route_after_session_resume_router({"learning_resume_target": "node_content_loader"}) == "node_content_loader"
    assert workflow_module.route_after_homework_review({"flow_status": "awaiting_homework_review_choice"}) == "pause"
    assert workflow_module.route_after_homework_review({"learning_resume_target": "node_content_loader"}) == "node_content_loader"

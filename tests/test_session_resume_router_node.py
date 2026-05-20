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


def test_resume_router_homework_with_missing_status_treated_as_active():
    """homework_items 非空但 homework_status 缺失时，应视为有活跃作业。"""
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_session_resume_router_node(runtime)

    result = node(
        {
            "flow_status": "normal",
            "homework_status": "",
            "homework_items": [{"question_id": "HW-001", "prompt": "测试题"}],
        }
    )

    assert result["learning_resume_target"] == "homework_review"
    assert result["learning_resume_reason"] == "existing_homework_found"


def test_resume_router_completed_homework_not_treated_as_active():
    """homework_status 为 completed 时不应视为活跃作业。"""
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_session_resume_router_node(runtime)

    result = node(
        {
            "flow_status": "normal",
            "homework_status": "completed",
            "homework_items": [{"question_id": "HW-001", "prompt": "测试题"}],
        }
    )

    assert result["learning_resume_target"] != "homework_review"


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


def test_session_resume_router_routes_homework_answer_pending_before_review():
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_session_resume_router_node(runtime)

    result = node(
        {
            "flow_status": "awaiting_homework_answers",
            "homework_status": "in_progress",
            "homework_items": [{"question_id": "HW-KM001", "prompt": "复习稳定性。"}],
        }
    )

    assert result["learning_resume_target"] == "homework_answer_dialog"
    assert result["learning_resume_reason"] == "resume_pending_interaction"


def test_session_resume_router_respects_deferred_homework_continue_choice():
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_session_resume_router_node(runtime)

    result = node(
        {
            "flow_status": "normal",
            "homework_status": "deferred",
            "homework_items": [{"question_id": "HW-KM001", "prompt": "复习稳定性。"}],
            "learning_resume_target": "node_content_loader",
        }
    )

    assert result["flow_status"] == "normal"
    assert result["learning_resume_target"] == "node_content_loader"
    assert result["learning_resume_reason"] == "homework_deferred_continue_learning"


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
    assert result["message_history"][-1]["kind"] == "homework_review_choice"
    assert result["message_history"][-1]["data"]["selected_value"] == "continue_learning"


def test_homework_review_can_save_homework_for_later_without_regenerating():
    runtime = RuntimeContext(event_sink=BufferedEventSink(), answer_provider=FakeAnswerProvider("稍后做"))
    node = build_homework_review_node(runtime)

    result = node(
        {
            "flow_status": "awaiting_homework_review_choice",
            "pending_interaction_answer": "稍后做",
            "homework_status": "assigned",
            "homework_items": [{"question_id": "HW-KM001", "prompt": "复习稳定性。"}],
        }
    )

    assert result["flow_status"] == "homework_assigned"
    assert result["homework_status"] == "assigned"
    assert result["learning_resume_target"] == "session_resume_router"
    assert result["learning_resume_reason"] == "homework_saved_for_later"
    assert result["pending_interaction_kind"] == ""
    assert result["message_history"][-1]["data"]["selected_value"] == "save_for_later"


def test_workflow_routes_session_resume_router_and_homework_review():
    assert workflow_module.get_entry_node({"learning_resume_target": "session_resume_router"}) == "session_resume_router"
    assert workflow_module.get_entry_node({"flow_status": "awaiting_homework_review_choice"}) == "homework_review"
    assert workflow_module.route_after_session_resume_router({"learning_resume_target": "homework_review"}) == "homework_review"
    assert workflow_module.route_after_session_resume_router({"learning_resume_target": "node_content_loader"}) == "node_content_loader"
    assert workflow_module.route_after_homework_review({"flow_status": "awaiting_homework_review_choice"}) == "pause"
    assert workflow_module.route_after_homework_review({"learning_resume_target": "node_content_loader"}) == "node_content_loader"


# ── Restore scenario coverage for remaining pending states ──


def test_resume_router_restores_awaiting_objective_answers():
    """Restoring from mid-quiz should route back to objective_test_scorer (re-score on resubmit)."""
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_session_resume_router_node(runtime)

    result = node({
        "flow_status": "awaiting_objective_answers",
        "current_node_id": "KM001",
        "node_quiz_items": [{"id": "Q1", "stem": "...", "options": {}, "answer_key": "A"}],
    })

    assert result["learning_resume_target"] == "objective_test_scorer"
    assert result["learning_resume_reason"] == "resume_pending_interaction"


def test_resume_router_restores_awaiting_variant_answers():
    """Restoring from variant quiz should route back to variant_test_answer_dialog."""
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_session_resume_router_node(runtime)

    result = node({
        "flow_status": "awaiting_variant_answers",
        "current_node_id": "KM001",
        "variant_questions": [{"id": "V1", "stem": "...", "options": {}, "answer_key": "B"}],
    })

    assert result["learning_resume_target"] == "variant_test_answer_dialog"
    assert result["learning_resume_reason"] == "resume_pending_interaction"


def test_resume_router_restores_awaiting_continue_or_homework_choice():
    """Restoring from continue/homework decision point should route back to selector."""
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_session_resume_router_node(runtime)

    result = node({
        "flow_status": "awaiting_continue_or_homework_choice",
        "current_node_id": "KM001",
        "next_node_candidate_id": "KM002",
    })

    assert result["learning_resume_target"] == "continue_or_homework_selector"
    assert result["learning_resume_reason"] == "resume_pending_interaction"


def test_resume_router_restores_awaiting_homework_review_choice():
    """Restoring from homework review decision should route back to homework_review."""
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_session_resume_router_node(runtime)

    result = node({
        "flow_status": "awaiting_homework_review_choice",
        "homework_status": "assigned",
        "homework_items": [{"question_id": "HW-KM001", "prompt": "复习稳定性。"}],
    })

    assert result["learning_resume_target"] == "homework_review"
    assert result["learning_resume_reason"] == "resume_pending_interaction"


def test_resume_router_restores_awaiting_interrupt_confirmation():
    """Restoring from interrupt confirmation should route back to interruption_tutor."""
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_session_resume_router_node(runtime)

    result = node({
        "flow_status": "awaiting_interrupt_confirmation",
        "interrupt_query": "为什么负反馈能提高稳定性？",
        "current_node_id": "KM001",
    })

    assert result["learning_resume_target"] == "interruption_tutor"
    assert result["learning_resume_reason"] == "resume_pending_interaction"


def test_resume_router_entry_node_mapping_for_all_pending_statuses():
    """get_entry_node should map all pending flow statuses to the correct workflow node."""
    cases = {
        "objective_test_scorer": "awaiting_objective_answers",
        "variant_test_answer_dialog": "awaiting_variant_answers",
        "continue_or_homework_selector": "awaiting_continue_or_homework_choice",
        "temporary_question_collector": "awaiting_temporary_question",
        "post_lesson_choice": "awaiting_post_lesson_choice",
        "homework_review": "awaiting_homework_review_choice",
        "homework_answer_dialog": "awaiting_homework_answers",
        "session_resume_router": "awaiting_consolidation_choice",
    }
    for expected_node, flow_status in cases.items():
        entry = workflow_module.get_entry_node({"flow_status": flow_status})
        assert entry == expected_node, f"flow_status={flow_status!r} should enter {expected_node}, got {entry}"

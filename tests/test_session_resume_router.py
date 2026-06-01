from ai_tutor_agent.core.learning_flow import build_learning_flow_scaffold, normalize_resume_target
from ai_tutor_agent.orchestration import workflow as workflow_module


def test_learning_flow_scaffold_preserves_new_explicit_resume_targets():
    state = {
        "learning_phase": "daily_wrapup",
        "learning_resume_target": "homework_generator",
        "flow_status": "normal",
    }

    patch = build_learning_flow_scaffold(state)

    assert patch == {}
    assert normalize_resume_target("temporary_question_collector") == "temporary_question_collector"
    assert normalize_resume_target("continue_or_homework_selector") == "continue_or_homework_selector"
    assert normalize_resume_target("homework_generator") == "homework_generator"
    assert normalize_resume_target("learning_plan_generator") == "learning_plan_generator"


def test_learning_flow_scaffold_preserves_skip_to_learning_plan_generator():
    state = {
        "learning_phase": "node_selection",
        "learning_resume_target": "learning_plan_generator",
        "flow_status": "normal",
    }

    patch = build_learning_flow_scaffold(state)

    assert patch == {}


def test_homework_assigned_second_login_scaffolds_to_session_resume_router():
    patch = build_learning_flow_scaffold(
        {
            "flow_status": "homework_assigned",
            "homework_status": "assigned",
            "homework_items": [{"question_id": "HW-KM001", "prompt": "复习稳定性。"}],
            "is_assessed": True,
        }
    )

    assert patch["learning_phase"] == "homework_resume"
    assert patch["learning_resume_target"] == "session_resume_router"


def test_workflow_entry_can_resume_all_new_strict_mainflow_nodes():
    assert workflow_module.get_entry_node({"learning_resume_target": "node_content_loader"}) == "node_content_loader"
    assert workflow_module.get_entry_node({"learning_resume_target": "temporary_question_collector"}) == "temporary_question_collector"
    assert workflow_module.get_entry_node({"learning_resume_target": "objective_test_scorer"}) == "objective_test_scorer"
    assert workflow_module.get_entry_node({"learning_resume_target": "continue_or_homework_selector"}) == "continue_or_homework_selector"
    assert workflow_module.get_entry_node({"learning_resume_target": "homework_generator"}) == "homework_generator"

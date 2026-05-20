from __future__ import annotations

from typing import Any, Mapping


PRE_TOPIC_FLOW_STATUSES = {
    "greeting",
    "topic_intake",
    "meta_qa",
    "smalltalk",
}

LEARNING_PHASES = {
    "topic_init",
    "pre_assessment",
    "profile_complete",
    "profiled",
    "node_selected",
    "node_content_loaded",
    "node_teaching",
    "post_lesson_choice",
    "temporary_question_collecting",
    "node_temp_qna",
    "node_quiz_batch",
    "node_quiz_remediation",
    "node_quiz_remediation_explaining",
    "node_quiz_variant_testing",
    "node_quiz_variant_scoring",
    "node_passed",
    "next_node_planned",
    "continue_or_homework_choice",
    "next_node_decision",
    "homework_generation_requested",
    "daily_wrapup",
    "homework_resume",
    "homework_answering",
    "homework_scoring",
    "homework_explanation",
    "homework_completed",
}

RESUME_TARGETS = {
    "intake_router",
    "greeter",
    "meta_qa",
    "smalltalk",
    "topic_confirmer",
    "assessment_generator",
    "assessment_dialog",
    "user_profiler",
    "initial_node_selector",
    "node_content_loader",
    "tutor",
    "interruption_tutor",
    "post_lesson_choice",
    "temporary_question_collector",
    "objective_test_generator",
    "objective_test_scorer",
    "wrong_question_explainer",
    "variant_question_generator",
    "variant_test_answer_dialog",
    "next_node_planner",
    "continue_or_homework_selector",
    "homework_generator",
    "session_resume_router",
    "homework_review",
    "homework_answer_dialog",
    "homework_scorer",
    "homework_explainer",
    "next_step_selector",
    "tester",
    "post_eval_selector",
    "post_eval_wrapup",
}


def normalize_learning_phase(value: Any) -> str:
    phase = str(value or "").strip()
    return phase if phase in LEARNING_PHASES else ""


def normalize_resume_target(value: Any) -> str:
    target = str(value or "").strip()
    return target if target in RESUME_TARGETS else ""


def infer_learning_phase(state: Mapping[str, Any] | None) -> str:
    values = state or {}
    flow_status = str(values.get("flow_status", "") or "")

    if flow_status in PRE_TOPIC_FLOW_STATUSES or flow_status in {
        "topic_confirmation_pending",
        "awaiting_topic_confirmation",
    }:
        return "topic_init"

    if flow_status in {"assessment_pending", "awaiting_assessment", "assessment_dialog"}:
        return "pre_assessment"
    if flow_status == "profiling":
        return "profile_complete"

    if values.get("interrupt_query") or flow_status == "awaiting_interrupt_confirmation":
        return "node_temp_qna"
    if flow_status == "awaiting_post_lesson_choice":
        return "post_lesson_choice"
    if flow_status == "awaiting_temporary_question":
        return "node_temp_qna"
    if flow_status == "awaiting_objective_answers":
        return "node_quiz_batch"
    if flow_status == "awaiting_variant_answers":
        return "node_quiz_variant_testing"
    if flow_status == "awaiting_continue_or_homework_choice":
        return "continue_or_homework_choice"
    if flow_status == "awaiting_consolidation_choice":
        return "homework_resume"
    if flow_status in {"homework_assigned", "awaiting_homework_review_choice", "awaiting_homework_answers"}:
        return "homework_resume"

    if flow_status == "awaiting_post_eval_selector":
        return "node_passed"
    if flow_status == "awaiting_next_step_selector":
        return "next_node_decision"

    if str(values.get("post_eval_choice", "") or "") == "summarize_wrapup":
        return "daily_wrapup"

    if str(values.get("practice_generation_mode", "") or "") == "same_type":
        return "node_quiz_remediation"

    if values.get("resume_tester") and values.get("tester_question"):
        return "node_quiz_batch"
    if str(values.get("next_step_choice", "") or "") == "practice_now":
        return "node_quiz_batch"

    if values.get("is_assessed"):
        return "node_teaching"

    return "topic_init"


def infer_resume_target(state: Mapping[str, Any] | None) -> str:
    values = state or {}
    flow_status = str(values.get("flow_status", "") or "")

    if values.get("interrupt_query") or flow_status == "awaiting_interrupt_confirmation":
        return "interruption_tutor"

    if flow_status == "assessment_dialog":
        return "assessment_dialog"
    if flow_status == "profiling":
        return "user_profiler"

    if flow_status in PRE_TOPIC_FLOW_STATUSES:
        if flow_status == "meta_qa":
            return "meta_qa"
        if flow_status == "smalltalk":
            return "smalltalk"
        if flow_status == "topic_intake":
            return "greeter"
        return "intake_router"

    if flow_status in {"topic_confirmation_pending", "awaiting_topic_confirmation"}:
        return "topic_confirmer"

    if flow_status == "awaiting_next_step_selector":
        return "next_step_selector"
    if flow_status == "awaiting_post_lesson_choice":
        return "post_lesson_choice"
    if flow_status == "awaiting_temporary_question":
        return "temporary_question_collector"
    if flow_status == "awaiting_objective_answers":
        return "objective_test_scorer"
    if flow_status == "awaiting_variant_answers":
        return "variant_test_answer_dialog"
    if flow_status == "awaiting_continue_or_homework_choice":
        return "continue_or_homework_selector"
    if flow_status == "awaiting_consolidation_choice":
        return "session_resume_router"
    if flow_status == "awaiting_homework_review_choice":
        return "homework_review"
    if flow_status == "homework_assigned":
        return "session_resume_router"
    if flow_status == "awaiting_homework_answers":
        return "homework_answer_dialog"
    if flow_status == "awaiting_post_eval_selector":
        return "post_eval_selector"

    if str(values.get("post_eval_choice", "") or "") == "summarize_wrapup":
        return "post_eval_wrapup"

    if str(values.get("practice_generation_mode", "") or "") == "same_type":
        return "tester"

    if values.get("resume_tester") and values.get("tester_question"):
        return "tester"
    if str(values.get("next_step_choice", "") or "") == "practice_now":
        return "tester"

    if flow_status == "direct_tutor" or values.get("is_assessed") or values.get("tutor_content"):
        return "tutor"

    return "assessment_generator"


def build_learning_flow_scaffold(state: Mapping[str, Any] | None) -> dict[str, Any]:
    values = state or {}
    patch: dict[str, Any] = {}

    phase = normalize_learning_phase(values.get("learning_phase")) or infer_learning_phase(values)
    if values.get("learning_phase") != phase:
        patch["learning_phase"] = phase

    resume_target = normalize_resume_target(values.get("learning_resume_target")) or infer_resume_target(values)
    if values.get("learning_resume_target") != resume_target:
        patch["learning_resume_target"] = resume_target

    return patch

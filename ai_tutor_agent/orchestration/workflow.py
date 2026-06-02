from typing import Optional

from langgraph.graph import END, StateGraph

from ..config import Settings
from ..core.learning_flow import normalize_resume_target
from ..core.ports import RuntimeContext
from ..core.state import AgentState
from ..infrastructure.checkpoint import create_sqlite_checkpointer
from ..infrastructure.llm import build_llms
from ..nodes.assessment import (
    build_assessment_generator_node,
    build_assessment_dialog_node,
    build_user_profiler_node,
)
from ..nodes.evaluator import build_evaluator_node
from ..nodes.intake import build_intake_router_node
from ..nodes.interruption import build_interruption_node
from ..nodes.initial_node_selector import build_initial_node_selector_node
from ..nodes.learning_plan_generator import build_learning_plan_generator_node
from ..nodes.meta import build_meta_node
from ..nodes.node_content_loader import build_node_content_loader_node
from ..nodes.objective_test import build_objective_test_generator_node, build_objective_test_scorer_node
from ..nodes.objective_remediation import (
    build_variant_question_generator_node,
    build_variant_test_answer_dialog_node,
    build_wrong_question_explainer_node,
)
from ..nodes.remediation_decision import build_remediation_decision_node, route_after_remediation_decision
from ..nodes.next_node_planner import build_next_node_planner_node
from ..nodes.continue_or_homework_selector import build_continue_or_homework_selector_node
from ..nodes.homework_generator import build_homework_generator_node
from ..nodes.session_resume_router import build_session_resume_router_node
from ..nodes.homework_review import build_homework_review_node
from ..nodes.homework_answer import (
    build_homework_answer_dialog_node,
    build_homework_explainer_node,
    build_homework_scorer_node,
)
from ..nodes.post_lesson_choice import build_post_lesson_choice_node
from ..nodes.temporary_question_collector import build_temporary_question_collector_node
from ..nodes.smalltalk import build_smalltalk_node
from ..nodes.tester import build_tester_node
from ..nodes.tutor import build_tutor_node
from ..nodes.greeting import build_greeting_node
from ..nodes.topic_confirm import build_topic_confirm_node
from ..nodes.coach import build_coach_node
from ..nodes.next_step import build_next_step_node
from ..nodes.post_eval import build_post_eval_selector_node, build_post_eval_wrapup_node
from .routing import build_route_logic


# ── 条件入口：决定初始节点 ──
def get_entry_node(state: AgentState) -> str:
    """
    路由逻辑:
    1. 如果 flow_status 是 'greeting'，且还没有明确主题，进入 greeter
    2. 如果 flow_status 是 'profiling'，进入 user_profiler
    3. 如果已经评估过 (is_assessed)，进入 tutor
    4. 如果有历史 tutor_content，进入 tutor
    5. 否则（已经有了 topic 但还没评测），进入 assessment_generator
    """
    resume_target = normalize_resume_target(state.get("learning_resume_target", ""))
    if resume_target:
        return resume_target

    if state.get("interrupt_query"):
        return "interruption_tutor"

    if state.get("flow_status") in {"greeting", "topic_intake", "meta_qa", "smalltalk"}:
        if state.get("flow_status") == "topic_intake":
            return "greeter"
        if state.get("flow_status") == "meta_qa":
            return "meta_qa"
        if state.get("flow_status") == "smalltalk":
            return "smalltalk"
        return "intake_router"

    if state.get("flow_status") in {"topic_confirmation_pending", "awaiting_topic_confirmation"}:
        return "topic_confirmer"
    if state.get("flow_status") == "awaiting_next_step_selector":
        return "next_step_selector"
    if state.get("flow_status") == "awaiting_post_lesson_choice":
        return "post_lesson_choice"
    if state.get("flow_status") == "awaiting_temporary_question":
        return "temporary_question_collector"
    if state.get("flow_status") == "awaiting_objective_answers":
        return "objective_test_scorer"
    if state.get("flow_status") == "awaiting_variant_answers":
        return "variant_test_answer_dialog"
    if state.get("flow_status") == "awaiting_remediation_decision":
        return "remediation_decision"
    if state.get("flow_status") == "awaiting_continue_or_homework_choice":
        return "continue_or_homework_selector"
    if state.get("flow_status") == "homework_assigned":
        return "session_resume_router"
    if state.get("flow_status") == "awaiting_consolidation_choice":
        return "session_resume_router"
    if state.get("flow_status") == "awaiting_homework_review_choice":
        return "homework_review"
    if state.get("flow_status") == "awaiting_homework_answers":
        return "homework_answer_dialog"
    if state.get("learning_resume_target") == "homework_generator":
        return "homework_generator"
    if state.get("learning_resume_target") == "node_content_loader":
        return "node_content_loader"
    if state.get("learning_resume_target") == "next_node_planner":
        return "next_node_planner"
    if state.get("learning_resume_target") == "remediation_decision":
        return "remediation_decision"
    if state.get("learning_resume_target") == "continue_or_homework_selector":
        return "continue_or_homework_selector"
    if state.get("flow_status") == "awaiting_post_eval_selector":
        return "post_eval_selector"

    if state.get("flow_status") == "direct_tutor":
        return "tutor"

    if state.get("flow_status") == "assessment_dialog":
        return "assessment_dialog"
    
    if state.get("flow_status") == "profiling":
        return "user_profiler"

    if state.get("resume_tester") and state.get("tester_question"):
        return "tester"

    if state.get("next_step_choice") == "practice_now":
        return "tester"

    if state.get("post_eval_choice") == "same_type_practice":
        return "tester"
    if state.get("post_eval_choice") == "continue_advance":
        return "tutor"
    if state.get("post_eval_choice") == "summarize_wrapup":
        return "post_eval_wrapup"

    if state.get("is_assessed", False):
        # 已完成诊断但还没有学习路径 → 先生成路径
        has_plan = bool(state.get("learning_plan"))
        if has_plan:
            # 如果已有教学内容，说明之前已经讲过了，不要重新生成。
            # 定位到 post_lesson_choice 等待用户选择下一步。
            if state.get("tutor_content"):
                return "post_lesson_choice"
            return "tutor"
        return "learning_plan_generator"
    
    # 不再把 tutor_content 存在当作"必须重新生成教学"的信号。
    # 上面 flow_status 检查（awaiting_post_lesson_choice 等）和
    # learning_resume_target 已覆盖了所有正常的恢复路由。
    # 如果到这里还没有匹配，走 assessment 重新评估。
    return "assessment_generator"


# ── Evaluator 之后的优化条件路由 ──
def route_after_evaluator(
    state: AgentState,
    pass_score: int,
    runtime_event_sink=None,
    knowledge_provider=None,
) -> str:
    decision = build_route_logic(pass_score, runtime_event_sink, knowledge_provider)(state)
    if decision == "pass":
        return "post_eval_selector"
    if decision == "remediate":
        return "coach"
    return "fail"


# ── greeter 之后的条件边 ──
def route_after_intake_router(state: AgentState) -> str:
    if state.get("flow_status") == "meta_qa":
        return "meta_qa"
    if state.get("flow_status") == "smalltalk":
        return "smalltalk"
    return "greeter"


def route_after_greeter(state: AgentState) -> str:
    if state.get("flow_status") == "greeting":
        return "pause"
    if state.get("flow_status") in {"topic_confirmation_pending", "awaiting_topic_confirmation"}:
        return "topic_confirmer"
    return "assessment_generator"


def route_after_topic_confirmer(state: AgentState) -> str:
    if state.get("flow_status") == "awaiting_topic_confirmation":
        return "pause"
    if state.get("flow_status") == "greeting":
        return "greeter"
    if normalize_resume_target(state.get("learning_resume_target", "")) == "learning_plan_generator":
        return "learning_plan_generator"
    if normalize_resume_target(state.get("learning_resume_target", "")) == "initial_node_selector":
        return "initial_node_selector"
    if state.get("flow_status") == "direct_tutor":
        return "tutor"
    return "assessment_generator"


# ── assessment_generator 之后的条件边 ──
def route_after_assessment_generator(state: AgentState) -> str:
    if normalize_resume_target(state.get("learning_resume_target", "")) == "initial_node_selector":
        return "initial_node_selector"
    if state.get("flow_status") == "awaiting_assessment":
        return "pause"
    if state.get("flow_status") == "assessment_dialog":
        return "pause"  # 等待用户回答第一道题
    return "user_profiler"


# ── assessment_dialog 之后的条件边 ──
def route_after_assessment_dialog(state: AgentState) -> str:
    if state.get("flow_status") == "profiling":
        return "user_profiler"
    # 还有下一题要等用户回答
    return "pause"


def route_after_user_profiler(state: AgentState) -> str:
    return "learning_plan_generator"


def route_after_initial_node_selector(state: AgentState) -> str:
    if state.get("current_node_id"):
        return "node_content_loader"
    return "tutor"


def route_after_node_content_loader(state: AgentState) -> str:
    return "tutor"


def route_after_tutor(state: AgentState) -> str:
    if state.get("interrupt_query"):
        return "interruption"
    if state.get("current_node_status") == "quick_check_pending":
        return "objective_test_generator"
    return "post_lesson_choice"


def route_after_post_lesson_choice(state: AgentState) -> str:
    if state.get("flow_status") == "awaiting_post_lesson_choice":
        return "pause"
    if state.get("post_lesson_choice") == "temporary_question" or state.get("interrupt_query"):
        return "temporary_question_collector"
    return "objective_test_generator"


def route_after_temporary_question_collector(state: AgentState) -> str:
    if state.get("flow_status") == "awaiting_temporary_question":
        return "pause"
    if state.get("interrupt_query"):
        return "interruption"
    return "pause"


def route_after_objective_test_generator(state: AgentState) -> str:
    if state.get("flow_status") == "awaiting_objective_answers":
        return "pause"
    return "objective_test_scorer"


def route_after_objective_test_scorer(state: AgentState) -> str:
    if state.get("current_node_status") == "passed":
        return "next_node_planner"
    if state.get("flow_status") == "awaiting_objective_answers":
        return "pause"
    target = normalize_resume_target(state.get("learning_resume_target", ""))
    if target == "wrong_question_explainer":
        return "wrong_question_explainer"
    if target == "remediation_decision":
        return "remediation_decision"
    if target == "objective_test_generator":
        return "objective_test_generator"
    if target == "next_node_planner":
        return "next_node_planner"
    return "pause"


def route_after_wrong_question_explainer(state: AgentState) -> str:
    target = normalize_resume_target(state.get("learning_resume_target", ""))
    if target == "remediation_decision":
        return "remediation_decision"
    if target == "variant_question_generator":
        return "variant_question_generator"
    return "pause"


def route_after_variant_question_generator(state: AgentState) -> str:
    if state.get("flow_status") == "awaiting_variant_answers":
        return "pause"
    if normalize_resume_target(state.get("learning_resume_target", "")) == "variant_test_answer_dialog":
        return "variant_test_answer_dialog"
    return "pause"


def route_after_variant_test_answer_dialog(state: AgentState) -> str:
    if state.get("flow_status") == "awaiting_variant_answers":
        return "pause"
    if normalize_resume_target(state.get("learning_resume_target", "")) == "objective_test_scorer":
        return "objective_test_scorer"
    return "pause"


def route_after_learning_plan_generator(state: AgentState) -> str:
    if state.get("learning_plan_source") == "all_mastered":
        return "continue_or_homework_selector"
    return "initial_node_selector"


def route_after_next_node_planner(state: AgentState) -> str:
    # 无论是否 plan_completed，都由 continue_or_homework_selector
    # 询问用户"开始新一轮 / 今天就到这里"，避免静默跳转。
    return "continue_or_homework_selector"


def route_after_continue_or_homework_selector(state: AgentState) -> str:
    if state.get("flow_status") == "awaiting_continue_or_homework_choice":
        return "pause"
    if state.get("continue_or_homework_choice") == "continue_next_node":
        return "node_content_loader"
    if state.get("continue_or_homework_choice") == "stop_today":
        return "homework_generator"
    if state.get("continue_or_homework_choice") == "start_next_round":
        return "learning_plan_generator"
    return "pause"


def route_after_session_resume_router(state: AgentState) -> str:
    if state.get("flow_status") == "awaiting_consolidation_choice":
        return "pause"
    target = normalize_resume_target(state.get("learning_resume_target", ""))
    if target in {
        "homework_review",
        "homework_generator",
        "temporary_question_collector",
        "objective_test_scorer",
        "wrong_question_explainer",
        "remediation_decision",
        "variant_question_generator",
        "variant_test_answer_dialog",
        "continue_or_homework_selector",
        "node_content_loader",
        "next_node_planner",
        "tutor",
        "post_lesson_choice",
    }:
        return target
    return "tutor"


def route_after_homework_review(state: AgentState) -> str:
    if state.get("flow_status") == "awaiting_homework_review_choice":
        return "pause"
    if state.get("flow_status") == "awaiting_homework_answers":
        return "homework_answer_dialog"
    target = normalize_resume_target(state.get("learning_resume_target", ""))
    if target in {"homework_answer_dialog", "node_content_loader", "next_node_planner", "tutor"}:
        return target
    return "pause"


def route_after_homework_answer_dialog(state: AgentState) -> str:
    if state.get("flow_status") == "awaiting_homework_answers":
        return "pause"
    if normalize_resume_target(state.get("learning_resume_target", "")) == "homework_scorer":
        return "homework_scorer"
    return "pause"


def route_after_homework_scorer(state: AgentState) -> str:
    if normalize_resume_target(state.get("learning_resume_target", "")) == "homework_explainer":
        return "homework_explainer"
    return "pause"


def route_after_homework_explainer(state: AgentState) -> str:
    if normalize_resume_target(state.get("learning_resume_target", "")) == "session_resume_router":
        return "session_resume_router"
    return "pause"


def route_after_next_step_selector(state: AgentState) -> str:
    if state.get("flow_status") == "awaiting_next_step_selector":
        return "pause"
    if state.get("interrupt_query"):
        return "interruption"
    if state.get("next_step_choice") == "practice_now":
        return "tester"
    return "tutor"


def route_after_post_eval_selector(state: AgentState) -> str:
    if state.get("flow_status") == "awaiting_post_eval_selector":
        return "pause"
    if state.get("post_eval_choice") == "same_type_practice":
        return "tester"
    if state.get("post_eval_choice") == "summarize_wrapup":
        return "post_eval_wrapup"
    return "tutor"


def route_after_tester(state: AgentState) -> str:
    if state.get("interrupt_query"):
        return "interruption"
    return "evaluator"


def route_after_interruption(state: AgentState) -> str:
    if state.get("flow_status") == "awaiting_interrupt_confirmation":
        return "pause"
    if state.get("resume_tester"):
        return "tester"
    # 如果中断问题引发了新话题，允许流转到 tutor 继续讲解
    if state.get("flow_status") == "direct_tutor":
        return "tutor"
    # 严格主流程：临时问题回答后回到讲解后选择，不直接进入旧 next_step。
    if state.get("flow_status") == "awaiting_post_lesson_choice" or state.get("learning_resume_target") == "post_lesson_choice":
        return "post_lesson_choice"
    # 兼容旧流程：如果中断后需要用户选择下一步
    if state.get("flow_status") == "awaiting_next_step_selector":
        return "next_step_selector"
    return "post_lesson_choice"


def build_workflow(
    settings: Settings,
    runtime: Optional[RuntimeContext] = None,
) -> StateGraph:
    runtime = runtime or RuntimeContext()
    tutor_llm, tester_llm, evaluator_llm = build_llms(settings)

    workflow = StateGraph(AgentState)

    # ========== 注册所有节点 ==========
    workflow.add_node("intake_router", build_intake_router_node(runtime.event_sink))
    workflow.add_node("greeter", build_greeting_node(tutor_llm, runtime.event_sink, runtime.answer_provider))
    workflow.add_node("meta_qa", build_meta_node(settings, tutor_llm, runtime.event_sink, runtime.answer_provider))
    workflow.add_node("smalltalk", build_smalltalk_node(tutor_llm, runtime.event_sink, runtime.answer_provider))
    workflow.add_node("topic_confirmer", build_topic_confirm_node(runtime.event_sink))
    
    workflow.add_node("initial_node_selector", build_initial_node_selector_node(runtime))
    workflow.add_node("learning_plan_generator", build_learning_plan_generator_node(tutor_llm, runtime))
    workflow.add_node("node_content_loader", build_node_content_loader_node(runtime))
    workflow.add_node("tutor", build_tutor_node(tutor_llm, runtime))
    workflow.add_node("interruption_tutor", build_interruption_node(tutor_llm, runtime))
    workflow.add_node("post_lesson_choice", build_post_lesson_choice_node(runtime.event_sink, runtime.answer_provider))
    workflow.add_node("temporary_question_collector", build_temporary_question_collector_node(runtime.event_sink))
    workflow.add_node("objective_test_generator", build_objective_test_generator_node(runtime, tester_llm))
    workflow.add_node("objective_test_scorer", build_objective_test_scorer_node(runtime, pass_score=settings.pass_score))
    workflow.add_node("wrong_question_explainer", build_wrong_question_explainer_node(runtime, tutor_llm))
    workflow.add_node("remediation_decision", build_remediation_decision_node(runtime.event_sink, runtime.answer_provider))
    workflow.add_node("variant_question_generator", build_variant_question_generator_node(runtime, tutor_llm))
    workflow.add_node("variant_test_answer_dialog", build_variant_test_answer_dialog_node(runtime))
    workflow.add_node("next_node_planner", build_next_node_planner_node(runtime))
    workflow.add_node("continue_or_homework_selector", build_continue_or_homework_selector_node(runtime))
    workflow.add_node("homework_generator", build_homework_generator_node(runtime))
    workflow.add_node("session_resume_router", build_session_resume_router_node(runtime))
    workflow.add_node("homework_review", build_homework_review_node(runtime))
    workflow.add_node("homework_answer_dialog", build_homework_answer_dialog_node(runtime))
    workflow.add_node("homework_scorer", build_homework_scorer_node(runtime, evaluator_llm))
    workflow.add_node("homework_explainer", build_homework_explainer_node(runtime, evaluator_llm))
    workflow.add_node("tester", build_tester_node(tester_llm, runtime))  # 统一传 runtime
    workflow.add_node("evaluator", build_evaluator_node(evaluator_llm, runtime))  # 统一传 runtime
    # 新增：Coach 助教节点
    workflow.add_node(
        "coach",
        build_coach_node(tutor_llm, runtime.event_sink, runtime.knowledge_provider)
    )
    workflow.add_node(
        "next_step_selector",
        build_next_step_node(runtime.event_sink, runtime.answer_provider, tutor_llm=tutor_llm, knowledge_provider=runtime.knowledge_provider),
    )
    workflow.add_node(
        "post_eval_selector",
        build_post_eval_selector_node(
            runtime.event_sink,
            runtime.answer_provider,
            graph_rag_pipeline=getattr(runtime, "graph_rag_pipeline", None),
        ),
    )
    workflow.add_node(
        "post_eval_wrapup",
        build_post_eval_wrapup_node(tutor_llm, runtime),
    )

    # 学前测评节点：注入图谱节点供 LLM 选概念，注入题库优先从题库出题
    graph_nodes = getattr(runtime.knowledge_provider, "course_graph_nodes", None) or {}
    workflow.add_node(
        "assessment_generator",
        build_assessment_generator_node(
            tutor_llm, runtime.event_sink,
            graph_nodes=graph_nodes,
            question_bank_provider=getattr(runtime, "question_bank_provider", None),
        ),
    )
    workflow.add_node(
        "assessment_dialog",
        build_assessment_dialog_node(runtime.event_sink),
    )
    workflow.add_node(
        "user_profiler",
        build_user_profiler_node(evaluator_llm, runtime.event_sink, getattr(runtime, "graph_rag_pipeline", None)),
    )

    # ========== 边和路由 ==========
    
    # Intake / Greeter 边
    workflow.add_conditional_edges(
        "intake_router",
        route_after_intake_router,
        {
            "meta_qa": "meta_qa",
            "smalltalk": "smalltalk",
            "greeter": "greeter",
        }
    )
    workflow.add_edge("meta_qa", "intake_router")
    workflow.add_edge("smalltalk", "intake_router")
    workflow.add_conditional_edges(
        "greeter",
        route_after_greeter,
        {
            "pause": END,
            "topic_confirmer": "topic_confirmer",
            "assessment_generator": "assessment_generator",
        }
    )
    workflow.add_conditional_edges(
        "topic_confirmer",
        route_after_topic_confirmer,
        {
            "pause": END,
            "greeter": "greeter",
            "tutor": "tutor",
            "learning_plan_generator": "learning_plan_generator",
            "initial_node_selector": "initial_node_selector",
            "assessment_generator": "assessment_generator",
        }
    )

    # 学前测评边
    workflow.add_conditional_edges(
        "assessment_generator",
        route_after_assessment_generator,
        {"pause": END, "user_profiler": "user_profiler", "initial_node_selector": "initial_node_selector"},
    )
    workflow.add_conditional_edges(
        "assessment_dialog",
        route_after_assessment_dialog,
        {"pause": END, "user_profiler": "user_profiler"},
    )
    workflow.add_conditional_edges(
        "user_profiler",
        route_after_user_profiler,
        {"learning_plan_generator": "learning_plan_generator"},
    )
    workflow.add_conditional_edges(
        "learning_plan_generator",
        route_after_learning_plan_generator,
        {
            "initial_node_selector": "initial_node_selector",
            "continue_or_homework_selector": "continue_or_homework_selector",
        },
    )
    workflow.add_conditional_edges(
        "initial_node_selector",
        route_after_initial_node_selector,
        {"node_content_loader": "node_content_loader", "tutor": "tutor"},
    )
    workflow.add_conditional_edges(
        "node_content_loader",
        route_after_node_content_loader,
        {"tutor": "tutor"},
    )

    # 主教学闭环边
    workflow.add_conditional_edges(
        "tutor",
        route_after_tutor,
        {
            "interruption": "interruption_tutor",
            "post_lesson_choice": "post_lesson_choice",
        },
    )
    workflow.add_conditional_edges(
        "post_lesson_choice",
        route_after_post_lesson_choice,
        {
            "pause": END,
            "temporary_question_collector": "temporary_question_collector",
            "objective_test_generator": "objective_test_generator",
        },
    )
    workflow.add_conditional_edges(
        "temporary_question_collector",
        route_after_temporary_question_collector,
        {
            "pause": END,
            "interruption": "interruption_tutor",
        },
    )
    workflow.add_conditional_edges(
        "objective_test_generator",
        route_after_objective_test_generator,
        {
            "pause": END,
            "objective_test_scorer": "objective_test_scorer",
        },
    )
    workflow.add_conditional_edges(
        "objective_test_scorer",
        route_after_objective_test_scorer,
        {
            "pause": END,
            "wrong_question_explainer": "wrong_question_explainer",
            "remediation_decision": "remediation_decision",
            "objective_test_generator": "objective_test_generator",
            "next_node_planner": "next_node_planner",
        },
    )
    workflow.add_conditional_edges(
        "wrong_question_explainer",
        route_after_wrong_question_explainer,
        {"pause": END, "remediation_decision": "remediation_decision", "variant_question_generator": "variant_question_generator"},
    )
    workflow.add_conditional_edges(
        "remediation_decision",
        route_after_remediation_decision,
        {
            "pause": END,
            "variant_question_generator": "variant_question_generator",
            "node_content_loader": "node_content_loader",
            "continue_or_homework_selector": "continue_or_homework_selector",
        },
    )
    workflow.add_conditional_edges(
        "variant_question_generator",
        route_after_variant_question_generator,
        {"pause": END, "variant_test_answer_dialog": "variant_test_answer_dialog"},
    )
    workflow.add_conditional_edges(
        "variant_test_answer_dialog",
        route_after_variant_test_answer_dialog,
        {"pause": END, "objective_test_scorer": "objective_test_scorer"},
    )
    workflow.add_conditional_edges(
        "next_node_planner",
        route_after_next_node_planner,
        {
            "continue_or_homework_selector": "continue_or_homework_selector",
        },
    )
    workflow.add_conditional_edges(
        "continue_or_homework_selector",
        route_after_continue_or_homework_selector,
        {
            "pause": END,
            "node_content_loader": "node_content_loader",
            "homework_generator": "homework_generator",
        },
    )
    workflow.add_edge("homework_generator", END)
    workflow.add_conditional_edges(
        "session_resume_router",
        route_after_session_resume_router,
        {
            "pause": END,
            "homework_review": "homework_review",
            "homework_generator": "homework_generator",
            "temporary_question_collector": "temporary_question_collector",
            "objective_test_scorer": "objective_test_scorer",
            "wrong_question_explainer": "wrong_question_explainer",
            "remediation_decision": "remediation_decision",
            "variant_question_generator": "variant_question_generator",
            "variant_test_answer_dialog": "variant_test_answer_dialog",
        },
    )
    workflow.add_conditional_edges(
        "homework_review",
        route_after_homework_review,
        {
            "pause": END,
            "homework_answer_dialog": "homework_answer_dialog",
            "node_content_loader": "node_content_loader",
            "next_node_planner": "next_node_planner",
            "tutor": "tutor",
        },
    )
    workflow.add_conditional_edges(
        "homework_answer_dialog",
        route_after_homework_answer_dialog,
        {"pause": END, "homework_scorer": "homework_scorer"},
    )
    workflow.add_conditional_edges(
        "homework_scorer",
        route_after_homework_scorer,
        {"pause": END, "homework_explainer": "homework_explainer"},
    )
    workflow.add_conditional_edges(
        "homework_explainer",
        route_after_homework_explainer,
        {"pause": END, "session_resume_router": "session_resume_router"},
    )
    workflow.add_conditional_edges(
        "next_step_selector",
        route_after_next_step_selector,
        {
            "pause": END,
            "interruption": "interruption_tutor",
            "tester": "tester",
            "tutor": "tutor",
        },
    )
    workflow.add_conditional_edges(
        "post_eval_selector",
        route_after_post_eval_selector,
        {
            "pause": END,
            "tester": "tester",
            "tutor": "tutor",
            "post_eval_wrapup": "post_eval_wrapup",
        },
    )
    workflow.add_edge("post_eval_wrapup", END)
    workflow.add_conditional_edges(
        "tester",
        route_after_tester,
        {
            "interruption": "interruption_tutor",
            "evaluator": "evaluator",
        },
    )
    workflow.add_conditional_edges(
        "interruption_tutor",
        route_after_interruption,
        {
            "tester": "tester",
            "tutor": "tutor",
            "next_step_selector": "next_step_selector",
            "post_lesson_choice": "post_lesson_choice",
            "pause": END,
        },
    )
    
    # 核心优化：Evaluator 后的分流
    workflow.add_conditional_edges(
        "evaluator",
        lambda s: route_after_evaluator(s, settings.pass_score, runtime.event_sink, runtime.knowledge_provider),
        {
            "post_eval_selector": "post_eval_selector",
            "coach": "coach",
            "fail": "tutor",
        },
    )
    
    # Coach 引导后，不强制立刻再考，交给下一步选择器决定
    workflow.add_edge("coach", "next_step_selector")

    # ========== 条件入口 ==========
    workflow.set_conditional_entry_point(
        get_entry_node,
        {
            "intake_router": "intake_router",
            "greeter": "greeter",
            "meta_qa": "meta_qa",
            "smalltalk": "smalltalk",
            "topic_confirmer": "topic_confirmer",
            "interruption_tutor": "interruption_tutor",
            "initial_node_selector": "initial_node_selector",
            "node_content_loader": "node_content_loader",
            "post_lesson_choice": "post_lesson_choice",
            "temporary_question_collector": "temporary_question_collector",
            "objective_test_generator": "objective_test_generator",
            "objective_test_scorer": "objective_test_scorer",
            "wrong_question_explainer": "wrong_question_explainer",
            "remediation_decision": "remediation_decision",
            "variant_question_generator": "variant_question_generator",
            "variant_test_answer_dialog": "variant_test_answer_dialog",
            "next_node_planner": "next_node_planner",
            "continue_or_homework_selector": "continue_or_homework_selector",
            "homework_generator": "homework_generator",
            "session_resume_router": "session_resume_router",
            "homework_review": "homework_review",
            "homework_answer_dialog": "homework_answer_dialog",
            "homework_scorer": "homework_scorer",
            "homework_explainer": "homework_explainer",
            "next_step_selector": "next_step_selector",
            "post_eval_selector": "post_eval_selector",
            "post_eval_wrapup": "post_eval_wrapup",
            "tutor": "tutor",
            "tester": "tester",
            "assessment_generator": "assessment_generator",
            "assessment_dialog": "assessment_dialog",
            "user_profiler": "user_profiler",
        },
    )

    return workflow


def create_app_with_sqlite_checkpointer(
    settings: Settings,
    runtime: Optional[RuntimeContext] = None,
):
    memory, conn = create_sqlite_checkpointer(settings.memory_db_path)
    app = build_workflow(settings, runtime=runtime).compile(checkpointer=memory)
    return app, conn

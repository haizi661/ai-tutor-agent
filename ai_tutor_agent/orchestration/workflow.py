from typing import Optional

from langgraph.graph import END, StateGraph

from ..config import Settings
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
from ..nodes.meta import build_meta_node
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
        return "tutor"
    
    if state.get("tutor_content"):
        return "tutor"

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
    if state.get("flow_status") == "direct_tutor":
        return "tutor"
    return "assessment_generator"


# ── assessment_generator 之后的条件边 ──
def route_after_assessment_generator(state: AgentState) -> str:
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


def route_after_tutor(state: AgentState) -> str:
    if state.get("interrupt_query"):
        return "interruption"
    return "next_step_selector"


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
    # 如果中断后需要用户选择下一步
    if state.get("flow_status") == "awaiting_next_step_selector":
        return "next_step_selector"
    return "pause"


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
    
    workflow.add_node("tutor", build_tutor_node(tutor_llm, runtime))
    workflow.add_node("interruption_tutor", build_interruption_node(tutor_llm, runtime))
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
        build_post_eval_selector_node(runtime.event_sink, runtime.answer_provider),
    )
    workflow.add_node(
        "post_eval_wrapup",
        build_post_eval_wrapup_node(tutor_llm, runtime.event_sink),
    )

    # 学前测评节点：注入图谱节点供 LLM 选概念
    graph_nodes = getattr(runtime.knowledge_provider, "course_graph_nodes", None) or {}
    workflow.add_node(
        "assessment_generator",
        build_assessment_generator_node(tutor_llm, runtime.event_sink, graph_nodes=graph_nodes),
    )
    workflow.add_node(
        "assessment_dialog",
        build_assessment_dialog_node(runtime.event_sink),
    )
    workflow.add_node(
        "user_profiler",
        build_user_profiler_node(evaluator_llm, runtime.event_sink),
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
            "assessment_generator": "assessment_generator",
        }
    )

    # 学前测评边
    workflow.add_conditional_edges(
        "assessment_generator",
        route_after_assessment_generator,
        {"pause": END, "user_profiler": "user_profiler"},
    )
    workflow.add_conditional_edges(
        "assessment_dialog",
        route_after_assessment_dialog,
        {"pause": END, "user_profiler": "user_profiler"},
    )
    workflow.add_edge("user_profiler", "tutor")

    # 主教学闭环边
    workflow.add_conditional_edges(
        "tutor",
        route_after_tutor,
        {
            "interruption": "interruption_tutor",
            "next_step_selector": "next_step_selector",
        },
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

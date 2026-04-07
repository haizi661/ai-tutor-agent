from typing import Optional

from langgraph.graph import END, StateGraph

from ..config import Settings
from ..core.ports import RuntimeContext
from ..core.state import AgentState
from ..infrastructure.checkpoint import create_sqlite_checkpointer
from ..infrastructure.llm import build_llms
from ..nodes.assessment import (
    build_assessment_generator_node,
    build_user_profiler_node,
)
from ..nodes.evaluator import build_evaluator_node
from ..nodes.intake import build_intake_router_node
from ..nodes.meta import build_meta_node
from ..nodes.smalltalk import build_smalltalk_node
from ..nodes.tester import build_tester_node
from ..nodes.tutor import build_tutor_node
from ..nodes.greeting import build_greeting_node
from ..nodes.topic_confirm import build_topic_confirm_node
from ..nodes.interruption import build_interruption_node
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
    
    if state.get("flow_status") == "profiling":
        return "user_profiler"

    if state.get("is_assessed", False):
        return "tutor"
    
    if state.get("tutor_content"):
        return "tutor"

    return "assessment_generator"


# ── greeter 之后的条件边 ──
def route_after_intake_router(state: AgentState) -> str:
    if state.get("flow_status") == "meta_qa":
        return "meta_qa"
    if state.get("flow_status") == "smalltalk":
        return "smalltalk"
    return "greeter"


def route_after_greeter(state: AgentState) -> str:
    """
    如果 greeter 没确认 topic，图暂停到 END (等待用户继续发消息)。
    如果确认了 topic (flow_status 变成了 awaiting_assessment)，继续流转到 assessment_generator。
    """
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
    return "assessment_generator"


# ── assessment_generator 之后的条件边 ──
def route_after_assessment_generator(state: AgentState) -> str:
    """
    如果 flow_status == 'awaiting_assessment'，图暂停到 END，
    等待前端提交答案 + API update_state 后重新 invoke。
    否则继续流转到 user_profiler（在恢复执行时触发）。
    """
    if state.get("flow_status") == "awaiting_assessment":
        return "pause"
    return "user_profiler"


def route_after_tester(state: AgentState) -> str:
    if state.get("interrupt_query"):
        return "interruption"
    return "evaluator"


def route_after_interruption(state: AgentState) -> str:
    if state.get("flow_status") == "awaiting_interrupt_confirmation":
        return "pause"
    if state.get("resume_tester"):
        return "tester"
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
    workflow.add_node("topic_confirmer", build_topic_confirm_node(runtime.event_sink, runtime.answer_provider))
    
    workflow.add_node("tutor", build_tutor_node(tutor_llm, runtime))
    workflow.add_node("interruption_tutor", build_interruption_node(tutor_llm, runtime))
    workflow.add_node("tester", build_tester_node(tester_llm, runtime)) # 统一传 runtime
    workflow.add_node("evaluator", build_evaluator_node(evaluator_llm, runtime)) # 统一传 runtime

    # 学前测评节点
    workflow.add_node(
        "assessment_generator",
        build_assessment_generator_node(tutor_llm, runtime.event_sink),
    )
    workflow.add_node(
        "user_profiler",
        build_user_profiler_node(evaluator_llm, runtime),
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
            "assessment_generator": "assessment_generator",
        }
    )

    # 学前测评边
    workflow.add_conditional_edges(
        "assessment_generator",
        route_after_assessment_generator,
        {"pause": END, "user_profiler": "user_profiler"},
    )
    workflow.add_edge("user_profiler", "tutor")
    #调试用#raise ValueError("DEBUG: 如果你能看到这个报错，说明 workflow.py 加载正确！")

    # 主教学闭环边
    workflow.add_edge("tutor", "tester")
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
            "pause": END,
        },
    )
    workflow.add_conditional_edges(
        "evaluator",
        build_route_logic(settings.pass_score, runtime.event_sink),
        {"pass": END, "fail": "tutor"},
    )

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
            "tutor": "tutor",
            "assessment_generator": "assessment_generator",
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

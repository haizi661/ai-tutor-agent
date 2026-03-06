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
from ..nodes.tester import build_tester_node
from ..nodes.tutor import build_tutor_node
from .routing import build_route_logic


# ── 条件入口：决定是否需要学前测评 ──
def check_assessment_needed(state: AgentState) -> str:
    """
    路由逻辑:
    1. 已完成画像 → tutor
    2. 有历史 tutor_content（兼容旧会话）→ tutor
    3. 否则 → assessment_generator（学前测评）
    """
    if state.get("is_assessed", False):
        return "tutor"
    if state.get("tutor_content"):
        return "tutor"
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


def build_workflow(
    settings: Settings,
    runtime: Optional[RuntimeContext] = None,
) -> StateGraph:
    runtime = runtime or RuntimeContext()
    tutor_llm, tester_llm, evaluator_llm = build_llms(settings)

    workflow = StateGraph(AgentState)

    # ========== 注册所有节点 ==========
    workflow.add_node("tutor", build_tutor_node(tutor_llm, runtime))
    workflow.add_node(
        "tester",
        build_tester_node(tester_llm, runtime.event_sink, runtime.answer_provider),
    )
    workflow.add_node(
        "evaluator",
        build_evaluator_node(evaluator_llm, runtime.event_sink),
    )

    # 学前测评节点
    workflow.add_node(
        "assessment_generator",
        build_assessment_generator_node(tutor_llm, runtime.event_sink),
    )
    workflow.add_node(
        "user_profiler",
        build_user_profiler_node(evaluator_llm, runtime.event_sink),
    )

    # ========== 主教学闭环边 ==========
    workflow.add_edge("tutor", "tester")
    workflow.add_edge("tester", "evaluator")
    workflow.add_conditional_edges(
        "evaluator",
        build_route_logic(settings.pass_score, runtime.event_sink),
        {"pass": END, "fail": "tutor"},
    )

    # ========== 学前测评边 ==========
    # assessment_generator → 条件分叉：暂停(END) 或 继续(user_profiler)
    workflow.add_conditional_edges(
        "assessment_generator",
        route_after_assessment_generator,
        {"pause": END, "user_profiler": "user_profiler"},
    )
    # user_profiler 完成后 → 进入主教学闭环
    workflow.add_edge("user_profiler", "tutor")

    # ========== 条件入口 ==========
    workflow.set_conditional_entry_point(
        check_assessment_needed,
        {
            "tutor": "tutor",
            "assessment_generator": "assessment_generator",
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

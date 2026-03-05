from typing import Optional

from langgraph.graph import END, StateGraph

from ..config import Settings
from ..core.ports import RuntimeContext
from ..core.state import AgentState
from ..infrastructure.checkpoint import create_sqlite_checkpointer
from ..infrastructure.llm import build_llms
from ..nodes.assessment import (
    build_assessment_conductor_node,
    build_assessment_generator_node,
    build_user_profiler_node,
)
from ..nodes.evaluator import build_evaluator_node
from ..nodes.tester import build_tester_node
from ..nodes.tutor import build_tutor_node
from .routing import build_route_logic


def check_assessment_needed(state: AgentState) -> str:
    # If the user has already been assessed, proceed to tutor
    if state.get("is_assessed", False):
        return "tutor"
    
    # Compatibility: If tutor_content is already present (e.g. legacy session),
    # assume we can skip assessment to avoid interrupting ongoing learning.
    if state.get("tutor_content"):
        return "tutor"

    # Otherwise, start assessment
    return "assessment_generator"


def build_workflow(
    settings: Settings,
    runtime: Optional[RuntimeContext] = None,
) -> StateGraph:
    runtime = runtime or RuntimeContext()
    tutor_llm, tester_llm, evaluator_llm = build_llms(settings)

    workflow = StateGraph(AgentState)
    
    # 1. Add Nodes
    workflow.add_node("tutor", build_tutor_node(tutor_llm, runtime.event_sink))
    workflow.add_node(
        "tester",
        build_tester_node(tester_llm, runtime.event_sink, runtime.answer_provider),
    )
    workflow.add_node(
        "evaluator",
        build_evaluator_node(evaluator_llm, runtime.event_sink),
    )
    
    # New Assessment Nodes
    workflow.add_node(
        "assessment_generator", 
        build_assessment_generator_node(tutor_llm, runtime.event_sink)
    )
    workflow.add_node(
        "assessment_conductor",
        build_assessment_conductor_node(runtime.event_sink, runtime.answer_provider)
    )
    workflow.add_node(
        "user_profiler",
        build_user_profiler_node(evaluator_llm, runtime.event_sink) # Use evaluator for strict scoring
    )

    # 2. Add Edges for Main Loop
    workflow.add_edge("tutor", "tester")
    workflow.add_edge("tester", "evaluator")

    workflow.add_conditional_edges(
        "evaluator",
        build_route_logic(settings.pass_score, runtime.event_sink),
        {
            "pass": END,
            "fail": "tutor",
        },
    )
    
    # 3. Add Edges for Assessment Flow
    workflow.add_edge("assessment_generator", "assessment_conductor")
    workflow.add_edge("assessment_conductor", "user_profiler")
    workflow.add_edge("user_profiler", "tutor") # Assessment done, start learning

    # 4. Set Conditional Entry Point
    workflow.set_conditional_entry_point(
        check_assessment_needed,
        {
            "tutor": "tutor",
            "assessment_generator": "assessment_generator",
        }
    )

    return workflow


def create_app_with_sqlite_checkpointer(
    settings: Settings,
    runtime: Optional[RuntimeContext] = None,
):
    memory, conn = create_sqlite_checkpointer(settings.memory_db_path)
    app = build_workflow(settings, runtime=runtime).compile(checkpointer=memory)
    return app, conn

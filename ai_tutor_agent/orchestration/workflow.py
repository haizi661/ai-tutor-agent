from typing import Optional

from langgraph.graph import END, StateGraph

from ..config import Settings
from ..core.ports import RuntimeContext
from ..core.state import AgentState
from ..infrastructure.checkpoint import create_sqlite_checkpointer
from ..infrastructure.llm import build_llms
from ..nodes.evaluator import build_evaluator_node
from ..nodes.tester import build_tester_node
from ..nodes.tutor import build_tutor_node
from .routing import build_route_logic


def build_workflow(
    settings: Settings,
    runtime: Optional[RuntimeContext] = None,
) -> StateGraph:
    runtime = runtime or RuntimeContext()
    tutor_llm, tester_llm, evaluator_llm = build_llms(settings)

    workflow = StateGraph(AgentState)
    workflow.add_node("tutor", build_tutor_node(tutor_llm, runtime))
    workflow.add_node(
        "tester",
        build_tester_node(tester_llm, runtime.event_sink, runtime.answer_provider),
    )
    workflow.add_node(
        "evaluator",
        build_evaluator_node(evaluator_llm, runtime.event_sink),
    )

    workflow.set_entry_point("tutor")
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
    return workflow


def create_app_with_sqlite_checkpointer(
    settings: Settings,
    runtime: Optional[RuntimeContext] = None,
):
    memory, conn = create_sqlite_checkpointer(settings.memory_db_path)
    app = build_workflow(settings, runtime=runtime).compile(checkpointer=memory)
    return app, conn

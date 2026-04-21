from ai_tutor_agent.knowledge_map.builders.graph_query_planner_v2 import GraphQueryPlanner
from ai_tutor_agent.knowledge_map.builders.graph_traverser import GraphTraverser
from ai_tutor_agent.knowledge_map.graph_rag_pipeline import GraphRAGPipeline


def test_graph_query_planner_uses_mode_override_without_llm():
    planner = GraphQueryPlanner(llm=None)

    plan = planner.plan("什么是自动控制的一般概念？", traversal_mode="focused")

    assert plan.traversal_mode == "focused"
    assert plan.max_depth == 1
    assert "HAS_SUBTOPIC" in plan.preferred_relations


def test_graph_traverser_prefers_local_semantic_neighborhood():
    edges = [
        {"source": "KM001", "target": "KM002", "relation": "HAS_SUBTOPIC"},
        {"source": "KM002", "target": "KM003", "relation": "LEADS_TO"},
        {"source": "KM003", "target": "KM004", "relation": "RELATED_TO"},
    ]
    traverser = GraphTraverser(edges)

    traversed = traverser.traverse(
        anchor_nodes=[{"node_id": "KM001", "name": "自动控制", "summary": "自动控制概念", "tags": ["自动控制"]}],
        anchor_terms=["自动控制"],
        question_type="knowledge_qa",
        preferred_relations=["HAS_SUBTOPIC", "LEADS_TO"],
        max_depth=2,
        node_budget=5,
    )

    assert traversed[0].node_id == "KM001"
    assert any(item.node_id == "KM002" and item.hop == 1 for item in traversed)
    assert any(item.node_id == "KM003" and item.hop == 2 for item in traversed)
    assert all(item.node_id != "KM004" for item in traversed)


def test_graph_rag_pipeline_runs_on_current_outputs_without_llm():
    pipeline = GraphRAGPipeline(enable_llm=False)

    result = pipeline.ask("学习线性系统的时域分析法之前要先学什么？", traversal_mode="balanced")

    assert result["plan"]["question_type"] == "prerequisite_query"
    assert result["anchor_nodes"]
    assert result["traversed_nodes"]
    assert result["evidence_items"]
    assert "依据：" in result["answer"]


def test_graph_rag_pipeline_includes_formula_and_figure_assets():
    pipeline = GraphRAGPipeline(enable_llm=False)

    result = pipeline.ask("一阶系统的时域分析有什么典型公式和图表？", traversal_mode="balanced")

    assert result["media_items"]
    assert any(item["asset_type"] == "formula" for item in result["media_items"])
    assert any(item["asset_type"] == "figure" for item in result["media_items"])
    assert "相关公式与图表：" not in result["answer"]


def test_graph_rag_pipeline_defaults_visual_llm_off():
    pipeline = GraphRAGPipeline(enable_llm=False)

    assert pipeline.media_enricher.visual_analyzer is None

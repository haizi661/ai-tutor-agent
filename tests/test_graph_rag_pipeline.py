from ai_tutor_agent.knowledge_map.builders.graph_query_planner_v2 import GraphQueryPlanner
from ai_tutor_agent.knowledge_map.builders.graph_traverser import GraphTraverser
from ai_tutor_agent.knowledge_map.builders.node_selector import NodeSelector
from ai_tutor_agent.knowledge_map.graph_rag_pipeline import GraphRAGPipeline


def test_graph_query_planner_uses_mode_override_without_llm():
    planner = GraphQueryPlanner(llm=None)

    plan = planner.plan("什么是自动控制的一般概念？", traversal_mode="focused")

    assert plan.traversal_mode == "focused"
    assert plan.max_depth == 1
    assert "parallel_to" in plan.preferred_relations


def test_node_selector_prefers_graph_21_teaching_attributes():
    selector = NodeSelector()
    nodes = [
        {
            "node_id": "KM001",
            "name": "自动控制的一般概念",
            "summary": "介绍自动控制基础。",
            "tags": ["自动控制"],
            "core_concepts": ["反馈控制系统"],
            "assessment_focus": "概念",
            "importance_level": "核心",
            "extra": {
                "retrieval_keywords": ["反馈控制", "控制系统组成"],
                "node_role": "chapter_anchor",
            },
        },
        {
            "node_id": "KM002",
            "name": "自动控制的基本原理与方式",
            "summary": "介绍开环与闭环。",
            "tags": ["开环控制", "闭环控制"],
            "core_concepts": ["开环控制"],
            "assessment_focus": "原理",
            "importance_level": "一般",
            "extra": {},
        },
    ]

    selected = selector.select_node("反馈控制系统的组成是什么", nodes)

    assert selected is not None
    assert selected["node_id"] == "KM001"


def test_graph_traverser_prefers_graph_21_relations_and_edge_metadata():
    node_map = {
        "KM001": {"node_id": "KM001", "name": "自动控制", "importance_level": "核心"},
        "KM002": {"node_id": "KM002", "name": "数学模型", "importance_level": "重要", "core_concepts": ["传递函数"]},
        "KM003": {"node_id": "KM003", "name": "时域分析", "assessment_focus": "分析"},
        "KM004": {"node_id": "KM004", "name": "稳态误差"},
    }
    edges = [
        {
            "edge_id": "E001",
            "source": "KM001",
            "target": "KM002",
            "relation": "prerequisite_of",
            "relation_type": "prerequisite_of",
            "direction_type": "directed",
            "weight": 1.0,
            "relation_strength": 1.0,
            "source_type": "config_prerequisite",
            "relation_note": "显式配置的前置知识关系",
            "evidence": "自动控制是数学模型的前置知识",
        },
        {
            "edge_id": "E002",
            "source": "KM002",
            "target": "KM003",
            "relation": "parallel_to",
            "relation_type": "parallel_to",
            "direction_type": "undirected",
            "weight": 0.9,
            "relation_strength": 0.9,
        },
        {
            "edge_id": "E003",
            "source": "KM003",
            "target": "KM004",
            "relation": "related_to",
            "relation_type": "related_to",
            "direction_type": "undirected",
            "weight": 0.8,
            "relation_strength": 0.8,
        },
    ]
    traverser = GraphTraverser(edges, node_map=node_map)

    traversed = traverser.traverse(
        anchor_nodes=[
            {
                "node_id": "KM001",
                "name": "自动控制",
                "summary": "自动控制概念",
                "tags": ["自动控制"],
                "core_concepts": ["反馈"],
            }
        ],
        anchor_terms=["自动控制"],
        question_type="knowledge_qa",
        preferred_relations=["prerequisite_of", "parallel_to"],
        max_depth=2,
        node_budget=5,
    )

    assert traversed[0].node_id == "KM001"
    assert any(item.node_id == "KM002" and item.hop == 1 for item in traversed)
    assert any(item.node_id == "KM003" and item.hop == 2 for item in traversed)
    assert all(item.node_id != "KM004" for item in traversed)
    second = next(item for item in traversed if item.node_id == "KM002")
    assert second.relation_reference == "E001"
    assert second.relation_note == "显式配置的前置知识关系"


def test_graph_rag_pipeline_runs_on_current_outputs_without_llm():
    pipeline = GraphRAGPipeline(enable_llm=False)

    result = pipeline.ask("学习线性系统的时域分析法之前要先学什么？", traversal_mode="balanced")

    assert result["plan"]["question_type"] == "prerequisite_query"
    assert result["anchor_nodes"]
    assert result["traversed_nodes"]
    assert result["evidence_items"]
    assert result["plan"]["preferred_relations"][0] == "prerequisite_of"
    assert any(item["relation_direction"] == "reverse" for item in result["traversed_nodes"][1:4])
    assert any(item["attribute"] == "relation_path" for item in result["evidence_items"])
    assert "依据：" in result["answer"]


def test_graph_rag_pipeline_includes_formula_and_figure_assets():
    pipeline = GraphRAGPipeline(enable_llm=False)

    result = pipeline.ask("控制系统的复数域数学模型有什么典型公式和图表？", traversal_mode="balanced")

    assert result["media_items"]
    assert any(item["asset_type"] == "formula" for item in result["media_items"])
    assert any(item["asset_type"] == "figure" for item in result["media_items"])
    assert "相关公式与图表：" not in result["answer"]


def test_graph_rag_pipeline_defaults_visual_llm_off():
    pipeline = GraphRAGPipeline(enable_llm=False)

    assert pipeline.media_enricher.visual_analyzer is None

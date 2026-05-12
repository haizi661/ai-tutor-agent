from pathlib import Path

from ai_tutor_agent.knowledge_map.builders.graph_query_planner_v2 import GraphQueryPlanner
from ai_tutor_agent.knowledge_map.builders.graph_traverser import GraphTraverser
from ai_tutor_agent.knowledge_map.builders.node_selector import NodeSelector
from ai_tutor_agent.knowledge_map.graph_rag_pipeline import GraphRAGPipeline


FIXTURE_CACHE_ROOT = Path("tests/fixtures/mineru_cache")
FIXTURE_NODES_CSV = "tests/fixtures/knowledge_map_outputs/auto_control_knowledge_map_v2_nodes.csv"
FIXTURE_EDGES_CSV = "tests/fixtures/knowledge_map_outputs/auto_control_knowledge_map_v2_edges.csv"
FIXTURE_MEDIA_INDEX = "tests/fixtures/media_evidence_index"


def _build_fixture_pipeline() -> GraphRAGPipeline:
    return GraphRAGPipeline(
        nodes_csv_path=FIXTURE_NODES_CSV,
        edges_csv_path=FIXTURE_EDGES_CSV,
        mineru_cache_root=str(FIXTURE_CACHE_ROOT),
        annotated_assets_path=FIXTURE_MEDIA_INDEX,
        enable_llm=False,
    )


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

    selected = selector.select_node("反馈控制系统的组成是什么？", nodes)

    assert selected is not None
    assert selected["node_id"] == "KM001"


def test_node_selector_matches_chinese_query_to_english_domain_alias():
    selector = NodeSelector()
    nodes = [
        {
            "node_id": "KM012",
            "name": "线性系统的时域分析法",
            "summary": "研究时间响应和稳态误差。",
            "tags": ["时域分析", "时间响应"],
            "core_concepts": ["时域分析", "时间响应"],
            "assessment_focus": "分析",
            "importance_level": "核心",
            "extra": {
                "retrieval_keywords": ["时域分析", "时间响应"],
                "node_role": "chapter_anchor",
            },
        },
        {
            "node_id": "KM029",
            "name": "频率域稳定判据",
            "summary": "介绍 Nyquist 稳定性判据等频域稳定分析方法。",
            "tags": ["Nyquist", "稳定判据"],
            "core_concepts": ["频率域稳定判据", "Nyquist", "频率特性"],
            "assessment_focus": "分析",
            "importance_level": "重要",
            "extra": {
                "retrieval_keywords": ["频域分析", "Nyquist", "频率响应"],
                "node_role": "topic",
            },
        },
    ]

    selected = selector.select_node("奈奎斯特曲线有什么作用？", nodes)

    assert selected is not None
    assert selected["node_id"] == "KM029"


def test_node_selector_prefers_feedback_control_topic_over_generic_disturbance_overlap():
    selector = NodeSelector()
    nodes = [
        {
            "node_id": "KM002",
            "name": "自动控制的基本原理与方式",
            "summary": "介绍反馈控制原理、开环控制方式和复合控制方式。",
            "tags": ["反馈控制", "开环控制"],
            "core_concepts": ["反馈控制", "闭环控制", "按偏差控制"],
            "assessment_focus": "原理",
            "importance_level": "核心",
            "extra": {
                "retrieval_keywords": ["反馈控制", "负反馈控制", "控制方式"],
                "node_role": "topic",
            },
        },
        {
            "node_id": "KM018",
            "name": "线性系统的稳态误差计算",
            "summary": "研究稳态误差的概念、类型及计算方法。",
            "tags": ["稳态误差", "误差系数"],
            "core_concepts": ["稳态误差", "反馈", "扰动"],
            "assessment_focus": "计算",
            "importance_level": "核心",
            "extra": {
                "retrieval_keywords": ["稳态误差", "误差系数", "扰动"],
                "node_role": "topic",
            },
        },
    ]

    selected = selector.select_node("为什么反馈控制能够抑制扰动？", nodes)

    assert selected is not None
    assert selected["node_id"] == "KM002"


def test_graph_traverser_prefers_graph_21_relations_and_edge_metadata():
    node_map = {
        "KM001": {"node_id": "KM001", "name": "自动控制", "importance_level": "核心"},
        "KM002": {
            "node_id": "KM002",
            "name": "数学模型",
            "importance_level": "重要",
            "core_concepts": ["传递函数"],
        },
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


def test_graph_rag_pipeline_runs_on_fixture_without_llm():
    pipeline = _build_fixture_pipeline()

    result = pipeline.ask("控制系统的复数域数学模型有什么典型公式和图表？", traversal_mode="balanced")

    assert result["plan"]["question_type"] == "knowledge_qa"
    assert result["anchor_nodes"]
    assert result["traversed_nodes"]
    assert result["evidence_items"]
    assert any(item["attribute"] == "relation_path" for item in result["evidence_items"])
    assert result["subgraph_roles"]["primary_nodes"]
    anchor_id = result["anchor_nodes"][0]["node_id"]
    assert result["subgraph_roles"]["node_roles"][anchor_id] == "primary"
    assert "依据：" in result["answer"]


def test_graph_rag_pipeline_includes_annotated_fixture_media():
    pipeline = _build_fixture_pipeline()

    result = pipeline.ask("控制系统的复数域数学模型有什么典型公式和图表？", traversal_mode="balanced")

    assert result["media_items"]
    assert any(item["asset_type"] == "formula" for item in result["media_items"])
    assert any(item["asset_type"] == "figure" for item in result["media_items"])
    assert any(item["is_primary"] is True for item in result["media_items"])
    assert sum(1 for item in result["media_items"] if item["is_primary"]) <= 3
    assert all(item["display_label"].startswith(("式", "图")) for item in result["media_items"])
    references = {str(item["reference"]) for item in result["media_items"]}
    assert "chapter_p33-81:formula:7e5687fd92f8" in references


def test_graph_rag_pipeline_defaults_visual_llm_off():
    pipeline = _build_fixture_pipeline()

    assert pipeline.media_enricher.visual_analyzer is None


def test_graph_rag_pipeline_prefers_fixture_formula_for_transfer_function_question():
    pipeline = _build_fixture_pipeline()

    result = pipeline.ask("传递函数有什么典型公式？", traversal_mode="balanced")

    assert result["media_items"]
    assert any(
        str(item["reference"]).startswith("chapter_p33-81:formula:")
        for item in result["media_items"]
    )
    assert any(
        item["asset_type"] == "formula" and item.get("analysis_hint")
        for item in result["media_items"]
    )

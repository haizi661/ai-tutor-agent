from ai_tutor_agent.course_assets import get_course_assets, normalize_course_id
from ai_tutor_agent.knowledge_map.graph_rag_pipeline import GraphRAGPipeline


def test_course_assets_resolve_known_aliases():
    assert normalize_course_id("a2-control-theory") == "auto_control"
    assert normalize_course_id("ai") == "artificial_intelligence"

    ai_assets = get_course_assets("artificial_intelligence")
    assert ai_assets.display_name == "人工智能"
    assert ai_assets.source_materials_dir.endswith("course_materials/artificial_intelligence")
    assert ai_assets.nodes_csv_path.endswith("artificial_intelligence/ai_nodes.csv")
    assert ai_assets.student_state_path.endswith("artificial_intelligence/student_state.json")


def test_graph_rag_pipeline_can_select_course_assets(monkeypatch):
    captured = {}

    def fake_load_nodes(self):
        captured["nodes_csv_path"] = self.nodes_csv_path.as_posix()
        return [{"node_id": "AI001", "name": "人工智能导论"}]

    def fake_load_edges(self):
        captured["edges_csv_path"] = self.edges_csv_path.as_posix()
        return []

    monkeypatch.setattr(GraphRAGPipeline, "_load_nodes", fake_load_nodes)
    monkeypatch.setattr(GraphRAGPipeline, "_load_edges", fake_load_edges)
    monkeypatch.setattr(GraphRAGPipeline, "_build_tutor_llm", lambda *args, **kwargs: None)
    monkeypatch.setattr(GraphRAGPipeline, "_build_visual_analyzer", lambda *args, **kwargs: None)

    pipeline = GraphRAGPipeline(course_id="artificial_intelligence", enable_llm=False)

    assert pipeline.course_assets.course_id == "artificial_intelligence"
    assert captured["nodes_csv_path"].endswith("data/knowledge_map_outputs/artificial_intelligence/ai_nodes.csv")
    assert captured["edges_csv_path"].endswith("data/knowledge_map_outputs/artificial_intelligence/ai_edges.csv")

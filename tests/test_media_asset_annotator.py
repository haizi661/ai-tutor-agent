from pathlib import Path

from ai_tutor_agent.knowledge_map.config.media_index_config import MediaIndexConfig
from ai_tutor_agent.knowledge_map.media_index.media_asset_annotator import MediaAssetAnnotator
from ai_tutor_agent.knowledge_map.media_index.media_asset_scanner import MediaAssetScanner
from ai_tutor_agent.knowledge_map.media_index.media_candidate_filter import MediaCandidateFilter
from ai_tutor_agent.knowledge_map.media_index.media_node_linker import MediaNodeLinker


FIXTURE_CACHE_ROOT = Path("tests/fixtures/mineru_cache")
FIXTURE_DOC_DIR = FIXTURE_CACHE_ROOT / "chapter_p33-81"
FIXTURE_NODES_CSV = "tests/fixtures/knowledge_map_outputs/auto_control_knowledge_map_v2_nodes.csv"


def _load_linked_assets():
    config = MediaIndexConfig(mineru_cache_root=FIXTURE_CACHE_ROOT, min_image_bytes=0)
    scanner = MediaAssetScanner(config=config)
    candidate_filter = MediaCandidateFilter(config=config)
    linker = MediaNodeLinker(nodes_csv_path=FIXTURE_NODES_CSV, config=config)
    candidates = scanner.scan_document(FIXTURE_DOC_DIR)
    filtered = candidate_filter.filter_candidates(candidates)
    linked = linker.link_candidates(filtered)
    return config, linked


def test_media_asset_annotator_extracts_formula_meaning_and_variables():
    config, linked = _load_linked_assets()
    annotator = MediaAssetAnnotator(config=config)

    target = next(
        item
        for item in linked
        if item["asset_type"] == "formula" and "G(s)" in str(item.get("raw_text", ""))
    )
    annotated = annotator.annotate_assets([target])[0]

    assert annotated["visual_type"] == "equation"
    assert "定量关系" in annotated["formula_meaning"]
    assert "G" in annotated["variables"]
    assert annotated["relation_statement"]


def test_media_asset_annotator_extracts_figure_affordances_from_fixture():
    config, linked = _load_linked_assets()
    annotator = MediaAssetAnnotator(config=config)

    target = next(
        item
        for item in linked
        if item["asset_type"] == "figure" and "图 4-3" in str(item.get("caption_text", ""))
    )
    annotated = annotator.annotate_assets([target])[0]

    assert annotated["visual_type"] == "trend_curve"
    assert annotated["retrieval_keywords"]
    assert "compare_parameters" in annotated["question_affordances"]


def test_media_asset_annotator_builds_retrieval_keywords_and_confidence():
    config, linked = _load_linked_assets()
    annotator = MediaAssetAnnotator(config=config)

    annotated = annotator.annotate_assets(linked[:5])

    assert len(annotated) == 2
    assert all(item["retrieval_keywords"] for item in annotated)
    assert all(0.0 <= float(item["confidence"]) <= 1.0 for item in annotated)


def test_media_asset_annotator_persists_structured_vision_fields_for_figures():
    class FakeVisualAnalyzer:
        def analyze_figure(self, *args, **kwargs):
            return {
                "visual_summary": "该图展示反馈控制系统中信号比较、控制器和反馈通道的关系。",
                "visual_key_elements": ["输入端", "比较环节", "控制器", "反馈通道"],
                "visual_relations": ["输出经反馈后再次与输入比较形成闭环调节。"],
                "teaching_focus": ["强调闭环结构如何抑制扰动。"],
                "confidence": 0.82,
                "vision_model": "fake-qwen-vl",
            }

    config, linked = _load_linked_assets()
    annotator = MediaAssetAnnotator(config=config, visual_analyzer=FakeVisualAnalyzer())

    target = next(item for item in linked if item["asset_type"] == "figure")
    annotated = annotator.annotate_assets([target], enable_visual=True)[0]

    assert annotated["visual_summary"]
    assert annotated["visual_key_elements"]
    assert annotated["visual_relations"]
    assert annotated["teaching_focus"]
    assert float(annotated["vision_confidence"]) == 0.82
    assert annotated["vision_model"] == "fake-qwen-vl"
    assert "visual_summary" in annotated["llm_generated_fields"]
    assert "visual_relations" in annotated["llm_generated_fields"]
    assert annotated["extra"]["visual_summary"] == annotated["visual_summary"]

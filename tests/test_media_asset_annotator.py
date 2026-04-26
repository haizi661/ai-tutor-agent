from ai_tutor_agent.knowledge_map.config.media_index_config import MediaIndexConfig
from ai_tutor_agent.knowledge_map.media_index.media_asset_annotator import MediaAssetAnnotator
from ai_tutor_agent.knowledge_map.media_index.media_asset_scanner import MediaAssetScanner
from ai_tutor_agent.knowledge_map.media_index.media_candidate_filter import MediaCandidateFilter
from ai_tutor_agent.knowledge_map.media_index.media_node_linker import MediaNodeLinker


DOC_DIR = "data/mineru_cache/chapter_03_p082-159_线性系统的时域分析法__082fadd0"


def _load_linked_assets():
    config = MediaIndexConfig()
    scanner = MediaAssetScanner(config=config)
    candidate_filter = MediaCandidateFilter(config=config)
    linker = MediaNodeLinker(config=config)
    candidates = scanner.scan_document(DOC_DIR)
    filtered = candidate_filter.filter_candidates(candidates)
    linked = linker.link_candidates(filtered)
    return config, linked


def test_media_asset_annotator_extracts_formula_meaning_and_variables():
    config, linked = _load_linked_assets()
    annotator = MediaAssetAnnotator(config=config)

    target = next(
        item
        for item in linked
        if item["asset_type"] == "formula"
        and "\\sigma \\%" in str(item.get("raw_text", ""))
        and "\\zeta" in str(item.get("raw_text", ""))
    )
    annotated = annotator.annotate_assets([target])[0]

    assert annotated["visual_type"] == "equation"
    assert "超调量" in annotated["formula_meaning"]
    assert any("\\zeta" in item or "ζ" in item for item in annotated["variables"])
    assert annotated["relation_statement"]


def test_media_asset_annotator_extracts_readable_claims_from_figure():
    config, linked = _load_linked_assets()
    annotator = MediaAssetAnnotator(config=config)

    target = next(
        item
        for item in linked
        if item["asset_type"] == "figure" and "图 3-12" in str(item.get("caption_text", ""))
    )
    annotated = annotator.annotate_assets([target])[0]

    assert annotated["visual_type"] == "trend_curve"
    assert annotated["direct_readable_claims"]
    assert any("阻尼比越大" in claim or "超调量越小" in claim for claim in annotated["direct_readable_claims"])
    assert "compare_parameters" in annotated["question_affordances"]


def test_media_asset_annotator_builds_retrieval_keywords_and_confidence():
    config, linked = _load_linked_assets()
    annotator = MediaAssetAnnotator(config=config)

    annotated = annotator.annotate_assets(linked[:5])

    assert len(annotated) == 5
    assert all(item["retrieval_keywords"] for item in annotated)
    assert all(0.0 <= float(item["confidence"]) <= 1.0 for item in annotated)

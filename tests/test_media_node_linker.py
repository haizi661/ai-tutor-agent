from ai_tutor_agent.knowledge_map.config.media_index_config import MediaIndexConfig
from ai_tutor_agent.knowledge_map.media_index.media_asset_scanner import MediaAssetScanner
from ai_tutor_agent.knowledge_map.media_index.media_candidate_filter import MediaCandidateFilter
from ai_tutor_agent.knowledge_map.media_index.media_node_linker import MediaNodeLinker


DOC_DIR = "data/mineru_cache/chapter_03_p082-159_线性系统的时域分析法__082fadd0"


def _load_filtered_candidates():
    config = MediaIndexConfig()
    scanner = MediaAssetScanner(config=config)
    candidate_filter = MediaCandidateFilter(config=config)
    return config, candidate_filter.filter_candidates(scanner.scan_document(DOC_DIR))


def test_media_node_linker_links_figure_312_to_second_order_related_node():
    config, candidates = _load_filtered_candidates()
    linker = MediaNodeLinker(config=config)

    target = next(
        item
        for item in candidates
        if item["asset_type"] == "figure" and "图 3-12" in str(item.get("caption_text", ""))
    )
    linked = linker.link_candidates([target])[0]

    assert linked["anchor_node_id"] in {"KM013", "KM015"}
    assert linked["anchor_node_name"] in {"系统时间响应的性能指标", "二阶系统的时域分析"}
    assert "KM015" in linked["linked_node_ids"] or "KM013" in linked["linked_node_ids"]


def test_media_node_linker_links_sigma_formula_to_second_order_related_node():
    config, candidates = _load_filtered_candidates()
    linker = MediaNodeLinker(config=config)

    target = next(
        item
        for item in candidates
        if item["asset_type"] == "formula"
        and "\\sigma \\%" in str(item.get("raw_text", ""))
        and "\\zeta" in str(item.get("raw_text", ""))
    )
    linked = linker.link_candidates([target])[0]

    assert linked["anchor_node_id"] in {"KM013", "KM015"}
    assert linked["linked_node_ids"]
    assert linked["link_scores"]


def test_media_node_linker_outputs_ranked_node_fields():
    config, candidates = _load_filtered_candidates()
    linker = MediaNodeLinker(config=config)

    linked = linker.link_candidates(candidates[:3])

    assert len(linked) == 3
    assert all("linked_node_ids" in item for item in linked)
    assert all("anchor_node_id" in item for item in linked)
    assert all(isinstance(item["link_scores"], list) for item in linked)

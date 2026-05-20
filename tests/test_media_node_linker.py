from pathlib import Path

from ai_tutor_agent.knowledge_map.config.media_index_config import MediaIndexConfig
from ai_tutor_agent.knowledge_map.media_index.media_asset_scanner import MediaAssetScanner
from ai_tutor_agent.knowledge_map.media_index.media_candidate_filter import MediaCandidateFilter
from ai_tutor_agent.knowledge_map.media_index.media_node_linker import MediaNodeLinker


FIXTURE_CACHE_ROOT = Path("tests/fixtures/mineru_cache")
FIXTURE_DOC_DIR = FIXTURE_CACHE_ROOT / "chapter_p33-81"
FIXTURE_NODES_CSV = "tests/fixtures/knowledge_map_outputs/auto_control_knowledge_map_v2_nodes.csv"


def _load_filtered_candidates():
    config = MediaIndexConfig(mineru_cache_root=FIXTURE_CACHE_ROOT, min_image_bytes=0)
    scanner = MediaAssetScanner(config=config)
    candidate_filter = MediaCandidateFilter(config=config)
    return config, candidate_filter.filter_candidates(scanner.scan_document(FIXTURE_DOC_DIR))


def test_media_node_linker_links_formula_to_complex_domain_model_node():
    config, candidates = _load_filtered_candidates()
    linker = MediaNodeLinker(nodes_csv_path=FIXTURE_NODES_CSV, config=config)

    target = next(
        item
        for item in candidates
        if item["asset_type"] == "formula" and "G(s)" in str(item.get("raw_text", ""))
    )
    linked = linker.link_candidates([target])[0]

    assert linked["anchor_node_id"] == "KM003"
    assert linked["anchor_node_name"] == "控制系统的复数域数学模型"
    assert linked["linked_node_ids"] == ["KM003"]


def test_media_node_linker_preserves_empty_links_for_unmatched_figure():
    config, candidates = _load_filtered_candidates()
    linker = MediaNodeLinker(nodes_csv_path=FIXTURE_NODES_CSV, config=config)

    target = next(
        item
        for item in candidates
        if item["asset_type"] == "figure" and "图 4-3" in str(item.get("caption_text", ""))
    )
    linked = linker.link_candidates([target])[0]

    assert linked["anchor_node_id"] == ""
    assert linked["linked_node_ids"] == []
    assert linked["link_scores"] == []


def test_media_node_linker_outputs_ranked_node_fields():
    config, candidates = _load_filtered_candidates()
    linker = MediaNodeLinker(nodes_csv_path=FIXTURE_NODES_CSV, config=config)

    linked = linker.link_candidates(candidates)

    assert len(linked) == 2
    assert all("linked_node_ids" in item for item in linked)
    assert all("anchor_node_id" in item for item in linked)
    assert all(isinstance(item["link_scores"], list) for item in linked)

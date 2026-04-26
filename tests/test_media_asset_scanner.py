from ai_tutor_agent.knowledge_map.config.media_index_config import MediaIndexConfig
from ai_tutor_agent.knowledge_map.media_index.media_asset_scanner import MediaAssetScanner


def test_media_asset_scanner_extracts_figures_and_formulas_from_chapter_03():
    config = MediaIndexConfig()
    scanner = MediaAssetScanner(config=config)

    candidates = scanner.scan_document(
        "data/mineru_cache/chapter_03_p082-159_线性系统的时域分析法__082fadd0"
    )

    assert candidates
    assert any(item["asset_type"] == "figure" for item in candidates)
    assert any(item["asset_type"] == "formula" for item in candidates)
    assert any("图 3-12" in item["caption_text"] for item in candidates if item["asset_type"] == "figure")


def test_media_asset_scanner_candidate_has_core_fields():
    config = MediaIndexConfig()
    scanner = MediaAssetScanner(config=config)

    candidates = scanner.scan_document(
        "data/mineru_cache/chapter_03_p082-159_线性系统的时域分析法__082fadd0"
    )
    sample = candidates[0]

    assert sample["asset_id"]
    assert sample["source_doc_id"]
    assert sample["source_doc_name"]
    assert sample["asset_type"] in {"figure", "formula", "table"}
    assert "nearby_text" in sample
    assert "content_hash" in sample

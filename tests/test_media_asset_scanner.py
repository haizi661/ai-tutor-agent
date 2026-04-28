from pathlib import Path

from ai_tutor_agent.knowledge_map.config.media_index_config import MediaIndexConfig
from ai_tutor_agent.knowledge_map.media_index.media_asset_scanner import MediaAssetScanner


FIXTURE_CACHE_ROOT = Path("tests/fixtures/mineru_cache")
FIXTURE_DOC_DIR = FIXTURE_CACHE_ROOT / "chapter_p33-81"


def test_media_asset_scanner_extracts_figures_and_formulas_from_fixture_doc():
    config = MediaIndexConfig(mineru_cache_root=FIXTURE_CACHE_ROOT)
    scanner = MediaAssetScanner(config=config)

    candidates = scanner.scan_document(FIXTURE_DOC_DIR)

    assert candidates
    assert any(item["asset_type"] == "figure" for item in candidates)
    assert any(item["asset_type"] == "formula" for item in candidates)
    assert any("图 4-3" in item["caption_text"] for item in candidates if item["asset_type"] == "figure")


def test_media_asset_scanner_candidate_has_core_fields():
    config = MediaIndexConfig(mineru_cache_root=FIXTURE_CACHE_ROOT)
    scanner = MediaAssetScanner(config=config)

    candidates = scanner.scan_document(FIXTURE_DOC_DIR)
    sample = candidates[0]

    assert sample["asset_id"]
    assert sample["source_doc_id"]
    assert sample["source_doc_name"]
    assert sample["asset_type"] in {"figure", "formula", "table"}
    assert "nearby_text" in sample
    assert "content_hash" in sample

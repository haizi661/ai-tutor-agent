from pathlib import Path

from ai_tutor_agent.knowledge_map.config.media_index_config import MediaIndexConfig
from ai_tutor_agent.knowledge_map.media_index.media_asset_scanner import MediaAssetScanner
from ai_tutor_agent.knowledge_map.media_index.media_candidate_filter import MediaCandidateFilter


FIXTURE_CACHE_ROOT = Path("tests/fixtures/mineru_cache")
FIXTURE_DOC_DIR = FIXTURE_CACHE_ROOT / "chapter_p33-81"


def test_media_candidate_filter_keeps_fixture_formula_and_figure():
    config = MediaIndexConfig(mineru_cache_root=FIXTURE_CACHE_ROOT, min_image_bytes=0)
    scanner = MediaAssetScanner(config=config)
    candidate_filter = MediaCandidateFilter(config=config)

    raw_candidates = scanner.scan_document(FIXTURE_DOC_DIR)
    filtered = candidate_filter.filter_candidates(raw_candidates)

    assert filtered
    assert len(filtered) == len(raw_candidates)
    assert any(item["asset_type"] == "figure" for item in filtered)
    assert any(item["asset_type"] == "formula" for item in filtered)


def test_media_candidate_filter_deduplicates_same_caption_figures():
    config = MediaIndexConfig(min_image_bytes=0)
    candidate_filter = MediaCandidateFilter(config=config)

    candidates = [
        {
            "asset_id": "a",
            "asset_type": "figure",
            "source_doc_id": "doc",
            "source_doc_name": "doc.pdf",
            "source_path": "tests/fixtures/mineru_cache/chapter_p33-81/images/figure1.png",
            "caption_text": "图 4-3 单位阶跃响应曲线",
            "nearby_text": "附近正文足够长，说明这是一张高价值候选图。",
            "raw_text": "图 4-3 单位阶跃响应曲线",
            "page_range": [],
            "chapter_title": "第二章",
            "content_hash": "1",
            "extra": {},
        },
        {
            "asset_id": "b",
            "asset_type": "figure",
            "source_doc_id": "doc",
            "source_doc_name": "doc.pdf",
            "source_path": "tests/fixtures/mineru_cache/chapter_p33-81/images/figure1.png",
            "caption_text": "图 4-3 单位阶跃响应曲线",
            "nearby_text": "另一处重复出现的相同标题图片。",
            "raw_text": "图 4-3 单位阶跃响应曲线",
            "page_range": [],
            "chapter_title": "第二章",
            "content_hash": "2",
            "extra": {},
        },
    ]

    filtered = candidate_filter.filter_candidates(candidates)

    assert len(filtered) == 1

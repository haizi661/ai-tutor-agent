from ai_tutor_agent.knowledge_map.config.media_index_config import MediaIndexConfig
from ai_tutor_agent.knowledge_map.media_index.media_asset_scanner import MediaAssetScanner
from ai_tutor_agent.knowledge_map.media_index.media_candidate_filter import MediaCandidateFilter


def test_media_candidate_filter_reduces_chapter_03_candidates():
    config = MediaIndexConfig()
    scanner = MediaAssetScanner(config=config)
    candidate_filter = MediaCandidateFilter(config=config)

    raw_candidates = scanner.scan_document(
        "data/mineru_cache/chapter_03_p082-159_线性系统的时域分析法__082fadd0"
    )
    filtered = candidate_filter.filter_candidates(raw_candidates)

    assert filtered
    assert len(filtered) < len(raw_candidates)
    assert any(item["asset_type"] == "figure" for item in filtered)
    assert any(item["asset_type"] == "formula" for item in filtered)


def test_media_candidate_filter_deduplicates_same_caption_figures():
    config = MediaIndexConfig()
    candidate_filter = MediaCandidateFilter(config=config)

    candidates = [
        {
            "asset_id": "a",
            "asset_type": "figure",
            "source_doc_id": "doc",
            "source_doc_name": "doc.pdf",
            "source_path": "data/mineru_cache/chapter_03_p082-159_线性系统的时域分析法__082fadd0/images/figure_128.jpg",
            "caption_text": "图 3-1 单位阶跃响应曲线",
            "nearby_text": "附近正文足够长，说明这是一张高价值候选图。",
            "raw_text": "图 3-1 单位阶跃响应曲线",
            "page_range": [],
            "chapter_title": "第三章",
            "content_hash": "1",
            "extra": {},
        },
        {
            "asset_id": "b",
            "asset_type": "figure",
            "source_doc_id": "doc",
            "source_doc_name": "doc.pdf",
            "source_path": "data/mineru_cache/chapter_03_p082-159_线性系统的时域分析法__082fadd0/images/figure_430.jpg",
            "caption_text": "图 3-1 单位阶跃响应曲线",
            "nearby_text": "另一处重复出现的相同标题图片。",
            "raw_text": "图 3-1 单位阶跃响应曲线",
            "page_range": [],
            "chapter_title": "第三章",
            "content_hash": "2",
            "extra": {},
        },
    ]

    filtered = candidate_filter.filter_candidates(candidates)

    assert len(filtered) == 1

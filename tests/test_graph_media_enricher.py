from pathlib import Path

import pytest

from ai_tutor_agent.knowledge_map.builders.graph_media_enricher import GraphMediaEnricher


def test_collect_for_nodes_falls_back_to_doc_figures_when_annotated_assets_only_have_formulas(tmp_path):
    image_dir = tmp_path / "cache" / "chapter" / "images"
    image_dir.mkdir(parents=True)
    image_path = image_dir / "response.jpg"
    image_path.write_bytes(b"fake image bytes")

    enricher = GraphMediaEnricher(mineru_cache_root=tmp_path / "cache", annotated_assets_path=tmp_path / "missing")
    enricher.annotated_assets = [
        {
            "asset_id": "doc:formula:overshoot",
            "asset_type": "formula",
            "anchor_node_id": "KM015",
            "anchor_node_name": "二阶系统的时域分析",
            "raw_text": r"\[\sigma\% = e^{-\pi\zeta/\sqrt{1-\zeta^2}} \times 100\%\]",
            "title_text": "式 3-21",
            "formula_meaning": "给出超调量与阻尼比之间的定量关系。",
            "confidence": 0.8,
        }
    ]
    enricher.chapter_docs = [
        {
            "manifest": {
                "cache_dir": str(tmp_path / "cache" / "chapter"),
                "images": {
                    "response.jpg": {
                        "abs_path": str(image_path),
                        "original_name": "response.jpg",
                    }
                },
            },
            "full_md": "\n".join(
                [
                    "# 3-3 二阶系统的时域分析",
                    "二阶系统可通过单位阶跃响应观察超调量与调节时间。",
                    "![](images/response.jpg)",
                    "图 3-8 二阶系统单位阶跃响应曲线",
                ]
            ),
            "start_page": 82,
            "end_page": 159,
        }
    ]
    node_map = {
        "KM015": {
            "node_id": "KM015",
            "name": "二阶系统的时域分析",
            "extra": {"chapter_page_range": [82, 159]},
            "page_refs": [100],
        }
    }

    media_items = enricher.collect_for_nodes(
        traversed_nodes=[{"node_id": "KM015", "name": "二阶系统的时域分析", "hop": 0, "node_role": "primary", "score": 1.0}],
        node_map=node_map,
        question="二阶系统超调量和响应曲线有什么关系",
    )

    assert any(item["asset_type"] == "formula" for item in media_items)
    figures = [item for item in media_items if item["asset_type"] == "figure"]
    assert figures
    assert figures[0]["reference"].startswith("KM015.figure_asset[")
    assert figures[0]["image_paths_abs"] == [str(image_path)]
    assert "单位阶跃响应曲线" in figures[0]["caption"]


def test_collect_for_nodes_includes_annotated_table_assets(tmp_path):
    enricher = GraphMediaEnricher(mineru_cache_root=tmp_path / "cache", annotated_assets_path=tmp_path / "missing")
    enricher.annotated_assets = [
        {
            "asset_id": "KM020.table_asset[1]",
            "asset_type": "table",
            "anchor_node_id": "KM020",
            "anchor_node_name": "典型输入信号",
            "raw_text": "<table><tr><th>输入</th><th>表达式</th></tr><tr><td>阶跃</td><td>1(t)</td></tr></table>",
            "caption_text": "典型输入信号对照表",
            "nearby_text": "阶跃、斜坡、抛物线等典型输入信号。",
            "confidence": 0.9,
        }
    ]
    node_map = {
        "KM020": {
            "node_id": "KM020",
            "name": "典型输入信号",
            "extra": {},
        }
    }

    media_items = enricher.collect_for_nodes(
        traversed_nodes=[{"node_id": "KM020", "name": "典型输入信号", "hop": 0, "node_role": "primary", "score": 1.0}],
        node_map=node_map,
        question="典型输入信号有哪些",
    )

    tables = [item for item in media_items if item["asset_type"] == "table"]
    assert tables
    assert tables[0]["reference"] == "KM020.table_asset[1]"
    assert "<table>" in tables[0]["text"]
    assert "典型输入信号对照表" in tables[0]["caption"]


def test_collect_for_nodes_replaces_annotated_figure_without_existing_source_with_fallback_figure(tmp_path):
    image_dir = tmp_path / "cache" / "chapter" / "images"
    image_dir.mkdir(parents=True)
    image_path = image_dir / "step.png"
    image_path.write_bytes(b"fake image bytes")

    enricher = GraphMediaEnricher(mineru_cache_root=tmp_path / "cache", annotated_assets_path=tmp_path / "missing")
    enricher.annotated_assets = [
        {
            "asset_id": "KM007.figure_asset[1]",
            "asset_type": "figure",
            "anchor_node_id": "KM007",
            "anchor_node_name": "控制系统的数学模型",
            "source_path": str(tmp_path / "cache" / "chapter" / "images" / "missing.png"),
            "caption_text": "图 4-3 单位阶跃响应曲线",
            "confidence": 0.9,
        }
    ]
    enricher.chapter_docs = [
        {
            "manifest": {
                "cache_dir": str(tmp_path / "cache" / "chapter"),
                "images": {},
            },
            "full_md": "\n".join(
                [
                    "# 4-2 控制系统的数学模型",
                    "控制系统的数学模型可通过单位阶跃响应曲线观察。",
                    "![图 4-3 单位阶跃响应曲线](images/step.png)",
                    "图 4-3 单位阶跃响应曲线",
                ]
            ),
            "start_page": 33,
            "end_page": 81,
        }
    ]
    node_map = {
        "KM007": {
            "node_id": "KM007",
            "name": "控制系统的数学模型",
            "extra": {"chapter_page_range": [33, 81]},
            "page_refs": [50],
        }
    }

    media_items = enricher.collect_for_nodes(
        traversed_nodes=[{"node_id": "KM007", "name": "控制系统的数学模型", "hop": 0, "node_role": "primary", "score": 1.0}],
        node_map=node_map,
        question="单位阶跃响应曲线怎么看",
    )

    figures = [item for item in media_items if item["asset_type"] == "figure"]
    assert figures
    assert figures[0]["image_paths_abs"] == [str(image_path)]


def test_find_matching_doc_prefers_rich_doc_over_same_page_stub(tmp_path):
    real_doc_dir = tmp_path / "cache" / "chapter_02_p033-081_real"
    real_image_dir = real_doc_dir / "images"
    real_image_dir.mkdir(parents=True)
    real_image = real_image_dir / "real-step.jpg"
    real_image.write_bytes(b"real image")

    stub_doc_dir = tmp_path / "cache" / "chapter_p33-81"
    stub_image_dir = stub_doc_dir / "images"
    stub_image_dir.mkdir(parents=True)
    stub_image = stub_image_dir / "figure1.png"
    stub_image.write_bytes(b"\x89PNG\r\n\x1a\n")

    enricher = GraphMediaEnricher(mineru_cache_root=tmp_path / "cache", annotated_assets_path=tmp_path / "missing")
    enricher.chapter_docs = [
        {
            "manifest": {
                "cache_dir": str(stub_doc_dir),
                "images": {"images/figure1.png": {"original_name": "figure1.png"}},
            },
            "full_md": "\n".join(
                [
                    "# 控制系统的数学模型",
                    "传递函数常写为：",
                    "![图 4-3 单位阶跃响应曲线](images/figure1.png)",
                    "图 4-3 单位阶跃响应曲线",
                ]
            ),
            "start_page": 33,
            "end_page": 81,
        },
        {
            "manifest": {
                "cache_dir": str(real_doc_dir),
                "images": {
                    "real-step.jpg": {
                        "abs_path": str(real_image),
                        "original_name": "real-step.jpg",
                        "friendly_name": "figure_42.jpg",
                    }
                },
            },
            "full_md": "\n".join(
                [
                    "# 第二章 控制系统的数学模型",
                    "# 2-2 控制系统的复数域数学模型",
                    "# 3. 传递函数的极点和零点对输出的影响",
                    "传递函数的零点影响响应曲线的形状。",
                    "![](images/real-step.jpg)",
                    "(b)单位阶跃响应",
                    "图 2-9 零极点对输出响应的影响(MATLAB)",
                    "# 4. 典型元部件的传递函数",
                ]
            ),
            "start_page": 33,
            "end_page": 81,
        },
    ]
    node = {
        "node_id": "KM007",
        "name": "控制系统的数学模型",
        "extra": {"chapter_page_range": [33, 81]},
        "page_refs": [50],
    }

    doc = enricher._find_matching_doc(node)
    media_items = enricher.collect_for_nodes(
        traversed_nodes=[{"node_id": "KM007", "name": "控制系统的数学模型", "hop": 0, "node_role": "primary", "score": 1.0}],
        node_map={"KM007": node},
        question="单位阶跃响应曲线怎么看",
    )
    figures = [item for item in media_items if item["asset_type"] == "figure"]

    assert doc["manifest"]["cache_dir"] == str(real_doc_dir)
    assert figures
    assert figures[0]["image_paths_abs"] == [str(real_image)]
    assert "图 2-9" in figures[0]["caption"]


def test_extract_figures_from_block_filters_qr_code_guide_images(tmp_path):
    cache_dir = tmp_path / "cache" / "chapter_01_p009-032"
    image_dir = cache_dir / "images"
    image_dir.mkdir(parents=True)
    qr_image = image_dir / "qr.png"
    real_image = image_dir / "system.png"
    qr_image.write_bytes(b"qr image bytes")
    real_image.write_bytes(b"real figure bytes")

    enricher = GraphMediaEnricher(mineru_cache_root=tmp_path / "cache", annotated_assets_path=tmp_path / "missing")
    manifest = {
        "cache_dir": str(cache_dir),
        "images": {
            "qr.png": {"abs_path": str(qr_image), "original_name": "qr.png"},
            "system.png": {"abs_path": str(real_image), "original_name": "system.png"},
        },
    }
    block = "\n".join(
        [
            "自动控制的基本原理与方式",
            "本章导学",
            "![](images/qr.png)",
            "本章导学",
            "扫码学习本章导学微课。",
            "![](images/system.png)",
            "图 1-2 自动控制系统组成框图",
        ]
    )

    figures = enricher._extract_figures_from_block(block, manifest)

    assert len(figures) == 1
    assert figures[0]["image_paths_abs"] == [str(real_image)]
    assert "图 1-2" in figures[0]["caption"]
    assert str(qr_image) not in figures[0]["image_paths_abs"]


@pytest.mark.parametrize(
    "image_path",
    [
        "images/real-step.jpg",
        "real-step.jpg",
        "data/mineru_cache\\chapter_02_p033-081_real\\images\\real-step.jpg",
        "C:\\Users\\haizi\\Desktop\\real-step.jpg",
        "E:\\data\\mineru_cache\\chapter_02_p033-081_real\\images\\real-step.jpg",
    ],
)
def test_resolve_image_paths_handles_manifest_variants_and_windows_paths(tmp_path, image_path):
    cache_dir = tmp_path / "data" / "mineru_cache" / "chapter_02_p033-081_real"
    image_dir = cache_dir / "images"
    image_dir.mkdir(parents=True)
    image = image_dir / "real-step.jpg"
    image.write_bytes(b"image")
    enricher = GraphMediaEnricher(mineru_cache_root=tmp_path / "data" / "mineru_cache", annotated_assets_path=tmp_path / "missing")
    manifest = {
        "cache_dir": str(cache_dir),
        "images": {
            "real-step.jpg": {
                "abs_path": str(image),
                "original_name": "real-step.jpg",
                "friendly_name": "figure_42.jpg",
            }
        },
    }

    resolved = enricher._resolve_image_paths([image_path], manifest)

    assert resolved == [str(image.resolve())]


def test_enricher_loads_annotated_assets_from_summary_with_relative_paths_under_target_dir(tmp_path):
    media_index_dir = tmp_path / "data" / "media_evidence_index"
    media_index_dir.mkdir(parents=True)
    annotated_file = media_index_dir / "chapter_02_annotated_assets.jsonl"
    annotated_file.write_text(
        '{"asset_id":"KM001.figure_asset[1]","asset_type":"figure","anchor_node_id":"KM001","source_path":"data/mineru_cache/chapter/images/x.png"}\n',
        encoding="utf-8",
    )
    (media_index_dir / "batch_summary.json").write_text(
        '{"count":1,"chapters":[{"annotated_path":"chapter_02_annotated_assets.jsonl"}]}',
        encoding="utf-8",
    )

    enricher = GraphMediaEnricher(
        mineru_cache_root=tmp_path / "data" / "mineru_cache",
        annotated_assets_path=media_index_dir,
    )

    assert len(enricher.annotated_assets) == 1
    assert enricher.annotated_assets[0]["asset_id"] == "KM001.figure_asset[1]"

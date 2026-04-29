import json

from ai_tutor_agent.knowledge_map.config.media_index_config import MediaIndexConfig
from ai_tutor_agent.knowledge_map.media_index.media_asset_scanner import MediaAssetScanner


def test_media_asset_scanner_resolves_windows_manifest_abs_path_by_image_name(tmp_path):
    doc_dir = tmp_path / "chapter_02_p033-081_real"
    image_dir = doc_dir / "images"
    image_dir.mkdir(parents=True)
    image = image_dir / "block.png"
    image.write_bytes(b"image")
    (doc_dir / "full.md").write_text("\n".join(["# chapter", "![](images/block.png)", "图 2-1 控制系统框图"]), encoding="utf-8")
    (doc_dir / "manifest.json").write_text(
        json.dumps(
            {
                "pdf_name": "chapter_02_p033-081_real.pdf",
                "images": {
                    "images/block.png": {
                        "abs_path": r"C:\Users\haizi\Desktop\old_cache\images\block.png",
                        "original_name": "block.png",
                    }
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    scanner = MediaAssetScanner(MediaIndexConfig(mineru_cache_root=tmp_path, min_image_bytes=0))
    candidates = scanner.scan_document(doc_dir)

    assert len(candidates) == 1
    assert candidates[0]["source_path"] == str(image.resolve())

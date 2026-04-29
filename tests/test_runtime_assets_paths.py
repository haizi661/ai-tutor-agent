import json

from ai_tutor_agent import platform_paths
from ai_tutor_agent.knowledge_map.runtime_assets import inspect_media_evidence_index


def test_inspect_media_evidence_index_reports_project_relative_path(monkeypatch, tmp_path):
    monkeypatch.setattr(platform_paths, "_PROJECT_ROOT", tmp_path)
    media_index_root = tmp_path / "data" / "media_evidence_index"
    media_index_root.mkdir(parents=True)
    (media_index_root / "chapter_02_annotated_assets.jsonl").write_text('{"id": 1}\n', encoding="utf-8")
    (media_index_root / "batch_summary.json").write_text(
        json.dumps({"count": 1, "chapters": []}, ensure_ascii=False),
        encoding="utf-8",
    )

    report = inspect_media_evidence_index("data/media_evidence_index")

    assert report["path"] == "data/media_evidence_index"
    assert report["summary_exists"] is True
    assert report["annotated_file_count"] == 1

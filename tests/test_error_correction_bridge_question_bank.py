import json

import ai_tutor_agent.infrastructure.error_correction_bridge as bridge


def test_saved_question_bank_assets_survive_workspace_reset(monkeypatch, tmp_path):
    monkeypatch.setattr(bridge, "resolve_project_path", lambda path: tmp_path / path)
    service = bridge.ErrorCorrectionService()

    source_asset = service.struct_dir / "imgs" / "demo.png"
    source_asset.parent.mkdir(parents=True, exist_ok=True)
    source_asset.write_bytes(b"fake-image")

    question_payload = [
        {
            "uid": "u1",
            "question_id": "1",
            "question_type": "选择题",
            "content_blocks": [
                {"block_type": "text", "content": "如图所示，求解下列问题。"},
                {"block_type": "image", "content": "/images/demo.png"},
            ],
            "image_refs": ["/images/demo.png"],
        }
    ]
    service._questions_path().write_text(
        json.dumps(question_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    result = service.save_questions_to_library(["u1"])
    saved_item = result["items"][0]
    saved_image_url = saved_item["content_blocks"][1]["content"]

    assert saved_image_url.startswith("/api/error-correction/assets/question_bank/assets/")

    service.clear_workspace()

    resolved = service.resolve_asset_path(saved_image_url)
    assert resolved.exists()
    assert resolved.read_bytes() == b"fake-image"


def test_saved_question_bank_falls_back_to_section_title_tag(monkeypatch, tmp_path):
    monkeypatch.setattr(bridge, "resolve_project_path", lambda path: tmp_path / path)
    service = bridge.ErrorCorrectionService()

    question_payload = [
        {
            "uid": "u1",
            "question_id": "1",
            "section_title": "根轨迹",
            "question_type": "选择题",
            "content_blocks": [
                {"block_type": "text", "content": "判断根轨迹的增益变化范围。"},
            ],
            "knowledge_tags": [],
        }
    ]
    service._questions_path().write_text(
        json.dumps(question_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    result = service.save_questions_to_library(["u1"])

    assert result["items"][0]["knowledge_tags"] == ["根轨迹"]

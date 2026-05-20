from pathlib import Path
from types import SimpleNamespace

from ai_tutor_agent.interfaces.api.app import create_api_app
from asgi_test_client import SyncASGITestClient as TestClient


class FakeErrorCorrectionService:
    def __init__(self, tmp_path: Path) -> None:
        self.tmp_path = tmp_path
        self.saved_uploads = []
        self.ocr_selected_filename = None
        self.split_payload = None
        self.saved_selected_ids = None
        self.saved_source_files = None
        self.question_bank_items = [{"library_id": "qb_1", "question_id": "1", "content_blocks": []}]
        export_file = tmp_path / "wrongbook.md"
        export_file.write_text("# 错题本\n", encoding="utf-8")
        self.export_path = export_file

    def get_workspace_snapshot(self, settings):
        return {
            "upload_files": [{"filename": "sample.pdf", "size_bytes": 128}],
            "questions": [{"uid": "0", "question_id": "1", "question_type": "选择题", "content_blocks": []}],
            "ocr_preview": {"pages": [{"page_index": 0, "blocks": []}], "answer_layout": {"type": "separated_tail"}},
            "summary": {"upload_count": 1, "ocr_page_count": 1, "question_count": 1, "question_bank_count": 1, "has_export": True, "export_filename": "wrongbook.md"},
            "capabilities": {
                "ocr_configured": True,
                "llm_configured": bool(settings.openai_api_key),
                "llm_profile": settings.chat_profile,
                "llm_model_name": settings.model_name,
            },
        }

    def list_uploads(self):
        return [{"filename": "sample.pdf", "size_bytes": 128}]

    def save_uploads(self, uploads):
        self.saved_uploads = uploads
        return [{"filename": name, "size_bytes": len(content)} for name, content in uploads]

    def delete_upload(self, filename):
        return filename == "sample.pdf"

    def clear_workspace(self):
        return None

    def resolve_upload_path(self, filename):
        path = self.tmp_path / filename
        path.write_bytes(b"demo")
        return path

    def run_ocr(self, settings=None, *, selected_filename=""):
        self.ocr_selected_filename = selected_filename
        return {
            "pages": [{"page_index": 0, "blocks": [], "block_count": 0, "preview_text": ""}],
            "answer_layout": {"type": "mixed_inline", "question_page_indices": [], "answer_page_indices": []},
            "selected_filename": selected_filename,
        }

    def run_split(self, settings, *, confirmed_answer_layout="", selected_page_indices=None, selected_filename=""):
        self.split_payload = {
            "profile": settings.chat_profile,
            "layout": confirmed_answer_layout,
            "pages": selected_page_indices or [],
            "selected_filename": selected_filename,
        }
        return {
            "questions": [{"uid": "0", "question_id": "1", "question_type": "选择题", "content_blocks": []}],
            "warnings": [],
            "selected_filename": selected_filename,
        }

    def export_questions(self, selected_ids=None):
        return {"output_path": str(self.export_path), "filename": self.export_path.name}

    def resolve_export_path(self, filename):
        return self.export_path

    def resolve_asset_path(self, asset_path):
        path = self.tmp_path / asset_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fake-image")
        return path

    def list_question_bank(self):
        return list(self.question_bank_items)

    def save_questions_to_library(self, selected_ids=None, source_files=None):
        self.saved_selected_ids = selected_ids or []
        self.saved_source_files = source_files or []
        return {
            "saved_count": len(self.question_bank_items),
            "batch_id": "qb_batch",
            "items": self.list_question_bank(),
        }

    def clear_question_bank(self):
        removed = len(self.question_bank_items)
        self.question_bank_items = []
        return removed

    def delete_question_bank_entry(self, library_id):
        existing = len(self.question_bank_items)
        self.question_bank_items = [
            item for item in self.question_bank_items
            if item.get("library_id") != library_id
        ]
        return len(self.question_bank_items) != existing


def build_test_app(monkeypatch, tmp_path: Path):
    fake_runtime = SimpleNamespace(
        settings=SimpleNamespace(
            openai_api_key="sk-test",
            chat_profile="deepseek",
            model_name="deepseek-v4-flash",
            paddleocr_api_url="https://ocr.example.com/jobs",
            paddleocr_api_token="ocr-token",
            paddleocr_model="PaddleOCR-VL-1.5",
        )
    )
    fake_service = FakeErrorCorrectionService(tmp_path)
    monkeypatch.setattr(
        "ai_tutor_agent.interfaces.api.error_correction.get_error_correction_service",
        lambda: fake_service,
    )
    monkeypatch.setattr(
        "ai_tutor_agent.interfaces.api.knowledge.get_error_correction_service",
        lambda: fake_service,
    )
    app = create_api_app(runtime_factory=lambda: fake_runtime)
    return app, fake_service


def test_error_correction_status_route_returns_workspace_snapshot(monkeypatch, tmp_path):
    app, _service = build_test_app(monkeypatch, tmp_path)

    with TestClient(app) as client:
        response = client.get("/api/error-correction/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["summary"]["question_count"] == 1
    assert payload["capabilities"]["llm_profile"] == "deepseek"


def test_error_correction_upload_route_accepts_multiple_files(monkeypatch, tmp_path):
    app, service = build_test_app(monkeypatch, tmp_path)

    with TestClient(app) as client:
        response = client.post(
            "/api/error-correction/upload",
            files=[
                ("files", ("paper-a.pdf", b"alpha", "application/pdf")),
                ("files", ("paper-b.png", b"beta", "image/png")),
            ],
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert [name for name, _content in service.saved_uploads] == ["paper-a.pdf", "paper-b.png"]


def test_error_correction_split_route_forwards_layout_confirmation(monkeypatch, tmp_path):
    app, service = build_test_app(monkeypatch, tmp_path)

    with TestClient(app) as client:
        response = client.post(
            "/api/error-correction/split",
            json={
                "confirmed_answer_layout": "separated_tail",
                "selected_page_indices": [0, 1],
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert service.split_payload == {
        "profile": "deepseek",
        "layout": "separated_tail",
        "pages": [0, 1],
        "selected_filename": "",
    }


def test_error_correction_ocr_route_forwards_selected_filename(monkeypatch, tmp_path):
    app, service = build_test_app(monkeypatch, tmp_path)

    with TestClient(app) as client:
        response = client.post(
            "/api/error-correction/ocr",
            json={"selected_filename": "paper-a.pdf"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["selected_filename"] == "paper-a.pdf"
    assert service.ocr_selected_filename == "paper-a.pdf"


def test_error_correction_split_route_forwards_selected_filename(monkeypatch, tmp_path):
    app, service = build_test_app(monkeypatch, tmp_path)

    with TestClient(app) as client:
        response = client.post(
            "/api/error-correction/split",
            json={
                "confirmed_answer_layout": "mixed_inline",
                "selected_filename": "paper-b.pdf",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["selected_filename"] == "paper-b.pdf"
    assert service.split_payload["selected_filename"] == "paper-b.pdf"


def test_error_correction_export_download_serves_markdown(monkeypatch, tmp_path):
    app, _service = build_test_app(monkeypatch, tmp_path)

    with TestClient(app) as client:
        response = client.get("/api/error-correction/exports/wrongbook.md")

    assert response.status_code == 200
    assert response.text.startswith("# 错题本")


def test_error_correction_asset_download_serves_local_images(monkeypatch, tmp_path):
    app, _service = build_test_app(monkeypatch, tmp_path)

    with TestClient(app) as client:
        response = client.get("/api/error-correction/assets/imgs/demo.jpg")

    assert response.status_code == 200


def test_question_bank_save_route_uses_selected_ids(monkeypatch, tmp_path):
    app, service = build_test_app(monkeypatch, tmp_path)

    with TestClient(app) as client:
        response = client.post(
            "/api/knowledge/question-bank",
            json={"selected_ids": ["0", "1"], "source_files": ["paper-a.pdf"]},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert service.saved_selected_ids == ["0", "1"]
    assert service.saved_source_files == ["paper-a.pdf"]


def test_question_bank_list_route_returns_saved_items(monkeypatch, tmp_path):
    app, _service = build_test_app(monkeypatch, tmp_path)

    with TestClient(app) as client:
        response = client.get("/api/knowledge/question-bank")

    assert response.status_code == 200
    assert response.json()["items"][0]["library_id"] == "qb_1"


def test_question_bank_delete_route_removes_single_item(monkeypatch, tmp_path):
    app, service = build_test_app(monkeypatch, tmp_path)

    with TestClient(app) as client:
        response = client.delete("/api/knowledge/question-bank/qb_1")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert service.question_bank_items == []


def test_question_bank_clear_route_removes_all_items(monkeypatch, tmp_path):
    app, service = build_test_app(monkeypatch, tmp_path)

    with TestClient(app) as client:
        response = client.delete("/api/knowledge/question-bank")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "success"
    assert payload["removed"] == 1
    assert service.question_bank_items == []

from __future__ import annotations

import importlib
import json
import os
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from copy import deepcopy

from ..config import Settings
from ..platform_paths import resolve_project_path


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _safe_filename(name: str) -> str:
    safe = Path(name or "").name.strip()
    if not safe:
        raise ValueError("文件名不能为空")
    return safe


@dataclass
class _LegacyModules:
    settings: Any
    utils: Any
    workflow: Any


class ErrorCorrectionService:
    def __init__(self) -> None:
        self.workspace_root = resolve_project_path("data/error_correction_runtime")
        self.upload_dir = self.workspace_root / "uploads"
        self.pages_dir = self.workspace_root / "pages"
        self.struct_dir = self.workspace_root / "struct"
        self.results_dir = self.workspace_root / "results"
        self.erased_dir = self.workspace_root / "erased"
        self._legacy_modules: _LegacyModules | None = None
        self._ensure_workspace_dirs()

    def _ensure_workspace_dirs(self) -> None:
        for path in (
            self.workspace_root,
            self.upload_dir,
            self.pages_dir,
            self.struct_dir,
            self.results_dir,
            self.erased_dir,
            self._question_bank_dir(),
            self._question_bank_assets_dir(),
        ):
            path.mkdir(parents=True, exist_ok=True)

    def _ocr_cache_path(self) -> Path:
        return self.results_dir / "ocr_cache.json"

    def _ocr_preview_path(self) -> Path:
        return self.results_dir / "ocr_preview.json"

    def _questions_path(self) -> Path:
        return self.results_dir / "questions.json"

    def _export_path(self) -> Path:
        return self.results_dir / "wrongbook.md"

    def _question_bank_dir(self) -> Path:
        return self.workspace_root / "question_bank"

    def _question_bank_path(self) -> Path:
        return self._question_bank_dir() / "questions.json"

    def _question_bank_assets_dir(self) -> Path:
        return self._question_bank_dir() / "assets"

    def _asset_relative_path(self, value: Any) -> str:
        raw = str(value or "").strip()
        if not raw:
            return ""
        if raw.startswith("http://") or raw.startswith("https://"):
            return raw
        normalized = raw.replace("\\", "/")
        if normalized.startswith("/api/error-correction/assets/"):
            normalized = normalized[len("/api/error-correction/assets/"):]
        elif normalized.startswith("/images/"):
            normalized = f"imgs/{normalized[len('/images/'):]}"
        elif normalized.startswith("images/"):
            normalized = f"imgs/{normalized[len('images/'):]}"
        elif normalized.startswith("/"):
            normalized = normalized[1:]
        return normalized

    def _normalize_asset_reference(self, value: Any) -> str:
        normalized = self._asset_relative_path(value)
        if not normalized:
            return ""
        if normalized.startswith("http://") or normalized.startswith("https://"):
            return normalized
        return f"/api/error-correction/assets/{normalized}"

    def _persist_question_asset(
        self,
        value: Any,
        *,
        batch_id: str,
        copied_assets: dict[str, str],
    ) -> str:
        normalized = self._asset_relative_path(value)
        if not normalized:
            return ""
        if normalized.startswith("http://") or normalized.startswith("https://"):
            return normalized
        if normalized.startswith("question_bank/assets/"):
            return normalized
        if normalized in copied_assets:
            return copied_assets[normalized]

        source = (self.struct_dir / normalized).resolve()
        struct_root = self.struct_dir.resolve()
        if struct_root not in source.parents and source != struct_root:
            return normalized
        if not source.exists() or not source.is_file():
            return normalized

        target_relative = Path("question_bank") / "assets" / batch_id / normalized
        target = (self.workspace_root / target_relative).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied_assets[normalized] = target_relative.as_posix()
        return copied_assets[normalized]

    def _persist_question_assets(
        self,
        question: dict[str, Any],
        *,
        batch_id: str,
        copied_assets: dict[str, str],
    ) -> dict[str, Any]:
        payload = deepcopy(question)
        for block in payload.get("content_blocks") or []:
            if block.get("block_type") == "image":
                block["content"] = self._persist_question_asset(
                    block.get("content"),
                    batch_id=batch_id,
                    copied_assets=copied_assets,
                )
        if isinstance(payload.get("option_images"), list):
            payload["option_images"] = [
                self._persist_question_asset(item, batch_id=batch_id, copied_assets=copied_assets) if item else ""
                for item in payload.get("option_images") or []
            ]
        if isinstance(payload.get("image_refs"), list):
            payload["image_refs"] = [
                self._persist_question_asset(item, batch_id=batch_id, copied_assets=copied_assets) if item else ""
                for item in payload.get("image_refs") or []
            ]
        return payload

    def _serialize_question_for_frontend(self, question: dict[str, Any]) -> dict[str, Any]:
        payload = self._normalize_question_payload(deepcopy(question))
        blocks = payload.get("content_blocks") or []
        for block in blocks:
            if block.get("block_type") == "image":
                block["content"] = self._normalize_asset_reference(block.get("content"))
        option_images = payload.get("option_images") or []
        if isinstance(option_images, list):
            payload["option_images"] = [
                self._normalize_asset_reference(item) if item else ""
                for item in option_images
            ]
        image_refs = payload.get("image_refs") or []
        if isinstance(image_refs, list):
            payload["image_refs"] = [
                self._normalize_asset_reference(item) if item else ""
                for item in image_refs
            ]
        return payload

    def _serialize_questions_for_frontend(self, questions: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [self._serialize_question_for_frontend(question) for question in (questions or [])]

    def _normalize_question_payload(self, question: dict[str, Any]) -> dict[str, Any]:
        payload = deepcopy(question)
        tags: list[str] = []
        seen: set[str] = set()
        for raw_tag in payload.get("knowledge_tags") or []:
            tag = " ".join(str(raw_tag or "").split()).strip()
            if not tag or tag in seen:
                continue
            seen.add(tag)
            tags.append(tag)

        section_title = " ".join(str(payload.get("section_title") or "").split()).strip()
        if not tags and section_title:
            tags.append(section_title)
        if not tags:
            tags.append("待补充知识板块")
        payload["knowledge_tags"] = tags[:6]
        return payload

    def read_question_bank(self) -> list[dict[str, Any]]:
        return _read_json(self._question_bank_path(), [])

    def list_question_bank(self) -> list[dict[str, Any]]:
        return self._serialize_questions_for_frontend(self.read_question_bank())

    def _legacy_backend_root(self) -> Path:
        return resolve_project_path("error_correction/backend")

    def _load_legacy(self) -> _LegacyModules:
        if self._legacy_modules is not None:
            return self._legacy_modules

        backend_root = self._legacy_backend_root()
        backend_root_str = str(backend_root)
        if backend_root_str not in sys.path:
            sys.path.insert(0, backend_root_str)

        legacy_settings = importlib.import_module("core.config").settings
        legacy_utils = importlib.import_module("src.utils")
        legacy_workflow = importlib.import_module("src.workflow")

        self._legacy_modules = _LegacyModules(
            settings=legacy_settings,
            utils=legacy_utils,
            workflow=legacy_workflow,
        )
        return self._legacy_modules

    def _configure_legacy_runtime(self) -> _LegacyModules:
        legacy = self._load_legacy()
        object.__setattr__(legacy.settings, "runtime_dir", self.workspace_root)
        object.__setattr__(legacy.settings, "upload_dir", self.upload_dir)
        object.__setattr__(legacy.settings, "pages_dir", self.pages_dir)
        object.__setattr__(legacy.settings, "struct_dir", self.struct_dir)
        object.__setattr__(legacy.settings, "results_dir", self.results_dir)
        object.__setattr__(legacy.settings, "erased_dir", self.erased_dir)
        legacy.settings.ensure_dirs()
        return legacy

    def _current_ocr_credentials(self, settings: Settings | None = None) -> dict[str, Any]:
        api_url = ""
        token = ""
        model = "PaddleOCR-VL-1.5"
        if settings is not None:
            api_url = (settings.paddleocr_api_url or "").strip()
            token = (settings.paddleocr_api_token or "").strip()
            model = (settings.paddleocr_model or "").strip() or model
        if not api_url:
            api_url = os.getenv("PADDLEOCR_API_URL", "").strip()
        if not token:
            token = os.getenv("PADDLEOCR_API_TOKEN", "").strip()
        if not model:
            model = os.getenv("PADDLEOCR_MODEL", "").strip() or "PaddleOCR-VL-1.5"
        if not api_url or not token:
            return {}
        return {
            "api_url": api_url,
            "token": token,
            "model": model,
            "use_doc_orientation": False,
            "use_doc_unwarping": False,
            "use_chart_recognition": False,
        }

    def _configure_legacy_llm(self, settings: Settings) -> _LegacyModules:
        legacy = self._configure_legacy_runtime()
        provider = legacy.settings.build_provider_config(
            "openai",
            api_key=settings.openai_api_key or "",
            base_url=settings.openai_api_base or "",
            model_name=settings.model_name or "gpt-4o-mini",
            light_model_name=settings.model_name or None,
            supports_function_calling=True,
        )
        legacy.settings.activate_request_providers({"openai": provider})
        return legacy

    def _clear_generated_outputs(self, *, keep_uploads: bool) -> None:
        if not keep_uploads:
            shutil.rmtree(self.upload_dir, ignore_errors=True)
        for directory in (self.pages_dir, self.struct_dir, self.results_dir, self.erased_dir):
            shutil.rmtree(directory, ignore_errors=True)
        self._ensure_workspace_dirs()

    def list_uploads(self) -> list[dict[str, Any]]:
        self._ensure_workspace_dirs()
        items = []
        for path in sorted(self.upload_dir.iterdir(), key=lambda p: p.name.lower()):
            if not path.is_file():
                continue
            stat = path.stat()
            items.append(
                {
                    "filename": path.name,
                    "size_bytes": stat.st_size,
                    "updated_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                }
            )
        return items

    def _select_uploads(self, selected_filename: str = "") -> list[dict[str, Any]]:
        uploads = self.list_uploads()
        if not uploads:
            return []
        target = str(selected_filename or "").strip()
        if not target:
            return uploads
        matched = [item for item in uploads if str(item.get("filename") or "").strip() == target]
        if not matched:
            raise RuntimeError(f"未找到指定的 PDF：{target}")
        return matched

    def save_uploads(self, uploads: list[tuple[str, bytes]]) -> list[dict[str, Any]]:
        saved = []
        self._ensure_workspace_dirs()
        for raw_name, content in uploads:
            safe_name = _safe_filename(raw_name)
            destination = self.upload_dir / safe_name
            stem = destination.stem
            suffix = destination.suffix
            counter = 2
            while destination.exists():
                destination = self.upload_dir / f"{stem}-{counter}{suffix}"
                counter += 1
            destination.write_bytes(content)
            saved.append({"filename": destination.name, "size_bytes": len(content)})
        if saved:
            # New upload invalidates stale OCR/split/export outputs from the previous batch.
            self._clear_generated_outputs(keep_uploads=True)
        return self.list_uploads()

    def delete_upload(self, filename: str) -> bool:
        safe_name = _safe_filename(filename)
        target = self.upload_dir / safe_name
        if not target.exists():
            return False
        target.unlink()
        self._clear_generated_outputs(keep_uploads=True)
        return True

    def clear_workspace(self) -> None:
        self._clear_generated_outputs(keep_uploads=False)

    def read_questions(self) -> list[dict[str, Any]]:
        return _read_json(self._questions_path(), [])

    def get_workspace_snapshot(self, settings: Settings) -> dict[str, Any]:
        uploads = self.list_uploads()
        questions = self._serialize_questions_for_frontend(self.read_questions())
        ocr_preview = _read_json(self._ocr_preview_path(), {})
        export_exists = self._export_path().exists()
        ocr_credentials = self._current_ocr_credentials(settings)
        return {
            "upload_files": uploads,
            "questions": questions,
            "ocr_preview": ocr_preview,
            "summary": {
                "upload_count": len(uploads),
                "ocr_page_count": len(ocr_preview.get("pages") or []),
                "question_count": len(questions),
                "question_bank_count": len(self.read_question_bank()),
                "has_export": export_exists,
                "export_filename": self._export_path().name if export_exists else "",
            },
            "capabilities": {
                "ocr_configured": bool(ocr_credentials),
                "llm_configured": bool(settings.openai_api_key),
                "llm_profile": settings.chat_profile,
                "llm_model_name": settings.model_name,
                "paddleocr_api_url": settings.paddleocr_api_url or "",
                "paddleocr_model": settings.paddleocr_model or "PaddleOCR-VL-1.5",
            },
        }

    def run_ocr(self, settings: Settings | None = None, *, selected_filename: str = "") -> dict[str, Any]:
        uploads = self._select_uploads(selected_filename)
        if not uploads:
            raise RuntimeError("请先上传题库文件")

        ocr_credentials = self._current_ocr_credentials(settings)
        if not ocr_credentials:
            raise RuntimeError("当前未配置 PaddleOCR；请先设置 PADDLEOCR_API_URL 和 PADDLEOCR_API_TOKEN")

        legacy = self._configure_legacy_runtime()
        for stale_path in (self._questions_path(), self._export_path()):
            stale_path.unlink(missing_ok=True)
        file_paths = [str(self.upload_dir / item["filename"]) for item in uploads]
        prepared_paths = []
        for path in file_paths:
            prepared_paths.extend(legacy.utils.prepare_input(path))

        ocr_data = legacy.workflow._run_ocr_and_simplify(prepared_paths, ocr_credentials=ocr_credentials)
        if not ocr_data:
            raise RuntimeError("OCR 未返回可用内容，请检查 PaddleOCR 配置或上传文件")

        answer_layout_type = legacy.workflow._classify_answer_layout(ocr_data)
        first_question_page_index = legacy.workflow._first_question_page_index(ocr_data)
        question_page_indices: list[int] = []
        answer_page_indices: list[int] = []
        if answer_layout_type == "separated_tail":
            question_page_indices, answer_page_indices = legacy.workflow._split_separated_tail_page_groups(ocr_data)

        pages = []
        for page in ocr_data:
            blocks = page.get("blocks", [])
            text_segments = []
            for block in blocks:
                content = str(block.get("block_content", "") or "").strip()
                if not content:
                    continue
                text_segments.append(content.replace("\n", " "))
                if len(" ".join(text_segments)) >= 220:
                    break
            pages.append(
                {
                    "page_index": int(page.get("page_index", 0)),
                    "block_count": len(blocks),
                    "preview_text": " ".join(text_segments)[:220],
                    "blocks": [
                        {
                            "label": block.get("block_label", ""),
                            "content": self._normalize_asset_reference(block.get("block_content"))
                            if str(block.get("block_label", "") or "") in {"image", "chart"}
                            else str(block.get("block_content", "") or "")[:240],
                            "order": block.get("block_order"),
                        }
                        for block in blocks[:24]
                    ],
                }
            )

        _write_json(self._ocr_cache_path(), ocr_data)
        preview_payload = {
            "updated_at": _utc_now_iso(),
            "selected_filename": uploads[0]["filename"] if len(uploads) == 1 else "",
            "source_filenames": [item["filename"] for item in uploads],
            "pages": pages,
            "answer_layout": {
                "type": answer_layout_type,
                "label": "题目后紧跟答案" if answer_layout_type == "mixed_inline" else "答案集中在后部" if answer_layout_type == "separated_tail" else "未识别",
                "first_question_page_index": first_question_page_index,
                "needs_confirmation": answer_layout_type in ("mixed_inline", "separated_tail"),
                "question_page_indices": question_page_indices,
                "answer_page_indices": answer_page_indices,
            },
        }
        _write_json(self._ocr_preview_path(), preview_payload)
        return preview_payload

    def run_split(
        self,
        settings: Settings,
        *,
        confirmed_answer_layout: str = "",
        selected_page_indices: list[int] | None = None,
        selected_filename: str = "",
    ) -> dict[str, Any]:
        uploads = self._select_uploads(selected_filename)
        if not uploads:
            raise RuntimeError("请先上传题库文件")
        if not settings.openai_api_key:
            raise RuntimeError("当前 AI Tutor 没有可用模型配置，无法执行题目分割")

        legacy = self._configure_legacy_llm(settings)
        self._export_path().unlink(missing_ok=True)
        state: dict[str, Any] = {
            "file_paths": [str(self.upload_dir / item["filename"]) for item in uploads],
            "model_provider": "openai",
            "model_name": settings.model_name,
            "ocr_credentials": self._current_ocr_credentials(settings),
            "ocr_cache_path": str(self._ocr_cache_path()),
            "confirmed_answer_layout": confirmed_answer_layout.strip(),
            "selected_page_indices": [int(i) for i in (selected_page_indices or [])],
        }
        try:
            state.update(legacy.workflow.prepare_input_node(state))
            state.update(legacy.workflow.split_questions_node(state))
            state.update(legacy.workflow.correct_questions_node(state))
            return {
            "questions": self._serialize_questions_for_frontend(
                    state.get("questions") or self.read_questions()
                ),
                "warnings": state.get("warnings") or [],
                "selected_filename": uploads[0]["filename"] if len(uploads) == 1 else "",
                "source_filenames": [item["filename"] for item in uploads],
            }
        finally:
            legacy.settings.clear_request_provider_context()

    def export_questions(self, selected_ids: list[str] | None = None) -> dict[str, Any]:
        questions = self.read_questions()
        if not questions:
            raise RuntimeError("当前没有可导出的分割结果")

        if selected_ids:
            chosen = [str(item) for item in selected_ids]
        else:
            chosen = [str(item.get("uid")) for item in questions if item.get("uid") is not None]

        legacy = self._configure_legacy_runtime()
        output_path = legacy.utils.export_wrongbook(
            questions,
            chosen,
            output_path=str(self._export_path()),
        )
        return {
            "output_path": output_path,
            "filename": Path(output_path).name,
        }

    def save_questions_to_library(
        self,
        selected_ids: list[str] | None = None,
        *,
        source_files: list[str] | None = None,
    ) -> dict[str, Any]:
        questions = self.read_questions()
        if not questions:
            raise RuntimeError("当前没有可保存的分割结果")

        selected_set = {str(item) for item in (selected_ids or []) if str(item).strip()}
        chosen = [
            dict(question)
            for question in questions
            if not selected_set or str(question.get("uid", "")).strip() in selected_set
        ]
        if not chosen:
            raise RuntimeError("没有选中可保存的题目")

        existing = self.read_question_bank()
        batch_id = datetime.now(timezone.utc).strftime("qb_%Y%m%d%H%M%S")
        saved_at = _utc_now_iso()
        normalized_source_files = [
            str(item).strip()
            for item in (source_files or [])
            if str(item).strip()
        ] or [item["filename"] for item in self.list_uploads()]

        copied_assets: dict[str, str] = {}
        new_entries: list[dict[str, Any]] = []
        for index, question in enumerate(chosen, start=1):
            entry = self._persist_question_assets(
                self._normalize_question_payload(question),
                batch_id=batch_id,
                copied_assets=copied_assets,
            )
            entry["library_id"] = f"{batch_id}_{index}"
            entry["source_batch_id"] = batch_id
            entry["saved_at"] = saved_at
            entry["source_files"] = normalized_source_files
            new_entries.append(entry)

        _write_json(self._question_bank_path(), new_entries + existing)
        return {
            "saved_count": len(new_entries),
            "batch_id": batch_id,
            "items": self.list_question_bank(),
        }

    def delete_question_bank_entry(self, library_id: str) -> bool:
        target_id = str(library_id or "").strip()
        if not target_id:
            raise ValueError("题库条目 ID 不能为空")
        entries = self.read_question_bank()
        removed_entry = next(
            (entry for entry in entries if str(entry.get("library_id", "")).strip() == target_id),
            None,
        )
        remaining = [
            entry for entry in entries
            if str(entry.get("library_id", "")).strip() != target_id
        ]
        if len(remaining) == len(entries):
            return False
        _write_json(self._question_bank_path(), remaining)
        source_batch_id = str((removed_entry or {}).get("source_batch_id", "")).strip()
        if source_batch_id and not any(
            str(entry.get("source_batch_id", "")).strip() == source_batch_id
            for entry in remaining
        ):
            shutil.rmtree(self._question_bank_assets_dir() / source_batch_id, ignore_errors=True)
        return True

    def clear_question_bank(self) -> int:
        entries = self.read_question_bank()
        self._question_bank_path().unlink(missing_ok=True)
        shutil.rmtree(self._question_bank_assets_dir(), ignore_errors=True)
        self._question_bank_assets_dir().mkdir(parents=True, exist_ok=True)
        return len(entries)

    def resolve_upload_path(self, filename: str) -> Path:
        safe_name = _safe_filename(filename)
        path = self.upload_dir / safe_name
        if not path.exists():
            raise FileNotFoundError(filename)
        return path

    def resolve_export_path(self, filename: str) -> Path:
        safe_name = _safe_filename(filename)
        path = self.results_dir / safe_name
        if not path.exists():
            raise FileNotFoundError(filename)
        return path

    def resolve_asset_path(self, asset_path: str) -> Path:
        normalized = self._asset_relative_path(asset_path)
        if not normalized:
            raise ValueError("资源路径不能为空")
        if normalized.startswith("question_bank/assets/"):
            candidate = (self.workspace_root / normalized).resolve()
            allowed_root = self._question_bank_assets_dir().resolve()
        else:
            candidate = (self.struct_dir / normalized).resolve()
            allowed_root = self.struct_dir.resolve()
        if allowed_root not in candidate.parents and candidate != allowed_root:
            raise ValueError("资源路径不合法")
        if not candidate.exists() or not candidate.is_file():
            raise FileNotFoundError(asset_path)
        return candidate

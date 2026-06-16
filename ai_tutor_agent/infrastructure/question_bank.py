from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class LocalQuestionBankProvider:
    def __init__(self, base_dir: str | Path = "data/question_bank", *, course_id: str = "a2-control-theory") -> None:
        self.base_dir = Path(base_dir)
        self.course_id = course_id
        self.objective_questions = self._load_items("objective_questions.jsonl")
        self.variant_questions = self._load_items("variant_questions.jsonl")
        self.homework_questions = self._load_items("homework_questions.jsonl")
        self.assessment_questions_pool = self._load_items("assessment_questions.jsonl")
        self.runtime_question_bank_path = Path("data/error_correction_runtime/question_bank/questions.json")

    def get_objective_questions(self, node_id: str, k: int = 10) -> list[dict[str, Any]]:
        return self._take_for_nodes(self.objective_questions, [node_id], k)

    def get_variant_question(self, wrong_item: dict[str, Any]) -> dict[str, Any]:
        source_qid = str(wrong_item.get("question_id") or wrong_item.get("id") or "").strip()
        node_id = str(wrong_item.get("node_id") or "").strip()
        for item in self.variant_questions:
            if source_qid and str(item.get("source_question_id") or "").strip() == source_qid:
                return dict(item)
        candidates = self._take_for_nodes(self.variant_questions, [node_id], 1)
        return dict(candidates[0]) if candidates else {}

    def get_homework_questions(self, node_ids: list[str], k: int = 5) -> list[dict[str, Any]]:
        return self._take_for_nodes(self.homework_questions, node_ids, k)

    def get_assessment_questions(self, node_ids: list[str], k: int = 10) -> list[dict[str, Any]]:
        return self._take_for_nodes(self.assessment_questions_pool, node_ids, k)

    def _load_items(self, filename: str) -> list[dict[str, Any]]:
        paths = [
            self.base_dir / self.course_id / filename,
            self.base_dir / filename,
        ]
        for path in paths:
            if path.exists():
                return self._read_jsonl(path)
        return []

    def _read_jsonl(self, path: Path) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        with open(path, "r", encoding="utf-8") as file_obj:
            for line in file_obj:
                raw = line.strip()
                if not raw:
                    continue
                try:
                    item = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if isinstance(item, dict):
                    normalized = self._normalize_question(item)
                    if normalized:
                        items.append(normalized)
        return items

    def _take_for_nodes(self, items: list[dict[str, Any]], node_ids: list[str], k: int) -> list[dict[str, Any]]:
        requested = [str(node_id or "").strip() for node_id in node_ids if str(node_id or "").strip()]
        requested_set = set(requested)
        matched: list[dict[str, Any]] = []
        for item in items:
            item_node_id = str(item.get("node_id") or "").strip()
            covered_node_ids = {str(value).strip() for value in item.get("covered_node_ids") or [] if str(value).strip()}
            if requested_set and item_node_id not in requested_set and not requested_set.intersection(covered_node_ids):
                continue
            matched.append(dict(item))
            if len(matched) >= k:
                return matched
        if requested_set:
            return matched
        return [dict(item) for item in items[:k]]

    def _normalize_question(self, item: dict[str, Any]) -> dict[str, Any] | None:
        question_id = str(item.get("question_id") or item.get("id") or "").strip()
        prompt = str(item.get("prompt") or item.get("stem") or item.get("question") or "").strip()
        if not question_id or not prompt:
            return None
        normalized = dict(item)
        normalized["question_id"] = question_id
        if "stem" not in normalized and prompt:
            normalized["stem"] = prompt
        if "prompt" not in normalized and prompt:
            normalized["prompt"] = prompt
        normalized["node_id"] = str(normalized.get("node_id") or "").strip()
        normalized["source"] = str(normalized.get("source") or "local_question_bank").strip()
        return normalized

    # ── 运行时题库 (来自 origin/524yang) ──

    def list_runtime_question_bank_items(self) -> list[dict[str, Any]]:
        """读取 error_correction_runtime 题库 (含 OCR 图片题)。"""
        if not self.runtime_question_bank_path.exists():
            return []
        try:
            payload = json.loads(self.runtime_question_bank_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        if not isinstance(payload, list):
            return []
        return [self._normalize_runtime_question(item) for item in payload if isinstance(item, dict)]

    def _normalize_runtime_asset(self, value: Any) -> str:
        raw = str(value or "").strip()
        if not raw:
            return ""
        if raw.startswith("http://") or raw.startswith("https://") or raw.startswith("/api/error-correction/assets/"):
            return raw
        normalized = raw.replace("\\", "/").lstrip("/")
        return f"/api/error-correction/assets/{normalized}"

    def _normalize_runtime_question(self, item: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(item)
        blocks = []
        for block in list(normalized.get("content_blocks") or []):
            payload = dict(block or {})
            if str(payload.get("block_type") or "") == "image":
                payload["content"] = self._normalize_runtime_asset(payload.get("content"))
            blocks.append(payload)
        normalized["content_blocks"] = blocks
        option_images = normalized.get("option_images")
        if isinstance(option_images, list):
            normalized["option_images"] = [self._normalize_runtime_asset(i) if i else "" for i in option_images]
        image_refs = normalized.get("image_refs")
        if isinstance(image_refs, list):
            normalized["image_refs"] = [self._normalize_runtime_asset(i) if i else "" for i in image_refs]
        return normalized

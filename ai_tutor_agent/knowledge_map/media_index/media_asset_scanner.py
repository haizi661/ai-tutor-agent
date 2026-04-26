from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from ai_tutor_agent.knowledge_map.config.media_index_config import MediaIndexConfig
from ai_tutor_agent.knowledge_map.schema.media_asset_schema import (
    build_empty_raw_media_candidate,
    normalize_raw_media_candidate,
)


class MediaAssetScanner:
    def __init__(self, config: MediaIndexConfig | None = None) -> None:
        self.config = config or MediaIndexConfig()

    def scan_documents(self) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        root = self.config.mineru_cache_root
        if not root.exists():
            return []

        for doc_dir in sorted(path for path in root.iterdir() if path.is_dir()):
            candidates.extend(self.scan_document(doc_dir))
        return candidates

    def scan_document(self, doc_dir: str | Path) -> list[dict[str, Any]]:
        directory = Path(doc_dir)
        manifest_path = directory / "manifest.json"
        full_md_path = directory / "full.md"
        if not manifest_path.exists() or not full_md_path.exists():
            return []

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            full_md = full_md_path.read_text(encoding="utf-8")
        except Exception:
            return []

        lines = full_md.splitlines()
        source_doc_id = directory.name
        source_doc_name = str(manifest.get("pdf_name", "") or directory.name)
        chapter_title = self._extract_chapter_title(lines, source_doc_name)

        candidates: list[dict[str, Any]] = []
        if self.config.include_figures:
            candidates.extend(
                self._extract_image_candidates(
                    lines=lines,
                    manifest=manifest,
                    source_doc_id=source_doc_id,
                    source_doc_name=source_doc_name,
                    chapter_title=chapter_title,
                    doc_dir=directory,
                )
            )
        if self.config.include_formulas:
            candidates.extend(
                self._extract_formula_candidates(
                    lines=lines,
                    source_doc_id=source_doc_id,
                    source_doc_name=source_doc_name,
                    chapter_title=chapter_title,
                )
            )
        if self.config.include_tables:
            candidates.extend(
                self._extract_table_candidates(
                    full_md=full_md,
                    source_doc_id=source_doc_id,
                    source_doc_name=source_doc_name,
                    chapter_title=chapter_title,
                )
            )
        return candidates

    def write_jsonl(self, candidates: list[dict[str, Any]], output_path: str | Path | None = None) -> Path:
        target = Path(output_path) if output_path is not None else self.config.raw_candidates_path
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as fh:
            for item in candidates:
                fh.write(json.dumps(item, ensure_ascii=False) + "\n")
        return target.resolve()

    def _extract_image_candidates(
        self,
        *,
        lines: list[str],
        manifest: dict[str, Any],
        source_doc_id: str,
        source_doc_name: str,
        chapter_title: str,
        doc_dir: Path,
    ) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        pending_images: list[str] = []
        pending_line_index = -1

        for idx, raw in enumerate(lines):
            line = (raw or "").strip()
            image_paths = re.findall(r"!\[.*?\]\((.*?)\)", line)
            if image_paths:
                pending_images.extend(image_paths)
                pending_line_index = idx
                trailing_text = re.sub(r"!\[.*?\]\((.*?)\)", "", line).strip()
                if trailing_text:
                    candidates.extend(
                        self._build_figure_candidates(
                            image_paths=pending_images,
                            caption_text=trailing_text,
                            line_index=idx,
                            lines=lines,
                            manifest=manifest,
                            source_doc_id=source_doc_id,
                            source_doc_name=source_doc_name,
                            chapter_title=chapter_title,
                            doc_dir=doc_dir,
                        )
                    )
                    pending_images = []
                    pending_line_index = -1
                continue

            if pending_images and self._looks_like_caption(line):
                candidates.extend(
                    self._build_figure_candidates(
                        image_paths=pending_images,
                        caption_text=line,
                        line_index=idx,
                        lines=lines,
                        manifest=manifest,
                        source_doc_id=source_doc_id,
                        source_doc_name=source_doc_name,
                        chapter_title=chapter_title,
                        doc_dir=doc_dir,
                    )
                )
                pending_images = []
                pending_line_index = -1
                continue

            if pending_images and idx - pending_line_index >= 2:
                nearby_text = self._extract_nearby_text(lines, pending_line_index)
                candidates.extend(
                    self._build_figure_candidates(
                        image_paths=pending_images,
                        caption_text="",
                        line_index=pending_line_index,
                        lines=lines,
                        manifest=manifest,
                        source_doc_id=source_doc_id,
                        source_doc_name=source_doc_name,
                        chapter_title=chapter_title,
                        doc_dir=doc_dir,
                        nearby_text_override=nearby_text,
                    )
                )
                pending_images = []
                pending_line_index = -1

        if pending_images:
            nearby_text = self._extract_nearby_text(lines, pending_line_index)
            candidates.extend(
                self._build_figure_candidates(
                    image_paths=pending_images,
                    caption_text="",
                    line_index=pending_line_index,
                    lines=lines,
                    manifest=manifest,
                    source_doc_id=source_doc_id,
                    source_doc_name=source_doc_name,
                    chapter_title=chapter_title,
                    doc_dir=doc_dir,
                    nearby_text_override=nearby_text,
                )
            )

        return candidates

    def _build_figure_candidates(
        self,
        *,
        image_paths: list[str],
        caption_text: str,
        line_index: int,
        lines: list[str],
        manifest: dict[str, Any],
        source_doc_id: str,
        source_doc_name: str,
        chapter_title: str,
        doc_dir: Path,
        nearby_text_override: str | None = None,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for image_path in image_paths:
            resolved_path = self._resolve_image_path(image_path, manifest, doc_dir)
            if not resolved_path:
                continue
            candidate = build_empty_raw_media_candidate()
            candidate["asset_type"] = "figure"
            candidate["source_doc_id"] = source_doc_id
            candidate["source_doc_name"] = source_doc_name
            candidate["source_path"] = str(resolved_path)
            candidate["chapter_title"] = chapter_title
            candidate["caption_text"] = self._normalize_whitespace(caption_text)
            candidate["nearby_text"] = nearby_text_override or self._extract_nearby_text(lines, line_index)
            candidate["raw_text"] = candidate["caption_text"] or candidate["nearby_text"]
            candidate["content_hash"] = self._hash_text(
                f"{candidate['source_path']}|{candidate['caption_text']}|{candidate['nearby_text']}"
            )
            candidate["asset_id"] = f"{source_doc_id}:figure:{candidate['content_hash'][:12]}"
            results.append(normalize_raw_media_candidate(candidate))
        return results

    def _extract_formula_candidates(
        self,
        *,
        lines: list[str],
        source_doc_id: str,
        source_doc_name: str,
        chapter_title: str,
    ) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []
        idx = 0
        while idx < len(lines):
            stripped = (lines[idx] or "").strip()
            if stripped.startswith("```math"):
                parts: list[str] = []
                idx += 1
                while idx < len(lines):
                    current = (lines[idx] or "").rstrip()
                    if current.strip().startswith("```"):
                        break
                    if current.strip():
                        parts.append(current.strip())
                    idx += 1
                formula_text = self._normalize_whitespace(" ".join(parts))[: self.config.max_formula_chars]
                if formula_text:
                    candidates.append(
                        self._build_formula_candidate(
                            formula_text=formula_text,
                            line_index=idx,
                            lines=lines,
                            source_doc_id=source_doc_id,
                            source_doc_name=source_doc_name,
                            chapter_title=chapter_title,
                        )
                    )
            elif stripped.startswith("$$"):
                parts = []
                first = stripped[2:].strip()
                if first and not stripped.endswith("$$"):
                    parts.append(first)
                elif stripped.endswith("$$") and len(stripped) > 4:
                    parts.append(stripped[2:-2].strip())
                idx += 1
                while idx < len(lines):
                    current = (lines[idx] or "").rstrip()
                    if current.strip().endswith("$$"):
                        tail = current.strip()[:-2].strip()
                        if tail:
                            parts.append(tail)
                        break
                    if current.strip():
                        parts.append(current.strip())
                    idx += 1
                formula_text = self._normalize_whitespace(" ".join(parts))[: self.config.max_formula_chars]
                if formula_text:
                    candidates.append(
                        self._build_formula_candidate(
                            formula_text=formula_text,
                            line_index=idx,
                            lines=lines,
                            source_doc_id=source_doc_id,
                            source_doc_name=source_doc_name,
                            chapter_title=chapter_title,
                        )
                    )
            idx += 1
        return candidates

    def _build_formula_candidate(
        self,
        *,
        formula_text: str,
        line_index: int,
        lines: list[str],
        source_doc_id: str,
        source_doc_name: str,
        chapter_title: str,
    ) -> dict[str, Any]:
        candidate = build_empty_raw_media_candidate()
        candidate["asset_type"] = "formula"
        candidate["source_doc_id"] = source_doc_id
        candidate["source_doc_name"] = source_doc_name
        candidate["chapter_title"] = chapter_title
        candidate["raw_text"] = formula_text
        candidate["nearby_text"] = self._extract_nearby_text(lines, line_index)
        candidate["content_hash"] = self._hash_text(formula_text)
        candidate["asset_id"] = f"{source_doc_id}:formula:{candidate['content_hash'][:12]}"
        return normalize_raw_media_candidate(candidate)

    def _extract_table_candidates(
        self,
        *,
        full_md: str,
        source_doc_id: str,
        source_doc_name: str,
        chapter_title: str,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for idx, match in enumerate(re.finditer(r"<table>.*?</table>", full_md, flags=re.DOTALL), start=1):
            table_html = self._normalize_whitespace(match.group(0))[: self.config.max_table_chars]
            if not table_html:
                continue
            candidate = build_empty_raw_media_candidate()
            candidate["asset_type"] = "table"
            candidate["source_doc_id"] = source_doc_id
            candidate["source_doc_name"] = source_doc_name
            candidate["chapter_title"] = chapter_title
            candidate["raw_text"] = table_html
            candidate["content_hash"] = self._hash_text(table_html)
            candidate["asset_id"] = f"{source_doc_id}:table:{idx:03d}:{candidate['content_hash'][:8]}"
            results.append(normalize_raw_media_candidate(candidate))
        return results

    def _extract_chapter_title(self, lines: list[str], fallback: str) -> str:
        for raw in lines[:40]:
            stripped = (raw or "").strip()
            if stripped.startswith("# "):
                return stripped[2:].strip()
        return fallback

    def _extract_nearby_text(self, lines: list[str], line_index: int) -> str:
        if line_index < 0:
            return ""
        start = max(0, line_index - 3)
        end = min(len(lines), line_index + 4)
        window = []
        for raw in lines[start:end]:
            stripped = (raw or "").strip()
            if not stripped or stripped.startswith("![]("):
                continue
            window.append(stripped)
        return self._normalize_whitespace(" ".join(window))[: self.config.nearby_text_chars]

    def _resolve_image_path(self, image_path: str, manifest: dict[str, Any], doc_dir: Path) -> Path | None:
        normalized = str(image_path).replace("\\", "/").strip()
        trimmed = normalized.replace("images/", "", 1)
        images = manifest.get("images", {}) or {}
        abs_path = None
        if normalized in images:
            abs_path = images[normalized].get("abs_path")
        elif trimmed in images:
            abs_path = images[trimmed].get("abs_path")
        else:
            image_name = Path(trimmed).name
            for meta in images.values():
                if meta.get("original_name") == image_name or meta.get("friendly_name") == image_name:
                    abs_path = meta.get("abs_path")
                    break
        resolved = Path(abs_path) if abs_path else doc_dir / "images" / Path(trimmed).name
        if not resolved.exists():
            return None
        return resolved.resolve()

    def _looks_like_caption(self, text: str) -> bool:
        cleaned = (text or "").strip()
        return bool(re.search(r"^(图|表|Figure|Table)\s*[\d\-]", cleaned, flags=re.IGNORECASE))

    def _normalize_whitespace(self, text: str) -> str:
        return re.sub(r"\s+", " ", (text or "").strip())

    def _hash_text(self, text: str) -> str:
        return hashlib.md5((text or "").encode("utf-8")).hexdigest()

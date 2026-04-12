from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any


class NodeContentEnricher:
    """
    基于现有 MinerU 缓存结果做节点内容增强：
    1. 不再直接读取原始 PDF
    2. 从 data/mineru_cache 下的 full.md 里按章节范围取内容
    3. 为节点补充：
       - page_refs
       - anchor_page
       - page_refs_refined
       - explanation_raw
       - core_concepts
       - key_points
    """

    def __init__(
        self,
        textbook_pdf_path: str | Path | None = None,
        mineru_cache_root: str | Path = "data/mineru_cache",
    ) -> None:
        self.textbook_pdf_path = Path(textbook_pdf_path) if textbook_pdf_path else None
        self.mineru_cache_root = Path(mineru_cache_root)

    def enrich_nodes(self, nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        chapter_docs = self._load_mineru_chapter_docs()

        if not chapter_docs:
            for node in nodes:
                node.setdefault("extra", {})
                node["extra"]["page_ref_status"] = "mineru_cache_missing"
            return nodes

        for node in nodes:
            node.setdefault("extra", {})

            chapter_page_range = node["extra"].get("chapter_page_range", []) or []
            if not isinstance(chapter_page_range, list) or len(chapter_page_range) != 2:
                node["extra"]["page_ref_status"] = "chapter_page_range_missing"
                continue

            chapter_start, chapter_end = chapter_page_range
            matched_doc = self._find_matching_chapter_doc(chapter_docs, chapter_start, chapter_end)

            if matched_doc is None:
                node["extra"]["page_ref_status"] = "mineru_doc_not_found"
                continue

            node["page_refs"] = list(range(chapter_start, chapter_end + 1))
            node["extra"]["anchor_page"] = chapter_start
            node["extra"]["page_refs_refined"] = self._build_refined_pages(node, chapter_start, chapter_end)
            node["extra"]["mineru_doc_name"] = matched_doc["pdf_name"]

            explanation_raw = self._build_explanation_raw_from_md(node, matched_doc["full_md"])
            node["explanation_raw"] = explanation_raw

            core_concepts = self._build_core_concepts(node)
            node["core_concepts"] = core_concepts

            key_points = self._build_key_points(node, explanation_raw)
            node["key_points"] = key_points

            if not str(node.get("summary", "")).strip():
                node["summary"] = self._build_summary_from_explanation(explanation_raw)

            node["extra"]["page_ref_status"] = "ok"
            node["extra"]["page_ref_count"] = len(node["page_refs"])
            node["extra"]["page_refined_count"] = len(node["extra"]["page_refs_refined"])

        return nodes

    def _load_mineru_chapter_docs(self) -> list[dict[str, Any]]:
        docs: list[dict[str, Any]] = []

        if not self.mineru_cache_root.exists():
            return docs

        for item in self.mineru_cache_root.iterdir():
            if not item.is_dir():
                continue

            manifest_path = item / "manifest.json"
            full_md_path = item / "full.md"

            if not manifest_path.exists() or not full_md_path.exists():
                continue

            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = json.load(f)

                with open(full_md_path, "r", encoding="utf-8") as f:
                    full_md = f.read()

                pdf_name = str(manifest.get("pdf_name", "")).strip()
                page_range = self._extract_page_range_from_pdf_name(pdf_name)

                if page_range is None:
                    continue

                start_page, end_page = page_range
                docs.append(
                    {
                        "cache_dir": str(item),
                        "pdf_name": pdf_name,
                        "full_md": full_md,
                        "start_page": start_page,
                        "end_page": end_page,
                    }
                )
            except Exception:
                continue

        docs.sort(key=lambda x: x["start_page"])
        return docs

    def _extract_page_range_from_pdf_name(self, pdf_name: str) -> tuple[int, int] | None:
        """
        从章节切分后的文件名里提取原书页码范围。
        例如：
        chapter_03_p082-159_xxx.pdf -> (82, 159)
        """
        m = re.search(r"_p(\d+)-(\d+)_", pdf_name)
        if not m:
            m = re.search(r"_p(\d+)-(\d+)\.pdf$", pdf_name, flags=re.I)

        if not m:
            return None

        return int(m.group(1)), int(m.group(2))

    def _find_matching_chapter_doc(
        self,
        chapter_docs: list[dict[str, Any]],
        start_page: int,
        end_page: int,
    ) -> dict[str, Any] | None:
        for doc in chapter_docs:
            if doc["start_page"] == start_page and doc["end_page"] == end_page:
                return doc

        for doc in chapter_docs:
            if doc["start_page"] <= start_page <= doc["end_page"]:
                return doc

        return None

    def _build_refined_pages(
        self,
        node: dict[str, Any],
        chapter_start: int,
        chapter_end: int,
    ) -> list[int]:
        level = int(node.get("level", 1))

        if level == 1:
            end = min(chapter_start + 3, chapter_end)
            return list(range(chapter_start, end + 1))

        # 二级节点先取该章前 4 页，后续如果你想再细化，可再做标题定位
        end = min(chapter_start + 3, chapter_end)
        return list(range(chapter_start, end + 1))

    def _build_explanation_raw_from_md(self, node: dict[str, Any], full_md: str) -> str:
        node_name = str(node.get("name", "")).strip()
        tags = node.get("tags", []) or []
        extra = node.get("extra", {}) or {}
        retrieval_keywords = extra.get("retrieval_keywords", []) or []

        lines = self._clean_md_lines(full_md)
        scored_lines: list[tuple[int, str]] = []

        for line in lines:
            score = 0

            if node_name and node_name in line:
                score += 5

            for kw in retrieval_keywords:
                kw = str(kw).strip()
                if len(kw) >= 2 and kw in line:
                    score += 3

            for tag in tags:
                tag = str(tag).strip()
                if len(tag) >= 2 and tag in line:
                    score += 1

            if score > 0:
                scored_lines.append((score, line))

        scored_lines.sort(key=lambda x: (-x[0], len(x[1])))

        selected: list[str] = []
        for _, line in scored_lines:
            if line not in selected:
                selected.append(line)
            if len(selected) >= 4:
                break

        return " ".join(selected)

    def _clean_md_lines(self, full_md: str) -> list[str]:
        lines: list[str] = []

        for raw in full_md.splitlines():
            line = (raw or "").strip()
            if not line:
                continue

            if line.startswith("![]("):
                continue
            if line.startswith("```"):
                continue
            if line.startswith("<table") or line.startswith("</table"):
                continue
            if "|" in line and line.count("|") >= 2:
                continue
            if re.match(r"^\s*[-:| ]+\s*$", line):
                continue

            line = re.sub(r"!\[.*?\]\(.*?\)", "", line)
            line = re.sub(r"<[^>]+>", " ", line)
            line = re.sub(r"\s+", " ", line).strip()

            if len(line) >= 10:
                lines.append(line)

        return lines

    def _build_core_concepts(self, node: dict[str, Any]) -> list[str]:
        tags = node.get("tags", []) or []
        extra = node.get("extra", {}) or {}
        retrieval_keywords = extra.get("retrieval_keywords", []) or []

        concepts: list[str] = []

        for item in retrieval_keywords + tags:
            item = str(item).strip()
            if item and item not in concepts:
                concepts.append(item)

        return concepts[:6]

    def _build_key_points(self, node: dict[str, Any], explanation_raw: str) -> list[str]:
        if not explanation_raw.strip():
            return []

        parts = re.split(r"(?<=[。！？.!?])\s+", explanation_raw)
        results: list[str] = []

        for part in parts:
            part = self._clean_sentence(part)
            if len(part) < 10:
                continue
            if part not in results:
                results.append(part)
            if len(results) >= 4:
                break

        return results

    def _build_summary_from_explanation(self, explanation_raw: str) -> str:
        if not explanation_raw.strip():
            return ""

        parts = re.split(r"(?<=[。！？.!?])\s+", explanation_raw)
        cleaned = [self._clean_sentence(p) for p in parts if self._clean_sentence(p)]
        if not cleaned:
            return ""

        return cleaned[0][:120]

    @staticmethod
    def _clean_sentence(text: str) -> str:
        text = text.strip()
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"^#+\s*", "", text)
        return text.strip()
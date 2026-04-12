from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class NodeRetrievalBuilder:
    """
    基于现有 MinerU 缓存结果做节点候选抽取：
    1. 不再从原始 PDF 读文本
    2. 直接从章节 full.md 中抽 definition / keypoint / formula / example
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
                node["extra"]["retrieval_status"] = "mineru_cache_missing"
            return nodes

        for node in nodes:
            node.setdefault("extra", {})
            chapter_page_range = node["extra"].get("chapter_page_range", []) or []

            if not isinstance(chapter_page_range, list) or len(chapter_page_range) != 2:
                node["extra"]["retrieval_status"] = "chapter_page_range_missing"
                continue

            chapter_start, chapter_end = chapter_page_range
            matched_doc = self._find_matching_chapter_doc(chapter_docs, chapter_start, chapter_end)

            if matched_doc is None:
                node["extra"]["retrieval_status"] = "mineru_doc_not_found"
                continue

            md_content = matched_doc["full_md"]

            text_lines = self._collect_text_lines(md_content)
            formula_lines = self._collect_formula_lines(md_content)
            figure_lines = self._collect_figure_related_lines(md_content)

            candidate_sentences = self._collect_candidate_sentences(node, text_lines)

            node["definition_candidates"] = self._select_definition_candidates(node, candidate_sentences)
            node["key_point_candidates"] = self._select_key_point_candidates(node, candidate_sentences)
            node["formula_candidates"] = self._select_formula_candidates(node, formula_lines, candidate_sentences)
            node["example_candidates"] = self._select_example_candidates(node, candidate_sentences, figure_lines)

            node["extra"]["retrieval_status"] = "ok"
            node["extra"]["retrieval_candidate_sentence_count"] = len(candidate_sentences)
            node["extra"]["retrieval_formula_line_count"] = len(formula_lines)
            node["extra"]["retrieval_figure_line_count"] = len(figure_lines)
            node["extra"]["retrieval_source_pdf"] = matched_doc["pdf_name"]

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

    def _collect_text_lines(self, md_content: str) -> list[str]:
        lines: list[str] = []

        for raw in md_content.splitlines():
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
            if self._is_figure_caption_line(line):
                continue
            if self._looks_like_formula_text(line):
                continue

            line = re.sub(r"!\[.*?\]\(.*?\)", "", line)
            line = re.sub(r"<[^>]+>", " ", line)
            line = re.sub(r"\s+", " ", line).strip()

            if len(line) >= 8:
                lines.append(line)

        return lines

    def _collect_formula_lines(self, md_content: str) -> list[str]:
        results: list[str] = []
        lines = md_content.splitlines()

        i = 0
        while i < len(lines):
            line = (lines[i] or "").rstrip()
            stripped = line.strip()

            if stripped.startswith("```math"):
                formula_parts: list[str] = []
                i += 1
                while i < len(lines):
                    candidate = (lines[i] or "").rstrip()
                    if candidate.strip().startswith("```"):
                        break
                    if candidate.strip():
                        formula_parts.append(candidate.strip())
                    i += 1

                if formula_parts:
                    results.append(self._normalize_formula_text(" ".join(formula_parts)))
                i += 1
                continue

            if stripped.startswith("$$"):
                formula_parts: list[str] = []
                after = stripped[2:]

                if after.endswith("$$") and len(after) > 2:
                    formula_parts.append(after[:-2].strip())
                    results.append(self._normalize_formula_text(" ".join(formula_parts)))
                    i += 1
                    continue

                if after.strip():
                    formula_parts.append(after.strip())

                i += 1
                while i < len(lines):
                    candidate = (lines[i] or "").rstrip()
                    cstrip = candidate.strip()

                    if cstrip.endswith("$$"):
                        body = cstrip[:-2].strip()
                        if body:
                            formula_parts.append(body)
                        break

                    if cstrip:
                        formula_parts.append(cstrip)
                    i += 1

                if formula_parts:
                    results.append(self._normalize_formula_text(" ".join(formula_parts)))
                i += 1
                continue

            if self._looks_like_formula_text(stripped):
                results.append(self._normalize_formula_text(stripped))

            i += 1

        dedup: list[str] = []
        for item in results:
            if item and item not in dedup:
                dedup.append(item)

        return dedup

    def _collect_figure_related_lines(self, md_content: str) -> list[str]:
        lines = md_content.splitlines()
        results: list[str] = []

        for idx, raw in enumerate(lines):
            line = (raw or "").strip()
            if not line:
                continue

            if self._is_figure_caption_line(line):
                prev_text = " ".join((lines[max(0, idx - 2):idx]))
                next_text = " ".join((lines[idx + 1:min(len(lines), idx + 3)]))
                combined = f"{prev_text} {line} {next_text}"
                combined = re.sub(r"\s+", " ", combined).strip()
                if combined:
                    results.append(combined)

        return results

    def _collect_candidate_sentences(
        self,
        node: dict[str, Any],
        text_lines: list[str],
    ) -> list[str]:
        node_name = str(node.get("name", "")).strip()
        tags = node.get("tags", []) or []
        extra = node.get("extra", {}) or {}
        retrieval_keywords = extra.get("retrieval_keywords", []) or []

        candidates: list[tuple[int, str]] = []

        for line in text_lines:
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
                candidates.append((score, line))

        candidates.sort(key=lambda x: (-x[0], len(x[1])))

        unique_sentences: list[str] = []
        for _, sent in candidates:
            if sent not in unique_sentences:
                unique_sentences.append(sent)

        return unique_sentences

    def _select_definition_candidates(
        self,
        node: dict[str, Any],
        candidate_sentences: list[str],
    ) -> list[str]:
        definition_markers = [
            "是",
            "指",
            "称为",
            "定义",
            "基本概念",
            "就是",
            "表示",
        ]

        return self._rank_and_select(
            candidate_sentences=candidate_sentences,
            positive_markers=definition_markers,
            negative_markers=["例如", "比如", "图", "表"],
            keep_top=4,
        )

    def _select_key_point_candidates(
        self,
        node: dict[str, Any],
        candidate_sentences: list[str],
    ) -> list[str]:
        keypoint_markers = [
            "主要",
            "一般",
            "通常",
            "特点",
            "关系",
            "条件",
            "分析",
            "设计",
            "应用",
            "性能",
            "要求",
        ]

        return self._rank_and_select(
            candidate_sentences=candidate_sentences,
            positive_markers=keypoint_markers,
            negative_markers=["图", "表"],
            keep_top=6,
        )

    def _select_formula_candidates(
        self,
        node: dict[str, Any],
        formula_lines: list[str],
        candidate_sentences: list[str],
    ) -> list[str]:
        node_name = str(node.get("name", "")).strip()
        tags = node.get("tags", []) or []
        results: list[str] = []

        # 先优先取 markdown 里明确识别到的公式块
        for line in formula_lines:
            score = 0

            if node_name and node_name in line:
                score += 3

            for tag in tags:
                tag = str(tag).strip()
                if len(tag) >= 2 and tag in line:
                    score += 1

            if score > 0 or self._looks_like_formula_text(line):
                cleaned = self._normalize_formula_text(line)
                if cleaned and cleaned not in results:
                    results.append(cleaned)

            if len(results) >= 4:
                return results

        # 再退回候选句中带公式特征的内容
        for sent in candidate_sentences:
            if self._looks_like_formula_text(sent):
                cleaned = self._normalize_formula_text(sent)
                if cleaned and cleaned not in results:
                    results.append(cleaned)
            if len(results) >= 4:
                break

        return results

    def _select_example_candidates(
        self,
        node: dict[str, Any],
        candidate_sentences: list[str],
        figure_lines: list[str],
    ) -> list[str]:
        example_markers = [
            "例如",
            "比如",
            "例",
            "实例",
            "系统",
            "应用",
        ]

        results = self._rank_and_select(
            candidate_sentences=candidate_sentences,
            positive_markers=example_markers,
            negative_markers=[],
            keep_top=3,
        )

        for line in figure_lines:
            if line not in results:
                results.append(line)
            if len(results) >= 4:
                break

        return results[:4]

    def _rank_and_select(
        self,
        candidate_sentences: list[str],
        positive_markers: list[str],
        negative_markers: list[str],
        keep_top: int,
    ) -> list[str]:
        scored: list[tuple[int, str]] = []

        for sent in candidate_sentences:
            score = 0

            for marker in positive_markers:
                if marker in sent:
                    score += 2

            for marker in negative_markers:
                if marker in sent:
                    score -= 1

            if score > 0:
                scored.append((score, sent))

        scored.sort(key=lambda x: (-x[0], len(x[1])))

        results: list[str] = []
        for _, sent in scored:
            if sent not in results:
                results.append(sent)
            if len(results) >= keep_top:
                break

        return results

    def _is_figure_caption_line(self, text: str) -> bool:
        if not text:
            return False
        return bool(re.match(r"^\s*(Figure|Fig\.?|图)\s*\d+", text, flags=re.I))

    def _looks_like_formula_text(self, text: str) -> bool:
        if not text:
            return False

        formula_markers = [
            "=",
            "传递函数",
            "微分方程",
            "状态方程",
            "拉氏变换",
            "拉普拉斯变换",
            "z变换",
            "Z变换",
            "频率特性",
        ]

        if any(marker in text for marker in formula_markers):
            return True

        if re.search(r"[A-Za-z]+\([sztjw]\)", text):
            return True

        if re.search(r"[A-Za-z]+\s*=\s*", text):
            return True

        if re.search(r"\$.*?\$", text):
            return True

        return False

    def _normalize_formula_text(self, text: str) -> str:
        text = text.replace("\n", " ").strip()
        text = re.sub(r"\s+", " ", text)
        return text[:600]
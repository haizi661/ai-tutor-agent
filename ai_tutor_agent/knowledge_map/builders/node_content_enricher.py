from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    import fitz  # PyMuPDF
except Exception:  # pragma: no cover
    fitz = None


class NodeContentEnricher:
    """
    第一阶段内容增强器：
    1. 从教材 PDF 中为节点补 page_refs
    2. 从 page_refs 对应页面中抽取 explanation_raw
    3. 生成 core_concepts / key_points 的初版内容

    当前仍然不是 RAG，只是规则增强版。
    """

    def __init__(self, textbook_pdf_path: str | Path | None = None) -> None:
        self.textbook_pdf_path = Path(textbook_pdf_path) if textbook_pdf_path else None

    def enrich_nodes(self, nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not self.textbook_pdf_path or not self.textbook_pdf_path.exists():
            for node in nodes:
                node.setdefault("extra", {})
                node["extra"]["page_ref_status"] = "textbook_pdf_missing"
            return nodes

        if fitz is None:
            for node in nodes:
                node.setdefault("extra", {})
                node["extra"]["page_ref_status"] = "pymupdf_not_installed"
            return nodes

        page_texts = self._read_pdf_pages(self.textbook_pdf_path)

        for node in nodes:
            matched_pages = self._match_pages_for_node(node, page_texts)
            node["page_refs"] = matched_pages

            explanation_raw = self._build_explanation_raw(node, page_texts, matched_pages)
            node["explanation_raw"] = explanation_raw

            core_concepts = self._build_core_concepts(node)
            node["core_concepts"] = core_concepts

            key_points = self._build_key_points(node, page_texts, matched_pages)
            node["key_points"] = key_points

            if not node.get("summary", "").strip():
                node["summary"] = self._build_summary_from_explanation(explanation_raw)

            node.setdefault("extra", {})
            node["extra"]["page_ref_status"] = "ok"
            node["extra"]["page_ref_count"] = len(matched_pages)

        return nodes

    def _read_pdf_pages(self, pdf_path: Path) -> list[str]:
        page_texts: list[str] = []

        with fitz.open(pdf_path) as doc:
            for i in range(len(doc)):
                text = doc[i].get_text("text") or ""
                text = self._normalize_text(text)
                page_texts.append(text)

        return page_texts

    def _match_pages_for_node(self, node: dict[str, Any], page_texts: list[str]) -> list[int]:
        node_name = str(node.get("name", "")).strip()
        tags = node.get("tags", []) or []
        extra = node.get("extra", {}) or {}

        chapter_page_range = extra.get("chapter_page_range", [])
        retrieval_keywords = extra.get("retrieval_keywords", []) or []

        start_page = None
        end_page = None
        if isinstance(chapter_page_range, list) and len(chapter_page_range) == 2:
            start_page, end_page = chapter_page_range

        matched_pages: list[tuple[int, int]] = []

        for idx, page_text in enumerate(page_texts, start=1):
            if not page_text:
                continue

            if start_page is not None and end_page is not None:
                if idx < start_page or idx > end_page:
                    continue

            score = 0

            if node_name and node_name in page_text:
                score += 4

            for kw in retrieval_keywords:
                kw = str(kw).strip()
                if len(kw) >= 2 and kw in page_text:
                    score += 3

            for tag in tags:
                tag = str(tag).strip()
                if len(tag) >= 2 and tag in page_text:
                    score += 1

            if score > 0:
                matched_pages.append((idx, score))

        matched_pages.sort(key=lambda x: (-x[1], x[0]))

        ordered_pages: list[int] = []
        for page_num, _ in matched_pages:
            if page_num not in ordered_pages:
                ordered_pages.append(page_num)

        return self._shrink_to_dense_window(ordered_pages, window_size=12, keep_top=6)

    def _build_explanation_raw(
        self,
        node: dict[str, Any],
        page_texts: list[str],
        matched_pages: list[int],
    ) -> str:
        if not matched_pages:
            return ""

        node_name = str(node.get("name", "")).strip()
        tags = node.get("tags", []) or []
        extra = node.get("extra", {}) or {}
        retrieval_keywords = extra.get("retrieval_keywords", []) or []

        sentences_with_score: list[tuple[int, str]] = []

        for page_num in matched_pages:
            if page_num < 1 or page_num > len(page_texts):
                continue

            text = page_texts[page_num - 1]
            sentences = self._split_sentences(text)

            for sent in sentences:
                score = 0

                if node_name and node_name in sent:
                    score += 4

                for kw in retrieval_keywords:
                    kw = str(kw).strip()
                    if len(kw) >= 2 and kw in sent:
                        score += 3

                for tag in tags:
                    tag = str(tag).strip()
                    if len(tag) >= 2 and tag in sent:
                        score += 1

                if score > 0 and len(sent) >= 12:
                    sentences_with_score.append((score, sent))

        if not sentences_with_score:
            return ""

        sentences_with_score.sort(key=lambda x: (-x[0], len(x[1])))

        selected_sentences: list[str] = []
        for _, sent in sentences_with_score:
            if sent not in selected_sentences:
                selected_sentences.append(sent)
            if len(selected_sentences) >= 4:
                break

        return " ".join(selected_sentences)

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

    def _build_key_points(
        self,
        node: dict[str, Any],
        page_texts: list[str],
        matched_pages: list[int],
    ) -> list[str]:
        explanation_raw = str(node.get("explanation_raw", "")).strip()
        if not explanation_raw:
            return []

        candidate_sentences = self._split_sentences(explanation_raw)

        key_points: list[str] = []
        for sent in candidate_sentences:
            sent = sent.strip()
            if len(sent) < 10:
                continue
            if sent not in key_points:
                key_points.append(sent)
            if len(key_points) >= 4:
                break

        return key_points

    def _build_summary_from_explanation(self, explanation_raw: str) -> str:
        if not explanation_raw.strip():
            return ""

        sentences = self._split_sentences(explanation_raw)
        if not sentences:
            return ""

        return sentences[0][:120]

    @staticmethod
    def _shrink_to_dense_window(pages: list[int], window_size: int = 12, keep_top: int = 6) -> list[int]:
        if not pages:
            return []

        pages = sorted(set(pages))
        best_window: list[int] = []
        best_count = 0

        for i in range(len(pages)):
            start = pages[i]
            current_window = [p for p in pages if start <= p <= start + window_size]

            if len(current_window) > best_count:
                best_count = len(current_window)
                best_window = current_window

        return best_window[:keep_top]

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        parts = re.split(r"(?<=[。！？.!?])\s+", text)
        return [p.strip() for p in parts if p.strip()]

    @staticmethod
    def _normalize_text(text: str) -> str:
        text = text.replace("\u3000", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()
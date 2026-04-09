from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    import fitz  # PyMuPDF
except Exception:  # pragma: no cover
    fitz = None


class NodeRetrievalBuilder:
    """
    第一版节点定向检索器（弱 RAG 检索层）：
    1. 在 refined pages 中切句
    2. 按不同目标构建候选：
       - definition_candidates
       - key_point_candidates
       - formula_candidates
       - example_candidates
    """

    def __init__(self, textbook_pdf_path: str | Path | None = None) -> None:
        self.textbook_pdf_path = Path(textbook_pdf_path) if textbook_pdf_path else None

    def enrich_nodes(self, nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not self.textbook_pdf_path or not self.textbook_pdf_path.exists():
            for node in nodes:
                node.setdefault("extra", {})
                node["extra"]["retrieval_status"] = "textbook_pdf_missing"
            return nodes

        if fitz is None:
            for node in nodes:
                node.setdefault("extra", {})
                node["extra"]["retrieval_status"] = "pymupdf_not_installed"
            return nodes

        page_texts = self._read_pdf_pages(self.textbook_pdf_path)

        for node in nodes:
            extra = node.get("extra", {}) or {}
            refined_pages = extra.get("page_refs_refined", []) or node.get("page_refs", []) or []

            candidate_sentences = self._collect_candidate_sentences(node, page_texts, refined_pages)

            node["definition_candidates"] = self._select_definition_candidates(node, candidate_sentences)
            node["key_point_candidates"] = self._select_key_point_candidates(node, candidate_sentences)
            node["formula_candidates"] = self._select_formula_candidates(node, candidate_sentences)
            node["example_candidates"] = self._select_example_candidates(node, candidate_sentences)

            node.setdefault("extra", {})
            node["extra"]["retrieval_status"] = "ok"
            node["extra"]["retrieval_candidate_sentence_count"] = len(candidate_sentences)

        return nodes

    def _read_pdf_pages(self, pdf_path: Path) -> list[str]:
        page_texts: list[str] = []

        with fitz.open(pdf_path) as doc:
            for i in range(len(doc)):
                text = doc[i].get_text("text") or ""
                text = self._normalize_text(text)
                page_texts.append(text)

        return page_texts

    def _collect_candidate_sentences(
        self,
        node: dict[str, Any],
        page_texts: list[str],
        refined_pages: list[int],
    ) -> list[str]:
        if not refined_pages:
            return []

        node_name = str(node.get("name", "")).strip()
        tags = node.get("tags", []) or []
        extra = node.get("extra", {}) or {}
        retrieval_keywords = extra.get("retrieval_keywords", []) or []

        candidates: list[tuple[int, str]] = []

        for page_num in refined_pages:
            if page_num < 1 or page_num > len(page_texts):
                continue

            text = page_texts[page_num - 1]
            sentences = self._split_sentences(text)

            for sent in sentences:
                cleaned = self._clean_sentence(sent)
                if len(cleaned) < 8:
                    continue

                score = 0

                if node_name and node_name in cleaned:
                    score += 4

                for kw in retrieval_keywords:
                    kw = str(kw).strip()
                    if len(kw) >= 2 and kw in cleaned:
                        score += 3

                for tag in tags:
                    tag = str(tag).strip()
                    if len(tag) >= 2 and tag in cleaned:
                        score += 1

                if score > 0:
                    candidates.append((score, cleaned))

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
            negative_markers=["例", "习题", "图", "表", "法则"],
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
        candidate_sentences: list[str],
    ) -> list[str]:
        formula_results: list[str] = []

        for sent in candidate_sentences:
            if self._looks_like_formula_sentence(sent):
                if sent not in formula_results:
                    formula_results.append(sent)
            if len(formula_results) >= 4:
                break

        return formula_results

    def _select_example_candidates(
        self,
        node: dict[str, Any],
        candidate_sentences: list[str],
    ) -> list[str]:
        example_markers = [
            "例如",
            "比如",
            "例",
            "实例",
            "系统",
            "图",
        ]

        return self._rank_and_select(
            candidate_sentences=candidate_sentences,
            positive_markers=example_markers,
            negative_markers=[],
            keep_top=4,
        )

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

    def _looks_like_formula_sentence(self, text: str) -> bool:
        if not text:
            return False

        formula_markers = [
            "=",
            "式",
            "方程",
            "传递函数",
            "微分方程",
            "状态方程",
            "拉氏变换",
            "拉普拉斯变换",
            "s 平面",
            "z 变换",
        ]

        if any(marker in text for marker in formula_markers):
            return True

        if re.search(r"[A-Za-z]\([A-Za-zszt]\)", text):
            return True

        if re.search(r"[A-Za-z]+\s*=\s*", text):
            return True

        return False

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        parts = re.split(r"(?<=[。！？.!?])\s+", text)
        return [p.strip() for p in parts if p.strip()]

    @staticmethod
    def _clean_sentence(text: str) -> str:
        text = text.strip()
        text = re.sub(r"·\d+·", " ", text)
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"^第[一二三四五六七八九十0-9]+章\s*", "", text)
        text = re.sub(r"^\d+\-\d+\s*", "", text)
        return text.strip()

    @staticmethod
    def _normalize_text(text: str) -> str:
        text = text.replace("\u3000", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()
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
    1. 从教材 PDF 中为节点补粗 page_refs
    2. 基于标题/关键词命中寻找 anchor_page
    3. 基于 anchor_page 生成更精细的 page_refs_refined
    4. 从 refined pages 中抽取 explanation_raw
    5. 生成 core_concepts / key_points 初版内容

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

            anchor_page = self._find_anchor_page(node, page_texts, matched_pages)
            node.setdefault("extra", {})
            node["extra"]["anchor_page"] = anchor_page

            refined_pages = self._build_refined_pages(node, matched_pages, anchor_page)
            node["extra"]["page_refs_refined"] = refined_pages

            explanation_raw = self._build_explanation_raw(node, page_texts, refined_pages)
            node["explanation_raw"] = explanation_raw

            core_concepts = self._build_core_concepts(node)
            node["core_concepts"] = core_concepts

            key_points = self._build_key_points(node, explanation_raw)
            node["key_points"] = key_points

            if not node.get("summary", "").strip():
                node["summary"] = self._build_summary_from_explanation(explanation_raw)

            node["extra"]["page_ref_status"] = "ok"
            node["extra"]["page_ref_count"] = len(matched_pages)
            node["extra"]["page_refined_count"] = len(refined_pages)

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

    def _find_anchor_page(
        self,
        node: dict[str, Any],
        page_texts: list[str],
        matched_pages: list[int],
    ) -> int | None:
        if not matched_pages:
            return None

        node_name = str(node.get("name", "")).strip()
        tags = node.get("tags", []) or []
        extra = node.get("extra", {}) or {}
        retrieval_keywords = extra.get("retrieval_keywords", []) or []
        chapter = str(node.get("chapter", "")).strip()
        level = int(node.get("level", 1))

        chapter_page_range = extra.get("chapter_page_range", [])
        chapter_start = None
        chapter_end = None
        if isinstance(chapter_page_range, list) and len(chapter_page_range) == 2:
            chapter_start, chapter_end = chapter_page_range

        # 关键修正 1：
        # 一级节点优先锚到本章起始页附近，而不是正文中关键词最密集页
        if level == 1 and chapter_start is not None:
            chapter_head_candidates = [
                p for p in matched_pages
                if chapter_start <= p <= min(chapter_start + 6, chapter_end or chapter_start + 6)
            ]
            if chapter_head_candidates:
                return chapter_head_candidates[0]
            return chapter_start

        # 二级节点仍然走标题/关键词页定位
        best_page = None
        best_score = -1

        for page_num in matched_pages:
            if page_num < 1 or page_num > len(page_texts):
                continue

            page_text = page_texts[page_num - 1]
            head_text = page_text[:220]
            score = 0

            if node_name and node_name in page_text:
                score += 8

            if node_name and node_name in head_text:
                score += 8

            if chapter and chapter in head_text:
                score += 2

            for kw in retrieval_keywords:
                kw = str(kw).strip()
                if len(kw) >= 2 and kw in page_text:
                    score += 3
                if len(kw) >= 2 and kw in head_text:
                    score += 3

            for tag in tags:
                tag = str(tag).strip()
                if len(tag) >= 2 and tag in page_text:
                    score += 1

            # 关键修正 2：
            # 强化“小节标题感”判定
            title_like_patterns = [
                rf"\d+\-\d+\s*.*{re.escape(node_name)}",
                rf"\d+\.\d+\s*.*{re.escape(node_name)}",
                rf"{re.escape(node_name)}",
            ]
            for pattern in title_like_patterns:
                if re.search(pattern, head_text):
                    score += 6
                    break

            if score > best_score:
                best_score = score
                best_page = page_num

        return best_page

    def _build_refined_pages(
        self,
        node: dict[str, Any],
        matched_pages: list[int],
        anchor_page: int | None,
    ) -> list[int]:
        if anchor_page is None:
            return matched_pages[:4]

        level = int(node.get("level", 1))
        extra = node.get("extra", {}) or {}
        chapter_page_range = extra.get("chapter_page_range", [])
        chapter_start = None
        chapter_end = None
        if isinstance(chapter_page_range, list) and len(chapter_page_range) == 2:
            chapter_start, chapter_end = chapter_page_range

        # 关键修正 3：
        # 一级节点直接看“章节开头总述”
        if level == 1:
            start = anchor_page
            end = anchor_page + 3
            if chapter_end is not None:
                end = min(end, chapter_end)
            return list(range(start, end + 1))

        # 二级节点围绕锚点页收缩
        radius_left = 1
        radius_right = 2

        refined = [
            p for p in matched_pages
            if (anchor_page - radius_left) <= p <= (anchor_page + radius_right)
        ]

        if refined:
            return refined

        start = max(1, anchor_page - radius_left)
        end = anchor_page + radius_right

        if chapter_start is not None:
            start = max(start, chapter_start)
        if chapter_end is not None:
            end = min(end, chapter_end)

        return list(range(start, end + 1))

    def _build_explanation_raw(
        self,
        node: dict[str, Any],
        page_texts: list[str],
        refined_pages: list[int],
    ) -> str:
        if not refined_pages:
            return ""

        node_name = str(node.get("name", "")).strip()
        tags = node.get("tags", []) or []
        extra = node.get("extra", {}) or {}
        retrieval_keywords = extra.get("retrieval_keywords", []) or []
        level = int(node.get("level", 1))

        sentences_with_score: list[tuple[int, str]] = []

        for page_num in refined_pages:
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

                cleaned = self._clean_sentence(sent)
                if len(cleaned) < 12:
                    continue

                # 一级节点更偏总述句，不要过度偏公式/法则/分离点这类细节
                if level == 1:
                    if any(bad in cleaned for bad in ["法则", "渐近线", "分离点", "实轴上的根轨迹", "式("]):
                        score -= 2
                    if any(good in cleaned for good in ["基本概念", "方法", "分析", "设计", "根轨迹法是", "本章"]):
                        score += 2

                if score > 0:
                    sentences_with_score.append((score, cleaned))

        if not sentences_with_score:
            return ""

        sentences_with_score.sort(key=lambda x: (-x[0], len(x[1])))

        selected_sentences: list[str] = []
        for _, sent in sentences_with_score:
            if sent and sent not in selected_sentences:
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

    def _build_key_points(self, node: dict[str, Any], explanation_raw: str) -> list[str]:
        if not explanation_raw.strip():
            return []

        candidate_sentences = self._split_sentences(explanation_raw)

        key_points: list[str] = []
        for sent in candidate_sentences:
            sent = self._clean_sentence(sent)
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
        cleaned_sentences = [self._clean_sentence(s) for s in sentences if self._clean_sentence(s)]
        if not cleaned_sentences:
            return ""

        return cleaned_sentences[0][:120]

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
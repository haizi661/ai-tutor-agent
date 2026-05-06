from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional


class NodeRetrievalBuilder:
    """
    基于现有 MinerU 缓存结果做节点候选抽取。

    V2 改动目标：
    - 不改字段，只提高 definition/key_point/formula/example 四类候选内容质量。
    - 不再只在 best_block 内抽取候选，而是使用 best_block + 相邻块 + 同章节高相关块。
    - 当精确候选为空时，自动放宽到同章节关键词候选，避免节点候选池全空。
    - 兼容 data/mineru_cache 与 data/minerU_cache 两种目录名。
    """

    def __init__(
        self,
        textbook_pdf_path: str | Path | None = None,
        mineru_cache_root: str | Path = "data/mineru_cache",
    ) -> None:
        self.textbook_pdf_path = Path(textbook_pdf_path) if textbook_pdf_path else None
        self.mineru_cache_root = self._resolve_cache_root(Path(mineru_cache_root))

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
            matched_doc = self._find_matching_chapter_doc(
                chapter_docs=chapter_docs,
                start_page=int(chapter_start),
                end_page=int(chapter_end),
            )

            if matched_doc is None:
                node["extra"]["retrieval_status"] = "mineru_doc_not_found"
                continue

            md_content = matched_doc["full_md"]
            chapter_blocks = self._split_md_into_blocks(md_content)
            scored_blocks = self._score_blocks_for_node(node, chapter_blocks)
            best_block = scored_blocks[0] if scored_blocks else None
            evidence_blocks = self._select_evidence_blocks(
                node=node,
                blocks=chapter_blocks,
                scored_blocks=scored_blocks,
            )
            evidence_text = "\n\n".join(str(block.get("content", "")) for block in evidence_blocks)
            if not evidence_text.strip():
                evidence_text = md_content

            text_lines = self._collect_text_lines(evidence_text)
            all_chapter_text_lines = self._collect_text_lines(md_content)
            formula_lines = self._collect_formula_lines(evidence_text)
            all_formula_lines = self._collect_formula_lines(md_content)
            figure_lines = self._collect_figure_related_lines(evidence_text)

            candidate_sentences = self._collect_candidate_sentences(node, text_lines, strict=True)
            if len(candidate_sentences) < 4:
                fallback = self._collect_candidate_sentences(node, all_chapter_text_lines, strict=False)
                candidate_sentences = self._merge_unique(candidate_sentences, fallback, max_items=24)

            definition_candidates = self._select_definition_candidates(candidate_sentences)
            key_point_candidates = self._select_key_point_candidates(candidate_sentences)
            formula_candidates = self._select_formula_candidates(
                node=node,
                formula_lines=formula_lines,
                candidate_sentences=candidate_sentences,
            )
            if len(formula_candidates) < 2:
                formula_candidates = self._merge_unique(
                    formula_candidates,
                    self._select_formula_candidates(
                        node=node,
                        formula_lines=all_formula_lines,
                        candidate_sentences=candidate_sentences,
                    ),
                    max_items=4,
                )
            example_candidates = self._select_example_candidates(candidate_sentences, figure_lines)
            figure_refs = self._select_figure_refs(figure_lines)

            # 最后兜底：如果某类为空，不留空字段，改用高质量通用候选补齐。
            if not definition_candidates:
                definition_candidates = candidate_sentences[:3]
            if not key_point_candidates:
                key_point_candidates = candidate_sentences[:5]
            if not example_candidates:
                example_candidates = self._select_example_candidates(candidate_sentences, [])
                if not example_candidates:
                    example_candidates = [s for s in candidate_sentences if any(k in s for k in ["例如", "比如", "图", "系统", "应用"])][:3]

            node["definition_candidates"] = definition_candidates[:4]
            node["key_point_candidates"] = key_point_candidates[:6]
            node["formula_candidates"] = formula_candidates[:4]
            node["example_candidates"] = example_candidates[:4]
            node["figures_refs"] = figure_refs[:6]

            node["extra"]["retrieval_status"] = "ok"
            node["extra"]["retrieval_candidate_sentence_count"] = len(candidate_sentences)
            node["extra"]["retrieval_formula_line_count"] = len(formula_lines)
            node["extra"]["retrieval_figure_line_count"] = len(figure_lines)
            node["extra"]["retrieval_source_pdf"] = matched_doc["pdf_name"]
            node["extra"]["retrieval_matched_block_title"] = best_block["title"] if best_block else ""
            node["extra"]["retrieval_matched_block_score"] = best_block["score"] if best_block else 0
            node["extra"]["retrieval_evidence_block_count"] = len(evidence_blocks)
            node["extra"]["retrieval_evidence_block_titles"] = [
                str(block.get("title", "")) for block in evidence_blocks[:6]
            ]

        return nodes

    def _resolve_cache_root(self, root: Path) -> Path:
        if root.exists():
            return root
        candidates = [
            root.parent / "minerU_cache",
            root.parent / "mineru_cache",
            Path("data/minerU_cache"),
            Path("data/mineru_cache"),
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return root

    def _load_mineru_chapter_docs(self) -> list[dict[str, Any]]:
        docs: list[dict[str, Any]] = []
        if not self.mineru_cache_root.exists():
            return docs

        for item in self.mineru_cache_root.iterdir():
            if not item.is_dir():
                continue
            manifest_path = item / "manifest.json"
            full_md_path = item / "full.md"
            if not full_md_path.exists():
                continue
            try:
                manifest: dict[str, Any] = {}
                if manifest_path.exists():
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        manifest = json.load(f)
                with open(full_md_path, "r", encoding="utf-8") as f:
                    full_md = f.read()
                pdf_name = str(manifest.get("pdf_name", "")).strip() or item.name
                page_range = self._extract_page_range_from_pdf_name(pdf_name)
                if page_range is None:
                    page_range = self._extract_page_range_from_pdf_name(item.name)
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
            m = re.search(r"_p(\d+)-(\d+)(?:\.pdf|__|$)", pdf_name, flags=re.I)
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

    def _split_md_into_blocks(self, full_md: str) -> list[dict[str, Any]]:
        lines = full_md.splitlines()
        blocks: list[dict[str, Any]] = []
        current_title = "ROOT"
        current_level = 0
        current_lines: list[str] = []
        order = 0

        def flush_block() -> None:
            nonlocal current_title, current_level, current_lines, order
            content = "\n".join(current_lines).strip()
            if content:
                blocks.append(
                    {
                        "title": current_title,
                        "level": current_level,
                        "content": content,
                        "order": order,
                    }
                )
                order += 1
            current_lines = []

        for raw in lines:
            line = (raw or "").rstrip()
            stripped = line.strip()
            m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
            if m:
                flush_block()
                current_level = len(m.group(1))
                current_title = m.group(2).strip()
                continue
            current_lines.append(line)
        flush_block()
        return blocks

    def _score_blocks_for_node(
        self,
        node: dict[str, Any],
        blocks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        node_name = str(node.get("name", "")).strip()
        tags = [str(x).strip() for x in (node.get("tags", []) or []) if str(x).strip()]
        extra = node.get("extra", {}) or {}
        retrieval_keywords = [str(x).strip() for x in (extra.get("retrieval_keywords", []) or []) if str(x).strip()]
        terms = self._build_query_terms(node_name, tags, retrieval_keywords)
        node_role = str(extra.get("node_role", "")).strip()
        legacy_level = int(extra.get("legacy_level", 1) or 1)

        scored: list[dict[str, Any]] = []
        for block in blocks:
            title = str(block.get("title", "")).strip()
            content = str(block.get("content", "")).strip()
            head_text = content[:2000]
            score = 0

            if node_name and node_name in title:
                score += 30
            if node_name and node_name in head_text:
                score += 10
            tail_name = self._extract_tail_name(node_name)
            if tail_name and tail_name in title:
                score += 14
            elif tail_name and tail_name in head_text:
                score += 5
            for term in terms:
                if len(term) < 2:
                    continue
                if term in title:
                    score += 5
                if term in head_text:
                    score += 2
            block_level = int(block.get("level", 0) or 0)
            if node_role == "topic" or legacy_level >= 2:
                if block_level >= 1:
                    score += 2
            else:
                if block_level in {1, 2}:
                    score += 2
            if title in {"习 题", "习题", "本章导学"}:
                score -= 8
            if "习 题" in title or "习题" in title:
                score -= 6
            if score > 0:
                new_block = dict(block)
                new_block["score"] = score
                scored.append(new_block)
        scored.sort(key=lambda x: (-int(x.get("score", 0)), int(x.get("order", 0))))
        return scored

    def _select_evidence_blocks(
        self,
        node: dict[str, Any],
        blocks: list[dict[str, Any]],
        scored_blocks: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not blocks:
            return []
        if not scored_blocks:
            return blocks[:3]
        by_order = {int(block.get("order", 0)): block for block in blocks}
        selected: list[dict[str, Any]] = []
        selected_orders: set[int] = set()

        def add_block(block: dict[str, Any] | None) -> None:
            if not block:
                return
            order = int(block.get("order", 0))
            if order in selected_orders:
                return
            content = str(block.get("content", "")).strip()
            if not content:
                return
            selected.append(block)
            selected_orders.add(order)

        best = scored_blocks[0]
        best_order = int(best.get("order", 0))
        add_block(best)
        add_block(by_order.get(best_order - 1))
        add_block(by_order.get(best_order + 1))
        for block in scored_blocks[1:8]:
            add_block(block)
            if len(selected) >= 7:
                break
        selected.sort(key=lambda x: int(x.get("order", 0)))
        return selected[:7]

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
            if re.match(r"^#{1,6}\s+", line):
                line = re.sub(r"^#{1,6}\s+", "", line)
            line = re.sub(r"!\[.*?\]\(.*?\)", "", line)
            line = re.sub(r"<[^>]+>", " ", line)
            line = self._normalize_ocr_symbols(line)
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
                    joined = self._normalize_formula_text(" ".join(formula_parts))
                    if self._is_formula_like_candidate(joined):
                        results.append(joined)
                i += 1
                continue
            if stripped.startswith("$$"):
                formula_parts: list[str] = []
                after = stripped[2:]
                if after.endswith("$$") and len(after) > 2:
                    formula_parts.append(after[:-2].strip())
                    joined = self._normalize_formula_text(" ".join(formula_parts))
                    if self._is_formula_like_candidate(joined):
                        results.append(joined)
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
                    joined = self._normalize_formula_text(" ".join(formula_parts))
                    if self._is_formula_like_candidate(joined):
                        results.append(joined)
                i += 1
                continue
            normalized = self._normalize_formula_text(stripped)
            if self._is_formula_like_candidate(normalized):
                results.append(normalized)
            i += 1
        return self._merge_unique([], results, max_items=80)

    def _collect_figure_related_lines(self, md_content: str) -> list[str]:
        lines = md_content.splitlines()
        results: list[str] = []
        for idx, raw in enumerate(lines):
            line = (raw or "").strip()
            if not line:
                continue
            if self._is_figure_caption_line(line):
                prev_text = " ".join(lines[max(0, idx - 2):idx])
                next_text = " ".join(lines[idx + 1:min(len(lines), idx + 3)])
                combined = f"{prev_text} {line} {next_text}"
                combined = re.sub(r"!\[.*?\]\(.*?\)", "", combined)
                combined = self._normalize_ocr_symbols(combined)
                combined = re.sub(r"\s+", " ", combined).strip()
                if combined:
                    results.append(combined)
        return self._merge_unique([], results, max_items=20)

    def _collect_candidate_sentences(
        self,
        node: dict[str, Any],
        text_lines: list[str],
        strict: bool = True,
    ) -> list[str]:
        node_name = str(node.get("name", "")).strip()
        tags = [str(x).strip() for x in (node.get("tags", []) or []) if str(x).strip()]
        extra = node.get("extra", {}) or {}
        retrieval_keywords = [str(x).strip() for x in (extra.get("retrieval_keywords", []) or []) if str(x).strip()]
        terms = self._build_query_terms(node_name, tags, retrieval_keywords)
        candidates: list[tuple[int, int, str]] = []

        for order, line in enumerate(text_lines):
            score = self._score_text_for_node(line, node_name, terms)
            if not strict and any(marker in line for marker in ["是", "指", "称为", "主要", "通常", "例如", "系统", "控制"]):
                score += 1
            threshold = 1 if not strict else 2
            if score >= threshold:
                candidates.append((score, order, line))

        candidates.sort(key=lambda x: (-x[0], x[1]))
        return self._merge_unique([], [line for _, _, line in candidates], max_items=30)

    def _select_definition_candidates(self, candidate_sentences: list[str]) -> list[str]:
        definition_markers = ["是指", "是", "称为", "定义", "就是", "表示", "可以理解为"]
        return self._rank_and_select(
            candidate_sentences=candidate_sentences,
            positive_markers=definition_markers,
            negative_markers=["例如", "比如", "图", "表", "习题"],
            keep_top=4,
        )

    def _select_key_point_candidates(self, candidate_sentences: list[str]) -> list[str]:
        keypoint_markers = [
            "主要", "一般", "通常", "特点", "关系", "条件", "分析", "设计", "应用", "性能", "要求",
            "可见", "因此", "必须", "能够", "需要", "任务", "作用", "过程",
        ]
        return self._rank_and_select(
            candidate_sentences=candidate_sentences,
            positive_markers=keypoint_markers,
            negative_markers=["习题", "试说明"],
            keep_top=6,
        )

    def _select_formula_candidates(
        self,
        node: dict[str, Any],
        formula_lines: list[str],
        candidate_sentences: list[str],
    ) -> list[str]:
        node_name = str(node.get("name", "")).strip()
        tags = [str(x).strip() for x in (node.get("tags", []) or []) if str(x).strip()]
        extra = node.get("extra", {}) or {}
        retrieval_keywords = [str(x).strip() for x in (extra.get("retrieval_keywords", []) or []) if str(x).strip()]
        terms = self._build_query_terms(node_name, tags, retrieval_keywords)
        results_with_score: list[tuple[int, str]] = []

        for line in formula_lines:
            score = self._score_formula_candidate(line, node_name, terms)
            if score > 0:
                results_with_score.append((score, line))

        for sent in candidate_sentences:
            normalized = self._normalize_formula_text(sent)
            if not self._is_formula_like_candidate(normalized):
                continue
            score = self._score_formula_candidate(normalized, node_name, terms)
            if score > 0:
                results_with_score.append((score, normalized))

        results_with_score.sort(key=lambda x: (-x[0], len(x[1])))
        return self._merge_unique([], [text for _, text in results_with_score], max_items=4)

    def _score_formula_candidate(self, text: str, node_name: str, terms: list[str]) -> int:
        score = 0
        text = self._normalize_formula_text(text)
        if not text:
            return 0
        negative_markers = [
            "例如", "比如", "一般来说", "通常", "可以看出", "说明", "主要有以下", "其特点是",
            "系统由", "系统可以", "同学们", "习题", "试说明",
        ]
        for marker in negative_markers:
            if marker in text:
                score -= 3
        if "=" in text:
            score += 3
        if re.search(r"[A-Za-z]+\([sztjw]\)", text):
            score += 4
        if re.search(r"[CRGHXYW]\([sztjw]\)", text):
            score += 5
        if re.search(r"\b\d+(\.\d+)?\b", text):
            score += 1
        if re.search(r"[+\-*/^]", text):
            score += 2
        if re.search(r"frac|\\frac|\\dfrac|∑|Σ|∫|lim", text):
            score += 4
        if any(k in text for k in ["传递函数", "微分方程", "状态方程", "特征方程", "拉普拉斯变换", "Z变换", "z变换"]):
            score += 3
        if len(text) > 180:
            score -= 2
        if len(text) > 300:
            score -= 3
        if "。" in text and len(text) > 120:
            score -= 2
        if node_name and node_name in text:
            score += 2
        for term in terms:
            if len(term) >= 2 and term in text:
                score += 1
        return score

    def _select_figure_refs(self, figure_lines: list[str]) -> list[str]:
        """
        将图相关证据写入 figures_refs 字段。
        不改字段结构，只放入可读的图注/图片引用文本。
        """
        results: list[str] = []

        for line in figure_lines:
            text = self._normalize_ocr_symbols(str(line)).strip()
            text = re.sub(r"\s+", " ", text)

            if not text:
                continue

            # 优先截取从“图 x-x / Figure x”开始的主体，避免把前后正文塞太长。
            m = re.search(r"((?:图|Figure|Fig\.?)\s*\d+(?:[-－]\d+)?[^。；;\\n]{0,120})", text, flags=re.I)
            if m:
                text = m.group(1).strip()

            text = self._clean_sentence(text)
            if len(text) < 4:
                continue

            if text not in results:
                results.append(text)

            if len(results) >= 8:
                break

        return results

    def _select_example_candidates(self, candidate_sentences: list[str], figure_lines: list[str]) -> list[str]:
        example_markers = ["例如", "比如", "实例", "示例", "应用", "图", "系统", "工程", "工业", "控制过程"]
        results = self._rank_and_select(
            candidate_sentences=candidate_sentences,
            positive_markers=example_markers,
            negative_markers=["习题", "试说明"],
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
        scored: list[tuple[int, int, str]] = []
        for order, sent in enumerate(candidate_sentences):
            score = 0
            for marker in positive_markers:
                if marker in sent:
                    score += 2
            for marker in negative_markers:
                if marker in sent:
                    score -= 2
            if len(sent) > 500:
                score -= 1
            if score > 0:
                scored.append((score, order, sent))
        scored.sort(key=lambda x: (-x[0], x[1]))
        return self._merge_unique([], [sent for _, _, sent in scored], max_items=keep_top)

    def _is_figure_caption_line(self, text: str) -> bool:
        if not text:
            return False
        return bool(re.match(r"^\s*(Figure|Fig\.?|图)\s*\d+", text, flags=re.I))

    def _looks_like_formula_text(self, text: str) -> bool:
        if not text:
            return False
        if re.search(r"[CRGHXYW]\([sztjw]\)", text):
            return True
        if re.search(r"[A-Za-z]+\([sztjw]\)", text):
            return True
        if re.search(r"[A-Za-z]+\s*=\s*", text):
            return True
        if re.search(r"\$.*?\$", text):
            return True
        if any(marker in text for marker in ["=", "传递函数", "微分方程", "状态方程", "特征方程", "拉氏变换", "拉普拉斯变换", "z变换", "Z变换"]):
            return True
        return False

    def _is_formula_like_candidate(self, text: str) -> bool:
        if not text:
            return False
        text = self._normalize_formula_text(text)
        strong_patterns = [
            r"[CRGHXYW]\([sztjw]\)",
            r"[A-Za-z]+\([sztjw]\)\s*=\s*",
            r"[A-Za-z]+\s*=\s*[^。]+",
            r"\\frac|frac|∑|Σ|∫|lim",
        ]
        if any(re.search(p, text) for p in strong_patterns):
            return True
        strong_keywords = ["传递函数", "微分方程", "状态方程", "特征方程", "闭环传递函数", "开环传递函数"]
        if any(k in text for k in strong_keywords) and "=" in text:
            return True
        if len(text) > 140 and not re.search(r"[A-Za-z]+\([sztjw]\)|=", text):
            return False
        return False

    def _normalize_formula_text(self, text: str) -> str:
        text = text.replace("\n", " ").strip()
        text = self._normalize_ocr_symbols(text)
        text = re.sub(r"\s+", " ", text)
        return text[:700]

    def _build_query_terms(self, node_name: str, tags: list[str], retrieval_keywords: list[str]) -> list[str]:
        terms: list[str] = []
        for item in [node_name, self._extract_tail_name(node_name)] + retrieval_keywords + tags:
            item = str(item).strip()
            if len(item) >= 2 and item not in terms:
                terms.append(item)
        expansions = {
            "自动控制的基本原理与方式": ["反馈控制原理", "自动控制系统基本控制方式", "反馈控制方式", "开环控制方式", "复合控制方式", "按偏差控制", "按扰动控制"],
            "自动控制系统示例": ["函数记录仪", "自动驾驶仪", "锅炉液位", "转速控制", "磁盘驱动", "电阻炉"],
            "自动控制系统的分类": ["按系统特性分类", "按输入量变化规律分类", "线性连续", "线性离散", "非线性控制系统", "恒值控制系统", "随动系统", "程序控制系统"],
            "对自动控制系统的基本要求": ["稳定性", "快速性", "准确性", "稳态误差", "过渡过程", "典型外作用"],
            "自动控制系统的分析与设计工具": ["MATLAB", "Python", "控制系统工具箱", "Python-control", "仿真"],
        }
        for key, values in expansions.items():
            if key == node_name or key in node_name:
                for value in values:
                    if value not in terms:
                        terms.append(value)
        return terms

    def _score_text_for_node(self, text: str, node_name: str, terms: list[str]) -> int:
        score = 0
        if node_name and node_name in text:
            score += 8
        tail_name = self._extract_tail_name(node_name)
        if tail_name and tail_name in text:
            score += 4
        for term in terms:
            if len(term) >= 2 and term in text:
                score += 2
        if len(text) > 700:
            score -= 1
        if "习题" in text or "试说明" in text:
            score -= 5
        return score

    def _merge_unique(self, base: list[str], extra: list[str], max_items: int) -> list[str]:
        results: list[str] = []
        for text in list(base) + list(extra):
            cleaned = self._clean_sentence(str(text))
            if not cleaned:
                continue
            if cleaned in results:
                continue
            if any(self._is_near_duplicate(cleaned, old) for old in results):
                continue
            results.append(cleaned)
            if len(results) >= max_items:
                break
        return results

    def _is_near_duplicate(self, a: str, b: str) -> bool:
        if not a or not b:
            return False
        short, long = (a, b) if len(a) <= len(b) else (b, a)
        if len(short) >= 30 and short in long:
            return True
        a_set = set(a[:120])
        b_set = set(b[:120])
        if not a_set or not b_set:
            return False
        return len(a_set & b_set) / max(1, len(a_set | b_set)) > 0.88

    def _extract_tail_name(self, node_name: str) -> str:
        if "的" in node_name:
            tail = node_name.split("的")[-1].strip()
            if len(tail) >= 2:
                return tail
        return ""

    def _normalize_ocr_symbols(self, text: str) -> str:
        replacements = {
            "": "+", "": "-", "": "=", "": "π", "": "Σ", "": "Π",
            "": "±", "": "∠", "": "θ", "": "ω", "": "μ",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text

    @staticmethod
    def _clean_sentence(text: str) -> str:
        text = text.strip()
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"^#+\s*", "", text)
        return text.strip()

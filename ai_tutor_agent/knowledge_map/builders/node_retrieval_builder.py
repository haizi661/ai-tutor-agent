from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional


class NodeRetrievalBuilder:
    """
    基于现有 MinerU 缓存结果做节点候选抽取：
    1. 读取章节 full.md
    2. 先按标题切成小节块
    3. 节点优先在自己最匹配的小节块内抽取 candidates
    4. 重点收紧公式候选，减少自然语言解释句污染
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
            matched_doc = self._find_matching_chapter_doc(
                chapter_docs=chapter_docs,
                start_page=chapter_start,
                end_page=chapter_end,
            )

            if matched_doc is None:
                node["extra"]["retrieval_status"] = "mineru_doc_not_found"
                continue

            md_content = matched_doc["full_md"]
            chapter_blocks = self._split_md_into_blocks(md_content)
            best_block = self._find_best_block_for_node(node, chapter_blocks)

            block_text = best_block["content"] if best_block else md_content

            text_lines = self._collect_text_lines(block_text)
            formula_lines = self._collect_formula_lines(block_text)
            figure_lines = self._collect_figure_related_lines(block_text)

            candidate_sentences = self._collect_candidate_sentences(node, text_lines)

            node["definition_candidates"] = self._select_definition_candidates(candidate_sentences)
            node["key_point_candidates"] = self._select_key_point_candidates(candidate_sentences)
            node["formula_candidates"] = self._select_formula_candidates(
                node=node,
                formula_lines=formula_lines,
                candidate_sentences=candidate_sentences,
            )
            node["example_candidates"] = self._select_example_candidates(candidate_sentences, figure_lines)

            node["extra"]["retrieval_status"] = "ok"
            node["extra"]["retrieval_candidate_sentence_count"] = len(candidate_sentences)
            node["extra"]["retrieval_formula_line_count"] = len(formula_lines)
            node["extra"]["retrieval_figure_line_count"] = len(figure_lines)
            node["extra"]["retrieval_source_pdf"] = matched_doc["pdf_name"]
            node["extra"]["retrieval_matched_block_title"] = best_block["title"] if best_block else ""
            node["extra"]["retrieval_matched_block_score"] = best_block["score"] if best_block else 0

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

    def _split_md_into_blocks(self, full_md: str) -> list[dict[str, Any]]:
        lines = full_md.splitlines()
        blocks: list[dict[str, Any]] = []

        current_title = "ROOT"
        current_level = 0
        current_lines: list[str] = []

        def flush_block() -> None:
            nonlocal current_title, current_level, current_lines
            content = "\n".join(current_lines).strip()
            if content:
                blocks.append(
                    {
                        "title": current_title,
                        "level": current_level,
                        "content": content,
                    }
                )
            current_lines = []

        for raw in lines:
            line = (raw or "").rstrip()
            stripped = line.strip()

            if not stripped:
                current_lines.append("")
                continue

            m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
            if m:
                flush_block()
                current_level = len(m.group(1))
                current_title = m.group(2).strip()
                continue

            current_lines.append(line)

        flush_block()
        return blocks

    def _find_best_block_for_node(
        self,
        node: dict[str, Any],
        blocks: list[dict[str, Any]],
    ) -> Optional[dict[str, Any]]:
        if not blocks:
            return None

        node_name = str(node.get("name", "")).strip()
        tags = node.get("tags", []) or []
        extra = node.get("extra", {}) or {}
        retrieval_keywords = extra.get("retrieval_keywords", []) or []
        level = int(node.get("level", 1))

        best_block: Optional[dict[str, Any]] = None
        best_score = -1

        for block in blocks:
            title = str(block.get("title", "")).strip()
            content = str(block.get("content", "")).strip()
            head_text = content[:1200]

            score = 0

            if node_name and node_name in title:
                score += 20

            if node_name and node_name in head_text:
                score += 6

            tail_name = self._extract_tail_name(node_name)
            if tail_name and tail_name in title:
                score += 12

            for kw in retrieval_keywords:
                kw = str(kw).strip()
                if len(kw) >= 2 and kw in title:
                    score += 4
                if len(kw) >= 2 and kw in head_text:
                    score += 2

            for tag in tags:
                tag = str(tag).strip()
                if len(tag) >= 2 and tag in title:
                    score += 2
                if len(tag) >= 2 and tag in head_text:
                    score += 1

            if level == 2 and block.get("level", 0) >= 2:
                score += 2

            if level == 1 and block.get("level", 0) == 1:
                score += 2

            if score > best_score:
                best_score = score
                best_block = dict(block)
                best_block["score"] = score

        return best_block

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

            # ```math ... ```
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

            # $$ ... $$
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

            # 单行公式风格
            normalized = self._normalize_formula_text(stripped)
            if self._is_formula_like_candidate(normalized):
                results.append(normalized)

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
                prev_text = " ".join(lines[max(0, idx - 2):idx])
                next_text = " ".join(lines[idx + 1:min(len(lines), idx + 3)])
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

            tail_name = self._extract_tail_name(node_name)
            if tail_name and tail_name in line:
                score += 3

            for kw in retrieval_keywords:
                kw = str(kw).strip()
                if len(kw) >= 2 and kw in line:
                    score += 2

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

    def _select_definition_candidates(self, candidate_sentences: list[str]) -> list[str]:
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

    def _select_key_point_candidates(self, candidate_sentences: list[str]) -> list[str]:
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
        results_with_score: list[tuple[int, str]] = []

        # 1. 优先吃真正的公式行
        for line in formula_lines:
            score = self._score_formula_candidate(
                text=line,
                node_name=node_name,
                tags=tags,
            )
            if score > 0:
                results_with_score.append((score, line))

        # 2. 再从普通句子里捞“像公式”的短句
        for sent in candidate_sentences:
            normalized = self._normalize_formula_text(sent)
            if not self._is_formula_like_candidate(normalized):
                continue

            score = self._score_formula_candidate(
                text=normalized,
                node_name=node_name,
                tags=tags,
            )
            if score > 0:
                results_with_score.append((score, normalized))

        results_with_score.sort(key=lambda x: (-x[0], len(x[1])))

        results: list[str] = []
        for _, text in results_with_score:
            if text not in results:
                results.append(text)
            if len(results) >= 4:
                break

        return results

    def _score_formula_candidate(
        self,
        text: str,
        node_name: str,
        tags: list[str],
    ) -> int:
        """
        分数越高越像真正公式候选。
        """
        score = 0
        text = self._normalize_formula_text(text)

        if not text:
            return 0

        # 明显是解释句，直接重罚
        negative_markers = [
            "例如",
            "比如",
            "一般来说",
            "通常",
            "可以看出",
            "说明",
            "表示为",
            "主要有以下",
            "其特点是",
            "系统由",
            "系统可以",
            "控制系统是",
            "自动控制系统",
            "反馈控制系统",
            "核心任务",
            "学习这部分内容",
            "同学们",
        ]
        for marker in negative_markers:
            if marker in text:
                score -= 4

        # 特征越“数学”，分越高
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

        if len(text) > 160:
            score -= 2
        if len(text) > 260:
            score -= 3

        if "。" in text:
            score -= 2

        if node_name and node_name in text:
            score += 2

        tail_name = self._extract_tail_name(node_name)
        if tail_name and tail_name in text:
            score += 1

        for tag in tags:
            tag = str(tag).strip()
            if len(tag) >= 2 and tag in text:
                score += 1

        return score

    def _select_example_candidates(
        self,
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
        """
        宽松判断：用于初筛。
        真正是否保留，还要交给 _score_formula_candidate。
        """
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

        if any(
            marker in text
            for marker in [
                "=",
                "传递函数",
                "微分方程",
                "状态方程",
                "特征方程",
                "拉氏变换",
                "拉普拉斯变换",
                "z变换",
                "Z变换",
            ]
        ):
            return True

        return False

    def _is_formula_like_candidate(self, text: str) -> bool:
        """
        严格判断：尽量排除纯解释句。
        """
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

        strong_keywords = [
            "传递函数",
            "微分方程",
            "状态方程",
            "特征方程",
            "闭环传递函数",
            "开环传递函数",
        ]
        if any(k in text for k in strong_keywords) and "=" in text:
            return True

        # 太长且没有明确公式结构，排除
        if len(text) > 140 and not re.search(r"[A-Za-z]+\([sztjw]\)|=", text):
            return False

        return False

    def _normalize_formula_text(self, text: str) -> str:
        text = text.replace("\n", " ").strip()
        text = re.sub(r"\s+", " ", text)
        return text[:600]

    def _extract_tail_name(self, node_name: str) -> str:
        if "的" in node_name:
            tail = node_name.split("的")[-1].strip()
            if len(tail) >= 2:
                return tail
        return ""
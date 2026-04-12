from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional


class NodeContentEnricher:
    """
    基于现有 MinerU 缓存结果做节点内容增强：
    1. 按章节 full.md 读取
    2. 在章节内按标题切块
    3. 为节点定位最相关的小节块
    4. 用该小节块生成 explanation_raw / key_points 等

    当前目标：
    - 解决同一章节多个二级节点都吃整章内容的问题
    - 不重跑 MinerU，直接复用已缓存的 full.md
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
            matched_doc = self._find_matching_chapter_doc(
                chapter_docs=chapter_docs,
                start_page=chapter_start,
                end_page=chapter_end,
            )

            if matched_doc is None:
                node["extra"]["page_ref_status"] = "mineru_doc_not_found"
                continue

            full_md = matched_doc["full_md"]
            chapter_blocks = self._split_md_into_blocks(full_md)

            node["page_refs"] = list(range(chapter_start, chapter_end + 1))
            node["extra"]["mineru_doc_name"] = matched_doc["pdf_name"]

            best_block = self._find_best_block_for_node(node, chapter_blocks)

            anchor_page = self._estimate_anchor_page(
                node=node,
                chapter_start=chapter_start,
                chapter_end=chapter_end,
                best_block=best_block,
            )
            node["extra"]["anchor_page"] = anchor_page

            refined_pages = self._build_refined_pages(
                node=node,
                chapter_start=chapter_start,
                chapter_end=chapter_end,
                best_block=best_block,
                anchor_page=anchor_page,
            )
            node["extra"]["page_refs_refined"] = refined_pages

            explanation_raw = self._build_explanation_raw_from_block(node, best_block, full_md)
            node["explanation_raw"] = explanation_raw

            node["core_concepts"] = self._build_core_concepts(node)
            node["key_points"] = self._build_key_points(explanation_raw)

            if not str(node.get("summary", "")).strip():
                node["summary"] = self._build_summary_from_explanation(explanation_raw)

            node["extra"]["page_ref_status"] = "ok"
            node["extra"]["page_ref_count"] = len(node["page_refs"])
            node["extra"]["page_refined_count"] = len(refined_pages)
            node["extra"]["matched_block_title"] = best_block["title"] if best_block else ""
            node["extra"]["matched_block_score"] = best_block["score"] if best_block else 0

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
        """
        按 markdown 标题切块。
        每个块结构：
        {
            "title": str,
            "level": int,
            "content": str
        }
        """
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

            # 二级节点优先匹配更细粒度标题块
            if level == 2 and block.get("level", 0) >= 2:
                score += 2

            # 一级节点优先大标题块
            if level == 1 and block.get("level", 0) == 1:
                score += 2

            if score > best_score:
                best_score = score
                best_block = dict(block)
                best_block["score"] = score

        return best_block

    def _estimate_anchor_page(
        self,
        node: dict[str, Any],
        chapter_start: int,
        chapter_end: int,
        best_block: Optional[dict[str, Any]],
    ) -> int:
        if best_block is None:
            return chapter_start

        level = int(node.get("level", 1))
        title = str(best_block.get("title", "")).strip()
        content = str(best_block.get("content", "")).strip()

        # 粗略估计：二级节点往章节中部或后部偏移一点
        # 不求绝对精确，先让不同子节点不再都落在同一页
        chapter_len = max(1, chapter_end - chapter_start + 1)

        if level == 1:
            return chapter_start

        hash_base = title + content[:200]
        bucket = sum(ord(ch) for ch in hash_base) % min(6, chapter_len)
        return min(chapter_start + bucket, chapter_end)

    def _build_refined_pages(
        self,
        node: dict[str, Any],
        chapter_start: int,
        chapter_end: int,
        best_block: Optional[dict[str, Any]],
        anchor_page: int,
    ) -> list[int]:
        level = int(node.get("level", 1))

        if level == 1:
            end = min(chapter_start + 3, chapter_end)
            return list(range(chapter_start, end + 1))

        # 二级节点围绕估计锚点收缩，避免所有子节点都共享同一组页
        start = max(chapter_start, anchor_page - 1)
        end = min(chapter_end, anchor_page + 2)
        return list(range(start, end + 1))

    def _build_explanation_raw_from_block(
        self,
        node: dict[str, Any],
        best_block: Optional[dict[str, Any]],
        full_md: str,
    ) -> str:
        if best_block is None:
            lines = self._clean_md_lines(full_md)
            return " ".join(lines[:4])

        block_text = str(best_block.get("content", "")).strip()
        lines = self._clean_md_lines(block_text)

        node_name = str(node.get("name", "")).strip()
        tags = node.get("tags", []) or []
        extra = node.get("extra", {}) or {}
        retrieval_keywords = extra.get("retrieval_keywords", []) or []

        scored_lines: list[tuple[int, str]] = []

        for line in lines:
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
                scored_lines.append((score, line))

        if not scored_lines:
            return " ".join(lines[:4])

        scored_lines.sort(key=lambda x: (-x[0], len(x[1])))

        selected: list[str] = []
        for _, line in scored_lines:
            if line not in selected:
                selected.append(line)
            if len(selected) >= 4:
                break

        return " ".join(selected)

    def _clean_md_lines(self, text: str) -> list[str]:
        results: list[str] = []

        for raw in text.splitlines():
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
                results.append(line)

        return results

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

    def _build_key_points(self, explanation_raw: str) -> list[str]:
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

    def _extract_tail_name(self, node_name: str) -> str:
        if "的" in node_name:
            tail = node_name.split("的")[-1].strip()
            if len(tail) >= 2:
                return tail
        return ""

    @staticmethod
    def _clean_sentence(text: str) -> str:
        text = text.strip()
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"^#+\s*", "", text)
        return text.strip()
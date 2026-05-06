from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional


class NodeContentEnricher:
    """
    基于现有 MinerU 缓存结果做节点内容增强。

    V2 改动目标：
    - 不改节点字段，只提高字段内容质量。
    - 不再只依赖单个 best_block，而是聚合 best_block、相邻块、同章节关键词块。
    - 增强 explanation_raw / key_points 的覆盖面，避免候选内容过短、过空、重复。
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
                start_page=int(chapter_start),
                end_page=int(chapter_end),
            )

            if matched_doc is None:
                node["extra"]["page_ref_status"] = "mineru_doc_not_found"
                continue

            full_md = matched_doc["full_md"]
            chapter_blocks = self._split_md_into_blocks(full_md)

            node["page_refs"] = list(range(int(chapter_start), int(chapter_end) + 1))
            node["extra"]["mineru_doc_name"] = matched_doc["pdf_name"]

            scored_blocks = self._score_blocks_for_node(node, chapter_blocks)
            best_block = scored_blocks[0] if scored_blocks else None
            evidence_blocks = self._select_evidence_blocks(
                node=node,
                blocks=chapter_blocks,
                scored_blocks=scored_blocks,
            )

            anchor_page = self._estimate_anchor_page(
                node=node,
                chapter_start=int(chapter_start),
                chapter_end=int(chapter_end),
                best_block=best_block,
            )
            node["extra"]["anchor_page"] = anchor_page

            refined_pages = self._build_refined_pages(
                node=node,
                chapter_start=int(chapter_start),
                chapter_end=int(chapter_end),
                best_block=best_block,
                anchor_page=anchor_page,
            )
            node["extra"]["page_refs_refined"] = refined_pages

            explanation_raw = self._build_explanation_raw_from_blocks(
                node=node,
                evidence_blocks=evidence_blocks,
                full_md=full_md,
            )
            node["explanation_raw"] = explanation_raw

            node["core_concepts"] = self._build_core_concepts(node, explanation_raw)
            node["key_points"] = self._build_key_points(explanation_raw)

            if not str(node.get("summary", "")).strip():
                node["summary"] = self._build_summary_from_explanation(explanation_raw)

            node["extra"]["page_ref_status"] = "ok"
            node["extra"]["page_ref_count"] = len(node["page_refs"])
            node["extra"]["page_refined_count"] = len(refined_pages)
            node["extra"]["matched_block_title"] = best_block["title"] if best_block else ""
            node["extra"]["matched_block_score"] = best_block["score"] if best_block else 0
            node["extra"]["content_evidence_block_count"] = len(evidence_blocks)
            node["extra"]["content_evidence_block_titles"] = [
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
        retrieval_keywords = [
            str(x).strip() for x in (extra.get("retrieval_keywords", []) or []) if str(x).strip()
        ]
        query_terms = self._build_query_terms(node_name, tags, retrieval_keywords)
        node_role = str(extra.get("node_role", "")).strip()
        legacy_level = int(extra.get("legacy_level", 1) or 1)

        scored: list[dict[str, Any]] = []
        for block in blocks:
            title = str(block.get("title", "")).strip()
            content = str(block.get("content", "")).strip()
            head_text = content[:1800]
            all_text = f"{title}\n{head_text}"
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

            for term in query_terms:
                if len(term) < 2:
                    continue
                if term in title:
                    score += 5
                if term in head_text:
                    score += 2

            # 子节点更适合吃具体小节，章节点更适合吃章内导论与高相关小节。
            block_level = int(block.get("level", 0) or 0)
            if node_role == "topic" or legacy_level >= 2:
                if block_level >= 1:
                    score += 2
            else:
                if block_level in {1, 2}:
                    score += 2

            # 常见章节标题噪声降权。
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
            return blocks[:2]

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

        # 加入相邻块，解决定义、例子、图示分散在前后小节的问题。
        add_block(by_order.get(best_order - 1))
        add_block(by_order.get(best_order + 1))

        # 加入同章节中其他高分块，作为补充证据。
        for block in scored_blocks[1:6]:
            add_block(block)
            if len(selected) >= 6:
                break

        selected.sort(key=lambda x: int(x.get("order", 0)))
        return selected[:6]

    def _estimate_anchor_page(
        self,
        node: dict[str, Any],
        chapter_start: int,
        chapter_end: int,
        best_block: Optional[dict[str, Any]],
    ) -> int:
        if best_block is None:
            return chapter_start

        extra = node.get("extra", {}) or {}
        legacy_level = int(extra.get("legacy_level", 1) or 1)
        if legacy_level == 1 or str(extra.get("node_role", "")) == "chapter_anchor":
            return chapter_start

        chapter_len = max(1, chapter_end - chapter_start + 1)
        order = int(best_block.get("order", 0) or 0)
        # 用 block 顺序近似页码，比原来的 hash 更稳定。
        estimated_offset = min(chapter_len - 1, max(0, round(order / max(1, order + 4) * chapter_len)))
        return min(chapter_start + estimated_offset, chapter_end)

    def _build_refined_pages(
        self,
        node: dict[str, Any],
        chapter_start: int,
        chapter_end: int,
        best_block: Optional[dict[str, Any]],
        anchor_page: int,
    ) -> list[int]:
        extra = node.get("extra", {}) or {}
        legacy_level = int(extra.get("legacy_level", 1) or 1)
        if legacy_level == 1 or str(extra.get("node_role", "")) == "chapter_anchor":
            end = min(chapter_start + 4, chapter_end)
            return list(range(chapter_start, end + 1))

        start = max(chapter_start, anchor_page - 1)
        end = min(chapter_end, anchor_page + 3)
        return list(range(start, end + 1))

    def _build_explanation_raw_from_blocks(
        self,
        node: dict[str, Any],
        evidence_blocks: list[dict[str, Any]],
        full_md: str,
    ) -> str:
        if not evidence_blocks:
            lines = self._clean_md_lines(full_md)
            return " ".join(lines[:6])[:1800]

        node_name = str(node.get("name", "")).strip()
        tags = [str(x).strip() for x in (node.get("tags", []) or []) if str(x).strip()]
        extra = node.get("extra", {}) or {}
        retrieval_keywords = [
            str(x).strip() for x in (extra.get("retrieval_keywords", []) or []) if str(x).strip()
        ]
        query_terms = self._build_query_terms(node_name, tags, retrieval_keywords)

        scored_lines: list[tuple[int, int, str]] = []
        line_order = 0
        for block in evidence_blocks:
            title = str(block.get("title", "")).strip()
            lines = self._clean_md_lines(str(block.get("content", "")))
            for line in lines:
                score = self._score_text_for_node(
                    text=line,
                    node_name=node_name,
                    query_terms=query_terms,
                    title=title,
                )
                # 对定义、特点、例子、总结类句子做轻微提权。
                if any(m in line for m in ["是指", "是", "称为", "特点", "因此", "可见", "例如", "比如", "系统"]):
                    score += 1
                if score > 0:
                    scored_lines.append((score, line_order, line))
                line_order += 1

        if not scored_lines:
            fallback_lines: list[str] = []
            for block in evidence_blocks[:2]:
                fallback_lines.extend(self._clean_md_lines(str(block.get("content", ""))))
            return " ".join(self._deduplicate_texts(fallback_lines)[:8])[:1800]

        scored_lines.sort(key=lambda x: (-x[0], x[1]))

        # 先拿高分句，再按原文顺序组织，保证解释更自然。
        selected_high = [line for _, _, line in scored_lines[:12]]
        selected = self._deduplicate_texts(selected_high)
        selected.sort(key=lambda s: next((order for _, order, line in scored_lines if line == s), 9999))

        return " ".join(selected[:8])[:2200]

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
            if re.match(r"^#{1,6}\s+", line):
                line = re.sub(r"^#{1,6}\s+", "", line)
            line = re.sub(r"!\[.*?\]\(.*?\)", "", line)
            line = re.sub(r"<[^>]+>", " ", line)
            line = self._normalize_ocr_symbols(line)
            line = re.sub(r"\s+", " ", line).strip()
            if len(line) >= 10:
                results.append(line)
        return results

    def _build_core_concepts(self, node: dict[str, Any], explanation_raw: str = "") -> list[str]:
        tags = node.get("tags", []) or []
        extra = node.get("extra", {}) or {}
        retrieval_keywords = extra.get("retrieval_keywords", []) or []
        node_name = str(node.get("name", "")).strip()
        concepts: list[str] = []
        for item in [node_name] + list(retrieval_keywords) + list(tags):
            item = str(item).strip()
            if item and item not in concepts:
                concepts.append(item)

        # 从原文中补充一些常见控制理论核心词，但不新增字段。
        domain_terms = [
            "反馈", "负反馈", "开环控制", "闭环控制", "复合控制", "扰动", "偏差", "被控对象",
            "被控量", "控制装置", "测量元件", "比较元件", "执行元件", "稳定性", "快速性", "准确性",
            "传递函数", "微分方程", "结构图", "信号流图", "根轨迹", "频率特性", "校正",
        ]
        for term in domain_terms:
            if term in explanation_raw and term not in concepts:
                concepts.append(term)
            if len(concepts) >= 8:
                break
        return concepts[:8]

    def _build_key_points(self, explanation_raw: str) -> list[str]:
        if not explanation_raw.strip():
            return []
        parts = re.split(r"(?<=[。！？.!?])\s+", explanation_raw)
        if len(parts) <= 1:
            parts = re.split(r"(?<=[；;])\s*", explanation_raw)
        results: list[str] = []
        for part in parts:
            part = self._clean_sentence(part)
            if len(part) < 12:
                continue
            if part not in results:
                results.append(part[:500])
            if len(results) >= 6:
                break
        return results

    def _build_summary_from_explanation(self, explanation_raw: str) -> str:
        if not explanation_raw.strip():
            return ""
        parts = re.split(r"(?<=[。！？.!?])\s+", explanation_raw)
        cleaned = [self._clean_sentence(p) for p in parts if self._clean_sentence(p)]
        if not cleaned:
            return ""
        return cleaned[0][:140]

    def _build_query_terms(self, node_name: str, tags: list[str], retrieval_keywords: list[str]) -> list[str]:
        terms: list[str] = []
        for item in [node_name, self._extract_tail_name(node_name)] + retrieval_keywords + tags:
            item = str(item).strip()
            if len(item) >= 2 and item not in terms:
                terms.append(item)

        expansions = {
            "自动控制的基本原理与方式": ["反馈控制原理", "自动控制系统基本控制方式", "反馈控制方式", "开环控制方式", "复合控制方式"],
            "自动控制系统示例": ["函数记录仪", "自动驾驶仪", "锅炉液位", "转速控制", "磁盘驱动"],
            "自动控制系统的分类": ["按系统特性分类", "按输入量变化规律分类", "线性连续", "非线性控制系统", "恒值控制系统", "随动系统", "程序控制系统"],
            "对自动控制系统的基本要求": ["稳定性", "快速性", "准确性", "稳态误差", "过渡过程"],
            "自动控制系统的分析与设计工具": ["MATLAB", "Python", "控制系统工具箱", "Python-control"],
        }
        for key, values in expansions.items():
            if key == node_name or key in node_name:
                for value in values:
                    if value not in terms:
                        terms.append(value)
        return terms

    def _score_text_for_node(self, text: str, node_name: str, query_terms: list[str], title: str = "") -> int:
        score = 0
        if node_name and node_name in text:
            score += 8
        tail_name = self._extract_tail_name(node_name)
        if tail_name and tail_name in text:
            score += 4
        for term in query_terms:
            if len(term) >= 2 and term in text:
                score += 2
            if len(term) >= 2 and term in title:
                score += 1
        if len(text) > 700:
            score -= 1
        if "习题" in text or "试说明" in text:
            score -= 4
        return score

    def _deduplicate_texts(self, texts: list[str]) -> list[str]:
        results: list[str] = []
        fingerprints: set[str] = set()
        for text in texts:
            cleaned = self._clean_sentence(text)
            if not cleaned:
                continue
            fingerprint = re.sub(r"\W+", "", cleaned)[:80]
            if fingerprint in fingerprints:
                continue
            if any(self._is_near_duplicate(cleaned, old) for old in results):
                continue
            results.append(cleaned)
            fingerprints.add(fingerprint)
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

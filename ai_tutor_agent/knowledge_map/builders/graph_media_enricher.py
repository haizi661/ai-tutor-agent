from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


class GraphMediaEnricher:
    def __init__(
        self,
        mineru_cache_root: str | Path = "data/mineru_cache",
        *,
        visual_analyzer: Any | None = None,
    ) -> None:
        self.mineru_cache_root = Path(mineru_cache_root)
        self.chapter_docs = self._load_chapter_docs()
        self.visual_analyzer = visual_analyzer
        self._visual_cache: dict[str, str] = {}

    def collect_for_nodes(
        self,
        *,
        traversed_nodes: list[dict[str, Any]],
        node_map: dict[str, dict[str, Any]],
        question: str = "",
    ) -> list[dict[str, Any]]:
        media_items: list[dict[str, Any]] = []
        seen_keys: set[tuple[str, str, str]] = set()
        prioritized_nodes = sorted(
            traversed_nodes,
            key=lambda item: (
                self._role_priority(item.get("node_role", "")),
                item.get("hop", 99),
                -item.get("score", 0.0),
            ),
        )

        for traversed in prioritized_nodes:
            if traversed.get("hop", 99) > 1:
                continue
            node = node_map.get(traversed["node_id"])
            if not node:
                continue

            doc = self._find_matching_doc(node)
            formulas = self._collect_formula_items(node, doc)
            figures = self._collect_figure_items(node, doc)

            for item in formulas + figures:
                dedup_key = (
                    item["node_id"],
                    item["asset_type"],
                    item.get("text", "") or item.get("caption", ""),
                )
                if dedup_key in seen_keys:
                    continue
                seen_keys.add(dedup_key)
                item["hop"] = traversed.get("hop", 99)
                item["node_role"] = traversed.get("node_role", "context")
                self._annotate_media_item(item, question=question)
                item["media_score"] = self._score_media_item(item, question=question)
                media_items.append(item)

        if not media_items:
            return []

        media_items.sort(
            key=lambda item: (
                -item.get("media_score", 0.0),
                item.get("hop", 99),
                0 if item["asset_type"] == "formula" else 1,
                item["reference"],
            )
        )

        self._assign_display_labels(media_items)
        primary_items = self._select_primary_media_items(media_items)
        supplementary_items = self._select_supplementary_media_items(media_items, primary_items)

        for item in primary_items:
            item["is_primary"] = True
        for item in supplementary_items:
            item["is_primary"] = False

        return primary_items + supplementary_items

    def _select_primary_media_items(self, media_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        selected: list[dict[str, Any]] = []
        formula_count = 0
        figure_count = 0
        for item in media_items:
            if item["asset_type"] == "formula" and formula_count >= 2:
                continue
            if item["asset_type"] == "figure" and figure_count >= 1:
                continue
            selected.append(item)
            if item["asset_type"] == "formula":
                formula_count += 1
            else:
                figure_count += 1
            if len(selected) >= 3:
                break
        return selected

    def _select_supplementary_media_items(
        self,
        media_items: list[dict[str, Any]],
        primary_items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        primary_refs = {item["reference"] for item in primary_items}
        supplementary: list[dict[str, Any]] = []
        for item in media_items:
            if item["reference"] in primary_refs:
                continue
            supplementary.append(item)
            if len(supplementary) >= 3:
                break
        return supplementary

    def _annotate_media_item(self, item: dict[str, Any], *, question: str) -> None:
        item["analysis_hint"] = self._build_analysis_hint(item)
        if item["asset_type"] == "formula":
            item["visual_summary"] = ""
            item["placement_hint"] = "analysis"
            return

        item["visual_summary"] = self._describe_figure(item, question=question)
        item["placement_hint"] = "analysis"

    def _score_media_item(self, item: dict[str, Any], *, question: str) -> float:
        score = 10.0
        question_tokens = self._extract_query_tokens(question)
        haystack = " ".join(
            [
                str(item.get("text", "") or ""),
                str(item.get("caption", "") or ""),
                str(item.get("analysis_hint", "") or ""),
                str(item.get("visual_summary", "") or ""),
                str(item.get("node_name", "") or ""),
            ]
        )
        for token in question_tokens:
            if token in haystack:
                score += 1.2

        role = str(item.get("node_role", "") or "")
        score += {
            "primary": 3.0,
            "prerequisite": 2.0,
            "supporting": 1.5,
            "comparison": 1.2,
        }.get(role, 0.5)

        if item["asset_type"] == "formula":
            score += 1.8
            if any(token in question for token in ["公式", "关系", "阻尼比", "超调量", "时间", "峰值"]):
                score += 1.2
        else:
            caption = str(item.get("caption", "") or "")
            if any(keyword in caption for keyword in ["响应曲线", "单位阶跃", "性能指标", "超调量", "曲线"]):
                score += 2.2
            if any(keyword in caption for keyword in ["结构图", "原理图", "框图"]) and not any(
                token in question for token in ["结构", "原理", "框图"]
            ):
                score -= 1.8

        score -= item.get("hop", 99) * 0.6
        return score

    def _assign_display_labels(self, media_items: list[dict[str, Any]]) -> None:
        formula_idx = 1
        figure_idx = 1
        for item in media_items:
            if item["asset_type"] == "formula":
                item["display_label"] = f"式{self._to_chinese_numeral(formula_idx)}"
                formula_idx += 1
            else:
                item["display_label"] = f"图{self._to_chinese_numeral(figure_idx)}"
                figure_idx += 1

    def _to_chinese_numeral(self, number: int) -> str:
        numerals = {
            0: "零",
            1: "一",
            2: "二",
            3: "三",
            4: "四",
            5: "五",
            6: "六",
            7: "七",
            8: "八",
            9: "九",
            10: "十",
        }
        if number in numerals:
            return numerals[number]
        if number < 20:
            return "十" + numerals[number - 10]
        tens, ones = divmod(number, 10)
        if ones == 0:
            return numerals.get(tens, str(tens)) + "十"
        return numerals.get(tens, str(tens)) + "十" + numerals.get(ones, str(ones))

    def _role_priority(self, role: str) -> int:
        order = {
            "primary": 0,
            "prerequisite": 1,
            "supporting": 2,
            "comparison": 2,
        }
        return order.get(role, 3)

    def _load_chapter_docs(self) -> list[dict[str, Any]]:
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
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                full_md = full_md_path.read_text(encoding="utf-8")
            except Exception:
                continue

            page_range = self._extract_page_range(manifest.get("pdf_name", "") or item.name)
            if page_range is None:
                continue

            docs.append(
                {
                    "cache_dir": item,
                    "manifest": manifest,
                    "full_md": full_md,
                    "start_page": page_range[0],
                    "end_page": page_range[1],
                }
            )

        docs.sort(key=lambda doc: doc["start_page"])
        return docs

    def _extract_page_range(self, text: str) -> tuple[int, int] | None:
        match = re.search(r"_p(\d+)-(\d+)", text)
        if not match:
            return None
        return int(match.group(1)), int(match.group(2))

    def _find_matching_doc(self, node: dict[str, Any]) -> dict[str, Any] | None:
        extra = node.get("extra", {}) or {}
        page_range = extra.get("chapter_page_range", []) or []
        if not isinstance(page_range, list) or len(page_range) != 2:
            return None

        start_page, end_page = page_range
        for doc in self.chapter_docs:
            if doc["start_page"] == start_page and doc["end_page"] == end_page:
                return doc
        for doc in self.chapter_docs:
            if doc["start_page"] <= start_page <= doc["end_page"]:
                return doc
        return None

    def _collect_formula_items(self, node: dict[str, Any], doc: dict[str, Any] | None) -> list[dict[str, Any]]:
        formulas: list[str] = []
        for formula in node.get("formulas", []) or []:
            cleaned = self._clean_formula_text(str(formula))
            if self._looks_like_formula(cleaned) and cleaned not in formulas:
                formulas.append(cleaned)

        scope_text = self._extract_node_scope_text(node, doc) if doc else ""
        if scope_text:
            for formula in self._extract_formulas_from_block(scope_text):
                if formula not in formulas:
                    formulas.append(formula)

        results: list[dict[str, Any]] = []
        for idx, formula in enumerate(formulas[:4], start=1):
            results.append(
                {
                    "node_id": str(node.get("node_id", "")),
                    "node_name": str(node.get("name", "")),
                    "asset_type": "formula",
                    "reference": f"{node.get('node_id', '')}.formula_asset[{idx}]",
                    "text": formula,
                }
            )
        return results

    def _collect_figure_items(self, node: dict[str, Any], doc: dict[str, Any] | None) -> list[dict[str, Any]]:
        if not doc:
            return []

        scope_text = self._extract_node_scope_text(node, doc)
        if not scope_text:
            return []

        figures = self._extract_figures_from_block(scope_text, doc["manifest"])
        results: list[dict[str, Any]] = []
        for idx, figure in enumerate(figures[:3], start=1):
            results.append(
                {
                    "node_id": str(node.get("node_id", "")),
                    "node_name": str(node.get("name", "")),
                    "asset_type": "figure",
                    "reference": f"{node.get('node_id', '')}.figure_asset[{idx}]",
                    "caption": figure["caption"],
                    "image_paths_abs": figure["image_paths_abs"],
                }
            )
        return results

    def _build_analysis_hint(self, item: dict[str, Any]) -> str:
        node_name = str(item.get("node_name", "")).strip() or "当前节点"
        if item.get("asset_type") == "formula":
            formula_text = str(item.get("text", "")).strip()
            if "e^" in formula_text or "e ^" in formula_text:
                return f"可结合{node_name}中的指数衰减关系，解释响应快慢、超调或衰减趋势。"
            if "\\frac" in formula_text or "/" in formula_text:
                return f"可结合{node_name}中的分子分母结构，说明参数如何影响系统性能。"
            return f"可结合{node_name}中的变量关系，解释概念之间的定量联系。"

        caption = str(item.get("caption", "")).strip()
        if any(keyword in caption for keyword in ["响应", "曲线", "阶跃", "波形"]):
            return f"可结合{node_name}的曲线走势，分析超调量、峰值时间、调节时间或稳态值。"
        return f"可结合{node_name}的图形结构，说明系统组成、信号流向或关键现象。"

    def _describe_figure(self, item: dict[str, Any], *, question: str) -> str:
        paths = item.get("image_paths_abs", []) or []
        if not paths:
            return ""

        cache_key = str(Path(paths[0]).resolve())
        if cache_key in self._visual_cache:
            return self._visual_cache[cache_key]

        summary = ""
        if self.visual_analyzer is not None:
            summary = self.visual_analyzer.describe_image(
                paths[0],
                node_name=str(item.get("node_name", "")),
                caption=str(item.get("caption", "")),
                question=question,
            )

        if not summary:
            caption = str(item.get("caption", "")).strip()
            node_name = str(item.get("node_name", "")).strip() or "该知识点"
            if caption:
                summary = f"该图与“{node_name}”相关，图注为“{caption}”。"
            else:
                summary = f"该图与“{node_name}”相关，可用于补充当前知识点的图形化分析。"

        self._visual_cache[cache_key] = summary
        return summary

    def _split_md_into_blocks(self, full_md: str) -> list[dict[str, Any]]:
        lines = full_md.splitlines()
        blocks: list[dict[str, Any]] = []
        current_title = "ROOT"
        current_level = 0
        current_lines: list[str] = []

        def flush_block() -> None:
            nonlocal current_lines
            content = "\n".join(current_lines).strip()
            if content:
                blocks.append({"title": current_title, "level": current_level, "content": content})
            current_lines = []

        for raw in lines:
            line = (raw or "").rstrip()
            stripped = line.strip()
            if not stripped:
                current_lines.append("")
                continue

            match = re.match(r"^(#{1,6})\s+(.*)$", stripped)
            if match:
                flush_block()
                current_level = len(match.group(1))
                current_title = match.group(2).strip()
                continue

            current_lines.append(line)

        flush_block()
        return blocks

    def _find_best_block(self, node: dict[str, Any], full_md: str) -> dict[str, Any] | None:
        blocks = self._split_md_into_blocks(full_md)
        if not blocks:
            return None

        node_name = str(node.get("name", "")).strip()
        tags = [str(tag).strip() for tag in (node.get("tags", []) or []) if str(tag).strip()]
        extra = node.get("extra", {}) or {}
        retrieval_keywords = [
            str(keyword).strip()
            for keyword in (extra.get("retrieval_keywords", []) or [])
            if str(keyword).strip()
        ]
        tail_name = self._extract_tail_name(node_name)

        best_block: dict[str, Any] | None = None
        best_score = -1
        for block in blocks:
            title = str(block.get("title", ""))
            content = str(block.get("content", ""))
            head_text = content[:1500]
            score = 0

            if node_name and node_name in title:
                score += 20
            if node_name and node_name in head_text:
                score += 6
            if tail_name and tail_name in title:
                score += 10
            if tail_name and tail_name in head_text:
                score += 4

            for keyword in retrieval_keywords + tags:
                if len(keyword) < 2:
                    continue
                if keyword in title:
                    score += 3
                if keyword in head_text:
                    score += 1

            if score > best_score:
                best_score = score
                best_block = dict(block)

        return best_block

    def _extract_node_scope_text(self, node: dict[str, Any], doc: dict[str, Any]) -> str:
        full_md = doc["full_md"]
        node_name = str(node.get("name", "")).strip()
        extra = node.get("extra", {}) or {}
        node_role = str(extra.get("node_role", "") or "").strip()
        is_focus = bool(extra.get("is_focus"))
        page_refs = node.get("page_refs", []) or []
        lines = full_md.splitlines()

        if node_role not in {"chapter_anchor", ""} and node_name:
            section_match = self._extract_named_section(lines, node_name)
            if section_match:
                return section_match

        if is_focus and page_refs:
            block = self._find_best_block(node, full_md)
            return block["content"] if block else ""

        block = self._find_best_block(node, full_md)
        return block["content"] if block else ""

    def _extract_named_section(self, lines: list[str], node_name: str) -> str:
        start_idx = None
        for idx, raw in enumerate(lines):
            stripped = (raw or "").strip()
            if stripped.startswith("#") and node_name in stripped:
                start_idx = idx
                break

        if start_idx is None:
            return ""

        end_idx = len(lines)
        for idx in range(start_idx + 1, len(lines)):
            stripped = (lines[idx] or "").strip()
            if not stripped.startswith("#"):
                continue
            if re.match(r"^#\s+\d+-\d+\b", stripped):
                end_idx = idx
                break

        return "\n".join(lines[start_idx + 1 : end_idx]).strip()

    def _extract_formulas_from_block(self, block_text: str) -> list[str]:
        formulas: list[str] = []
        lines = block_text.splitlines()
        index = 0

        while index < len(lines):
            stripped = (lines[index] or "").strip()

            if stripped.startswith("```math"):
                parts: list[str] = []
                index += 1
                while index < len(lines):
                    candidate = (lines[index] or "").strip()
                    if candidate.startswith("```"):
                        break
                    if candidate:
                        parts.append(candidate)
                    index += 1
                formula = self._clean_formula_text(" ".join(parts))
                if self._looks_like_formula(formula) and formula not in formulas:
                    formulas.append(formula)
                index += 1
                continue

            if stripped.startswith("$$"):
                parts = [stripped[2:].strip()] if stripped[2:].strip() else []
                if stripped.endswith("$$") and len(stripped) > 4:
                    parts = [stripped[2:-2].strip()]
                else:
                    index += 1
                    while index < len(lines):
                        candidate = (lines[index] or "").strip()
                        if candidate.endswith("$$"):
                            tail = candidate[:-2].strip()
                            if tail:
                                parts.append(tail)
                            break
                        if candidate:
                            parts.append(candidate)
                        index += 1
                formula = self._clean_formula_text(" ".join(parts))
                if self._looks_like_formula(formula) and formula not in formulas:
                    formulas.append(formula)
                index += 1
                continue

            cleaned = self._clean_formula_text(stripped)
            if self._looks_like_formula(cleaned) and cleaned not in formulas:
                formulas.append(cleaned)
            index += 1

        return formulas[:4]

    def _extract_figures_from_block(self, block_text: str, manifest: dict[str, Any]) -> list[dict[str, Any]]:
        figures: list[dict[str, Any]] = []
        lines = block_text.splitlines()
        pending_paths: list[str] = []

        for idx, raw in enumerate(lines):
            line = (raw or "").strip()
            if not line:
                continue

            image_paths = re.findall(r"!\[.*?\]\((.*?)\)", line)
            if image_paths:
                pending_paths.extend(image_paths)
                caption = self._clean_caption(re.sub(r"!\[.*?\]\((.*?)\)", "", line))
                if caption:
                    resolved = self._resolve_image_paths(pending_paths, manifest)
                    if resolved:
                        figures.append({"caption": caption, "image_paths_abs": resolved})
                    pending_paths = []
                continue

            if pending_paths and self._looks_like_figure_caption(line):
                resolved = self._resolve_image_paths(pending_paths, manifest)
                if resolved:
                    figures.append(
                        {
                            "caption": self._clean_caption(line),
                            "image_paths_abs": resolved,
                        }
                    )
                pending_paths = []
                continue

            if pending_paths:
                next_text = " ".join(part.strip() for part in lines[idx : idx + 2] if part.strip())
                resolved = self._resolve_image_paths(pending_paths, manifest)
                if resolved:
                    figures.append(
                        {
                            "caption": self._clean_caption(next_text) or "相关图表",
                            "image_paths_abs": resolved,
                        }
                    )
                pending_paths = []

        return figures

    def _resolve_image_paths(self, image_paths: list[str], manifest: dict[str, Any]) -> list[str]:
        resolved: list[str] = []
        images = manifest.get("images", {}) or {}
        cache_dir = Path(manifest.get("cache_dir", self.mineru_cache_root))

        for image_path in image_paths:
            normalized = str(image_path).replace("\\", "/").strip()
            trimmed = normalized.replace("images/", "", 1)
            abs_path = None

            if normalized in images:
                abs_path = images[normalized].get("abs_path")
            elif trimmed in images:
                abs_path = images[trimmed].get("abs_path")
            else:
                image_name = Path(trimmed).name
                for meta in images.values():
                    if meta.get("original_name") == image_name:
                        abs_path = meta.get("abs_path")
                        break

            if abs_path is None:
                abs_path = str((cache_dir / "images" / Path(trimmed).name).resolve())
            else:
                abs_path = str(Path(abs_path).resolve())

            if abs_path not in resolved:
                resolved.append(abs_path)

        return resolved

    def _looks_like_formula(self, text: str) -> bool:
        if not text:
            return False
        cjk_count = len(re.findall(r"[\u4e00-\u9fff]", text))
        if cjk_count > 12 and "\\tag" not in text:
            return False
        patterns = [
            r"\\tag",
            r"\\frac|\\dot|\\sum|\\omega|\\sigma|\\Phi",
            r"[A-Za-z]\s*\(.*?\)\s*=",
            r"[A-Za-z]\s*=",
            r"\b[eEsSzZ]\b",
        ]
        if any(re.search(pattern, text) for pattern in patterns):
            return True
        return "=" in text and any(ch in text for ch in ["+", "-", "/", "^"])

    def _looks_like_figure_caption(self, text: str) -> bool:
        return bool(re.search(r"(图|Figure|Fig\.)\s*[\d\-]+", text, flags=re.IGNORECASE))

    def _clean_formula_text(self, text: str) -> str:
        return re.sub(r"\s+", " ", (text or "").strip())[:240]

    def _clean_caption(self, text: str) -> str:
        return re.sub(r"\s+", " ", (text or "").strip())[:180]

    def _extract_tail_name(self, node_name: str) -> str:
        if "的" in node_name:
            tail = node_name.split("的", 1)[-1].strip()
            if len(tail) >= 2:
                return tail
        return ""

    def _extract_query_tokens(self, question: str) -> list[str]:
        text = " ".join((question or "").split())
        stop_words = {"什么", "关系", "如何", "为什么", "请问", "一个", "系统"}
        tokens: list[str] = []
        current = []
        for ch in text:
            if ch.isalnum() or ("\u4e00" <= ch <= "\u9fff"):
                current.append(ch)
            else:
                if current:
                    token = "".join(current)
                    if len(token) >= 2 and token not in stop_words and token not in tokens:
                        tokens.append(token)
                    current = []
        if current:
            token = "".join(current)
            if len(token) >= 2 and token not in stop_words and token not in tokens:
                tokens.append(token)
        return tokens[:8]

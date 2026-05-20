from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ai_tutor_agent.platform_paths import resolve_existing_path, resolve_project_path


class GraphMediaEnricher:
    def __init__(
        self,
        mineru_cache_root: str | Path = "data/mineru_cache",
        *,
        visual_analyzer: Any | None = None,
        annotated_assets_path: str | Path = "data/media_evidence_index",
    ) -> None:
        self.mineru_cache_root = resolve_project_path(mineru_cache_root)
        self.chapter_docs = self._load_chapter_docs()
        self.visual_analyzer = visual_analyzer
        self.annotated_assets_path = resolve_project_path(annotated_assets_path)
        self.annotated_assets = self._load_annotated_assets()
        self._visual_cache: dict[str, str] = {}

    def collect_for_nodes(
        self,
        *,
        traversed_nodes: list[dict[str, Any]],
        node_map: dict[str, dict[str, Any]],
        question: str = "",
    ) -> list[dict[str, Any]]:
        media_by_ref: dict[str, dict[str, Any]] = {}
        prioritized_nodes = sorted(
            traversed_nodes,
            key=lambda item: (
                self._role_priority(item.get("node_role", "")),
                item.get("hop", 99),
                -float(item.get("score", 0.0)),
            ),
        )

        for traversed in prioritized_nodes:
            if traversed.get("hop", 99) > 1:
                continue

            node = node_map.get(traversed["node_id"])
            if not node:
                continue

            candidates = self._collect_annotated_media_items(traversed, question=question)
            doc = self._find_matching_doc(node)
            fallback_candidates: list[dict[str, Any]] = []
            if doc:
                fallback_candidates = self._collect_fallback_media_items(node, doc, traversed, question=question)
            if candidates:
                candidates = self._merge_missing_media_types(candidates, fallback_candidates)
                candidates = self._replace_unusable_figure_candidates(candidates, fallback_candidates)
            else:
                candidates = fallback_candidates

            for item in candidates:
                ref = str(item.get("reference", "") or "").strip()
                if not ref:
                    continue
                existing = media_by_ref.get(ref)
                if existing is None or float(item.get("media_score", 0.0)) > float(existing.get("media_score", 0.0)):
                    media_by_ref[ref] = item

        media_items = list(media_by_ref.values())
        if not media_items:
            return []

        media_items.sort(
            key=lambda item: (
                -float(item.get("media_score", 0.0)),
                int(item.get("hop", 99)),
                0 if item.get("asset_type") == "formula" else 1,
                str(item.get("reference", "")),
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

    def _collect_annotated_media_items(
        self,
        traversed: dict[str, Any],
        *,
        question: str,
    ) -> list[dict[str, Any]]:
        node_id = str(traversed.get("node_id", "") or "")
        node_name = str(traversed.get("name", "") or "")
        hop = int(traversed.get("hop", 99))
        node_role = str(traversed.get("node_role", "context") or "context")
        results: list[dict[str, Any]] = []

        for asset in self.annotated_assets:
            match_info = self._match_asset_to_node(asset, node_id)
            if not match_info["matched"]:
                continue
            item = self._build_media_item_from_annotated_asset(
                asset,
                traversed,
                question=question,
                match_info=match_info,
            )
            if not item:
                continue
            item["node_id"] = node_id
            item["node_name"] = node_name
            item["hop"] = hop
            item["node_role"] = node_role
            item["media_score"] = self._score_media_item(item, question=question)
            results.append(item)
        return results

    def _build_media_item_from_annotated_asset(
        self,
        asset: dict[str, Any],
        traversed: dict[str, Any],
        *,
        question: str,
        match_info: dict[str, Any],
    ) -> dict[str, Any] | None:
        asset_type = str(asset.get("asset_type", "") or "")
        if asset_type not in {"figure", "formula", "table"}:
            return None

        reference = str(asset.get("asset_id", "") or "").strip()
        if not reference:
            return None

        visual_summary = str((asset.get("extra", {}) or {}).get("visual_summary", "") or "").strip()
        relation_statement = str(asset.get("relation_statement", "") or "").strip()
        direct_claims = [str(item).strip() for item in (asset.get("direct_readable_claims", []) or []) if str(item).strip()]
        formula_meaning = str(asset.get("formula_meaning", "") or "").strip()
        analysis_hint = (
            relation_statement
            or formula_meaning
            or (direct_claims[0] if direct_claims else "")
            or self._build_analysis_hint_from_asset(asset)
        )

        item: dict[str, Any] = {
            "reference": reference,
            "asset_type": asset_type,
            "caption": str(asset.get("caption_text", "") or asset.get("title_text", "") or "").strip(),
            "text": str(asset.get("raw_text", "") or "").strip(),
            "analysis_hint": analysis_hint,
            "visual_summary": visual_summary or (direct_claims[0] if direct_claims and asset_type == "figure" else ""),
            "placement_hint": "analysis",
            "evidence_role": str(asset.get("evidence_role", "") or ""),
            "question_affordances": list(asset.get("question_affordances", []) or []),
            "retrieval_keywords": list(asset.get("retrieval_keywords", []) or []),
            "relation_statement": relation_statement,
            "formula_meaning": formula_meaning,
            "variables": list(asset.get("variables", []) or []),
            "domain_terms": list(asset.get("domain_terms", []) or []),
            "confidence": float(asset.get("confidence", 0.0) or 0.0),
            "source_path": str(asset.get("source_path", "") or "").strip(),
            "visual_type": str(asset.get("visual_type", "") or "").strip(),
            "asset_anchor_node_id": str(asset.get("anchor_node_id", "") or "").strip(),
            "asset_anchor_node_name": str(asset.get("anchor_node_name", "") or "").strip(),
            "node_link_score": float(match_info.get("link_score", 0.0) or 0.0),
            "match_kind": str(match_info.get("kind", "") or "").strip(),
            "chapter_title": str(asset.get("chapter_title", "") or "").strip(),
        }

        if asset_type == "figure":
            source_path = str(asset.get("source_path", "") or "").strip()
            image_paths_abs = [source_path] if source_path else []
            if not image_paths_abs:
                return None
            item["image_paths_abs"] = [str(resolved) for path in image_paths_abs if (resolved := resolve_existing_path(path))]
            if not item["image_paths_abs"]:
                return None
            if self.visual_analyzer is not None and not item["visual_summary"]:
                item["visual_summary"] = self._describe_figure(item, question=question)
        else:
            if not item["text"]:
                return None
            item["caption"] = str(asset.get("title_text", "") or asset.get("caption_text", "") or "").strip()

        return item

    def _collect_fallback_media_items(
        self,
        node: dict[str, Any],
        doc: dict[str, Any] | None,
        traversed: dict[str, Any],
        *,
        question: str,
    ) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        formulas = self._collect_formula_items(node, doc)
        figures = self._collect_figure_items(node, doc)

        tables = self._collect_table_items(node, doc)

        for item in formulas + figures + tables:
            item["hop"] = traversed.get("hop", 99)
            item["node_role"] = traversed.get("node_role", "context")
            item["analysis_hint"] = self._build_analysis_hint_from_media_item(item)
            item["placement_hint"] = "analysis"
            if item["asset_type"] == "figure":
                item["visual_summary"] = self._describe_figure(item, question=question)
            else:
                item["visual_summary"] = ""
            item["media_score"] = self._score_media_item(item, question=question)
            results.append(item)

        return results

    def _merge_missing_media_types(
        self,
        candidates: list[dict[str, Any]],
        fallback_candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not fallback_candidates:
            return candidates
        present_types = {str(item.get("asset_type", "")) for item in candidates}
        missing_fallbacks = [
            item
            for item in fallback_candidates
            if str(item.get("asset_type", "")) not in present_types
        ]
        if not missing_fallbacks:
            return candidates
        seen_refs = {str(item.get("reference", "")) for item in candidates}
        merged = list(candidates)
        for item in missing_fallbacks:
            ref = str(item.get("reference", ""))
            if ref and ref in seen_refs:
                continue
            merged.append(item)
            if ref:
                seen_refs.add(ref)
        return merged

    def _replace_unusable_figure_candidates(
        self,
        candidates: list[dict[str, Any]],
        fallback_candidates: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        fallback_figures = [
            item
            for item in fallback_candidates
            if item.get("asset_type") == "figure" and self._figure_has_existing_image(item)
        ]
        if not fallback_figures:
            return candidates

        replacements = list(fallback_figures)
        updated: list[dict[str, Any]] = []
        for item in candidates:
            if item.get("asset_type") == "figure" and not self._figure_has_existing_image(item):
                if replacements:
                    updated.append(replacements.pop(0))
                continue
            updated.append(item)

        seen_refs = {str(item.get("reference", "")) for item in updated}
        for item in replacements:
            ref = str(item.get("reference", ""))
            if ref and ref not in seen_refs:
                updated.append(item)
                seen_refs.add(ref)
        return updated

    def _figure_has_existing_image(self, item: dict[str, Any]) -> bool:
        if item.get("asset_type") != "figure":
            return True
        for path in item.get("image_paths_abs", []) or []:
            try:
                if Path(str(path)).exists():
                    return True
            except OSError:
                continue
        return False

    def _select_primary_media_items(self, media_items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        selected: list[dict[str, Any]] = []
        formula_count = 0
        figure_count = 0
        table_count = 0
        for item in media_items:
            asset_type = item["asset_type"]
            if asset_type == "formula" and formula_count >= 2:
                continue
            if asset_type == "figure" and figure_count >= 1:
                continue
            if asset_type == "table" and table_count >= 1:
                continue
            selected.append(item)
            if asset_type == "formula":
                formula_count += 1
            elif asset_type == "figure":
                figure_count += 1
            elif asset_type == "table":
                table_count += 1
            if len(selected) >= 4:
                break
        return selected

    def _select_supplementary_media_items(
        self,
        media_items: list[dict[str, Any]],
        primary_items: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        primary_refs = {str(item.get("reference", "")) for item in primary_items}
        supplementary: list[dict[str, Any]] = []
        for item in media_items:
            if str(item.get("reference", "")) in primary_refs:
                continue
            supplementary.append(item)
            if len(supplementary) >= 3:
                break
        return supplementary

    def _assign_display_labels(self, media_items: list[dict[str, Any]]) -> None:
        formula_idx = 1
        figure_idx = 1
        for item in media_items:
            asset_type = item["asset_type"]
            if asset_type == "formula":
                item["display_label"] = f"式{self._to_chinese_numeral(formula_idx)}"
                formula_idx += 1
            elif asset_type == "table":
                item["display_label"] = f"表{self._to_chinese_numeral(figure_idx)}"
                figure_idx += 1
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

    def _score_media_item(self, item: dict[str, Any], *, question: str) -> float:
        score = 10.0
        question_tokens = self._extract_query_tokens(question)
        haystack_parts = [
            str(item.get("text", "") or ""),
            str(item.get("caption", "") or ""),
            str(item.get("analysis_hint", "") or ""),
            str(item.get("visual_summary", "") or ""),
            str(item.get("node_name", "") or ""),
            str(item.get("relation_statement", "") or ""),
            str(item.get("formula_meaning", "") or ""),
            " ".join(str(x) for x in (item.get("retrieval_keywords", []) or [])),
            " ".join(str(x) for x in (item.get("domain_terms", []) or [])),
            " ".join(str(x) for x in (item.get("variables", []) or [])),
            str(item.get("chapter_title", "") or ""),
            str(item.get("asset_anchor_node_name", "") or ""),
        ]
        haystack = " ".join(part for part in haystack_parts if part)
        overlap_count = 0
        for token in question_tokens:
            if token in haystack:
                overlap_count += 1
                score += 1.2
        score += min(overlap_count * 0.45, 2.25)

        role = str(item.get("node_role", "") or "")
        score += {
            "primary": 2.2,
            "prerequisite": 2.0,
            "supporting": 1.7,
            "comparison": 1.2,
        }.get(role, 0.5)

        node_id = str(item.get("node_id", "") or "")
        asset_anchor_node_id = str(item.get("asset_anchor_node_id", "") or "")
        node_link_score = float(item.get("node_link_score", 0.0) or 0.0)
        if node_id and node_id == asset_anchor_node_id:
            score += 3.2
        elif node_link_score >= 14:
            score += 1.8
        elif node_link_score >= 11:
            score += 0.9
        else:
            score -= 0.6
        if role == "primary" and asset_anchor_node_id and asset_anchor_node_id != node_id:
            score -= 1.6

        if item["asset_type"] == "formula":
            score += 1.8
            if any(token in question for token in ["公式", "关系", "阻尼比", "超调量", "时间", "峰值"]):
                score += 1.2
            if item.get("formula_meaning"):
                score += 0.8
            if self._contains_all(haystack, ["超调量", "阻尼比"]):
                score += 2.2
            if "超调量" in question and "超调量" not in haystack:
                score -= 1.1
            if "阻尼比" in question and "阻尼比" not in haystack and "\\zeta" not in haystack:
                score -= 1.1
        else:
            caption = str(item.get("caption", "") or "")
            visual_type = str(item.get("visual_type", "") or "")
            if any(keyword in caption for keyword in ["响应曲线", "单位阶跃", "性能指标", "超调量", "关系曲线"]):
                score += 2.2
            if visual_type == "trend_curve":
                score += 0.8
            if any(keyword in caption for keyword in ["结构图", "原理图", "框图"]) and not any(
                token in question for token in ["结构", "原理", "框图"]
            ):
                score -= 3.0
            if "斜坡误差" in caption and not any(token in question for token in ["斜坡", "误差"]):
                score -= 2.4
            if "超调量" in question and "超调量" not in haystack and "\\sigma" not in haystack:
                score -= 1.0
            if "阻尼比" in question and "阻尼比" not in haystack and "\\zeta" not in haystack:
                score -= 1.0
            if self._contains_all(haystack, ["超调量", "阻尼比"]):
                score += 2.4
            if item.get("visual_summary"):
                score += 0.8

        score += min(float(item.get("confidence", 0.0) or 0.0), 1.0)
        score -= int(item.get("hop", 99)) * 0.6
        return round(score, 4)

    def _contains_all(self, text: str, needles: list[str]) -> bool:
        return all(needle in text for needle in needles)

    def _build_analysis_hint_from_asset(self, asset: dict[str, Any]) -> str:
        asset_type = str(asset.get("asset_type", "") or "")
        title = str(asset.get("title_text", "") or asset.get("caption_text", "") or "").strip()
        if asset_type == "formula":
            meaning = str(asset.get("formula_meaning", "") or "").strip()
            if meaning:
                return meaning
            if title:
                return f"可结合{title}中的变量关系解释系统特性。"
            return "可结合公式中的变量关系解释系统特性。"
        relation_statement = str(asset.get("relation_statement", "") or "").strip()
        if relation_statement:
            return relation_statement
        if title:
            return f"可结合{title}中的曲线走势、关键拐点或结构特征进行分析。"
        return "可结合图形走势、关键拐点或结构特征进行分析。"

    def _build_analysis_hint_from_media_item(self, item: dict[str, Any]) -> str:
        node_name = str(item.get("node_name", "")).strip() or "当前知识点"
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

    def _load_annotated_assets(self) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        for path in self._resolve_annotated_asset_files():
            try:
                for line in path.read_text(encoding="utf-8").splitlines():
                    if not line.strip():
                        continue
                    try:
                        item = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if isinstance(item, dict):
                        results.append(item)
            except Exception:
                continue
        return results

    def _resolve_annotated_asset_files(self) -> list[Path]:
        target = resolve_existing_path(self.annotated_assets_path) or self.annotated_assets_path
        if not target.exists():
            return []
        if target.is_file():
            return [target]

        files: list[Path] = []
        summary_path = target / "batch_summary.json"
        if summary_path.exists():
            try:
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
                for chapter in summary.get("chapters", []) or []:
                    annotated_path = resolve_existing_path(chapter.get("annotated_path", "") or "", base_dir=target)
                    if annotated_path is not None and annotated_path not in files:
                        files.append(annotated_path)
            except Exception:
                pass

        for pattern in ("*_annotated_assets.jsonl", "chapter03_annotated_assets.jsonl"):
            for path in sorted(target.glob(pattern)):
                if path.exists() and path not in files:
                    files.append(path)
        return files

    def _match_asset_to_node(self, asset: dict[str, Any], node_id: str) -> dict[str, Any]:
        anchor_id = str(asset.get("anchor_node_id", "") or "").strip()
        if anchor_id == node_id:
            return {"matched": True, "kind": "anchor", "link_score": 99.0}
        linked_ids = [str(item).strip() for item in (asset.get("linked_node_ids", []) or [])]
        link_scores = [float(score or 0.0) for score in (asset.get("link_scores", []) or [])]
        for idx, linked_id in enumerate(linked_ids):
            if linked_id != node_id:
                continue
            score = link_scores[idx] if idx < len(link_scores) else 0.0
            return {"matched": True, "kind": "linked", "link_score": score}
        return {"matched": False, "kind": "", "link_score": 0.0}

    def _load_chapter_docs(self) -> list[dict[str, Any]]:
        docs: list[dict[str, Any]] = []
        root = resolve_existing_path(self.mineru_cache_root) or resolve_project_path(self.mineru_cache_root)
        if not root.exists():
            return docs

        for item in root.iterdir():
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

            page_range = self._extract_page_range(str(manifest.get("pdf_name", "") or item.name))
            if page_range is None:
                continue
            manifest["cache_dir"] = str(item.resolve())
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
        exact_matches = [doc for doc in self.chapter_docs if doc["start_page"] == start_page and doc["end_page"] == end_page]
        if exact_matches:
            return max(exact_matches, key=lambda doc: self._doc_quality_score(doc))
        containing_matches = [doc for doc in self.chapter_docs if doc["start_page"] <= start_page <= doc["end_page"]]
        if containing_matches:
            return max(containing_matches, key=lambda doc: self._doc_quality_score(doc))
        return None

    def _doc_quality_score(self, doc: dict[str, Any]) -> float:
        manifest = doc.get("manifest", {}) or {}
        images = manifest.get("images", {}) or {}
        cache_dir = str(manifest.get("cache_dir", "") or doc.get("cache_dir", "") or "")
        full_md = str(doc.get("full_md", "") or "")
        score = 0.0
        score += min(len(full_md) / 1000.0, 80.0)
        score += min(len(images), 80) * 1.5
        if "content_list" in " ".join(str(path) for path in (manifest.get("json_files", []) or [])):
            score += 10.0
        if re.search(r"chapter_\d+_p\d+-\d+", cache_dir):
            score += 25.0
        if re.search(r"chapter_p\d+-\d+", cache_dir):
            score -= 20.0
        return score

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
                    "caption": "",
                }
            )
        return results

    def _collect_figure_items(self, node: dict[str, Any], doc: dict[str, Any] | None) -> list[dict[str, Any]]:
        if not doc:
            return []

        scope_text = self._extract_node_scope_text(node, doc)
        figures = self._extract_figures_from_block(scope_text, doc["manifest"]) if scope_text else []
        if not figures:
            figures = self._extract_chapter_fallback_figures(node, doc)
        return self._build_figure_media_items(node, figures)

    def _build_figure_media_items(self, node: dict[str, Any], figures: list[dict[str, Any]]) -> list[dict[str, Any]]:
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
                    "text": "",
                }
            )
        return results

    def _collect_table_items(self, node: dict[str, Any], doc: dict[str, Any] | None) -> list[dict[str, Any]]:
        if not doc:
            return []
        scope_text = self._extract_node_scope_text(node, doc)
        if not scope_text:
            return []
        tables = self._extract_tables_from_block(scope_text)
        results: list[dict[str, Any]] = []
        for idx, table in enumerate(tables[:2], start=1):
            results.append(
                {
                    "node_id": str(node.get("node_id", "")),
                    "node_name": str(node.get("name", "")),
                    "asset_type": "table",
                    "reference": f"{node.get('node_id', '')}.table_asset[{idx}]",
                    "caption": table.get("caption", "相关表格"),
                    "text": table.get("text", ""),
                }
            )
        return results

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
        retrieval_keywords = [str(keyword).strip() for keyword in (extra.get("retrieval_keywords", []) or []) if str(keyword).strip()]
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
        page_refs = node.get("page_refs", []) or []
        lines = full_md.splitlines()

        if node_role not in {"chapter_anchor", ""} and node_name:
            section_match = self._extract_named_section(lines, node_name)
            if section_match:
                return section_match

        if page_refs:
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

    def _extract_tables_from_block(self, block_text: str) -> list[dict[str, str]]:
        tables: list[dict[str, str]] = []
        for idx, match in enumerate(re.finditer(r"<table\b.*?</table>", block_text, flags=re.IGNORECASE | re.DOTALL), start=1):
            raw_table = match.group(0).strip()
            if raw_table:
                tables.append({"caption": f"相关表格 {idx}", "text": raw_table})
        return tables

    def _extract_chapter_fallback_figures(self, node: dict[str, Any], doc: dict[str, Any]) -> list[dict[str, Any]]:
        full_md = str(doc.get("full_md", "") or "")
        if not full_md:
            return []
        candidates = self._extract_figures_from_block(full_md, doc["manifest"])
        if not candidates:
            return []

        query_terms = self._chapter_figure_query_terms(node)
        ranked: list[tuple[float, int, dict[str, Any]]] = []
        for idx, figure in enumerate(candidates):
            caption = str(figure.get("caption", "") or "")
            score = self._score_chapter_fallback_figure(caption, query_terms)
            if score <= 0:
                continue
            ranked.append((score, idx, figure))
        if not ranked:
            return candidates[:1]
        ranked.sort(key=lambda item: (-item[0], item[1]))
        return [figure for _, _, figure in ranked[:3]]

    def _chapter_figure_query_terms(self, node: dict[str, Any]) -> list[str]:
        terms: list[str] = []

        def add(value: Any) -> None:
            if isinstance(value, list):
                for item in value:
                    add(item)
                return
            text = str(value or "").strip()
            if not text:
                return
            for part in re.findall(r"[\u4e00-\u9fff]{2,}|[A-Za-z][A-Za-z0-9_%\-]{1,}|\d+-\d+", text):
                if part not in terms:
                    terms.append(part)
            compact = re.sub(r"\s+", "", text)
            if 2 <= len(compact) <= 16 and compact not in terms:
                terms.append(compact)

        extra = node.get("extra", {}) or {}
        add(node.get("name", ""))
        add(node.get("tags", []))
        add(node.get("core_concepts", []))
        add(extra.get("retrieval_keywords", []))
        add(extra.get("matched_block_title", ""))
        add(extra.get("retrieval_matched_block_title", ""))
        return terms[:24]

    def _score_chapter_fallback_figure(self, caption: str, query_terms: list[str]) -> float:
        normalized_caption = re.sub(r"\s+", "", str(caption or ""))
        if not normalized_caption:
            return 0.0
        score = 0.0
        if self._looks_like_figure_caption(normalized_caption):
            score += 2.0
        for term in query_terms:
            compact = re.sub(r"\s+", "", str(term or ""))
            if len(compact) < 2:
                continue
            if compact in normalized_caption or normalized_caption in compact:
                score += min(len(compact), 8) * 0.5
        figure_keywords = ["框图", "方框图", "结构", "原理", "系统", "反馈", "响应", "曲线", "特性", "流程"]
        for keyword in figure_keywords:
            if keyword in normalized_caption:
                score += 0.7
        return score

    def _extract_figures_from_block(self, block_text: str, manifest: dict[str, Any]) -> list[dict[str, Any]]:
        figures: list[dict[str, Any]] = []
        lines = block_text.splitlines()
        pending_paths: list[str] = []

        def flush_pending(caption: str) -> None:
            nonlocal pending_paths
            resolved = self._resolve_image_paths(pending_paths, manifest)
            cleaned_caption = self._clean_caption(caption) or "相关图表"
            if resolved and not self._looks_like_qr_guide_image(cleaned_caption, pending_paths):
                figures.append({"caption": cleaned_caption, "image_paths_abs": resolved})
            pending_paths = []

        for idx, raw in enumerate(lines):
            line = (raw or "").strip()
            if not line:
                continue

            image_paths = re.findall(r"!\[.*?\]\((.*?)\)", line)
            if image_paths:
                alt_texts = [alt.strip() for alt in re.findall(r"!\[(.*?)\]\(.*?\)", line) if alt.strip()]
                inline_caption = self._clean_caption(re.sub(r"!\[.*?\]\((.*?)\)", "", line))
                if pending_paths and (inline_caption or alt_texts):
                    flush_pending(inline_caption or alt_texts[0])
                pending_paths.extend(image_paths)
                caption = inline_caption or (alt_texts[0] if alt_texts and self._looks_like_figure_caption(alt_texts[0]) else "")
                if caption:
                    flush_pending(caption)
                continue

            if pending_paths and self._looks_like_figure_caption(line):
                caption_parts = []
                previous_non_empty = ""
                for lookbehind in reversed(lines[max(0, idx - 3) : idx]):
                    candidate = (lookbehind or "").strip()
                    if candidate:
                        previous_non_empty = candidate
                        break
                if previous_non_empty and not previous_non_empty.startswith("!") and not self._looks_like_figure_caption(previous_non_empty):
                    caption_parts.append(previous_non_empty)
                caption_parts.append(line)
                flush_pending(" ".join(caption_parts))
                continue

            if pending_paths:
                next_non_empty = ""
                upcoming_caption = ""
                for lookahead in lines[idx : min(idx + 4, len(lines))]:
                    candidate = (lookahead or "").strip()
                    if not candidate:
                        continue
                    if not next_non_empty:
                        next_non_empty = candidate
                    if self._looks_like_figure_caption(candidate):
                        upcoming_caption = candidate
                        break
                if upcoming_caption:
                    flush_pending(upcoming_caption)
                    continue
                flush_pending(next_non_empty or "相关图表")
        if pending_paths:
            flush_pending("相关图表")
        return figures

    def _resolve_image_paths(self, image_paths: list[str], manifest: dict[str, Any]) -> list[str]:
        resolved: list[str] = []
        images = manifest.get("images", {}) or {}
        cache_dir = Path(str(manifest.get("cache_dir", self.mineru_cache_root)))

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

            image_name = Path(trimmed).name
            if abs_path is None:
                candidate = resolve_existing_path(image_name, base_dir=cache_dir / "images")
            else:
                candidate = resolve_existing_path(abs_path, base_dir=cache_dir)
                if candidate is None:
                    candidate = resolve_existing_path(image_name, base_dir=cache_dir / "images")

            if candidate is not None:
                candidate_text = str(candidate)
                if candidate_text not in resolved:
                    resolved.append(candidate_text)
        return resolved

    def _looks_like_formula(self, text: str) -> bool:
        if not text:
            return False
        cjk_count = len(re.findall(r"[\u4e00-\u9fff]", text))
        if cjk_count > 12 and "\\tag" not in text:
            return False
        patterns = [
            r"\\tag",
            r"\\frac|\\dot|\\sum|\\omega|\\sigma|\\Phi|\\zeta",
            r"[A-Za-z]\s*\(.*?\)\s*=",
            r"[A-Za-z]\s*=",
            r"\b[eEsSzZ]\b",
        ]
        if any(re.search(pattern, text) for pattern in patterns):
            return True
        return "=" in text and any(ch in text for ch in ["+", "-", "/", "^"])

    def _looks_like_figure_caption(self, text: str) -> bool:
        return bool(re.search(r"(图|Figure|Fig\.)\s*[\d\-]+", text, flags=re.IGNORECASE))

    def _looks_like_qr_guide_image(self, caption: str, image_paths: list[str]) -> bool:
        haystack = " ".join([caption, *[Path(str(path)).name for path in image_paths]]).lower()
        qr_keywords = [
            "二维码",
            "扫码",
            "扫一扫",
            "qr",
            "qrcode",
            "本章导学",
            "导学",
            "微课",
            "视频",
        ]
        if any(keyword.lower() in haystack for keyword in qr_keywords):
            return True
        return bool(image_paths) and not self._looks_like_figure_caption(caption)

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
        current: list[str] = []
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

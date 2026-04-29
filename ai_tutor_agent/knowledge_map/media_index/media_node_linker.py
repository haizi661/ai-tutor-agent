from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

import pandas as pd

from ai_tutor_agent.knowledge_map.config.media_index_config import MediaIndexConfig
from ai_tutor_agent.knowledge_map.schema.media_asset_schema import (
    normalize_linked_media_asset,
    normalize_raw_media_candidate,
)
from ai_tutor_agent.platform_paths import resolve_project_path


class MediaNodeLinker:
    def __init__(
        self,
        *,
        nodes_csv_path: str | Path = "data/knowledge_map_outputs/auto_control_knowledge_map_v2_nodes.csv",
        config: MediaIndexConfig | None = None,
    ) -> None:
        self.config = config or MediaIndexConfig()
        self.nodes_csv_path = resolve_project_path(nodes_csv_path)
        self.nodes = self.load_nodes()

    def load_nodes(self) -> list[dict[str, Any]]:
        if not self.nodes_csv_path.exists():
            return []
        df = pd.read_csv(self.nodes_csv_path)
        records = df.to_dict(orient="records")
        return [self._parse_node_record(record) for record in records]

    def link_candidates(
        self,
        candidates: list[dict[str, Any]],
        *,
        top_k: int = 3,
        min_score: float = 2.4,
    ) -> list[dict[str, Any]]:
        linked_assets: list[dict[str, Any]] = []
        for raw_candidate in candidates:
            candidate = normalize_raw_media_candidate(raw_candidate)
            ranked = self._rank_candidate_nodes(candidate)
            kept = [(node, score) for node, score in ranked[:top_k] if score >= min_score]

            linked = normalize_linked_media_asset(candidate)
            linked["linked_node_ids"] = [node["node_id"] for node, _ in kept]
            linked["linked_node_names"] = [str(node.get("name", "") or "") for node, _ in kept]
            linked["link_scores"] = [round(score, 4) for _, score in kept]
            if kept:
                linked["anchor_node_id"] = kept[0][0]["node_id"]
                linked["anchor_node_name"] = str(kept[0][0].get("name", "") or "")
            linked_assets.append(linked)
        return linked_assets

    def write_jsonl(self, candidates: list[dict[str, Any]], output_path: str | Path | None = None) -> Path:
        target = resolve_project_path(output_path or (self.config.output_dir / self.config.linked_candidates_filename))
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8") as fh:
            for item in candidates:
                fh.write(json.dumps(item, ensure_ascii=False) + "\n")
        return target.resolve()

    def _rank_candidate_nodes(self, candidate: dict[str, Any]) -> list[tuple[dict[str, Any], float]]:
        ranked: list[tuple[dict[str, Any], float]] = []
        for node in self.nodes:
            score = self._score_node_link(candidate, node)
            if score > 0:
                ranked.append((node, score))
        ranked.sort(key=lambda item: (-item[1], item[0].get("node_id", "")))
        return ranked

    def _score_node_link(self, candidate: dict[str, Any], node: dict[str, Any]) -> float:
        candidate_text = self._build_candidate_main_text(candidate)
        candidate_doc_keys = self._candidate_doc_keys(candidate)
        score = 0.0

        node_extra = node.get("extra", {}) or {}
        doc_score = self._score_document_signal(candidate_doc_keys, node_extra)
        score += doc_score

        chapter_title = str(candidate.get("chapter_title", "") or "").strip()
        node_chapter = str(node.get("chapter", "") or "").strip()
        node_page_range = node_extra.get("chapter_page_range", []) if isinstance(node_extra, dict) else []
        if chapter_title and node_chapter and self._text_overlap(chapter_title, node_chapter):
            score += 1.6
        if isinstance(node_page_range, list) and node_page_range and candidate.get("page_range"):
            score += 0.4

        block_titles = [
            str(node_extra.get("matched_block_title", "") or "").strip(),
            str(node_extra.get("retrieval_matched_block_title", "") or "").strip(),
            str(node.get("name", "") or "").strip(),
        ]
        title_match_score = 0.0
        for title in block_titles:
            if not title:
                continue
            title_variants = [title, self._strip_leading_section_number(title)]
            for variant in title_variants:
                if len(variant) >= 2 and variant in candidate_text:
                    current_score = 4.0 if variant == title else 3.2
                    title_match_score = max(title_match_score, current_score)
                    score += current_score
                    break

        node_terms = self._extract_node_terms(node)
        for term, weight in node_terms:
            if len(term) < 2:
                continue
            if term in candidate_text:
                score += weight

        candidate_tokens = self._extract_tokens(candidate_text)
        node_tokens = self._extract_tokens(
            " ".join(term for term, _ in node_terms)
        )
        overlap = candidate_tokens & node_tokens
        if overlap:
            score += min(len(overlap) * 0.45, 3.0)

        role = str(node_extra.get("node_role", "") or "").strip()
        score += self._role_adjustment(role, title_match_score=title_match_score, overlap_count=len(overlap))
        importance = str(node.get("importance_level", "") or "").strip()
        if importance == "核心":
            score += 0.35
        elif importance == "重要":
            score += 0.2

        return round(score, 6)

    def _build_candidate_main_text(self, candidate: dict[str, Any]) -> str:
        pieces = [
            str(candidate.get("caption_text", "") or ""),
            str(candidate.get("nearby_text", "") or ""),
            str(candidate.get("raw_text", "") or ""),
        ]
        text = " ".join(piece.strip() for piece in pieces if piece and piece.strip())
        return self._normalize_text(text)

    def _candidate_doc_keys(self, candidate: dict[str, Any]) -> set[str]:
        keys: set[str] = set()
        for raw in [
            candidate.get("source_doc_name"),
            candidate.get("source_doc_id"),
            Path(str(candidate.get("source_path", "") or "")).parent.parent.name,
        ]:
            normalized = self._normalize_doc_key(raw)
            if normalized:
                keys.add(normalized)
        return keys

    def _score_document_signal(self, candidate_doc_keys: set[str], node_extra: dict[str, Any]) -> float:
        if not candidate_doc_keys or not isinstance(node_extra, dict):
            return 0.0

        node_doc_keys: set[str] = set()
        for raw in [
            node_extra.get("mineru_doc_name"),
            node_extra.get("retrieval_source_pdf"),
        ]:
            normalized = self._normalize_doc_key(raw)
            if normalized:
                node_doc_keys.add(normalized)

        if not node_doc_keys:
            return 0.0
        if candidate_doc_keys & node_doc_keys:
            return 5.5
        for candidate_key in candidate_doc_keys:
            for node_key in node_doc_keys:
                if candidate_key and node_key and (candidate_key in node_key or node_key in candidate_key):
                    return 4.0
        return 0.0

    def _extract_node_terms(self, node: dict[str, Any]) -> list[tuple[str, float]]:
        extra = node.get("extra", {}) or {}
        weighted_terms: list[tuple[str, float]] = []

        def add_terms(values: Any, weight: float) -> None:
            if isinstance(values, list):
                iterable = values
            else:
                iterable = [values]
            for value in iterable:
                text = str(value or "").strip()
                if not text:
                    continue
                normalized = self._normalize_text(text)
                if normalized and all(existing != normalized for existing, _ in weighted_terms):
                    weighted_terms.append((normalized, weight))

        add_terms(node.get("name"), 4.5)
        add_terms(self._strip_leading_section_number(str(node.get("name", "") or "")), 3.2)
        add_terms(node.get("summary"), 1.6)
        add_terms(node.get("core_concepts", []), 2.8)
        add_terms(node.get("key_points", [])[:2], 1.2)
        add_terms(node.get("formulas", [])[:2], 1.6)
        add_terms(extra.get("retrieval_keywords", []), 2.3)
        add_terms(extra.get("matched_block_title"), 4.2)
        add_terms(self._strip_leading_section_number(str(extra.get("matched_block_title", "") or "")), 3.6)
        add_terms(extra.get("retrieval_matched_block_title"), 3.8)
        add_terms(self._strip_leading_section_number(str(extra.get("retrieval_matched_block_title", "") or "")), 3.2)
        add_terms(extra.get("resolved_related_names", []), 1.0)
        add_terms(extra.get("resolved_prerequisite_names", []), 0.8)
        return weighted_terms

    def _role_adjustment(self, role: str, *, title_match_score: float, overlap_count: int) -> float:
        if role == "topic":
            return 1.0 + min(title_match_score * 0.15, 0.8)
        if role == "chapter_anchor":
            if title_match_score > 0:
                return 0.25
            if overlap_count >= 4:
                return -0.2
            return -1.35
        if role:
            return 0.15
        return 0.0

    def _parse_node_record(self, record: dict[str, Any]) -> dict[str, Any]:
        parsed = dict(record)
        list_like_fields = [
            "tags",
            "core_concepts",
            "key_points",
            "formulas",
            "examples",
            "figures_refs",
            "page_refs",
            "definition_candidates",
            "key_point_candidates",
            "formula_candidates",
            "example_candidates",
            "prerequisite_nodes",
            "next_nodes",
            "related_nodes",
            "application_nodes",
            "recommended_next_nodes",
        ]
        for field in list_like_fields:
            parsed[field] = self._safe_parse_literal(parsed.get(field), default=[])
        parsed["extra"] = self._safe_parse_literal(parsed.get("extra"), default={})
        return parsed

    def _safe_parse_literal(self, value: Any, default: Any) -> Any:
        if isinstance(value, (list, dict)):
            return value
        if value is None:
            return default
        text = str(value).strip()
        if not text:
            return default
        try:
            return ast.literal_eval(text)
        except Exception:
            return default

    def _normalize_doc_key(self, value: Any) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        text = text.replace("\\", "/")
        text = Path(text).name
        text = re.sub(r"(__[0-9a-f]{8,})", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\.pdf$", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s+", "", text)
        return text.lower()

    def _normalize_text(self, text: str) -> str:
        normalized = str(text or "").strip().lower()
        normalized = re.sub(r"\s+", " ", normalized)
        return normalized

    def _extract_tokens(self, text: str) -> set[str]:
        tokens = set(re.findall(r"[a-zA-Z][a-zA-Z0-9_%\-]*|[\u4e00-\u9fff]{2,}|[0-9]+(?:\.[0-9]+)?|[ζωσξηtpnTs]+", text))
        return {token.lower() for token in tokens if len(token.strip()) >= 1}

    def _strip_leading_section_number(self, text: str) -> str:
        return re.sub(r"^\s*[0-9]+(?:[-.][0-9]+)*\s*", "", str(text or "").strip())

    def _text_overlap(self, left: str, right: str) -> bool:
        left_norm = self._normalize_text(left)
        right_norm = self._normalize_text(right)
        return bool(left_norm and right_norm and (left_norm in right_norm or right_norm in left_norm))

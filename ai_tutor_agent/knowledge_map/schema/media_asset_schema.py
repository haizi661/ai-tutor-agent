from __future__ import annotations

import copy
from typing import Any


RAW_MEDIA_CANDIDATE_TEMPLATE: dict[str, Any] = {
    "asset_id": "",
    "asset_type": "",  # figure / formula / table
    "source_doc_id": "",
    "source_doc_name": "",
    "source_path": "",
    "page_range": [],
    "chapter_title": "",
    "caption_text": "",
    "nearby_text": "",
    "raw_text": "",
    "content_hash": "",
    "extra": {},
}


LINKED_MEDIA_ASSET_TEMPLATE: dict[str, Any] = {
    **RAW_MEDIA_CANDIDATE_TEMPLATE,
    "linked_node_ids": [],
    "linked_node_names": [],
    "link_scores": [],
    "anchor_node_id": "",
    "anchor_node_name": "",
}


ANNOTATED_MEDIA_ASSET_TEMPLATE: dict[str, Any] = {
    **LINKED_MEDIA_ASSET_TEMPLATE,
    "visual_type": "",
    "layout_features": [],
    "evidence_role": "",
    "question_affordances": [],
    "title_text": "",
    "domain_terms": [],
    "variables": [],
    "direct_readable_claims": [],
    "relation_statement": "",
    "formula_meaning": "",
    "retrieval_keywords": [],
    "confidence": 0.0,
    "dedup_group": "",
    "needs_review": False,
    "llm_generated_fields": [],
}


def build_empty_raw_media_candidate() -> dict[str, Any]:
    return copy.deepcopy(RAW_MEDIA_CANDIDATE_TEMPLATE)


def build_empty_linked_media_asset() -> dict[str, Any]:
    return copy.deepcopy(LINKED_MEDIA_ASSET_TEMPLATE)


def build_empty_annotated_media_asset() -> dict[str, Any]:
    return copy.deepcopy(ANNOTATED_MEDIA_ASSET_TEMPLATE)


def normalize_raw_media_candidate(record: dict[str, Any]) -> dict[str, Any]:
    candidate = build_empty_raw_media_candidate()
    candidate.update(copy.deepcopy(record or {}))
    candidate["page_range"] = list(candidate.get("page_range", []) or [])
    candidate["extra"] = copy.deepcopy(candidate.get("extra", {}) or {})
    return candidate


def normalize_linked_media_asset(record: dict[str, Any]) -> dict[str, Any]:
    asset = build_empty_linked_media_asset()
    asset.update(copy.deepcopy(record or {}))
    asset["page_range"] = list(asset.get("page_range", []) or [])
    asset["linked_node_ids"] = list(asset.get("linked_node_ids", []) or [])
    asset["linked_node_names"] = list(asset.get("linked_node_names", []) or [])
    asset["link_scores"] = list(asset.get("link_scores", []) or [])
    asset["extra"] = copy.deepcopy(asset.get("extra", {}) or {})
    return asset


def normalize_annotated_media_asset(record: dict[str, Any]) -> dict[str, Any]:
    asset = build_empty_annotated_media_asset()
    asset.update(copy.deepcopy(record or {}))
    for key in [
        "page_range",
        "linked_node_ids",
        "linked_node_names",
        "link_scores",
        "layout_features",
        "question_affordances",
        "domain_terms",
        "variables",
        "direct_readable_claims",
        "retrieval_keywords",
        "llm_generated_fields",
    ]:
        asset[key] = list(asset.get(key, []) or [])
    asset["extra"] = copy.deepcopy(asset.get("extra", {}) or {})
    return asset

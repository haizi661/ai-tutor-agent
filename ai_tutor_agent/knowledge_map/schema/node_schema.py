from __future__ import annotations

import copy
from typing import Any


NODE_FIELD_GROUPS: dict[str, list[str]] = {
    "basic": [
        "node_id",
        "name",
        "chapter",
        "summary",
        "tags",
        "keep",
        "source_type",
    ],
    "teaching": [
        "requirement_level",
        "mastery_threshold",
        "importance_level",
        "assessment_focus",
        "explanation_raw",
        "explanation_teacher_style",
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
    ],
    "relations": [
        "prerequisite_nodes",
        "next_nodes",
        "related_nodes",
        "application_nodes",
        "recommended_next_nodes",
    ],
    "meta": [
        "extra",
    ],
}


NODE_DEFAULT_TEMPLATE: dict[str, Any] = {
    "node_id": "",
    "name": "",
    "chapter": "",
    "summary": "",
    "tags": [],
    "requirement_level": "",
    "mastery_threshold": 0.0,
    "importance_level": "",
    "assessment_focus": "",
    "explanation_raw": "",
    "explanation_teacher_style": "",
    "core_concepts": [],
    "key_points": [],
    "formulas": [],
    "examples": [],
    "figures_refs": [],
    "page_refs": [],
    "definition_candidates": [],
    "key_point_candidates": [],
    "formula_candidates": [],
    "example_candidates": [],
    "prerequisite_nodes": [],
    "next_nodes": [],
    "related_nodes": [],
    "application_nodes": [],
    "recommended_next_nodes": [],
    "keep": True,
    "source_type": "skeleton",
    "extra": {},
}


EDGE_DEFAULT_TEMPLATE: dict[str, Any] = {
    "edge_id": "",
    "source": "",
    "target": "",
    "relation": "",
    "relation_type": "",
    "relation_label": "",
    "relation_strength": 0.0,
    "direction_type": "undirected",
    "keep": True,
    "weight": 0.0,
    "source_type": "rule",
    "evidence": "",
    "relation_note": "",
    "extra": {},
}


LEGACY_NODE_KEY_MAP: dict[str, str] = {
    "level": "legacy_level",
    "part_of": "legacy_part_of",
}


def build_empty_node() -> dict[str, Any]:
    return copy.deepcopy(NODE_DEFAULT_TEMPLATE)


def build_empty_edge() -> dict[str, Any]:
    return copy.deepcopy(EDGE_DEFAULT_TEMPLATE)


def normalize_node_record(record: dict[str, Any]) -> dict[str, Any]:
    record = copy.deepcopy(record or {})
    extra = copy.deepcopy(record.get("extra", {}) or {})

    for legacy_key, extra_key in LEGACY_NODE_KEY_MAP.items():
        if legacy_key in record:
            extra.setdefault(extra_key, record.pop(legacy_key))

    node = build_empty_node()
    node.update(record)
    node["extra"] = extra
    return node


def normalize_edge_record(record: dict[str, Any]) -> dict[str, Any]:
    edge = build_empty_edge()
    edge.update(copy.deepcopy(record or {}))

    if not edge.get("relation_type"):
        edge["relation_type"] = edge.get("relation", "")
    if not edge.get("relation"):
        edge["relation"] = edge.get("relation_type", "")

    strength = edge.get("relation_strength")
    weight = edge.get("weight")

    if (strength is None or strength == 0.0) and weight not in (None, 0.0):
        edge["relation_strength"] = float(weight)
    elif weight in (None, 0.0) and strength not in (None, 0.0):
        edge["weight"] = float(strength)

    if edge.get("direction_type") not in {"directed", "undirected"}:
        edge["direction_type"] = "undirected"

    return edge

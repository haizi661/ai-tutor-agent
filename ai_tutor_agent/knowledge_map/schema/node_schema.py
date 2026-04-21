from __future__ import annotations

import copy
from typing import Any


# 节点字段分组：后面前端编辑时可以直接按组渲染
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


# 节点默认字段模板
# 已去掉 level / part_of，所有节点统一平权
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


# 边默认字段模板
# 统一字段：所有边都有关系类型、强度、方向，不使用 NaN
EDGE_DEFAULT_TEMPLATE: dict[str, Any] = {
    "edge_id": "",
    "source": "",
    "target": "",
    "relation": "",
    "relation_type": "",
    "relation_label": "",
    "relation_strength": 0.0,
    "direction_type": "undirected",  # directed / undirected
    "keep": True,
    "weight": 0.0,  # 与 relation_strength 保持一致，兼容旧逻辑
    "source_type": "rule",
    "evidence": "",
    "relation_note": "",
    "extra": {},
}


LEGACY_NODE_KEY_MAP: dict[str, str] = {
    "level": "legacy_level",
    "part_of": "legacy_part_of",
}


LEGACY_EDGE_KEY_MAP: dict[str, str] = {
    "weight": "weight",
    "relation": "relation",
}


def build_empty_node() -> dict[str, Any]:
    """构建一个空节点模板。"""
    return copy.deepcopy(NODE_DEFAULT_TEMPLATE)


def build_empty_edge() -> dict[str, Any]:
    """构建一条空边模板。"""
    return copy.deepcopy(EDGE_DEFAULT_TEMPLATE)


def normalize_node_record(record: dict[str, Any]) -> dict[str, Any]:
    """
    用默认模板补齐缺失字段，保证后续 DataFrame / JSON 导出稳定。
    同时把旧版 level / part_of 收纳到 extra 中，避免历史数据直接炸掉。
    """
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
    """
    用默认模板补齐缺失字段，保证后续 DataFrame / JSON 导出稳定。
    relation_type 缺失时回填 relation；weight 与 relation_strength 互相对齐。
    """
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

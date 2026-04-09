from __future__ import annotations

import copy
from typing import Any


# 节点字段分组：后面前端编辑时可以直接按组渲染
NODE_FIELD_GROUPS: dict[str, list[str]] = {
    "basic": [
        "node_id",
        "name",
        "chapter",
        "level",
        "summary",
        "tags",
        "keep",
        "source_type",
    ],
    "teaching": [
        "explanation_raw",
        "explanation_teacher_style",
        "core_concepts",
        "key_points",
        "formulas",
        "examples",
        "figures_refs",
        "page_refs",
    ],
    "relations": [
        "prerequisite_nodes",
        "next_nodes",
        "related_nodes",
        "application_nodes",
        "part_of",
    ],
    "meta": [
        "extra",
    ],
}


# 节点默认字段模板
# 后期你们要改字段名、加字段，优先改这里
NODE_DEFAULT_TEMPLATE: dict[str, Any] = {
    "node_id": "",
    "name": "",
    "chapter": "",
    "level": 1,
    "summary": "",
    "tags": [],
    "explanation_raw": "",
    "explanation_teacher_style": "",
    "core_concepts": [],
    "key_points": [],
    "formulas": [],
    "examples": [],
    "figures_refs": [],
    "page_refs": [],
    "prerequisite_nodes": [],
    "next_nodes": [],
    "related_nodes": [],
    "application_nodes": [],
    "part_of": "",
    "keep": True,
    "source_type": "skeleton",
    "extra": {},
}


# 边默认字段模板
EDGE_DEFAULT_TEMPLATE: dict[str, Any] = {
    "edge_id": "",
    "source": "",
    "target": "",
    "relation": "",
    "relation_label": "",
    "keep": True,
    "weight": 1.0,
    "source_type": "rule",
    "evidence": "",
    "extra": {},
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
    """
    node = build_empty_node()
    node.update(record or {})
    return node


def normalize_edge_record(record: dict[str, Any]) -> dict[str, Any]:
    """
    用默认模板补齐缺失字段，保证后续 DataFrame / JSON 导出稳定。
    """
    edge = build_empty_edge()
    edge.update(record or {})
    return edge
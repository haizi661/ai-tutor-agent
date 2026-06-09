"""Ability Mapper — 8 维能力 ↔ 42 知识点映射 + 自评 → 知识点 mastery 转换。

数据源:data/knowledge_map_outputs/auto_control_knowledge_map_v2_node_metadata.json

核心职责:
1. 读 metadata,缓存到内存
2. 节点元数据查询(主 ability / 难度 / 预估时长 / ability 权重)
3. 8 维自评分数 → 42 节点 mastery 的映射
4. 跳过自评时默认 mastery 提供
5. 6 步模板(step1-step6)的查询
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any


DEFAULT_METADATA_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "knowledge_map_outputs"
    / "auto_control_knowledge_map_v2_node_metadata.json"
)


# ── 加载与缓存 ─────────────────────────────────────────

@lru_cache(maxsize=4)
def _load_metadata(path_str: str = "") -> dict[str, Any]:
    path = Path(path_str) if path_str else DEFAULT_METADATA_PATH
    if not path.exists():
        raise FileNotFoundError(f"节点 metadata 缺失: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def reset_cache() -> None:
    """测试用,清空 lru_cache。"""
    _load_metadata.cache_clear()


def load_metadata(path: str | Path | None = None) -> dict[str, Any]:
    if path is None:
        return _load_metadata()
    return _load_metadata(str(path))


# ── 元数据查询 ─────────────────────────────────────────

def get_ability_names() -> dict[str, str]:
    """返回 8 维 ability 的代码 → 中文名。"""
    return dict(load_metadata().get("abilities", {}))


def get_self_assessment_questions() -> list[dict[str, str]]:
    """返回 8 维自评题目。"""
    return list(load_metadata().get("self_assessment", {}).get("questions", []))


def get_self_assessment_scale() -> dict[str, str]:
    return dict(load_metadata().get("self_assessment", {}).get("scale", {}))


def get_node_meta(node_id: str) -> dict[str, Any]:
    """返回单个节点的全部 metadata。"""
    return dict(load_metadata()["nodes"].get(node_id, {}))


def get_node_primary_ability(node_id: str) -> str:
    return str(get_node_meta(node_id).get("primary_ability", ""))


def get_node_difficulty(node_id: str) -> int:
    return int(get_node_meta(node_id).get("difficulty", 3))


def get_node_estimated_time(node_id: str) -> int:
    return int(get_node_meta(node_id).get("estimated_time_min", 30))


def get_node_ability_weights(node_id: str) -> dict[str, float]:
    return dict(get_node_meta(node_id).get("ability_weights", {}))


def get_node_importance(node_id: str) -> str:
    return str(get_node_meta(node_id).get("importance", "supporting"))


def get_nodes_for_ability(ability: str) -> list[str]:
    """返回属于某 ability 的所有节点(按主 ability 判)。"""
    nodes = load_metadata()["nodes"]
    return [nid for nid, m in nodes.items() if m.get("primary_ability") == ability]


def get_all_node_ids() -> list[str]:
    return list(load_metadata()["nodes"].keys())


def get_node_name_map() -> dict[str, str]:
    """Lazily load v2.json and return node_id → Chinese name mapping."""
    return dict(_load_v2_node_names())


@lru_cache(maxsize=2)
def _load_v2_node_names(path_str: str = "") -> dict[str, str]:
    DEFAULT_V2_PATH = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "knowledge_map_outputs"
        / "auto_control_knowledge_map_v2.json"
    )
    path = Path(path_str) if path_str else DEFAULT_V2_PATH
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    nodes = payload.get("nodes", [])
    return {n["node_id"]: n.get("name", n["node_id"]) for n in nodes if isinstance(n, dict)}


@lru_cache(maxsize=2)
def _load_v2_node_chapters(path_str: str = "") -> dict[str, str]:
    DEFAULT_V2_PATH = (
        Path(__file__).resolve().parents[2]
        / "data"
        / "knowledge_map_outputs"
        / "auto_control_knowledge_map_v2.json"
    )
    path = Path(path_str) if path_str else DEFAULT_V2_PATH
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    nodes = payload.get("nodes", [])
    return {n["node_id"]: str(n.get("chapter", "") or "") for n in nodes if isinstance(n, dict)}


def get_node_chapter_map() -> dict[str, str]:
    """返回 node_id → chapter 映射(从 V2 JSON 动态加载)。"""
    return dict(_load_v2_node_chapters())


# ── 6 步模板 ─────────────────────────────────────────

def get_step_templates() -> dict[str, dict[str, Any]]:
    return dict(load_metadata().get("step_templates", {}))


def get_step_template_ids() -> list[str]:
    return list(load_metadata().get("step_templates", {}).keys())


def get_step_template_nodes(template_id: str) -> list[str]:
    tpl = get_step_templates().get(template_id, {})
    return list(tpl.get("node_ids", []))


# ── 自评分数 → 知识点 mastery 映射 ────────────────────

def map_self_scores_to_concept_mastery(
    self_scores: dict[str, int],
) -> dict[str, dict[str, Any]]:
    """将 8 维自评分数(1-5)转成 42 节点的 mastery 初始值。

    规则:
    - 对每个 ability 维度分(1-5)
    - 遍历所有节点,该 ability 权重 > 0 的节点都会受影响
    - mastery = sum(score[ability] * weight[node][ability]) / 5
      等价于"按 ability 加权平均"
    - confidence = 0.3(自评统一低置信度)
    - source = "self_assessment"

    例:学生系统建模分 4、根轨迹分 1,则:
    - KM007(建模权重 0.7, 根轨迹权重 0)→ mastery = (4 * 0.7 + 1 * 0) / 5 = 0.56
    - KM020(根轨迹权重 1)→ mastery = (4 * 0 + 1 * 1) / 5 = 0.20
    """
    if not self_scores:
        return {}

    confidence = float(load_metadata().get("self_assessment", {}).get("confidence_after_self_assessment", 0.3))
    result: dict[str, dict[str, Any]] = {}
    nodes = load_metadata()["nodes"]
    for nid, m in nodes.items():
        weights = m.get("ability_weights", {})
        if not weights:
            continue
        weighted_sum = 0.0
        weight_total = 0.0
        for ability, weight in weights.items():
            score = int(self_scores.get(ability, 0) or 0)
            if score <= 0 or weight <= 0:
                continue
            weighted_sum += score * weight
            weight_total += weight
        if weight_total <= 0:
            continue
        mastery = (weighted_sum / weight_total) / 5.0  # 归一化到 [0, 1]
        mastery = max(0.0, min(1.0, mastery))
        result[nid] = {
            "mastery": round(mastery, 3),
            "confidence": confidence,
            "source": "self_assessment",
            "risk": "low" if mastery >= 0.7 else ("medium" if mastery >= 0.4 else "high"),
        }
    return result


def get_default_scores_when_skipped() -> dict[str, int]:
    """跳过自评时的默认 8 维分数。"""
    return dict(load_metadata().get("self_assessment", {}).get("default_scores_when_skipped", {}))


def get_default_mastery_when_skipped() -> dict[str, dict[str, Any]]:
    """跳过自评时的 42 节点默认 mastery。"""
    default_scores = get_default_scores_when_skipped()
    default_confidence = float(load_metadata().get("self_assessment", {}).get("confidence_default", 0.2))
    if not default_scores:
        return {}
    mapped = map_self_scores_to_concept_mastery(default_scores)
    for entry in mapped.values():
        entry["confidence"] = default_confidence
        entry["source"] = "default"
    return mapped


# ── 能力 → 节点加权的批量查询(给路径生成器用)────────

def ability_to_node_mastery_matrix() -> dict[str, dict[str, float]]:
    """返回 {ability: {node_id: weight}} 反向索引。"""
    matrix: dict[str, dict[str, float]] = {}
    nodes = load_metadata()["nodes"]
    for nid, m in nodes.items():
        for ability, weight in (m.get("ability_weights") or {}).items():
            matrix.setdefault(ability, {})[nid] = float(weight)
    return matrix

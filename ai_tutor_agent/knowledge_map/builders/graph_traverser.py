from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ai_tutor_agent.knowledge_map.config.graph_rag_config import GraphRAGConfig


@dataclass
class TraversedNode:
    node_id: str
    hop: int
    score: float
    via_relation: str
    parent_node_id: str | None
    relation_direction: str
    relation_strength: float = 1.0
    edge_weight: float = 1.0
    relation_note: str = ""
    edge_source_type: str = ""
    direction_type: str = "directed"
    parent_name: str = ""
    relation_reference: str = ""
    relation_evidence: str = ""
    relation_meta: dict[str, Any] = field(default_factory=dict)


class GraphTraverser:
    def __init__(
        self,
        edges: list[dict[str, Any]],
        *,
        node_map: dict[str, dict[str, Any]] | None = None,
        relation_weights: dict[str, float] | None = None,
        config: GraphRAGConfig | None = None,
    ) -> None:
        self.config = config or GraphRAGConfig()
        self.node_map = node_map or {}
        self.relation_weights = relation_weights or self.config.relation_weights
        self.forward_adj: dict[str, dict[str, list[dict[str, Any]]]] = {}
        self.reverse_adj: dict[str, dict[str, list[dict[str, Any]]]] = {}
        self._build_adjacency(edges)

    def traverse(
        self,
        *,
        anchor_nodes: list[dict[str, Any]],
        anchor_terms: list[str],
        question_type: str,
        preferred_relations: list[str],
        max_depth: int,
        node_budget: int,
    ) -> list[TraversedNode]:
        visited: dict[str, TraversedNode] = {}
        frontier: list[tuple[dict[str, Any], int, float, str, str | None, str, dict[str, Any]]] = []
        anchor_term_blob = " ".join(anchor_terms)
        normalized_relations = [self.config.normalize_relation(item) for item in preferred_relations if item]

        for node in anchor_nodes:
            score = self._anchor_match_score(anchor_term_blob, node)
            frontier.append((node, 0, score, "ANCHOR", None, "self", {}))

        while frontier and len(visited) < node_budget:
            frontier.sort(key=lambda item: (item[1], -item[2], str(item[0].get("node_id"))))
            current_node, hop, score, relation, parent_node_id, direction, edge_meta = frontier.pop(0)
            node_id = str(current_node.get("node_id"))
            existing = visited.get(node_id)
            if existing is not None:
                if existing.hop < hop:
                    continue
                if existing.hop == hop and existing.score >= score:
                    continue

            visited[node_id] = TraversedNode(
                node_id=node_id,
                hop=hop,
                score=round(score, 4),
                via_relation=relation,
                parent_node_id=parent_node_id,
                relation_direction=direction,
                relation_strength=self._safe_float(edge_meta.get("relation_strength"), default=1.0),
                edge_weight=self._safe_float(edge_meta.get("weight"), default=1.0),
                relation_note=str(edge_meta.get("relation_note", "") or "").strip(),
                edge_source_type=str(edge_meta.get("source_type", "") or "").strip(),
                direction_type=str(edge_meta.get("direction_type", "") or "directed"),
                parent_name=str(edge_meta.get("parent_name", "") or "").strip(),
                relation_reference=str(edge_meta.get("relation_reference", "") or "").strip(),
                relation_evidence=str(edge_meta.get("evidence", "") or "").strip(),
                relation_meta=dict(edge_meta),
            )

            if hop >= max_depth:
                continue

            for relation_name in normalized_relations:
                if not relation_name:
                    continue
                allowed_directions = self.config.relation_direction_preferences.get(
                    question_type,
                    {},
                ).get(relation_name, ["forward", "reverse"])

                if "forward" in allowed_directions:
                    neighbors = self.forward_adj.get(node_id, {}).get(relation_name, [])
                    for neighbor in neighbors:
                        next_score = self._expand_score(score, relation_name, hop + 1, neighbor)
                        frontier.append((neighbor, hop + 1, next_score, relation_name, node_id, "forward", neighbor))

                if "reverse" in allowed_directions:
                    neighbors = self.reverse_adj.get(node_id, {}).get(relation_name, [])
                    for neighbor in neighbors:
                        next_score = self._expand_score(score, relation_name, hop + 1, neighbor)
                        frontier.append((neighbor, hop + 1, next_score, relation_name, node_id, "reverse", neighbor))

        return sorted(visited.values(), key=lambda item: (item.hop, -item.score, item.node_id))

    def _build_adjacency(self, edges: list[dict[str, Any]]) -> None:
        for edge in edges:
            source = str(edge.get("source", "") or "").strip()
            target = str(edge.get("target", "") or "").strip()
            relation = self.config.normalize_relation(
                edge.get("relation_type") or edge.get("relation") or edge.get("relation_label") or ""
            )
            if not source or not target or not relation:
                continue

            target_node = dict(self.node_map.get(target, {}))
            source_node = dict(self.node_map.get(source, {}))

            payload = dict(target_node)
            payload.update(
                {
                    "node_id": target,
                    "relation": relation,
                    "weight": self._safe_float(edge.get("weight"), default=1.0),
                    "relation_strength": self._safe_float(edge.get("relation_strength"), default=1.0),
                    "direction_type": str(edge.get("direction_type", "") or "").strip().lower() or "directed",
                    "relation_note": str(edge.get("relation_note", "") or "").strip(),
                    "source_type": str(edge.get("source_type", "") or "").strip(),
                    "evidence": str(edge.get("evidence", "") or "").strip(),
                    "relation_reference": str(edge.get("edge_id", "") or "").strip(),
                    "parent_name": str(source_node.get("name", "") or "").strip(),
                }
            )
            self.forward_adj.setdefault(source, {}).setdefault(relation, []).append(payload)

            reverse_payload = dict(source_node)
            reverse_payload.update(
                {
                    "node_id": source,
                    "relation": relation,
                    "weight": self._safe_float(edge.get("weight"), default=1.0),
                    "relation_strength": self._safe_float(edge.get("relation_strength"), default=1.0),
                    "direction_type": str(edge.get("direction_type", "") or "").strip().lower() or "directed",
                    "relation_note": str(edge.get("relation_note", "") or "").strip(),
                    "source_type": str(edge.get("source_type", "") or "").strip(),
                    "evidence": str(edge.get("evidence", "") or "").strip(),
                    "relation_reference": str(edge.get("edge_id", "") or "").strip(),
                    "parent_name": str(target_node.get("name", "") or "").strip(),
                }
            )
            self.reverse_adj.setdefault(target, {}).setdefault(relation, []).append(reverse_payload)

            if payload["direction_type"] == "undirected":
                undirected_payload = dict(source_node)
                undirected_payload.update(
                    {
                        "node_id": source,
                        "relation": relation,
                        "weight": payload["weight"],
                        "relation_strength": payload["relation_strength"],
                        "direction_type": payload["direction_type"],
                        "relation_note": payload["relation_note"],
                        "source_type": payload["source_type"],
                        "evidence": payload["evidence"],
                        "relation_reference": payload["relation_reference"],
                        "parent_name": str(target_node.get("name", "") or "").strip(),
                    }
                )
                self.forward_adj.setdefault(target, {}).setdefault(relation, []).append(undirected_payload)

                reverse_undirected_payload = dict(target_node)
                reverse_undirected_payload.update(
                    {
                        "node_id": target,
                        "relation": relation,
                        "weight": payload["weight"],
                        "relation_strength": payload["relation_strength"],
                        "direction_type": payload["direction_type"],
                        "relation_note": payload["relation_note"],
                        "source_type": payload["source_type"],
                        "evidence": payload["evidence"],
                        "relation_reference": payload["relation_reference"],
                        "parent_name": str(source_node.get("name", "") or "").strip(),
                    }
                )
                self.reverse_adj.setdefault(source, {}).setdefault(relation, []).append(reverse_undirected_payload)

    def _anchor_match_score(self, anchor_term_blob: str, node: dict[str, Any]) -> float:
        tags = node.get("tags", []) or []
        concepts = node.get("core_concepts", []) or []
        extra = node.get("extra", {}) or {}
        retrieval_keywords = extra.get("retrieval_keywords", []) if isinstance(extra, dict) else []
        text = " ".join(
            [
                str(node.get("name", "")),
                str(node.get("chapter", "")),
                str(node.get("summary", "")),
                str(node.get("assessment_focus", "")),
                " ".join(str(item) for item in tags),
                " ".join(str(item) for item in concepts),
                " ".join(str(item) for item in retrieval_keywords),
            ]
        )
        score = 1.0 + self._node_attribute_bonus(node)
        for token in [item for item in anchor_term_blob.split() if item]:
            if token in text:
                score += 1.2
        return score

    def _expand_score(
        self,
        parent_score: float,
        relation_name: str,
        hop: int,
        node: dict[str, Any],
    ) -> float:
        relation_weight = self.relation_weights.get(relation_name, 0.6)
        edge_weight = self._safe_float(node.get("weight"), default=1.0)
        edge_strength = self._safe_float(node.get("relation_strength"), default=1.0)
        hop_penalty = self.config.hop_penalties.get(hop, 1.3)
        direction_bonus = 0.05 if str(node.get("direction_type", "")).lower() == "directed" else 0.0
        semantic_bonus = self._edge_semantic_bonus(node)
        node_bonus = self._node_attribute_bonus(node)
        return (
            parent_score
            + relation_weight * edge_weight * edge_strength
            + direction_bonus
            + semantic_bonus
            + node_bonus
            - hop_penalty
        )

    def _node_attribute_bonus(self, node: dict[str, Any]) -> float:
        bonus = 0.0
        importance = str(node.get("importance_level", "") or "").strip()
        bonus += self.config.important_node_bonus.get(importance, 0.0)
        if node.get("summary"):
            bonus += 0.08
        if node.get("assessment_focus"):
            bonus += 0.08
        if node.get("core_concepts"):
            bonus += 0.1
        if node.get("explanation_teacher_style"):
            bonus += 0.05
        extra = node.get("extra", {}) or {}
        if isinstance(extra, dict) and extra.get("node_role") == "chapter_anchor":
            bonus += 0.06
        return bonus

    def _edge_semantic_bonus(self, node: dict[str, Any]) -> float:
        note = str(node.get("relation_note", "") or "")
        source_type = str(node.get("source_type", "") or "")
        bonus = 0.0
        if "显式配置" in note:
            bonus += 0.12
        if source_type.startswith("config_"):
            bonus += 0.08
        return bonus

    def _safe_float(self, value: Any, *, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

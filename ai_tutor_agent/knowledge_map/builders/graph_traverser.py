from __future__ import annotations

from collections import deque
from dataclasses import dataclass
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


class GraphTraverser:
    def __init__(
        self,
        edges: list[dict[str, Any]],
        relation_weights: dict[str, float] | None = None,
        config: GraphRAGConfig | None = None,
    ) -> None:
        self.config = config or GraphRAGConfig()
        self.relation_weights = relation_weights or self.config.relation_weights
        self.forward_adj = self._build_adjacency(edges, reverse=False)
        self.reverse_adj = self._build_adjacency(edges, reverse=True)

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
        queue: deque[tuple[dict[str, Any], int, float, str, str | None, str]] = deque()
        anchor_term_blob = " ".join(anchor_terms)

        for node in anchor_nodes:
            score = self._anchor_match_score(anchor_term_blob, node)
            queue.append((node, 0, score, "ANCHOR", None, "self"))

        while queue and len(visited) < node_budget:
            current_node, hop, score, relation, parent_node_id, direction = queue.popleft()
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
            )

            if hop >= max_depth:
                continue

            for relation_name in preferred_relations:
                allowed_directions = self.config.relation_direction_preferences.get(
                    question_type,
                    {},
                ).get(relation_name, ["forward", "reverse"])

                if "forward" in allowed_directions:
                    neighbors = self.forward_adj.get(node_id, {}).get(relation_name, [])
                    for neighbor in neighbors:
                        next_score = self._expand_score(score, relation_name, hop + 1, neighbor)
                        queue.append((neighbor, hop + 1, next_score, relation_name, node_id, "forward"))

                if "reverse" in allowed_directions:
                    neighbors = self.reverse_adj.get(node_id, {}).get(relation_name, [])
                    for neighbor in neighbors:
                        next_score = self._expand_score(score, relation_name, hop + 1, neighbor)
                        queue.append((neighbor, hop + 1, next_score, relation_name, node_id, "reverse"))

        return sorted(visited.values(), key=lambda item: (item.hop, -item.score, item.node_id))

    def _build_adjacency(
        self,
        edges: list[dict[str, Any]],
        *,
        reverse: bool,
    ) -> dict[str, dict[str, list[dict[str, Any]]]]:
        graph: dict[str, dict[str, list[dict[str, Any]]]] = {}
        for edge in edges:
            source = str(edge.get("source"))
            target = str(edge.get("target"))
            relation = str(edge.get("relation"))
            left, right = (target, source) if reverse else (source, target)
            graph.setdefault(left, {}).setdefault(relation, []).append({"node_id": right})
        return graph

    def _anchor_match_score(self, anchor_term_blob: str, node: dict[str, Any]) -> float:
        text = " ".join(
            [
                str(node.get("name", "")),
                str(node.get("chapter", "")),
                str(node.get("summary", "")),
                " ".join(str(item) for item in (node.get("tags", []) or [])),
            ]
        )
        score = 1.0
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
        hop_penalty = self.config.hop_penalties.get(hop, 1.5)
        chapter_penalty = 0.0 if node.get("chapter") else 0.2
        return parent_score + relation_weight - hop_penalty - chapter_penalty

from __future__ import annotations

from typing import Any

from ai_tutor_agent.knowledge_map.schema.node_schema import normalize_edge_record


class GraphRelationBuilder:
    """
    根据骨架节点生成第一版规则关系。
    当前阶段先做：
    1. HAS_SUBTOPIC
    2. PRE_REQUIRES
    3. LEADS_TO
    """

    def __init__(self, relation_types: dict[str, str]) -> None:
        self.relation_types = relation_types
        self._edge_counter = 0

    def build_edges(self, nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        edges: list[dict[str, Any]] = []

        level1_nodes = [n for n in nodes if int(n.get("level", 0)) == 1]
        parent_map = {n["node_id"]: n for n in level1_nodes}

        # 1. 包含关系：一级 -> 二级
        for node in nodes:
            if int(node.get("level", 0)) != 2:
                continue
            parent_id = node.get("part_of", "")
            if not parent_id or parent_id not in parent_map:
                continue

            edges.append(
                self._build_edge(
                    source=parent_id,
                    target=node["node_id"],
                    relation="HAS_SUBTOPIC",
                    evidence="rule: parent-child skeleton relation",
                    source_type="rule_has_subtopic",
                )
            )

        # 2. 一级节点的前置/后继关系：按章节顺序串起来
        for i in range(len(level1_nodes) - 1):
            current_node = level1_nodes[i]
            next_node = level1_nodes[i + 1]

            edges.append(
                self._build_edge(
                    source=current_node["node_id"],
                    target=next_node["node_id"],
                    relation="LEADS_TO",
                    evidence="rule: sequential chapter order",
                    source_type="rule_sequence",
                )
            )

            edges.append(
                self._build_edge(
                    source=next_node["node_id"],
                    target=current_node["node_id"],
                    relation="PRE_REQUIRES",
                    evidence="rule: reverse of sequential chapter order",
                    source_type="rule_sequence",
                )
            )

        return edges

    def _next_edge_id(self) -> str:
        self._edge_counter += 1
        return f"E{self._edge_counter:03d}"

    def _build_edge(
        self,
        source: str,
        target: str,
        relation: str,
        evidence: str,
        source_type: str,
        weight: float = 1.0,
    ) -> dict[str, Any]:
        edge = {
            "edge_id": self._next_edge_id(),
            "source": source,
            "target": target,
            "relation": relation,
            "relation_label": self.relation_types.get(relation, relation),
            "weight": weight,
            "source_type": source_type,
            "evidence": evidence,
        }
        return normalize_edge_record(edge)
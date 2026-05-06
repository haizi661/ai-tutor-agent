from __future__ import annotations

from typing import Any

from ai_tutor_agent.knowledge_map.schema.node_schema import normalize_edge_record


class GraphRelationBuilder:
    """
    根据骨架节点生成第一版规则关系。
    当前阶段做：
    1. HAS_SUBTOPIC
    2. PRE_REQUIRES
    3. LEADS_TO
    4. 同章节二级节点顺序关系
    """

    def __init__(self, relation_types: dict[str, str]) -> None:
        self.relation_types = relation_types
        self._edge_counter = 0

    def build_edges(self, nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        edges: list[dict[str, Any]] = []

        level1_nodes = [n for n in nodes if int(n.get("level", 0)) == 1]
        level2_nodes = [n for n in nodes if int(n.get("level", 0)) == 2]

        parent_map = {n["node_id"]: n for n in level1_nodes}

        # 1. 包含关系：一级 -> 二级
        for node in level2_nodes:
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

        # 3. 同一父节点下的二级节点按配置顺序串联
        children_by_parent: dict[str, list[dict[str, Any]]] = {}
        for node in level2_nodes:
            parent_id = node.get("part_of", "")
            if not parent_id:
                continue
            children_by_parent.setdefault(parent_id, []).append(node)

        for parent_id, children in children_by_parent.items():
            for i in range(len(children) - 1):
                current_child = children[i]
                next_child = children[i + 1]

                edges.append(
                    self._build_edge(
                        source=current_child["node_id"],
                        target=next_child["node_id"],
                        relation="LEADS_TO",
                        evidence=f"rule: sibling order under {parent_id}",
                        source_type="rule_subtopic_sequence",
                    )
                )

                edges.append(
                    self._build_edge(
                        source=next_child["node_id"],
                        target=current_child["node_id"],
                        relation="PRE_REQUIRES",
                        evidence=f"rule: reverse sibling order under {parent_id}",
                        source_type="rule_subtopic_sequence",
                    )
                )

        return edges

    def _collect_connected_node_ids(self, edges: list[dict[str, Any]]) -> set[str]:
        connected: set[str] = set()
        for edge in edges:
            source = edge.get("source", "")
            target = edge.get("target", "")
            if source:
                connected.add(source)
            if target:
                connected.add(target)
        return connected

    def _append_edge(
        self,
        edges: list[dict[str, Any]],
        edge: dict[str, Any],
        existing_pairs: set[tuple[str, str, str]],
    ) -> None:
        key = (edge["source"], edge["target"], edge["relation_type"])
        if key in existing_pairs:
            return
        existing_pairs.add(key)
        edges.append(edge)

    def _write_relation_debug_info(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        node_id_map: dict[str, dict[str, Any]],
    ) -> None:
        """
        只回填"事实关系"，不在这里生成学习推荐路径。

        注意 prerequisite_of 的方向：
        source 是前置知识，target 是依赖该前置知识的后续知识。
        因此：
        - target.prerequisite_nodes 应包含 source
        - source 不能因为是前置知识，就自动把 target 当成 next_nodes
        """
        prerequisite_by_target: dict[str, list[str]] = {}
        dependent_by_source: dict[str, list[str]] = {}
        related_targets: dict[str, list[str]] = {}
        weak_targets: dict[str, list[str]] = {}

        for edge in edges:
            source = edge.get("source", "")
            target = edge.get("target", "")
            relation_type = edge.get("relation_type", edge.get("relation", ""))

            if not source or not target:
                continue

            if relation_type == "prerequisite_of":
                prerequisite_by_target.setdefault(target, []).append(source)
                dependent_by_source.setdefault(source, []).append(target)
            elif relation_type in {"related_to", "parallel_to", "extends_to", "easy_to_confuse_with"}:
                related_targets.setdefault(source, []).append(target)
                if edge.get("direction_type") == "undirected":
                    related_targets.setdefault(target, []).append(source)
            elif relation_type == "weak_related_to":
                weak_targets.setdefault(source, []).append(target)
                if edge.get("direction_type") == "undirected":
                    weak_targets.setdefault(target, []).append(source)

        for node in nodes:
            node_id = node["node_id"]
            extra = node.setdefault("extra", {})

            prerequisites = self._dedup_keep_order(prerequisite_by_target.get(node_id, []))
            related = sorted(set(related_targets.get(node_id, []) + weak_targets.get(node_id, [])))

            extra["resolved_prerequisite_nodes"] = prerequisites
            extra["resolved_related_nodes"] = self._dedup_keep_order(related_targets.get(node_id, []))
            extra["resolved_weak_related_nodes"] = self._dedup_keep_order(weak_targets.get(node_id, []))
            extra["resolved_dependent_nodes"] = self._dedup_keep_order(dependent_by_source.get(node_id, []))

            node["prerequisite_nodes"] = prerequisites
            node["related_nodes"] = related

            # 这里不再写 next_nodes / recommended_next_nodes。
            # 学习顺序统一交给 LearningPathBuilder 处理。
            node.setdefault("next_nodes", [])
            node.setdefault("recommended_next_nodes", [])

            extra["resolved_prerequisite_names"] = self._node_names_from_ids(
                prerequisites, node_id_map
            )
            extra["resolved_related_names"] = self._node_names_from_ids(
                extra["resolved_related_nodes"], node_id_map
            )
            extra["resolved_weak_related_names"] = self._node_names_from_ids(
                extra["resolved_weak_related_nodes"], node_id_map
            )
            extra["resolved_dependent_names"] = self._node_names_from_ids(
                extra["resolved_dependent_nodes"], node_id_map
            )

    @staticmethod
    def _dedup_keep_order(items: list[str]) -> list[str]:
        results: list[str] = []
        for item in items:
            if item and item not in results:
                results.append(item)
        return results

    def _node_names_from_ids(
        self,
        node_ids: list[str],
        node_id_map: dict[str, dict[str, Any]],
    ) -> list[str]:
        names: list[str] = []
        for node_id in node_ids:
            node = node_id_map.get(node_id)
            if node is not None:
                names.append(node.get("name", node_id))
        return names
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
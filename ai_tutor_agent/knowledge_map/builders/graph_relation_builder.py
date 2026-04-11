from __future__ import annotations

from typing import Any

from ai_tutor_agent.knowledge_map.schema.node_schema import normalize_edge_record


class GraphRelationBuilder:
    """
    根据骨架节点生成规则关系。

    当前阶段支持：
    1. HAS_SUBTOPIC
    2. PRE_REQUIRES（优先显式配置）
    3. LEADS_TO
    4. 顺序规则兜底
    """

    def __init__(self, relation_types: dict[str, str]) -> None:
        self.relation_types = relation_types
        self._edge_counter = 0

    def build_edges(self, nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        edges: list[dict[str, Any]] = []

        level1_nodes = [n for n in nodes if int(n.get("level", 0)) == 1]
        level2_nodes = [n for n in nodes if int(n.get("level", 0)) == 2]

        parent_map = {n["node_id"]: n for n in level1_nodes}
        node_id_map = {n["node_id"]: n for n in nodes}
        name_to_node = {str(n.get("name", "")).strip(): n for n in nodes}

        existing_pairs: set[tuple[str, str, str]] = set()

        # 1. 包含关系：一级 -> 二级
        for node in level2_nodes:
            parent_id = node.get("part_of", "")
            if not parent_id or parent_id not in parent_map:
                continue

            edge = self._build_edge(
                source=parent_id,
                target=node["node_id"],
                relation="HAS_SUBTOPIC",
                evidence="rule: parent-child skeleton relation",
                source_type="rule_has_subtopic",
            )
            self._append_edge(edges, edge, existing_pairs)

        # 2. 显式前置关系：优先读取 extra["configured_prerequisites"]
        for node in nodes:
            extra = node.get("extra", {}) or {}
            configured_prerequisites = extra.get("configured_prerequisites", []) or []

            for prereq_name in configured_prerequisites:
                prereq_name = str(prereq_name).strip()
                if not prereq_name:
                    continue

                prereq_node = name_to_node.get(prereq_name)
                if prereq_node is None:
                    continue

                prereq_id = prereq_node["node_id"]
                current_id = node["node_id"]

                pre_edge = self._build_edge(
                    source=current_id,
                    target=prereq_id,
                    relation="PRE_REQUIRES",
                    evidence=f"{node.get('name')} requires {prereq_name}",
                    source_type="config_prerequisite",
                )
                self._append_edge(edges, pre_edge, existing_pairs)

                lead_edge = self._build_edge(
                    source=prereq_id,
                    target=current_id,
                    relation="LEADS_TO",
                    evidence=f"{prereq_name} leads to {node.get('name')}",
                    source_type="config_prerequisite_forward",
                )
                self._append_edge(edges, lead_edge, existing_pairs)

        # 3. 一级节点顺序关系：只有未显式配置前置时才兜底
        for i in range(len(level1_nodes) - 1):
            current_node = level1_nodes[i]
            next_node = level1_nodes[i + 1]

            next_extra = next_node.get("extra", {}) or {}
            has_explicit_prereq = bool(next_extra.get("configured_prerequisites", []))

            if has_explicit_prereq:
                continue

            pre_edge = self._build_edge(
                source=next_node["node_id"],
                target=current_node["node_id"],
                relation="PRE_REQUIRES",
                evidence="fallback rule: next chapter requires previous chapter",
                source_type="rule_sequence_fallback",
            )
            self._append_edge(edges, pre_edge, existing_pairs)

            lead_edge = self._build_edge(
                source=current_node["node_id"],
                target=next_node["node_id"],
                relation="LEADS_TO",
                evidence="fallback rule: previous chapter leads to next chapter",
                source_type="rule_sequence_fallback",
            )
            self._append_edge(edges, lead_edge, existing_pairs)

        # 4. 同父节点下二级节点顺序关系：只有目标节点未显式配置前置时才兜底
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

                next_extra = next_child.get("extra", {}) or {}
                has_explicit_prereq = bool(next_extra.get("configured_prerequisites", []))

                if has_explicit_prereq:
                    continue

                pre_edge = self._build_edge(
                    source=next_child["node_id"],
                    target=current_child["node_id"],
                    relation="PRE_REQUIRES",
                    evidence=f"fallback rule: next sibling requires previous sibling under {parent_id}",
                    source_type="rule_subtopic_fallback",
                )
                self._append_edge(edges, pre_edge, existing_pairs)

                lead_edge = self._build_edge(
                    source=current_child["node_id"],
                    target=next_child["node_id"],
                    relation="LEADS_TO",
                    evidence=f"fallback rule: previous sibling leads to next sibling under {parent_id}",
                    source_type="rule_subtopic_fallback",
                )
                self._append_edge(edges, lead_edge, existing_pairs)

        # 5. 把关系写回节点 extra 里，方便 debug
        self._write_relation_debug_info(
            nodes=nodes,
            edges=edges,
            node_id_map=node_id_map,
        )

        return edges

    def _append_edge(
        self,
        edges: list[dict[str, Any]],
        edge: dict[str, Any],
        existing_pairs: set[tuple[str, str, str]],
    ) -> None:
        key = (edge["source"], edge["target"], edge["relation"])
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
        prerequisite_targets: dict[str, list[str]] = {}
        leads_to_targets: dict[str, list[str]] = {}

        for edge in edges:
            source = edge.get("source", "")
            target = edge.get("target", "")
            relation = edge.get("relation", "")

            if relation == "PRE_REQUIRES":
                prerequisite_targets.setdefault(source, []).append(target)

            elif relation == "LEADS_TO":
                leads_to_targets.setdefault(source, []).append(target)

        for node in nodes:
            node_id = node["node_id"]
            extra = node.setdefault("extra", {})

            extra["resolved_prerequisite_nodes"] = prerequisite_targets.get(node_id, [])
            extra["resolved_next_nodes"] = leads_to_targets.get(node_id, [])

            prereq_names = []
            for prereq_id in prerequisite_targets.get(node_id, []):
                prereq_node = node_id_map.get(prereq_id)
                if prereq_node is not None:
                    prereq_names.append(prereq_node.get("name", prereq_id))

            next_names = []
            for next_id in leads_to_targets.get(node_id, []):
                next_node = node_id_map.get(next_id)
                if next_node is not None:
                    next_names.append(next_node.get("name", next_id))

            extra["resolved_prerequisite_names"] = prereq_names
            extra["resolved_next_names"] = next_names

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
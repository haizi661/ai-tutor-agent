from __future__ import annotations

from typing import Any

from ai_tutor_agent.knowledge_map.schema.node_schema import normalize_edge_record


class GraphRelationBuilder:
    """
    根据骨架节点生成统一的网状关系。

    统一规则：
    1. 所有边都有 relation_type / relation_strength / direction_type
    2. 不再生成 HAS_SUBTOPIC 这类树状包含边
    3. 通过显式前置、章节锚点关联、并列关系、弱桥接关系共同构造网状图
    """

    DEFAULT_RELATION_STRENGTH = {
        "prerequisite_of": 1.0,
        "parallel_to": 0.7,
        "related_to": 0.7,
        "extends_to": 0.7,
        "easy_to_confuse_with": 0.7,
        "weak_related_to": 0.2,
    }

    DIRECTED_RELATIONS = {"prerequisite_of", "extends_to"}

    def __init__(self, relation_types: dict[str, str]) -> None:
        self.relation_types = relation_types
        self._edge_counter = 0

    def build_edges(self, nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        edges: list[dict[str, Any]] = []
        node_id_map = {n["node_id"]: n for n in nodes}
        name_to_node = {str(n.get("name", "")).strip(): n for n in nodes}
        existing_pairs: set[tuple[str, str, str]] = set()

        chapter_anchor_nodes = [
            n for n in nodes if (n.get("extra", {}) or {}).get("node_role") == "chapter_anchor"
        ]
        topic_nodes = [
            n for n in nodes if (n.get("extra", {}) or {}).get("node_role") == "topic"
        ]

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

                edge = self._build_edge(
                    source=prereq_node["node_id"],
                    target=node["node_id"],
                    relation_type="prerequisite_of",
                    evidence=f"{prereq_name} is prerequisite of {node.get('name')}",
                    source_type="config_prerequisite",
                    relation_note="显式配置的前置知识关系",
                    relation_strength=1.0,
                )
                self._append_edge(edges, edge, existing_pairs)

        for topic in topic_nodes:
            extra = topic.get("extra", {}) or {}
            anchor_id = extra.get("chapter_anchor_node_id", "")
            if not anchor_id or anchor_id not in node_id_map:
                continue

            anchor_node = node_id_map[anchor_id]
            edge = self._build_edge(
                source=anchor_node["node_id"],
                target=topic["node_id"],
                relation_type="related_to",
                evidence="chapter anchor links topic node",
                source_type="rule_chapter_anchor",
                relation_note="章节概览节点与本章知识点的主题关联",
                relation_strength=0.7,
            )
            self._append_edge(edges, edge, existing_pairs)

        topics_by_anchor: dict[str, list[dict[str, Any]]] = {}
        for topic in topic_nodes:
            anchor_id = (topic.get("extra", {}) or {}).get("chapter_anchor_node_id", "")
            if anchor_id:
                topics_by_anchor.setdefault(anchor_id, []).append(topic)

        for anchor_id, topics in topics_by_anchor.items():
            topics.sort(key=lambda x: int((x.get("extra", {}) or {}).get("order_in_chapter", 0)))
            for i in range(len(topics) - 1):
                current_topic = topics[i]
                next_topic = topics[i + 1]
                edge = self._build_edge(
                    source=current_topic["node_id"],
                    target=next_topic["node_id"],
                    relation_type="parallel_to",
                    evidence=f"same chapter ordered neighbors under {anchor_id}",
                    source_type="rule_parallel_topic_neighbors",
                    relation_note="同章节相邻知识点，适合并列展示与比较学习",
                    relation_strength=0.7,
                )
                self._append_edge(edges, edge, existing_pairs)

        chapter_anchor_nodes.sort(key=lambda x: x.get("chapter", ""))
        for i in range(len(chapter_anchor_nodes) - 1):
            current_anchor = chapter_anchor_nodes[i]
            next_anchor = chapter_anchor_nodes[i + 1]
            next_extra = next_anchor.get("extra", {}) or {}
            has_explicit_prereq = bool(next_extra.get("configured_prerequisites", []))

            relation_type = "weak_related_to"
            relation_strength = 0.2
            relation_note = "章节级弱桥接关系，用于保证整图连通和可视化连续性"
            source_type = "rule_chapter_bridge"
            evidence = "adjacent chapter anchors bridged for graph connectivity"

            if has_explicit_prereq:
                relation_type = "prerequisite_of"
                relation_strength = 0.7
                relation_note = "章节概览节点的显式前置关系"
                source_type = "config_chapter_prerequisite"
                evidence = f"{current_anchor.get('name')} precedes {next_anchor.get('name')}"

            edge = self._build_edge(
                source=current_anchor["node_id"],
                target=next_anchor["node_id"],
                relation_type=relation_type,
                evidence=evidence,
                source_type=source_type,
                relation_note=relation_note,
                relation_strength=relation_strength,
            )
            self._append_edge(edges, edge, existing_pairs)

        connected_node_ids = self._collect_connected_node_ids(edges)
        if chapter_anchor_nodes:
            fallback_anchor = chapter_anchor_nodes[0]
            for node in nodes:
                if node["node_id"] in connected_node_ids:
                    continue

                extra = node.get("extra", {}) or {}
                anchor_id = extra.get("chapter_anchor_node_id")
                anchor_node = node_id_map.get(anchor_id, fallback_anchor)
                if anchor_node["node_id"] == node["node_id"]:
                    continue

                edge = self._build_edge(
                    source=anchor_node["node_id"],
                    target=node["node_id"],
                    relation_type="weak_related_to",
                    evidence="fallback edge for isolated node connectivity",
                    source_type="rule_isolated_node_bridge",
                    relation_note="孤立节点兜底弱连接，避免可视化中出现脱离主图的节点",
                    relation_strength=0.2,
                )
                self._append_edge(edges, edge, existing_pairs)

        self._write_relation_debug_info(nodes=nodes, edges=edges, node_id_map=node_id_map)
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
        prerequisite_targets: dict[str, list[str]] = {}
        related_targets: dict[str, list[str]] = {}
        weak_targets: dict[str, list[str]] = {}

        for edge in edges:
            source = edge.get("source", "")
            target = edge.get("target", "")
            relation_type = edge.get("relation_type", edge.get("relation", ""))

            if relation_type == "prerequisite_of":
                prerequisite_targets.setdefault(source, []).append(target)
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

            extra["resolved_prerequisite_nodes"] = prerequisite_targets.get(node_id, [])
            extra["resolved_related_nodes"] = related_targets.get(node_id, [])
            extra["resolved_weak_related_nodes"] = weak_targets.get(node_id, [])

            node["prerequisite_nodes"] = prerequisite_targets.get(node_id, [])
            node["related_nodes"] = sorted(
                set(related_targets.get(node_id, []) + weak_targets.get(node_id, []))
            )
            node["next_nodes"] = prerequisite_targets.get(node_id, [])
            node["recommended_next_nodes"] = node["related_nodes"][:]

            extra["resolved_prerequisite_names"] = self._node_names_from_ids(
                prerequisite_targets.get(node_id, []), node_id_map
            )
            extra["resolved_related_names"] = self._node_names_from_ids(
                related_targets.get(node_id, []), node_id_map
            )
            extra["resolved_weak_related_names"] = self._node_names_from_ids(
                weak_targets.get(node_id, []), node_id_map
            )

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
        relation_type: str,
        evidence: str,
        source_type: str,
        relation_note: str,
        relation_strength: float | None = None,
    ) -> dict[str, Any]:
        if relation_strength is None:
            relation_strength = self.DEFAULT_RELATION_STRENGTH.get(relation_type, 0.4)

        direction_type = "directed" if relation_type in self.DIRECTED_RELATIONS else "undirected"

        edge = {
            "edge_id": self._next_edge_id(),
            "source": source,
            "target": target,
            "relation": relation_type,
            "relation_type": relation_type,
            "relation_label": self.relation_types.get(relation_type, relation_type),
            "relation_strength": relation_strength,
            "direction_type": direction_type,
            "weight": relation_strength,
            "source_type": source_type,
            "evidence": evidence,
            "relation_note": relation_note,
        }
        return normalize_edge_record(edge)

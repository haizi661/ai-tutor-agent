from __future__ import annotations

from typing import Any


class LearningPathBuilder:
    """
    学习路径推荐器（顺序路径版）。

    设计原则：
    1. prerequisite_nodes 只表示“学习当前节点之前需要掌握什么”。
       它不能反推出“学完前置节点后下一步就去学被依赖节点”。
    2. next_nodes / recommended_next_nodes 主要表示教学顺序：
       章锚点 -> 本章第一个子知识点；
       子知识点 -> 同章下一个子知识点；
       本章最后一个子知识点 -> 下一章章锚点。
    3. related_nodes 只表示相关/并列/弱连接，不自动进入推荐路径。
    """

    def build_learning_paths(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        node_map = {str(node.get("node_id", "")): node for node in nodes}

        chapter_anchors = self._collect_chapter_anchors(nodes)
        topics_by_anchor = self._collect_topics_by_anchor(nodes)

        next_map: dict[str, list[str]] = {}

        # 1. 章锚点：优先进入本章第一个子知识点
        for idx, anchor in enumerate(chapter_anchors):
            anchor_id = anchor["node_id"]
            topics = topics_by_anchor.get(anchor_id, [])

            if topics:
                next_map[anchor_id] = [topics[0]["node_id"]]
            else:
                # 非重点章可能没有子节点，此时才进入下一章章锚点
                next_anchor = self._next_chapter_anchor(chapter_anchors, idx)
                next_map[anchor_id] = [next_anchor["node_id"]] if next_anchor else []

            # 2. 子知识点：按同章 order_in_chapter 串起来
            for topic_idx, topic in enumerate(topics):
                topic_id = topic["node_id"]
                if topic_idx + 1 < len(topics):
                    next_map[topic_id] = [topics[topic_idx + 1]["node_id"]]
                else:
                    next_anchor = self._next_chapter_anchor(chapter_anchors, idx)
                    next_map[topic_id] = [next_anchor["node_id"]] if next_anchor else []

        # 3. 显式 LEADS_TO / recommended_next 边可作为补充，但不覆盖主线顺序
        explicit_next = self._collect_explicit_next_edges(edges)
        for source, targets in explicit_next.items():
            current = next_map.setdefault(source, [])
            for target in targets:
                if target not in current:
                    current.append(target)

        # 4. 回填 next_nodes / recommended_next_nodes
        for node in nodes:
            node_id = str(node.get("node_id", "")).strip()
            recommended = [x for x in next_map.get(node_id, []) if x in node_map and x != node_id]

            node["next_nodes"] = recommended[:]
            node["recommended_next_nodes"] = recommended[:]

            extra = node.setdefault("extra", {})
            extra["learning_path_status"] = "ok"
            extra["recommended_next_reasons"] = [
                {
                    "target": target_id,
                    "reason": self._build_reason(node, node_map[target_id]),
                }
                for target_id in recommended
            ]

        return nodes

    def _collect_chapter_anchors(self, nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        anchors = [
            node for node in nodes
            if (node.get("extra", {}) or {}).get("node_role") == "chapter_anchor"
        ]

        def sort_key(node: dict[str, Any]) -> tuple[int, str]:
            extra = node.get("extra", {}) or {}
            page_range = extra.get("chapter_page_range", []) or []
            start_page = page_range[0] if isinstance(page_range, list) and page_range else 10**9
            return int(start_page), str(node.get("node_id", ""))

        anchors.sort(key=sort_key)
        return anchors

    def _collect_topics_by_anchor(self, nodes: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        result: dict[str, list[dict[str, Any]]] = {}

        for node in nodes:
            extra = node.get("extra", {}) or {}
            if extra.get("node_role") != "topic":
                continue

            anchor_id = str(extra.get("chapter_anchor_node_id", "")).strip()
            if not anchor_id:
                # 兼容旧字段：normalize_node_record 会把 part_of 放到 extra.legacy_part_of
                anchor_id = str(extra.get("legacy_part_of", "")).strip()

            if anchor_id:
                result.setdefault(anchor_id, []).append(node)

        for anchor_id, topics in result.items():
            topics.sort(
                key=lambda node: (
                    int((node.get("extra", {}) or {}).get("order_in_chapter", 10**6)),
                    str(node.get("node_id", "")),
                )
            )

        return result

    def _next_chapter_anchor(
        self,
        chapter_anchors: list[dict[str, Any]],
        current_index: int,
    ) -> dict[str, Any] | None:
        if current_index + 1 < len(chapter_anchors):
            return chapter_anchors[current_index + 1]
        return None

    def _collect_explicit_next_edges(self, edges: list[dict[str, Any]]) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}

        for edge in edges:
            relation_type = str(edge.get("relation_type", edge.get("relation", ""))).strip()
            relation = str(edge.get("relation", "")).strip()

            # 这里只接受真正表达“学习后继”的边，不接受 prerequisite_of / related_to / parallel_to。
            if relation_type not in {"leads_to", "LEADS_TO", "recommended_next", "RECOMMENDED_NEXT"} and relation not in {"leads_to", "LEADS_TO", "recommended_next", "RECOMMENDED_NEXT"}:
                continue

            source = str(edge.get("source", "")).strip()
            target = str(edge.get("target", "")).strip()
            if source and target:
                result.setdefault(source, []).append(target)

        return result

    def _build_reason(self, current_node: dict[str, Any], target_node: dict[str, Any]) -> str:
        current_extra = current_node.get("extra", {}) or {}
        target_extra = target_node.get("extra", {}) or {}

        current_role = current_extra.get("node_role", "")
        target_role = target_extra.get("node_role", "")

        if current_role == "chapter_anchor" and target_role == "topic":
            return "推荐先学习本章的第一个核心子知识点"
        if current_role == "topic" and target_role == "topic":
            return "这是当前知识点在本章内部的后续学习内容"
        if current_role == "topic" and target_role == "chapter_anchor":
            return "本章子知识点已学习完毕，可进入下一章概览节点"
        if current_role == "chapter_anchor" and target_role == "chapter_anchor":
            return "当前章节没有配置子知识点，推荐进入下一章"
        return "根据显式学习路径配置推荐"

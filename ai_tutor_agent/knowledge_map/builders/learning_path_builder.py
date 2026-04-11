from __future__ import annotations

from typing import Any


class LearningPathBuilder:
    """
    标准版学习路径推荐器。

    当前策略：
    1. 一级节点：
       - 先推荐本章子节点
       - 再推荐章节后继节点
    2. 二级节点：
       - 先推荐同章节下一个兄弟节点
       - 若无兄弟后继，则推荐父章节的后继章节
    """

    def build_learning_paths(
        self,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        node_map = {node["node_id"]: node for node in nodes}

        children_map: dict[str, list[str]] = {}
        for node in nodes:
            parent_id = node.get("part_of", "")
            if parent_id:
                children_map.setdefault(parent_id, []).append(node["node_id"])

        next_map: dict[str, list[str]] = {}
        for edge in edges:
            if edge.get("relation") != "LEADS_TO":
                continue
            source = edge.get("source", "")
            target = edge.get("target", "")
            if source and target:
                next_map.setdefault(source, []).append(target)

        for node in nodes:
            node_id = node["node_id"]
            level = int(node.get("level", 0))
            recommended: list[str] = []
            recommendation_reasons: list[dict[str, str]] = []

            if level == 1:
                # 一级节点优先推荐本章展开知识点
                child_ids = children_map.get(node_id, [])
                for child_id in child_ids:
                    recommended.append(child_id)
                    recommendation_reasons.append(
                        {
                            "target": child_id,
                            "reason": "推荐先学习本章节的核心子知识点",
                        }
                    )

                # 再推荐下一个章节
                for next_id in next_map.get(node_id, []):
                    if next_id not in recommended:
                        recommended.append(next_id)
                        recommendation_reasons.append(
                            {
                                "target": next_id,
                                "reason": "当前章节学习后，可进入后续章节",
                            }
                        )

            elif level == 2:
                # 二级节点优先推荐同章节后继子节点
                for next_id in next_map.get(node_id, []):
                    if next_id not in recommended:
                        recommended.append(next_id)
                        recommendation_reasons.append(
                            {
                                "target": next_id,
                                "reason": "这是当前知识点在本章节内的后续内容",
                            }
                        )

                # 如果本章没有后继子节点，则推荐父章节的后续章节
                if not recommended:
                    parent_id = node.get("part_of", "")
                    if parent_id:
                        for next_parent_id in next_map.get(parent_id, []):
                            if next_parent_id not in recommended:
                                recommended.append(next_parent_id)
                                recommendation_reasons.append(
                                    {
                                        "target": next_parent_id,
                                        "reason": "本章核心子知识点已完成，可进入下一章节",
                                    }
                                )

            node["recommended_next_nodes"] = recommended

            extra = node.setdefault("extra", {})
            extra["learning_path_status"] = "ok"
            extra["recommended_next_reasons"] = recommendation_reasons

        return nodes
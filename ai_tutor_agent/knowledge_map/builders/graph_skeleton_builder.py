from __future__ import annotations

from typing import Any

from ai_tutor_agent.knowledge_map.schema.node_schema import normalize_node_record


class GraphSkeletonBuilder:
    """
    根据静态课程配置，生成知识图谱骨架节点。

    改造后：
    1. 所有节点平权，不再输出 level / part_of
    2. 章节概览节点与子知识点节点统一作为普通知识点
    3. 层级痕迹仅保存在 extra 中，便于调试与过渡迁移
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self._node_counter = 0

    def build_nodes(self) -> list[dict[str, Any]]:
        nodes: list[dict[str, Any]] = []

        chapters = self.config.get("chapters", [])
        for chapter_cfg in chapters:
            if not chapter_cfg.get("enabled", True):
                continue

            chapter_anchor_node = self._build_chapter_anchor_node(chapter_cfg)
            nodes.append(chapter_anchor_node)

            subtopics = chapter_cfg.get("subtopics", []) or []
            for order_in_chapter, subtopic_cfg in enumerate(subtopics, start=1):
                topic_node = self._build_topic_node(
                    chapter_cfg=chapter_cfg,
                    subtopic_cfg=subtopic_cfg,
                    chapter_anchor_node=chapter_anchor_node,
                    order_in_chapter=order_in_chapter,
                )
                nodes.append(topic_node)

        return nodes

    def _next_node_id(self) -> str:
        self._node_counter += 1
        return f"KM{self._node_counter:03d}"

    def _build_chapter_anchor_node(self, chapter_cfg: dict[str, Any]) -> dict[str, Any]:
        node = {
            "node_id": self._next_node_id(),
            "name": chapter_cfg["name"],
            "chapter": chapter_cfg["chapter"],
            "summary": chapter_cfg.get("summary", ""),
            "tags": chapter_cfg.get("tags", []),
            "requirement_level": chapter_cfg.get("requirement_level", ""),
            "mastery_threshold": chapter_cfg.get("mastery_threshold", 0.0),
            "importance_level": chapter_cfg.get("importance_level", ""),
            "assessment_focus": chapter_cfg.get("assessment_focus", ""),
            "source_type": "skeleton_chapter_anchor",
            "extra": {
                "is_focus": chapter_cfg.get("is_focus", False),
                "enabled": chapter_cfg.get("enabled", True),
                "subtopic_count_configured": len(chapter_cfg.get("subtopics", []) or []),
                "chapter_page_range": chapter_cfg.get("page_range", []),
                "retrieval_keywords": chapter_cfg.get("retrieval_keywords", []),
                "syllabus_rule_source": "course_graph_config",
                "configured_prerequisites": chapter_cfg.get("prerequisites", []),
                "node_role": "chapter_anchor",
                "legacy_level": chapter_cfg.get("level", 1),
                "legacy_part_of": "",
            },
        }
        return normalize_node_record(node)

    def _build_topic_node(
        self,
        chapter_cfg: dict[str, Any],
        subtopic_cfg: dict[str, Any],
        chapter_anchor_node: dict[str, Any],
        order_in_chapter: int,
    ) -> dict[str, Any]:
        node = {
            "node_id": self._next_node_id(),
            "name": subtopic_cfg["name"],
            "chapter": chapter_cfg["chapter"],
            "summary": subtopic_cfg.get("summary", ""),
            "tags": subtopic_cfg.get("tags", []),
            "requirement_level": subtopic_cfg.get(
                "requirement_level",
                chapter_cfg.get("requirement_level", ""),
            ),
            "mastery_threshold": subtopic_cfg.get(
                "mastery_threshold",
                chapter_cfg.get("mastery_threshold", 0.0),
            ),
            "importance_level": subtopic_cfg.get(
                "importance_level",
                chapter_cfg.get("importance_level", ""),
            ),
            "assessment_focus": subtopic_cfg.get(
                "assessment_focus",
                chapter_cfg.get("assessment_focus", ""),
            ),
            "source_type": "skeleton_topic",
            "extra": {
                "chapter_anchor_node_id": chapter_anchor_node["node_id"],
                "chapter_anchor_name": chapter_anchor_node["name"],
                "is_focus_chapter": chapter_cfg.get("is_focus", False),
                "chapter_page_range": chapter_cfg.get("page_range", []),
                "retrieval_keywords": chapter_cfg.get("retrieval_keywords", []),
                "syllabus_rule_source": "chapter_inherited",
                "configured_prerequisites": subtopic_cfg.get("prerequisites", []),
                "node_role": "topic",
                "order_in_chapter": order_in_chapter,
                "legacy_level": 2,
                "legacy_part_of": chapter_anchor_node["node_id"],
            },
        }
        return normalize_node_record(node)

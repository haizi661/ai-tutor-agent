from __future__ import annotations

from typing import Any

from ai_tutor_agent.knowledge_map.schema.node_schema import normalize_node_record


class GraphSkeletonBuilder:
    """
    根据静态课程配置，生成知识图谱骨架节点。
    当前阶段做：
    1. 一级节点
    2. 二级节点（仅重点章节默认展开）
    3. 大纲规则字段写入
    4. 基本字段补齐
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

            parent_node = self._build_parent_node(chapter_cfg)
            nodes.append(parent_node)

            # 只有重点章节才默认展开二级节点
            should_expand_subtopics = chapter_cfg.get("is_focus", False)

            if not should_expand_subtopics:
                continue

            subtopics = chapter_cfg.get("subtopics", []) or []
            for subtopic_cfg in subtopics:
                child_node = self._build_child_node(
                    chapter_cfg=chapter_cfg,
                    subtopic_cfg=subtopic_cfg,
                    parent_node=parent_node,
                )
                nodes.append(child_node)

        return nodes

    def _next_node_id(self) -> str:
        self._node_counter += 1
        return f"KM{self._node_counter:03d}"

    def _build_parent_node(self, chapter_cfg: dict[str, Any]) -> dict[str, Any]:
        node = {
            "node_id": self._next_node_id(),
            "name": chapter_cfg["name"],
            "chapter": chapter_cfg["chapter"],
            "level": chapter_cfg.get("level", 1),
            "summary": chapter_cfg.get("summary", ""),
            "tags": chapter_cfg.get("tags", []),
            "requirement_level": chapter_cfg.get("requirement_level", ""),
            "mastery_threshold": chapter_cfg.get("mastery_threshold", 0.0),
            "importance_level": chapter_cfg.get("importance_level", ""),
            "assessment_focus": chapter_cfg.get("assessment_focus", ""),
            "part_of": "",
            "source_type": "skeleton_parent",
            "extra": {
                "is_focus": chapter_cfg.get("is_focus", False),
                "enabled": chapter_cfg.get("enabled", True),
                "subtopic_count_configured": len(chapter_cfg.get("subtopics", []) or []),
                "chapter_page_range": chapter_cfg.get("page_range", []),
                "retrieval_keywords": chapter_cfg.get("retrieval_keywords", []),
                "syllabus_rule_source": "course_graph_config",
            },
        }
        return normalize_node_record(node)

    def _build_child_node(
        self,
        chapter_cfg: dict[str, Any],
        subtopic_cfg: dict[str, Any],
        parent_node: dict[str, Any],
    ) -> dict[str, Any]:
        node = {
            "node_id": self._next_node_id(),
            "name": subtopic_cfg["name"],
            "chapter": chapter_cfg["chapter"],
            "level": 2,
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
            "part_of": parent_node["node_id"],
            "source_type": "skeleton_child",
            "extra": {
                "parent_name": parent_node["name"],
                "is_focus_chapter": chapter_cfg.get("is_focus", False),
                "chapter_page_range": chapter_cfg.get("page_range", []),
                "retrieval_keywords": chapter_cfg.get("retrieval_keywords", []),
                "syllabus_rule_source": "chapter_inherited",
            },
        }
        return normalize_node_record(node)
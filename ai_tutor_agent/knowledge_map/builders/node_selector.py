from __future__ import annotations

import re
from typing import Any


class NodeSelector:
    """
    问题对应节点选择器。

    当前版本优先使用图谱 2.1 的教学属性做锚点定位：
    - core_concepts
    - assessment_focus
    - explanation_teacher_style
    - extra.retrieval_keywords / resolved_* / node_role
    """

    def detect_question_type(self, question: str) -> str:
        q = (question or "").strip()

        learning_path_keywords = [
            "接下来学什么",
            "下一步学什么",
            "后面学什么",
            "推荐学什么",
            "学习路径",
            "学完",
            "之后学什么",
        ]
        requirement_keywords = [
            "要求是什么",
            "课程要求",
            "掌握到什么程度",
            "是了解还是掌握",
            "掌握还是了解",
            "过关标准",
            "掌握门槛",
        ]
        prerequisite_keywords = [
            "前置知识",
            "先修知识",
            "学习这个之前要学什么",
            "之前要学什么",
            "之前要先学什么",
            "先学什么",
            "先学哪些",
            "学这个前要学什么",
        ]

        if any(k in q for k in prerequisite_keywords):
            return "prerequisite_query"
        if any(k in q for k in learning_path_keywords):
            return "learning_path"
        if any(k in q for k in requirement_keywords):
            return "requirement_query"
        return "knowledge_qa"

    def select_node(
        self,
        question: str,
        nodes: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        if not question or not nodes:
            return None

        best_node: dict[str, Any] | None = None
        best_score = -1.0
        for node in nodes:
            score = self._score_node(question, node)
            if score > best_score:
                best_score = score
                best_node = node
        return best_node

    def select_best_node(
        self,
        query: str,
        nodes: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        return self.select_node(query, nodes)

    def _score_node(self, query: str, node: dict[str, Any]) -> float:
        query = (query or "").strip()
        if not query:
            return 0.0

        name = str(node.get("name", "") or "").strip()
        chapter = str(node.get("chapter", "") or "").strip()
        summary = str(node.get("summary", "") or "").strip()
        assessment_focus = str(node.get("assessment_focus", "") or "").strip()
        explanation_teacher_style = str(node.get("explanation_teacher_style", "") or "").strip()
        tags = [str(tag).strip() for tag in (node.get("tags", []) or []) if str(tag).strip()]
        core_concepts = [
            str(item).strip()
            for item in (node.get("core_concepts", []) or [])
            if str(item).strip()
        ]
        extra = node.get("extra", {}) or {}

        retrieval_keywords = self._collect_extra_keywords(extra)
        query_tokens = self._extract_query_tokens(query)
        score = 0.0

        if name and name in query:
            score += 12.0

        for kw in self._extract_name_keywords(name):
            if kw and kw in query:
                score += 4.0

        if chapter and chapter in query:
            score += 1.5

        if assessment_focus and assessment_focus in query:
            score += 2.6

        for tag in tags:
            if tag in query:
                score += 1.8

        for concept in core_concepts:
            if concept in query:
                score += 2.2

        for keyword in retrieval_keywords:
            if keyword in query:
                score += 2.4

        for keyword in self._split_keywords(summary):
            if keyword in query:
                score += 0.5

        for keyword in self._split_keywords(explanation_teacher_style)[:12]:
            if keyword in query:
                score += 0.2

        evidence_terms: list[str] = []
        evidence_terms.extend(self._extract_name_keywords(name))
        evidence_terms.extend(tags)
        evidence_terms.extend(core_concepts)
        evidence_terms.extend(retrieval_keywords)
        evidence_terms.extend(self._split_keywords(summary))
        overlap_count = 0
        for token in query_tokens:
            if any(token and token in term for term in evidence_terms):
                overlap_count += 1
                score += 1.35

        if overlap_count:
            score += min(overlap_count * 0.55, 3.0)
        if any(token in name for token in query_tokens):
            score += 1.2
        if any(token in concept for token in query_tokens for concept in core_concepts):
            score += 1.0

        score += self._importance_bonus(node)
        score += self._role_bonus(extra)
        score += min(len(name) / 20.0, 1.0)
        return score

    def _collect_extra_keywords(self, extra: dict[str, Any]) -> list[str]:
        if not isinstance(extra, dict):
            return []

        keys_to_collect = [
            "retrieval_keywords",
            "resolved_prerequisite_names",
            "resolved_related_names",
            "resolved_weak_related_names",
            "matched_block_title",
        ]
        results: list[str] = []

        for key in keys_to_collect:
            value = extra.get(key)
            if isinstance(value, list):
                for item in value:
                    text = str(item).strip()
                    if text and text not in results:
                        results.append(text)
            else:
                text = str(value or "").strip()
                if text and text not in results:
                    results.append(text)

        node_role = str(extra.get("node_role", "") or "").strip()
        if node_role and node_role not in results:
            results.append(node_role)
        return results

    def _importance_bonus(self, node: dict[str, Any]) -> float:
        importance = str(node.get("importance_level", "") or "").strip()
        bonuses = {
            "核心": 0.9,
            "重要": 0.55,
            "一般": 0.15,
        }
        return bonuses.get(importance, 0.0)

    def _role_bonus(self, extra: dict[str, Any]) -> float:
        if not isinstance(extra, dict):
            return 0.0
        role = str(extra.get("node_role", "") or "").strip()
        if role == "chapter_anchor":
            return 0.35
        if role:
            return 0.1
        return 0.0

    def _extract_name_keywords(self, name: str) -> list[str]:
        results: list[str] = []
        name = name.strip()
        if not name:
            return results

        results.append(name)

        if "的" in name:
            tail = name.split("的", 1)[-1].strip()
            if len(tail) >= 2:
                results.append(tail)

        common_parts = [
            "根轨迹法",
            "频域分析",
            "时域分析",
            "数学模型",
            "自动控制系统",
            "自动控制",
            "负反馈",
            "稳态误差",
            "稳定性",
            "状态空间",
            "离散系统",
            "校正方法",
            "频率特性",
            "结构图与信号流图",
        ]
        for part in common_parts:
            if part in name and part not in results:
                results.append(part)

        deduped: list[str] = []
        for item in results:
            if item not in deduped:
                deduped.append(item)
        return deduped

    def _split_keywords(self, text: str) -> list[str]:
        cleaned = re.sub(r"[，。？！；：、“”‘’（）()【】\[\],.;:!?]", " ", text or "")
        parts = [item.strip() for item in cleaned.split() if item.strip()]
        return [item for item in parts if len(item) >= 2]

    def _extract_query_tokens(self, text: str) -> list[str]:
        parts = re.findall(r"[A-Za-z][A-Za-z0-9_%-]*|[\u4e00-\u9fff]{2,}|[0-9]+(?:\.[0-9]+)?", text or "")
        stop_words = {"什么", "关系", "如何", "为什么", "请问", "一个", "系统"}
        results: list[str] = []
        for part in parts:
            token = part.strip()
            if len(token) < 2 or token in stop_words or token in results:
                continue
            results.append(token)
        return results[:10]

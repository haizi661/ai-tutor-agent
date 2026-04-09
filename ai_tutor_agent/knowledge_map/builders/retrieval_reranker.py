from __future__ import annotations

from typing import Any


class RetrievalReranker:
    """
    对向量检索结果做二次重排。
    目标：
    1. 让定义类问题更容易把 definition_candidates 顶上来
    2. 让公式类问题更容易把 formula_candidates 顶上来
    3. 让例子类问题更容易把 example_candidates 顶上来
    4. 综合 candidate_type、关键词命中、节点名命中做简单规则重排
    """

    def rerank(
        self,
        query: str,
        rows: list[dict[str, Any]],
        target_node_name: str | None = None,
    ) -> list[dict[str, Any]]:
        reranked_rows: list[dict[str, Any]] = []

        for row in rows:
            metadata = row.get("metadata", {}) or {}
            text = str(row.get("text", "")).strip()
            distance = float(row.get("distance", 999.0))
            candidate_type = str(metadata.get("candidate_type", "")).strip()

            score = self._base_score_from_distance(distance)
            score += self._candidate_type_bonus(query, candidate_type)
            score += self._query_text_match_bonus(query, text)
            score += self._definition_style_bonus(query, text)
            score += self._formula_style_bonus(query, text)
            score += self._example_style_bonus(query, text)

            if target_node_name:
                if target_node_name in text:
                    score += 1.2

            new_row = dict(row)
            new_row["rerank_score"] = round(score, 4)
            reranked_rows.append(new_row)

        reranked_rows.sort(key=lambda x: x.get("rerank_score", -999), reverse=True)
        return reranked_rows

    def _base_score_from_distance(self, distance: float) -> float:
        """
        Chroma distance 越小越相近，所以转成“越大越好”的基础分。
        """
        return -distance

    def _candidate_type_bonus(self, query: str, candidate_type: str) -> float:
        query = query.strip()

        if self._is_definition_query(query):
            if candidate_type == "definition_candidates":
                return 3.5
            if candidate_type == "key_point_candidates":
                return 1.2

        if self._is_formula_query(query):
            if candidate_type == "formula_candidates":
                return 2.5
            if candidate_type == "definition_candidates":
                return 0.8

        if self._is_example_query(query):
            if candidate_type == "example_candidates":
                return 2.5
            if candidate_type == "key_point_candidates":
                return 0.8

        if self._is_keypoint_query(query):
            if candidate_type == "key_point_candidates":
                return 2.2
            if candidate_type == "definition_candidates":
                return 1.0

        return 0.3

    def _query_text_match_bonus(self, query: str, text: str) -> float:
        bonus = 0.0

        query_keywords = self._extract_query_keywords(query)
        for kw in query_keywords:
            if kw and kw in text:
                bonus += 0.5

        return bonus

    def _definition_style_bonus(self, query: str, text: str) -> float:
        if not self._is_definition_query(query):
            return 0.0

        bonus = 0.0

        # ⭐ 强定义句（直接加大分）
        strong_patterns = [
            "是",
            "是指",
            "是一种",
            "是用来",
            "称为",
        ]

        # ⭐ 弱提示
        weak_patterns = [
            "基本概念",
            "定义",
            "概念",
        ]

        # ⭐ 关键：必须同时包含“主题词 + 定义结构”
        if "根轨迹法" in text:
            for p in strong_patterns:
                if p in text:
                    bonus += 2.0   # 🔥 核心提升点

        # 普通定义提示
        for p in weak_patterns:
            if p in text:
                bonus += 0.6

        return bonus

    def _formula_style_bonus(self, query: str, text: str) -> float:
        if not self._is_formula_query(query):
            return 0.0

        markers = ["方程", "公式", "传递函数", "相角条件", "模值条件", "=", "式("]
        bonus = 0.0
        for marker in markers:
            if marker in text:
                bonus += 0.5

        return bonus

    def _example_style_bonus(self, query: str, text: str) -> float:
        if not self._is_example_query(query):
            return 0.0

        markers = ["例如", "比如", "实例", "图", "系统"]
        bonus = 0.0
        for marker in markers:
            if marker in text:
                bonus += 0.4

        return bonus

    def _is_definition_query(self, query: str) -> bool:
        markers = ["什么是", "定义", "概念", "含义", "是什么"]
        return any(m in query for m in markers)

    def _is_formula_query(self, query: str) -> bool:
        markers = ["公式", "方程", "表达式", "传递函数", "怎么算", "计算公式"]
        return any(m in query for m in markers)

    def _is_example_query(self, query: str) -> bool:
        markers = ["例子", "实例", "应用", "举例", "案例"]
        return any(m in query for m in markers)

    def _is_keypoint_query(self, query: str) -> bool:
        markers = ["要点", "重点", "特点", "作用", "意义", "关系"]
        return any(m in query for m in markers)

    def _extract_query_keywords(self, query: str) -> list[str]:
        raw_keywords = [
            "根轨迹",
            "根轨迹法",
            "自动控制",
            "反馈控制",
            "数学模型",
            "时域分析",
            "稳定性",
            "稳态误差",
            "频率响应",
            "校正",
            "状态空间",
            "离散系统",
        ]
        return [kw for kw in raw_keywords if kw in query]
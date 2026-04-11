from __future__ import annotations

from typing import Any


class NodeSelector:
    """
    问题对应节点选择器。

    当前支持：
    1. question_type 识别
    2. 根据问题内容匹配最相关节点
    3. 保留原先“节点粗选”的思路，但统一成 select_node 接口
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
        """
        兼容你旧代码里可能还在调用的接口。
        实际上内部直接复用 select_node。
        """
        return self.select_node(query, nodes)

    def _score_node(self, query: str, node: dict[str, Any]) -> float:
        query = (query or "").strip()
        name = str(node.get("name", "") or "").strip()
        chapter = str(node.get("chapter", "") or "").strip()
        summary = str(node.get("summary", "") or "").strip()
        tags = node.get("tags", []) or []
        level = int(node.get("level", 1))

        score = 0.0

        # 1. 完整节点名直接命中
        if name and name in query:
            score += 10.0

        # 2. 节点名核心短语命中
        name_keywords = self._extract_name_keywords(name)
        for kw in name_keywords:
            if kw and kw in query:
                score += 4.0

        # 3. 章节名命中
        if chapter and chapter in query:
            score += 2.0

        # 4. tags 命中
        for tag in tags:
            tag_str = str(tag).strip()
            if tag_str and tag_str in query:
                score += 2.0

        # 5. summary 弱命中
        for keyword in self._split_keywords(summary):
            if keyword and keyword in query:
                score += 0.5

        # 6. 一级节点轻微优先
        if level == 1:
            score += 0.8

        # 7. 名称越完整稍微加一点分
        score += min(len(name) / 20.0, 1.0)

        return score

    def _extract_name_keywords(self, name: str) -> list[str]:
        """
        从节点名里提取更适合匹配问句的核心短语。
        比如：
        线性系统的根轨迹法 -> 根轨迹法
        自动控制系统的分类 -> 自动控制系统 / 分类
        """
        results: list[str] = []

        name = name.strip()
        if not name:
            return results

        # 原名保留
        results.append(name)

        # 常见“X的Y”结构，提取后半部分
        if "的" in name:
            tail = name.split("的")[-1].strip()
            if len(tail) >= 2:
                results.append(tail)

        # 常见短语补充
        common_parts = [
            "根轨迹法",
            "根轨迹",
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
            "频率域稳定判据",
            "时域数学模型",
            "复数域数学模型",
            "结构图与信号流图",
        ]
        for part in common_parts:
            if part in name and part not in results:
                results.append(part)

        # 去重
        unique_results: list[str] = []
        for item in results:
            if item not in unique_results:
                unique_results.append(item)

        return unique_results

    def _split_keywords(self, text: str) -> list[str]:
        text = (
            text.replace("、", " ")
            .replace("，", " ")
            .replace("：", " ")
            .replace("。", " ")
            .replace("（", " ")
            .replace("）", " ")
            .replace("(", " ")
            .replace(")", " ")
        )
        parts = [x.strip() for x in text.split() if x.strip()]
        results: list[str] = []
        for part in parts:
            if len(part) >= 2:
                results.append(part)
        return results
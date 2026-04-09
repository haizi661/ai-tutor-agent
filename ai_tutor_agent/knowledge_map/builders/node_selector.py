from __future__ import annotations

from typing import Any


class NodeSelector:
    """
    根据用户问题，从已有节点中粗选最相关的节点。
    改进版策略：
    1. 优先看节点名核心短语是否命中
    2. 再看 tags / summary
    3. 对一级节点和更完整名称做轻微加权
    """

    def select_best_node(
        self,
        query: str,
        nodes: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        best_node: dict[str, Any] | None = None
        best_score = -1.0

        for node in nodes:
            score = self._score_node(query, node)
            if score > best_score:
                best_score = score
                best_node = node

        return best_node

    def _score_node(self, query: str, node: dict[str, Any]) -> float:
        query = query.strip()
        name = str(node.get("name", "")).strip()
        summary = str(node.get("summary", "")).strip()
        tags = node.get("tags", []) or []
        level = int(node.get("level", 1))

        score = 0.0

        # 1. 完整节点名直接命中
        if name and name in query:
            score += 10.0

        # 2. 节点名中的核心短语命中
        name_keywords = self._extract_name_keywords(name)
        for kw in name_keywords:
            if kw and kw in query:
                score += 4.0

        # 3. tags 命中
        for tag in tags:
            tag = str(tag).strip()
            if tag and tag in query:
                score += 2.0

        # 4. summary 关键词弱命中
        for keyword in self._split_keywords(summary):
            if keyword and keyword in query:
                score += 0.5

        # 5. 一级节点轻微优先
        if level == 1:
            score += 0.8

        # 6. 名称越完整越稍微加一点分
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
        for part in [
            "根轨迹法",
            "根轨迹",
            "频域分析",
            "时域分析",
            "数学模型",
            "自动控制系统",
            "负反馈",
            "稳态误差",
            "稳定性",
            "状态空间",
            "离散系统",
            "校正方法",
        ]:
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
        )
        parts = [x.strip() for x in text.split() if x.strip()]
        results = []
        for part in parts:
            if len(part) >= 2:
                results.append(part)
        return results
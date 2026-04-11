from __future__ import annotations

from typing import Any


class RAGAnswerGenerator:
    """
    问答答案生成器。

    当前支持：
    1. 普通知识问答
    2. 学习路径问答
    3. 课程要求问答
    4. 前置知识问答
    """

    def generate_answer(
        self,
        question: str,
        question_type: str,
        matched_node: dict[str, Any] | None,
        retrieval_evidence: list[dict[str, Any]] | None = None,
        node_map: dict[str, dict[str, Any]] | None = None,
    ) -> str:
        if matched_node is None:
            return "我暂时没有定位到明确的知识点节点，你可以把问题再说具体一点。"

        if question_type == "learning_path":
            return self._answer_learning_path(matched_node, node_map or {})

        if question_type == "requirement_query":
            return self._answer_requirement(matched_node)

        if question_type == "prerequisite_query":
            return self._answer_prerequisite(matched_node, node_map or {})

        return self._answer_knowledge_qa(
            matched_node=matched_node,
            retrieval_evidence=retrieval_evidence or [],
        )

    def _answer_learning_path(
        self,
        matched_node: dict[str, Any],
        node_map: dict[str, dict[str, Any]],
    ) -> str:
        node_name = matched_node.get("name", "")
        recommended_ids = matched_node.get("recommended_next_nodes", []) or []
        extra = matched_node.get("extra", {}) or {}
        reasons = extra.get("recommended_next_reasons", []) or []

        if not recommended_ids:
            return f"当前节点“{node_name}”暂时没有配置明确的后续推荐路径。"

        lines = [f"从当前知识点“{node_name}”出发，推荐你下一步学习："]

        for idx, node_id in enumerate(recommended_ids, start=1):
            target_name = node_map.get(node_id, {}).get("name", node_id)
            reason_text = ""
            for item in reasons:
                if item.get("target") == node_id:
                    reason_text = item.get("reason", "")
                    break

            if reason_text:
                lines.append(f"{idx}. {target_name}。原因：{reason_text}")
            else:
                lines.append(f"{idx}. {target_name}")

        req = matched_node.get("requirement_level", "")
        focus = matched_node.get("assessment_focus", "")
        threshold = matched_node.get("mastery_threshold", 0.0)

        lines.append(
            f"这个节点当前课程要求是“{req}”，考查重点偏“{focus}”，建议掌握度达到 {threshold:.0%} 左右再进入后续内容。"
        )

        return "\n".join(lines)

    def _answer_requirement(self, matched_node: dict[str, Any]) -> str:
        node_name = matched_node.get("name", "")
        req = matched_node.get("requirement_level", "")
        threshold = matched_node.get("mastery_threshold", 0.0)
        importance = matched_node.get("importance_level", "")
        focus = matched_node.get("assessment_focus", "")

        return (
            f"知识点“{node_name}”的课程要求如下：\n"
            f"1. 要求层级：{req}\n"
            f"2. 掌握门槛：建议达到 {threshold:.0%}\n"
            f"3. 重要程度：{importance}\n"
            f"4. 考查重点：{focus}"
        )

    def _answer_prerequisite(
        self,
        matched_node: dict[str, Any],
        node_map: dict[str, dict[str, Any]],
    ) -> str:
        node_name = matched_node.get("name", "")
        prerequisite_ids = matched_node.get("prerequisite_nodes", []) or []

        if not prerequisite_ids:
            return f"知识点“{node_name}”当前没有显式配置前置知识，通常可以直接进入学习。"

        prerequisite_names = [
            node_map.get(node_id, {}).get("name", node_id)
            for node_id in prerequisite_ids
        ]

        joined = "、".join(prerequisite_names)
        return f"学习“{node_name}”之前，建议先掌握这些前置知识：{joined}。"

    def _answer_knowledge_qa(
        self,
        matched_node: dict[str, Any],
        retrieval_evidence: list[dict[str, Any]],
    ) -> str:
        node_name = matched_node.get("name", "")
        teacher_text = matched_node.get("explanation_teacher_style", "") or ""
        summary = matched_node.get("summary", "") or ""

        evidence_texts = []
        for item in retrieval_evidence[:3]:
            text = str(item.get("text", "") or "").strip()
            if text:
                evidence_texts.append(text)

        if teacher_text:
            base = teacher_text
        elif summary:
            base = f"关于“{node_name}”，可以先这样理解：{summary}"
        else:
            base = f"这是关于“{node_name}”的知识点。"

        if evidence_texts:
            base += "\n\n相关证据：\n"
            for i, text in enumerate(evidence_texts, start=1):
                base += f"{i}. {text}\n"

        return base.strip()
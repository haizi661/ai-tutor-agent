from __future__ import annotations
import re
from typing import Any

from ai_tutor_agent.knowledge_map.builders.vector_retriever import VectorRetriever
from ai_tutor_agent.knowledge_map.builders.teacher_style_generator import TeacherStyleGenerator

class NodePropertyGenerator:
    """
    基于节点内检索结果，生成第一版节点属性：
    1. explanation_teacher_style
    2. formulas
    3. examples

    当前版本先不用大模型，采用“检索 + 模板拼接”的方式。
    后续可替换为真正的 LLM 生成器。
    """

    def __init__(self) -> None:
        self.retriever = VectorRetriever()
        self.teacher_generator = TeacherStyleGenerator()

    def enrich_nodes(self, nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for node in nodes:
            node_id = str(node.get("node_id", "")).strip()
            node_name = str(node.get("name", "")).strip()

            definition_rows = self.retriever.retrieve(
                query=f"什么是{node_name}",
                node_id=node_id,
                candidate_types=["definition_candidates", "key_point_candidates"],
                top_k=3,
                use_rerank=True,
                target_node_name=node_name,
            )

            keypoint_rows = self.retriever.retrieve(
                query=f"{node_name}的重点和作用是什么",
                node_id=node_id,
                candidate_types=["key_point_candidates", "definition_candidates"],
                top_k=4,
                use_rerank=True,
                target_node_name=node_name,
            )

            formula_rows = self.retriever.retrieve(
                query=f"{node_name}的公式和方程是什么",
                node_id=node_id,
                candidate_types=["formula_candidates", "definition_candidates", "key_point_candidates"],
                top_k=4,
                use_rerank=True,
                target_node_name=node_name,
            )

            example_rows = self.retriever.retrieve(
                query=f"{node_name}有哪些例子或应用",
                node_id=node_id,
                candidate_types=["example_candidates", "key_point_candidates"],
                top_k=3,
                use_rerank=True,
                target_node_name=node_name,
            )

            definition_texts = self._pick_distinct_texts(definition_rows, max_items=3)
            keypoint_texts = self._pick_distinct_texts(keypoint_rows, max_items=3)
            formula_texts = self._pick_distinct_texts(formula_rows, max_items=3)
            example_texts = self._pick_distinct_texts(example_rows, max_items=3)

            node["explanation_teacher_style"] = self.teacher_generator.generate_explanation(
                node_name=node_name,
                summary=str(node.get("summary", "")).strip(),
                definition_texts=definition_texts,
                keypoint_texts=keypoint_texts,
                formula_texts=formula_texts,
                example_texts=example_texts,
            )

            node["formulas"] = self._build_formula_list(formula_rows)
            node["examples"] = self._build_example_list(example_rows)

            node.setdefault("extra", {})
            node["extra"]["generation_status"] = "ok"
            node["extra"]["generation_debug"] = {
                "definition_hits": len(definition_rows),
                "keypoint_hits": len(keypoint_rows),
                "formula_hits": len(formula_rows),
                "example_hits": len(example_rows),
            }

        return nodes

    def _build_teacher_style_explanation(
        self,
        node_name: str,
        definition_rows: list[dict[str, Any]],
        keypoint_rows: list[dict[str, Any]],
    ) -> str:
        definition_text = self._pick_best_text(definition_rows)
        keypoint_texts = self._pick_distinct_texts(keypoint_rows, max_items=2)

        parts: list[str] = []

        if definition_text:
            parts.append(
                f"{node_name}可以先理解为：{definition_text}"
            )

        if keypoint_texts:
            parts.append("从学习重点来看，主要需要把握以下内容：")
            for idx, text in enumerate(keypoint_texts, start=1):
                parts.append(f"{idx}. {text}")

        if not parts:
            return ""

        return " ".join(parts)

    def _build_formula_list(self, formula_rows: list[dict[str, Any]]) -> list[str]:
        return self._pick_distinct_texts(formula_rows, max_items=3)

    def _build_example_list(self, example_rows: list[dict[str, Any]]) -> list[str]:
        return self._pick_distinct_texts(example_rows, max_items=3)

    def _pick_best_text(self, rows: list[dict[str, Any]]) -> str:
        if not rows:
            return ""
        return self._clean_text(str(rows[0].get("text", "")).strip())

    def _pick_distinct_texts(self, rows: list[dict[str, Any]], max_items: int = 3) -> list[str]:
        results: list[str] = []

        for row in rows:
            text = self._clean_text(str(row.get("text", "")).strip())
            if not text:
                continue
            if text not in results:
                results.append(text)
            if len(results) >= max_items:
                break

        return results

    def _clean_ocr_formula(self, text: str) -> str:
        text = text.replace("", "+")
        text = text.replace("", "-")
        text = text.replace("", "=")
        text = text.replace("", "π")
        text = text.replace("", "Σ")
        text = text.replace("", "Π")
        text = text.replace("", "±")
        text = text.replace("", "∠")

        text = re.sub(r"\s+", " ", text)

        # 一些常见 OCR 公式碎片修复
        text = text.replace("G s", "G(s)")
        text = text.replace("H s", "H(s)")
        text = text.replace("s p", "s-p")
        text = text.replace("s z", "s-z")
        text = text.replace("j ", "j")
        text = text.replace("( ", "(").replace(" )", ")")

        return text.strip()

    def _clean_text(self, text: str) -> str:
        text = text.replace("\n", " ").strip()
        text = " ".join(text.split())
        text = self._clean_ocr_formula(text)
        return text[:600]
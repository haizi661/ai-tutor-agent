from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pandas as pd

from ai_tutor_agent.knowledge_map.builders.node_selector import NodeSelector
from ai_tutor_agent.knowledge_map.builders.rag_answer_generator import RAGAnswerGenerator


class KnowledgeMapRAGQAPipeline:
    """
    图谱驱动的问答流程。

    支持：
    1. learning_path
    2. requirement_query
    3. prerequisite_query
    4. knowledge_qa
    """

    def __init__(
        self,
        nodes_csv_path: str = "data/knowledge_map_outputs/auto_control_knowledge_map_v2_nodes.csv",
    ) -> None:
        self.nodes_csv_path = Path(nodes_csv_path)
        self.node_selector = NodeSelector()
        self.answer_generator = RAGAnswerGenerator()
        self.nodes = self._load_nodes()
        self.node_map = {node["node_id"]: node for node in self.nodes}

    def ask(self, question: str) -> dict[str, Any]:
        question_type = self.node_selector.detect_question_type(question)
        matched_node = self.node_selector.select_node(question, self.nodes)

        retrieval_evidence: list[dict[str, Any]] = []

        # 只有普通知识问答才进入证据检索
        if question_type == "knowledge_qa" and matched_node is not None:
            retrieval_evidence = self._build_simple_evidence(matched_node)

        final_answer = self.answer_generator.generate_answer(
            question=question,
            question_type=question_type,
            matched_node=matched_node,
            retrieval_evidence=retrieval_evidence,
            node_map=self.node_map,
        )

        return {
            "question": question,
            "question_type": question_type,
            "matched_node": matched_node,
            "retrieval_evidence": retrieval_evidence,
            "final_answer": final_answer,
        }

    def _load_nodes(self) -> list[dict[str, Any]]:
        if not self.nodes_csv_path.exists():
            raise FileNotFoundError(f"节点表不存在: {self.nodes_csv_path}")

        df = pd.read_csv(self.nodes_csv_path)

        records = df.to_dict(orient="records")
        parsed_records = [self._parse_record(record) for record in records]
        return parsed_records

    def _parse_record(self, record: dict[str, Any]) -> dict[str, Any]:
        parsed = dict(record)

        list_like_fields = [
            "tags",
            "core_concepts",
            "key_points",
            "formulas",
            "examples",
            "figures_refs",
            "page_refs",
            "definition_candidates",
            "key_point_candidates",
            "formula_candidates",
            "example_candidates",
            "prerequisite_nodes",
            "next_nodes",
            "related_nodes",
            "application_nodes",
            "recommended_next_nodes",
        ]

        for field in list_like_fields:
            parsed[field] = self._safe_parse_python_literal(parsed.get(field))

        parsed["extra"] = self._safe_parse_python_literal(parsed.get("extra"), default={})

        return parsed

    def _safe_parse_python_literal(self, value: Any, default: Any = None) -> Any:
        if isinstance(value, (list, dict)):
            return value

        if value is None:
            return [] if default is None else default

        text = str(value).strip()
        if not text:
            return [] if default is None else default

        try:
            return ast.literal_eval(text)
        except Exception:
            return [] if default is None else default

    def _build_simple_evidence(self, matched_node: dict[str, Any]) -> list[dict[str, Any]]:
        evidence = []

        for text in (matched_node.get("definition_candidates", []) or [])[:2]:
            evidence.append({"text": text, "candidate_type": "definition"})

        for text in (matched_node.get("key_point_candidates", []) or [])[:2]:
            evidence.append({"text": text, "candidate_type": "key_point"})

        for text in (matched_node.get("example_candidates", []) or [])[:1]:
            evidence.append({"text": text, "candidate_type": "example"})

        return evidence
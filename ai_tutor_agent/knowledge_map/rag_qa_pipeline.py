from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from ai_tutor_agent.knowledge_map.builders.node_selector import NodeSelector
from ai_tutor_agent.knowledge_map.builders.rag_answer_generator import RagAnswerGenerator
from ai_tutor_agent.knowledge_map.builders.vector_retriever import VectorRetriever


class KnowledgeMapRAGPipeline:
    """
    最小可用版 RAG 问答：
    1. 读取 nodes.csv
    2. 粗选最相关节点
    3. 在该节点里做向量检索
    4. 用 DeepSeek 生成答案
    """

    def __init__(self, nodes_csv_path: str) -> None:
        self.nodes_csv_path = Path(nodes_csv_path)
        self.node_selector = NodeSelector()
        self.retriever = VectorRetriever()
        self.answer_generator = RagAnswerGenerator()

    def answer(self, question: str) -> dict[str, Any]:
        nodes_df = pd.read_csv(self.nodes_csv_path)
        nodes = nodes_df.to_dict(orient="records")

        best_node = self.node_selector.select_best_node(question, nodes)
        if not best_node:
            return {
                "question": question,
                "matched_node": None,
                "retrieval_rows": [],
                "answer": "未找到合适的知识点节点。",
            }

        node_id = str(best_node.get("node_id", "")).strip()
        node_name = str(best_node.get("name", "")).strip()

        retrieval_rows = self.retriever.retrieve(
            query=question,
            node_id=node_id,
            top_k=5,
            use_rerank=True,
            target_node_name=node_name,
        )

        contexts = [str(row.get("text", "")).strip() for row in retrieval_rows if row.get("text")]

        answer_text = self.answer_generator.generate_answer(
            question=question,
            node_name=node_name,
            contexts=contexts,
        )

        return {
            "question": question,
            "matched_node": {
                "node_id": node_id,
                "name": node_name,
                "chapter": best_node.get("chapter", ""),
                "summary": best_node.get("summary", ""),
            },
            "retrieval_rows": retrieval_rows,
            "answer": answer_text,
        }
from __future__ import annotations

from typing import Any

import chromadb
from chromadb.config import Settings

from ai_tutor_agent.knowledge_map.builders.retrieval_reranker import RetrievalReranker
from ai_tutor_agent.knowledge_map.config.retrieval_config import (
    COLLECTION_NAME,
    VECTOR_DB_DIR,
)


class VectorRetriever:
    """
    节点级向量检索器：
    - 支持按 node_id 过滤
    - 支持按 candidate_type 过滤
    - 支持检索后重排
    """

    def __init__(self) -> None:
        self.client = chromadb.PersistentClient(
            path=str(VECTOR_DB_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(name=COLLECTION_NAME)
        self.reranker = RetrievalReranker()

    def retrieve(
        self,
        query: str,
        node_id: str | None = None,
        candidate_types: list[str] | None = None,
        top_k: int = 5,
        use_rerank: bool = True,
        target_node_name: str | None = None,
    ) -> list[dict[str, Any]]:
        where_clause = self._build_where_clause(node_id=node_id, candidate_types=candidate_types)

        result = self.collection.query(
            query_texts=[query],
            n_results=max(top_k * 3, 10),
            where=where_clause if where_clause else None,
        )

        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        ids = result.get("ids", [[]])[0]

        rows: list[dict[str, Any]] = []
        for doc_id, doc, meta, dist in zip(ids, documents, metadatas, distances):
            rows.append(
                {
                    "doc_id": doc_id,
                    "text": doc,
                    "metadata": meta,
                    "distance": dist,
                }
            )

        if use_rerank:
            rows = self.reranker.rerank(
                query=query,
                rows=rows,
                target_node_name=target_node_name,
            )

        return rows[:top_k]

    def _build_where_clause(
        self,
        node_id: str | None,
        candidate_types: list[str] | None,
    ) -> dict[str, Any] | None:
        clauses: list[dict[str, Any]] = []

        if node_id:
            clauses.append({"node_id": node_id})

        if candidate_types:
            if len(candidate_types) == 1:
                clauses.append({"candidate_type": candidate_types[0]})
            else:
                clauses.append(
                    {
                        "$or": [{"candidate_type": item} for item in candidate_types]
                    }
                )

        if not clauses:
            return None

        if len(clauses) == 1:
            return clauses[0]

        return {"$and": clauses}
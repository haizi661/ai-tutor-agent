from __future__ import annotations

from typing import Any

import chromadb
from chromadb.config import Settings

from ai_tutor_agent.knowledge_map.config.retrieval_config import (
    CANDIDATE_FIELD_WEIGHTS,
    COLLECTION_NAME,
    VECTOR_DB_DIR,
)


class VectorIndexBuilder:
    """
    把节点候选池摊平，写入 Chroma 向量库。
    当前版本先用 Chroma 自带 embedding，避免你额外折腾。
    """

    def __init__(self) -> None:
        VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(VECTOR_DB_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection(name=COLLECTION_NAME)

    def rebuild_from_nodes(self, nodes: list[dict[str, Any]]) -> dict[str, Any]:
        """
        重建索引：
        1. 清空旧 collection
        2. 从 nodes 摊平候选文本
        3. 写入 Chroma
        """
        self._reset_collection()

        docs, ids, metadatas = self._flatten_nodes_to_documents(nodes)

        if docs:
            self.collection.add(
                documents=docs,
                ids=ids,
                metadatas=metadatas,
            )

        return {
            "collection_name": COLLECTION_NAME,
            "document_count": len(docs),
        }

    def _reset_collection(self) -> None:
        try:
            self.client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(name=COLLECTION_NAME)

    def _flatten_nodes_to_documents(
        self,
        nodes: list[dict[str, Any]],
    ) -> tuple[list[str], list[str], list[dict[str, Any]]]:
        docs: list[str] = []
        ids: list[str] = []
        metadatas: list[dict[str, Any]] = []

        doc_counter = 0

        for node in nodes:
            node_id = str(node.get("node_id", "")).strip()
            node_name = str(node.get("name", "")).strip()
            chapter = str(node.get("chapter", "")).strip()
            level = int(node.get("level", 1))
            page_refs = node.get("page_refs", []) or []
            extra = node.get("extra", {}) or {}
            refined_pages = extra.get("page_refs_refined", []) or []

            for field_name, weight in CANDIDATE_FIELD_WEIGHTS.items():
                candidates = node.get(field_name, []) or []
                for idx, candidate in enumerate(candidates):
                    text = str(candidate).strip()
                    if len(text) < 6:
                        continue

                    doc_counter += 1
                    doc_id = f"{node_id}_{field_name}_{idx+1:03d}"

                    docs.append(text)
                    ids.append(doc_id)
                    metadatas.append(
                        {
                            "node_id": node_id,
                            "node_name": node_name,
                            "chapter": chapter,
                            "level": level,
                            "candidate_type": field_name,
                            "candidate_rank": idx + 1,
                            "candidate_weight": float(weight),
                            "page_refs": ",".join(str(p) for p in page_refs),
                            "page_refs_refined": ",".join(str(p) for p in refined_pages),
                        }
                    )

        return docs, ids, metadatas
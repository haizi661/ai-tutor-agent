from __future__ import annotations

from ai_tutor_agent.knowledge_map.builders.vector_retriever import VectorRetriever


def print_rows(title: str, rows: list[dict]) -> None:
    print(f"\n=== {title} ===")
    for i, row in enumerate(rows, start=1):
        print(f"\n--- result {i} ---")
        print("doc_id:", row["doc_id"])
        print("distance:", row.get("distance"))
        if "rerank_score" in row:
            print("rerank_score:", row.get("rerank_score"))
        print("metadata:", row["metadata"])
        print("text:", row["text"])


def main() -> None:
    retriever = VectorRetriever()

    query1 = "什么是根轨迹法，它有什么作用"

    rows_raw = retriever.retrieve(
        query=query1,
        node_id="KM020",
        top_k=5,
        use_rerank=False,
    )
    print_rows("query 1 raw retrieval", rows_raw)

    rows_rerank = retriever.retrieve(
        query=query1,
        node_id="KM020",
        top_k=5,
        use_rerank=True,
        target_node_name="线性系统的根轨迹法",
    )
    print_rows("query 1 reranked retrieval", rows_rerank)

    query2 = "什么是根轨迹法"

    rows_rerank_def = retriever.retrieve(
        query=query2,
        node_id="KM020",
        candidate_types=["definition_candidates", "key_point_candidates"],
        top_k=5,
        use_rerank=True,
        target_node_name="线性系统的根轨迹法",
    )
    print_rows("query 2 reranked definition retrieval", rows_rerank_def)

    query3 = "根轨迹法的公式和方程是什么"

    rows_rerank_formula = retriever.retrieve(
        query=query3,
        node_id="KM020",
        candidate_types=["formula_candidates", "definition_candidates", "key_point_candidates"],
        top_k=5,
        use_rerank=True,
        target_node_name="线性系统的根轨迹法",
    )
    print_rows("query 3 reranked formula retrieval", rows_rerank_formula)


if __name__ == "__main__":
    main()
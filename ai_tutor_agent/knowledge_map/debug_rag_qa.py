from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

# 关闭代理，避免 DeepSeek 超时
os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""

from ai_tutor_agent.knowledge_map.rag_qa_pipeline import KnowledgeMapRAGPipeline


def main() -> None:
    pipeline = KnowledgeMapRAGPipeline(
        nodes_csv_path="data/knowledge_map_outputs/auto_control_knowledge_map_v2_nodes.csv"
    )

    questions = [
        "什么是根轨迹法？",
        "根轨迹法有什么作用？",
        "自动控制系统为什么要用负反馈？",
    ]

    for question in questions:
        result = pipeline.answer(question)

        print("\n" + "=" * 80)
        print("question:", result["question"])
        print("matched_node:", result["matched_node"])
        print("\nretrieval evidence:")
        for i, row in enumerate(result["retrieval_rows"], start=1):
            print(f"\n--- evidence {i} ---")
            print("doc_id:", row.get("doc_id"))
            print("rerank_score:", row.get("rerank_score"))
            print("metadata:", row.get("metadata"))
            print("text:", row.get("text"))

        print("\nfinal answer:")
        print(result["answer"])


if __name__ == "__main__":
    main()
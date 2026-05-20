from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

# 关闭代理，避免 DeepSeek 超时
os.environ["HTTP_PROXY"] = ""
os.environ["HTTPS_PROXY"] = ""

from ai_tutor_agent.knowledge_map.rag_qa_pipeline import KnowledgeMapRAGQAPipeline


def main() -> None:
    pipeline = KnowledgeMapRAGQAPipeline()

    test_questions = [
        "我接下来该学什么？",
        "学完自动控制的一般概念后学什么？",
        "控制系统的数学模型课程要求是什么？",
        "学习线性系统的时域分析法之前要先学什么？",
        "什么是自动控制的基本原理与方式？",
    ]

    for question in test_questions:
        print("\n" + "=" * 80)
        print("question:", question)

        result = pipeline.ask(question)

        matched_node = result.get("matched_node")
        print("question_type:", result.get("question_type"))
        print("matched_node:", matched_node.get("name") if matched_node else None)

        print("retrieval_evidence:")
        for item in result.get("retrieval_evidence", []):
            print("-", item)

        print("\nfinal_answer:")
        print(result.get("final_answer", ""))


if __name__ == "__main__":
    main()
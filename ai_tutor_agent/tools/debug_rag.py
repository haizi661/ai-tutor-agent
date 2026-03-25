import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from openai import OpenAI

try:
    from ..config import get_settings
    from ..infrastructure.retriever import LocalFileKnowledgeProvider
except ImportError:
    # Support direct file execution: python ai_tutor_agent/tools/debug_rag.py
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from ai_tutor_agent.config import get_settings
    from ai_tutor_agent.infrastructure.retriever import LocalFileKnowledgeProvider


@dataclass
class RetrievedChunk:
    rank: int
    score: Optional[float]
    content: str
    metadata: dict[str, Any]


class LLMQueryRewriter:
    def __init__(self, api_key: str, model: str, base_url: str):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def rewrite(self, question: str, chat_history: Optional[list[dict[str, str]]] = None) -> str:
        history_text = ""
        if chat_history:
            lines = []
            for msg in chat_history[-4:]:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                lines.append(f"{role}: {content}")
            history_text = "\n".join(lines)

        prompt = f"""
你是一个“面向学术论文知识库”的检索问题改写器。

任务：
把用户问题改写成更适合从论文、技术报告、研究文章中检索答案的表达。

改写要求：
1. 保留原意，不要回答问题
2. 补全代词指代，如“它”“这个方法”“这篇论文”“作者”
3. 优先改写成学术论文常见问法
4. 输出只能是一句话，不要解释，不要分点

历史对话：
{history_text if history_text else "无"}

当前用户问题：
{question}
""".strip()

        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=0.1,
            messages=[
                {"role": "system", "content": "你专门负责把自然语言问题改写为知识库检索问题。"},
                {"role": "user", "content": prompt},
            ],
        )
        return (resp.choices[0].message.content or "").strip()


class DebugKnowledgeSearcher:
    def __init__(self, provider: LocalFileKnowledgeProvider):
        self.provider = provider
        self.settings = provider.settings

    def search_raw(self, query: str, k: Optional[int] = None) -> list[RetrievedChunk]:
        k = k or self.settings.knowledge_top_k
        docs_and_scores = self.provider.query_with_scores(query, k=k)

        results: list[RetrievedChunk] = []
        for idx, (doc, score) in enumerate(docs_and_scores, start=1):
            results.append(
                RetrievedChunk(
                    rank=idx,
                    score=score,
                    content=doc.page_content,
                    metadata=doc.metadata or {},
                )
            )
        return results

    def search_reranked(self, query: str, recall_k: int = 8, final_k: int = 3) -> list[RetrievedChunk]:
        docs_and_scores = self.provider.query_with_scores(query, k=recall_k)
        reranked_docs = self.provider._section_rerank(docs_and_scores, final_k=final_k)

        score_map: dict[tuple[Any, Any, str], float] = {}
        for doc, score in docs_and_scores:
            key = (
                doc.metadata.get("filename", ""),
                doc.metadata.get("chunk_id", -1),
                (doc.page_content or "")[:100],
            )
            score_map[key] = score

        results: list[RetrievedChunk] = []
        for idx, doc in enumerate(reranked_docs, start=1):
            key = (
                doc.metadata.get("filename", ""),
                doc.metadata.get("chunk_id", -1),
                (doc.page_content or "")[:100],
            )
            results.append(
                RetrievedChunk(
                    rank=idx,
                    score=score_map.get(key),
                    content=doc.page_content,
                    metadata=doc.metadata or {},
                )
            )
        return results

    def search_hybrid(self, query: str, recall_k: int = 8, final_k: int = 3) -> list[RetrievedChunk]:
        vector_docs_and_scores = self.provider.query_with_scores(query, k=recall_k)

        score_map: dict[tuple[Any, Any, str], float] = {}
        for doc, score in vector_docs_and_scores:
            key = (
                doc.metadata.get("filename", ""),
                doc.metadata.get("chunk_id", -1),
                (doc.page_content or "")[:120],
            )
            score_map[key] = score

        docs = self.provider.query_hybrid(query, recall_k=recall_k, final_k=final_k)
        results: list[RetrievedChunk] = []
        for idx, doc in enumerate(docs, start=1):
            key = (
                doc.metadata.get("filename", ""),
                doc.metadata.get("chunk_id", -1),
                (doc.page_content or "")[:120],
            )
            results.append(
                RetrievedChunk(
                    rank=idx,
                    score=score_map.get(key),
                    content=doc.page_content,
                    metadata=doc.metadata or {},
                )
            )
        return results

    @staticmethod
    def pretty_print(original_query: str, rewritten_query: str, results: list[RetrievedChunk]) -> None:
        print("\n" + "=" * 100)
        print(f"[原问题]   {original_query}")
        print(f"[改写后]   {rewritten_query}")
        print(f"[命中数量] {len(results)}")
        print("=" * 100)

        if not results:
            print("没有检索到结果。")
            return

        for item in results:
            print(f"\n[Rank {item.rank}] score = {item.score}")
            print("[Metadata]")
            if item.metadata:
                for key, value in item.metadata.items():
                    print(f"  - {key}: {value}")
            else:
                print("  (无 metadata)")

            print("[Content Preview]")
            preview = item.content[:800].replace("\n", " ")
            print(preview)
            print("-" * 100)


def run_search_mode(
    searcher: DebugKnowledgeSearcher,
    *,
    mode: str,
    query: str,
    top_k: int,
    recall_k: int,
    final_k: int,
) -> list[RetrievedChunk]:
    if mode == "raw":
        return searcher.search_raw(query, k=top_k)
    if mode == "rerank":
        return searcher.search_reranked(query, recall_k=recall_k, final_k=final_k)
    return searcher.search_hybrid(query, recall_k=recall_k, final_k=final_k)


def build_report(
    *,
    mode: str,
    original_query: str,
    rewritten_query: str,
    results: list[RetrievedChunk],
) -> dict[str, Any]:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "original_query": original_query,
        "rewritten_query": rewritten_query,
        "result_count": len(results),
        "results": [asdict(item) for item in results],
    }


def save_report_json(path: str, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Debug RAG retrieval quality")
    parser.add_argument("--mode", choices=["hybrid", "raw", "rerank"], default="hybrid")
    parser.add_argument("--top-k", type=int, default=3, dest="top_k")
    parser.add_argument("--recall-k", type=int, default=8, dest="recall_k")
    parser.add_argument("--final-k", type=int, default=3, dest="final_k")
    parser.add_argument("--no-rewrite", action="store_true", dest="no_rewrite")
    parser.add_argument("--once", type=str, default="", help="Run one query and exit")
    parser.add_argument("--export", type=str, default="", help="Write retrieval report to a json file")
    return parser.parse_args(argv)


def build_rewriter_from_settings(settings):
    if settings.deepseek_api_key:
        return LLMQueryRewriter(
            api_key=settings.deepseek_api_key,
            model="deepseek-chat",
            base_url="https://api.deepseek.com/v1",
        )

    if settings.openai_api_key and settings.openai_api_base:
        return LLMQueryRewriter(
            api_key=settings.openai_api_key,
            model=settings.model_name,
            base_url=settings.openai_api_base,
        )

    raise RuntimeError("No rewrite model configured. Set DEEPSEEK_API_KEY or OPENAI_API_KEY.")


def _run_one_query(
    *,
    args: argparse.Namespace,
    searcher: DebugKnowledgeSearcher,
    rewriter: Optional[LLMQueryRewriter],
    question: str,
    chat_history: list[dict[str, str]],
) -> None:
    rewritten = question
    if rewriter is not None:
        rewritten = rewriter.rewrite(question, chat_history=chat_history)

    results = run_search_mode(
        searcher,
        mode=args.mode,
        query=rewritten,
        top_k=args.top_k,
        recall_k=args.recall_k,
        final_k=args.final_k,
    )
    searcher.pretty_print(question, rewritten, results)

    if args.export:
        payload = build_report(
            mode=args.mode,
            original_query=question,
            rewritten_query=rewritten,
            results=results,
        )
        save_report_json(args.export, payload)
        print(f"report exported to {args.export}")

    chat_history.append({"role": "user", "content": question})
    chat_history.append({"role": "assistant", "content": rewritten})


def main(argv: Optional[list[str]] = None) -> None:
    args = parse_args(argv)
    print("[debug-rag] booting...")
    settings = get_settings()

    print(f"knowledge_dir={settings.knowledge_dir}")
    print(f"embedding_provider={settings.embedding_provider}")
    print(f"embedding_model_name={settings.embedding_model_name}")
    print(f"knowledge_top_k={settings.knowledge_top_k}")
    print(f"mode={args.mode}")

    provider = LocalFileKnowledgeProvider(settings)
    searcher = DebugKnowledgeSearcher(provider)
    rewriter: Optional[LLMQueryRewriter] = None
    if not args.no_rewrite:
        try:
            rewriter = build_rewriter_from_settings(settings)
        except RuntimeError as exc:
            print(f"rewrite disabled: {exc}")

    print("\nready. input your question, or type exit.\n")

    chat_history: list[dict[str, str]] = []

    if args.once:
        _run_one_query(
            args=args,
            searcher=searcher,
            rewriter=rewriter,
            question=args.once,
            chat_history=chat_history,
        )
        return

    while True:
        question = input("question> ").strip()
        if not question:
            continue
        if question.lower() in {"exit", "quit", "q"}:
            print("bye")
            break

        _run_one_query(
            args=args,
            searcher=searcher,
            rewriter=rewriter,
            question=question,
            chat_history=chat_history,
        )


if __name__ == "__main__":
    main()

import os
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

from openai import OpenAI

from ai_tutor_agent.config import get_settings
from ai_tutor_agent.infrastructure.retriever import LocalFileKnowledgeProvider

#图表公式用
import subprocess
import sys
#----
@dataclass
class RetrievedChunk:
    rank: int
    score: Optional[float]
    content: str
    metadata: Dict[str, Any]


class LLMQueryRewriter:
    """
    用 DeepSeek / OpenAI 兼容接口做 query rewrite
    默认优先用 DeepSeek key；如果没配，则退回当前项目主模型配置
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
    ):
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def rewrite(
        self,
        question: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
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
4. 如果用户问：
   - “研究什么问题” -> 改写为“研究目标、核心问题或研究动机是什么”
   - “创新点” -> 改写为“主要创新点、核心贡献、相较已有方法的改进是什么”
   - “方法是什么” -> 改写为“提出了什么核心方法、方法框架或关键步骤”
   - “数据集” -> 改写为“实验中使用了哪些数据集、benchmark或评测任务”
   - “结论” -> 改写为“主要结论、发现或局限性是什么”
5. 输出只能是一句话，不要解释，不要分点

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
    """
    调试专用知识库检索器
    """

    def __init__(self, provider: LocalFileKnowledgeProvider):
        self.provider = provider
        self.settings = provider.settings

    def search_raw(self, query: str, k: Optional[int] = None) -> List[RetrievedChunk]:
        k = k or self.settings.knowledge_top_k

        # 这里要求你已经在 retriever.py 里加了 query_with_scores
        docs_and_scores = self.provider.query_with_scores(query, k=k)

        results: List[RetrievedChunk] = []
        for idx, item in enumerate(docs_and_scores, start=1):
            doc, score = item
            results.append(
                RetrievedChunk(
                    rank=idx,
                    score=score,
                    content=doc.page_content,
                    metadata=doc.metadata or {},
                )
            )
        return results

    def search_reranked(self, query: str, recall_k: int = 8, final_k: int = 3) -> List[RetrievedChunk]:
        docs_and_scores = self.provider.query_with_scores(query, k=recall_k)
        reranked_docs = self.provider._section_rerank(docs_and_scores, final_k=final_k)

        # 为了打印原始 score，这里重新映射一下
        score_map = {}
        for doc, score in docs_and_scores:
            key = (
                doc.metadata.get("filename", ""),
                doc.metadata.get("chunk_id", -1),
                (doc.page_content or "")[:100],
            )
            score_map[key] = score

        results = []
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

    def pretty_print(self, original_query: str, rewritten_query: str, results: List[RetrievedChunk]) -> None:
        print("\n" + "=" * 100)
        print(f"[原问题]   {original_query}")
        print(f"[改写后]   {rewritten_query}")
        print(f"[命中数量] {len(results)}")
        print("=" * 100)

        if not results:
            print("⚠️ 没有检索到任何结果。")
            return

        for item in results:
            print(f"\n[Rank {item.rank}] score = {item.score}")
            print("[Metadata]")

            meta = item.metadata or {}
            important_keys = [
                "block_type", "filename", "chunk_id", "section",
                "figure_id", "figure_caption", "image_path", "image_path_abs",
                "vlm_desc", "table_id", "latex", "char_length"
            ]
            for k in important_keys:
                if k in meta:
                    print(f"  - {k}: {meta[k]}")

            print("[Content Preview]")
            preview = item.content[:1000].replace("\n", " ")
            print(preview)
            print("-" * 100)

    def search_hybrid(self, query: str, recall_k: int = 8, final_k: int = 3) -> List[RetrievedChunk]:
        vector_docs_and_scores = self.provider.query_with_scores(query, k=recall_k)
        bm25_docs = self.provider.query_with_bm25(query, k=recall_k)

        score_map = {}
        for doc, score in vector_docs_and_scores:
            key = (
                doc.metadata.get("filename", ""),
                doc.metadata.get("chunk_id", -1),
                (doc.page_content or "")[:120],
            )
            score_map[key] = score

        docs = self.provider.query_hybrid(query, recall_k=recall_k, final_k=final_k)

        results = []
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
    

def rerank_by_section(results):
    """
    Chroma 返回的 score 越小越相似。
    这里做一个轻量的“规则修正分数”，然后重新排序。
    """
    good_keywords = [
        "abstract",
        "introduction",
        "method",
        "methodology",
        "experiment",
        "evaluation",
        "benchmark",
        "conclusion",
    ]

    bad_keywords = [
        "related work",
        "references",
        "acknowledgements",
        "author contributions",
        "appendix",
    ]

    reranked = []

    for item in results:
        score = item.score if item.score is not None else 999.0

        # 优先取统一 section，没有就退回 H1
        section = str(
            item.metadata.get("section") or item.metadata.get("H1") or ""
        ).lower()

        bonus = 0.0

        # 好章节：分数减小（更靠前）
        if any(k in section for k in good_keywords):
            bonus -= 0.12

        # 差章节：分数增大（更靠后）
        if any(k in section for k in bad_keywords):
            bonus += 0.35

        # 如果内容里明显出现 benchmarks / dataset，也给一点加成
        content_head = (item.content or "")[:300].lower()
        if any(k in content_head for k in ["benchmark", "benchmarks", "dataset", "datasets"]):
            bonus -= 0.08

        new_score = score + bonus
        reranked.append((new_score, item))

    reranked.sort(key=lambda x: x[0])

    final = []
    for idx, (_, item) in enumerate(reranked, start=1):
        item.rank = idx
        final.append(item)

    return final

def open_image_file(path: str):
    if not path or not os.path.exists(path):
        print(f"❌ 图片不存在: {path}")
        return

    try:
        if os.name == "nt":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.run(["open", path], check=False)
        else:
            subprocess.run(["xdg-open", path], check=False)
        print(f"🖼️ 已尝试打开图片: {path}")
    except Exception as e:
        print(f"❌ 打开图片失败: {e}")

def build_rewriter_from_settings(settings):
    """
    优先使用 DeepSeek；
    如果没配 DeepSeek，就退回项目当前主模型配置
    """
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

    raise RuntimeError("没有可用的改写模型配置。请至少在 .env 中配置 DEEPSEEK_API_KEY 或 OPENAI_API_KEY。")



def main():
    print("🚀 [DEBUG_RAG] 启动知识库调试模式...")

    # 关键：不能直接 Settings()，要走项目自己的配置入口
    settings = get_settings()

    print(f"📚 [DEBUG_RAG] knowledge_dir = {settings.knowledge_dir}")
    print(f"🧠 [DEBUG_RAG] embedding_provider = {settings.embedding_provider}")
    print(f"🧠 [DEBUG_RAG] embedding_model_name = {settings.embedding_model_name}")
    print(f"🔢 [DEBUG_RAG] knowledge_top_k = {settings.knowledge_top_k}")

    provider = LocalFileKnowledgeProvider(settings)
    searcher = DebugKnowledgeSearcher(provider)
    rewriter = build_rewriter_from_settings(settings)

    print("\n✅ 调试器已就绪。输入问题开始检索；输入 exit 退出。\n")

    chat_history: List[Dict[str, str]] = []

    last_results: List[RetrievedChunk] = []

    while True:
        question = input("请输入测试问题: ").strip()
        if not question:
            continue

        if question.lower() in {"exit", "quit", "q"}:
            print("👋 已退出 debug_rag。")
            break

        if question.lower().startswith("figonly:"):
            raw_q = question[len("figonly:"):].strip()
            docs = provider.query_with_scores_filtered(raw_q, k=8, block_types=["figure"])
            results = []
            for idx, (doc, score) in enumerate(docs[:3], start=1):
                results.append(
                    RetrievedChunk(
                        rank=idx,
                        score=score,
                        content=doc.page_content,
                        metadata=doc.metadata or {},
                    )
                )
            searcher.pretty_print(raw_q, raw_q, results)
            last_results = results
            continue

        if question.lower().startswith("open "):
            try:
                idx = int(question.split()[1]) - 1
                if idx < 0 or idx >= len(last_results):
                    print("❌ rank 越界")
                    continue

                meta = last_results[idx].metadata or {}
                block_type = meta.get("block_type")

                if block_type != "figure":
                    print(f"❌ Rank {idx+1} 不是 figure 结果，而是 {block_type}，无法打开图片。")
                    continue

                path = meta.get("image_path_abs")
                if not path:
                    print("❌ 该 figure 没有 image_path_abs")
                    continue

                open_image_file(path)

            except Exception as exc:
                print(f"❌ open 命令失败: {exc}")

            continue

        try:
            q_lower = question.lower()
            if any(k in q_lower for k in ["figure", "fig.", "图", "表格", "table", "公式", "equation"]):
                rewritten = question
            else:
                rewritten = rewriter.rewrite(question, chat_history=chat_history)
            results = searcher.search_hybrid(rewritten, recall_k=8, final_k=3)
            searcher.pretty_print(question, rewritten, results)
            last_results = results

            chat_history.append({"role": "user", "content": question})
            chat_history.append({"role": "assistant", "content": rewritten})

        except Exception as exc:
            print(f"❌ 调试失败: {exc}")



if __name__ == "__main__":
    main()
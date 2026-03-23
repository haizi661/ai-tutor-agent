import glob
import os
import shutil
import json
from typing import List

import httpx
import fitz  # PyMuPDF

from langchain_core.documents import Document
from langchain_chroma import Chroma

from ..config import Settings
from ..core.ports import KnowledgeProvider
#--知识库构建新增
import re
from rank_bm25 import BM25Okapi
import dashscope
from .processor import KnowledgeProcessor
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
#---
#解决挂了梯子做不了mineru和千问embedding问题--实际没解决啊哈哈
def disable_proxy_for_current_process():
    """禁用当前 Python 进程的代理环境变量，不影响系统和浏览器"""
    proxy_keys = [
        "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
        "http_proxy", "https_proxy", "all_proxy",
    ]
    removed = []
    for key in proxy_keys:
        if key in os.environ:
            removed.append(f"{key}={os.environ.get(key)}")
            os.environ.pop(key, None)

    if removed:
        print("🌐 [DEBUG] 已禁用当前进程代理环境变量:")
        for item in removed:
            print(f"   - {item}")
    else:
        print("🌐 [DEBUG] 当前进程未检测到代理环境变量")

def build_embedding_backend(settings: Settings):
    provider = settings.embedding_provider

    # --- 新增：千问 Embedding 支持 ---
    if provider == "dashscope":
        from langchain_community.embeddings import DashScopeEmbeddings
        return DashScopeEmbeddings(
            model="text-embedding-v2", 
            dashscope_api_key=settings.dashscope_api_key
        )
     # ---    
    if provider == "local":
        if "/" not in settings.embedding_model_name:
            raise RuntimeError(
                "Local embedding expects a HuggingFace-style model name such as "
                "'sentence-transformers/all-MiniLM-L6-v2'. "
                f"Current EMBEDDING_MODEL_NAME={settings.embedding_model_name!r}. "
                "If you want to use Google embedding, set EMBEDDING_PROVIDER=google."
            )
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(model_name=settings.embedding_model_name)

    if provider == "google":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(
            model=settings.embedding_model_name,
            google_api_key=settings.google_api_key,
            transport="rest",
        )

    if provider == "openai":
        from langchain_openai import OpenAIEmbeddings
        kwargs = {
            "model": settings.embedding_model_name,
            "api_key": settings.openai_api_key,
        }
        if settings.openai_api_base:
            kwargs["base_url"] = settings.openai_api_base
        proxy_url = settings.http_proxy or settings.https_proxy
        if proxy_url:
            kwargs["http_client"] = httpx.Client(proxy=proxy_url)
        return OpenAIEmbeddings(**kwargs)

    raise RuntimeError(f"Unsupported EMBEDDING_PROVIDER: {provider}")

@dataclass
class ScoredChunk:
    doc: Document
    score: float
    adjusted_score: float
    metadata: Dict[str, Any]

#新增mineru处理逻辑
class LocalFileKnowledgeProvider(KnowledgeProvider):
    def __init__(self, settings: Settings):
        print(f"🚀 [CRITICAL DEBUG] RAG 2.0 引擎启动中...")
        disable_proxy_for_current_process()
        self.settings = settings

        # 0. 初始化知识库索引文件（用于避免重复处理）
        self.index_file = os.path.join("data", "knowledge_index.json")
        self.knowledge_index = self._load_index()

        # 1. 强制检查并构建 Embedding
        self.embeddings = build_embedding_backend(settings)
        print(f"🧬 [DEBUG] Embedding Provider: {settings.embedding_provider}")
        print(f"🧬 [DEBUG] 使用类: {type(self.embeddings).__name__}")

        # 2. 初始化向量库 (注意：collection_name 统一用 knowledge)
        self.vector_store = Chroma(
            collection_name="knowledge",
            embedding_function=self.embeddings,
            persist_directory=self.settings.chroma_dir,
        )

        # 3. 初始化 MinerU 处理器
        token_len = len(settings.mineru_api_token) if settings.mineru_api_token else 0
        print(f"📡 [DEBUG] MinerU Token 载入中, 长度: {token_len}")
        self.processor = KnowledgeProcessor(api_token=settings.mineru_api_token)

        # 4. 执行自动同步 (扫描本地 data/knowledge 目录)
        print(f"🔄 [DEBUG] 开始扫描本地目录并同步...")
        self._sync_knowledge_dir()
        print(f"✅ [DEBUG] 知识库初始化全流程完成。")

        self.bm25 = None
        self.bm25_docs = []
        self._build_bm25_index()
        print(f"✅ [DEBUG] BM25 索引建立完成，共 {len(self.bm25_docs)} 个文档。")

    def _load_index(self):
        """加载已处理文件索引"""
        if os.path.exists(self.index_file):
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    print(f"📚 [DEBUG] 已加载知识库索引，共 {len(data)} 条记录")
                    return data
            except Exception as e:
                print(f"⚠️ [DEBUG] 读取知识库索引失败，将使用空索引: {e}")
        return {}

    def _save_index(self):
        """保存已处理文件索引"""
        try:
            os.makedirs(os.path.dirname(self.index_file), exist_ok=True)
            with open(self.index_file, "w", encoding="utf-8") as f:
                json.dump(self.knowledge_index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ [DEBUG] 保存知识库索引失败: {e}")

    def _get_file_fingerprint(self, file_path: str) -> str:
        """生成文件指纹：文件名 + 大小 + 修改时间"""
        stat = os.stat(file_path)
        return f"{os.path.basename(file_path)}_{stat.st_size}_{int(stat.st_mtime)}"

    def _should_process(self, file_path: str) -> bool:
        """判断文件是否需要处理"""
        filename = os.path.basename(file_path)
        fingerprint = self._get_file_fingerprint(file_path)

        old_record = self.knowledge_index.get(filename)
        if old_record and old_record.get("fingerprint") == fingerprint:
            print(f"⏭️ [DEBUG] 跳过未变化文件: {filename}")
            return False

        print(f"🆕 [DEBUG] 检测到新文件或已变更文件: {filename}")
        return True
    def _delete_existing_vectors(self, filename: str):
        """删除某个文件对应的旧向量"""
        try:
            print(f"🧹 [DEBUG] 尝试删除旧向量: {filename}")
            self.vector_store._collection.delete(
                where={"filename": filename}
            )
            print(f"✅ [DEBUG] 旧向量删除完成: {filename}")
        except Exception as e:
            print(f"⚠️ [DEBUG] 删除旧向量失败: {filename}, 错误: {e}")

    def _sync_knowledge_dir(self):
        """扫描目录，仅处理新增或变更文件"""
        if not os.path.exists(self.settings.knowledge_dir):
            os.makedirs(self.settings.knowledge_dir)

        # 先清理磁盘上已删除的文件
        self._cleanup_deleted_files()

        files = glob.glob(os.path.join(self.settings.knowledge_dir, "*.*"))
        for f in files:
            if self._should_process(f):
                self.add_local_file(f)

    def _parse_file(self, file_path: str) -> List[Document]:
        ext = os.path.splitext(file_path)[1].lower()
        print(f"📂 [DEBUG] 正在解析文件: {os.path.basename(file_path)}")

        if ext == ".pdf":
            print(f"🔥 [FIRE] 强制进入 MinerU 解析路径！")
            # 这里的调用会产生 MinerU 费用和用量
            md_content = self.processor.parse_pdf_to_md(file_path)
            return self.processor.split_by_semantics(md_content)

        if ext == ".txt":
            from langchain_community.document_loaders import TextLoader
            loader = TextLoader(file_path, encoding="utf-8")
            return loader.load_and_split()

        return []
    def _cleanup_deleted_files(self):
        """清理已经从 knowledge_dir 删除的文件对应的向量和索引"""
        current_files = {
            os.path.basename(f)
            for f in glob.glob(os.path.join(self.settings.knowledge_dir, "*.*"))
        }

        indexed_files = set(self.knowledge_index.keys())
        deleted_files = indexed_files - current_files

        for filename in deleted_files:
            print(f"🗑️ [DEBUG] 检测到文件已被删除，正在清理向量和索引: {filename}")
            self._delete_existing_vectors(filename)
            self.knowledge_index.pop(filename, None)

        if deleted_files:
            self._save_index()
            print(f"✅ [DEBUG] 已完成删除文件清理，共 {len(deleted_files)} 个")

    def add_local_file(self, source_path: str) -> dict:
        filename = os.path.basename(source_path)
        print(f"📥 [DEBUG] 处理文件: {filename}")

        fingerprint = self._get_file_fingerprint(source_path)
        old_record = self.knowledge_index.get(filename)

        # 如果这个文件以前处理过，但现在变了，先删旧向量
        if old_record is not None:
            old_fingerprint = old_record.get("fingerprint")
            if old_fingerprint != fingerprint:
                print(f"♻️ [DEBUG] 检测到文件已更新，准备删除旧向量后重建: {filename}")
                self._delete_existing_vectors(filename)

        docs = self._parse_file(source_path)
        if docs:
            # 给每个 chunk 打 metadata，方便后续删除和追踪
            for doc in docs:
                if doc.metadata is None:
                    doc.metadata = {}
                doc.metadata["source"] = source_path
                doc.metadata["filename"] = filename
                doc.metadata["fingerprint"] = fingerprint

            print(f"🧬 [DEBUG] 正在向量化 {len(docs)} 个片段...")

            for i, doc in enumerate(docs):
                text = (doc.page_content or "").strip()
                print(f"   [CHUNK {i}] 长度: {len(text)}")
                
            self.vector_store.add_documents(docs)

            # 成功后记录索引
            self.knowledge_index[filename] = {
                "fingerprint": fingerprint,
                "chunks": len(docs),
            }
            self._save_index()

            print(f"✅ [DEBUG] 文件处理完成并已写入索引: {filename}")
            return {"success": True, "chunks": len(docs)}

        return {"success": False, "chunks": 0}
    
    def _tokenize_for_bm25(self, text: str) -> list[str]:
        text = (text or "").lower()
        tokens = re.findall(r"[a-zA-Z0-9_\-\.\(\)]+|[\u4e00-\u9fff]+", text)
        return tokens

    def _build_bm25_index(self):
        """
        从当前 Chroma 中取出所有文档，建立 BM25 索引
        """
        try:
            raw = self.vector_store._collection.get(include=["documents", "metadatas"])
            docs = raw.get("documents", [])
            metas = raw.get("metadatas", [])

            self.bm25_docs = []
            tokenized_corpus = []

            for doc_text, meta in zip(docs, metas):
                if not doc_text:
                    continue
                self.bm25_docs.append(
                    Document(
                        page_content=doc_text,
                        metadata=meta or {}
                    )
                )
                tokenized_corpus.append(self._tokenize_for_bm25(doc_text))

            if tokenized_corpus:
                self.bm25 = BM25Okapi(tokenized_corpus)
                print(f"🔎 [DEBUG] BM25 索引构建完成，共 {len(self.bm25_docs)} 个文档块")
            else:
                self.bm25 = None
                print("⚠️ [DEBUG] BM25 索引未构建：没有可用文档")
        except Exception as e:
            self.bm25 = None
            self.bm25_docs = []
            print(f"⚠️ [DEBUG] BM25 索引构建失败: {e}")

    def query_with_bm25(self, query: str, k: int = 5) -> list[Document]:
        if not self.bm25 or not self.bm25_docs:
            return []

        query_tokens = self._tokenize_for_bm25(query)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)

        ranked = sorted(
            zip(self.bm25_docs, scores),
            key=lambda x: x[1],
            reverse=True
        )

        results = []
        for doc, score in ranked[:k]:
            meta = dict(doc.metadata or {})
            meta["_bm25_score"] = float(score)
            results.append(
                Document(
                    page_content=doc.page_content,
                    metadata=meta
                )
            )
        return results

    def query_hybrid(self, query: str, recall_k: int = 8, final_k: int | None = None) -> list[Document]:
        """
        混合检索：
        1. 向量召回
        2. BM25召回
        3. 合并去重
        4. 走现有轻量 rerank
        """
        final_k = final_k or self.settings.knowledge_top_k

        vector_docs_and_scores = self.query_with_scores(query, k=recall_k)
        vector_docs = [doc for doc, _ in vector_docs_and_scores]

        bm25_docs = self.query_with_bm25(query, k=recall_k)

        merged = []
        seen = set()

        def doc_key(doc: Document):
            meta = doc.metadata or {}
            return (
                meta.get("filename", ""),
                meta.get("chunk_id", -1),
                (doc.page_content or "")[:120]
            )

        # 先放向量召回
        for doc, score in vector_docs_and_scores:
            key = doc_key(doc)
            if key in seen:
                continue
            seen.add(key)
            merged.append((doc, score))

        # 再补 BM25 召回
        for doc in bm25_docs:
            key = doc_key(doc)
            if key in seen:
                continue
            seen.add(key)
            # BM25 结果没有向量 score，先给一个中性较大值
            merged.append((doc, 999.0))

        return self._section_rerank(merged, final_k=final_k)






    def query_with_docs(self, query: str, k: int | None = None) -> List[Document]:
        k = k or self.settings.knowledge_top_k
        return self.vector_store.similarity_search(query, k=k)

    def query_with_scores(self, query: str, k: int | None = None):
        k = k or self.settings.knowledge_top_k
        return self.vector_store.similarity_search_with_score(query, k=k)

    def _section_rerank(self, docs_and_scores, final_k: int | None = None) -> List[Document]:
        """
        对召回结果做轻量规则重排：
        - 好章节加权
        - 差章节降权
        - dataset / benchmark 关键词轻微加权
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

        reranked: List[ScoredChunk] = []

        for doc, score in docs_and_scores:
            meta = doc.metadata or {}
            section = str(meta.get("section") or meta.get("H1") or "").lower()
            content_head = (doc.page_content or "")[:300].lower()

            bonus = 0.0

            # 好章节：分数更小
            if any(k in section for k in good_keywords):
                bonus -= 0.12

            # 差章节：分数更大
            if any(k in section for k in bad_keywords):
                bonus += 0.35

            # 明显的表格块稍微降权
            if "<table>" in content_head:
                bonus += 0.12

            # dataset / benchmark 问题时常有帮助，轻微加权
            if any(k in content_head for k in ["benchmark", "benchmarks", "dataset", "datasets"]):
                bonus -= 0.08

            adjusted_score = score + bonus

            reranked.append(
                ScoredChunk(
                    doc=doc,
                    score=score,
                    adjusted_score=adjusted_score,
                    metadata=meta,
                )
            )

        reranked.sort(key=lambda x: x.adjusted_score)

        final_k = final_k or self.settings.knowledge_top_k
        return [item.doc for item in reranked[:final_k]]

    def query_reranked(self, query: str, recall_k: int = 8, final_k: int | None = None) -> List[Document]:
        docs_and_scores = self.query_with_scores(query, k=recall_k)
        return self._section_rerank(docs_and_scores, final_k=final_k)

    def query(self, query: str) -> str:
        results = self.query_hybrid(
            query=query,
            recall_k=8,
            final_k=self.settings.knowledge_top_k
        )
        return "\n\n".join([doc.page_content for doc in results])

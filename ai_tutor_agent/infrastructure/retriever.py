import glob
import os
import shutil
from typing import List

import httpx
import fitz  # PyMuPDF

from langchain_core.documents import Document
from langchain_chroma import Chroma

from ..config import Settings
from ..core.ports import KnowledgeProvider
#--知识库构建新增
import dashscope
from .processor import KnowledgeProcessor
#---
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

#新增mineru处理逻辑
class LocalFileKnowledgeProvider(KnowledgeProvider):
    def __init__(self, settings: Settings):
        print(f"🚀 [CRITICAL DEBUG] RAG 2.0 引擎启动中...")
        self.settings = settings
        
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

    def _sync_knowledge_dir(self):
        """扫描目录，发现新文件则调用解析"""
        if not os.path.exists(self.settings.knowledge_dir):
            os.makedirs(self.settings.knowledge_dir)
            
        files = glob.glob(os.path.join(self.settings.knowledge_dir, "*.*"))
        for f in files:
            # 这里简单判断一下是否已存在，实际生产环境建议存 md5
            # 为了测试，我们现在主要是看 _parse_file 是否被触发
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

    def add_local_file(self, source_path: str) -> dict:
        # 这里为了防止重复添加，可以加一个简单的判断
        # 但为了看 Debug 日志，我们直接跑解析
        filename = os.path.basename(source_path)
        print(f"📥 [DEBUG] 处理文件: {filename}")
        
        docs = self._parse_file(source_path)
        if docs:
            print(f"🧬 [DEBUG] 正在向量化 {len(docs)} 个片段...")
            self.vector_store.add_documents(docs)
            return {"success": True, "chunks": len(docs)}
        return {"success": False, "chunks": 0}

    def query(self, query: str) -> str:
        # ... 保持你的 query 逻辑不变 ...
        results = self.vector_store.similarity_search(query, k=self.settings.knowledge_top_k)
        return "\n\n".join([doc.page_content for doc in results])


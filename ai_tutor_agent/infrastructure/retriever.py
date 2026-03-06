import glob
import os
import shutil
from typing import List

import httpx

from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from pypdf import PdfReader

from ..config import Settings
from ..core.ports import KnowledgeProvider


def build_embedding_backend(settings: Settings):
    provider = settings.embedding_provider

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


def chunk_text(text: str, *, chunk_size: int, chunk_overlap: int) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        return []

    if chunk_size <= 0:
        return [cleaned]

    overlap = max(0, min(chunk_overlap, chunk_size - 1)) if chunk_size > 1 else 0
    step = max(1, chunk_size - overlap)
    chunks: list[str] = []
    start = 0

    while start < len(cleaned):
        chunk = cleaned[start:start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        if start + chunk_size >= len(cleaned):
            break
        start += step

    return chunks


class LocalFileKnowledgeProvider(KnowledgeProvider):
    def __init__(self, settings: Settings):
        self.settings = settings
        self.vector_store = None

        try:
            print(
                f"🚀 正在加载知识检索引擎 "
                f"({settings.embedding_provider}:{settings.embedding_model_name})..."
            )
            self.embeddings = build_embedding_backend(settings)
            self.vector_store = InMemoryVectorStore(self.embeddings)
            self._load_documents()
        except Exception as e:
            print(f"⚠️ 本地知识库引擎加载失败: {e}")
            print("   系统将回退到无 RAG 模式运行。")

    def _parse_file(self, file_path: str) -> List[Document]:
        documents = []
        try:
            content = ""
            if file_path.lower().endswith(".pdf"):
                reader = PdfReader(file_path)
                for page_number, page in enumerate(reader.pages, start=1):
                    text = page.extract_text()
                    if text:
                        content += f"\n[Page {page_number}]\n{text}\n"
            else:
                with open(file_path, "r", encoding="utf-8") as file_obj:
                    content = file_obj.read()

            for index, chunk in enumerate(
                chunk_text(
                    content,
                    chunk_size=self.settings.knowledge_chunk_size,
                    chunk_overlap=self.settings.knowledge_chunk_overlap,
                )
            ):
                documents.append(
                    Document(
                        page_content=chunk,
                        metadata={"source": file_path, "chunk_index": index},
                    )
                )
        except Exception as e:
            print(f"❌ 解析文件失败 {file_path}: {e}")
        return documents

    def _load_documents(self):
        if not self.vector_store:
            return

        knowledge_dir = self.settings.knowledge_dir
        if not os.path.exists(knowledge_dir):
            os.makedirs(knowledge_dir, exist_ok=True)
            return

        extensions = ["**/*.txt", "**/*.md", "**/*.pdf"]
        files = []
        for ext in extensions:
            files.extend(glob.glob(os.path.join(knowledge_dir, ext), recursive=True))

        documents = []
        for file_path in files:
            docs = self._parse_file(file_path)
            if docs:
                documents.extend(docs)
                print(f"✅ 已提取文件内容: {os.path.basename(file_path)} ({len(docs)} chunks)")

        if documents:
            try:
                print(f"⏳ 正在为 {len(documents)} 个文本块建立本地向量索引，请稍候...")
                self.vector_store.add_documents(documents)
                print("✨ 成功建立本地向量索引，知识库就绪！")
            except Exception as e:
                print(f"⚠️ 无法为文档建立索引: {e}")
                print("   RAG 功能暂时不可用，但你依然可以进行普通对话。")

    def add_document(self, source_path: str) -> bool:
        if not self.vector_store:
            print("⚠️ 向量引擎未就绪，无法上传文档。")
            return False

        if not os.path.exists(source_path):
            print(f"❌ 找不到文件: {source_path}")
            return False

        knowledge_dir = self.settings.knowledge_dir
        os.makedirs(knowledge_dir, exist_ok=True)

        filename = os.path.basename(source_path)
        dest_path = os.path.join(knowledge_dir, filename)

        try:
            shutil.copy2(source_path, dest_path)
            docs = self._parse_file(dest_path)
            if docs:
                print("⏳ 正在处理新文档并建立索引...")
                self.vector_store.add_documents(docs)
                print(f"🎉 成功导入知识库: {filename}")
                return True
            print(f"⚠️ 文件内容为空: {filename}")
            return False
        except Exception as e:
            print(f"❌ 上传失败: {e}")
            return False

    def query(self, query: str) -> str:
        if not self.vector_store:
            return ""

        try:
            results = self.vector_store.similarity_search(
                query,
                k=self.settings.knowledge_top_k,
            )
            if not results:
                return ""
            return "\n---\n".join([doc.page_content for doc in results])
        except Exception as e:
            print(f"⚠️ 知识检索失败: {e}")
            return ""

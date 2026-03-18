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
        chunk = cleaned[start : start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        if start + chunk_size >= len(cleaned):
            break
        start += step

    return chunks


def _parse_pdf(file_path: str) -> str:
    """用 PyMuPDF 解析 PDF，提取所有页面文本。"""
    text = ""
    try:
        doc = fitz.open(file_path)
        for page_number, page in enumerate(doc, start=1):
            page_text = page.get_text()
            if page_text.strip():
                text += f"\n[Page {page_number}]\n{page_text}\n"
        doc.close()
    except Exception as e:
        print(f"❌ PyMuPDF 解析失败 {file_path}: {e}")
    return text


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

            # ChromaDB 持久化目录
            chroma_dir = getattr(settings, "chroma_dir", None) or os.path.join(
                os.path.dirname(settings.knowledge_dir), "chroma_db"
            )
            os.makedirs(chroma_dir, exist_ok=True)

            self.vector_store = Chroma(
                collection_name="knowledge",
                embedding_function=self.embeddings,
                persist_directory=chroma_dir,
            )
            self._chroma_dir = chroma_dir

            # 启动时同步本地文件目录（只加载尚未在 Chroma 里的文件）
            self._sync_knowledge_dir()

        except Exception as e:
            print(f"⚠️ 本地知识库引擎加载失败: {e}")
            print("   系统将回退到无 RAG 模式运行。")

    def _parse_file(self, source_path: str) -> List[Document]:
        import os
        import fitz  # PyMuPDF
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        
        filename = os.path.basename(source_path)
        ext = os.path.splitext(filename)[1].lower()
        full_text = ""

        # 1. 提取文本内容
        if ext == ".pdf":
            try:
                doc = fitz.open(source_path)
                for page in doc:
                    full_text += page.get_text("text") + "\n"
                doc.close()
            except Exception as e:
                print(f"PDF 解析出错: {e}")
        elif ext in [".md", ".txt"]:
            with open(source_path, "r", encoding="utf-8") as f:
                full_text = f.read()

        if not full_text.strip():
            return []

        # 2. RAG 2.0 语义切片逻辑
        # 按照 Markdown 标题和段落进行智能切分，保证知识点不被切断
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.settings.knowledge_chunk_size,
            chunk_overlap=self.settings.knowledge_chunk_overlap,
            separators=["\n# ", "\n## ", "\n### ", "\n\n", "\n", " "]
        )
        
        chunks = splitter.split_text(full_text)
        
        # 3. 封装成带元数据的文档
        docs = []
        for i, chunk in enumerate(chunks):
            docs.append(Document(
                page_content=chunk,
                metadata={
                    "source": filename,
                    "chunk_id": i,
                    "type": "static_knowledge"
                }
            ))
        return docs

    def _get_indexed_sources(self) -> set[str]:
        """从 Chroma 里取出已经索引过的文件路径集合。"""
        if not self.vector_store:
            return set()
        try:
            result = self.vector_store._collection.get(include=["metadatas"])
            sources = {m.get("source", "") for m in result["metadatas"] if m.get("source")}
            return sources
        except Exception:
            return set()

    def _sync_knowledge_dir(self):
        """启动时扫描 knowledge_dir，把还没入库的文件加进 Chroma。"""
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

        if not files:
            print("📂 知识库目录为空，跳过索引。")
            return

        indexed = self._get_indexed_sources()
        new_files = [f for f in files if os.path.abspath(f) not in indexed and f not in indexed]

        if not new_files:
            print(f"✅ 知识库已是最新，共 {len(files)} 个文件，无需重建索引。")
            return

        print(f"📚 发现 {len(new_files)} 个新文件，开始建立索引...")
        all_docs = []
        for file_path in new_files:
            docs = self._parse_file(file_path)
            if docs:
                all_docs.extend(docs)
                print(f"  ✅ {os.path.basename(file_path)} ({len(docs)} chunks)")

        if all_docs:
            try:
                print(f"⏳ 正在向量化 {len(all_docs)} 个文本块...")
                self.vector_store.add_documents(all_docs)
                print("✨ 索引建立完成，知识库就绪！")
            except Exception as e:
                print(f"⚠️ 向量化失败: {e}")

    def add_document(self, source_path: str) -> dict:
        """
        上传新文件到知识库。
        返回 dict: {"success": bool, "chunks": int, "filename": str, "message": str}
        """
        result = {"success": False, "chunks": 0, "filename": os.path.basename(source_path), "message": ""}

        if not self.vector_store:
            result["message"] = "向量引擎未就绪，无法上传文档。"
            print(f"⚠️ {result['message']}")
            return result

        if not os.path.exists(source_path):
            result["message"] = f"找不到文件: {source_path}"
            print(f"❌ {result['message']}")
            return result

        knowledge_dir = self.settings.knowledge_dir
        os.makedirs(knowledge_dir, exist_ok=True)

        filename = os.path.basename(source_path)
        dest_path = os.path.join(knowledge_dir, filename)

        try:
            shutil.copy2(source_path, dest_path)
            docs = self._parse_file(dest_path)

            if not docs:
                result["message"] = f"文件内容为空或解析失败: {filename}"
                print(f"⚠️ {result['message']}")
                return result

            print(f"⏳ 正在处理 {filename}（{len(docs)} chunks）并建立索引...")
            self.vector_store.add_documents(docs)
            result["success"] = True
            result["chunks"] = len(docs)
            result["message"] = f"成功导入知识库: {filename}"
            print(f"🎉 {result['message']}")
            return result

        except Exception as e:
            result["message"] = f"上传失败: {e}"
            print(f"❌ {result['message']}")
            return result

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
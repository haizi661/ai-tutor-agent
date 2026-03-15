import glob
import json
import os
import shutil
from datetime import datetime
from typing import Any, List, Optional

import httpx

from langchain_core.documents import Document
from langchain_core.vectorstores import InMemoryVectorStore
from pypdf import PdfReader

from ..config import Settings
from ..core.ports import KnowledgeProvider


def resolve_local_embedding_model_path(model_name: str) -> str:
    from huggingface_hub import snapshot_download

    try:
        return snapshot_download(repo_id=model_name, local_files_only=True)
    except Exception as exc:
        raise RuntimeError(
            "Local embedding model was not found in the local HuggingFace cache: "
            f"{model_name}. To avoid blocking startup on repeated download retries, "
            "AI Tutor will skip RAG for now. Pre-download this model first, or switch "
            "EMBEDDING_PROVIDER to google/openai."
        ) from exc


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

        model_path = resolve_local_embedding_model_path(settings.embedding_model_name)
        return HuggingFaceEmbeddings(model_name=model_path)

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
        self.manifest_path = os.path.join(self.settings.knowledge_dir, ".rag_manifest.json")
        self._manifest: dict[str, dict[str, Any]] = {}

        try:
            print(
                f"🚀 正在加载知识检索引擎 "
                f"({settings.embedding_provider}:{settings.embedding_model_name})..."
            )
            self.embeddings = build_embedding_backend(settings)
            self.vector_store = self._build_vector_store()
            self._sync_documents()
        except Exception as e:
            print(f"⚠️ 本地知识库引擎加载失败: {e}")
            print("   系统将回退到无 RAG 模式运行。")

    def _build_vector_store(self):
        backend = self.settings.vector_store_backend
        if backend == "inmemory":
            return InMemoryVectorStore(self.embeddings)

        if backend == "chroma":
            try:
                from langchain_chroma import Chroma
            except Exception as exc:
                print("⚠️ 未安装 langchain-chroma/chromadb，自动回退到 InMemoryVectorStore。")
                print(f"   详细原因: {exc}")
                return InMemoryVectorStore(self.embeddings)

            os.makedirs(self.settings.vector_store_dir, exist_ok=True)
            return Chroma(
                collection_name="ai_tutor_knowledge",
                embedding_function=self.embeddings,
                persist_directory=self.settings.vector_store_dir,
            )

        raise RuntimeError(f"Unsupported VECTOR_STORE_BACKEND: {backend}")

    def _load_manifest(self) -> dict[str, dict[str, Any]]:
        if not os.path.exists(self.manifest_path):
            return {}
        try:
            with open(self.manifest_path, "r", encoding="utf-8") as file_obj:
                payload = json.load(file_obj)
            files = payload.get("files", {}) if isinstance(payload, dict) else {}
            if isinstance(files, dict):
                return files
        except Exception as e:
            print(f"⚠️ 读取知识库索引清单失败，忽略旧清单: {e}")
        return {}

    def _save_manifest(self) -> None:
        os.makedirs(self.settings.knowledge_dir, exist_ok=True)
        payload = {
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "files": self._manifest,
        }
        with open(self.manifest_path, "w", encoding="utf-8") as file_obj:
            json.dump(payload, file_obj, ensure_ascii=False, indent=2)

    def _is_chroma_store(self) -> bool:
        return self.vector_store.__class__.__name__.lower() == "chroma"

    def _parse_file(self, file_path: str) -> List[Document]:
        documents = []
        try:
            if file_path.lower().endswith(".pdf"):
                reader = PdfReader(file_path)
                for page_number, page in enumerate(reader.pages, start=1):
                    text = page.extract_text()
                    if not text:
                        continue
                    page_chunks = chunk_text(
                        text,
                        chunk_size=self.settings.knowledge_chunk_size,
                        chunk_overlap=self.settings.knowledge_chunk_overlap,
                    )
                    for page_chunk_index, chunk in enumerate(page_chunks):
                        documents.append(
                            Document(
                                page_content=chunk,
                                metadata={
                                    "source": file_path,
                                    "filename": os.path.basename(file_path),
                                    "page": page_number,
                                    "chunk_index": len(documents),
                                    "page_chunk_index": page_chunk_index,
                                },
                            )
                        )
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
                            metadata={
                                "source": file_path,
                                "filename": os.path.basename(file_path),
                                "chunk_index": index,
                            },
                        )
                    )
        except Exception as e:
            print(f"❌ 解析文件失败 {file_path}: {e}")
        return documents

    def _list_knowledge_files(self) -> list[str]:
        extensions = ["**/*.txt", "**/*.md", "**/*.pdf"]
        files = []
        for ext in extensions:
            files.extend(glob.glob(os.path.join(self.settings.knowledge_dir, ext), recursive=True))
        return sorted(files)

    def _sync_documents(self):
        if not self.vector_store:
            return

        knowledge_dir = self.settings.knowledge_dir
        if not os.path.exists(knowledge_dir):
            os.makedirs(knowledge_dir, exist_ok=True)
            return

        files = self._list_knowledge_files()
        if not files:
            return

        is_chroma = self._is_chroma_store()
        self._manifest = self._load_manifest() if is_chroma else {}

        stale_filenames = [name for name in self._manifest.keys() if os.path.join(knowledge_dir, name) not in files]
        for filename in stale_filenames:
            self._delete_vectors_by_filename(filename)
            self._manifest.pop(filename, None)

        total_new_chunks = 0
        for file_path in files:
            filename = os.path.basename(file_path)
            if is_chroma and filename in self._manifest:
                continue

            docs = self._parse_file(file_path)
            if not docs:
                continue

            try:
                ids = self.vector_store.add_documents(docs)
                total_new_chunks += len(docs)
                print(f"✅ 已提取并索引: {filename} ({len(docs)} chunks)")
                if is_chroma:
                    self._manifest[filename] = {
                        "doc_ids": ids if isinstance(ids, list) else [],
                        "chunks": len(docs),
                        "updated_at": datetime.utcnow().isoformat() + "Z",
                    }
            except Exception as e:
                print(f"⚠️ 无法为 {filename} 建立索引: {e}")

        if is_chroma:
            self._save_manifest()

        if total_new_chunks:
            print(f"✨ 成功建立/更新向量索引，共新增 {total_new_chunks} 个文本块。")

    def _delete_vectors_by_filename(self, filename: str) -> None:
        if not self.vector_store:
            return

        if self._is_chroma_store():
            try:
                doc_ids = self._manifest.get(filename, {}).get("doc_ids", [])
                if doc_ids:
                    self.vector_store.delete(ids=doc_ids)
                    return
            except Exception:
                pass
            try:
                self.vector_store.delete(where={"filename": filename})
            except Exception:
                pass
            return

        self._rebuild_inmemory_index(excluding_filename=filename)

    def _rebuild_inmemory_index(self, excluding_filename: Optional[str] = None) -> None:
        self.vector_store = InMemoryVectorStore(self.embeddings)
        for file_path in self._list_knowledge_files():
            if excluding_filename and os.path.basename(file_path) == excluding_filename:
                continue
            docs = self._parse_file(file_path)
            if docs:
                self.vector_store.add_documents(docs)

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
                ids = self.vector_store.add_documents(docs)
                if self._is_chroma_store():
                    self._manifest = self._load_manifest()
                    self._manifest[filename] = {
                        "doc_ids": ids if isinstance(ids, list) else [],
                        "chunks": len(docs),
                        "updated_at": datetime.utcnow().isoformat() + "Z",
                    }
                    self._save_manifest()
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

    def query_with_sources(self, query: str) -> dict[str, Any]:
        if not self.vector_store:
            return {"context": "", "citations": []}

        try:
            results = self.vector_store.similarity_search(
                query,
                k=self.settings.knowledge_top_k,
            )
            if not results:
                return {"context": "", "citations": []}

            context = "\n---\n".join([doc.page_content for doc in results])
            citations = []
            for doc in results:
                meta = doc.metadata or {}
                snippet = " ".join((doc.page_content or "").split())
                citations.append(
                    {
                        "filename": meta.get("filename") or os.path.basename(meta.get("source", "") or ""),
                        "page": meta.get("page"),
                        "chunk_index": meta.get("chunk_index"),
                        "snippet": snippet[:180],
                    }
                )

            return {"context": context, "citations": citations}
        except Exception as e:
            print(f"⚠️ 带来源的知识检索失败: {e}")
            return {"context": "", "citations": []}

    def list_documents(self) -> list[dict[str, Any]]:
        knowledge_dir = self.settings.knowledge_dir
        if not os.path.exists(knowledge_dir):
            return []

        manifest = self._load_manifest() if self._is_chroma_store() else {}
        entries: list[dict[str, Any]] = []
        for file_path in self._list_knowledge_files():
            filename = os.path.basename(file_path)
            stat = os.stat(file_path)
            chunk_count = manifest.get(filename, {}).get("chunks")
            entries.append(
                {
                    "filename": filename,
                    "size_bytes": stat.st_size,
                    "updated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "chunk_count": int(chunk_count) if isinstance(chunk_count, int) else None,
                }
            )
        return entries

    def delete_document(self, filename: str) -> bool:
        clean_name = os.path.basename((filename or "").strip())
        if not clean_name:
            return False

        target_path = os.path.join(self.settings.knowledge_dir, clean_name)
        if not os.path.exists(target_path):
            return False

        try:
            self._delete_vectors_by_filename(clean_name)
            os.remove(target_path)
            if self._is_chroma_store():
                self._manifest = self._load_manifest()
                self._manifest.pop(clean_name, None)
                self._save_manifest()
            return True
        except Exception as e:
            print(f"❌ 删除知识文件失败 {clean_name}: {e}")
            return False

    def clear_documents(self) -> int:
        knowledge_files = self._list_knowledge_files()
        removed_count = 0

        for file_path in knowledge_files:
            filename = os.path.basename(file_path)
            if self.delete_document(filename):
                removed_count += 1

        return removed_count

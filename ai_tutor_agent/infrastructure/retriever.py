import glob
import importlib
import json
import os
import re
import shutil
import time
from dataclasses import dataclass
from typing import Any, List

import fitz  # PyMuPDF
import httpx
from langchain_chroma import Chroma
from langchain_core.documents import Document

from ..config import Settings
from ..core.ports import KnowledgeProvider
from .processor import KnowledgeProcessor

try:
    BM25Okapi = importlib.import_module("rank_bm25").BM25Okapi
except Exception:  # pragma: no cover - optional dependency in degraded mode
    BM25Okapi = None


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

    if provider == "dashscope":
        from langchain_community.embeddings import DashScopeEmbeddings

        return DashScopeEmbeddings(
            model=settings.embedding_model_name,
            dashscope_api_key=settings.dashscope_api_key,
        )

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
    text = ""
    try:
        doc = fitz.open(file_path)
        for page_number, page in enumerate(doc, start=1):
            page_text = page.get_text()
            if page_text.strip():
                text += f"\n[Page {page_number}]\n{page_text}\n"
        doc.close()
    except Exception as exc:
        print(f"PyMuPDF parse failed for {file_path}: {exc}")
    return text


@dataclass
class ScoredChunk:
    doc: Document
    score: float
    adjusted_score: float
    metadata: dict[str, Any]


class LocalFileKnowledgeProvider(KnowledgeProvider):
    def __init__(self, settings: Settings):
        self.settings = settings
        self.vector_store = None
        self.bm25 = None
        self.bm25_docs: list[Document] = []
        self.purge_stale_on_start = os.getenv("RAG_PURGE_STALE_ON_START", "false").strip().lower() == "true"
        self.processor = KnowledgeProcessor(api_token=settings.mineru_api_token)
        self.index_file = os.path.join(os.path.dirname(settings.knowledge_dir), "knowledge_index.json")
        self.knowledge_index = self._load_index()

        try:
            print(
                f"Loading knowledge retriever "
                f"({settings.embedding_provider}:{settings.embedding_model_name})..."
            )
            self.embeddings = build_embedding_backend(settings)

            chroma_dir = settings.chroma_dir or os.path.join(
                os.path.dirname(settings.knowledge_dir), "chroma_db"
            )
            os.makedirs(chroma_dir, exist_ok=True)

            self.vector_store = Chroma(
                collection_name="knowledge",
                embedding_function=self.embeddings,
                persist_directory=chroma_dir,
            )
            self._chroma_dir = chroma_dir

            self._sync_knowledge_dir()
            self._build_bm25_index()
            collection_size = self._collection_count()
            self._log(
                "init_ready",
                embedding_provider=settings.embedding_provider,
                embedding_model=settings.embedding_model_name,
                retrieval_mode="hybrid" if settings.rag_hybrid_enabled else "vector",
                mineru_enabled=bool(settings.rag_mineru_enabled and settings.mineru_api_token),
                collection_size=collection_size,
                bm25_ready=bool(self.bm25),
            )
        except Exception as exc:
            print(f"Knowledge retriever init failed: {exc}")
            print("System falls back to no-RAG mode.")

    @staticmethod
    def _safe_value(value: Any) -> Any:
        if isinstance(value, dict):
            return {str(k): LocalFileKnowledgeProvider._safe_value(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [LocalFileKnowledgeProvider._safe_value(item) for item in value]
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        return str(value)

    def _log(self, event: str, **fields: Any) -> None:
        payload = {key: self._safe_value(value) for key, value in fields.items()}
        print(f"[RAG][{event}] {json.dumps(payload, ensure_ascii=False)}", flush=True)

    def _collection_count(self) -> int:
        if not self.vector_store:
            return 0
        try:
            return int(self.vector_store._collection.count())
        except Exception as exc:
            self._log("collection_count_error", error=str(exc))
            return 0

    @staticmethod
    def _preview(text: str, limit: int = 120) -> str:
        normalized = re.sub(r"\s+", " ", (text or "")).strip()
        return normalized[:limit]

    def _reset_vector_store(self, reason: str) -> None:
        if not getattr(self, "embeddings", None):
            self._log("reset_skipped", reason="embeddings_unavailable")
            return
        try:
            if os.path.exists(self._chroma_dir):
                shutil.rmtree(self._chroma_dir, ignore_errors=True)
            os.makedirs(self._chroma_dir, exist_ok=True)
            self.vector_store = Chroma(
                collection_name="knowledge",
                embedding_function=self.embeddings,
                persist_directory=self._chroma_dir,
            )
            self._log("reset_vector_store", reason=reason)
        except Exception as exc:
            self._log("reset_vector_store_error", reason=reason, error=str(exc))

    def _load_index(self) -> dict[str, dict[str, Any]]:
        if not os.path.exists(self.index_file):
            return {}
        try:
            with open(self.index_file, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            return data if isinstance(data, dict) else {}
        except Exception as exc:
            print(f"Failed to read knowledge index, use empty index: {exc}")
            return {}

    def _save_index(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.index_file), exist_ok=True)
            with open(self.index_file, "w", encoding="utf-8") as fh:
                json.dump(self.knowledge_index, fh, ensure_ascii=False, indent=2)
        except Exception as exc:
            print(f"Failed to save knowledge index: {exc}")

    def _get_file_fingerprint(self, file_path: str) -> str:
        stat = os.stat(file_path)
        return f"{os.path.basename(file_path)}_{stat.st_size}_{int(stat.st_mtime)}"

    def _should_process(self, file_path: str) -> bool:
        filename = os.path.basename(file_path)
        fingerprint = self._get_file_fingerprint(file_path)
        old_record = self.knowledge_index.get(filename)
        return not old_record or old_record.get("fingerprint") != fingerprint

    def _delete_existing_vectors(self, filename: str) -> None:
        if not self.vector_store:
            return
        try:
            self.vector_store._collection.delete(where={"filename": filename})
        except Exception as exc:
            print(f"Failed to delete old vectors for {filename}: {exc}")

    def _cleanup_deleted_files(self) -> None:
        current_files = {
            os.path.basename(f)
            for f in glob.glob(os.path.join(self.settings.knowledge_dir, "*.*"))
        }
        indexed_files = set(self.knowledge_index.keys())
        deleted_files = indexed_files - current_files

        for filename in deleted_files:
            self._delete_existing_vectors(filename)
            self.knowledge_index.pop(filename, None)

        if deleted_files:
            self._save_index()

    def _purge_stale_vectors(self, active_filenames: set[str]) -> int:
        if not self.vector_store:
            return 0
        try:
            raw = self.vector_store._collection.get(include=["metadatas"])
            ids = raw.get("ids") or []
            metas = raw.get("metadatas") or []
            stale_ids: list[str] = []
            for item_id, meta in zip(ids, metas):
                metadata = meta or {}
                filename = str(metadata.get("filename", "")).strip()
                if not filename or filename not in active_filenames:
                    stale_ids.append(item_id)

            if stale_ids:
                self.vector_store._collection.delete(ids=stale_ids)
                self._log("purge_stale_vectors", removed=len(stale_ids))
                return len(stale_ids)

            self._log("purge_stale_vectors", removed=0)
            return 0
        except Exception as exc:
            self._log(
                "purge_stale_vectors_skipped",
                reason="compactor_failure",
                error=str(exc),
            )
            return 0

    def _parse_file(self, source_path: str) -> List[Document]:
        from langchain_community.document_loaders import TextLoader

        filename = os.path.basename(source_path)
        ext = os.path.splitext(filename)[1].lower()

        if ext == ".pdf":
            if self.settings.rag_mineru_enabled and self.settings.mineru_api_token:
                try:
                    md_content = self.processor.parse_pdf_to_md(source_path)
                    docs = self.processor.split_by_semantics(md_content)
                    for doc in docs:
                        meta = dict(doc.metadata or {})
                        meta["parse_backend"] = "mineru"
                        doc.metadata = meta
                    return docs
                except Exception as exc:
                    # Fallback keeps default behavior stable when MinerU is unavailable.
                    print(f"MinerU parse failed, fallback to PyMuPDF: {exc}")

            full_text = _parse_pdf(source_path)
            chunks = chunk_text(
                full_text,
                chunk_size=self.settings.knowledge_chunk_size,
                chunk_overlap=self.settings.knowledge_chunk_overlap,
            )
            return [
                Document(
                    page_content=chunk,
                    metadata={
                        "source": source_path,
                        "filename": filename,
                        "chunk_id": i,
                        "type": "static_knowledge",
                        "parse_backend": "pymupdf",
                    },
                )
                for i, chunk in enumerate(chunks)
            ]

        if ext in {".txt", ".md"}:
            loader = TextLoader(source_path, encoding="utf-8")
            docs = loader.load_and_split()
            for i, doc in enumerate(docs):
                meta = dict(doc.metadata or {})
                meta.setdefault("source", source_path)
                meta.setdefault("filename", filename)
                meta.setdefault("chunk_id", i)
                meta.setdefault("type", "static_knowledge")
                meta.setdefault("parse_backend", "text")
                doc.metadata = meta
            return docs

        return []

    @staticmethod
    def _tokenize_for_bm25(text: str) -> list[str]:
        text = (text or "").lower()
        return re.findall(r"[a-zA-Z0-9_\-\.\(\)]+|[\u4e00-\u9fff]+", text)

    def _build_bm25_index(self) -> None:
        self.bm25 = None
        self.bm25_docs = []

        if not self.vector_store or not self.settings.rag_hybrid_enabled or BM25Okapi is None:
            if self.settings.rag_hybrid_enabled and BM25Okapi is None:
                self._log("bm25_skipped", reason="rank_bm25_not_installed")
            return

        try:
            raw = self.vector_store._collection.get(include=["documents", "metadatas"])
            docs = raw.get("documents") or []
            metas = raw.get("metadatas") or []

            tokenized_corpus = []
            for doc_text, meta in zip(docs, metas):
                if not doc_text:
                    continue
                doc = Document(page_content=doc_text, metadata=meta or {})
                if not self._is_doc_active(doc):
                    continue
                self.bm25_docs.append(doc)
                tokenized_corpus.append(self._tokenize_for_bm25(doc_text))

            if tokenized_corpus:
                self.bm25 = BM25Okapi(tokenized_corpus)
                self._log("bm25_built", docs=len(tokenized_corpus))
            else:
                self._log("bm25_built", docs=0)
        except Exception as exc:
            print(f"BM25 index build failed: {exc}")
            self.bm25 = None
            self.bm25_docs = []
            self._log("bm25_error", error=str(exc))

    def _sync_knowledge_dir(self) -> None:
        if not self.vector_store:
            return

        if not os.path.exists(self.settings.knowledge_dir):
            os.makedirs(self.settings.knowledge_dir, exist_ok=True)
            return

        self._cleanup_deleted_files()

        # 如果 knowledge_index 记录存在但向量集合为空/异常，说明索引与向量库已漂移，强制全量重建。
        current_count = self._collection_count()
        if current_count <= 0 and bool(self.knowledge_index):
            self._log(
                "sync_force_reindex",
                reason="collection_empty_or_unhealthy_with_existing_index",
                index_size=len(self.knowledge_index),
            )
            self._reset_vector_store("force_reindex_on_unhealthy_collection")
            self.knowledge_index = {}
            self._save_index()

        files = glob.glob(os.path.join(self.settings.knowledge_dir, "*.*"))
        active_filenames = {os.path.basename(path) for path in files}
        purged = 0
        if self.purge_stale_on_start:
            purged = self._purge_stale_vectors(active_filenames)
        else:
            self._log("purge_stale_vectors_skipped", reason="disabled_by_default")
        attempted = 0
        succeeded = 0
        failed = 0
        for file_path in files:
            if self._should_process(file_path):
                attempted += 1
                result = self.add_local_file(file_path)
                if result.get("success"):
                    succeeded += 1
                else:
                    failed += 1
                    self._log(
                        "sync_file_failed",
                        filename=os.path.basename(file_path),
                        message=result.get("message", "unknown"),
                    )
        self._log(
            "sync_done",
            scanned=len(files),
            attempted=attempted,
            succeeded=succeeded,
            failed=failed,
            purged=purged,
        )

    def _is_doc_active(self, doc: Document) -> bool:
        metadata = doc.metadata or {}
        filename = str(metadata.get("filename", "")).strip()
        if not filename:
            return False
        if self.knowledge_index and filename not in self.knowledge_index:
            return False
        return True

    def add_local_file(self, source_path: str) -> dict:
        if not self.vector_store:
            return {"success": False, "chunks": 0, "filename": os.path.basename(source_path), "message": "vector store unavailable"}

        filename = os.path.basename(source_path)
        start_time = time.perf_counter()
        fingerprint = self._get_file_fingerprint(source_path)
        old_record = self.knowledge_index.get(filename)

        self._log(
            "upload_start",
            filename=filename,
            source=source_path,
            retrieval_mode="hybrid" if self.settings.rag_hybrid_enabled else "vector",
            mineru_enabled=bool(self.settings.rag_mineru_enabled and self.settings.mineru_api_token),
        )

        if old_record and old_record.get("fingerprint") != fingerprint:
            self._delete_existing_vectors(filename)

        docs = self._parse_file(source_path)
        if not docs:
            self._log("upload_failed", filename=filename, reason="empty_or_parse_failed")
            return {
                "success": False,
                "chunks": 0,
                "filename": filename,
                "message": f"empty content or parse failed: {filename}",
            }

        for doc in docs:
            meta = dict(doc.metadata or {})
            meta["source"] = source_path
            meta["filename"] = filename
            meta["fingerprint"] = fingerprint
            doc.metadata = meta

        self.vector_store.add_documents(docs)

        self.knowledge_index[filename] = {
            "fingerprint": fingerprint,
            "chunks": len(docs),
        }
        self._save_index()

        self._build_bm25_index()

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        parse_backend = docs[0].metadata.get("parse_backend", "unknown")
        self._log(
            "upload_done",
            filename=filename,
            chunks=len(docs),
            parse_backend=parse_backend,
            bm25_ready=bool(self.bm25),
            elapsed_ms=elapsed_ms,
        )

        return {
            "success": True,
            "chunks": len(docs),
            "filename": filename,
            "message": f"imported into knowledge base: {filename}",
            "parse_backend": parse_backend,
            "bm25_rebuilt": bool(self.bm25),
        }

    def add_document(self, source_path: str) -> dict:
        if not self.vector_store:
            return {
                "success": False,
                "chunks": 0,
                "filename": os.path.basename(source_path),
                "message": "vector engine unavailable",
            }

        if not os.path.exists(source_path):
            return {
                "success": False,
                "chunks": 0,
                "filename": os.path.basename(source_path),
                "message": f"file not found: {source_path}",
            }

        knowledge_dir = self.settings.knowledge_dir
        os.makedirs(knowledge_dir, exist_ok=True)

        filename = os.path.basename(source_path)
        dest_path = os.path.join(knowledge_dir, filename)

        try:
            shutil.copy2(source_path, dest_path)
            return self.add_local_file(dest_path)
        except Exception as exc:
            return {
                "success": False,
                "chunks": 0,
                "filename": filename,
                "message": f"upload failed: {exc}",
            }

    def query_with_scores(self, query: str, k: int | None = None):
        if not self.vector_store:
            return []
        k = k or self.settings.knowledge_top_k
        fetch_k = max(k * 20, 50)
        raw_results = self.vector_store.similarity_search_with_score(query, k=fetch_k)
        filtered_results = [(doc, score) for doc, score in raw_results if self._is_doc_active(doc)]
        return filtered_results[:k]

    def query_with_bm25(self, query: str, k: int = 5) -> list[Document]:
        if not self.bm25 or not self.bm25_docs:
            return []

        query_tokens = self._tokenize_for_bm25(query)
        if not query_tokens:
            return []

        scores = self.bm25.get_scores(query_tokens)
        ranked = sorted(zip(self.bm25_docs, scores), key=lambda item: item[1], reverse=True)

        results: list[Document] = []
        for doc, score in ranked[:k]:
            meta = dict(doc.metadata or {})
            meta["_bm25_score"] = float(score)
            results.append(Document(page_content=doc.page_content, metadata=meta))
        return results

    def _section_rerank(self, docs_and_scores, final_k: int | None = None) -> List[Document]:
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

        reranked: list[ScoredChunk] = []
        for doc, score in docs_and_scores:
            meta = doc.metadata or {}
            section = str(meta.get("section") or meta.get("H1") or "").lower()
            content_head = (doc.page_content or "")[:300].lower()

            bonus = 0.0
            if any(token in section for token in good_keywords):
                bonus -= 0.12
            if any(token in section for token in bad_keywords):
                bonus += 0.35
            if "<table>" in content_head:
                bonus += 0.12
            if any(token in content_head for token in ["benchmark", "benchmarks", "dataset", "datasets"]):
                bonus -= 0.08

            reranked.append(
                ScoredChunk(
                    doc=doc,
                    score=score,
                    adjusted_score=score + bonus,
                    metadata=meta,
                )
            )

        reranked.sort(key=lambda item: item.adjusted_score)
        final_k = final_k or self.settings.knowledge_top_k
        return [item.doc for item in reranked[:final_k]]

    def query_hybrid(self, query: str, recall_k: int = 8, final_k: int | None = None) -> list[Document]:
        final_k = final_k or self.settings.knowledge_top_k

        vector_docs_and_scores = self.query_with_scores(query, k=max(recall_k, final_k))
        bm25_docs = self.query_with_bm25(query, k=recall_k)
        if not vector_docs_and_scores and not bm25_docs:
            return []

        merged: list[tuple[Document, float]] = []
        seen = set()

        def doc_key(doc: Document):
            meta = doc.metadata or {}
            return (meta.get("filename", ""), meta.get("chunk_id", -1), (doc.page_content or "")[:120])

        for doc, score in vector_docs_and_scores:
            key = doc_key(doc)
            if key in seen:
                continue
            seen.add(key)
            merged.append((doc, score))

        for doc in bm25_docs:
            key = doc_key(doc)
            if key in seen:
                continue
            seen.add(key)
            merged.append((doc, 999.0))

        return self._section_rerank(merged, final_k=final_k)

    def query(self, query: str) -> str:
        if not self.vector_store:
            self._log("query_skipped", reason="vector_store_unavailable", query=query)
            return ""

        try:
            mode = "hybrid" if self.settings.rag_hybrid_enabled else "vector"
            self._log(
                "query_start",
                mode=mode,
                query=query,
                top_k=self.settings.knowledge_top_k,
            )
            if self.settings.rag_hybrid_enabled:
                results = self.query_hybrid(
                    query=query,
                    recall_k=max(8, self.settings.knowledge_top_k),
                    final_k=self.settings.knowledge_top_k,
                )
                scored_results = [(doc, None) for doc in results]
            else:
                fetch_k = max(self.settings.knowledge_top_k * 20, 50)
                scored_results = self.vector_store.similarity_search_with_score(query, k=fetch_k)
            filtered_scored_results = [
                (doc, score) for doc, score in scored_results if self._is_doc_active(doc)
            ]
            if len(filtered_scored_results) != len(scored_results):
                self._log(
                    "query_filtered",
                    mode=mode,
                    query=query,
                    before=len(scored_results),
                    after=len(filtered_scored_results),
                )

            filtered_scored_results = filtered_scored_results[: self.settings.knowledge_top_k]
            results = [doc for doc, _ in filtered_scored_results]
            if not results:
                self._log("query_empty", mode=mode, query=query)
                return ""

            hit_logs = []
            for idx, (doc, score) in enumerate(filtered_scored_results[:3], start=1):
                meta = doc.metadata or {}
                hit_logs.append(
                    {
                        "rank": idx,
                        "filename": meta.get("filename", ""),
                        "chunk_id": meta.get("chunk_id", ""),
                        "parse_backend": meta.get("parse_backend", ""),
                        "score": score,
                        "preview": self._preview(doc.page_content),
                    }
                )
            self._log("query_hits", mode=mode, query=query, hit_count=len(results), hits=hit_logs)
            return "\n---\n".join([doc.page_content for doc in results])
        except Exception as exc:
            print(f"Knowledge retrieval failed: {exc}")
            self._log("query_error", query=query, error=str(exc))
            return ""

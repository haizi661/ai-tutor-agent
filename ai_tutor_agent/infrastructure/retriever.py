from __future__ import annotations

import glob
import hashlib
import json
import os
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

import fitz  # PyMuPDF
import huggingface_hub
import httpx
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage
from rank_bm25 import BM25Okapi

from ..config import PROJECT_ROOT, Settings
from ..platform_paths import resolve_project_path
from ..core.output_format import parse_json_object
from ..core.ports import KnowledgeProvider
from ..core.text import content_to_text
from .llm import build_retrieval_planner_llm
from .processor import KnowledgeProcessor
from .web_search import TavilySearchClient, WebSearchResult


def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive.")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must be non-negative.")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size.")

    content = (text or "").strip()
    if not content:
        return []

    if len(content) <= chunk_size:
        return [content]

    step = chunk_size - chunk_overlap
    chunks: list[str] = []
    start = 0

    while start < len(content):
        end = min(len(content), start + chunk_size)
        chunk = content[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(content):
            break
        start += step

    return chunks


def resolve_local_embedding_model_path(model_name: str) -> str:
    if os.path.isdir(model_name):
        return model_name

    try:
        return huggingface_hub.snapshot_download(repo_id=model_name, local_files_only=True)
    except Exception as exc:
        raise RuntimeError(
            f"Local embedding model {model_name!r} was not found in the local HuggingFace cache. "
            "Run once with network access or configure HTTP_PROXY / HTTPS_PROXY to pre-download it."
        ) from exc


def build_embedding_backend(settings: Settings):
    provider = settings.embedding_provider

    if provider == "dashscope":
        from langchain_community.embeddings import DashScopeEmbeddings

        return DashScopeEmbeddings(
            model=settings.embedding_model_name,
            dashscope_api_key=settings.dashscope_api_key,
        )

    if provider == "local":
        if "/" not in settings.embedding_model_name and not os.path.isdir(settings.embedding_model_name):
            raise RuntimeError(
                "Local embedding expects a HuggingFace-style model name such as "
                "'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2' or a local directory path. "
                f"Current EMBEDDING_MODEL_NAME={settings.embedding_model_name!r}."
            )

        from langchain_huggingface import HuggingFaceEmbeddings

        try:
            model_name = resolve_local_embedding_model_path(settings.embedding_model_name)
        except RuntimeError:
            model_name = settings.embedding_model_name

        try:
            return HuggingFaceEmbeddings(model_name=model_name)
        except Exception as exc:
            raise RuntimeError(
                f"Failed to initialize local embedding model {settings.embedding_model_name!r}. "
                "If this is the first launch, make sure HuggingFace is reachable, or pre-download "
                "the model into the local HuggingFace cache."
            ) from exc

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


@dataclass(frozen=True)
class RetrievalRewriteRequest:
    channel: str
    raw_query: str
    current_topic: str = ""
    attempt_count: int = 0
    teaching_strategy: str = ""
    weak_areas_hint: str = ""
    conversation_hint: str = ""


@dataclass
class RetrievalRewritePlan:
    intent: str = "concept_overview"
    rewrite_needed: bool = False
    reason: str = ""
    must_keep: list[str] = field(default_factory=list)
    vector_queries: list[str] = field(default_factory=list)
    bm25_queries: list[str] = field(default_factory=list)
    metadata_terms: list[str] = field(default_factory=list)


@dataclass
class RetrievalRewriteTrace:
    gate_outcome: str
    gate_reason: str
    planner_intent: str | None = None
    raw_query: str = ""
    rewritten_vector_queries: list[str] = field(default_factory=list)
    rewritten_bm25_queries: list[str] = field(default_factory=list)
    metadata_terms: list[str] = field(default_factory=list)
    must_keep: list[str] = field(default_factory=list)
    must_keep_repaired: bool = False
    raw_confidence: dict[str, Any] = field(default_factory=dict)
    rewritten_confidence: dict[str, Any] = field(default_factory=dict)
    planner_reason: str = ""
    planner_error: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_outcome": self.gate_outcome,
            "gate_reason": self.gate_reason,
            "planner_intent": self.planner_intent,
            "raw_query": self.raw_query,
            "rewritten_vector_queries": list(self.rewritten_vector_queries),
            "rewritten_bm25_queries": list(self.rewritten_bm25_queries),
            "metadata_terms": list(self.metadata_terms),
            "must_keep": list(self.must_keep),
            "must_keep_repaired": bool(self.must_keep_repaired),
            "raw_confidence": dict(self.raw_confidence or {}),
            "rewritten_confidence": dict(self.rewritten_confidence or {}),
            "planner_reason": self.planner_reason,
            "planner_error": self.planner_error,
        }


@dataclass
class FamilyHit:
    doc: Document
    rank: int
    score: float | None = None


@dataclass(frozen=True)
class KnowledgeSourceSpec:
    scope: str
    path: Path
    label: str
    primary: bool = False
    managed_uploads: bool = False


RRF_K = 60
RRF_SCALE = 100.0
RETRIEVAL_STATE_VERSION = 2
CONFIDENT_CITATION_MIN_DOMINANCE = 0.74
CONFIDENT_CITATION_MIN_RRF = 0.03
FILENAME_MATCH_BOOST = -1.55
TITLE_MATCH_BOOST = -0.3
TERM_OVERLAP_BOOST = -0.08
COURSE_PRIMARY_SOURCE_BOOST = -0.06
SOURCE_SCOPE_COURSE_PRIMARY = "course_primary"
SOURCE_SCOPE_SUPPLEMENTAL = "supplemental"
RETRIEVAL_REWRITE_INTENTS = {
    "exact_lookup",
    "concept_overview",
    "procedure",
    "comparison",
    "example_application",
    "troubleshoot",
}
QUESTION_WORD_PATTERN = re.compile(
    r"(什么|怎么|如何|为什么|区别|差别|步骤|例子|应用|案例|报错|错误|失败|原因|解决|排查|讲解|介绍|原理)"
)
QUESTION_HINT_MARKERS = [
    "什么",
    "怎么",
    "如何",
    "为什么",
    "区别",
    "差别",
    "步骤",
    "例子",
    "应用",
    "案例",
    "报错",
    "错误",
    "失败",
    "原因",
    "解决",
    "排查",
    "讲解",
    "介绍",
    "原理",
]
QUERY_INTENT_PREFIXES = [
    "什么",
    "怎么",
    "如何",
    "为什么",
    "区别",
    "差别",
    "步骤",
    "例子",
    "应用",
    "案例",
    "报错",
    "错误",
    "失败",
    "原因",
    "解决",
    "排查",
    "讲解",
    "介绍",
    "原理",
]
QUERY_FUNCTION_PREFIXES = ["是", "的", "里", "中", "上", "下", "把", "给", "对", "在"]
MAX_REWRITE_VECTOR_QUERIES = 2
MAX_REWRITE_BM25_QUERIES = 2
MAX_REWRITE_METADATA_TERMS = 4
MAX_CITABLE_EVIDENCE_ITEMS = 4
COURSE_PRIMARY_MIN_RESULTS = 2
SUPPLEMENTAL_MIN_RESULTS = 1
GRAPH_NOTE_ENRICHMENT_FIELDS = (
    "id",
    "prerequisites",
    "neighbors",
    "learning_objectives",
    "must_know",
    "teaching_modes",
    "assessment_modes",
    "target_mastery_level",
    "common_errors",
    "difficulty",
)


@dataclass
class EvidenceItem:
    source_type: str
    source_id: str
    display_label: str
    snippet: str
    goal_alignment: float
    can_cite: bool
    rank_score: float
    filename: str = ""
    page: int | None = None
    section: str = ""
    chunk_index: int | None = None
    source_scope: str = ""
    url: str = ""
    domain: str = ""
    title: str = ""
    published_date: str = ""
    retrieval_sources: list[str] = field(default_factory=list)
    citation_index: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "source_id": self.source_id,
            "display_label": self.display_label,
            "snippet": self.snippet,
            "goal_alignment": float(self.goal_alignment),
            "can_cite": bool(self.can_cite),
            "rank_score": float(self.rank_score),
            "filename": self.filename,
            "page": self.page,
            "section": self.section,
            "chunk_index": self.chunk_index,
            "source_scope": self.source_scope,
            "url": self.url,
            "domain": self.domain,
            "title": self.title,
            "published_date": self.published_date,
            "retrieval_sources": list(self.retrieval_sources),
            "citation_index": self.citation_index,
        }


def _normalize_lookup_text(text: str) -> str:
    cleaned = str(text or "").strip().lower()
    if not cleaned:
        return ""
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", cleaned)


def _extract_lookup_terms(text: str) -> list[str]:
    lowered = str(text or "").strip().lower()
    if not lowered:
        return []
    raw_terms = re.findall(r"[a-z0-9]{2,}|[\u4e00-\u9fff]{2,}", lowered)
    deduped: list[str] = []
    seen: set[str] = set()
    for term in raw_terms:
        if term in seen:
            continue
        seen.add(term)
        deduped.append(term)
        if re.fullmatch(r"[\u4e00-\u9fff]{4,}", term):
            max_ngram = min(4, len(term))
            for size in range(2, max_ngram + 1):
                for start in range(0, len(term) - size + 1):
                    fragment = term[start : start + size]
                    if fragment in seen:
                        continue
                    seen.add(fragment)
                    deduped.append(fragment)
    return deduped


def _dedupe_texts(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned = str(value or "").strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(cleaned)
    return deduped


def _strip_query_prefixes(term: str) -> str:
    cleaned = str(term or "").strip().lower()
    if not cleaned:
        return ""

    changed = True
    while changed and cleaned:
        changed = False
        for prefix in QUERY_INTENT_PREFIXES:
            if cleaned.startswith(prefix) and len(cleaned) > len(prefix):
                cleaned = cleaned[len(prefix) :].strip()
                changed = True
        for prefix in QUERY_FUNCTION_PREFIXES:
            if cleaned.startswith(prefix) and len(cleaned) > len(prefix):
                cleaned = cleaned[len(prefix) :].strip()
                changed = True
    return cleaned


class LocalFileKnowledgeProvider(KnowledgeProvider):
    def __init__(self, settings: Settings):
        self.settings = settings
        self.knowledge_dir = resolve_project_path(settings.knowledge_dir)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        self.course_primary_dir = self._resolve_source_dir(settings.course_primary_dir)
        self.index_file = self.knowledge_dir.parent / "knowledge_index.json"
        self.index_files = {
            SOURCE_SCOPE_COURSE_PRIMARY: self.knowledge_dir.parent / "knowledge_index__course_primary.json",
            SOURCE_SCOPE_SUPPLEMENTAL: self.knowledge_dir.parent / "knowledge_index__supplemental.json",
        }
        self.bm25_cache_file = self.knowledge_dir.parent / "bm25_cache.json"
        self.retrieval_state_file = self.knowledge_dir.parent / "retrieval_state.json"

        self.initialization_error: str | None = None
        self.embeddings = None
        self.vector_store = None
        self.vector_stores: dict[str, Chroma] = {}
        self.bm25 = None
        self.bm25_docs: list[Document] = []
        self.bm25_by_scope: dict[str, BM25Okapi | None] = {}
        self.bm25_docs_by_scope: dict[str, list[Document]] = {}
        self.processor = (
            KnowledgeProcessor(
                api_token=settings.mineru_api_token,
                proxy_mode=settings.mineru_proxy_mode,
                http_proxy=settings.mineru_http_proxy,
                https_proxy=settings.mineru_https_proxy,
                connect_timeout_seconds=settings.mineru_connect_timeout_seconds,
                status_file_path=str(self.knowledge_dir.parent / "mineru_runtime_state.json"),
                cache_dir=str(self.knowledge_dir.parent / "minerU_cache"),
                public_dns_bypass_enabled=settings.mineru_public_dns_bypass_enabled,
                public_dns_server=settings.mineru_public_dns_server,
                public_dns_port=settings.mineru_public_dns_port,
                public_dns_hosts=settings.mineru_public_dns_hosts,
            )
            if settings.mineru_api_token
            else None
        )
        self.source_specs = self._build_source_specs()
        self.source_specs_by_scope = {spec.scope: spec for spec in self.source_specs}
        self.bm25_cache_files = {
            spec.scope: self._bm25_cache_file_for_scope(spec.scope)
            for spec in self.source_specs
        }
        self.knowledge_index = self._load_index()
        self.retrieval_state = self._load_retrieval_state()
        self.course_graph_index = self._load_course_graph_index()
        self.retrieval_planner_llm = None
        self.web_search_client = None
        self.last_rewrite_trace: dict[str, Any] | None = None

        print("🚀 [RAG] 知识库引擎启动中...")

        try:
            self._ensure_retrieval_compatibility()
            if self.settings.web_search_enabled and self.settings.tavily_api_key:
                try:
                    self.web_search_client = TavilySearchClient(
                        api_key=self.settings.tavily_api_key,
                        max_results=self.settings.web_search_max_results,
                        proxy_url=self.settings.https_proxy or self.settings.http_proxy,
                    )
                except Exception as exc:
                    self.web_search_client = None
                    print(f"⚠️ [RAG] Tavily 搜索客户端初始化失败，已自动禁用外部搜索: {exc}")
            if self.settings.retrieval_rewrite_enabled:
                try:
                    self.retrieval_planner_llm = build_retrieval_planner_llm(settings)
                except Exception as exc:
                    self.retrieval_planner_llm = None
                    print(f"⚠️ [RAG] Retrieval rewrite planner 初始化失败，已自动禁用改写: {exc}")
            self.embeddings = build_embedding_backend(settings)
            print(f"🧬 [RAG] Embedding Provider: {settings.embedding_provider}")
            print(f"🧬 [RAG] Embedding Backend: {type(self.embeddings).__name__}")
            self.vector_stores = self._create_vector_stores()
            self.vector_store = (
                self.vector_stores.get(SOURCE_SCOPE_SUPPLEMENTAL)
                or self.vector_stores.get(SOURCE_SCOPE_COURSE_PRIMARY)
            )
            self._log_source_layout()
            self._sync_knowledge_dir()
            self._build_bm25_index()
            self._save_retrieval_state()
            chroma_doc_count = self._vector_doc_count()
            print(
                f"✅ [RAG] 初始化完成，Chroma 文档块数: {chroma_doc_count}，"
                f"BM25 文档块数: {len(self.bm25_docs)}"
            )
        except Exception as exc:
            self.initialization_error = str(exc)
            self.embeddings = None
            self.vector_store = None
            self.vector_stores = {}
            self.bm25 = None
            self.bm25_docs = []
            self.bm25_by_scope = {}
            self.bm25_docs_by_scope = {}
            print(f"⚠️ [RAG] 初始化失败，已回退为无知识库模式: {exc}")

    def _resolve_source_dir(self, path_value: str) -> Path:
        return resolve_project_path(path_value)

    def _build_source_specs(self) -> list[KnowledgeSourceSpec]:
        specs: list[KnowledgeSourceSpec] = []
        if self.settings.course_primary_enabled:
            specs.append(
                KnowledgeSourceSpec(
                    scope=SOURCE_SCOPE_COURSE_PRIMARY,
                    path=self.course_primary_dir,
                    label="主课程知识源",
                    primary=True,
                    managed_uploads=False,
                )
            )
        specs.append(
            KnowledgeSourceSpec(
                scope=SOURCE_SCOPE_SUPPLEMENTAL,
                path=self.knowledge_dir,
                label="补充知识源",
                primary=False,
                managed_uploads=True,
            )
        )
        return specs

    def _log_source_layout(self) -> None:
        for spec in self.source_specs:
            if not spec.path.exists():
                if spec.scope == SOURCE_SCOPE_COURSE_PRIMARY:
                    print(f"⚠️ [RAG] {spec.label}目录不存在，已跳过: {spec.path}")
                continue
            file_count = len(
                [
                    path
                    for path in spec.path.iterdir()
                    if path.is_file() and path.name != ".gitkeep"
                ]
            )
            print(f"📚 [RAG] {spec.label}: {spec.path} ({file_count} files)")

    def _bm25_cache_file_for_scope(self, source_scope: str) -> Path:
        if source_scope == SOURCE_SCOPE_SUPPLEMENTAL:
            return self.bm25_cache_file
        return self.knowledge_dir.parent / f"bm25_cache__{source_scope}.json"

    def _record_key(self, filename: str, source_scope: str) -> str:
        return f"{source_scope}::{filename}"

    def _load_course_graph_index(self) -> dict[str, dict[str, Any]]:
        notes_path = self.course_primary_dir.parent / "notes.jsonl"
        graph_path = self.course_primary_dir.parent / "graph.json"
        index: dict[str, dict[str, Any]] = {}
        self.course_graph_nodes: dict[str, dict[str, Any]] = {}
        self.course_graph_lookup: dict[str, str] = {}

        def ingest_item(item: dict[str, Any]) -> None:
            source_path = str(item.get("source_path") or item.get("raw_copy_path") or "").strip()
            file_name = str(item.get("file_name") or "").strip()
            filename = Path(source_path).name if source_path else file_name
            title = str(item.get("title") or item.get("name") or Path(filename).stem or "").strip()
            node_id = str(item.get("id") or title or Path(filename).stem or "").strip()

            node = {
                "id": node_id,
                "title": title,
                "filename": filename,
                "prerequisites": self._normalize_graph_list(item.get("prerequisites")),
                "neighbors": self._normalize_graph_list(item.get("neighbors")),
                "learning_objectives": self._normalize_graph_list(item.get("learning_objectives")),
                "must_know": self._normalize_graph_list(item.get("must_know")),
                "common_errors": self._normalize_graph_list(item.get("common_errors")),
                "teaching_modes": self._normalize_graph_list(item.get("teaching_modes")),
                "assessment_modes": self._normalize_graph_list(item.get("assessment_modes")),
                "target_mastery_level": str(item.get("target_mastery_level") or "").strip(),
                "difficulty": str(item.get("difficulty") or "").strip(),
            }
            if title:
                self.course_graph_nodes[title] = node

            for candidate in [node_id, title, filename, Path(filename).stem if filename else ""]:
                normalized_candidate = _normalize_lookup_text(candidate)
                if normalized_candidate and title:
                    self.course_graph_lookup[normalized_candidate] = title

            enrichment = {
                field: item.get(field)
                for field in GRAPH_NOTE_ENRICHMENT_FIELDS
                if item.get(field) not in (None, "", [], {})
            }
            if title:
                enrichment["title"] = title
                enrichment["_title"] = title
            if filename:
                enrichment["_filename"] = filename
                index[filename] = enrichment
            if title:
                index[title] = enrichment

        try:
            if notes_path.exists():
                with notes_path.open("r", encoding="utf-8") as file_obj:
                    for line in file_obj:
                        line = line.strip()
                        if not line:
                            continue
                        ingest_item(json.loads(line))
                return index

            if graph_path.exists():
                graph_obj = json.loads(graph_path.read_text(encoding="utf-8"))
                for item in list(graph_obj.get("nodes") or []):
                    if isinstance(item, dict):
                        ingest_item(item)
                print(
                    "⚠️ [RAG] 未找到 notes.jsonl，已回退使用 graph.json 加载课程图谱。"
                )
                return index

            print(
                "⚠️ [RAG] 课程图谱文件缺失：未找到 notes.jsonl 或 graph.json。"
                f"期望路径: {notes_path} 或 {graph_path}"
            )
            return index
        except Exception as exc:
            print(f"⚠️ [RAG] 课程图谱精细化字段加载失败，已忽略: {exc}")
            return {}
        return index

    def _normalize_graph_list(self, value: Any) -> list[str]:
        if isinstance(value, list):
            return _dedupe_texts([str(item).strip() for item in value if str(item).strip()])
        if isinstance(value, dict):
            return _dedupe_texts([str(key).strip() for key in value.keys() if str(key).strip()])
        text = str(value or "").strip()
        if not text:
            return []
        parts = re.split(r"[；;、,，/\n]+", text)
        return _dedupe_texts(parts)

    def _serialize_graph_value(self, value: Any) -> str:
        if isinstance(value, list):
            items = [str(item).strip() for item in value if str(item).strip()]
            return "；".join(items)
        if isinstance(value, dict):
            parts: list[str] = []
            for key, sub_value in value.items():
                if isinstance(sub_value, dict):
                    reason = str(sub_value.get("reason") or "").strip()
                    priority = str(sub_value.get("priority") or "").strip()
                    fragment = f"{key}:{priority}" if priority else str(key)
                    if reason:
                        fragment = f"{fragment} {reason}"
                    parts.append(fragment.strip())
                else:
                    text = str(sub_value).strip()
                    if text:
                        parts.append(f"{key}:{text}")
            return "；".join([part for part in parts if part])
        return str(value or "").strip()

    def _graph_enrichment_for_file(self, filename: str) -> dict[str, str]:
        raw = self.course_graph_index.get(filename) or self.course_graph_index.get(Path(filename).stem) or {}
        if not raw:
            return {}

        serialized: dict[str, str] = {}
        for key, value in raw.items():
            if str(key).startswith("_"):
                continue
            text = self._serialize_graph_value(value)
            if text:
                serialized[f"kg_{key}"] = text
        return serialized

    def _split_record_key(self, key: str) -> tuple[str, str]:
        raw = str(key or "").strip()
        if "::" in raw:
            scope, filename = raw.split("::", 1)
            return scope or SOURCE_SCOPE_SUPPLEMENTAL, filename
        return SOURCE_SCOPE_SUPPLEMENTAL, raw

    def _source_priority(self, source_scope: str) -> int:
        return 0 if source_scope == SOURCE_SCOPE_COURSE_PRIMARY else 1

    def _find_record(self, filename: str, source_scope: str) -> dict[str, Any] | None:
        record = self.knowledge_index.get(self._record_key(filename, source_scope))
        if record is not None:
            return record
        if source_scope == SOURCE_SCOPE_SUPPLEMENTAL:
            legacy = self.knowledge_index.get(filename)
            if isinstance(legacy, dict):
                return legacy
        return None

    def _pop_record(self, filename: str, source_scope: str) -> None:
        self.knowledge_index.pop(self._record_key(filename, source_scope), None)
        if source_scope == SOURCE_SCOPE_SUPPLEMENTAL:
            self.knowledge_index.pop(filename, None)

    def _infer_source_scope(self, source_path: str) -> str:
        try:
            resolved = Path(source_path).resolve()
        except Exception:
            return SOURCE_SCOPE_SUPPLEMENTAL
        try:
            resolved.relative_to(self.course_primary_dir)
            return SOURCE_SCOPE_COURSE_PRIMARY
        except Exception:
            return SOURCE_SCOPE_SUPPLEMENTAL

    def _source_bucket_key(self, metadata: dict[str, Any]) -> tuple[str, str]:
        return (
            str(metadata.get("source_scope") or SOURCE_SCOPE_SUPPLEMENTAL),
            str(metadata.get("filename") or "").strip(),
        )

    def _collection_name_for_scope(self, source_scope: str) -> str:
        return f"knowledge__{source_scope}"

    def _create_vector_store(self, source_scope: str) -> Chroma:
        persist_directory = None
        if self.settings.vector_store_backend == "chroma":
            persist_directory = self.settings.vector_store_dir

        return Chroma(
            collection_name=self._collection_name_for_scope(source_scope),
            embedding_function=self.embeddings,
            persist_directory=persist_directory,
        )

    def _create_vector_stores(self) -> dict[str, Chroma]:
        stores: dict[str, Chroma] = {}
        for spec in self.source_specs:
            stores[spec.scope] = self._create_vector_store(spec.scope)
        return stores

    def _vector_store_for_scope(self, source_scope: str) -> Chroma | None:
        return self.vector_stores.get(source_scope)

    def _refresh_bm25_views(self) -> None:
        self.bm25_docs = []
        self.bm25 = None
        for spec in self.source_specs:
            docs = list(self.bm25_docs_by_scope.get(spec.scope) or [])
            self.bm25_docs.extend(docs)
            if self.bm25 is None and self.bm25_by_scope.get(spec.scope) is not None:
                self.bm25 = self.bm25_by_scope.get(spec.scope)

    def _vector_doc_count(self) -> int:
        if not self.vector_stores:
            return 0
        count = 0
        for scope in [spec.scope for spec in self.source_specs]:
            store = self._vector_store_for_scope(scope)
            if store is None:
                continue
            try:
                count += int(store._collection.count())
            except Exception:
                count += len(self.bm25_docs_by_scope.get(scope) or [])
        return count

    def _doc_key(self, doc: Document) -> tuple[str, str, Any, str]:
        metadata = doc.metadata or {}
        return (
            str(metadata.get("source_scope") or SOURCE_SCOPE_SUPPLEMENTAL),
            str(metadata.get("filename", "")),
            metadata.get("chunk_id", -1),
            (doc.page_content or "")[:120],
        )

    def _raw_query_for_rewrite(self, query: str, rewrite_request: RetrievalRewriteRequest | None) -> str:
        if rewrite_request and str(rewrite_request.raw_query or "").strip():
            return str(rewrite_request.raw_query or "").strip()
        return str(query or "").strip()

    def _extract_required_must_keep(self, text: str) -> list[str]:
        cleaned = str(text or "").strip()
        if not cleaned:
            return []

        required: list[str] = []
        for token in re.findall(r"[A-Za-z][A-Za-z0-9_\-\.]{1,24}|[\u4e00-\u9fff0-9]{2,24}", cleaned):
            normalized = token.strip()
            if not normalized:
                continue
            has_digit = any(ch.isdigit() for ch in normalized)
            is_ascii_term = bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9_\-\.]{1,24}", normalized))
            if has_digit or is_ascii_term:
                required.append(normalized)

        if re.search(r"\.(pdf|md|txt|markdown)\b", cleaned, flags=re.IGNORECASE):
            required.append(cleaned)

        return _dedupe_texts(required)

    def _looks_like_exact_lookup(self, query: str) -> bool:
        text = str(query or "").strip()
        if not text:
            return False
        lowered = text.lower()
        if re.search(r"\.(pdf|md|txt|markdown)\b", lowered):
            return True
        if any(marker in text for marker in QUESTION_HINT_MARKERS):
            return False
        if QUESTION_WORD_PATTERN.search(text):
            return False

        terms = _extract_lookup_terms(text)
        normalized = _normalize_lookup_text(text)
        if not terms or not normalized:
            return False

        if any(ch.isdigit() for ch in text) and len(terms) <= 3 and len(text) <= 32 and " " not in text:
            return True

        if len(terms) == 1 and re.fullmatch(r"[A-Za-z][A-Za-z0-9_\-\.]{1,16}", text):
            return True

        return False

    def _query_expresses_goal_intent(self, query: str) -> bool:
        text = str(query or "").strip()
        if not text:
            return False
        if QUESTION_WORD_PATTERN.search(text):
            return True
        lowered = text.lower()
        return any(
            marker in lowered
            for marker in [
                "how",
                "what",
                "why",
                "difference",
                "compare",
                "comparison",
                "example",
                "examples",
                "error",
                "issue",
                "troubleshoot",
                "step",
                "steps",
            ]
        )

    def _extract_goal_terms(self, query: str) -> list[str]:
        lowered = str(query or "").strip().lower()
        if not lowered:
            return []

        candidates: list[str] = []
        seen: set[str] = set()
        for term in re.findall(r"[a-z0-9]{2,}|[\u4e00-\u9fff]{2,}", lowered):
            cleaned = _strip_query_prefixes(term)
            if not cleaned or cleaned in QUESTION_HINT_MARKERS or len(cleaned) < 2:
                continue
            normalized = _normalize_lookup_text(cleaned)
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            candidates.append(cleaned)
        return candidates

    def _doc_query_term_alignment(self, doc: Document, query_terms: list[str]) -> tuple[int, float, list[str]]:
        if not query_terms:
            return 0, 0.0, []

        metadata = dict(doc.metadata or {})
        combined = " ".join(
            [
                doc.page_content or "",
                str(metadata.get("filename") or ""),
                str(metadata.get("section") or ""),
                str(metadata.get("H1") or ""),
                str(metadata.get("H2") or ""),
                str(metadata.get("H3") or ""),
            ]
        )
        haystack = _normalize_lookup_text(combined)
        if not haystack:
            return 0, 0.0, []

        matched: list[str] = []
        for term in query_terms:
            needle = _normalize_lookup_text(term)
            if not needle:
                continue
            if needle in haystack:
                matched.append(term)

        hit_count = len(matched)
        ratio = hit_count / len(query_terms) if query_terms else 0.0
        return hit_count, ratio, matched

    def _missing_query_terms(self, query_terms: list[str], matched_terms: list[str]) -> list[str]:
        matched_norm = {_normalize_lookup_text(term) for term in matched_terms if _normalize_lookup_text(term)}
        missing: list[str] = []
        for term in query_terms:
            normalized = _normalize_lookup_text(term)
            if normalized and normalized not in matched_norm:
                missing.append(term)
        return missing

    def _infer_rewrite_intent(self, query: str, rewrite_request: RetrievalRewriteRequest) -> str:
        text = " ".join(
            [
                str(query or ""),
                str(rewrite_request.raw_query or ""),
                str(rewrite_request.current_topic or ""),
                str(rewrite_request.conversation_hint or ""),
            ]
        ).lower()
        if self._looks_like_exact_lookup(query):
            return "exact_lookup"
        if any(marker in text for marker in ["报错", "错误", "失败", "原因", "解决", "排查", "error", "issue", "troubleshoot"]):
            return "troubleshoot"
        if any(marker in text for marker in ["区别", "差别", "对比", "compare", "comparison", "difference"]):
            return "comparison"
        if any(marker in text for marker in ["例子", "应用", "案例", "example", "examples", "application"]):
            return "example_application"
        if any(marker in text for marker in ["怎么", "如何", "步骤", "流程", "方法", "how", "step", "steps"]):
            return "procedure"
        return "concept_overview"

    def _should_force_goal_rewrite(self, query: str, summary: dict[str, Any]) -> bool:
        if not self._query_expresses_goal_intent(query):
            return False
        query_term_count = int(summary.get("query_term_count") or 0)
        if query_term_count <= 0:
            return False
        best_query_term_hits = int(summary.get("best_query_term_hits") or 0)
        best_query_term_ratio = float(summary.get("best_query_term_ratio") or 0.0)
        return best_query_term_hits < min(2, query_term_count) and best_query_term_ratio < 0.6

    def _build_heuristic_rewrite_plan(
        self,
        query: str,
        rewrite_request: RetrievalRewriteRequest,
        *,
        intent_hint: str = "",
    ) -> RetrievalRewritePlan:
        raw_query = self._raw_query_for_rewrite(query, rewrite_request)
        current_topic = str(rewrite_request.current_topic or "").strip()
        intent = intent_hint or self._infer_rewrite_intent(raw_query, rewrite_request)
        if intent not in RETRIEVAL_REWRITE_INTENTS:
            intent = "concept_overview"

        must_keep = _dedupe_texts(
            self._extract_required_must_keep(raw_query)
            + self._extract_required_must_keep(current_topic)
        )
        goal_terms = self._extract_goal_terms(raw_query)
        anchor_terms = _dedupe_texts([current_topic] + goal_terms + must_keep)
        anchor_text = " ".join(anchor_terms).strip()

        if intent == "procedure":
            vector_queries = _dedupe_texts(
                [
                    f"{anchor_text} 操作流程".strip(),
                    f"{anchor_text} 步骤 方法".strip(),
                ]
            )
            bm25_queries = _dedupe_texts(
                [
                    f"{anchor_text} 步骤".strip(),
                    f"{anchor_text} 登录 操作".strip() if "登录" in anchor_text else f"{anchor_text} 操作".strip(),
                ]
            )
        elif intent == "comparison":
            vector_queries = _dedupe_texts(
                [
                    f"{anchor_text} 区别 对比".strip(),
                    f"{anchor_text} 适用场景 差异".strip(),
                ]
            )
            bm25_queries = _dedupe_texts(
                [
                    f"{anchor_text} 区别".strip(),
                    f"{anchor_text} 对比".strip(),
                ]
            )
        elif intent == "example_application":
            vector_queries = _dedupe_texts(
                [
                    f"{anchor_text} 例子 应用".strip(),
                    f"{anchor_text} 案例 场景".strip(),
                ]
            )
            bm25_queries = _dedupe_texts(
                [
                    f"{anchor_text} 例子".strip(),
                    f"{anchor_text} 应用".strip(),
                ]
            )
        elif intent == "troubleshoot":
            vector_queries = _dedupe_texts(
                [
                    f"{anchor_text} 原因 解决".strip(),
                    f"{anchor_text} 排查 修复".strip(),
                ]
            )
            bm25_queries = _dedupe_texts(
                [
                    f"{anchor_text} 报错 原因".strip(),
                    f"{anchor_text} 解决 排查".strip(),
                ]
            )
        else:
            vector_queries = _dedupe_texts(
                [
                    f"{anchor_text} 核心概念".strip(),
                    f"{anchor_text} 定义 原理".strip(),
                ]
            )
            bm25_queries = _dedupe_texts(
                [
                    f"{anchor_text} 定义".strip(),
                    f"{anchor_text} 原理".strip(),
                ]
            )

        return RetrievalRewritePlan(
            intent=intent,
            rewrite_needed=True,
            reason="raw retrieval misses the user goal terms; use heuristic goal-oriented rewrite fallback",
            must_keep=must_keep,
            vector_queries=vector_queries[:MAX_REWRITE_VECTOR_QUERIES],
            bm25_queries=bm25_queries[:MAX_REWRITE_BM25_QUERIES],
            metadata_terms=anchor_terms[:MAX_REWRITE_METADATA_TERMS],
        )

    def _build_retrieval_planner_prompt(
        self,
        query: str,
        rewrite_request: RetrievalRewriteRequest,
    ) -> tuple[SystemMessage, HumanMessage]:
        system_msg = SystemMessage(
            content=(
                "你是教学知识库的检索规划器。你的任务不是回答问题，而是为混合检索生成更好的查询计划。"
                "必须严格输出 JSON，不要输出代码块，不要输出 JSON 以外的解释。\n"
                "JSON schema:\n"
                "{\n"
                '  "intent": "exact_lookup|concept_overview|procedure|comparison|example_application|troubleshoot",\n'
                '  "rewrite_needed": true,\n'
                '  "reason": "一句话说明为什么需要或不需要改写",\n'
                '  "must_keep": ["不能丢的实体/术语"],\n'
                '  "vector_queries": ["适合语义检索的查询1", "适合语义检索的查询2"],\n'
                '  "bm25_queries": ["适合关键词检索的查询1", "适合关键词检索的查询2"],\n'
                '  "metadata_terms": ["适合命中文件名/标题/小节名的短词"]\n'
                "}\n"
                "要求：\n"
                "1. 不要改写成泛泛问题，必须围绕用户当前目标。\n"
                "2. 不要删除文件编号、英文术语、关键实体。\n"
                "3. vector_queries 与 bm25_queries 各最多 2 条，metadata_terms 最多 4 条。\n"
                "4. 如果原查询已经足够精确，也要返回 JSON，但 rewrite_needed=false。"
            )
        )
        weak_hint = str(rewrite_request.weak_areas_hint or "").strip() or "无"
        conversation_hint = str(rewrite_request.conversation_hint or "").strip() or "无"
        human_msg = HumanMessage(
            content=(
                f"检索通道：{rewrite_request.channel}\n"
                f"原始检索 query：{query}\n"
                f"用户原话：{rewrite_request.raw_query}\n"
                f"当前主题：{rewrite_request.current_topic}\n"
                f"尝试轮次：{rewrite_request.attempt_count}\n"
                f"教学策略：{rewrite_request.teaching_strategy}\n"
                f"薄弱点提示：{weak_hint}\n"
                f"最近会话提示：{conversation_hint}\n"
                "请基于“用户真正想解决什么问题”来决定是否改写检索。"
            )
        )
        return system_msg, human_msg

    def _invoke_retrieval_planner(
        self,
        query: str,
        rewrite_request: RetrievalRewriteRequest,
    ) -> tuple[RetrievalRewritePlan | None, str]:
        if self.retrieval_planner_llm is None:
            return None, "retrieval rewrite planner unavailable"

        try:
            system_msg, human_msg = self._build_retrieval_planner_prompt(query, rewrite_request)
            response = self.retrieval_planner_llm.invoke([system_msg, human_msg])
            payload = parse_json_object(content_to_text(getattr(response, "content", response)))
            if payload is None:
                return None, "planner returned invalid JSON"
            return self._sanitize_rewrite_plan(payload, query=query, rewrite_request=rewrite_request), ""
        except Exception as exc:
            return None, f"planner invocation failed: {exc}"

    def _sanitize_rewrite_plan(
        self,
        payload: dict[str, Any],
        *,
        query: str,
        rewrite_request: RetrievalRewriteRequest,
    ) -> RetrievalRewritePlan:
        intent = str(payload.get("intent") or "concept_overview").strip().lower()
        if intent not in RETRIEVAL_REWRITE_INTENTS:
            intent = "concept_overview"

        plan = RetrievalRewritePlan(
            intent=intent,
            rewrite_needed=bool(payload.get("rewrite_needed", False)),
            reason=str(payload.get("reason") or "").strip()[:240],
            must_keep=_dedupe_texts([str(item) for item in payload.get("must_keep", []) if str(item or "").strip()]),
            vector_queries=_dedupe_texts([str(item) for item in payload.get("vector_queries", []) if str(item or "").strip()])[:MAX_REWRITE_VECTOR_QUERIES],
            bm25_queries=_dedupe_texts([str(item) for item in payload.get("bm25_queries", []) if str(item or "").strip()])[:MAX_REWRITE_BM25_QUERIES],
            metadata_terms=_dedupe_texts([str(item) for item in payload.get("metadata_terms", []) if str(item or "").strip()])[:MAX_REWRITE_METADATA_TERMS],
        )
        required_terms = _dedupe_texts(
            self._extract_required_must_keep(self._raw_query_for_rewrite(query, rewrite_request))
            + self._extract_required_must_keep(rewrite_request.current_topic)
        )
        plan.must_keep = _dedupe_texts(plan.must_keep + required_terms)
        return plan

    def _repair_query_with_must_keep(self, query: str, must_keep: list[str]) -> tuple[str, bool]:
        repaired = str(query or "").strip()
        changed = False
        for term in must_keep:
            if not term:
                continue
            if term.lower() not in repaired.lower():
                repaired = f"{repaired} {term}".strip()
                changed = True
        return repaired, changed

    def _repair_rewrite_plan(self, plan: RetrievalRewritePlan) -> tuple[RetrievalRewritePlan, bool]:
        repaired = False
        vector_queries: list[str] = []
        for query in plan.vector_queries:
            fixed, changed = self._repair_query_with_must_keep(query, plan.must_keep)
            vector_queries.append(fixed)
            repaired = repaired or changed

        bm25_queries: list[str] = []
        for query in plan.bm25_queries:
            fixed, changed = self._repair_query_with_must_keep(query, plan.must_keep)
            bm25_queries.append(fixed)
            repaired = repaired or changed

        metadata_terms = _dedupe_texts(list(plan.metadata_terms) + list(plan.must_keep))[:MAX_REWRITE_METADATA_TERMS]
        if metadata_terms != plan.metadata_terms:
            repaired = True

        return (
            RetrievalRewritePlan(
                intent=plan.intent,
                rewrite_needed=plan.rewrite_needed,
                reason=plan.reason,
                must_keep=list(plan.must_keep),
                vector_queries=_dedupe_texts(vector_queries)[:MAX_REWRITE_VECTOR_QUERIES],
                bm25_queries=_dedupe_texts(bm25_queries)[:MAX_REWRITE_BM25_QUERIES],
                metadata_terms=metadata_terms,
            ),
            repaired,
        )

    def _build_confidence_summary(self, docs: list[Document], query: str = "") -> dict[str, Any]:
        query_terms = self._extract_goal_terms(query)
        summary = {
            "hit_count": len(docs),
            "citation_confident": False,
            "top_filename": "",
            "top_source_scope": "",
            "dominance": 0.0,
            "top_rrf_score": 0.0,
            "top_source_count": 0,
            "top_multi_source": False,
            "top_strong_match": False,
            "query_term_count": len(query_terms),
            "query_terms": list(query_terms),
            "top_query_term_hits": 0,
            "top_query_term_ratio": 0.0,
            "top_query_terms_matched": [],
            "top_query_terms_missing": list(query_terms),
            "best_query_term_hits": 0,
            "best_query_term_ratio": 0.0,
            "best_query_terms_matched": [],
            "best_query_terms_missing": list(query_terms),
        }
        if not docs:
            return summary

        grouped: dict[tuple[str, str], dict[str, Any]] = {}
        total_weight = 0.0
        for rank, doc in enumerate(docs, start=1):
            metadata = dict(doc.metadata or {})
            filename = str(metadata.get("filename") or "").strip()
            source_scope = str(metadata.get("source_scope") or SOURCE_SCOPE_SUPPLEMENTAL)
            term_hits, term_ratio, matched_terms = self._doc_query_term_alignment(doc, query_terms)
            if rank == 1:
                summary["top_query_term_hits"] = int(term_hits)
                summary["top_query_term_ratio"] = float(term_ratio)
                summary["top_query_terms_matched"] = matched_terms
                summary["top_query_terms_missing"] = self._missing_query_terms(query_terms, matched_terms)
            if term_hits > int(summary["best_query_term_hits"]) or (
                term_hits == int(summary["best_query_term_hits"]) and term_ratio > float(summary["best_query_term_ratio"])
            ):
                summary["best_query_term_hits"] = int(term_hits)
                summary["best_query_term_ratio"] = float(term_ratio)
                summary["best_query_terms_matched"] = matched_terms
                summary["best_query_terms_missing"] = self._missing_query_terms(query_terms, matched_terms)
            if not filename:
                continue
            weight = float(metadata.get("_rrf_score") or (1.0 / (RRF_K + rank)))
            total_weight += weight
            bucket = grouped.setdefault(
                (source_scope, filename),
                {
                    "weight": 0.0,
                    "best_rrf": 0.0,
                    "multi_source": False,
                    "strong_match": False,
                    "top3_count": 0,
                    "top_source_count": 0,
                },
            )
            bucket["weight"] += weight
            bucket["best_rrf"] = max(bucket["best_rrf"], float(metadata.get("_rrf_score") or 0.0))
            source_count = len(set(metadata.get("_retrieval_sources", [])))
            bucket["top_source_count"] = max(bucket["top_source_count"], source_count)
            bucket["multi_source"] = bucket["multi_source"] or source_count >= 2
            signals = list(metadata.get("_query_match_signals", []))
            bucket["strong_match"] = bucket["strong_match"] or any(signal in {"filename", "title"} for signal in signals)
            if rank <= 3:
                bucket["top3_count"] += 1

        if not grouped or total_weight <= 0:
            return summary

        (top_source_scope, top_filename), top_bucket = max(grouped.items(), key=lambda item: item[1]["weight"])
        dominance = float(top_bucket["weight"]) / total_weight if total_weight else 0.0
        citation_confident = bool(top_bucket["strong_match"]) or (
            dominance >= CONFIDENT_CITATION_MIN_DOMINANCE
            and float(top_bucket["best_rrf"]) >= CONFIDENT_CITATION_MIN_RRF
            and (int(top_bucket["top3_count"]) >= 2 or bool(top_bucket["multi_source"]))
        )

        summary.update(
            {
                "citation_confident": citation_confident,
                "top_filename": top_filename,
                "top_source_scope": top_source_scope,
                "dominance": float(dominance),
                "top_rrf_score": float(top_bucket["best_rrf"]),
                "top_source_count": int(top_bucket["top_source_count"]),
                "top_multi_source": bool(top_bucket["multi_source"]),
                "top_strong_match": bool(top_bucket["strong_match"]),
            }
        )
        return summary

    def _confidence_rank_tuple(self, summary: dict[str, Any]) -> tuple:
        return (
            int(bool(summary.get("citation_confident"))),
            int(bool(summary.get("top_strong_match"))),
            int(bool(summary.get("top_multi_source"))),
            int(summary.get("top_source_count") or 0),
            float(summary.get("dominance") or 0.0),
            float(summary.get("top_rrf_score") or 0.0),
            int(summary.get("hit_count") or 0),
        )

    def _goal_alignment_rank_tuple(self, summary: dict[str, Any]) -> tuple:
        return (
            int(summary.get("best_query_term_hits") or 0),
            float(summary.get("best_query_term_ratio") or 0.0),
        )

    def _should_skip_rewrite_for_raw_confidence(
        self,
        query: str,
        docs: list[Document],
    ) -> tuple[bool, str, dict[str, Any]]:
        summary = self._build_confidence_summary(docs, query=query)
        goal_intent = self._query_expresses_goal_intent(query)
        strong_support = bool(summary.get("top_multi_source")) or int(summary.get("top_source_count") or 0) >= 2
        dominance = float(summary.get("dominance") or 0.0)
        top_rrf_score = float(summary.get("top_rrf_score") or 0.0)
        citation_confident = bool(summary.get("citation_confident"))
        best_query_term_hits = int(summary.get("best_query_term_hits") or 0)
        best_query_term_ratio = float(summary.get("best_query_term_ratio") or 0.0)
        query_term_count = int(summary.get("query_term_count") or 0)
        goal_alignment_strong = (
            query_term_count == 0
            or best_query_term_hits >= min(2, query_term_count)
            or best_query_term_ratio >= 0.6
        )
        strong_raw_confidence = citation_confident and (
            strong_support
            or (
                dominance >= CONFIDENT_CITATION_MIN_DOMINANCE
                and top_rrf_score >= CONFIDENT_CITATION_MIN_RRF
            )
        )

        if summary.get("top_strong_match") and not goal_intent:
            return True, "raw retrieval already has strong filename/title signal", summary
        if goal_intent and not goal_alignment_strong:
            return False, "raw retrieval misses the user goal terms; rewrite may help", summary
        if strong_raw_confidence:
            return True, "raw retrieval is already confident", summary
        return False, "raw retrieval confidence is weak", summary

    def _load_index(self) -> dict[str, dict[str, Any]]:
        normalized: dict[str, dict[str, Any]] = {}

        def ingest(data: dict[str, Any], *, default_scope: str | None = None) -> None:
            for raw_key, raw_record in data.items():
                if not isinstance(raw_record, dict):
                    continue
                source_scope, filename = self._split_record_key(str(raw_key))
                if default_scope:
                    source_scope = default_scope
                    filename = str(raw_key)
                record = dict(raw_record)
                record["source_scope"] = source_scope
                normalized[self._record_key(filename, source_scope)] = record

        split_exists = any(path.exists() for path in self.index_files.values())
        if split_exists:
            for scope, path in self.index_files.items():
                if not path.exists():
                    continue
                try:
                    with path.open("r", encoding="utf-8") as file_obj:
                        data = json.load(file_obj)
                    if isinstance(data, dict):
                        ingest(data, default_scope=scope)
                except Exception as exc:
                    print(f"⚠️ [RAG] 读取知识库索引失败，将忽略 {path.name}: {exc}")
            return normalized

        if not self.index_file.exists():
            return {}

        try:
            with self.index_file.open("r", encoding="utf-8") as file_obj:
                data = json.load(file_obj)
                if isinstance(data, dict):
                    ingest(data)
                    return normalized
        except Exception as exc:
            print(f"⚠️ [RAG] 读取知识库索引失败，将使用空索引: {exc}")

        return {}

    def _save_index(self) -> None:
        try:
            self.index_file.parent.mkdir(parents=True, exist_ok=True)
            payloads: dict[str, dict[str, Any]] = {scope: {} for scope in self.index_files}
            for record_key, record in self.knowledge_index.items():
                source_scope, filename = self._split_record_key(record_key)
                clean_record = dict(record)
                clean_record["source_scope"] = source_scope
                payloads.setdefault(source_scope, {})[filename] = clean_record

            for scope, path in self.index_files.items():
                with path.open("w", encoding="utf-8") as file_obj:
                    json.dump(payloads.get(scope, {}), file_obj, ensure_ascii=False, indent=2)
            self.index_file.unlink(missing_ok=True)
        except Exception as exc:
            print(f"⚠️ [RAG] 保存知识库索引失败: {exc}")

    def _current_retrieval_state(self) -> dict[str, Any]:
        return {
            "version": RETRIEVAL_STATE_VERSION,
            "embedding_provider": self.settings.embedding_provider,
            "embedding_model_name": self.settings.embedding_model_name,
            "vector_store_backend": self.settings.vector_store_backend,
            "vector_store_dir": self.settings.vector_store_dir,
            "vector_store_layout": {spec.scope: self._collection_name_for_scope(spec.scope) for spec in self.source_specs},
            "knowledge_index_layout": {scope: path.name for scope, path in self.index_files.items()},
            "knowledge_chunk_size": int(self.settings.knowledge_chunk_size),
            "knowledge_chunk_overlap": int(self.settings.knowledge_chunk_overlap),
        }

    def _load_retrieval_state(self) -> dict[str, Any]:
        if not self.retrieval_state_file.exists():
            return {}

        try:
            with self.retrieval_state_file.open("r", encoding="utf-8") as file_obj:
                payload = json.load(file_obj)
                if isinstance(payload, dict):
                    return payload
        except Exception as exc:
            print(f"⚠️ [RAG] 读取检索状态失败，将重新评估兼容性: {exc}")

        return {}

    def _save_retrieval_state(self) -> None:
        self.retrieval_state = self._current_retrieval_state()
        try:
            self.retrieval_state_file.parent.mkdir(parents=True, exist_ok=True)
            with self.retrieval_state_file.open("w", encoding="utf-8") as file_obj:
                json.dump(self.retrieval_state, file_obj, ensure_ascii=False, indent=2)
        except Exception as exc:
            print(f"⚠️ [RAG] 保存检索状态失败: {exc}")

    def _clear_retrieval_artifacts(self) -> None:
        vector_dir = Path(self.settings.vector_store_dir)
        if self.settings.vector_store_backend == "chroma" and vector_dir.exists():
            shutil.rmtree(vector_dir, ignore_errors=True)

        for cache_path in self.knowledge_dir.parent.glob("bm25_cache*.json"):
            cache_path.unlink(missing_ok=True)
        for index_path in self.knowledge_dir.parent.glob("knowledge_index*.json"):
            index_path.unlink(missing_ok=True)

        self.knowledge_index = {}
        self._save_index()

    def _ensure_retrieval_compatibility(self) -> None:
        current_state = self._current_retrieval_state()
        previous_state = self.retrieval_state or {}

        if previous_state == current_state:
            return

        vector_dir = Path(self.settings.vector_store_dir)
        legacy_vectors_exist = (
            self.settings.vector_store_backend == "chroma"
            and vector_dir.exists()
            and any(vector_dir.iterdir())
        )
        indexed_docs_exist = bool(self.knowledge_index)

        should_rebuild = False
        if previous_state:
            should_rebuild = True
            print("♻️ [RAG] 检测到 embedding / chunk 配置变化，正在重建知识向量索引...")
        elif legacy_vectors_exist and indexed_docs_exist:
            should_rebuild = True
            print("♻️ [RAG] 检测到历史向量库缺少兼容性状态文件，正在执行一次安全重建...")

        if should_rebuild:
            self._clear_retrieval_artifacts()

        self.retrieval_state = current_state

    def _bm25_signature(self, source_scope: str) -> str:
        scope_index = {
            key: value
            for key, value in self.knowledge_index.items()
            if self._split_record_key(key)[0] == source_scope
        }
        payload = {
            "version": RETRIEVAL_STATE_VERSION,
            "source_scope": source_scope,
            "tokenizer": "regex_v2_multilingual_terms",
            "knowledge_index": scope_index,
        }
        serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def _to_json_safe(self, value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        if isinstance(value, dict):
            return {str(key): self._to_json_safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self._to_json_safe(item) for item in value]
        return str(value)

    def _load_bm25_cache(self, signature: str, *, source_scope: str) -> bool:
        cache_file = self._bm25_cache_file_for_scope(source_scope)
        if not cache_file.exists():
            return False

        try:
            with cache_file.open("r", encoding="utf-8") as file_obj:
                payload = json.load(file_obj)
        except Exception as exc:
            print(f"⚠️ [RAG] 读取 BM25 缓存失败，将重建索引: {exc}")
            return False

        if not isinstance(payload, dict) or payload.get("signature") != signature:
            return False

        docs_payload = payload.get("docs", [])
        tokens_payload = payload.get("tokenized_corpus", [])

        if not isinstance(docs_payload, list) or not isinstance(tokens_payload, list):
            return False

        docs: list[Document] = []
        tokenized_corpus: list[list[str]] = []

        for item in docs_payload:
            if not isinstance(item, dict):
                continue
            metadata = item.get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = {}
            docs.append(
                Document(
                    page_content=str(item.get("page_content", "")),
                    metadata=metadata,
                )
            )

        for row in tokens_payload:
            if not isinstance(row, list):
                tokenized_corpus.append([])
                continue
            tokenized_corpus.append([str(token) for token in row if str(token)])

        if len(docs) != len(tokenized_corpus):
            return False

        self.bm25_docs_by_scope[source_scope] = docs
        self.bm25_by_scope[source_scope] = BM25Okapi(tokenized_corpus) if tokenized_corpus else None
        self._refresh_bm25_views()
        return True

    def _save_bm25_cache(self, signature: str, tokenized_corpus: list[list[str]], *, source_scope: str) -> None:
        try:
            docs_payload = [
                {
                    "page_content": doc.page_content,
                    "metadata": self._to_json_safe(doc.metadata or {}),
                }
                for doc in (self.bm25_docs_by_scope.get(source_scope) or [])
            ]
            payload = {
                "version": 1,
                "signature": signature,
                "docs": docs_payload,
                "tokenized_corpus": tokenized_corpus,
            }
            cache_file = self._bm25_cache_file_for_scope(source_scope)
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            with cache_file.open("w", encoding="utf-8") as file_obj:
                json.dump(payload, file_obj, ensure_ascii=False)
        except Exception as exc:
            print(f"⚠️ [RAG] 保存 BM25 缓存失败: {exc}")

    def _get_file_fingerprint(self, file_path: str) -> str:
        stat = os.stat(file_path)
        return f"{os.path.basename(file_path)}_{stat.st_size}_{int(stat.st_mtime)}"

    def _should_process(self, file_path: str, *, source_scope: str) -> bool:
        filename = os.path.basename(file_path)
        fingerprint = self._get_file_fingerprint(file_path)
        old_record = self._find_record(filename, source_scope)
        return not old_record or old_record.get("fingerprint") != fingerprint

    def _delete_existing_vectors(self, filename: str, *, source_scope: str) -> None:
        store = self._vector_store_for_scope(source_scope)
        if store is None:
            return

        try:
            store._collection.delete(
                where={
                    "$and": [
                        {"filename": filename},
                        {"source_scope": source_scope},
                    ]
                }
            )
        except Exception as exc:
            print(f"⚠️ [RAG] 删除旧向量失败: {source_scope}/{filename}: {exc}")

    def _delete_all_vectors(self, *, source_scope: str | None = None) -> None:
        scopes = [source_scope] if source_scope else [spec.scope for spec in self.source_specs]
        for scope in scopes:
            store = self._vector_store_for_scope(scope)
            if store is None:
                continue
            try:
                raw = store._collection.get(include=[])
                ids = raw.get("ids") or []
                if ids:
                    store._collection.delete(ids=ids)
            except Exception as exc:
                print(f"⚠️ [RAG] 清空向量库失败: {scope}: {exc}")

    def _sync_knowledge_dir(self) -> None:
        self._cleanup_deleted_files()

        for spec in self.source_specs:
            if not spec.path.exists():
                continue
            for file_path in sorted(glob.glob(os.path.join(str(spec.path), "*.*"))):
                if Path(file_path).name == ".gitkeep":
                    continue
                if not self._should_process(file_path, source_scope=spec.scope):
                    continue
                result = self.add_local_file(file_path, source_scope=spec.scope)
                if not result.get("success"):
                    print(f"⚠️ [RAG] 资料未成功入库: {spec.scope}/{Path(file_path).name}")

    def _cleanup_deleted_files(self) -> None:
        current_files_by_scope: dict[str, set[str]] = {
            spec.scope: set()
            for spec in self.source_specs
        }
        for spec in self.source_specs:
            if not spec.path.exists():
                continue
            current_files_by_scope[spec.scope] = {
                path.name
                for path in spec.path.iterdir()
                if path.is_file() and path.name != ".gitkeep"
            }

        deleted_records: list[tuple[str, str, str]] = []
        for record_key in list(self.knowledge_index.keys()):
            source_scope, filename = self._split_record_key(record_key)
            current_files = current_files_by_scope.get(source_scope, set())
            if filename in current_files:
                continue
            deleted_records.append((record_key, source_scope, filename))

        if not deleted_records:
            return

        for record_key, source_scope, filename in deleted_records:
            self._delete_existing_vectors(filename, source_scope=source_scope)
            self.knowledge_index.pop(record_key, None)

        self._save_index()

    def _docs_from_text(
        self,
        text: str,
        *,
        metadata: dict[str, Any] | None = None,
        starting_chunk_id: int = 0,
    ) -> list[Document]:
        base_metadata = dict(metadata or {})
        docs: list[Document] = []

        for offset, chunk in enumerate(
            chunk_text(
                text,
                chunk_size=self.settings.knowledge_chunk_size,
                chunk_overlap=self.settings.knowledge_chunk_overlap,
            )
        ):
            chunk_metadata = dict(base_metadata)
            chunk_metadata["chunk_id"] = starting_chunk_id + offset
            chunk_metadata["char_length"] = len(chunk)
            docs.append(Document(page_content=chunk, metadata=chunk_metadata))

        return docs

    def _parse_pdf_locally(self, file_path: str) -> list[Document]:
        docs: list[Document] = []
        chunk_id = 0

        with fitz.open(file_path) as pdf:
            for page_index, page in enumerate(pdf, start=1):
                page_text = page.get_text("text").strip()
                if not page_text:
                    continue

                page_docs = self._docs_from_text(
                    page_text,
                    metadata={
                        "section": f"page-{page_index}",
                        "page": page_index,
                        "parser": "pymupdf",
                    },
                    starting_chunk_id=chunk_id,
                )
                docs.extend(page_docs)
                chunk_id += len(page_docs)

        return docs

    def _parse_file(self, file_path: str) -> List[Document]:
        ext = Path(file_path).suffix.lower()
        filename = Path(file_path).name
        print(f"📂 [RAG] 正在解析文件: {filename}")

        if ext == ".pdf":
            if self.settings.pdf_parse_backend == "local":
                print("ℹ️ [RAG] PDF_PARSE_BACKEND=local，直接使用本地 PyMuPDF 解析。")
                return self._parse_pdf_locally(file_path)

            if self.processor is not None:
                try:
                    md_content = self.processor.parse_pdf_to_md(file_path)
                    docs = self.processor.split_by_semantics(md_content)
                    if docs:
                        return docs
                except Exception as exc:
                    if self.settings.pdf_parse_backend == "mineru":
                        raise
                    print(f"⚠️ [RAG] MinerU 解析失败，将回退到本地 PyMuPDF: {exc}")
            else:
                if self.settings.pdf_parse_backend == "mineru":
                    raise RuntimeError("PDF_PARSE_BACKEND=mineru 但未配置 MINERU_API_TOKEN。")
                print("ℹ️ [RAG] 未配置 MINERU_API_TOKEN，PDF 将直接使用本地 PyMuPDF 解析。")
            return self._parse_pdf_locally(file_path)

        if ext in {".txt", ".md", ".markdown"}:
            text = Path(file_path).read_text(encoding="utf-8")
            return self._docs_from_text(text)

        print(f"⚠️ [RAG] 暂不支持的文件类型: {filename}")
        return []

    def add_local_file(self, source_path: str, *, source_scope: str | None = None) -> dict[str, Any]:
        source_scope = source_scope or self._infer_source_scope(source_path)
        store = self._vector_store_for_scope(source_scope)
        if store is None:
            return {"success": False, "chunks": 0, "error": self.initialization_error or "vector store unavailable"}

        filename = os.path.basename(source_path)

        try:
            fingerprint = self._get_file_fingerprint(source_path)
        except FileNotFoundError:
            return {"success": False, "chunks": 0, "error": "file not found"}

        old_record = self._find_record(filename, source_scope)
        if old_record and old_record.get("fingerprint") != fingerprint:
            self._delete_existing_vectors(filename, source_scope=source_scope)

        try:
            docs = self._parse_file(source_path)
        except Exception as exc:
            return {"success": False, "chunks": 0, "error": str(exc)}

        if not docs:
            return {"success": False, "chunks": 0, "error": "no parsable content"}

        for doc in docs:
            doc.metadata = dict(doc.metadata or {})
            doc.metadata["source"] = source_path
            doc.metadata["filename"] = filename
            doc.metadata["fingerprint"] = fingerprint
            doc.metadata["source_scope"] = source_scope
            doc.metadata["source_priority"] = self._source_priority(source_scope)
            if source_scope == SOURCE_SCOPE_COURSE_PRIMARY:
                doc.metadata.update(self._graph_enrichment_for_file(filename))

        try:
            store.add_documents(docs)
        except Exception as exc:
            return {"success": False, "chunks": 0, "error": str(exc)}

        self.knowledge_index[self._record_key(filename, source_scope)] = {
            "fingerprint": fingerprint,
            "chunks": len(docs),
            "source_scope": source_scope,
        }
        self._save_index()
        self._build_bm25_index()
        return {"success": True, "chunks": len(docs)}

    def add_document(self, source_path: str) -> bool:
        if not self.vector_stores or not os.path.exists(source_path):
            return False

        destination = self.knowledge_dir / Path(source_path).name
        destination.parent.mkdir(parents=True, exist_ok=True)

        if Path(source_path).resolve() != destination.resolve():
            shutil.copy2(source_path, destination)

        return bool(self.add_local_file(str(destination)).get("success"))

    def list_documents(self) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []

        for path in sorted(self.knowledge_dir.iterdir()):
            if not path.is_file() or path.name == ".gitkeep":
                continue

            record = self._find_record(path.name, SOURCE_SCOPE_SUPPLEMENTAL) or {}
            items.append(
                {
                    "filename": path.name,
                    "size_bytes": path.stat().st_size,
                    "chunk_count": record.get("chunks"),
                }
            )

        return items

    def delete_document(self, filename: str) -> bool:
        safe_name = Path(filename).name
        removed = False

        path = self.knowledge_dir / safe_name
        if path.exists():
            path.unlink()
            removed = True

        if self._find_record(safe_name, SOURCE_SCOPE_SUPPLEMENTAL):
            self._pop_record(safe_name, SOURCE_SCOPE_SUPPLEMENTAL)
            self._save_index()
            removed = True

        self._delete_existing_vectors(safe_name, source_scope=SOURCE_SCOPE_SUPPLEMENTAL)
        self._build_bm25_index()
        return removed

    def clear_documents(self) -> int:
        files = [item["filename"] for item in self.list_documents()]
        for filename in files:
            self.delete_document(filename)

        return len(files)

    def _tokenize_for_bm25(self, text: str) -> list[str]:
        tokens: list[str] = []
        for segment in re.findall(r"[a-zA-Z0-9_\-\.\(\)]+|[\u4e00-\u9fff]+", (text or "").lower()):
            tokens.append(segment)
            if re.fullmatch(r"[\u4e00-\u9fff]{4,}", segment):
                max_ngram = min(4, len(segment))
                for size in range(2, max_ngram + 1):
                    for start in range(0, len(segment) - size + 1):
                        tokens.append(segment[start : start + size])
        return tokens

    def _metadata_title_candidates(self, metadata: dict[str, Any] | None) -> list[str]:
        metadata = dict(metadata or {})
        candidates: list[str] = []
        filename = str(metadata.get("filename") or "").strip()
        filename_stem = Path(filename).stem.strip() if filename else ""
        for candidate in [
            filename_stem,
            metadata.get("H1"),
            metadata.get("H2"),
            metadata.get("H3"),
            metadata.get("section"),
        ]:
            value = str(candidate or "").strip()
            if not value:
                continue
            if re.fullmatch(r"page-\d+", value.lower()):
                continue
            if value not in candidates:
                candidates.append(value)
        for candidate in [
            metadata.get("kg_title"),
            metadata.get("kg_prerequisites"),
            metadata.get("kg_neighbors"),
            metadata.get("kg_learning_objectives"),
            metadata.get("kg_must_know"),
            metadata.get("kg_target_mastery_level"),
            metadata.get("kg_difficulty"),
        ]:
            value = str(candidate or "").strip()
            if value and value not in candidates:
                candidates.append(value)
        return candidates

    def _query_match_bonus(self, metadata: dict[str, Any] | None, query: str) -> tuple[float, list[str]]:
        query_norm = _normalize_lookup_text(query)
        query_terms = _extract_lookup_terms(query)
        if not query_norm and not query_terms:
            return 0.0, []

        metadata = dict(metadata or {})
        filename = str(metadata.get("filename") or "").strip()
        filename_stem = Path(filename).stem.strip() if filename else ""
        filename_norm = _normalize_lookup_text(filename_stem)
        title_candidates = self._metadata_title_candidates(metadata)
        title_norms = [_normalize_lookup_text(item) for item in title_candidates]

        bonus = 0.0
        signals: list[str] = []

        if query_norm and filename_norm and (query_norm in filename_norm or filename_norm in query_norm):
            bonus += FILENAME_MATCH_BOOST
            signals.append("filename")

        if query_norm:
            for title_norm in title_norms:
                if not title_norm or title_norm == filename_norm:
                    continue
                if query_norm in title_norm or title_norm in query_norm:
                    bonus += TITLE_MATCH_BOOST
                    signals.append("title")
                    break

        query_term_set = set(query_terms)
        metadata_terms = set(_extract_lookup_terms(" ".join(title_candidates)))
        overlap = len(query_term_set & metadata_terms)
        if overlap:
            bonus += min(3, overlap) * TERM_OVERLAP_BOOST
            signals.append(f"term_overlap:{overlap}")

        return bonus, signals

    def _query_with_metadata_matches(
        self,
        query: str,
        k: int = 5,
        *,
        source_scope: str | None = None,
    ) -> list[Document]:
        if source_scope:
            docs_pool = list(self.bm25_docs_by_scope.get(source_scope) or [])
            if not docs_pool:
                docs_pool = list(self.bm25_docs)
        else:
            docs_pool = list(self.bm25_docs)
        if not docs_pool:
            return []

        candidates: list[tuple[float, int, Document]] = []
        for doc in docs_pool:
            metadata = dict(doc.metadata or {})
            if source_scope and str(metadata.get("source_scope") or SOURCE_SCOPE_SUPPLEMENTAL) != source_scope:
                continue
            bonus, signals = self._query_match_bonus(metadata, query)
            if not signals:
                continue

            metadata["_query_match_signals"] = signals
            metadata["_query_match_bonus"] = float(abs(bonus))
            candidates.append(
                (
                    abs(bonus),
                    len(signals),
                    Document(page_content=doc.page_content, metadata=metadata),
                )
            )

        candidates.sort(key=lambda item: (-item[0], -item[1], len(item[2].page_content or "")))
        return [doc for _, _, doc in candidates[:k]]

    def _build_bm25_index(self) -> None:
        if not self.vector_stores:
            self.bm25 = None
            self.bm25_docs = []
            self.bm25_by_scope = {}
            self.bm25_docs_by_scope = {}
            return

        for spec in self.source_specs:
            source_scope = spec.scope
            store = self._vector_store_for_scope(source_scope)
            if store is None:
                self.bm25_docs_by_scope[source_scope] = []
                self.bm25_by_scope[source_scope] = None
                continue

            signature = self._bm25_signature(source_scope)
            if self._load_bm25_cache(signature, source_scope=source_scope):
                continue

            try:
                raw = store._collection.get(include=["documents", "metadatas"])
                docs = raw.get("documents", [])
                metas = raw.get("metadatas", [])

                scope_docs: list[Document] = []
                tokenized_corpus: list[list[str]] = []

                for doc_text, meta in zip(docs, metas):
                    if not doc_text:
                        continue

                    scope_docs.append(Document(page_content=doc_text, metadata=meta or {}))
                    tokenized_corpus.append(self._tokenize_for_bm25(doc_text))

                self.bm25_docs_by_scope[source_scope] = scope_docs
                self.bm25_by_scope[source_scope] = BM25Okapi(tokenized_corpus) if tokenized_corpus else None
                self._save_bm25_cache(signature, tokenized_corpus, source_scope=source_scope)
            except Exception as exc:
                self.bm25_by_scope[source_scope] = None
                self.bm25_docs_by_scope[source_scope] = []
                print(f"⚠️ [RAG] BM25 索引构建失败: {source_scope}: {exc}")

        self._refresh_bm25_views()

    def query_with_bm25(
        self,
        query: str,
        k: int = 5,
        *,
        source_scope: str | None = None,
    ) -> list[Document]:
        query_tokens = self._tokenize_for_bm25(query)
        if not query_tokens:
            return []

        ranked: list[tuple[Document, float]] = []
        scopes = [source_scope] if source_scope else [spec.scope for spec in self.source_specs]
        for scope in scopes:
            bm25 = self.bm25_by_scope.get(scope)
            docs = self.bm25_docs_by_scope.get(scope) or []
            if not bm25 or not docs:
                continue
            ranked.extend(zip(docs, bm25.get_scores(query_tokens)))
        ranked.sort(
            key=lambda item: (
                -item[1],
                self._source_priority(str((item[0].metadata or {}).get("source_scope") or SOURCE_SCOPE_SUPPLEMENTAL)),
                len(item[0].page_content or ""),
            )
        )

        results: list[Document] = []
        for doc, score in ranked:
            metadata = dict(doc.metadata or {})
            if source_scope and str(metadata.get("source_scope") or SOURCE_SCOPE_SUPPLEMENTAL) != source_scope:
                continue
            metadata["_bm25_score"] = float(score)
            results.append(Document(page_content=doc.page_content, metadata=metadata))
            if len(results) >= k:
                break

        return results

    def query_with_docs(
        self,
        query: str,
        k: int | None = None,
        *,
        source_scope: str | None = None,
    ) -> List[Document]:
        return [doc for doc, _ in self.query_with_scores(query, k=k, source_scope=source_scope)]

    def query_with_scores(
        self,
        query: str,
        k: int | None = None,
        *,
        source_scope: str | None = None,
    ):
        k = k or self.settings.knowledge_top_k
        fetch_k = max(k * 4, k)
        scopes = [source_scope] if source_scope else [spec.scope for spec in self.source_specs]
        docs_and_scores: list[tuple[Document, float]] = []
        for scope in scopes:
            store = self._vector_store_for_scope(scope)
            if store is None:
                continue
            try:
                scoped_results = store.similarity_search_with_score(query, k=fetch_k)
            except Exception:
                continue
            for doc, score in scoped_results:
                metadata = dict(doc.metadata or {})
                metadata.setdefault("source_scope", scope)
                docs_and_scores.append((Document(page_content=doc.page_content, metadata=metadata), float(score)))

        docs_and_scores.sort(
            key=lambda item: (
                item[1],
                self._source_priority(str((item[0].metadata or {}).get("source_scope") or SOURCE_SCOPE_SUPPLEMENTAL)),
                len(item[0].page_content or ""),
            )
        )
        return docs_and_scores[:k]

    def _collect_vector_hits(
        self,
        queries: list[str],
        *,
        k: int,
        source_scope: str | None = None,
    ) -> list[FamilyHit]:
        best: dict[tuple[str, Any, str], FamilyHit] = {}
        for query in _dedupe_texts(queries):
            try:
                docs_and_scores = self.query_with_scores(query, k=k, source_scope=source_scope)
            except TypeError:
                docs_and_scores = self.query_with_scores(query, k=k)
                if source_scope:
                    docs_and_scores = [
                        (doc, score)
                        for doc, score in docs_and_scores
                        if str((doc.metadata or {}).get("source_scope") or SOURCE_SCOPE_SUPPLEMENTAL) == source_scope
                    ]
            for rank, (doc, score) in enumerate(docs_and_scores, start=1):
                key = self._doc_key(doc)
                score_value = float(score)
                existing = best.get(key)
                if existing is None or rank < existing.rank or (
                    rank == existing.rank and score_value < float(existing.score if existing.score is not None else score_value)
                ):
                    best[key] = FamilyHit(doc=doc, rank=rank, score=score_value)

        hits = list(best.values())
        hits.sort(key=lambda item: (item.rank, float(item.score if item.score is not None else 0.0), len(item.doc.page_content or "")))
        return hits[:k]

    def _collect_bm25_hits(
        self,
        queries: list[str],
        *,
        k: int,
        source_scope: str | None = None,
    ) -> list[FamilyHit]:
        best: dict[tuple[str, Any, str], FamilyHit] = {}
        for query in _dedupe_texts(queries):
            try:
                docs = self.query_with_bm25(query, k=k, source_scope=source_scope)
            except TypeError:
                docs = self.query_with_bm25(query, k=k)
                if source_scope:
                    docs = [
                        doc
                        for doc in docs
                        if str((doc.metadata or {}).get("source_scope") or SOURCE_SCOPE_SUPPLEMENTAL) == source_scope
                    ]
            for rank, doc in enumerate(docs, start=1):
                key = self._doc_key(doc)
                score_value = float((doc.metadata or {}).get("_bm25_score") or 0.0)
                existing = best.get(key)
                if existing is None or rank < existing.rank or (
                    rank == existing.rank and score_value > float(existing.score if existing.score is not None else score_value)
                ):
                    best[key] = FamilyHit(doc=doc, rank=rank, score=score_value)

        hits = list(best.values())
        hits.sort(key=lambda item: (item.rank, -float(item.score if item.score is not None else 0.0), len(item.doc.page_content or "")))
        return hits[:k]

    def _collect_metadata_hits(
        self,
        queries: list[str],
        *,
        k: int,
        source_scope: str | None = None,
    ) -> list[FamilyHit]:
        best: dict[tuple[str, Any, str], FamilyHit] = {}
        for query in _dedupe_texts(queries):
            try:
                docs = self._query_with_metadata_matches(query, k=k, source_scope=source_scope)
            except TypeError:
                docs = self._query_with_metadata_matches(query, k=k)
                if source_scope:
                    docs = [
                        doc
                        for doc in docs
                        if str((doc.metadata or {}).get("source_scope") or SOURCE_SCOPE_SUPPLEMENTAL) == source_scope
                    ]
            for rank, doc in enumerate(docs, start=1):
                key = self._doc_key(doc)
                score_value = float((doc.metadata or {}).get("_query_match_bonus") or 0.0)
                existing = best.get(key)
                if existing is None or rank < existing.rank or (
                    rank == existing.rank and score_value > float(existing.score if existing.score is not None else score_value)
                ):
                    best[key] = FamilyHit(doc=doc, rank=rank, score=score_value)

        hits = list(best.values())
        hits.sort(key=lambda item: (item.rank, -float(item.score if item.score is not None else 0.0), len(item.doc.page_content or "")))
        return hits[:k]

    def _section_rerank(self, docs_and_scores, final_k: int | None = None, query: str | None = None) -> List[Document]:
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
            metadata = doc.metadata or {}
            section = str(metadata.get("section") or metadata.get("H1") or "").lower()
            content_head = (doc.page_content or "")[:300].lower()
            bonus = 0.0

            if any(keyword in section for keyword in good_keywords):
                bonus -= 0.12
            if any(keyword in section for keyword in bad_keywords):
                bonus += 0.35
            if "<table>" in content_head:
                bonus += 0.12
            if any(keyword in content_head for keyword in ["benchmark", "benchmarks", "dataset", "datasets"]):
                bonus -= 0.08
            if str(metadata.get("source_scope") or "") == SOURCE_SCOPE_COURSE_PRIMARY:
                bonus += COURSE_PRIMARY_SOURCE_BOOST

            query_bonus, query_signals = self._query_match_bonus(metadata, query or "")
            if query_bonus:
                bonus += query_bonus
            if query_signals:
                merged_signals = list(dict.fromkeys(list(metadata.get("_query_match_signals", [])) + query_signals))
                metadata["_query_match_signals"] = merged_signals
                metadata["_query_match_bonus"] = max(float(metadata.get("_query_match_bonus", 0.0)), float(abs(query_bonus)))

            reranked.append(
                ScoredChunk(
                    doc=Document(page_content=doc.page_content, metadata=metadata),
                    score=score,
                    adjusted_score=score + bonus,
                    metadata=metadata,
                )
            )

        reranked.sort(key=lambda item: item.adjusted_score)
        final_k = final_k or self.settings.knowledge_top_k
        return [item.doc for item in reranked[:final_k]]

    def _fuse_with_rrf(
        self,
        vector_hits: list[FamilyHit],
        bm25_hits: list[FamilyHit],
        metadata_hits: list[FamilyHit] | None = None,
    ) -> list[tuple[Document, float]]:
        merged: list[tuple[Document, float]] = []
        score_map: dict[tuple[str, Any, str], dict[str, Any]] = {}

        for hit in vector_hits:
            key = self._doc_key(hit.doc)
            entry = score_map.setdefault(
                key,
                {
                    "doc": hit.doc,
                    "vector_rank": None,
                    "bm25_rank": None,
                    "metadata_rank": None,
                    "vector_score": None,
                    "bm25_score": None,
                    "query_match_signals": [],
                    "query_match_bonus": 0.0,
                },
            )
            if entry["vector_rank"] is None or int(hit.rank) < int(entry["vector_rank"]):
                entry["vector_rank"] = int(hit.rank)
                entry["vector_score"] = float(hit.score if hit.score is not None else 0.0)

        for hit in bm25_hits:
            key = self._doc_key(hit.doc)
            entry = score_map.setdefault(
                key,
                {
                    "doc": hit.doc,
                    "vector_rank": None,
                    "bm25_rank": None,
                    "metadata_rank": None,
                    "vector_score": None,
                    "bm25_score": None,
                    "query_match_signals": [],
                    "query_match_bonus": 0.0,
                },
            )
            if entry["bm25_rank"] is None or int(hit.rank) < int(entry["bm25_rank"]):
                entry["bm25_rank"] = int(hit.rank)
                entry["bm25_score"] = float(hit.score if hit.score is not None else 0.0)

        for hit in metadata_hits or []:
            key = self._doc_key(hit.doc)
            entry = score_map.setdefault(
                key,
                {
                    "doc": hit.doc,
                    "vector_rank": None,
                    "bm25_rank": None,
                    "metadata_rank": None,
                    "vector_score": None,
                    "bm25_score": None,
                    "query_match_signals": [],
                    "query_match_bonus": 0.0,
                },
            )
            if entry["metadata_rank"] is None or int(hit.rank) < int(entry["metadata_rank"]):
                entry["doc"] = hit.doc
                entry["metadata_rank"] = int(hit.rank)
                entry["query_match_bonus"] = float(hit.score if hit.score is not None else 0.0)
            entry["query_match_signals"] = list(
                dict.fromkeys(entry["query_match_signals"] + list(hit.doc.metadata.get("_query_match_signals", [])))
            )
            entry["query_match_bonus"] = max(
                float(entry["query_match_bonus"] or 0.0),
                float(hit.doc.metadata.get("_query_match_bonus", 0.0)),
            )

        for entry in score_map.values():
            vector_rank = entry["vector_rank"]
            bm25_rank = entry["bm25_rank"]
            metadata_rank = entry["metadata_rank"]

            rrf_score = 0.0
            if vector_rank is not None:
                rrf_score += 1.0 / (RRF_K + int(vector_rank))
            if bm25_rank is not None:
                rrf_score += 1.0 / (RRF_K + int(bm25_rank))
            if metadata_rank is not None:
                rrf_score += 1.0 / (RRF_K + int(metadata_rank))

            metadata = dict((entry["doc"].metadata or {}))
            retrieval_sources: list[str] = []
            if vector_rank is not None:
                metadata["_vector_rank"] = int(vector_rank)
                metadata["_vector_score"] = entry["vector_score"]
                retrieval_sources.append("vector")
            if bm25_rank is not None:
                metadata["_bm25_rank"] = int(bm25_rank)
                if entry["bm25_score"] is not None:
                    metadata["_bm25_score"] = entry["bm25_score"]
                retrieval_sources.append("bm25")
            if metadata_rank is not None:
                metadata["_metadata_rank"] = int(metadata_rank)
                retrieval_sources.append("metadata")
            if entry["query_match_signals"]:
                metadata["_query_match_signals"] = entry["query_match_signals"]
            if entry["query_match_bonus"]:
                metadata["_query_match_bonus"] = float(entry["query_match_bonus"])

            metadata["_retrieval_sources"] = retrieval_sources
            metadata["_rrf_score"] = float(rrf_score)

            merged_doc = Document(
                page_content=entry["doc"].page_content,
                metadata=metadata,
            )
            # _section_rerank 默认按 score + bonus 从小到大排序，故这里取负值。
            merged.append((merged_doc, -RRF_SCALE * rrf_score))

        return merged

    def _query_scope_hybrid(
        self,
        query: str,
        *,
        source_scope: str,
        recall_k: int,
        final_k: int,
        vector_queries: list[str] | None = None,
        bm25_queries: list[str] | None = None,
        metadata_terms: list[str] | None = None,
    ) -> list[Document]:
        lane_recall_k = max(recall_k, max(1, final_k) * 2)
        vector_hits = self._collect_vector_hits(
            [query] + list(vector_queries or []),
            k=lane_recall_k,
            source_scope=source_scope,
        )
        bm25_hits = self._collect_bm25_hits(
            [query] + list(bm25_queries or []),
            k=lane_recall_k,
            source_scope=source_scope,
        )
        metadata_hits = self._collect_metadata_hits(
            [query] + list(metadata_terms or []),
            k=lane_recall_k,
            source_scope=source_scope,
        )
        merged = self._fuse_with_rrf(vector_hits, bm25_hits, metadata_hits=metadata_hits)
        if not merged:
            return []
        return self._section_rerank(merged, final_k=lane_recall_k, query=query)[:final_k]

    def _dedupe_docs(self, docs: list[Document]) -> list[Document]:
        deduped: list[Document] = []
        seen: set[tuple[str, str, Any, str]] = set()
        for doc in docs:
            key = self._doc_key(doc)
            if key in seen:
                continue
            seen.add(key)
            deduped.append(doc)
        return deduped

    def _resolve_graph_node(self, *candidates: str) -> dict[str, Any] | None:
        cleaned_candidates = [str(item or "").strip() for item in candidates if str(item or "").strip()]
        if not cleaned_candidates or not self.course_graph_nodes:
            return None

        for candidate in cleaned_candidates:
            normalized = _normalize_lookup_text(candidate)
            title = self.course_graph_lookup.get(normalized)
            if title and title in self.course_graph_nodes:
                return dict(self.course_graph_nodes[title])

        best_score = 0
        best_title = ""
        for candidate in cleaned_candidates:
            normalized_candidate = _normalize_lookup_text(candidate)
            candidate_terms = set(_extract_lookup_terms(candidate))
            if not normalized_candidate and not candidate_terms:
                continue
            for title, node in self.course_graph_nodes.items():
                node_title_norm = _normalize_lookup_text(title)
                node_file_norm = _normalize_lookup_text(Path(str(node.get("filename") or "")).stem)
                score = 0
                if normalized_candidate and node_title_norm and (
                    normalized_candidate in node_title_norm or node_title_norm in normalized_candidate
                ):
                    score += 6
                if normalized_candidate and node_file_norm and (
                    normalized_candidate in node_file_norm or node_file_norm in normalized_candidate
                ):
                    score += 4
                node_terms = set(_extract_lookup_terms(" ".join([title, str(node.get("filename") or "")])))
                score += 2 * len(candidate_terms & node_terms)
                if score > best_score:
                    best_score = score
                    best_title = title

        if best_title and best_score >= 2:
            return dict(self.course_graph_nodes[best_title])
        return None

    def _graph_next_steps_from_node(self, node: dict[str, Any] | None) -> list[dict[str, str]]:
        if not node:
            return []

        current_title = str(node.get("title") or "").strip()
        current_id = str(node.get("id") or current_title).strip()
        prerequisites = [item for item in self._normalize_graph_list(node.get("prerequisites")) if item != current_title]
        neighbors = [item for item in self._normalize_graph_list(node.get("neighbors")) if item != current_title]

        steps: list[dict[str, str]] = []
        if prerequisites:
            prereq_title = prerequisites[0]
            prereq_node = self._resolve_graph_node(prereq_title) or {}
            steps.append(
                {
                    "choice": "review_prerequisite",
                    "label": f"先补前置：{prereq_title}",
                    "target": prereq_title,
                    "target_id": str(prereq_node.get("id") or prereq_title).strip(),
                    "relation": "prerequisite",
                }
            )
        if current_title:
            steps.append(
                {
                    "choice": "continue_current",
                    "label": f"继续当前：{current_title}",
                    "target": current_title,
                    "target_id": current_id,
                    "relation": "current",
                }
            )
        if neighbors:
            neighbor_title = neighbors[0]
            neighbor_node = self._resolve_graph_node(neighbor_title) or {}
            steps.append(
                {
                    "choice": "branch_related",
                    "label": f"转到相关：{neighbor_title}",
                    "target": neighbor_title,
                    "target_id": str(neighbor_node.get("id") or neighbor_title).strip(),
                    "relation": "neighbor",
                }
            )
        if current_title:
            steps.append(
                {
                    "choice": "practice_now",
                    "label": f"围绕{current_title}来一道题",
                    "target": current_title,
                    "target_id": current_id,
                    "relation": "practice",
                }
            )
        steps.append(
            {
                "choice": "summarize_now",
                "label": "先收束当前点",
                "target": current_title,
                "target_id": current_id,
                "relation": "summary",
            }
        )
        return steps

    def _build_graph_context(
        self,
        *,
        query: str,
        rewrite_request: RetrievalRewriteRequest | None = None,
        docs: list[Document] | None = None,
    ) -> dict[str, Any]:
        anchor = self._resolve_graph_node(
            str(getattr(rewrite_request, "current_topic", "") or ""),
            str(getattr(rewrite_request, "raw_query", "") or ""),
            query,
        )
        if anchor is None and docs:
            for doc in docs:
                metadata = dict(doc.metadata or {})
                if str(metadata.get("source_scope") or "") != SOURCE_SCOPE_COURSE_PRIMARY:
                    continue
                anchor = self._resolve_graph_node(str(metadata.get("kg_title") or metadata.get("filename") or ""))
                if anchor:
                    break

        if not anchor:
            return {}

        return {
            "anchor": anchor,
            "anchor_id": str(anchor.get("id") or anchor.get("title") or "").strip(),
            "anchor_title": str(anchor.get("title") or "").strip(),
            "anchor_filename": str(anchor.get("filename") or "").strip(),
            "prerequisites": self._normalize_graph_list(anchor.get("prerequisites")),
            "neighbors": self._normalize_graph_list(anchor.get("neighbors")),
            "learning_objectives": self._normalize_graph_list(anchor.get("learning_objectives")),
            "must_know": self._normalize_graph_list(anchor.get("must_know")),
            "common_errors": self._normalize_graph_list(anchor.get("common_errors")),
            "target_mastery_level": str(anchor.get("target_mastery_level") or "").strip(),
            "difficulty": str(anchor.get("difficulty") or "").strip(),
            "next_steps": self._graph_next_steps_from_node(anchor),
        }

    def resolve_graph_context(self, query: str) -> dict[str, Any]:
        """Resolve one explicit graph anchor into the normalized graph-context contract."""
        text = str(query or "").strip()
        if not text:
            return {}
        rewrite_request = RetrievalRewriteRequest(
            channel="graph_context",
            raw_query=text,
            current_topic=text,
        )
        return self._build_graph_context(query=text, rewrite_request=rewrite_request)

    def _query_graph_priority(
        self,
        query: str,
        *,
        final_k: int,
        rewrite_request: RetrievalRewriteRequest | None = None,
    ) -> tuple[list[Document], dict[str, Any], dict[str, Any]]:
        graph_context = self._build_graph_context(query=query, rewrite_request=rewrite_request)
        if not graph_context:
            return [], {}, {"graph_priority": False}

        anchor_title = str(graph_context.get("anchor_title") or "").strip()
        related_queries = [
            *list(graph_context.get("prerequisites") or [])[:2],
            *list(graph_context.get("neighbors") or [])[:2],
        ]
        quotas = dict(self._source_scope_quotas(final_k))
        course_quota = int(quotas.get(SOURCE_SCOPE_COURSE_PRIMARY, 0))
        supplemental_quota = int(quotas.get(SOURCE_SCOPE_SUPPLEMENTAL, 0))

        current_docs = self._query_scope_hybrid(
            anchor_title or query,
            source_scope=SOURCE_SCOPE_COURSE_PRIMARY,
            recall_k=8,
            final_k=max(1, min(course_quota or final_k, 2)),
            vector_queries=[query],
            bm25_queries=[str(getattr(rewrite_request, "raw_query", "") or query)],
            metadata_terms=[anchor_title, Path(str(graph_context.get("anchor_filename") or "")).stem],
        )
        related_docs: list[Document] = []
        remaining_quota = max(0, course_quota - len(current_docs))
        for related in related_queries:
            if remaining_quota <= 0:
                break
            related_docs.extend(
                self._query_scope_hybrid(
                    related,
                    source_scope=SOURCE_SCOPE_COURSE_PRIMARY,
                    recall_k=4,
                    final_k=1,
                    metadata_terms=[related],
                )
            )
            remaining_quota -= 1

        supplemental_docs: list[Document] = []
        if supplemental_quota > 0:
            supplemental_docs = self._query_scope_hybrid(
                query,
                source_scope=SOURCE_SCOPE_SUPPLEMENTAL,
                recall_k=8,
                final_k=max(1, supplemental_quota),
            )

        docs = self._merge_source_lane_docs(
            {
                SOURCE_SCOPE_COURSE_PRIMARY: self._dedupe_docs(current_docs + related_docs),
                SOURCE_SCOPE_SUPPLEMENTAL: self._dedupe_docs(supplemental_docs),
            },
            final_k=final_k,
        )
        return docs, graph_context, {
            "graph_priority": True,
            "graph_anchor": anchor_title,
            "graph_related_queries": related_queries,
        }

    def _source_scope_quotas(self, final_k: int) -> list[tuple[str, int]]:
        active_scopes = [spec.scope for spec in self.source_specs if spec.path.exists()]
        if SOURCE_SCOPE_COURSE_PRIMARY not in active_scopes:
            return [(SOURCE_SCOPE_SUPPLEMENTAL, final_k)]

        quotas: list[tuple[str, int]] = []
        course_quota = min(final_k, max(COURSE_PRIMARY_MIN_RESULTS, final_k - SUPPLEMENTAL_MIN_RESULTS))
        supplemental_quota = max(0, final_k - course_quota)

        if course_quota > 0:
            quotas.append((SOURCE_SCOPE_COURSE_PRIMARY, course_quota))
        if supplemental_quota > 0:
            quotas.append((SOURCE_SCOPE_SUPPLEMENTAL, supplemental_quota))
        return quotas

    def _merge_source_lane_docs(
        self,
        docs_by_scope: dict[str, list[Document]],
        *,
        final_k: int,
    ) -> list[Document]:
        merged: list[Document] = []
        seen: set[tuple[str, str, Any, str]] = set()

        for source_scope, quota in self._source_scope_quotas(final_k):
            lane_docs = docs_by_scope.get(source_scope, [])
            taken = 0
            for doc in lane_docs:
                key = self._doc_key(doc)
                if key in seen:
                    continue
                seen.add(key)
                merged.append(doc)
                taken += 1
                if taken >= quota:
                    break

        overflow: list[Document] = []
        for source_scope in [spec.scope for spec in self.source_specs]:
            for doc in docs_by_scope.get(source_scope, []):
                key = self._doc_key(doc)
                if key in seen:
                    continue
                overflow.append(doc)
                seen.add(key)

        if len(merged) < final_k:
            merged.extend(overflow[: max(0, final_k - len(merged))])
        return merged[:final_k]

    def _query_hybrid_once(
        self,
        query: str,
        *,
        recall_k: int,
        final_k: int,
        vector_queries: list[str] | None = None,
        bm25_queries: list[str] | None = None,
        metadata_terms: list[str] | None = None,
    ) -> list[Document]:
        docs_by_scope: dict[str, list[Document]] = {}
        for source_scope, lane_quota in self._source_scope_quotas(final_k):
            docs_by_scope[source_scope] = self._query_scope_hybrid(
                query,
                source_scope=source_scope,
                recall_k=recall_k,
                final_k=max(1, lane_quota * 2),
                vector_queries=vector_queries,
                bm25_queries=bm25_queries,
                metadata_terms=metadata_terms,
            )

        return self._merge_source_lane_docs(docs_by_scope, final_k=final_k)

    def _build_trace(
        self,
        *,
        gate_outcome: str,
        gate_reason: str,
        raw_query: str,
        planner_intent: str | None = None,
        vector_queries: list[str] | None = None,
        bm25_queries: list[str] | None = None,
        metadata_terms: list[str] | None = None,
        must_keep: list[str] | None = None,
        must_keep_repaired: bool = False,
        raw_confidence: dict[str, Any] | None = None,
        rewritten_confidence: dict[str, Any] | None = None,
        planner_reason: str = "",
        planner_error: str = "",
    ) -> RetrievalRewriteTrace:
        return RetrievalRewriteTrace(
            gate_outcome=gate_outcome,
            gate_reason=gate_reason,
            planner_intent=planner_intent,
            raw_query=raw_query,
            rewritten_vector_queries=list(vector_queries or []),
            rewritten_bm25_queries=list(bm25_queries or []),
            metadata_terms=list(metadata_terms or []),
            must_keep=list(must_keep or []),
            must_keep_repaired=must_keep_repaired,
            raw_confidence=dict(raw_confidence or {}),
            rewritten_confidence=dict(rewritten_confidence or {}),
            planner_reason=planner_reason,
            planner_error=planner_error,
        )

    def _run_rewrite_decision(
        self,
        query: str,
        *,
        raw_docs: list[Document],
        recall_k: int,
        final_k: int,
        rewrite_request: RetrievalRewriteRequest,
    ) -> tuple[list[Document], RetrievalRewriteTrace]:
        raw_query = self._raw_query_for_rewrite(query, rewrite_request)
        should_skip, skip_reason, raw_confidence = self._should_skip_rewrite_for_raw_confidence(raw_query, raw_docs)
        force_goal_rewrite = self._should_force_goal_rewrite(raw_query, raw_confidence)
        if should_skip:
            return raw_docs, self._build_trace(
                gate_outcome="bypass",
                gate_reason=skip_reason,
                raw_query=raw_query,
                raw_confidence=raw_confidence,
            )

        plan, planner_error = self._invoke_retrieval_planner(query, rewrite_request)
        if plan is None:
            return raw_docs, self._build_trace(
                gate_outcome="rewrite_failed_fallback",
                gate_reason="planner failed; fallback to raw retrieval",
                raw_query=raw_query,
                raw_confidence=raw_confidence,
                planner_error=planner_error,
            )

        plan, must_keep_repaired = self._repair_rewrite_plan(plan)
        if not plan.rewrite_needed and force_goal_rewrite:
            heuristic_plan = self._build_heuristic_rewrite_plan(query, rewrite_request, intent_hint=plan.intent)
            heuristic_plan, heuristic_repaired = self._repair_rewrite_plan(heuristic_plan)
            must_keep_repaired = must_keep_repaired or heuristic_repaired
            planner_reason = f"{plan.reason} | heuristic goal rewrite fallback applied".strip(" |")
            plan = heuristic_plan
        else:
            planner_reason = plan.reason

        if not plan.rewrite_needed:
            return raw_docs, self._build_trace(
                gate_outcome="raw_only",
                gate_reason="planner decided rewrite is unnecessary",
                raw_query=raw_query,
                planner_intent=plan.intent,
                must_keep=plan.must_keep,
                must_keep_repaired=must_keep_repaired,
                raw_confidence=raw_confidence,
                planner_reason=planner_reason,
            )

        if not (plan.vector_queries or plan.bm25_queries or plan.metadata_terms):
            return raw_docs, self._build_trace(
                gate_outcome="rewrite_failed_fallback",
                gate_reason="planner produced no usable rewritten queries",
                raw_query=raw_query,
                planner_intent=plan.intent,
                must_keep=plan.must_keep,
                must_keep_repaired=must_keep_repaired,
                raw_confidence=raw_confidence,
                planner_reason=planner_reason,
                planner_error=planner_error,
            )

        rewrite_docs = self._query_hybrid_once(
            query,
            recall_k=recall_k,
            final_k=final_k,
            vector_queries=plan.vector_queries,
            bm25_queries=plan.bm25_queries,
            metadata_terms=plan.metadata_terms,
        )
        rewritten_confidence = self._build_confidence_summary(rewrite_docs, query=raw_query)
        goal_alignment_not_improved = force_goal_rewrite and (
            self._goal_alignment_rank_tuple(rewritten_confidence) <= self._goal_alignment_rank_tuple(raw_confidence)
        )
        if not rewrite_docs or self._confidence_rank_tuple(rewritten_confidence) < self._confidence_rank_tuple(raw_confidence):
            return raw_docs, self._build_trace(
                gate_outcome="rewrite_failed_fallback",
                gate_reason="rewritten retrieval was empty or weaker than raw retrieval",
                raw_query=raw_query,
                planner_intent=plan.intent,
                vector_queries=plan.vector_queries,
                bm25_queries=plan.bm25_queries,
                metadata_terms=plan.metadata_terms,
                must_keep=plan.must_keep,
                must_keep_repaired=must_keep_repaired,
                raw_confidence=raw_confidence,
                rewritten_confidence=rewritten_confidence,
                planner_reason=planner_reason,
                planner_error=planner_error,
            )
        if goal_alignment_not_improved:
            return raw_docs, self._build_trace(
                gate_outcome="rewrite_failed_fallback",
                gate_reason="rewritten retrieval did not improve goal-term alignment",
                raw_query=raw_query,
                planner_intent=plan.intent,
                vector_queries=plan.vector_queries,
                bm25_queries=plan.bm25_queries,
                metadata_terms=plan.metadata_terms,
                must_keep=plan.must_keep,
                must_keep_repaired=must_keep_repaired,
                raw_confidence=raw_confidence,
                rewritten_confidence=rewritten_confidence,
                planner_reason=planner_reason,
                planner_error=planner_error,
            )

        return rewrite_docs, self._build_trace(
            gate_outcome="rewrite_used",
            gate_reason="rewritten retrieval improved or matched raw confidence",
            raw_query=raw_query,
            planner_intent=plan.intent,
            vector_queries=plan.vector_queries,
            bm25_queries=plan.bm25_queries,
            metadata_terms=plan.metadata_terms,
            must_keep=plan.must_keep,
            must_keep_repaired=must_keep_repaired,
            raw_confidence=raw_confidence,
            rewritten_confidence=rewritten_confidence,
            planner_reason=planner_reason,
            planner_error=planner_error,
        )

    def query_hybrid(
        self,
        query: str,
        recall_k: int = 8,
        final_k: int | None = None,
        *,
        rewrite_request: RetrievalRewriteRequest | None = None,
        include_debug: bool = False,
    ):
        final_k = final_k or self.settings.knowledge_top_k
        raw_docs = self._query_hybrid_once(query, recall_k=recall_k, final_k=final_k)
        raw_query = self._raw_query_for_rewrite(query, rewrite_request)

        if not self.settings.retrieval_rewrite_enabled:
            trace = self._build_trace(
                gate_outcome="raw_only",
                gate_reason="retrieval rewrite feature is disabled",
                raw_query=raw_query,
                raw_confidence=self._build_confidence_summary(raw_docs, query=raw_query),
            )
            self.last_rewrite_trace = trace.to_dict()
            return {"docs": raw_docs, "debug": trace.to_dict()} if include_debug else raw_docs

        if rewrite_request is None:
            trace = self._build_trace(
                gate_outcome="raw_only",
                gate_reason="no rewrite request provided",
                raw_query=raw_query,
                raw_confidence=self._build_confidence_summary(raw_docs, query=raw_query),
            )
            self.last_rewrite_trace = trace.to_dict()
            return {"docs": raw_docs, "debug": trace.to_dict()} if include_debug else raw_docs

        if self.settings.retrieval_rewrite_mode != "smart":
            trace = self._build_trace(
                gate_outcome="raw_only",
                gate_reason=f"unsupported rewrite mode: {self.settings.retrieval_rewrite_mode}",
                raw_query=raw_query,
                raw_confidence=self._build_confidence_summary(raw_docs, query=raw_query),
            )
            self.last_rewrite_trace = trace.to_dict()
            return {"docs": raw_docs, "debug": trace.to_dict()} if include_debug else raw_docs

        if self._looks_like_exact_lookup(raw_query):
            trace = self._build_trace(
                gate_outcome="bypass",
                gate_reason="query looks like an exact filename/code/term lookup",
                raw_query=raw_query,
                raw_confidence=self._build_confidence_summary(raw_docs, query=raw_query),
            )
            self.last_rewrite_trace = trace.to_dict()
            return {"docs": raw_docs, "debug": trace.to_dict()} if include_debug else raw_docs

        final_docs, trace = self._run_rewrite_decision(
            query,
            raw_docs=raw_docs,
            recall_k=recall_k,
            final_k=final_k,
            rewrite_request=rewrite_request,
        )
        self.last_rewrite_trace = trace.to_dict()
        return {"docs": final_docs, "debug": trace.to_dict()} if include_debug else final_docs

    def query_reranked(self, query: str, recall_k: int = 8, final_k: int | None = None) -> List[Document]:
        docs_and_scores = self.query_with_scores(query, k=recall_k)
        if not docs_and_scores:
            return []
        return self._section_rerank(docs_and_scores, final_k=final_k, query=query)

    def _trim_snippet(self, text: str, *, max_chars: int = 260) -> str:
        normalized = re.sub(r"\s+", " ", str(text or "")).strip()
        if len(normalized) <= max_chars:
            return normalized
        return f"{normalized[: max_chars - 3]}..."

    def _format_local_label(self, metadata: dict[str, Any]) -> str:
        scope = str(metadata.get("source_scope") or SOURCE_SCOPE_SUPPLEMENTAL)
        filename = str(metadata.get("filename") or "未命名资料").strip()
        page = metadata.get("page")
        section = str(
            metadata.get("section")
            or metadata.get("H3")
            or metadata.get("H2")
            or metadata.get("H1")
            or ""
        ).strip()
        parts = [filename]
        if isinstance(page, int):
            parts.append(f"第 {page} 页")
        if section and not re.fullmatch(r"page-\d+", section.lower()):
            parts.append(section)
        prefix = "课程图谱" if scope == SOURCE_SCOPE_COURSE_PRIMARY else "上传资料"
        return f"[{prefix}] " + " · ".join(parts)

    def _format_web_label(self, result: WebSearchResult) -> str:
        parts = [result.title or result.domain or result.url]
        if result.domain:
            parts.append(result.domain)
        return " · ".join(parts)

    def _build_local_evidence_items(self, docs: list[Document], *, query: str) -> list[EvidenceItem]:
        query_terms = self._extract_goal_terms(query)
        items: list[EvidenceItem] = []
        for doc in docs:
            metadata = dict(doc.metadata or {})
            source_scope = str(metadata.get("source_scope") or SOURCE_SCOPE_SUPPLEMENTAL)
            term_hits, term_ratio, _ = self._doc_query_term_alignment(doc, query_terms)
            signals = list(metadata.get("_query_match_signals", []))
            retrieval_sources = list(metadata.get("_retrieval_sources", []))
            pure_title_match = bool(signals) and set(signals).issubset({"filename", "title"}) and term_hits == 0
            can_cite = bool(self._trim_snippet(doc.page_content)) and not pure_title_match and (
                not query_terms or term_hits > 0 or any(source in {"vector", "bm25"} for source in retrieval_sources)
            )
            items.append(
                EvidenceItem(
                    source_type="local_kb",
                    source_id=f"{source_scope}::{metadata.get('filename','')}::{metadata.get('chunk_id','')}",
                    display_label=self._format_local_label(metadata),
                    snippet=self._trim_snippet(doc.page_content),
                    goal_alignment=float(term_ratio if query_terms else 1.0),
                    can_cite=can_cite,
                    rank_score=float(metadata.get("_rrf_score") or 0.0),
                    filename=str(metadata.get("filename") or "").strip(),
                    page=metadata.get("page") if isinstance(metadata.get("page"), int) else None,
                    section=str(metadata.get("section") or metadata.get("H3") or metadata.get("H2") or metadata.get("H1") or "").strip(),
                    chunk_index=metadata.get("chunk_id") if isinstance(metadata.get("chunk_id"), int) else None,
                    source_scope=source_scope,
                    retrieval_sources=retrieval_sources,
                )
            )
        return items

    def _build_web_evidence_items(self, results: list[WebSearchResult], *, query: str) -> list[EvidenceItem]:
        query_terms = self._extract_goal_terms(query)
        items: list[EvidenceItem] = []
        for index, result in enumerate(results, start=1):
            combined = " ".join([result.title, result.snippet, result.domain])
            doc = Document(page_content=combined, metadata={})
            term_hits, term_ratio, _ = self._doc_query_term_alignment(doc, query_terms)
            can_cite = bool(result.snippet) and (not query_terms or term_hits > 0 or term_ratio >= 0.5)
            items.append(
                EvidenceItem(
                    source_type="web_search",
                    source_id=result.url or f"web::{index}",
                    display_label=self._format_web_label(result),
                    snippet=self._trim_snippet(result.snippet),
                    goal_alignment=float(term_ratio if query_terms else 1.0),
                    can_cite=can_cite,
                    rank_score=float(result.score or 0.0),
                    url=result.url,
                    domain=result.domain,
                    title=result.title,
                    published_date=result.published_date,
                )
            )
        return items

    def _select_web_search_query(self, query: str, debug_payload: dict[str, Any] | None) -> str:
        candidates = [str(query or "").strip()]
        if isinstance(debug_payload, dict):
            candidates.extend(debug_payload.get("rewritten_vector_queries", []) or [])
            candidates.extend(debug_payload.get("rewritten_bm25_queries", []) or [])
        deduped = _dedupe_texts(candidates)
        return deduped[0] if deduped else str(query or "").strip()

    def _search_web_evidence(self, query: str, *, debug_payload: dict[str, Any] | None = None) -> list[EvidenceItem]:
        if self.web_search_client is None:
            return []
        search_query = self._select_web_search_query(query, debug_payload)
        try:
            results = self.web_search_client.search(search_query, max_results=self.settings.web_search_max_results)
        except Exception as exc:
            print(f"⚠️ [RAG] Tavily 外部搜索失败，已忽略本次外部补充: {exc}")
            return []
        return self._build_web_evidence_items(results, query=query)

    def _build_context_from_evidence(self, evidence_items: list[EvidenceItem]) -> str:
        blocks: list[str] = []
        for index, item in enumerate(evidence_items, start=1):
            label = item.display_label
            if item.source_type == "web_search" and item.url:
                label = f"{label} ({item.url})"
            blocks.append(f"[证据{index}] {label}\n{item.snippet}")
        return "\n\n".join(blocks)

    def _build_graph_guidance(self, docs: list[Document], *, graph_context: dict[str, Any] | None = None) -> str:
        lines: list[str] = []
        if graph_context:
            anchor_title = str(graph_context.get("anchor_title") or "").strip()
            prerequisites = "；".join(graph_context.get("prerequisites") or [])
            must_know = "；".join(graph_context.get("must_know") or [])
            objectives = "；".join(graph_context.get("learning_objectives") or [])
            mastery = str(graph_context.get("target_mastery_level") or "").strip()
            difficulty = str(graph_context.get("difficulty") or "").strip()
            entry = [f"- 节点：{anchor_title}"]
            if prerequisites:
                entry.append(f"前置：{prerequisites}")
            if must_know:
                entry.append(f"核心抓手：{must_know}")
            if objectives:
                entry.append(f"目标：{objectives}")
            descriptor = " / ".join([item for item in [mastery, difficulty] if item])
            if descriptor:
                entry.append(f"建议层级：{descriptor}")
            if len(entry) > 1:
                lines.append("；".join(entry))

        seen_files: set[str] = set()
        for doc in docs:
            metadata = dict(doc.metadata or {})
            if str(metadata.get("source_scope") or "") != SOURCE_SCOPE_COURSE_PRIMARY:
                continue
            filename = str(metadata.get("filename") or "").strip()
            if not filename or filename in seen_files:
                continue
            seen_files.add(filename)

            title = str(metadata.get("kg_title") or Path(filename).stem).strip()
            must_know = str(metadata.get("kg_must_know") or "").strip()
            prerequisites = str(metadata.get("kg_prerequisites") or "").strip()
            objectives = str(metadata.get("kg_learning_objectives") or "").strip()
            mastery = str(metadata.get("kg_target_mastery_level") or "").strip()
            difficulty = str(metadata.get("kg_difficulty") or "").strip()

            entry = [f"- 节点：{title}"]
            if prerequisites:
                entry.append(f"前置：{prerequisites}")
            if must_know:
                entry.append(f"核心抓手：{must_know}")
            if objectives:
                entry.append(f"目标：{objectives}")
            descriptor = " / ".join([item for item in [mastery, difficulty] if item])
            if descriptor:
                entry.append(f"建议层级：{descriptor}")
            line = "；".join(entry)
            if line not in lines:
                lines.append(line)
            if len(lines) >= 2:
                break

        return "\n".join(lines)

    def _build_follow_up_question(self, query: str, confidence: dict[str, Any]) -> str:
        matched_terms = list(confidence.get("best_query_terms_matched") or [])
        missing_terms = list(confidence.get("best_query_terms_missing") or [])
        if matched_terms and missing_terms:
            return (
                f"我现在只定位到和「{'」「'.join(matched_terms)}」相关的资料，还没有准确定位到「{'」「'.join(missing_terms)}」。"
                "你能再补一句你最想解决的具体问题吗？比如想看某一步操作、某个概念，还是某种报错原因。"
            )
        return (
            f"我还没有在当前资料里定位到能直接支撑“{query}”的证据片段。"
            "你可以把问题再收紧一点，例如说明具体步骤、概念、例题，或者报错现象。"
        )

    def _select_confident_citation_docs(self, docs: list[Document], *, query: str = "") -> list[Document]:
        if not docs:
            return []

        grouped: dict[tuple[str, str], dict[str, Any]] = {}
        total_weight = 0.0
        for rank, doc in enumerate(docs, start=1):
            metadata = dict(doc.metadata or {})
            filename = str(metadata.get("filename") or "").strip()
            source_scope = str(metadata.get("source_scope") or SOURCE_SCOPE_SUPPLEMENTAL)
            if not filename:
                continue
            weight = float(metadata.get("_rrf_score") or (1.0 / (RRF_K + rank)))
            total_weight += weight
            bucket = grouped.setdefault(
                (source_scope, filename),
                {
                    "docs": [],
                    "weight": 0.0,
                    "top3_count": 0,
                    "multi_source": False,
                    "strong_match": False,
                    "best_rrf": 0.0,
                },
            )
            bucket["docs"].append(doc)
            bucket["weight"] += weight
            bucket["best_rrf"] = max(bucket["best_rrf"], float(metadata.get("_rrf_score") or 0.0))
            bucket["multi_source"] = bucket["multi_source"] or len(set(metadata.get("_retrieval_sources", []))) >= 2
            signals = list(metadata.get("_query_match_signals", []))
            bucket["strong_match"] = bucket["strong_match"] or any(signal in {"filename", "title"} for signal in signals)
            if rank <= 3:
                bucket["top3_count"] += 1

        if not grouped or total_weight <= 0:
            return []

        _, top_bucket = max(grouped.items(), key=lambda item: item[1]["weight"])
        dominance = float(top_bucket["weight"]) / total_weight if total_weight else 0.0
        confidence = self._build_confidence_summary(docs, query=query)
        goal_intent = self._query_expresses_goal_intent(query)
        goal_alignment_strong = (
            int(confidence.get("query_term_count") or 0) == 0
            or int(confidence.get("best_query_term_hits") or 0) >= min(2, int(confidence.get("query_term_count") or 0))
            or float(confidence.get("best_query_term_ratio") or 0.0) >= 0.6
        )
        confident = bool(top_bucket["strong_match"]) or (
            dominance >= CONFIDENT_CITATION_MIN_DOMINANCE
            and float(top_bucket["best_rrf"]) >= CONFIDENT_CITATION_MIN_RRF
            and (int(top_bucket["top3_count"]) >= 2 or bool(top_bucket["multi_source"]))
        )
        if not confident or (goal_intent and not goal_alignment_strong):
            return []
        filtered_docs = list(top_bucket["docs"])
        if goal_intent:
            aligned_docs = [
                doc
                for doc in filtered_docs
                if self._doc_query_term_alignment(doc, self._extract_goal_terms(query))[0] > 0
            ]
            if aligned_docs:
                filtered_docs = aligned_docs
        return filtered_docs[:4]

    def query_with_sources(
        self,
        query: str,
        *,
        rewrite_request: RetrievalRewriteRequest | None = None,
        include_debug: bool = False,
    ) -> dict[str, Any]:
        alignment_query = self._raw_query_for_rewrite(query, rewrite_request)
        should_collect_debug = include_debug or self.settings.retrieval_rewrite_debug or bool(self.web_search_client)
        graph_docs, graph_context, graph_debug = self._query_graph_priority(
            query,
            final_k=self.settings.knowledge_top_k,
            rewrite_request=rewrite_request,
        )
        debug_payload = None
        docs: list[Document]
        if graph_docs:
            docs = graph_docs
            debug_payload = graph_debug
        else:
            try:
                hybrid_result = self.query_hybrid(
                    query=query,
                    recall_k=8,
                    final_k=self.settings.knowledge_top_k,
                    rewrite_request=rewrite_request,
                    include_debug=should_collect_debug,
                )
            except TypeError:
                hybrid_result = self.query_hybrid(
                    query=query,
                    recall_k=8,
                    final_k=self.settings.knowledge_top_k,
                )
            if isinstance(hybrid_result, dict):
                docs = list(hybrid_result.get("docs", []))
                debug_payload = hybrid_result.get("debug")
            else:
                docs = hybrid_result
            graph_context = self._build_graph_context(query=alignment_query, rewrite_request=rewrite_request, docs=docs)

        local_confidence = self._build_confidence_summary(docs, query=alignment_query)
        local_evidence = self._build_local_evidence_items(docs, query=alignment_query)
        citation_docs = self._select_confident_citation_docs(docs, query=alignment_query)
        confident_ids = {
            f"{str(doc.metadata.get('source_scope') or SOURCE_SCOPE_SUPPLEMENTAL)}::{str(doc.metadata.get('filename') or '')}::{doc.metadata.get('chunk_id')}"
            for doc in citation_docs
        }
        citation_plan: list[EvidenceItem] = [
            item
            for item in local_evidence
            if item.source_id in confident_ids and item.can_cite
        ][:MAX_CITABLE_EVIDENCE_ITEMS]

        web_evidence: list[EvidenceItem] = []
        needs_web_search = (
            self.web_search_client is not None
            and (
                not citation_plan
                or not bool(local_confidence.get("citation_confident"))
                or (
                    self._query_expresses_goal_intent(alignment_query)
                    and float(local_confidence.get("best_query_term_ratio") or 0.0) < 0.6
                )
            )
        )
        if needs_web_search:
            web_evidence = self._search_web_evidence(alignment_query, debug_payload=debug_payload)
            web_citable = [item for item in web_evidence if item.can_cite]
            if not citation_plan:
                citation_plan = web_citable[:MAX_CITABLE_EVIDENCE_ITEMS]
            elif len(citation_plan) < MAX_CITABLE_EVIDENCE_ITEMS:
                remaining = MAX_CITABLE_EVIDENCE_ITEMS - len(citation_plan)
                citation_plan.extend(web_citable[:remaining])

        for index, item in enumerate(citation_plan, start=1):
            item.citation_index = index

        context = self._build_context_from_evidence(citation_plan)
        graph_guidance = self._build_graph_guidance(docs, graph_context=graph_context)
        citations: list[dict[str, Any]] = []
        for item in citation_plan:
            citations.append(
                {
                    "rank": item.citation_index,
                    "filename": item.filename,
                    "page": item.page,
                    "section": item.section,
                    "chunk_index": item.chunk_index,
                    "source_scope": item.source_scope,
                    "sources": list(item.retrieval_sources),
                    "rrf_score": item.rank_score,
                    "snippet": item.snippet,
                    "source_type": item.source_type,
                    "display_label": item.display_label,
                    "url": item.url,
                    "domain": item.domain,
                    "title": item.title,
                    "published_date": item.published_date,
                }
            )

        needs_follow_up = not bool(citation_plan)
        follow_up_question = self._build_follow_up_question(alignment_query, local_confidence) if needs_follow_up else ""
        result = {
            "context": context,
            "graph_guidance": graph_guidance,
            "graph_context": graph_context,
            "graph_next_steps": list(graph_context.get("next_steps") or []),
            "citations": citations,
            "citation_plan": citations,
            "evidence": [item.to_dict() for item in (local_evidence + web_evidence)],
            "source_breakdown": {
                "course_primary": len([item for item in local_evidence if item.source_scope == SOURCE_SCOPE_COURSE_PRIMARY]),
                "supplemental": len([item for item in local_evidence if item.source_scope == SOURCE_SCOPE_SUPPLEMENTAL]),
            },
            "citation_confident": bool(citation_plan),
            "needs_follow_up": needs_follow_up,
            "follow_up_question": follow_up_question,
        }
        if include_debug and debug_payload is not None:
            result["debug"] = debug_payload
        return result

    def query(
        self,
        query: str,
        *,
        rewrite_request: RetrievalRewriteRequest | None = None,
    ) -> str:
        return str(self.query_with_sources(query, rewrite_request=rewrite_request).get("context", ""))

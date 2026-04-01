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

from ..config import Settings
from ..core.output_format import parse_json_object
from ..core.ports import KnowledgeProvider
from ..core.text import content_to_text
from .llm import build_retrieval_planner_llm
from .processor import KnowledgeProcessor


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


RRF_K = 60
RRF_SCALE = 100.0
RETRIEVAL_STATE_VERSION = 1
CONFIDENT_CITATION_MIN_DOMINANCE = 0.74
CONFIDENT_CITATION_MIN_RRF = 0.03
FILENAME_MATCH_BOOST = -1.55
TITLE_MATCH_BOOST = -0.3
TERM_OVERLAP_BOOST = -0.08
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
        self.knowledge_dir = Path(settings.knowledge_dir)
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.knowledge_dir.parent / "knowledge_index.json"
        self.bm25_cache_file = self.knowledge_dir.parent / "bm25_cache.json"
        self.retrieval_state_file = self.knowledge_dir.parent / "retrieval_state.json"

        self.initialization_error: str | None = None
        self.embeddings = None
        self.vector_store = None
        self.bm25 = None
        self.bm25_docs: list[Document] = []
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
        self.knowledge_index = self._load_index()
        self.retrieval_state = self._load_retrieval_state()
        self.retrieval_planner_llm = None
        self.last_rewrite_trace: dict[str, Any] | None = None

        print("🚀 [RAG] 知识库引擎启动中...")

        try:
            self._ensure_retrieval_compatibility()
            if self.settings.retrieval_rewrite_enabled:
                try:
                    self.retrieval_planner_llm = build_retrieval_planner_llm(settings)
                except Exception as exc:
                    self.retrieval_planner_llm = None
                    print(f"⚠️ [RAG] Retrieval rewrite planner 初始化失败，已自动禁用改写: {exc}")
            self.embeddings = build_embedding_backend(settings)
            print(f"🧬 [RAG] Embedding Provider: {settings.embedding_provider}")
            print(f"🧬 [RAG] Embedding Backend: {type(self.embeddings).__name__}")
            self.vector_store = self._create_vector_store()
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
            self.bm25 = None
            self.bm25_docs = []
            print(f"⚠️ [RAG] 初始化失败，已回退为无知识库模式: {exc}")

    def _create_vector_store(self) -> Chroma:
        persist_directory = None
        if self.settings.vector_store_backend == "chroma":
            persist_directory = self.settings.vector_store_dir

        return Chroma(
            collection_name="knowledge",
            embedding_function=self.embeddings,
            persist_directory=persist_directory,
        )

    def _vector_doc_count(self) -> int:
        if self.vector_store is None:
            return 0
        try:
            return int(self.vector_store._collection.count())
        except Exception:
            return len(self.bm25_docs)

    def _doc_key(self, doc: Document) -> tuple[str, Any, str]:
        metadata = doc.metadata or {}
        return (
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

        grouped: dict[str, dict[str, Any]] = {}
        total_weight = 0.0
        for rank, doc in enumerate(docs, start=1):
            metadata = dict(doc.metadata or {})
            filename = str(metadata.get("filename") or "").strip()
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
                filename,
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

        top_filename, top_bucket = max(grouped.items(), key=lambda item: item[1]["weight"])
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
        if not self.index_file.exists():
            return {}

        try:
            with self.index_file.open("r", encoding="utf-8") as file_obj:
                data = json.load(file_obj)
                if isinstance(data, dict):
                    return data
        except Exception as exc:
            print(f"⚠️ [RAG] 读取知识库索引失败，将使用空索引: {exc}")

        return {}

    def _save_index(self) -> None:
        try:
            self.index_file.parent.mkdir(parents=True, exist_ok=True)
            with self.index_file.open("w", encoding="utf-8") as file_obj:
                json.dump(self.knowledge_index, file_obj, ensure_ascii=False, indent=2)
        except Exception as exc:
            print(f"⚠️ [RAG] 保存知识库索引失败: {exc}")

    def _current_retrieval_state(self) -> dict[str, Any]:
        return {
            "version": RETRIEVAL_STATE_VERSION,
            "embedding_provider": self.settings.embedding_provider,
            "embedding_model_name": self.settings.embedding_model_name,
            "vector_store_backend": self.settings.vector_store_backend,
            "vector_store_dir": self.settings.vector_store_dir,
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

        if self.bm25_cache_file.exists():
            self.bm25_cache_file.unlink(missing_ok=True)

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

    def _bm25_signature(self) -> str:
        payload = {
            "version": 1,
            "tokenizer": "regex_v2_multilingual_terms",
            "knowledge_index": self.knowledge_index,
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

    def _load_bm25_cache(self, signature: str) -> bool:
        if not self.bm25_cache_file.exists():
            return False

        try:
            with self.bm25_cache_file.open("r", encoding="utf-8") as file_obj:
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

        self.bm25_docs = docs
        self.bm25 = BM25Okapi(tokenized_corpus) if tokenized_corpus else None
        return True

    def _save_bm25_cache(self, signature: str, tokenized_corpus: list[list[str]]) -> None:
        try:
            docs_payload = [
                {
                    "page_content": doc.page_content,
                    "metadata": self._to_json_safe(doc.metadata or {}),
                }
                for doc in self.bm25_docs
            ]
            payload = {
                "version": 1,
                "signature": signature,
                "docs": docs_payload,
                "tokenized_corpus": tokenized_corpus,
            }
            self.bm25_cache_file.parent.mkdir(parents=True, exist_ok=True)
            with self.bm25_cache_file.open("w", encoding="utf-8") as file_obj:
                json.dump(payload, file_obj, ensure_ascii=False)
        except Exception as exc:
            print(f"⚠️ [RAG] 保存 BM25 缓存失败: {exc}")

    def _get_file_fingerprint(self, file_path: str) -> str:
        stat = os.stat(file_path)
        return f"{os.path.basename(file_path)}_{stat.st_size}_{int(stat.st_mtime)}"

    def _should_process(self, file_path: str) -> bool:
        filename = os.path.basename(file_path)
        fingerprint = self._get_file_fingerprint(file_path)
        old_record = self.knowledge_index.get(filename)
        return not old_record or old_record.get("fingerprint") != fingerprint

    def _delete_existing_vectors(self, filename: str) -> None:
        if self.vector_store is None:
            return

        try:
            self.vector_store._collection.delete(where={"filename": filename})
        except Exception as exc:
            print(f"⚠️ [RAG] 删除旧向量失败: {filename}: {exc}")

    def _delete_all_vectors(self) -> None:
        if self.vector_store is None:
            return

        try:
            raw = self.vector_store._collection.get(include=[])
            ids = raw.get("ids") or []
            if ids:
                self.vector_store._collection.delete(ids=ids)
        except Exception as exc:
            print(f"⚠️ [RAG] 清空向量库失败: {exc}")

    def _sync_knowledge_dir(self) -> None:
        self._cleanup_deleted_files()

        for file_path in sorted(glob.glob(os.path.join(self.settings.knowledge_dir, "*.*"))):
            if Path(file_path).name == ".gitkeep":
                continue
            if not self._should_process(file_path):
                continue
            result = self.add_local_file(file_path)
            if not result.get("success"):
                print(f"⚠️ [RAG] 资料未成功入库: {Path(file_path).name}")

    def _cleanup_deleted_files(self) -> None:
        current_files = {
            path.name
            for path in self.knowledge_dir.iterdir()
            if path.is_file() and path.name != ".gitkeep"
        }
        indexed_files = set(self.knowledge_index.keys())
        deleted_files = indexed_files - current_files

        if not deleted_files:
            return

        for filename in deleted_files:
            self._delete_existing_vectors(filename)
            self.knowledge_index.pop(filename, None)

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

    def add_local_file(self, source_path: str) -> dict[str, Any]:
        if self.vector_store is None:
            return {"success": False, "chunks": 0, "error": self.initialization_error or "vector store unavailable"}

        filename = os.path.basename(source_path)

        try:
            fingerprint = self._get_file_fingerprint(source_path)
        except FileNotFoundError:
            return {"success": False, "chunks": 0, "error": "file not found"}

        old_record = self.knowledge_index.get(filename)
        if old_record and old_record.get("fingerprint") != fingerprint:
            self._delete_existing_vectors(filename)

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

        try:
            self.vector_store.add_documents(docs)
        except Exception as exc:
            return {"success": False, "chunks": 0, "error": str(exc)}

        self.knowledge_index[filename] = {
            "fingerprint": fingerprint,
            "chunks": len(docs),
        }
        self._save_index()
        self._build_bm25_index()
        return {"success": True, "chunks": len(docs)}

    def add_document(self, source_path: str) -> bool:
        if self.vector_store is None or not os.path.exists(source_path):
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

            record = self.knowledge_index.get(path.name, {})
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

        if safe_name in self.knowledge_index:
            self.knowledge_index.pop(safe_name, None)
            self._save_index()
            removed = True

        self._delete_existing_vectors(safe_name)
        self._build_bm25_index()
        return removed

    def clear_documents(self) -> int:
        files = [item["filename"] for item in self.list_documents()]
        for filename in files:
            self.delete_document(filename)

        self._delete_all_vectors()
        self.knowledge_index = {}
        self._save_index()
        self._build_bm25_index()
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

    def _query_with_metadata_matches(self, query: str, k: int = 5) -> list[Document]:
        if not self.bm25_docs:
            return []

        candidates: list[tuple[float, int, Document]] = []
        for doc in self.bm25_docs:
            metadata = dict(doc.metadata or {})
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
        if self.vector_store is None:
            self.bm25 = None
            self.bm25_docs = []
            return

        signature = self._bm25_signature()
        if self._load_bm25_cache(signature):
            return

        try:
            raw = self.vector_store._collection.get(include=["documents", "metadatas"])
            docs = raw.get("documents", [])
            metas = raw.get("metadatas", [])

            self.bm25_docs = []
            tokenized_corpus = []

            for doc_text, meta in zip(docs, metas):
                if not doc_text:
                    continue

                self.bm25_docs.append(Document(page_content=doc_text, metadata=meta or {}))
                tokenized_corpus.append(self._tokenize_for_bm25(doc_text))

            self.bm25 = BM25Okapi(tokenized_corpus) if tokenized_corpus else None
            self._save_bm25_cache(signature, tokenized_corpus)
        except Exception as exc:
            self.bm25 = None
            self.bm25_docs = []
            print(f"⚠️ [RAG] BM25 索引构建失败: {exc}")

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
            metadata = dict(doc.metadata or {})
            metadata["_bm25_score"] = float(score)
            results.append(Document(page_content=doc.page_content, metadata=metadata))

        return results

    def query_with_docs(self, query: str, k: int | None = None) -> List[Document]:
        if self.vector_store is None:
            return []

        k = k or self.settings.knowledge_top_k
        return self.vector_store.similarity_search(query, k=k)

    def query_with_scores(self, query: str, k: int | None = None):
        if self.vector_store is None:
            return []

        k = k or self.settings.knowledge_top_k
        return self.vector_store.similarity_search_with_score(query, k=k)

    def _collect_vector_hits(self, queries: list[str], *, k: int) -> list[FamilyHit]:
        best: dict[tuple[str, Any, str], FamilyHit] = {}
        for query in _dedupe_texts(queries):
            for rank, (doc, score) in enumerate(self.query_with_scores(query, k=k), start=1):
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

    def _collect_bm25_hits(self, queries: list[str], *, k: int) -> list[FamilyHit]:
        best: dict[tuple[str, Any, str], FamilyHit] = {}
        for query in _dedupe_texts(queries):
            for rank, doc in enumerate(self.query_with_bm25(query, k=k), start=1):
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

    def _collect_metadata_hits(self, queries: list[str], *, k: int) -> list[FamilyHit]:
        best: dict[tuple[str, Any, str], FamilyHit] = {}
        for query in _dedupe_texts(queries):
            for rank, doc in enumerate(self._query_with_metadata_matches(query, k=k), start=1):
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
        vector_hits = self._collect_vector_hits([query] + list(vector_queries or []), k=recall_k)
        bm25_hits = self._collect_bm25_hits([query] + list(bm25_queries or []), k=recall_k)
        metadata_hits = self._collect_metadata_hits([query] + list(metadata_terms or []), k=recall_k)

        merged = self._fuse_with_rrf(vector_hits, bm25_hits, metadata_hits=metadata_hits)
        if not merged:
            return []
        return self._section_rerank(merged, final_k=final_k, query=query)

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

    def _select_confident_citation_docs(self, docs: list[Document], *, query: str = "") -> list[Document]:
        if not docs:
            return []

        grouped: dict[str, dict[str, Any]] = {}
        total_weight = 0.0
        for rank, doc in enumerate(docs, start=1):
            metadata = dict(doc.metadata or {})
            filename = str(metadata.get("filename") or "").strip()
            if not filename:
                continue
            weight = float(metadata.get("_rrf_score") or (1.0 / (RRF_K + rank)))
            total_weight += weight
            bucket = grouped.setdefault(
                filename,
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

        top_filename, top_bucket = max(grouped.items(), key=lambda item: item[1]["weight"])
        del top_filename
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
        try:
            hybrid_result = self.query_hybrid(
                query=query,
                recall_k=8,
                final_k=self.settings.knowledge_top_k,
                rewrite_request=rewrite_request,
                include_debug=include_debug,
            )
        except TypeError:
            hybrid_result = self.query_hybrid(
                query=query,
                recall_k=8,
                final_k=self.settings.knowledge_top_k,
            )
        debug_payload = None
        if include_debug and isinstance(hybrid_result, dict):
            docs = list(hybrid_result.get("docs", []))
            debug_payload = hybrid_result.get("debug")
        else:
            docs = hybrid_result

        context = "\n\n".join(doc.page_content for doc in docs)
        citations: list[dict[str, Any]] = []
        citation_docs = self._select_confident_citation_docs(docs, query=query)

        for index, doc in enumerate(citation_docs, start=1):
            metadata = dict(doc.metadata or {})
            snippet = re.sub(r"\s+", " ", doc.page_content or "").strip()
            if len(snippet) > 180:
                snippet = f"{snippet[:177]}..."

            citations.append(
                {
                    "rank": index,
                    "filename": metadata.get("filename") or "",
                    "page": metadata.get("page"),
                    "section": metadata.get("section") or metadata.get("H3") or metadata.get("H2") or metadata.get("H1"),
                    "chunk_index": metadata.get("chunk_id"),
                    "sources": metadata.get("_retrieval_sources", []),
                    "vector_rank": metadata.get("_vector_rank"),
                    "bm25_rank": metadata.get("_bm25_rank"),
                    "vector_score": metadata.get("_vector_score"),
                    "bm25_score": metadata.get("_bm25_score"),
                    "rrf_score": metadata.get("_rrf_score"),
                    "snippet": snippet,
                }
            )

        result = {
            "context": context,
            "citations": citations,
            "citation_confident": bool(citation_docs),
        }
        if debug_payload is not None:
            result["debug"] = debug_payload
        return result

    def query(
        self,
        query: str,
        *,
        rewrite_request: RetrievalRewriteRequest | None = None,
    ) -> str:
        return str(self.query_with_sources(query, rewrite_request=rewrite_request).get("context", ""))

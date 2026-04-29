from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from langchain_core.documents import Document

from ai_tutor_agent.config import Settings
from ai_tutor_agent.infrastructure import retriever
from ai_tutor_agent.infrastructure.processor import MinerUConnectTimeoutBudgetExceeded


def _delete_where(filename: str, source_scope: str) -> dict:
    return {
        "$and": [
            {"filename": filename},
            {"source_scope": source_scope},
        ]
    }


def build_test_settings(tmp_path):
    return Settings(
        chat_profile="custom",
        llm_provider="google",
        google_api_key="google-key",
        gemini_api_key="gemini-key",
        openai_api_key=None,
        openai_api_base=None,
        qwen_api_key=None,
        deepseek_api_key=None,
        minimax_api_key=None,
        glm_api_key=None,
        model_name="gemini-2.5-pro",
        embedding_provider="local",
        embedding_model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        tutor_temperature=0.7,
        tester_temperature=0.4,
        evaluator_temperature=0.0,
        pass_score=80,
        memory_db_path=str(tmp_path / "memory.sqlite"),
        knowledge_dir=str(tmp_path / "knowledge"),
        course_primary_enabled=False,
        course_primary_dir=str(tmp_path / "course-primary"),
        knowledge_chunk_size=100,
        knowledge_chunk_overlap=10,
        knowledge_top_k=3,
        default_thread_id="test-thread",
        http_proxy=None,
        https_proxy=None,
        local_config_enabled=True,
    )


class _EmptyCollection:
    def get(self, include=None):
        del include
        return {"documents": [], "metadatas": []}

    def delete(self, ids=None, where=None):
        del ids, where

    def count(self):
        return 0


class _FakeChroma:
    def __init__(self, *args, **kwargs):
        del args, kwargs
        self._collection = _EmptyCollection()


class _MemoryCollection:
    def __init__(self):
        self.docs = []
        self.metas = []
        self.deleted_wheres = []

    def get(self, include=None):
        payload = {"ids": [f"id-{index}" for index in range(len(self.docs))]}
        include = include or []
        if "documents" in include:
            payload["documents"] = list(self.docs)
        if "metadatas" in include:
            payload["metadatas"] = list(self.metas)
        return payload

    def delete(self, ids=None, where=None):
        if ids is not None:
            keep = [index for index in range(len(self.docs)) if f"id-{index}" not in set(ids)]
            self.docs = [self.docs[index] for index in keep]
            self.metas = [self.metas[index] for index in keep]
            return

        if where is None:
            return

        self.deleted_wheres.append(dict(where))
        keep_docs = []
        keep_metas = []
        for doc, meta in zip(self.docs, self.metas):
            meta = meta or {}
            if all(meta.get(key) == value for key, value in where.items()):
                continue
            keep_docs.append(doc)
            keep_metas.append(meta)
        self.docs = keep_docs
        self.metas = keep_metas

    def count(self):
        return len(self.docs)


class _MemoryChroma:
    def __init__(self, collection):
        self._collection = collection

    def add_documents(self, docs):
        for doc in docs:
            self._collection.docs.append(doc.page_content)
            self._collection.metas.append(dict(doc.metadata or {}))


class _FakePlannerLLM:
    def __init__(self, responses):
        if isinstance(responses, str):
            responses = [responses]
        self.responses = list(responses)
        self.messages = []

    def invoke(self, messages):
        self.messages.append(messages)
        payload = self.responses.pop(0)
        return SimpleNamespace(content=payload)


def _build_provider(monkeypatch, tmp_path, *, settings=None):
    settings = settings or build_test_settings(tmp_path)
    monkeypatch.setattr(retriever, "build_embedding_backend", lambda settings: object())
    monkeypatch.setattr(retriever, "Chroma", _FakeChroma)
    monkeypatch.setattr(retriever.LocalFileKnowledgeProvider, "_sync_knowledge_dir", lambda self: None)
    return retriever.LocalFileKnowledgeProvider(settings)


def _build_memory_provider(monkeypatch, settings):
    collection = _MemoryCollection()

    def fake_chroma_ctor(*args, **kwargs):
        del args, kwargs
        return _MemoryChroma(collection)

    monkeypatch.setattr(retriever, "build_embedding_backend", lambda settings: object())
    monkeypatch.setattr(retriever, "Chroma", fake_chroma_ctor)
    provider = retriever.LocalFileKnowledgeProvider(settings)
    return provider, collection


def test_local_knowledge_provider_falls_back_when_embedding_backend_fails(monkeypatch, tmp_path):
    monkeypatch.setattr(
        retriever,
        "build_embedding_backend",
        lambda settings: (_ for _ in ()).throw(
            RuntimeError(f"boom: {settings.embedding_provider}:{settings.embedding_model_name}")
        ),
    )

    provider = retriever.LocalFileKnowledgeProvider(build_test_settings(tmp_path))

    assert provider.vector_store is None
    assert provider.query("控制理论") == ""
    assert provider.add_document(str(tmp_path / "missing.pdf")) is False


def test_chunk_text_produces_overlapping_segments():
    chunks = retriever.chunk_text("abcdefghij" * 30, chunk_size=50, chunk_overlap=10)

    assert len(chunks) >= 2
    assert chunks[0][-10:] == chunks[1][:10]


def test_resolve_local_embedding_model_path_raises_clear_error_when_cache_missing(monkeypatch):
    def fake_snapshot_download(*args, **kwargs):
        assert kwargs["local_files_only"] is True
        raise RuntimeError("cache miss")

    monkeypatch.setattr("huggingface_hub.snapshot_download", fake_snapshot_download)

    with pytest.raises(RuntimeError, match="not found in the local HuggingFace cache"):
        retriever.resolve_local_embedding_model_path("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


def test_build_embedding_backend_uses_local_cached_path(monkeypatch, tmp_path):
    settings = build_test_settings(tmp_path)
    monkeypatch.setattr(retriever, "resolve_local_embedding_model_path", lambda _: "/tmp/hf-model")

    captured = {}

    class FakeEmbeddings:
        def __init__(self, model_name):
            captured["model_name"] = model_name

    monkeypatch.setattr("langchain_huggingface.HuggingFaceEmbeddings", FakeEmbeddings)

    backend = retriever.build_embedding_backend(settings)

    assert isinstance(backend, FakeEmbeddings)
    assert captured["model_name"] == "/tmp/hf-model"


def test_build_embedding_backend_retries_huggingface_mirror_when_default_endpoint_fails(monkeypatch, tmp_path):
    settings = build_test_settings(tmp_path)
    monkeypatch.delenv("HF_ENDPOINT", raising=False)
    monkeypatch.setenv("HF_MIRROR_ENDPOINT", "https://hf-mirror.com")
    monkeypatch.setattr(
        retriever,
        "resolve_local_embedding_model_path",
        lambda _: (_ for _ in ()).throw(RuntimeError("cache miss")),
    )

    attempts = []

    class FakeEmbeddings:
        def __init__(self, model_name):
            attempts.append((model_name, retriever.os.getenv("HF_ENDPOINT")))
            if retriever.os.getenv("HF_ENDPOINT") != "https://hf-mirror.com":
                raise OSError("huggingface default endpoint blocked")

    monkeypatch.setattr("langchain_huggingface.HuggingFaceEmbeddings", FakeEmbeddings)

    backend = retriever.build_embedding_backend(settings)

    assert isinstance(backend, FakeEmbeddings)
    assert attempts == [
        ("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", None),
        ("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", "https://hf-mirror.com"),
    ]
    assert retriever.os.getenv("HF_ENDPOINT") is None


def test_build_embedding_backend_can_disable_huggingface_mirror_fallback(monkeypatch, tmp_path):
    settings = build_test_settings(tmp_path)
    monkeypatch.delenv("HF_ENDPOINT", raising=False)
    monkeypatch.setenv("HF_ENDPOINT_FALLBACK_ENABLED", "false")
    monkeypatch.setattr(
        retriever,
        "resolve_local_embedding_model_path",
        lambda _: (_ for _ in ()).throw(RuntimeError("cache miss")),
    )

    class FakeEmbeddings:
        def __init__(self, model_name):
            del model_name
            raise OSError("huggingface default endpoint blocked")

    monkeypatch.setattr("langchain_huggingface.HuggingFaceEmbeddings", FakeEmbeddings)

    with pytest.raises(RuntimeError, match="Failed to initialize local embedding model"):
        retriever.build_embedding_backend(settings)


def test_clear_documents_removes_files_and_vector_entries(monkeypatch, tmp_path):
    settings = build_test_settings(tmp_path)
    deleted_wheres = []
    deleted_ids = []

    class FakeCollection:
        def __init__(self):
            self.ids = ["vec-1", "vec-2"]

        def get(self, include=None):
            del include
            return {"ids": list(self.ids)}

        def delete(self, ids=None, where=None):
            if where is not None:
                deleted_wheres.append(where)
            if ids is not None:
                deleted_ids.append(list(ids))
                self.ids = []

    fake_collection = FakeCollection()

    class FakeChroma:
        def __init__(self, *args, **kwargs):
            del args, kwargs
            self._collection = fake_collection

    monkeypatch.setattr(retriever, "build_embedding_backend", lambda settings: object())
    monkeypatch.setattr(retriever, "Chroma", FakeChroma)
    monkeypatch.setattr(retriever.LocalFileKnowledgeProvider, "_build_bm25_index", lambda self: None)

    provider = retriever.LocalFileKnowledgeProvider(settings)
    first = provider.knowledge_dir / "a.md"
    second = provider.knowledge_dir / "b.md"
    first.write_text("alpha", encoding="utf-8")
    second.write_text("beta", encoding="utf-8")
    provider.knowledge_index = {
        "a.md": {"fingerprint": "fp-a", "chunks": 1},
        "b.md": {"fingerprint": "fp-b", "chunks": 1},
    }

    removed = provider.clear_documents()

    assert removed == 2
    assert provider.list_documents() == []
    assert provider.knowledge_index == {}
    assert _delete_where("a.md", retriever.SOURCE_SCOPE_SUPPLEMENTAL) in deleted_wheres
    assert _delete_where("b.md", retriever.SOURCE_SCOPE_SUPPLEMENTAL) in deleted_wheres
    assert deleted_ids == []


def test_course_primary_docs_get_graph_enrichment_metadata(monkeypatch, tmp_path):
    settings = build_test_settings(tmp_path)
    settings = replace(settings, course_primary_enabled=True)
    course_dir = Path(settings.course_primary_dir)
    course_dir.mkdir(parents=True, exist_ok=True)
    notes_jsonl = course_dir.parent / "notes.jsonl"
    notes_jsonl.write_text(
        json.dumps(
            {
                "title": "反馈",
                "source_path": "src/site/notes/反馈.md",
                "prerequisites": ["系统"],
                "must_know": ["反馈的核心定义"],
                "learning_objectives": ["能解释反馈的作用"],
                "target_mastery_level": "Understand",
                "difficulty": "easy",
            },
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )
    provider, collection = _build_memory_provider(monkeypatch, settings)
    source = course_dir / "反馈.md"
    source.write_text("反馈是系统的重要概念。", encoding="utf-8")

    result = provider.add_local_file(str(source), source_scope=retriever.SOURCE_SCOPE_COURSE_PRIMARY)

    assert result["success"] is True
    metadata = collection.metas[0]
    assert metadata["kg_prerequisites"] == "系统"
    assert metadata["kg_must_know"] == "反馈的核心定义"
    assert metadata["kg_target_mastery_level"] == "Understand"
    assert metadata["kg_difficulty"] == "easy"


def test_query_with_sources_exposes_source_breakdown_and_graph_guidance(monkeypatch, tmp_path):
    settings = build_test_settings(tmp_path)
    provider = _build_provider(monkeypatch, tmp_path, settings=settings)
    docs = [
        Document(
            page_content="反馈用于把输出送回输入端。",
            metadata={
                "filename": "反馈.md",
                "source_scope": retriever.SOURCE_SCOPE_COURSE_PRIMARY,
                "_rrf_score": 0.08,
                "_retrieval_sources": ["vector"],
                "kg_title": "反馈",
                "kg_prerequisites": "系统",
                "kg_must_know": "反馈的核心定义",
                "kg_learning_objectives": "能解释反馈的作用",
                "kg_target_mastery_level": "Understand",
                "kg_difficulty": "easy",
            },
        ),
        Document(
            page_content="上传讲义里提到反馈能抑制扰动。",
            metadata={
                "filename": "lecture.pdf",
                "source_scope": retriever.SOURCE_SCOPE_SUPPLEMENTAL,
                "_rrf_score": 0.05,
                "_retrieval_sources": ["bm25"],
            },
        ),
    ]
    monkeypatch.setattr(provider, "query_hybrid", lambda *args, **kwargs: {"docs": docs, "debug": {}})

    result = provider.query_with_sources("反馈有什么作用", include_debug=True)

    assert result["source_breakdown"]["course_primary"] == 1
    assert result["source_breakdown"]["supplemental"] == 1
    assert "节点：反馈" in result["graph_guidance"]
    assert result["evidence"][0]["display_label"].startswith("[课程图谱]")


def test_query_with_sources_prefers_graph_anchor_then_related_then_supplemental(monkeypatch, tmp_path):
    settings = replace(build_test_settings(tmp_path), course_primary_enabled=True)
    course_dir = Path(settings.course_primary_dir)
    course_dir.mkdir(parents=True, exist_ok=True)
    (course_dir.parent / "notes.jsonl").write_text(
        json.dumps(
            {
                "title": "反馈",
                "source_path": "src/site/notes/反馈.md",
                "prerequisites": ["系统"],
                "neighbors": ["负反馈"],
                "learning_objectives": ["能解释反馈作用"],
                "common_errors": ["把反馈和闭环画法混为一谈"],
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    provider = _build_provider(monkeypatch, tmp_path, settings=settings)
    provider.course_graph_index = provider._load_course_graph_index()

    anchor_doc = Document(
        page_content="反馈把输出信息送回输入端。",
        metadata={"filename": "反馈.md", "chunk_id": 0, "source_scope": retriever.SOURCE_SCOPE_COURSE_PRIMARY, "_rrf_score": 0.08, "_retrieval_sources": ["vector"], "kg_title": "反馈"},
    )
    prereq_doc = Document(
        page_content="系统是反馈分析的前置。",
        metadata={"filename": "系统.md", "chunk_id": 1, "source_scope": retriever.SOURCE_SCOPE_COURSE_PRIMARY, "_rrf_score": 0.07, "_retrieval_sources": ["bm25"], "kg_title": "系统"},
    )
    supplemental_doc = Document(
        page_content="上传资料补充了反馈抑制扰动的例子。",
        metadata={"filename": "lecture.pdf", "chunk_id": 2, "source_scope": retriever.SOURCE_SCOPE_SUPPLEMENTAL, "_rrf_score": 0.05, "_retrieval_sources": ["vector"]},
    )

    def fake_query_scope_hybrid(query, *, source_scope, **kwargs):
        del kwargs
        if source_scope == retriever.SOURCE_SCOPE_COURSE_PRIMARY and query == "反馈":
            return [anchor_doc]
        if source_scope == retriever.SOURCE_SCOPE_COURSE_PRIMARY and query == "系统":
            return [prereq_doc]
        if source_scope == retriever.SOURCE_SCOPE_SUPPLEMENTAL:
            return [supplemental_doc]
        return []

    monkeypatch.setattr(provider, "_query_scope_hybrid", fake_query_scope_hybrid)

    result = provider.query_with_sources(
        "反馈有什么作用",
        rewrite_request=retriever.RetrievalRewriteRequest(channel="tutor", raw_query="反馈有什么作用", current_topic="反馈"),
    )

    assert result["graph_context"]["anchor_title"] == "反馈"
    assert result["graph_next_steps"][0]["choice"] == "review_prerequisite"
    assert [item["source_scope"] for item in result["evidence"][:3]] == [
        retriever.SOURCE_SCOPE_COURSE_PRIMARY,
        retriever.SOURCE_SCOPE_COURSE_PRIMARY,
        retriever.SOURCE_SCOPE_SUPPLEMENTAL,
    ]


def test_provider_loads_course_primary_and_supplemental_sources(monkeypatch, tmp_path):
    course_dir = tmp_path / "course-notes"
    course_dir.mkdir(parents=True, exist_ok=True)
    (course_dir / "PID.md").write_text("PID 是经典控制中的核心控制器。", encoding="utf-8")

    settings = replace(
        build_test_settings(tmp_path),
        course_primary_enabled=True,
        course_primary_dir=str(course_dir),
    )
    supplemental_dir = Path(settings.knowledge_dir)
    supplemental_dir.mkdir(parents=True, exist_ok=True)
    (supplemental_dir / "extra.md").write_text("这是补充资料。", encoding="utf-8")

    provider, collection = _build_memory_provider(monkeypatch, settings)

    assert provider._find_record("PID.md", retriever.SOURCE_SCOPE_COURSE_PRIMARY) is not None
    assert provider._find_record("extra.md", retriever.SOURCE_SCOPE_SUPPLEMENTAL) is not None
    scopes = {meta.get("source_scope") for meta in collection.metas}
    assert retriever.SOURCE_SCOPE_COURSE_PRIMARY in scopes
    assert retriever.SOURCE_SCOPE_SUPPLEMENTAL in scopes


def test_provider_uses_separate_physical_collections_per_source_scope(monkeypatch, tmp_path):
    settings = replace(build_test_settings(tmp_path), course_primary_enabled=True)
    Path(settings.course_primary_dir).mkdir(parents=True, exist_ok=True)
    collection_names = []

    class FakeCollection:
        def get(self, include=None):
            del include
            return {"documents": [], "metadatas": []}

        def delete(self, ids=None, where=None):
            del ids, where

        def count(self):
            return 0

    class FakeChroma:
        def __init__(self, *args, **kwargs):
            collection_names.append(kwargs.get("collection_name"))
            self._collection = FakeCollection()

    monkeypatch.setattr(retriever, "build_embedding_backend", lambda settings: object())
    monkeypatch.setattr(retriever, "Chroma", FakeChroma)
    monkeypatch.setattr(retriever.LocalFileKnowledgeProvider, "_sync_knowledge_dir", lambda self: None)

    provider = retriever.LocalFileKnowledgeProvider(settings)

    assert set(provider.vector_stores) == {
        retriever.SOURCE_SCOPE_COURSE_PRIMARY,
        retriever.SOURCE_SCOPE_SUPPLEMENTAL,
    }
    assert "knowledge__course_primary" in collection_names
    assert "knowledge__supplemental" in collection_names


def test_provider_persists_split_knowledge_indexes(monkeypatch, tmp_path):
    settings = replace(build_test_settings(tmp_path), course_primary_enabled=True)
    Path(settings.course_primary_dir).mkdir(parents=True, exist_ok=True)
    provider = _build_provider(monkeypatch, tmp_path, settings=settings)
    provider.knowledge_index = {
        "course_primary::反馈.md": {"fingerprint": "fp-course", "chunks": 2, "source_scope": retriever.SOURCE_SCOPE_COURSE_PRIMARY},
        "supplemental::lecture.pdf": {"fingerprint": "fp-supp", "chunks": 3, "source_scope": retriever.SOURCE_SCOPE_SUPPLEMENTAL},
    }

    provider._save_index()

    course_index = tmp_path / "knowledge_index__course_primary.json"
    supplemental_index = tmp_path / "knowledge_index__supplemental.json"
    assert course_index.exists()
    assert supplemental_index.exists()
    assert not (tmp_path / "knowledge_index.json").exists()

    course_payload = json.loads(course_index.read_text(encoding="utf-8"))
    supplemental_payload = json.loads(supplemental_index.read_text(encoding="utf-8"))
    assert "反馈.md" in course_payload
    assert "lecture.pdf" in supplemental_payload


def test_clear_documents_only_removes_supplemental_source(monkeypatch, tmp_path):
    course_dir = tmp_path / "course-notes"
    course_dir.mkdir(parents=True, exist_ok=True)
    (course_dir / "PID.md").write_text("PID 是课程主资料。", encoding="utf-8")

    settings = replace(
        build_test_settings(tmp_path),
        course_primary_enabled=True,
        course_primary_dir=str(course_dir),
    )
    supplemental_dir = Path(settings.knowledge_dir)
    supplemental_dir.mkdir(parents=True, exist_ok=True)
    (supplemental_dir / "extra.md").write_text("这是补充资料。", encoding="utf-8")

    provider, collection = _build_memory_provider(monkeypatch, settings)

    removed = provider.clear_documents()

    assert removed == 1
    assert provider.list_documents() == []
    assert provider._find_record("PID.md", retriever.SOURCE_SCOPE_COURSE_PRIMARY) is not None
    assert provider._find_record("extra.md", retriever.SOURCE_SCOPE_SUPPLEMENTAL) is None
    assert _delete_where("extra.md", retriever.SOURCE_SCOPE_SUPPLEMENTAL) in collection.deleted_wheres
    assert _delete_where("PID.md", retriever.SOURCE_SCOPE_COURSE_PRIMARY) not in collection.deleted_wheres


def test_parse_file_falls_back_to_local_after_direct_timeout_budget(monkeypatch, tmp_path):
    settings = replace(build_test_settings(tmp_path), mineru_api_token="token-demo")

    class FakeCollection:
        def get(self, include=None):
            del include
            return {"documents": [], "metadatas": []}

        def delete(self, ids=None, where=None):
            del ids, where

    class FakeChroma:
        def __init__(self, *args, **kwargs):
            del args, kwargs
            self._collection = FakeCollection()

    monkeypatch.setattr(retriever, "build_embedding_backend", lambda settings: object())
    monkeypatch.setattr(retriever, "Chroma", FakeChroma)

    provider = retriever.LocalFileKnowledgeProvider(settings)
    local_docs = [Document(page_content="local fallback", metadata={"parser": "pymupdf"})]
    pdf_path = provider.knowledge_dir / "sample.pdf"
    pdf_path.write_bytes(b"%PDF-1.4")

    monkeypatch.setattr(
        provider.processor,
        "parse_pdf_to_md",
        lambda path: (_ for _ in ()).throw(
            MinerUConnectTimeoutBudgetExceeded(
                proxy_mode="direct",
                proxy_desc="直连",
                stage="申请上传链接",
                count=3,
            )
        ),
    )
    monkeypatch.setattr(provider, "_parse_pdf_locally", lambda path: local_docs)

    docs = provider._parse_file(str(pdf_path))

    assert docs == local_docs


def test_query_hybrid_applies_rrf_and_tracks_retrieval_sources(monkeypatch, tmp_path):
    settings = build_test_settings(tmp_path)

    class FakeCollection:
        def get(self, include=None):
            del include
            return {"documents": [], "metadatas": []}

        def delete(self, ids=None, where=None):
            del ids, where

    class FakeChroma:
        def __init__(self, *args, **kwargs):
            del args, kwargs
            self._collection = FakeCollection()

    monkeypatch.setattr(retriever, "build_embedding_backend", lambda settings: object())
    monkeypatch.setattr(retriever, "Chroma", FakeChroma)

    provider = retriever.LocalFileKnowledgeProvider(settings)
    vector_doc = Document(
        page_content="vector context",
        metadata={"filename": "vector.md", "chunk_id": 1, "section": "introduction"},
    )
    bm25_doc = Document(
        page_content="bm25 context",
        metadata={"filename": "bm25.md", "chunk_id": 2, "_bm25_score": 8.7},
    )

    monkeypatch.setattr(provider, "query_with_scores", lambda query, k=None: [(vector_doc, 0.2)])
    monkeypatch.setattr(provider, "query_with_bm25", lambda query, k=5: [bm25_doc])

    docs = provider.query_hybrid("什么是控制系统", recall_k=8, final_k=2)

    assert len(docs) == 2
    by_name = {doc.metadata.get("filename"): doc for doc in docs}
    assert {"vector.md", "bm25.md"} == set(by_name)
    assert by_name["vector.md"].metadata["_vector_rank"] == 1
    assert by_name["bm25.md"].metadata["_bm25_rank"] == 1
    assert by_name["vector.md"].metadata["_rrf_score"] > 0
    assert by_name["bm25.md"].metadata["_rrf_score"] > 0
    assert "vector" in by_name["vector.md"].metadata["_retrieval_sources"]
    assert "bm25" in by_name["bm25.md"].metadata["_retrieval_sources"]


def test_query_hybrid_boosts_filename_matches_into_top_results(monkeypatch, tmp_path):
    settings = build_test_settings(tmp_path)

    class FakeCollection:
        def get(self, include=None):
            del include
            return {"documents": [], "metadatas": []}

        def delete(self, ids=None, where=None):
            del ids, where

    class FakeChroma:
        def __init__(self, *args, **kwargs):
            del args, kwargs
            self._collection = FakeCollection()

    monkeypatch.setattr(retriever, "build_embedding_backend", lambda settings: object())
    monkeypatch.setattr(retriever, "Chroma", FakeChroma)

    provider = retriever.LocalFileKnowledgeProvider(settings)
    wrong_doc = Document(
        page_content="这是一段泛化上下文。",
        metadata={"filename": "朱海-2350775-作业1.pdf", "chunk_id": 1, "section": "introduction"},
    )
    target_doc = Document(
        page_content="3403 使用相关说明。",
        metadata={"filename": "3403使用指南.pdf", "chunk_id": 2, "H1": "3403使用指南", "section": "3403使用指南"},
    )
    provider.bm25_docs = [wrong_doc, target_doc]

    monkeypatch.setattr(provider, "query_with_scores", lambda query, k=None: [(wrong_doc, 0.08)])
    monkeypatch.setattr(provider, "query_with_bm25", lambda query, k=5: [wrong_doc])

    docs = provider.query_hybrid("3403使用指南", recall_k=4, final_k=2)

    assert docs[0].metadata["filename"] == "3403使用指南.pdf"
    assert "metadata" in docs[0].metadata["_retrieval_sources"]
    assert "filename" in docs[0].metadata["_query_match_signals"]


def test_section_rerank_prefers_course_primary_source_when_scores_are_equal(monkeypatch, tmp_path):
    provider = _build_provider(monkeypatch, tmp_path)
    course_doc = Document(
        page_content="PID 控制器课程主资料。",
        metadata={"filename": "PID.md", "chunk_id": 1, "source_scope": retriever.SOURCE_SCOPE_COURSE_PRIMARY},
    )
    supplemental_doc = Document(
        page_content="PID 控制器补充资料。",
        metadata={"filename": "PID-extra.md", "chunk_id": 1, "source_scope": retriever.SOURCE_SCOPE_SUPPLEMENTAL},
    )

    ranked = provider._section_rerank(
        [(supplemental_doc, -1.0), (course_doc, -1.0)],
        final_k=2,
        query="PID",
    )

    assert ranked[0].metadata["source_scope"] == retriever.SOURCE_SCOPE_COURSE_PRIMARY


def test_query_hybrid_reserves_slots_for_course_primary_and_supplemental(monkeypatch, tmp_path):
    settings = replace(build_test_settings(tmp_path), course_primary_enabled=True)
    Path(settings.course_primary_dir).mkdir(parents=True, exist_ok=True)
    provider = _build_provider(monkeypatch, tmp_path, settings=settings)

    def fake_collect_vector_hits(queries, *, k, source_scope=None):
        del queries, k
        scope = source_scope or retriever.SOURCE_SCOPE_SUPPLEMENTAL
        docs = []
        for index in range(3):
            docs.append(
                retriever.FamilyHit(
                    doc=Document(
                        page_content=f"{scope} chunk {index}",
                        metadata={
                            "filename": f"{scope}-{index}.md",
                            "chunk_id": index,
                            "source_scope": scope,
                        },
                    ),
                    rank=index + 1,
                    score=0.1 + index,
                )
            )
        return docs

    monkeypatch.setattr(provider, "_collect_vector_hits", fake_collect_vector_hits)
    monkeypatch.setattr(provider, "_collect_bm25_hits", lambda *args, **kwargs: [])
    monkeypatch.setattr(provider, "_collect_metadata_hits", lambda *args, **kwargs: [])

    docs = provider.query_hybrid("反馈", final_k=3)

    assert len(docs) == 3
    scopes = [doc.metadata["source_scope"] for doc in docs]
    assert scopes.count(retriever.SOURCE_SCOPE_COURSE_PRIMARY) == 2
    assert scopes.count(retriever.SOURCE_SCOPE_SUPPLEMENTAL) == 1


def test_query_with_sources_returns_context_and_citations(monkeypatch, tmp_path):
    settings = build_test_settings(tmp_path)

    class FakeCollection:
        def get(self, include=None):
            del include
            return {"documents": [], "metadatas": []}

        def delete(self, ids=None, where=None):
            del ids, where

    class FakeChroma:
        def __init__(self, *args, **kwargs):
            del args, kwargs
            self._collection = FakeCollection()

    monkeypatch.setattr(retriever, "build_embedding_backend", lambda settings: object())
    monkeypatch.setattr(retriever, "Chroma", FakeChroma)

    provider = retriever.LocalFileKnowledgeProvider(settings)
    retrieved = [
        Document(
            page_content="第一段资料内容。",
            metadata={
                "filename": "guide.pdf",
                "page": 3,
                "chunk_id": 5,
                "section": "method",
                "_retrieval_sources": ["vector", "bm25"],
                "_vector_rank": 1,
                "_bm25_rank": 2,
                "_vector_score": 0.16,
                "_bm25_score": 7.2,
                "_rrf_score": 0.03,
            },
        )
    ]
    monkeypatch.setattr(provider, "query_hybrid", lambda query, recall_k=8, final_k=None, include_debug=False, rewrite_request=None: {"docs": retrieved, "debug": {}})

    result = provider.query_with_sources("控制系统")

    assert "[证据1] [上传资料] guide.pdf · 第 3 页 · method" in result["context"]
    assert len(result["citations"]) == 1
    assert len(result["citation_plan"]) == 1
    assert result["evidence"][0]["source_type"] == "local_kb"
    citation = result["citations"][0]
    assert citation["filename"] == "guide.pdf"
    assert citation["page"] == 3
    assert citation["chunk_index"] == 5
    assert citation["sources"] == ["vector", "bm25"]
    assert citation["rrf_score"] == 0.03


def test_query_with_sources_hides_citations_when_retrieval_is_ambiguous(monkeypatch, tmp_path):
    settings = build_test_settings(tmp_path)

    class FakeCollection:
        def get(self, include=None):
            del include
            return {"documents": [], "metadatas": []}

        def delete(self, ids=None, where=None):
            del ids, where

    class FakeChroma:
        def __init__(self, *args, **kwargs):
            del args, kwargs
            self._collection = FakeCollection()

    monkeypatch.setattr(retriever, "build_embedding_backend", lambda settings: object())
    monkeypatch.setattr(retriever, "Chroma", FakeChroma)

    provider = retriever.LocalFileKnowledgeProvider(settings)
    retrieved = [
        Document(
            page_content="资料 A。",
            metadata={"filename": "a.pdf", "_retrieval_sources": ["vector"], "_vector_rank": 1, "_rrf_score": 0.016},
        ),
        Document(
            page_content="资料 B。",
            metadata={"filename": "b.pdf", "_retrieval_sources": ["bm25"], "_bm25_rank": 1, "_rrf_score": 0.016},
        ),
        Document(
            page_content="资料 C。",
            metadata={"filename": "c.pdf", "_retrieval_sources": ["vector"], "_vector_rank": 2, "_rrf_score": 0.015},
        ),
    ]
    monkeypatch.setattr(provider, "query_hybrid", lambda query, recall_k=8, final_k=None, include_debug=False, rewrite_request=None: {"docs": retrieved, "debug": {}})

    result = provider.query_with_sources("控制系统")

    assert result["context"] == ""
    assert result["citations"] == []
    assert result["citation_confident"] is False
    assert result["needs_follow_up"] is True


def test_query_with_sources_uses_web_search_when_local_evidence_is_insufficient(monkeypatch, tmp_path):
    settings = replace(
        build_test_settings(tmp_path),
        web_search_enabled=True,
        tavily_api_key="tavily-key",
    )
    provider = _build_provider(monkeypatch, tmp_path, settings=settings)
    provider.web_search_client = object()
    local_docs = [
        Document(
            page_content="3403 使用指南概览。",
            metadata={"filename": "3403使用指南.pdf", "_retrieval_sources": ["metadata"], "_metadata_rank": 1, "_rrf_score": 0.02},
        )
    ]
    monkeypatch.setattr(provider, "query_hybrid", lambda query, recall_k=8, final_k=None, include_debug=False, rewrite_request=None: {"docs": local_docs, "debug": {}})
    monkeypatch.setattr(
        provider,
        "_search_web_evidence",
        lambda query, debug_payload=None: [
            retriever.EvidenceItem(
                source_type="web_search",
                source_id="https://example.com/login",
                display_label="3403 登录说明 · example.com",
                snippet="3403 登录步骤需要先连上终端，再输入默认账号。",
                goal_alignment=1.0,
                can_cite=True,
                rank_score=0.9,
                url="https://example.com/login",
                domain="example.com",
                title="3403 登录说明",
            )
        ],
    )

    result = provider.query_with_sources("3403 怎么登录")

    assert result["citation_confident"] is True
    assert result["citation_plan"][0]["source_type"] == "web_search"
    assert "https://example.com/login" in result["context"]


def test_build_bm25_index_uses_cache_on_next_start(monkeypatch, tmp_path):
    settings = build_test_settings(tmp_path)

    class FakeCollection:
        def __init__(self, docs, metas, fail_on_get=False):
            self._docs = docs
            self._metas = metas
            self.fail_on_get = fail_on_get
            self.get_calls = 0

        def get(self, include=None):
            del include
            self.get_calls += 1
            if self.fail_on_get:
                raise RuntimeError("collection.get should not be called when cache is available")
            return {"documents": self._docs, "metadatas": self._metas}

        def delete(self, ids=None, where=None):
            del ids, where

    class FakeChroma:
        def __init__(self, collection):
            self._collection = collection

    first_collection = FakeCollection(
        ["控制系统由被控对象、控制器和反馈构成。"],
        [{"filename": "guide.md", "chunk_id": 0}],
    )
    second_collection = FakeCollection(
        ["不会被使用"],
        [{"filename": "unused.md", "chunk_id": 0}],
        fail_on_get=True,
    )
    collections = [first_collection, second_collection]

    def fake_chroma_ctor(*args, **kwargs):
        del args, kwargs
        return FakeChroma(collections.pop(0))

    monkeypatch.setattr(retriever, "build_embedding_backend", lambda settings: object())
    monkeypatch.setattr(retriever, "Chroma", fake_chroma_ctor)
    monkeypatch.setattr(retriever.LocalFileKnowledgeProvider, "_sync_knowledge_dir", lambda self: None)

    provider_first = retriever.LocalFileKnowledgeProvider(settings)
    assert first_collection.get_calls == 1
    assert provider_first.bm25 is not None
    assert provider_first.bm25_cache_file.exists()

    provider_second = retriever.LocalFileKnowledgeProvider(settings)
    assert second_collection.get_calls == 0
    assert provider_second.bm25 is not None
    assert len(provider_second.bm25_docs) == 1


def test_legacy_vector_store_without_state_file_triggers_safe_rebuild(monkeypatch, tmp_path):
    settings = build_test_settings(tmp_path)
    vector_dir = tmp_path / "chroma"
    vector_dir.mkdir(parents=True, exist_ok=True)
    (vector_dir / "stale.bin").write_text("legacy", encoding="utf-8")

    knowledge_parent = Path(settings.knowledge_dir).parent
    knowledge_parent.mkdir(parents=True, exist_ok=True)
    index_file = knowledge_parent / "knowledge_index.json"
    index_file.write_text(
        '{"legacy.pdf": {"fingerprint": "legacy_1_1", "chunks": 3}}',
        encoding="utf-8",
    )

    settings = replace(settings, vector_store_dir=str(vector_dir))

    class FakeCollection:
        def get(self, include=None):
            del include
            return {"documents": [], "metadatas": []}

        def delete(self, ids=None, where=None):
            del ids, where

    class FakeChroma:
        def __init__(self, *args, **kwargs):
            del args, kwargs
            self._collection = FakeCollection()

    monkeypatch.setattr(retriever, "build_embedding_backend", lambda settings: object())
    monkeypatch.setattr(retriever, "Chroma", FakeChroma)
    monkeypatch.setattr(retriever.LocalFileKnowledgeProvider, "_sync_knowledge_dir", lambda self: None)
    monkeypatch.setattr(retriever.LocalFileKnowledgeProvider, "_build_bm25_index", lambda self: None)

    provider = retriever.LocalFileKnowledgeProvider(settings)

    assert provider.knowledge_index == {}
    assert not vector_dir.exists()
    assert provider.retrieval_state_file.exists()
    assert provider.retrieval_state["embedding_model_name"] == settings.embedding_model_name


def test_query_hybrid_bypasses_rewrite_for_exact_filename_lookup(monkeypatch, tmp_path):
    settings = replace(build_test_settings(tmp_path), retrieval_rewrite_enabled=True)
    planner = _FakePlannerLLM('{"intent":"concept_overview","rewrite_needed":true,"vector_queries":["ignored"],"bm25_queries":[],"metadata_terms":[]}')
    monkeypatch.setattr(retriever, "build_retrieval_planner_llm", lambda settings: planner)
    provider = _build_provider(monkeypatch, tmp_path, settings=settings)

    target_doc = Document(page_content="3403 使用说明", metadata={"filename": "3403使用指南.pdf", "chunk_id": 1, "section": "3403使用指南"})
    monkeypatch.setattr(provider, "query_with_scores", lambda query, k=None: [(target_doc, 0.1)])
    monkeypatch.setattr(provider, "query_with_bm25", lambda query, k=5: [target_doc])

    result = provider.query_hybrid(
        "3403使用指南.pdf",
        include_debug=True,
        rewrite_request=retriever.RetrievalRewriteRequest(channel="tutor", raw_query="3403使用指南.pdf", current_topic="3403使用指南"),
    )

    assert result["docs"][0].metadata["filename"] == "3403使用指南.pdf"
    assert result["debug"]["gate_outcome"] == "bypass"
    assert planner.messages == []


def test_query_hybrid_bypasses_rewrite_for_exact_short_term(monkeypatch, tmp_path):
    settings = replace(build_test_settings(tmp_path), retrieval_rewrite_enabled=True)
    planner = _FakePlannerLLM('{"intent":"concept_overview","rewrite_needed":true,"vector_queries":["ignored"],"bm25_queries":[],"metadata_terms":[]}')
    monkeypatch.setattr(retriever, "build_retrieval_planner_llm", lambda settings: planner)
    provider = _build_provider(monkeypatch, tmp_path, settings=settings)

    pid_doc = Document(page_content="PID 控制器", metadata={"filename": "control.pdf", "chunk_id": 1, "section": "PID"})
    monkeypatch.setattr(provider, "query_with_scores", lambda query, k=None: [(pid_doc, 0.1)])
    monkeypatch.setattr(provider, "query_with_bm25", lambda query, k=5: [pid_doc])

    result = provider.query_hybrid(
        "PID",
        include_debug=True,
        rewrite_request=retriever.RetrievalRewriteRequest(channel="tutor", raw_query="PID", current_topic="PID"),
    )

    assert result["debug"]["gate_outcome"] == "bypass"
    assert planner.messages == []


def test_query_hybrid_uses_rewrite_for_low_confidence_queries(monkeypatch, tmp_path):
    settings = replace(build_test_settings(tmp_path), retrieval_rewrite_enabled=True)
    planner = _FakePlannerLLM(
        """
        {
          "intent": "procedure",
          "rewrite_needed": true,
          "reason": "原问题过于口语化，需要补充操作目标。",
          "must_keep": ["3403"],
          "vector_queries": ["3403 文档中系统登录的操作流程"],
          "bm25_queries": ["3403 登录 系统 步骤"],
          "metadata_terms": ["3403", "登录"]
        }
        """
    )
    monkeypatch.setattr(retriever, "build_retrieval_planner_llm", lambda settings: planner)
    provider = _build_provider(monkeypatch, tmp_path, settings=settings)

    raw_doc = Document(page_content="泛化资料", metadata={"filename": "other.pdf", "chunk_id": 1, "section": "intro"})
    target_doc = Document(page_content="这里是 3403 登录步骤", metadata={"filename": "3403使用指南.pdf", "chunk_id": 2, "H1": "3403使用指南", "section": "登录"})

    def fake_query_with_scores(query, k=None):
        if "操作流程" in query:
            return [(target_doc, 0.05)]
        return [(raw_doc, 0.22)]

    def fake_query_with_bm25(query, k=5):
        if "登录" in query:
            enriched = Document(
                page_content=target_doc.page_content,
                metadata={**target_doc.metadata, "_bm25_score": 9.4},
            )
            return [enriched]
        return []

    monkeypatch.setattr(provider, "query_with_scores", fake_query_with_scores)
    monkeypatch.setattr(provider, "query_with_bm25", fake_query_with_bm25)

    result = provider.query_hybrid(
        "3403 怎么登录",
        include_debug=True,
        rewrite_request=retriever.RetrievalRewriteRequest(channel="tutor", raw_query="3403 怎么登录", current_topic="3403使用指南"),
    )

    assert result["docs"][0].metadata["filename"] == "3403使用指南.pdf"
    assert result["debug"]["gate_outcome"] == "rewrite_used"
    assert result["debug"]["planner_intent"] == "procedure"


def test_query_hybrid_falls_back_when_planner_returns_invalid_json(monkeypatch, tmp_path):
    settings = replace(build_test_settings(tmp_path), retrieval_rewrite_enabled=True)
    planner = _FakePlannerLLM("not-json")
    monkeypatch.setattr(retriever, "build_retrieval_planner_llm", lambda settings: planner)
    provider = _build_provider(monkeypatch, tmp_path, settings=settings)

    raw_doc = Document(page_content="泛化资料", metadata={"filename": "other.pdf", "chunk_id": 1, "section": "intro"})
    monkeypatch.setattr(provider, "query_with_scores", lambda query, k=None: [(raw_doc, 0.22)])
    monkeypatch.setattr(provider, "query_with_bm25", lambda query, k=5: [])

    result = provider.query_hybrid(
        "这个东西怎么用",
        include_debug=True,
        rewrite_request=retriever.RetrievalRewriteRequest(channel="tutor", raw_query="这个东西怎么用", current_topic="3403使用指南"),
    )

    assert result["docs"][0].metadata["filename"] == "other.pdf"
    assert result["debug"]["gate_outcome"] == "rewrite_failed_fallback"
    assert "invalid JSON" in result["debug"]["planner_error"]


def test_query_hybrid_repairs_missing_must_keep_terms(monkeypatch, tmp_path):
    settings = replace(build_test_settings(tmp_path), retrieval_rewrite_enabled=True)
    planner = _FakePlannerLLM(
        """
        {
          "intent": "procedure",
          "rewrite_needed": true,
          "reason": "需要更明确的步骤查询。",
          "must_keep": [],
          "vector_queries": ["系统登录步骤"],
          "bm25_queries": ["登录 步骤"],
          "metadata_terms": ["登录"]
        }
        """
    )
    monkeypatch.setattr(retriever, "build_retrieval_planner_llm", lambda settings: planner)
    provider = _build_provider(monkeypatch, tmp_path, settings=settings)

    recorded_queries = []
    raw_doc = Document(page_content="raw", metadata={"filename": "other.pdf", "chunk_id": 1, "section": "intro"})
    target_doc = Document(page_content="fixed", metadata={"filename": "3403使用指南.pdf", "chunk_id": 2, "section": "登录"})

    def fake_query_with_scores(query, k=None):
        recorded_queries.append(query)
        if "系统登录步骤 3403" in query or "系统登录步骤 3403使用指南" in query:
            return [(target_doc, 0.1)]
        return [(raw_doc, 0.2)]

    monkeypatch.setattr(provider, "query_with_scores", fake_query_with_scores)
    monkeypatch.setattr(provider, "query_with_bm25", lambda query, k=5: [])

    result = provider.query_hybrid(
        "3403使用指南 怎么登录",
        include_debug=True,
        rewrite_request=retriever.RetrievalRewriteRequest(channel="tutor", raw_query="3403使用指南 怎么登录", current_topic="3403使用指南"),
    )

    assert result["debug"]["must_keep_repaired"] is True
    assert any("3403" in query for query in result["debug"]["rewritten_vector_queries"])
    assert any(query != "3403使用指南 怎么登录" and "3403" in query for query in recorded_queries)


def test_query_hybrid_falls_back_when_rewrite_plan_has_no_queries(monkeypatch, tmp_path):
    settings = replace(build_test_settings(tmp_path), retrieval_rewrite_enabled=True)
    planner = _FakePlannerLLM(
        '{"intent":"concept_overview","rewrite_needed":true,"reason":"需要改写","must_keep":[],"vector_queries":[],"bm25_queries":[],"metadata_terms":[]}'
    )
    monkeypatch.setattr(retriever, "build_retrieval_planner_llm", lambda settings: planner)
    provider = _build_provider(monkeypatch, tmp_path, settings=settings)

    raw_doc = Document(page_content="raw", metadata={"filename": "other.pdf", "chunk_id": 1, "section": "intro"})
    monkeypatch.setattr(provider, "query_with_scores", lambda query, k=None: [(raw_doc, 0.2)])
    monkeypatch.setattr(provider, "query_with_bm25", lambda query, k=5: [])

    result = provider.query_hybrid(
        "控制系统怎么理解",
        include_debug=True,
        rewrite_request=retriever.RetrievalRewriteRequest(channel="tutor", raw_query="控制系统怎么理解", current_topic="控制系统"),
    )

    assert result["debug"]["gate_outcome"] == "rewrite_failed_fallback"
    assert result["docs"][0].metadata["filename"] == "other.pdf"


def test_query_hybrid_keeps_best_rank_per_family_across_multiple_rewritten_queries(monkeypatch, tmp_path):
    settings = replace(build_test_settings(tmp_path), retrieval_rewrite_enabled=True)
    planner = _FakePlannerLLM(
        """
        {
          "intent": "comparison",
          "rewrite_needed": true,
          "reason": "需要多条检索式覆盖不同表达。",
          "must_keep": ["PID"],
          "vector_queries": ["PID 控制器 原理", "PID controller principle"],
          "bm25_queries": ["PID 控制器", "PID 原理"],
          "metadata_terms": ["PID"]
        }
        """
    )
    monkeypatch.setattr(retriever, "build_retrieval_planner_llm", lambda settings: planner)
    provider = _build_provider(monkeypatch, tmp_path, settings=settings)

    distractor = Document(page_content="other", metadata={"filename": "other.pdf", "chunk_id": 0, "section": "other"})
    target = Document(page_content="pid", metadata={"filename": "control.pdf", "chunk_id": 3, "section": "PID"})

    def fake_query_with_scores(query, k=None):
        if query == "PID 控制器 原理":
            return [(distractor, 0.05), (target, 0.06)]
        if query == "PID controller principle":
            return [(target, 0.04)]
        return [(distractor, 0.03)]

    def fake_query_with_bm25(query, k=5):
        if query == "PID 控制器":
            return [
                Document(page_content=target.page_content, metadata={**target.metadata, "_bm25_score": 7.0}),
                Document(page_content=distractor.page_content, metadata={**distractor.metadata, "_bm25_score": 6.0}),
            ]
        if query == "PID 原理":
            return [Document(page_content=target.page_content, metadata={**target.metadata, "_bm25_score": 8.0})]
        return []

    monkeypatch.setattr(provider, "query_with_scores", fake_query_with_scores)
    monkeypatch.setattr(provider, "query_with_bm25", fake_query_with_bm25)

    result = provider.query_hybrid(
        "PID 怎么理解",
        include_debug=True,
        rewrite_request=retriever.RetrievalRewriteRequest(channel="tutor", raw_query="PID 怎么理解", current_topic="PID"),
    )

    top_doc = result["docs"][0]
    assert top_doc.metadata["filename"] == "control.pdf"
    assert top_doc.metadata["_vector_rank"] == 1
    assert top_doc.metadata["_bm25_rank"] == 1


def test_query_with_sources_keeps_citations_after_rewrite(monkeypatch, tmp_path):
    settings = replace(build_test_settings(tmp_path), retrieval_rewrite_enabled=True)
    planner = _FakePlannerLLM(
        """
        {
          "intent": "procedure",
          "rewrite_needed": true,
          "reason": "需要突出步骤信息。",
          "must_keep": ["3403"],
          "vector_queries": ["3403 文档中的登录流程"],
          "bm25_queries": ["3403 登录 步骤"],
          "metadata_terms": ["3403", "登录"]
        }
        """
    )
    monkeypatch.setattr(retriever, "build_retrieval_planner_llm", lambda settings: planner)
    provider = _build_provider(monkeypatch, tmp_path, settings=settings)

    raw_doc = Document(page_content="raw", metadata={"filename": "other.pdf", "chunk_id": 1, "section": "intro"})
    target = Document(
        page_content="第一步打开系统，第二步输入账号密码。",
        metadata={"filename": "3403使用指南.pdf", "chunk_id": 2, "section": "登录", "page": 5, "H1": "3403使用指南"},
    )

    def fake_query_with_scores(query, k=None):
        if "登录流程" in query:
            return [(target, 0.05)]
        return [(raw_doc, 0.2)]

    def fake_query_with_bm25(query, k=5):
        if "登录" in query:
            return [Document(page_content=target.page_content, metadata={**target.metadata, "_bm25_score": 9.0})]
        return []

    monkeypatch.setattr(provider, "query_with_scores", fake_query_with_scores)
    monkeypatch.setattr(provider, "query_with_bm25", fake_query_with_bm25)

    result = provider.query_with_sources(
        "3403 怎么登录",
        rewrite_request=retriever.RetrievalRewriteRequest(channel="tutor", raw_query="3403 怎么登录", current_topic="3403使用指南"),
        include_debug=True,
    )

    assert result["citation_confident"] is True
    assert result["citations"][0]["filename"] == "3403使用指南.pdf"
    assert result["debug"]["gate_outcome"] == "rewrite_used"

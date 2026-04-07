from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest
from langchain_core.documents import Document

from ai_tutor_agent.config import Settings
from ai_tutor_agent.infrastructure import retriever
from ai_tutor_agent.infrastructure.processor import MinerUConnectTimeoutBudgetExceeded


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
        knowledge_chunk_size=100,
        knowledge_chunk_overlap=10,
        knowledge_top_k=3,
        default_thread_id="test-thread",
        http_proxy=None,
        https_proxy=None,
        local_config_enabled=True,
        chroma_dir=str(tmp_path / "chroma_db"),
        dashscope_api_key=None,
        mineru_api_token=None,
        rag_hybrid_enabled=False,
        rag_mineru_enabled=False,
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
    result = provider.add_document(str(tmp_path / "missing.pdf"))
    assert result["success"] is False


def test_add_local_file_skips_reimport_when_fingerprint_unchanged(monkeypatch, tmp_path):
    settings = build_test_settings(tmp_path)

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
            del args, kwargs
            self._collection = FakeCollection()
            self.added_docs = []

        def add_documents(self, docs):
            self.added_docs.append(docs)

    monkeypatch.setattr(retriever, "build_embedding_backend", lambda settings: object())
    monkeypatch.setattr(retriever, "Chroma", FakeChroma)
    monkeypatch.setattr(retriever.LocalFileKnowledgeProvider, "_sync_knowledge_dir", lambda self: None)
    monkeypatch.setattr(retriever.LocalFileKnowledgeProvider, "_build_bm25_index", lambda self: None)

    provider = retriever.LocalFileKnowledgeProvider(settings)
    sample = Path(settings.knowledge_dir) / "dup.pdf"
    sample.parent.mkdir(parents=True, exist_ok=True)
    sample.write_bytes(b"%PDF-1.4\nDUPLICATE")

    fingerprint = provider._get_file_fingerprint(str(sample))
    provider.knowledge_index["dup.pdf"] = {"fingerprint": fingerprint, "chunks": 3}

    monkeypatch.setattr(
        provider,
        "_parse_file",
        lambda source_path: [Document(page_content="x", metadata={"filename": "dup.pdf", "chunk_id": 0})],
    )

    result = provider.add_local_file(str(sample))

    assert result["success"] is True
    assert result["chunks"] == 3
    assert "skipped re-import" in result["message"]
    assert provider.vector_store.added_docs == []


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
    assert {"filename": "a.md"} in deleted_wheres
    assert {"filename": "b.md"} in deleted_wheres
    assert deleted_ids == [["vec-1", "vec-2"]]


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
    monkeypatch.setattr(provider, "query_hybrid", lambda query, recall_k=8, final_k=None: retrieved)

    result = provider.query_with_sources("控制系统")

    assert result["context"] == "第一段资料内容。"
    assert len(result["citations"]) == 1
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
    monkeypatch.setattr(provider, "query_hybrid", lambda query, recall_k=8, final_k=None: retrieved)

    result = provider.query_with_sources("控制系统")

    assert result["context"] == "资料 A。\n\n资料 B。\n\n资料 C。"
    assert result["citations"] == []
    assert result["citation_confident"] is False


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

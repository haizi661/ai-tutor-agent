import pytest

from ai_tutor_agent.config import Settings
from ai_tutor_agent.infrastructure import retriever


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
        embedding_model_name="sentence-transformers/all-MiniLM-L6-v2",
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
    )


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
        retriever.resolve_local_embedding_model_path("sentence-transformers/all-MiniLM-L6-v2")


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

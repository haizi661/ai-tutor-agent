import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ai_tutor_agent.tools.debug_rag import (
    DebugKnowledgeSearcher,
    RetrievedChunk,
    build_rewriter_from_settings,
    build_report,
    parse_args,
    run_search_mode,
    save_report_json,
)


class FakeSearcher:
    def __init__(self):
        self.calls = []

    def search_raw(self, query, k):
        self.calls.append(("raw", query, k))
        return [RetrievedChunk(rank=1, score=0.1, content="raw", metadata={"source": "raw"})]

    def search_reranked(self, query, recall_k, final_k):
        self.calls.append(("rerank", query, recall_k, final_k))
        return [RetrievedChunk(rank=1, score=0.2, content="rerank", metadata={"source": "rerank"})]

    def search_hybrid(self, query, recall_k, final_k):
        self.calls.append(("hybrid", query, recall_k, final_k))
        return [RetrievedChunk(rank=1, score=0.3, content="hybrid", metadata={"source": "hybrid"})]


def test_run_search_mode_dispatches_correct_method():
    searcher = FakeSearcher()

    result_raw = run_search_mode(
        searcher,
        mode="raw",
        query="q1",
        top_k=5,
        recall_k=8,
        final_k=3,
    )
    result_rerank = run_search_mode(
        searcher,
        mode="rerank",
        query="q2",
        top_k=5,
        recall_k=9,
        final_k=4,
    )
    result_hybrid = run_search_mode(
        searcher,
        mode="hybrid",
        query="q3",
        top_k=5,
        recall_k=10,
        final_k=2,
    )

    assert result_raw[0].content == "raw"
    assert result_rerank[0].content == "rerank"
    assert result_hybrid[0].content == "hybrid"
    assert searcher.calls == [
        ("raw", "q1", 5),
        ("rerank", "q2", 9, 4),
        ("hybrid", "q3", 10, 2),
    ]


def test_build_report_contains_expected_shape():
    payload = build_report(
        mode="hybrid",
        original_query="原问题",
        rewritten_query="改写问题",
        results=[RetrievedChunk(rank=1, score=0.12, content="abc", metadata={"filename": "x.txt"})],
    )

    assert payload["mode"] == "hybrid"
    assert payload["original_query"] == "原问题"
    assert payload["rewritten_query"] == "改写问题"
    assert payload["result_count"] == 1
    assert payload["results"][0]["metadata"]["filename"] == "x.txt"


def test_parse_args_supports_debug_options():
    args = parse_args([
        "--mode",
        "rerank",
        "--top-k",
        "6",
        "--recall-k",
        "9",
        "--final-k",
        "3",
        "--no-rewrite",
        "--once",
        "PID 控制是什么",
        "--export",
        "data/report.json",
    ])

    assert args.mode == "rerank"
    assert args.top_k == 6
    assert args.recall_k == 9
    assert args.final_k == 3
    assert args.no_rewrite is True
    assert args.once == "PID 控制是什么"
    assert args.export == "data/report.json"


def test_save_report_json_writes_file(tmp_path):
    output = tmp_path / "report.json"
    payload = build_report(
        mode="raw",
        original_query="q",
        rewritten_query="q",
        results=[RetrievedChunk(rank=1, score=0.2, content="abc", metadata={"x": 1})],
    )

    save_report_json(str(output), payload)

    assert output.exists()
    text = output.read_text(encoding="utf-8")
    assert '"mode": "raw"' in text
    assert '"result_count": 1' in text


def test_build_rewriter_prefers_deepseek(monkeypatch):
    captured = {}

    class FakeRewriter:
        def __init__(self, api_key, model, base_url):
            captured["api_key"] = api_key
            captured["model"] = model
            captured["base_url"] = base_url

    import ai_tutor_agent.tools.debug_rag as mod

    monkeypatch.setattr(mod, "LLMQueryRewriter", FakeRewriter)
    settings = type("S", (), {
        "deepseek_api_key": "deepseek-key",
        "openai_api_key": "openai-key",
        "openai_api_base": "https://example.com/v1",
        "model_name": "x-model",
    })()

    build_rewriter_from_settings(settings)

    assert captured["api_key"] == "deepseek-key"
    assert captured["model"] == "deepseek-chat"
    assert captured["base_url"] == "https://api.deepseek.com/v1"


def test_build_rewriter_falls_back_to_openai(monkeypatch):
    captured = {}

    class FakeRewriter:
        def __init__(self, api_key, model, base_url):
            captured["api_key"] = api_key
            captured["model"] = model
            captured["base_url"] = base_url

    import ai_tutor_agent.tools.debug_rag as mod

    monkeypatch.setattr(mod, "LLMQueryRewriter", FakeRewriter)
    settings = type("S", (), {
        "deepseek_api_key": None,
        "openai_api_key": "openai-key",
        "openai_api_base": "https://openai.compat/v1",
        "model_name": "my-model",
    })()

    build_rewriter_from_settings(settings)

    assert captured["api_key"] == "openai-key"
    assert captured["model"] == "my-model"
    assert captured["base_url"] == "https://openai.compat/v1"


def test_build_rewriter_raises_when_no_model_configured():
    settings = type("S", (), {
        "deepseek_api_key": None,
        "openai_api_key": None,
        "openai_api_base": None,
        "model_name": "unused",
    })()

    try:
        build_rewriter_from_settings(settings)
        assert False, "Expected RuntimeError when rewrite model config is missing"
    except RuntimeError as exc:
        assert "DEEPSEEK_API_KEY" in str(exc) or "OPENAI_API_KEY" in str(exc)


def test_search_hybrid_maps_score_from_vector_results():
    class FakeDoc:
        def __init__(self, content, metadata):
            self.page_content = content
            self.metadata = metadata

    class FakeProvider:
        def __init__(self):
            self.settings = type("S", (), {"knowledge_top_k": 3})()

        def query_with_scores(self, query, k):
            del query, k
            return [
                (FakeDoc("doc-1", {"filename": "a.txt", "chunk_id": 1}), 0.21),
            ]

        def query_with_bm25(self, query, k):
            del query, k
            return [FakeDoc("doc-2", {"filename": "b.txt", "chunk_id": 2})]

        def query_hybrid(self, query, recall_k, final_k):
            del query, recall_k, final_k
            return [
                FakeDoc("doc-1", {"filename": "a.txt", "chunk_id": 1}),
                FakeDoc("doc-2", {"filename": "b.txt", "chunk_id": 2}),
            ]

    searcher = DebugKnowledgeSearcher(FakeProvider())
    results = searcher.search_hybrid("pid", recall_k=8, final_k=3)

    assert len(results) == 2
    assert results[0].score == 0.21
    assert results[1].score is None

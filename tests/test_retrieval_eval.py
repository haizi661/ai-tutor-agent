import json

import pytest
from langchain_core.documents import Document

from ai_tutor_agent.infrastructure.retrieval_eval import (
    RetrievalExample,
    evaluate_queries,
    evaluate_ranked_docs,
    load_eval_examples,
)


def test_load_eval_examples_supports_jsonl(tmp_path):
    eval_path = tmp_path / "eval.jsonl"
    lines = [
        json.dumps(
            {
                "query": "什么是闭环系统",
                "relevant": [{"filename": "guide.pdf", "chunk_id": 2}],
            },
            ensure_ascii=False,
        ),
        json.dumps(
            {
                "query": "稳定性判据",
                "relevant_filenames": ["notes.md"],
            },
            ensure_ascii=False,
        ),
    ]
    eval_path.write_text("\n".join(lines), encoding="utf-8")

    examples = load_eval_examples(str(eval_path))

    assert len(examples) == 2
    assert examples[0].query == "什么是闭环系统"
    assert "chunk::guide.pdf::2" in examples[0].relevant_ids
    assert "file::notes.md" in examples[1].relevant_ids


def test_evaluate_ranked_docs_computes_recall_mrr_ndcg():
    docs = [
        Document(page_content="irrelevant", metadata={"filename": "other.md", "chunk_id": 1}),
        Document(page_content="relevant1", metadata={"filename": "guide.pdf", "chunk_id": 2}),
        Document(page_content="relevant2", metadata={"filename": "notes.md", "chunk_id": 9}),
    ]
    relevant_ids = frozenset({"chunk::guide.pdf::2", "file::notes.md"})

    metrics = evaluate_ranked_docs(docs, relevant_ids, [1, 3])

    assert metrics[1]["recall"] == 0.0
    assert metrics[1]["mrr"] == 0.0
    assert metrics[1]["ndcg"] == 0.0

    assert metrics[3]["recall"] == pytest.approx(1.0)
    assert metrics[3]["mrr"] == pytest.approx(0.5)
    assert metrics[3]["ndcg"] == pytest.approx(0.6934264, rel=1e-4)


class FakeProvider:
    def __init__(self, docs_by_query):
        self._docs_by_query = docs_by_query

    def query_hybrid(self, query, recall_k=8, final_k=3, rewrite_request=None, include_debug=False):
        del recall_k, final_k, rewrite_request
        docs = self._docs_by_query.get(query, [])
        if include_debug:
            return {"docs": docs, "debug": {"gate_outcome": "raw_only"}}
        return self._docs_by_query.get(query, [])


def test_evaluate_queries_aggregates_metrics():
    provider = FakeProvider(
        {
            "q1": [Document(page_content="hit", metadata={"filename": "a.md", "chunk_id": 1})],
            "q2": [
                Document(page_content="miss", metadata={"filename": "x.md", "chunk_id": 0}),
                Document(page_content="hit", metadata={"filename": "b.md", "chunk_id": 2}),
            ],
        }
    )
    examples = [
        RetrievalExample(query="q1", relevant_ids=frozenset({"chunk::a.md::1"})),
        RetrievalExample(query="q2", relevant_ids=frozenset({"chunk::b.md::2"})),
    ]

    report = evaluate_queries(provider, examples, recall_k=10, k_values=[1, 3])

    assert report["examples"] == 2
    assert report["summary"]["Recall@1"] == pytest.approx(0.5)
    assert report["summary"]["MRR@3"] == pytest.approx(0.75)
    assert "nDCG@3" in report["summary"]


def test_evaluate_queries_can_collect_rewrite_debug_payload():
    provider = FakeProvider({"q1": [Document(page_content="hit", metadata={"filename": "a.md", "chunk_id": 1})]})
    examples = [RetrievalExample(query="q1", relevant_ids=frozenset({"chunk::a.md::1"}))]

    report = evaluate_queries(provider, examples, recall_k=10, k_values=[1], use_rewrite=True, include_debug=True)

    assert report["rewrite_enabled"] is True
    assert report["per_query"][0]["debug"]["gate_outcome"] == "raw_only"

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from langchain_core.documents import Document

from .retriever import RetrievalRewriteRequest


@dataclass(frozen=True)
class RetrievalExample:
    query: str
    relevant_ids: frozenset[str]


def _chunk_identifier(filename: str, chunk_id: Any) -> str:
    return f"chunk::{filename}::{chunk_id}"


def _file_identifier(filename: str) -> str:
    return f"file::{filename}"


def _parse_relevant_ids(payload: dict[str, Any]) -> frozenset[str]:
    ids: set[str] = set()

    relevant_items = payload.get("relevant", [])
    if isinstance(relevant_items, list):
        for item in relevant_items:
            if isinstance(item, str):
                filename = item.strip()
                if filename:
                    ids.add(_file_identifier(filename))
                continue

            if not isinstance(item, dict):
                continue

            filename = str(item.get("filename", "")).strip()
            if not filename:
                continue
            chunk_id = item.get("chunk_id", item.get("chunk_index"))
            if chunk_id is None:
                ids.add(_file_identifier(filename))
            else:
                ids.add(_chunk_identifier(filename, chunk_id))

    relevant_filenames = payload.get("relevant_filenames", [])
    if isinstance(relevant_filenames, list):
        for filename in relevant_filenames:
            if not isinstance(filename, str):
                continue
            cleaned = filename.strip()
            if cleaned:
                ids.add(_file_identifier(cleaned))

    return frozenset(ids)


def load_eval_examples(eval_file: str) -> list[RetrievalExample]:
    path = Path(eval_file)
    if not path.exists():
        raise FileNotFoundError(f"Evaluation file was not found: {eval_file}")

    if path.suffix.lower() == ".jsonl":
        raw_items: list[Any] = []
        for index, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                raw_items.append(json.loads(stripped))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSONL at line {index}: {exc}") from exc
    else:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            raw_items = list(payload.get("items", []))
        elif isinstance(payload, list):
            raw_items = payload
        else:
            raise ValueError("Evaluation file must be a JSON array or an object with an 'items' array.")

    examples: list[RetrievalExample] = []

    for index, item in enumerate(raw_items, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Item #{index} must be a JSON object.")

        query = str(item.get("query", "")).strip()
        if not query:
            raise ValueError(f"Item #{index} is missing a non-empty 'query'.")

        relevant_ids = _parse_relevant_ids(item)
        if not relevant_ids:
            raise ValueError(
                f"Item #{index} has no relevance labels. Add 'relevant' or 'relevant_filenames'."
            )

        examples.append(RetrievalExample(query=query, relevant_ids=relevant_ids))

    return examples


def _doc_candidate_ids(doc: Document) -> list[str]:
    metadata = doc.metadata or {}
    filename = str(metadata.get("filename", "")).strip()
    if not filename:
        return []

    chunk_id = metadata.get("chunk_id", metadata.get("chunk_index"))
    ids = []
    if chunk_id is not None:
        ids.append(_chunk_identifier(filename, chunk_id))
    ids.append(_file_identifier(filename))
    return ids


def _dcg(binary_relevance: list[int]) -> float:
    score = 0.0
    for rank, rel in enumerate(binary_relevance, start=1):
        if rel <= 0:
            continue
        score += 1.0 / math.log2(rank + 1)
    return score


def evaluate_ranked_docs(
    docs: list[Document],
    relevant_ids: frozenset[str],
    k_values: list[int],
) -> dict[int, dict[str, float]]:
    if not k_values:
        raise ValueError("k_values must not be empty.")

    ordered_ks = sorted(set(k for k in k_values if k > 0))
    if not ordered_ks:
        raise ValueError("k_values must include positive integers.")

    max_k = ordered_ks[-1]
    used_ids: set[str] = set()
    relevance_by_rank: list[int] = []
    matched_counts: list[int] = []
    first_relevant_rank: int | None = None

    for rank in range(1, max_k + 1):
        hit = 0
        if rank <= len(docs):
            doc = docs[rank - 1]
            for candidate_id in _doc_candidate_ids(doc):
                if candidate_id in relevant_ids and candidate_id not in used_ids:
                    used_ids.add(candidate_id)
                    hit = 1
                    if first_relevant_rank is None:
                        first_relevant_rank = rank
                    break

        relevance_by_rank.append(hit)
        matched_counts.append(len(used_ids))

    relevant_total = len(relevant_ids)
    metrics_by_k: dict[int, dict[str, float]] = {}

    for k in ordered_ks:
        hits = matched_counts[k - 1]
        recall = hits / relevant_total if relevant_total else 0.0
        mrr = 0.0
        if first_relevant_rank is not None and first_relevant_rank <= k:
            mrr = 1.0 / first_relevant_rank

        relevance_prefix = relevance_by_rank[:k]
        dcg = _dcg(relevance_prefix)
        ideal_len = min(relevant_total, k)
        idcg = _dcg([1] * ideal_len)
        ndcg = (dcg / idcg) if idcg > 0 else 0.0

        metrics_by_k[k] = {
            "recall": recall,
            "mrr": mrr,
            "ndcg": ndcg,
        }

    return metrics_by_k


def evaluate_queries(
    provider,
    examples: list[RetrievalExample],
    *,
    recall_k: int,
    k_values: list[int],
    use_rewrite: bool = False,
    include_debug: bool = False,
) -> dict[str, Any]:
    if not examples:
        raise ValueError("No evaluation examples were provided.")

    ordered_ks = sorted(set(k for k in k_values if k > 0))
    if not ordered_ks:
        raise ValueError("k_values must include positive integers.")

    final_k = ordered_ks[-1]
    per_query: list[dict[str, Any]] = []
    totals: dict[int, dict[str, float]] = {
        k: {"recall": 0.0, "mrr": 0.0, "ndcg": 0.0} for k in ordered_ks
    }

    for example in examples:
        rewrite_request = None
        if use_rewrite:
            rewrite_request = RetrievalRewriteRequest(
                channel="eval",
                raw_query=example.query,
                current_topic="",
            )

        result = provider.query_hybrid(
            example.query,
            recall_k=max(recall_k, final_k),
            final_k=final_k,
            rewrite_request=rewrite_request,
            include_debug=include_debug,
        )
        debug_payload = None
        if include_debug and isinstance(result, dict):
            docs = list(result.get("docs", []))
            debug_payload = result.get("debug")
        else:
            docs = result
        metrics_by_k = evaluate_ranked_docs(docs, example.relevant_ids, ordered_ks)

        per_query_entry = {
            "query": example.query,
            "hits": len(docs),
            "metrics": {f"@{k}": metrics_by_k[k] for k in ordered_ks},
        }
        if debug_payload is not None:
            per_query_entry["debug"] = debug_payload
        per_query.append(per_query_entry)

        for k in ordered_ks:
            totals[k]["recall"] += metrics_by_k[k]["recall"]
            totals[k]["mrr"] += metrics_by_k[k]["mrr"]
            totals[k]["ndcg"] += metrics_by_k[k]["ndcg"]

    count = float(len(examples))
    summary = {
        f"Recall@{k}": totals[k]["recall"] / count for k in ordered_ks
    }
    summary.update({
        f"MRR@{k}": totals[k]["mrr"] / count for k in ordered_ks
    })
    summary.update({
        f"nDCG@{k}": totals[k]["ndcg"] / count for k in ordered_ks
    })

    return {
        "examples": len(examples),
        "k_values": ordered_ks,
        "recall_k": max(recall_k, final_k),
        "rewrite_enabled": bool(use_rewrite),
        "summary": summary,
        "per_query": per_query,
    }

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import sys
import warnings
from dataclasses import replace
from pathlib import Path

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai_tutor_agent.config import get_settings
from ai_tutor_agent.infrastructure.retriever import LocalFileKnowledgeProvider, RetrievalRewriteRequest

warnings.filterwarnings("ignore", category=FutureWarning, module=r"google\.api_core")
warnings.filterwarnings("ignore", category=FutureWarning, module=r"google\.auth")
warnings.filterwarnings("ignore", category=FutureWarning, module=r"google\.oauth2")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manual retrieval debug runner.")
    parser.add_argument("query", help="Actual retrieval query to send into the provider.")
    parser.add_argument(
        "--channel",
        default="tutor",
        choices=["tutor", "interruption", "eval"],
        help="Rewrite channel context.",
    )
    parser.add_argument(
        "--raw-query",
        default="",
        help="Original user utterance. Defaults to the positional query.",
    )
    parser.add_argument(
        "--current-topic",
        default="",
        help="Current learning topic or document anchor.",
    )
    parser.add_argument("--attempt-count", type=int, default=0, help="Tutor attempt count.")
    parser.add_argument("--teaching-strategy", default="", help="Teaching strategy hint.")
    parser.add_argument("--weak-areas-hint", default="", help="Weak areas hint for tutor retrieval.")
    parser.add_argument("--conversation-hint", default="", help="Recent context hint for interruption retrieval.")
    parser.add_argument("--recall-k", type=int, default=8, help="Recall pool size before rerank.")
    parser.add_argument("--final-k", type=int, default=0, help="Final number of chunks to keep.")
    parser.add_argument(
        "--enable-rewrite",
        action="store_true",
        help="Force-enable retrieval rewrite for this debug run.",
    )
    parser.add_argument(
        "--disable-rewrite",
        action="store_true",
        help="Force-disable retrieval rewrite for this debug run.",
    )
    parser.add_argument(
        "--output",
        default="",
        help="Optional JSON output path.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print full JSON instead of compact human-readable output.",
    )
    parser.add_argument(
        "--show-init-logs",
        action="store_true",
        help="Show knowledge provider startup logs instead of suppressing them.",
    )
    return parser


def _doc_to_debug_entry(index: int, doc) -> dict:
    metadata = dict(doc.metadata or {})
    snippet = " ".join((doc.page_content or "").split())
    if len(snippet) > 220:
        snippet = f"{snippet[:217]}..."
    return {
        "rank": index,
        "filename": metadata.get("filename"),
        "chunk_id": metadata.get("chunk_id"),
        "section": metadata.get("section") or metadata.get("H3") or metadata.get("H2") or metadata.get("H1"),
        "page": metadata.get("page"),
        "retrieval_sources": metadata.get("_retrieval_sources", []),
        "vector_rank": metadata.get("_vector_rank"),
        "bm25_rank": metadata.get("_bm25_rank"),
        "metadata_rank": metadata.get("_metadata_rank"),
        "vector_score": metadata.get("_vector_score"),
        "bm25_score": metadata.get("_bm25_score"),
        "rrf_score": metadata.get("_rrf_score"),
        "query_match_signals": metadata.get("_query_match_signals", []),
        "snippet": snippet,
    }


def _citation_to_debug_entry(index: int, doc) -> dict:
    metadata = dict(doc.metadata or {})
    snippet = " ".join((doc.page_content or "").split())
    if len(snippet) > 180:
        snippet = f"{snippet[:177]}..."
    return {
        "rank": index,
        "filename": metadata.get("filename"),
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


def _format_compact_report(report: dict) -> str:
    request = report["request"]
    trace = report["rewrite_trace"] or {}
    raw_conf = trace.get("raw_confidence", {}) or {}
    rewritten_conf = trace.get("rewritten_confidence", {}) or {}
    raw_terms = raw_conf.get("query_terms", []) or []
    raw_matched = raw_conf.get("best_query_terms_matched", []) or []
    raw_missing = raw_conf.get("best_query_terms_missing", []) or []
    rewritten_matched = rewritten_conf.get("best_query_terms_matched", []) or []
    rewritten_missing = rewritten_conf.get("best_query_terms_missing", []) or []

    lines = [
        "== Retrieval Debug ==",
        "",
        "[Request]",
        f"query: {request['query']}",
        f"channel: {request['channel']}",
        f"topic: {request['current_topic'] or '-'}",
        f"rewrite: {'on' if report['settings']['retrieval_rewrite_enabled'] else 'off'} ({report['settings']['retrieval_rewrite_mode']})",
        "",
        "[Decision]",
        f"gate: {trace.get('gate_outcome', '-')}",
        f"reason: {trace.get('gate_reason', '-')}",
    ]
    if trace.get("planner_intent"):
        lines.append(f"planner_intent: {trace['planner_intent']}")
    if trace.get("planner_reason"):
        lines.append(f"planner_reason: {trace['planner_reason']}")
    if trace.get("planner_error"):
        lines.append(f"planner_error: {trace['planner_error']}")
    lines.extend(["", "[Rewrite Plan]", f"raw_query: {trace.get('raw_query', request['query'])}"])
    if trace.get("rewritten_vector_queries"):
        lines.append("vector_queries:")
        for index, item in enumerate(trace["rewritten_vector_queries"], start=1):
            lines.append(f"  {index}. {item}")
    else:
        lines.append("vector_queries: none")
    if trace.get("rewritten_bm25_queries"):
        lines.append("bm25_queries:")
        for index, item in enumerate(trace["rewritten_bm25_queries"], start=1):
            lines.append(f"  {index}. {item}")
    else:
        lines.append("bm25_queries: none")
    if trace.get("metadata_terms"):
        lines.append(f"metadata_terms: {trace['metadata_terms']}")
    else:
        lines.append("metadata_terms: none")

    lines.extend(["", "[Goal Match Comparison]"])
    if raw_terms:
        lines.append(f"goal_terms: {raw_terms}")
    if raw_conf:
        lines.append(
            "raw_match: "
            f"hits={raw_conf.get('best_query_term_hits', 0)}/{raw_conf.get('query_term_count', 0)} "
            f"matched={raw_matched or []} "
            f"missing={raw_missing or []}"
        )
    if rewritten_conf:
        lines.append(
            "rewritten_match: "
            f"hits={rewritten_conf.get('best_query_term_hits', 0)}/{rewritten_conf.get('query_term_count', 0)} "
            f"matched={rewritten_matched or []} "
            f"missing={rewritten_missing or []}"
        )
    if raw_conf:
        lines.append(
            "raw_confidence: "
            f"citation={raw_conf.get('citation_confident')} "
            f"filename={raw_conf.get('top_filename') or '-'} "
            f"sources={raw_conf.get('top_source_count')} "
            f"dominance={raw_conf.get('dominance', 0.0):.2f} "
            f"best_rrf={raw_conf.get('top_rrf_score', 0.0):.4f}"
        )
    if rewritten_conf:
        lines.append(
            "rewritten_confidence: "
            f"citation={rewritten_conf.get('citation_confident')} "
            f"filename={rewritten_conf.get('top_filename') or '-'} "
            f"sources={rewritten_conf.get('top_source_count')} "
            f"dominance={rewritten_conf.get('dominance', 0.0):.2f} "
            f"best_rrf={rewritten_conf.get('top_rrf_score', 0.0):.4f}"
        )

    lines.extend(["", "[Top Docs]"])
    for doc in report.get("top_docs", []):
        lines.append(
            f"{doc['rank']}. {doc.get('filename') or '-'} | section={doc.get('section') or '-'} | "
            f"sources={doc.get('retrieval_sources') or []} | signals={doc.get('query_match_signals') or []}"
        )
        lines.append(f"   snippet: {doc.get('snippet') or ''}")

    lines.extend(["", "[Citations]", f"citation_confident: {report.get('citation_confident')}"])
    if report.get("citations"):
        for citation in report["citations"]:
            lines.append(
                f"{citation['rank']}. {citation.get('filename') or '-'} | section={citation.get('section') or '-'} | "
                f"sources={citation.get('sources') or []}"
            )
            lines.append(f"   snippet: {citation.get('snippet') or ''}")
    else:
        lines.append("none")

    lines.extend(
        [
            "",
            "[Context]",
            f"context_chars: {report.get('context_chars', 0)}",
            f"context_preview: {report.get('context_preview', '')}",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    if args.enable_rewrite and args.disable_rewrite:
        raise SystemExit("Cannot use --enable-rewrite and --disable-rewrite together.")

    settings = get_settings()
    if args.enable_rewrite:
        settings = replace(settings, retrieval_rewrite_enabled=True)
    elif args.disable_rewrite:
        settings = replace(settings, retrieval_rewrite_enabled=False)

    if args.show_init_logs:
        provider = LocalFileKnowledgeProvider(settings)
    else:
        hidden_logs = io.StringIO()
        with contextlib.redirect_stdout(hidden_logs), contextlib.redirect_stderr(hidden_logs):
            provider = LocalFileKnowledgeProvider(settings)
    if provider.vector_store is None:
        raise SystemExit(
            "Knowledge provider initialization failed; vector store unavailable. "
            f"Error: {provider.initialization_error or 'unknown'}"
        )

    rewrite_request = RetrievalRewriteRequest(
        channel=args.channel,
        raw_query=(args.raw_query or args.query).strip(),
        current_topic=args.current_topic.strip(),
        attempt_count=max(0, int(args.attempt_count or 0)),
        teaching_strategy=args.teaching_strategy.strip(),
        weak_areas_hint=args.weak_areas_hint.strip(),
        conversation_hint=args.conversation_hint.strip(),
    )

    final_k = args.final_k or settings.knowledge_top_k
    hybrid_result = provider.query_hybrid(
        args.query,
        recall_k=max(1, int(args.recall_k)),
        final_k=max(1, int(final_k)),
        rewrite_request=rewrite_request,
        include_debug=True,
    )
    docs = list(hybrid_result.get("docs", []))
    trace = hybrid_result.get("debug", {})
    context = "\n\n".join(doc.page_content for doc in docs)
    citation_docs = provider._select_confident_citation_docs(docs, query=args.query)

    report = {
        "settings": {
            "retrieval_rewrite_enabled": bool(settings.retrieval_rewrite_enabled),
            "retrieval_rewrite_mode": settings.retrieval_rewrite_mode,
            "knowledge_top_k": int(settings.knowledge_top_k),
            "embedding_provider": settings.embedding_provider,
            "embedding_model_name": settings.embedding_model_name,
        },
        "request": {
            "query": args.query,
            "channel": args.channel,
            "raw_query": rewrite_request.raw_query,
            "current_topic": rewrite_request.current_topic,
            "attempt_count": rewrite_request.attempt_count,
            "teaching_strategy": rewrite_request.teaching_strategy,
            "weak_areas_hint": rewrite_request.weak_areas_hint,
            "conversation_hint": rewrite_request.conversation_hint,
            "recall_k": max(1, int(args.recall_k)),
            "final_k": max(1, int(final_k)),
        },
        "rewrite_trace": trace,
        "top_docs": [_doc_to_debug_entry(index, doc) for index, doc in enumerate(docs, start=1)],
        "citation_confident": bool(citation_docs),
        "citations": [_citation_to_debug_entry(index, doc) for index, doc in enumerate(citation_docs, start=1)],
        "context_chars": len(context),
        "context_preview": context[:500],
    }

    serialized = json.dumps(report, ensure_ascii=False, indent=2)
    if args.json:
        print(serialized)
    else:
        print(_format_compact_report(report))

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(serialized, encoding="utf-8")
        print(f"\nSaved debug report to: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

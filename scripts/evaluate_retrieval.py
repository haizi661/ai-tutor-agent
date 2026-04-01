#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ai_tutor_agent.config import get_settings
from ai_tutor_agent.infrastructure.retrieval_eval import evaluate_queries, load_eval_examples
from ai_tutor_agent.infrastructure.retriever import LocalFileKnowledgeProvider


def parse_k_values(raw: str) -> list[int]:
    values = []
    for part in raw.split(","):
        text = part.strip()
        if not text:
            continue
        try:
            value = int(text)
        except ValueError as exc:
            raise ValueError(f"Invalid k value: {text!r}") from exc
        if value <= 0:
            raise ValueError(f"k must be positive, got: {value}")
        values.append(value)

    if not values:
        raise ValueError("At least one positive k value is required.")

    return sorted(set(values))


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline retrieval regression evaluation.")
    parser.add_argument("--eval-file", required=True, help="Path to JSON/JSONL evaluation dataset.")
    parser.add_argument("--k-values", default="1,3,5", help="Comma-separated metric cutoffs, e.g. 1,3,5")
    parser.add_argument("--recall-k", type=int, default=12, help="Recall pool size before final reranking.")
    parser.add_argument("--output", default="", help="Optional output JSON path for full report.")
    parser.add_argument(
        "--rewrite-mode",
        default="raw",
        choices=["raw", "rewrite", "both"],
        help="Evaluate raw retrieval, rewrite-enabled retrieval, or both.",
    )
    parser.add_argument(
        "--include-debug",
        action="store_true",
        help="Include per-query rewrite trace in the report when available.",
    )

    args = parser.parse_args()
    k_values = parse_k_values(args.k_values)

    examples = load_eval_examples(args.eval_file)

    settings = get_settings()
    provider = LocalFileKnowledgeProvider(settings)
    if provider.vector_store is None:
        raise RuntimeError(
            "Knowledge provider is in fallback mode (vector store unavailable). "
            "Please fix embedding/vector-store initialization before running retrieval evaluation."
        )

    if args.rewrite_mode == "both":
        report = {
            "raw": evaluate_queries(
                provider,
                examples,
                recall_k=args.recall_k,
                k_values=k_values,
                use_rewrite=False,
                include_debug=args.include_debug,
            ),
            "rewrite": evaluate_queries(
                provider,
                examples,
                recall_k=args.recall_k,
                k_values=k_values,
                use_rewrite=True,
                include_debug=args.include_debug,
            ),
        }
        print(json.dumps({"raw": report["raw"]["summary"], "rewrite": report["rewrite"]["summary"]}, ensure_ascii=False, indent=2))
    else:
        report = evaluate_queries(
            provider,
            examples,
            recall_k=args.recall_k,
            k_values=k_values,
            use_rewrite=args.rewrite_mode == "rewrite",
            include_debug=args.include_debug,
        )
        print(json.dumps(report["summary"], ensure_ascii=False, indent=2))

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Saved full report to: {output_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

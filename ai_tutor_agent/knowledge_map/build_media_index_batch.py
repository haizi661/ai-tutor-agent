from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from ai_tutor_agent.knowledge_map.config.media_index_config import MediaIndexConfig
from ai_tutor_agent.knowledge_map.media_index.media_asset_annotator import MediaAssetAnnotator
from ai_tutor_agent.knowledge_map.media_index.media_asset_scanner import MediaAssetScanner
from ai_tutor_agent.knowledge_map.media_index.media_candidate_filter import MediaCandidateFilter
from ai_tutor_agent.knowledge_map.media_index.media_node_linker import MediaNodeLinker


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch build media evidence index artifacts by chapter.")
    parser.add_argument(
        "--nodes-csv",
        type=str,
        default="data/knowledge_map_outputs/auto_control_knowledge_map_v2_nodes.csv",
        help="Knowledge graph nodes csv used for media-node linking.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/media_evidence_index",
        help="Directory for generated jsonl and summary files.",
    )
    parser.add_argument(
        "--include",
        nargs="*",
        default=[],
        help="Optional chapter directory name fragments to include.",
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        default=[],
        help="Optional chapter directory name fragments to exclude.",
    )
    parser.add_argument(
        "--skip-chapter03",
        action="store_true",
        help="Skip chapter_03 directory.",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    config = MediaIndexConfig()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    scanner = MediaAssetScanner(config=config)
    candidate_filter = MediaCandidateFilter(config=config)
    linker = MediaNodeLinker(nodes_csv_path=args.nodes_csv, config=config)
    annotator = MediaAssetAnnotator(config=config)

    docs = collect_docs(
        config.mineru_cache_root,
        include=args.include,
        exclude=args.exclude,
        skip_chapter03=args.skip_chapter03,
    )

    batch_summary: list[dict[str, object]] = []
    for doc_dir in docs:
        chapter_key = build_chapter_key(doc_dir.name)
        raw_candidates = scanner.scan_document(doc_dir)
        filtered_candidates = candidate_filter.filter_candidates(raw_candidates)
        linked_candidates = linker.link_candidates(filtered_candidates)
        annotated_assets = annotator.annotate_assets(linked_candidates, enable_visual=False)

        filtered_path = output_dir / f"{chapter_key}_filtered_candidates.jsonl"
        linked_path = output_dir / f"{chapter_key}_linked_candidates.jsonl"
        annotated_path = output_dir / f"{chapter_key}_annotated_assets.jsonl"

        candidate_filter.write_jsonl(filtered_candidates, filtered_path)
        linker.write_jsonl(linked_candidates, linked_path)
        annotator.write_jsonl(annotated_assets, annotated_path)

        batch_summary.append(
            {
                "doc_dir": doc_dir.name,
                "chapter_key": chapter_key,
                "raw_count": len(raw_candidates),
                "filtered_count": len(filtered_candidates),
                "linked_count": len(linked_candidates),
                "annotated_count": len(annotated_assets),
                "asset_type_counts": dict(Counter(item.get("asset_type", "") for item in annotated_assets)),
                "filtered_path": str(filtered_path.resolve()),
                "linked_path": str(linked_path.resolve()),
                "annotated_path": str(annotated_path.resolve()),
            }
        )

    summary_path = output_dir / "batch_summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "count": len(batch_summary),
                "chapters": batch_summary,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps({"processed": len(batch_summary), "summary_path": str(summary_path.resolve())}, ensure_ascii=False, indent=2))


def collect_docs(
    mineru_cache_root: Path,
    *,
    include: list[str],
    exclude: list[str],
    skip_chapter03: bool,
) -> list[Path]:
    docs: list[Path] = []
    include_patterns = [item.strip() for item in include if item.strip()]
    exclude_patterns = [item.strip() for item in exclude if item.strip()]

    for doc_dir in sorted(path for path in mineru_cache_root.iterdir() if path.is_dir()):
        name = doc_dir.name
        if skip_chapter03 and name.startswith("chapter_03_"):
            continue
        if include_patterns and not any(pattern in name for pattern in include_patterns):
            continue
        if exclude_patterns and any(pattern in name for pattern in exclude_patterns):
            continue
        docs.append(doc_dir)
    return docs


def build_chapter_key(doc_dir_name: str) -> str:
    match = re.match(r"^(chapter_\d+)", doc_dir_name)
    return match.group(1) if match else doc_dir_name


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from dataclasses import replace
from pathlib import Path

from ai_tutor_agent.config import get_settings
from ai_tutor_agent.knowledge_map.builders.qwen_visual_analyzer import QwenVisualAnalyzer
from ai_tutor_agent.knowledge_map.config.media_index_config import MediaIndexConfig
from ai_tutor_agent.knowledge_map.media_index.media_asset_annotator import MediaAssetAnnotator
from ai_tutor_agent.knowledge_map.media_index.media_candidate_filter import MediaCandidateFilter
from ai_tutor_agent.knowledge_map.media_index.media_asset_scanner import MediaAssetScanner
from ai_tutor_agent.knowledge_map.media_index.media_node_linker import MediaNodeLinker
from ai_tutor_agent.platform_paths import resolve_project_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Debug standalone media evidence indexing.")
    parser.add_argument("--doc", type=str, default="", help="Optional single MinerU document directory name.")
    parser.add_argument("--output", type=str, default="", help="Optional jsonl output path.")
    parser.add_argument("--limit", type=int, default=10, help="Preview item count.")
    parser.add_argument("--filter", action="store_true", help="Apply basic filtering and deduplication.")
    parser.add_argument("--link", action="store_true", help="Link media candidates to knowledge graph nodes.")
    parser.add_argument("--annotate", action="store_true", help="Annotate linked media assets with structured fields.")
    parser.add_argument("--enable-vision", action="store_true", help="Enable Qwen vision analysis during annotation.")
    parser.add_argument(
        "--mineru-cache-root",
        type=str,
        default="data/mineru_cache",
        help="Root directory that contains MinerU chapter cache directories.",
    )
    parser.add_argument(
        "--nodes-csv",
        type=str,
        default="data/knowledge_map_outputs/auto_control_knowledge_map_v2_nodes.csv",
        help="Optional node csv path used by the linker.",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    config = replace(
        MediaIndexConfig(),
        mineru_cache_root=resolve_project_path(args.mineru_cache_root),
    )
    scanner = MediaAssetScanner(config=config)
    candidate_filter = MediaCandidateFilter(config=config)
    linker = MediaNodeLinker(nodes_csv_path=resolve_project_path(args.nodes_csv), config=config) if args.link else None
    visual_analyzer = build_visual_analyzer() if args.annotate and args.enable_vision else None
    annotator = MediaAssetAnnotator(config=config, visual_analyzer=visual_analyzer) if args.annotate else None

    if args.doc:
        doc_dir = config.mineru_cache_root / args.doc
        candidates = scanner.scan_document(doc_dir)
    else:
        candidates = scanner.scan_documents()

    if args.filter:
        candidates = candidate_filter.filter_candidates(candidates)

    if linker is not None:
        candidates = linker.link_candidates(candidates)

    if annotator is not None:
        candidates = annotator.annotate_assets(candidates, enable_visual=args.enable_vision)

    output_path = None
    if args.output:
        if annotator is not None:
            output_path = annotator.write_jsonl(candidates, args.output)
        elif linker is not None:
            output_path = linker.write_jsonl(candidates, args.output)
        else:
            output_path = scanner.write_jsonl(candidates, args.output)

    print("\n=== media_candidates_summary ===")
    linked_count = sum(1 for item in candidates if item.get("anchor_node_id"))
    annotated_count = sum(1 for item in candidates if item.get("visual_type") or item.get("retrieval_keywords"))
    print(
        json.dumps(
            {
                "count": len(candidates),
                "preview_count": min(len(candidates), args.limit),
                "asset_type_counts": dict(Counter(item["asset_type"] for item in candidates)),
                "linked_count": linked_count,
                "annotated_count": annotated_count,
                "output_path": str(output_path) if output_path else "",
            },
            ensure_ascii=False,
            indent=2,
        )
    )

    print("\n=== media_candidates_preview ===")
    preview_text = json.dumps(candidates[: args.limit], ensure_ascii=True, indent=2)
    sys.stdout.write(preview_text + "\n")


def build_visual_analyzer() -> QwenVisualAnalyzer | None:
    try:
        settings = get_settings()
    except Exception:
        return None
    if not settings.qwen_api_key:
        return None
    try:
        return QwenVisualAnalyzer(api_key=settings.qwen_api_key)
    except Exception:
        return None


if __name__ == "__main__":
    main()

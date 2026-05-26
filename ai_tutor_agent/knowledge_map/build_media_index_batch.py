from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from dataclasses import replace
from pathlib import Path

from ai_tutor_agent.config import get_settings
from ai_tutor_agent.knowledge_map.builders.qwen_visual_analyzer import QwenVisualAnalyzer
from ai_tutor_agent.knowledge_map.config.media_index_config import MediaIndexConfig
from ai_tutor_agent.knowledge_map.media_index.media_asset_annotator import MediaAssetAnnotator
from ai_tutor_agent.knowledge_map.media_index.media_asset_scanner import MediaAssetScanner
from ai_tutor_agent.knowledge_map.media_index.media_candidate_filter import MediaCandidateFilter
from ai_tutor_agent.knowledge_map.media_index.media_node_linker import MediaNodeLinker
from ai_tutor_agent.knowledge_map.runtime_defaults import DEFAULT_MEDIA_EVIDENCE_INDEX_DIR
from ai_tutor_agent.platform_paths import project_relative_path, resolve_project_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Batch build media evidence index artifacts by chapter.")
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
        help="Knowledge graph nodes csv used for media-node linking.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=DEFAULT_MEDIA_EVIDENCE_INDEX_DIR,
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
    parser.add_argument(
        "--enable-vision",
        action="store_true",
        help="Enable visual LLM annotation for figure assets.",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    mineru_cache_root = resolve_project_path(args.mineru_cache_root)
    output_dir = resolve_project_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    config = replace(
        MediaIndexConfig(),
        mineru_cache_root=mineru_cache_root,
        output_dir=output_dir,
    )

    if not config.mineru_cache_root.exists():
        raise FileNotFoundError(f"MinerU 缓存目录不存在: {config.mineru_cache_root}")

    scanner = MediaAssetScanner(config=config)
    candidate_filter = MediaCandidateFilter(config=config)
    linker = MediaNodeLinker(nodes_csv_path=resolve_project_path(args.nodes_csv), config=config)
    visual_analyzer = build_visual_analyzer() if args.enable_vision else None
    annotator = MediaAssetAnnotator(config=config, visual_analyzer=visual_analyzer)

    docs = collect_docs(
        config.mineru_cache_root,
        include=args.include,
        exclude=args.exclude,
        skip_chapter03=args.skip_chapter03,
    )

    batch_summary, expected_output_names = process_documents(
        docs=docs,
        output_dir=output_dir,
        scanner=scanner,
        candidate_filter=candidate_filter,
        linker=linker,
        annotator=annotator,
        enable_visual=args.enable_vision,
    )
    summary_path = write_batch_summary(output_dir, batch_summary)
    cleanup_stale_outputs(output_dir, expected_output_names)
    print(json.dumps({"processed": len(batch_summary), "summary_path": project_relative_path(summary_path)}, ensure_ascii=False, indent=2))


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
        if not is_mineru_document_dir(doc_dir):
            continue
        if skip_chapter03 and name.startswith("chapter_03_"):
            continue
        if include_patterns and not any(pattern in name for pattern in include_patterns):
            continue
        if exclude_patterns and any(pattern in name for pattern in exclude_patterns):
            continue
        docs.append(doc_dir)
    return docs


def is_mineru_document_dir(doc_dir: Path) -> bool:
    return (doc_dir / "full.md").exists() and (
        (doc_dir / "manifest.json").exists() or (doc_dir / "metadata.json").exists()
    )


def build_chapter_key(doc_dir_name: str) -> str:
    match = re.match(r"^(chapter_\d+)", doc_dir_name)
    if match:
        return match.group(1)
    sanitized = re.sub(r"[^\w\u4e00-\u9fff.-]+", "_", doc_dir_name, flags=re.UNICODE)
    sanitized = re.sub(r"_+", "_", sanitized).strip("._")
    return sanitized or "chapter"


def cleanup_stale_outputs(output_dir: Path, expected_output_names: set[str]) -> None:
    patterns = ("*_filtered_candidates.jsonl", "*_linked_candidates.jsonl", "*_annotated_assets.jsonl")
    for pattern in patterns:
        for path in output_dir.glob(pattern):
            if path.name in expected_output_names:
                continue
            try:
                path.unlink()
            except OSError:
                # Keep build resilient when a stale file is locked by the environment.
                continue


def process_documents(
    *,
    docs: list[Path],
    output_dir: Path,
    scanner: MediaAssetScanner,
    candidate_filter: MediaCandidateFilter,
    linker: MediaNodeLinker,
    annotator: MediaAssetAnnotator,
    enable_visual: bool,
) -> tuple[list[dict[str, object]], set[str]]:
    batch_summary: list[dict[str, object]] = []
    expected_output_names: set[str] = {"batch_summary.json"}
    for doc_dir in docs:
        chapter_key = build_chapter_key(doc_dir.name)
        raw_candidates = scanner.scan_document(doc_dir)
        filtered_candidates = candidate_filter.filter_candidates(raw_candidates)
        linked_candidates = linker.link_candidates(filtered_candidates)
        annotated_assets = annotator.annotate_assets(linked_candidates, enable_visual=enable_visual)

        filtered_path = output_dir / f"{chapter_key}_filtered_candidates.jsonl"
        linked_path = output_dir / f"{chapter_key}_linked_candidates.jsonl"
        annotated_path = output_dir / f"{chapter_key}_annotated_assets.jsonl"

        candidate_filter.write_jsonl(filtered_candidates, filtered_path)
        linker.write_jsonl(linked_candidates, linked_path)
        annotator.write_jsonl(annotated_assets, annotated_path)
        expected_output_names.update({filtered_path.name, linked_path.name, annotated_path.name})

        batch_summary.append(
            {
                "doc_dir": doc_dir.name,
                "chapter_key": chapter_key,
                "raw_count": len(raw_candidates),
                "filtered_count": len(filtered_candidates),
                "linked_count": len(linked_candidates),
                "annotated_count": len(annotated_assets),
                "asset_type_counts": dict(Counter(item.get("asset_type", "") for item in annotated_assets)),
                "vision_enabled": bool(enable_visual),
                "filtered_path": project_relative_path(filtered_path),
                "linked_path": project_relative_path(linked_path),
                "annotated_path": project_relative_path(annotated_path),
            }
        )
    return batch_summary, expected_output_names


def write_batch_summary(output_dir: Path, batch_summary: list[dict[str, object]]) -> Path:
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
    return summary_path


if __name__ == "__main__":
    main()

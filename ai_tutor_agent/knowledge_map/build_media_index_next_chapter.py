from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path
from typing import Any

from ai_tutor_agent.knowledge_map.build_media_index_batch import (
    build_chapter_key,
    build_visual_analyzer,
    collect_docs,
    process_documents,
    write_batch_summary,
)
from ai_tutor_agent.knowledge_map.config.media_index_config import MediaIndexConfig
from ai_tutor_agent.knowledge_map.media_index.media_asset_annotator import MediaAssetAnnotator
from ai_tutor_agent.knowledge_map.media_index.media_asset_scanner import MediaAssetScanner
from ai_tutor_agent.knowledge_map.media_index.media_candidate_filter import MediaCandidateFilter
from ai_tutor_agent.knowledge_map.media_index.media_node_linker import MediaNodeLinker
from ai_tutor_agent.knowledge_map.runtime_defaults import DEFAULT_MEDIA_EVIDENCE_INDEX_DIR
from ai_tutor_agent.platform_paths import project_relative_path, resolve_project_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Annotate the next incomplete chapter with visual figure labels.")
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
        "--start-from",
        type=str,
        default="",
        help="Optional chapter key or doc-dir fragment to start from, for example chapter_02.",
    )
    return parser.parse_args(argv)


def main() -> None:
    args = parse_args()
    mineru_cache_root = resolve_project_path(args.mineru_cache_root)
    output_dir = resolve_project_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    config = replace(MediaIndexConfig(), mineru_cache_root=mineru_cache_root, output_dir=output_dir)

    docs = collect_docs(config.mineru_cache_root, include=[], exclude=[], skip_chapter03=False)
    target_doc = select_next_incomplete_doc(docs, output_dir=output_dir, start_from=args.start_from.strip())
    if target_doc is None:
        print(
            json.dumps(
                {
                    "status": "all_completed",
                    "output_dir": project_relative_path(output_dir),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    scanner = MediaAssetScanner(config=config)
    candidate_filter = MediaCandidateFilter(config=config)
    linker = MediaNodeLinker(nodes_csv_path=resolve_project_path(args.nodes_csv), config=config)
    visual_analyzer = build_visual_analyzer()
    annotator = MediaAssetAnnotator(config=config, visual_analyzer=visual_analyzer)

    chapter_summary, _ = process_documents(
        docs=[target_doc],
        output_dir=output_dir,
        scanner=scanner,
        candidate_filter=candidate_filter,
        linker=linker,
        annotator=annotator,
        enable_visual=True,
    )
    merged_summary = merge_batch_summary(output_dir=output_dir, fresh_chapters=chapter_summary)
    write_batch_summary(output_dir, merged_summary)

    chapter_key = build_chapter_key(target_doc.name)
    completion = inspect_chapter_completion(output_dir / f"{chapter_key}_annotated_assets.jsonl")
    print(
        json.dumps(
            {
                "status": "completed_one_chapter",
                "doc_dir": target_doc.name,
                "chapter_key": chapter_key,
                "output_dir": project_relative_path(output_dir),
                "figure_assets": completion["figure_assets"],
                "figures_with_visual_summary": completion["figures_with_visual_summary"],
                "pending_figures": completion["pending_figures"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


def select_next_incomplete_doc(
    docs: list[Path],
    *,
    output_dir: Path,
    start_from: str,
) -> Path | None:
    start_enabled = not start_from
    for doc_dir in docs:
        chapter_key = build_chapter_key(doc_dir.name)
        if not start_enabled:
            if start_from in {chapter_key, doc_dir.name} or start_from in doc_dir.name:
                start_enabled = True
            else:
                continue
        annotated_path = output_dir / f"{chapter_key}_annotated_assets.jsonl"
        status = inspect_chapter_completion(annotated_path)
        if not status["complete"]:
            return doc_dir
    return None


def inspect_chapter_completion(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {
            "complete": False,
            "figure_assets": 0,
            "figures_with_visual_summary": 0,
            "pending_figures": 0,
        }
    figure_assets = 0
    figures_with_visual_summary = 0
    with path.open("r", encoding="utf-8") as handle:
        for line_no, raw_line in enumerate(handle, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_no}: {path}") from exc
            if str(record.get("asset_type", "")).strip() != "figure":
                continue
            figure_assets += 1
            if str(record.get("visual_summary", "")).strip():
                figures_with_visual_summary += 1
    pending_figures = max(0, figure_assets - figures_with_visual_summary)
    return {
        "complete": figure_assets > 0 and pending_figures == 0,
        "figure_assets": figure_assets,
        "figures_with_visual_summary": figures_with_visual_summary,
        "pending_figures": pending_figures,
    }


def merge_batch_summary(
    *,
    output_dir: Path,
    fresh_chapters: list[dict[str, object]],
) -> list[dict[str, object]]:
    summary_path = output_dir / "batch_summary.json"
    existing: list[dict[str, object]] = []
    if summary_path.exists():
        try:
            payload = json.loads(summary_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = {}
        chapters = payload.get("chapters", []) if isinstance(payload, dict) else []
        if isinstance(chapters, list):
            existing = [item for item in chapters if isinstance(item, dict)]

    merged_by_key: dict[str, dict[str, object]] = {}
    for item in existing + fresh_chapters:
        chapter_key = str(item.get("chapter_key", "")).strip()
        if chapter_key:
            merged_by_key[chapter_key] = item
    return [merged_by_key[key] for key in sorted(merged_by_key)]


if __name__ == "__main__":
    main()

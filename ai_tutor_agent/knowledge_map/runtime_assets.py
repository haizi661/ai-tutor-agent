from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
from ai_tutor_agent.platform_paths import project_relative_path, resolve_project_path


def _count_jsonl(path: Path) -> int:
    if not path.exists():
        return 0
    count = 0
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                count += 1
    return count


def inspect_media_evidence_index(path: str | Path) -> dict[str, Any]:
    root = resolve_project_path(path)
    summary_path = root / "batch_summary.json"
    annotated_paths = sorted(root.glob("*_annotated_assets.jsonl")) if root.exists() else []
    linked_paths = sorted(root.glob("*_linked_candidates.jsonl")) if root.exists() else []
    filtered_paths = sorted(root.glob("*_filtered_candidates.jsonl")) if root.exists() else []

    summary: dict[str, Any] = {}
    if summary_path.exists():
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            summary = {"invalid_json": True}

    if isinstance(summary, dict) and summary.get("chapters"):
        summary_annotated_paths: list[Path] = []
        summary_linked_paths: list[Path] = []
        summary_filtered_paths: list[Path] = []
        for chapter in summary.get("chapters", []) or []:
            if not isinstance(chapter, dict):
                continue
            for field, bucket in (
                ("annotated_path", summary_annotated_paths),
                ("linked_path", summary_linked_paths),
                ("filtered_path", summary_filtered_paths),
            ):
                raw = str(chapter.get(field, "") or "").strip()
                if not raw:
                    continue
                candidate = resolve_project_path(raw)
                if candidate.exists() and candidate not in bucket:
                    bucket.append(candidate)
        if summary_annotated_paths:
            annotated_paths = summary_annotated_paths
        if summary_linked_paths:
            linked_paths = summary_linked_paths
        if summary_filtered_paths:
            filtered_paths = summary_filtered_paths

    annotated_count = sum(_count_jsonl(item) for item in annotated_paths)
    linked_count = sum(_count_jsonl(item) for item in linked_paths)
    filtered_count = sum(_count_jsonl(item) for item in filtered_paths)

    return {
        "path": project_relative_path(root),
        "exists": root.exists(),
        "summary_exists": summary_path.exists(),
        "summary_valid": bool(summary) and not summary.get("invalid_json"),
        "chapter_count": int(summary.get("count") or len(annotated_paths) or 0) if isinstance(summary, dict) else len(annotated_paths),
        "annotated_file_count": len(annotated_paths),
        "linked_file_count": len(linked_paths),
        "filtered_file_count": len(filtered_paths),
        "annotated_asset_count": annotated_count,
        "linked_candidate_count": linked_count,
        "filtered_candidate_count": filtered_count,
        "ok": root.exists() and summary_path.exists() and bool(annotated_paths) and annotated_count > 0,
    }


def assert_media_evidence_index_ready(path: str | Path) -> dict[str, Any]:
    report = inspect_media_evidence_index(path)
    if not report["ok"]:
        raise FileNotFoundError(
            "media_evidence_index 不可用：需要先运行 "
            "python -m ai_tutor_agent.knowledge_map.build_media_index_batch "
            "--mineru-cache-root data/mineru_cache "
            "--nodes-csv data/knowledge_map_outputs/auto_control_knowledge_map_v2_nodes.csv "
            "--output-dir data/media_evidence_index"
        )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect runtime knowledge-map assets.")
    parser.add_argument("--media-index", default="data/media_evidence_index")
    parser.add_argument("--require-media-index", action="store_true")
    args = parser.parse_args()
    report = assert_media_evidence_index_ready(args.media_index) if args.require_media_index else inspect_media_evidence_index(args.media_index)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

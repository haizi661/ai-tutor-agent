from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Iterable

from ai_tutor_agent.config import apply_network_environment, get_settings
from ai_tutor_agent.course_assets import get_course_assets
from ai_tutor_agent.infrastructure.processor import KnowledgeProcessor
from ai_tutor_agent.platform_paths import project_relative_path, resolve_project_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    assets = get_course_assets("artificial_intelligence")
    parser = argparse.ArgumentParser(
        description=(
            "Offline one-shot builder for artificial intelligence course assets. "
            "This command is intentionally not used by python main.py."
        )
    )
    parser.add_argument("--input-dir", default=assets.source_materials_dir)
    parser.add_argument("--split-manifest", default="")
    parser.add_argument("--skip-mineru", action="store_true")
    parser.add_argument("--mineru-only", action="store_true")
    parser.add_argument("--split-only", action="store_true")
    parser.add_argument("--skip-node-generation", action="store_true")
    parser.add_argument("--skip-edge-generation", action="store_true")
    parser.add_argument("--skip-media-index", action="store_true")
    parser.add_argument("--node-size", choices=["20", "200"], default="200")
    parser.add_argument("--overwrite-nodes", action="store_true")
    parser.add_argument("--overwrite-edges", action="store_true")
    parser.add_argument("--skip-edge-llm", action="store_true")
    parser.add_argument("--enable-vision", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def _find_pdfs(input_dir: Path) -> list[Path]:
    if not input_dir.exists():
        return []
    return sorted(path for path in input_dir.iterdir() if path.is_file() and path.suffix.lower() == ".pdf")


def _sanitize_name(value: str) -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff\.-]+", "_", value.strip(), flags=re.UNICODE)
    cleaned = re.sub(r"_+", "_", cleaned).strip("._")
    return cleaned or "chapter"


def _load_split_manifest(path: Path) -> dict:
    if not path.exists():
        return {"documents": []}
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Split manifest must be a JSON object: {path}")
    docs = payload.get("documents", [])
    if not isinstance(docs, list):
        raise ValueError("Split manifest field 'documents' must be a list.")
    return payload


def _resolve_split_manifest(input_dir: Path, configured: str) -> Path:
    if configured:
        return resolve_project_path(configured)
    formal = input_dir / "chapter_splits.json"
    if formal.exists():
        return formal
    example = input_dir / "chapter_splits.example.json"
    if example.exists():
        return example
    return formal


def _planned_split_outputs(input_dir: Path, manifest_path: Path) -> tuple[list[Path], set[str]]:
    manifest = _load_split_manifest(manifest_path)
    planned: list[Path] = []
    split_sources: set[str] = set()
    if not manifest.get("documents"):
        return planned, split_sources

    for doc in manifest["documents"]:
        if not isinstance(doc, dict):
            continue
        source_name = str(doc.get("source") or "").strip()
        chapters = doc.get("chapters") or []
        if not source_name or not isinstance(chapters, list):
            continue
        split_sources.add(source_name)
        for index, chapter in enumerate(chapters, start=1):
            if not isinstance(chapter, dict):
                continue
            start_page = int(chapter["start_page"])
            end_page = int(chapter["end_page"])
            chapter_id = str(chapter.get("chapter_id") or f"chapter_{index:02d}").strip()
            title = _sanitize_name(str(chapter.get("title") or chapter_id))
            planned.append(input_dir / "splits" / f"{chapter_id}_p{start_page:03d}-{end_page:03d}_{title}.pdf")
    return planned, split_sources


def _validate_split_manifest(input_dir: Path, manifest_path: Path) -> None:
    manifest = _load_split_manifest(manifest_path)
    if not manifest.get("documents"):
        return

    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PyMuPDF is required for PDF splitting. Install package 'pymupdf'.") from exc

    for doc in manifest["documents"]:
        if not isinstance(doc, dict):
            continue
        source_name = str(doc.get("source") or "").strip()
        chapters = doc.get("chapters") or []
        if not source_name or not isinstance(chapters, list):
            continue
        source_path = input_dir / source_name
        if not source_path.exists():
            raise FileNotFoundError(f"Split manifest source PDF not found: {source_path}")
        with fitz.open(source_path) as source_pdf:
            total_pages = source_pdf.page_count
        previous_end = 0
        for chapter in chapters:
            start_page = int(chapter["start_page"])
            end_page = int(chapter["end_page"])
            if start_page < 1 or end_page < start_page or end_page > total_pages:
                raise ValueError(
                    f"Invalid page range for {source_name}: {start_page}-{end_page}, total={total_pages}"
                )
            if start_page <= previous_end:
                raise ValueError(
                    f"Overlapping or unsorted page range for {source_name}: {start_page}-{end_page}"
                )
            previous_end = end_page


def _split_pdf_by_manifest(input_dir: Path, manifest_path: Path) -> tuple[list[Path], set[str]]:
    manifest = _load_split_manifest(manifest_path)
    split_docs: list[Path] = []
    split_sources: set[str] = set()
    if not manifest.get("documents"):
        return split_docs, split_sources

    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PyMuPDF is required for PDF splitting. Install package 'pymupdf'.") from exc

    output_root = input_dir / "splits"
    output_root.mkdir(parents=True, exist_ok=True)

    for doc in manifest["documents"]:
        if not isinstance(doc, dict):
            continue
        source_name = str(doc.get("source") or "").strip()
        chapters = doc.get("chapters") or []
        if not source_name or not isinstance(chapters, list):
            continue
        source_path = input_dir / source_name
        if not source_path.exists():
            raise FileNotFoundError(f"Split manifest source PDF not found: {source_path}")

        split_sources.add(source_path.name)
        with fitz.open(source_path) as source_pdf:
            total_pages = source_pdf.page_count
            for index, chapter in enumerate(chapters, start=1):
                if not isinstance(chapter, dict):
                    continue
                start_page = int(chapter["start_page"])
                end_page = int(chapter["end_page"])
                if start_page < 1 or end_page < start_page or end_page > total_pages:
                    raise ValueError(
                        f"Invalid page range for {source_name}: {start_page}-{end_page}, total={total_pages}"
                    )
                chapter_id = str(chapter.get("chapter_id") or f"chapter_{index:02d}").strip()
                title = _sanitize_name(str(chapter.get("title") or chapter_id))
                output_name = f"{chapter_id}_p{start_page:03d}-{end_page:03d}_{title}.pdf"
                output_path = output_root / output_name

                target_pdf = fitz.open()
                try:
                    target_pdf.insert_pdf(source_pdf, from_page=start_page - 1, to_page=end_page - 1)
                    target_pdf.save(output_path)
                finally:
                    target_pdf.close()

                split_docs.append(output_path)
                print(f"[AI assets] Split PDF: {source_path.name} p{start_page}-{end_page} -> {output_path.name}")

    return split_docs, split_sources


def _run_module_main(module_name: str, args: Iterable[str]) -> None:
    module = importlib.import_module(module_name)
    old_argv = sys.argv[:]
    try:
        sys.argv = [module_name, *list(args)]
        module.main()
    finally:
        sys.argv = old_argv


def _process_mineru_pdfs(pdf_paths: list[Path], cache_root: Path) -> list[dict[str, str]]:
    settings = get_settings()
    apply_network_environment(settings)
    if not settings.mineru_api_token:
        raise RuntimeError("MINERU_API_TOKEN is required for the one-shot MinerU build command.")

    cache_root.mkdir(parents=True, exist_ok=True)
    processor = KnowledgeProcessor(
        settings.mineru_api_token,
        proxy_mode=settings.mineru_proxy_mode,
        http_proxy=settings.mineru_http_proxy,
        https_proxy=settings.mineru_https_proxy,
        connect_timeout_seconds=settings.mineru_connect_timeout_seconds,
        status_file_path=str(cache_root / "mineru_runtime_state.json"),
        cache_dir=str(cache_root),
        public_dns_bypass_enabled=settings.mineru_public_dns_bypass_enabled,
        public_dns_server=settings.mineru_public_dns_server,
        public_dns_port=settings.mineru_public_dns_port,
        public_dns_hosts=settings.mineru_public_dns_hosts,
    )

    results: list[dict[str, str]] = []
    for pdf_path in pdf_paths:
        print(f"[AI assets] MinerU processing: {project_relative_path(pdf_path)}")
        markdown = processor.parse_pdf_to_md(str(pdf_path))
        results.append({
            "pdf": project_relative_path(pdf_path),
            "markdown_chars": str(len(markdown)),
        })
    return results


def _build_media_index(*, mineru_cache_root: Path, nodes_csv: Path, output_dir: Path, enable_vision: bool) -> None:
    args = [
        "--mineru-cache-root",
        str(mineru_cache_root),
        "--nodes-csv",
        str(nodes_csv),
        "--output-dir",
        str(output_dir),
    ]
    if enable_vision:
        args.append("--enable-vision")
    _run_module_main("ai_tutor_agent.knowledge_map.build_media_index_batch", args)


def _write_manifest(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    assets = get_course_assets("artificial_intelligence")
    input_dir = resolve_project_path(args.input_dir)
    split_manifest = _resolve_split_manifest(input_dir, args.split_manifest)
    mineru_cache_root = assets.resolve("mineru_cache_root")
    nodes_csv = assets.resolve("nodes_csv_path")
    edges_csv = assets.resolve("edges_csv_path")
    media_index_dir = assets.resolve("media_evidence_index_dir")
    manifest_path = nodes_csv.parent / "ai_course_asset_build_manifest.json"

    input_dir.mkdir(parents=True, exist_ok=True)
    nodes_csv.parent.mkdir(parents=True, exist_ok=True)
    media_index_dir.mkdir(parents=True, exist_ok=True)

    _validate_split_manifest(input_dir, split_manifest)
    planned_split_pdf_paths, split_source_names = _planned_split_outputs(input_dir, split_manifest)
    split_pdf_paths: list[Path] = []
    if not args.dry_run:
        split_pdf_paths, split_source_names = _split_pdf_by_manifest(input_dir, split_manifest)
    pdf_paths = [
        path
        for path in _find_pdfs(input_dir)
        if path.name not in split_source_names
    ] + (planned_split_pdf_paths if args.dry_run else split_pdf_paths)
    print("[AI assets] This is an offline one-shot command. python main.py will not run MinerU.")
    print(f"[AI assets] PDF input dir: {project_relative_path(input_dir)}")
    print(f"[AI assets] Split manifest: {project_relative_path(split_manifest)}")
    print(f"[AI assets] MinerU cache: {project_relative_path(mineru_cache_root)}")
    print(f"[AI assets] Nodes CSV: {project_relative_path(nodes_csv)}")
    print(f"[AI assets] Edges CSV: {project_relative_path(edges_csv)}")
    print(f"[AI assets] Media index: {project_relative_path(media_index_dir)}")
    print(f"[AI assets] Found PDFs: {len(pdf_paths)}")

    if args.dry_run:
        for pdf_path in pdf_paths:
            print(f"  - {project_relative_path(pdf_path)}")
        return

    if args.split_only:
        for pdf_path in split_pdf_paths:
            print(f"  - {project_relative_path(pdf_path)}")
        return

    mineru_results: list[dict[str, str]] = []
    if not args.skip_mineru:
        if not pdf_paths:
            raise FileNotFoundError(f"No PDF files found in {project_relative_path(input_dir)}")
        mineru_results = _process_mineru_pdfs(pdf_paths, mineru_cache_root)

    if args.mineru_only:
        _write_manifest(
            manifest_path,
            {
                "course_id": assets.course_id,
                "built_at": datetime.now().isoformat(timespec="seconds"),
                "mode": "mineru_only",
                "pdfs": mineru_results,
            },
        )
        return

    if not args.skip_node_generation:
        node_args = ["--size", args.node_size]
        if args.overwrite_nodes:
            node_args.append("--overwrite")
        _run_module_main("ai_tutor_agent.ai_learning_path.build_ai_nodes_from_seed", node_args)

    if not args.skip_edge_generation:
        edge_args = []
        if args.overwrite_edges:
            edge_args.append("--overwrite")
        if args.skip_edge_llm:
            edge_args.append("--skip-llm")
        _run_module_main("ai_tutor_agent.ai_learning_path.build_ai_edges_from_nodes", edge_args)

    if not args.skip_media_index:
        if not nodes_csv.exists():
            raise FileNotFoundError(f"AI nodes CSV does not exist: {project_relative_path(nodes_csv)}")
        _build_media_index(
            mineru_cache_root=mineru_cache_root,
            nodes_csv=nodes_csv,
            output_dir=media_index_dir,
            enable_vision=args.enable_vision,
        )

    _write_manifest(
        manifest_path,
        {
            "course_id": assets.course_id,
            "built_at": datetime.now().isoformat(timespec="seconds"),
            "mode": "full",
            "input_dir": project_relative_path(input_dir),
            "split_manifest": project_relative_path(split_manifest),
            "mineru_cache_root": project_relative_path(mineru_cache_root),
            "nodes_csv": project_relative_path(nodes_csv),
            "edges_csv": project_relative_path(edges_csv),
            "media_index_dir": project_relative_path(media_index_dir),
            "pdfs": mineru_results,
            "notes": "Generated by offline command; runtime python main.py only reads the produced assets.",
        },
    )
    print(f"[AI assets] Build manifest: {project_relative_path(manifest_path)}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import os
import webbrowser

from kg_builder_standalone.pipeline import PDFKnowledgeGraphBuilder


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Debug tool for standalone knowledge graph generation")
    parser.add_argument("--pdf", required=True, help="Path to textbook PDF")
    parser.add_argument("--out", default="kg_builder_standalone/outputs", help="Output directory")
    parser.add_argument("--name", default="debug_course_graph", help="Graph file prefix")
    parser.add_argument("--min-nodes", type=int, default=50)
    parser.add_argument("--max-nodes", type=int, default=100)
    parser.add_argument("--top-per-chapter", type=int, default=28)
    parser.add_argument("--open", action="store_true", help="Open generated HTML in browser")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not os.path.exists(args.pdf):
        raise FileNotFoundError(f"PDF not found: {args.pdf}")

    builder = PDFKnowledgeGraphBuilder(
        min_nodes=args.min_nodes,
        max_nodes=args.max_nodes,
        top_terms_per_chapter=args.top_per_chapter,
    )

    print("[debug] start generating candidate graph...")
    nodes_df, edges_df, metadata = builder.generate(args.pdf)
    print(f"[debug] metadata: {metadata}")
    print(f"[debug] nodes: {len(nodes_df)}, edges: {len(edges_df)}")

    print("[debug] finalizing graph with current candidates (no manual filtering)...")
    paths = builder.finalize(nodes_df, edges_df, output_dir=args.out, graph_name=args.name)
    for key, value in paths.items():
        print(f"[debug] {key}: {value}")

    print("[debug] node preview:")
    print(nodes_df.head(10).to_string(index=False))
    print("[debug] edge preview:")
    print(edges_df.head(10).to_string(index=False))

    if args.open:
        webbrowser.open(paths["html"])


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import json
import os
import webbrowser

from kg_builder_standalone.pipeline import PDFKnowledgeGraphBuilder


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Debug tool: textbook PDF + outline PDF -> weighted knowledge graph"
    )
    parser.add_argument(
        "--textbook-pdf",
        default="data/knowledge/配套资料1：自动控制原理（第八版） (胡寿松、姜斌、张绍杰) .pdf",
        help="Path to textbook PDF",
    )
    parser.add_argument(
        "--outline-pdf",
        default="data/knowledge/自动控制原理课程大纲-上海交通大学.pdf",
        help="Path to course outline PDF",
    )
    parser.add_argument("--out", default="kg_builder_standalone/outputs", help="Output directory")
    parser.add_argument("--name", default="weighted_course_graph", help="Graph file prefix")
    parser.add_argument("--min-nodes", type=int, default=50)
    parser.add_argument("--max-nodes", type=int, default=100)
    parser.add_argument("--top-per-chapter", type=int, default=28)
    parser.add_argument("--base-weight-col", default="confidence", help="Base weight column in nodes table")
    parser.add_argument("--open", action="store_true", help="Open generated HTML in browser")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not os.path.exists(args.textbook_pdf):
        raise FileNotFoundError(f"Textbook PDF not found: {args.textbook_pdf}")
    if not os.path.exists(args.outline_pdf):
        raise FileNotFoundError(f"Outline PDF not found: {args.outline_pdf}")

    builder = PDFKnowledgeGraphBuilder(
        min_nodes=args.min_nodes,
        max_nodes=args.max_nodes,
        top_terms_per_chapter=args.top_per_chapter,
    )

    print("[weighted-debug] step1/3 generate graph candidates from textbook...")
    nodes_df, edges_df, metadata = builder.generate(args.textbook_pdf)
    print(f"[weighted-debug] metadata: {metadata}")
    print(f"[weighted-debug] nodes={len(nodes_df)}, edges={len(edges_df)}")

    print("[weighted-debug] step2/3 annotate node weights from outline...")
    weighted_nodes_df, weight_summary = builder.annotate_node_weights_from_outline(
        nodes_df,
        args.outline_pdf,
        base_weight_col=args.base_weight_col,
    )
    print(f"[weighted-debug] weight_summary: {weight_summary}")

    print("[weighted-debug] step3/3 finalize weighted graph outputs...")
    paths = builder.finalize(weighted_nodes_df, edges_df, output_dir=args.out, graph_name=args.name)
    for key, value in paths.items():
        print(f"[weighted-debug] {key}: {value}")

    summary_path = os.path.join(args.out, f"{args.name}_weight_summary.json")
    with open(summary_path, "w", encoding="utf-8") as fh:
        json.dump(weight_summary, fh, ensure_ascii=False, indent=2)
    print(f"[weighted-debug] weight_summary_json: {summary_path}")

    preview_cols = [
        col
        for col in ["node_id", "label", "confidence", "weight", "weight_bonus", "outline_hits", "outline_keywords"]
        if col in weighted_nodes_df.columns
    ]
    if preview_cols:
        print("[weighted-debug] top weighted nodes:")
        top_df = weighted_nodes_df.sort_values(by=["weight_bonus", "weight"], ascending=False).head(15)
        print(top_df[preview_cols].to_string(index=False))

    if args.open:
        webbrowser.open(paths["html"])


if __name__ == "__main__":
    main()

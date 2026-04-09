from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()

from ai_tutor_agent.knowledge_map.pipeline_v2 import KnowledgeMapPipelineV2

def main() -> None:
    pipeline = KnowledgeMapPipelineV2()
    nodes_df, edges_df, metadata = pipeline.generate()

    print("=== metadata ===")
    print(metadata)

    print("\n=== nodes preview ===")
    preview_cols = [
        "node_id",
        "name",
        "chapter",
        "level",
        "page_refs",
        "source_type",
    ]
    print(nodes_df[preview_cols].head(20).to_string(index=False))

    print("\n=== refined page preview ===")
    for _, row in nodes_df.head(8).iterrows():
        extra = row.get("extra", {}) or {}
        print(
            f"{row['node_id']} | {row['name']} | "
            f"anchor_page={extra.get('anchor_page')} | "
            f"page_refs_refined={extra.get('page_refs_refined', [])}"
        )

    print("\n=== content preview ===")
    for _, row in nodes_df.head(5).iterrows():
        extra = row.get("extra", {}) or {}
        print(f"\n[{row['node_id']}] {row['name']}")
        print("anchor_page:", extra.get("anchor_page"))
        print("page_refs_refined:", extra.get("page_refs_refined", []))
        print("summary:", row.get("summary", ""))
        print("explanation_teacher_style:", row.get("explanation_teacher_style", ""))
        print("formulas:", row.get("formulas", []))
        print("examples:", row.get("examples", []))

    print("\n=== edges preview ===")
    print(edges_df[["edge_id", "source", "target", "relation", "relation_label"]].head(20).to_string(index=False))

    print("\n=== KM020 check ===")
    target_df = nodes_df[nodes_df["node_id"] == "KM020"]
    if not target_df.empty:
        row = target_df.iloc[0]
        extra = row.get("extra", {}) or {}
        print("name:", row["name"])
        print("page_refs:", row.get("page_refs", []))
        print("anchor_page:", extra.get("anchor_page"))
        print("page_refs_refined:", extra.get("page_refs_refined", []))
        print("summary:", row.get("summary", ""))
        print("explanation_teacher_style:", row.get("explanation_teacher_style", ""))
        print("formulas:", row.get("formulas", []))
        print("examples:", row.get("examples", []))
        
    paths = pipeline.finalize(
        nodes_df=nodes_df,
        edges_df=edges_df,
        output_dir="data/knowledge_map_outputs",
        graph_name="auto_control_knowledge_map_v2",
    )

    print("\n=== output files ===")
    for k, v in paths.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
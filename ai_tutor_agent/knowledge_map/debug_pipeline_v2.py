from __future__ import annotations

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
        "core_concepts",
        "source_type",
    ]
    print(nodes_df[preview_cols].head(20).to_string(index=False))
    print("\n=== content preview ===")
    for _, row in nodes_df.head(5).iterrows():
        print(f"\n[{row['node_id']}] {row['name']}")
        print("summary:", row.get("summary", ""))
        print("explanation_raw:", row.get("explanation_raw", ""))
        print("key_points:", row.get("key_points", []))
    print("\n=== edges preview ===")
    print(edges_df[["edge_id", "source", "target", "relation", "relation_label"]].head(20).to_string(index=False))

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
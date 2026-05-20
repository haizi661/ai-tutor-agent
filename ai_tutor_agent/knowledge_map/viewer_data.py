from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _node_id(node: dict[str, Any]) -> str:
    return str(node.get("id") or node.get("node_id") or "").strip()


def _node_title(node: dict[str, Any]) -> str:
    return str(node.get("title") or node.get("name") or _node_id(node)).strip()


def _viewer_markdown_path(node: dict[str, Any]) -> str:
    value = str(node.get("content_markdown_file") or "").strip()
    if not value:
        return ""
    marker = "source-notes/"
    if marker in value:
        return "../source-notes/" + value.split(marker, 1)[1]
    return value


def _build_meta(graph_payload: dict[str, Any], nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    source_meta = _as_dict(graph_payload.get("meta"))
    return {
        "dataset": source_meta.get("dataset", "A2 Control Theory Knowledge Graph"),
        "generated_at": source_meta.get("generated_at"),
        "note_count": len(nodes),
        "internal_edge_count": len(edges),
        "out_of_scope_reference_count": source_meta.get("out_of_scope_reference_count", 0),
        "missing_reference_count": source_meta.get("missing_reference_count", 0),
        "subgraphs": source_meta.get("subgraphs", {}),
        "root_notes": source_meta.get("root_notes", []),
    }


def _build_viewer_node(node: dict[str, Any], inbound_count: int, outbound_count: int) -> dict[str, Any]:
    node_id = _node_id(node)
    title = _node_title(node)
    degree = inbound_count + outbound_count
    return {
        "id": node_id,
        "name": title,
        "category": node.get("category") or "未分类",
        "subcategory": node.get("subcategory") or node.get("category") or "未分类",
        "size": max(4, min(20, 4 + degree * 2)),
        "summary": node.get("summary") or "",
        "pinned": bool(node.get("pinned")),
    }


def _build_viewer_note(node: dict[str, Any]) -> dict[str, Any]:
    node_id = _node_id(node)
    internal_links = _as_list(node.get("outbound_internal_ids"))
    inbound_links = _as_list(node.get("inbound_internal_ids"))
    return {
        "id": node_id,
        "title": _node_title(node),
        "category": node.get("category") or "未分类",
        "subcategory": node.get("subcategory") or node.get("category") or "未分类",
        "summary": node.get("summary") or "",
        "tags": _as_list(node.get("tags")),
        "aliases": _as_list(node.get("aliases")),
        "terminology": node.get("terminology") or "",
        "headings": _as_list(node.get("headings")),
        "pinned": bool(node.get("pinned")),
        "level": node.get("level"),
        "created": node.get("created"),
        "updated": node.get("updated"),
        "dg_path": node.get("dg_path") or "",
        "permalink": node.get("permalink") or "",
        "source_path": node.get("source_path") or "",
        "viewer_markdown_path": _viewer_markdown_path(node),
        "content_excerpt": node.get("content_excerpt") or node.get("summary") or "",
        "internal_links": internal_links,
        "inbound_links": inbound_links,
        "out_of_scope_links": _as_list(node.get("outbound_out_of_scope_links")),
        "missing_links": _as_list(node.get("outbound_missing_links")),
        "prerequisites": _as_list(node.get("prerequisites")),
        "neighbors": _as_list(node.get("neighbors")),
        "learning_objectives": _as_list(node.get("learning_objectives")),
        "must_know": _as_list(node.get("must_know")),
        "common_errors": _as_list(node.get("common_errors")),
        "target_mastery_level": node.get("target_mastery_level") or "",
        "difficulty": node.get("difficulty") or "",
    }


def _build_viewer_link(edge: dict[str, Any]) -> dict[str, Any]:
    return {
        "source": edge.get("source") or edge.get("from") or edge.get("source_id"),
        "target": edge.get("target") or edge.get("to") or edge.get("target_id"),
        "weight": edge.get("weight", 1),
        "relation_label": edge.get("relation_label") or "",
    }


def build_viewer_data(graph_payload: dict[str, Any]) -> dict[str, Any]:
    """Build the 2026-04-27-style static viewer payload from graph.json.

    The viewer is an archived Graph A / old A2 projection helper. It keeps only
    the fields consumed by the archived viewer while preserving historical
    teaching fields for provenance checks.
    """

    nodes = [node for node in _as_list(graph_payload.get("nodes")) if _node_id(node)]
    edges = [edge for edge in _as_list(graph_payload.get("edges") or graph_payload.get("links")) if edge.get("source") and edge.get("target")]

    inbound: dict[str, int] = {_node_id(node): 0 for node in nodes}
    outbound: dict[str, int] = {_node_id(node): 0 for node in nodes}
    for edge in edges:
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        if source in outbound:
            outbound[source] += 1
        if target in inbound:
            inbound[target] += 1

    return {
        "meta": _build_meta(graph_payload, nodes, edges),
        "graph": {
            "nodes": [_build_viewer_node(node, inbound.get(_node_id(node), 0), outbound.get(_node_id(node), 0)) for node in nodes],
            "links": [_build_viewer_link(edge) for edge in edges],
        },
        "notes": {_node_id(node): _build_viewer_note(node) for node in nodes},
    }


def write_viewer_data_js(graph_json_path: str | Path, output_path: str | Path) -> dict[str, Any]:
    graph_path = Path(graph_json_path)
    payload = json.loads(graph_path.read_text(encoding="utf-8-sig"))
    viewer_data = build_viewer_data(payload)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    rendered = "window.A2_GRAPH_VIEWER_DATA = " + json.dumps(viewer_data, ensure_ascii=False, indent=2) + ";\n"
    output.write_text(rendered, encoding="utf-8")
    return viewer_data


def main() -> None:
    parser = argparse.ArgumentParser(description="Build archived Graph A / A2 viewer data.js from graph.json.")
    parser.add_argument("--graph-json", default="docs/archive/a2-control-theory/graph.json")
    parser.add_argument("--output", default="docs/archive/a2-control-theory/viewer/data.js")
    args = parser.parse_args()
    data = write_viewer_data_js(args.graph_json, args.output)
    print(
        json.dumps(
            {
                "output": args.output,
                "note_count": data["meta"]["note_count"],
                "internal_edge_count": data["meta"]["internal_edge_count"],
                "generated_at": data["meta"].get("generated_at"),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()

from __future__ import annotations

import ast
import csv
import json
from pathlib import Path
from typing import Any


GRAPH_REFERENCE_FIELDS = (
    "prerequisite_nodes",
    "next_nodes",
    "related_nodes",
    "application_nodes",
    "recommended_next_nodes",
    "prerequisites",
    "neighbors",
    "outbound_internal_ids",
    "inbound_internal_ids",
)

REQUIRED_NODE_FIELDS = ("node_id", "name", "core_concepts", "key_points")
EDGE_SOURCE_FIELDS = ("source", "from", "source_id")
EDGE_TARGET_FIELDS = ("target", "to", "target_id")


def _safe_literal(value: Any, default: Any) -> Any:
    if isinstance(value, (list, dict)):
        return value
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    try:
        return ast.literal_eval(text)
    except Exception:
        return default


def _string_list(value: Any) -> list[str]:
    parsed = _safe_literal(value, value)
    if isinstance(parsed, list):
        return [str(item).strip() for item in parsed if str(item).strip()]
    return []


def _read_csv(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def load_graph_records(
    *,
    nodes_csv_path: str | Path | None = None,
    edges_csv_path: str | Path | None = None,
    graph_json_path: str | Path | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if graph_json_path is not None:
        payload = json.loads(Path(graph_json_path).read_text(encoding="utf-8-sig"))
        nodes = list(payload.get("nodes") or [])
        edges = list(payload.get("edges") or payload.get("links") or [])
        return nodes, edges

    if nodes_csv_path is None or edges_csv_path is None:
        raise ValueError("Either graph_json_path or both nodes_csv_path and edges_csv_path are required.")
    return _read_csv(nodes_csv_path), _read_csv(edges_csv_path)


def _node_id(node: dict[str, Any]) -> str:
    return str(node.get("node_id") or node.get("id") or "").strip()


def _node_title(node: dict[str, Any]) -> str:
    return str(node.get("name") or node.get("title") or _node_id(node)).strip()


def _edge_endpoint(edge: dict[str, Any], candidates: tuple[str, ...]) -> str:
    for field in candidates:
        value = str(edge.get(field) or "").strip()
        if value:
            return value
    return ""


def _external_reference_ids(external_references: Any = None, external_reference_ids: set[str] | None = None) -> set[str]:
    ids = {str(item).strip() for item in (external_reference_ids or set()) if str(item).strip()}
    if isinstance(external_references, list):
        for item in external_references:
            if isinstance(item, dict):
                target = str(item.get("target") or item.get("id") or item.get("name") or "").strip()
                if target:
                    ids.add(target)
            else:
                target = str(item).strip()
                if target:
                    ids.add(target)
    elif isinstance(external_references, dict):
        for key, value in external_references.items():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        target = str(item.get("target") or item.get("id") or item.get("name") or "").strip()
                    else:
                        target = str(item).strip()
                    if target:
                        ids.add(target)
            elif isinstance(value, dict):
                target = str(value.get("target") or value.get("id") or value.get("name") or key or "").strip()
                if target:
                    ids.add(target)
            else:
                target = str(value or key or "").strip()
                if target:
                    ids.add(target)
    return ids


def audit_knowledge_graph(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    *,
    require_explanation_fields: bool = True,
    external_references: Any = None,
    external_reference_ids: set[str] | None = None,
) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    declared_external_ids = _external_reference_ids(external_references, external_reference_ids)
    node_ids: list[str] = []
    seen: set[str] = set()
    duplicate_node_ids: set[str] = set()

    for index, node in enumerate(nodes):
        node_id = _node_id(node)
        if not node_id:
            issues.append({"kind": "missing_node_id", "index": index})
            continue
        node_ids.append(node_id)
        if node_id in seen:
            duplicate_node_ids.add(node_id)
            issues.append({"kind": "duplicate_node_id", "node_id": node_id})
        seen.add(node_id)

    node_id_set = set(node_ids)
    edge_pairs: set[tuple[str, str]] = set()
    inbound: dict[str, int] = {node_id: 0 for node_id in node_id_set}
    outbound: dict[str, int] = {node_id: 0 for node_id in node_id_set}

    for index, edge in enumerate(edges):
        source = _edge_endpoint(edge, EDGE_SOURCE_FIELDS)
        target = _edge_endpoint(edge, EDGE_TARGET_FIELDS)
        if not source or not target:
            issues.append({"kind": "edge_missing_endpoint", "index": index, "source": source, "target": target})
            continue
        if source not in node_id_set:
            issues.append({"kind": "dangling_edge_source", "edge_id": edge.get("edge_id", index), "source": source})
        if target not in node_id_set:
            issues.append({"kind": "dangling_edge_target", "edge_id": edge.get("edge_id", index), "target": target})
        if source in node_id_set and target in node_id_set:
            edge_pairs.add((source, target))
            outbound[source] = outbound.get(source, 0) + 1
            inbound[target] = inbound.get(target, 0) + 1

    for node in nodes:
        node_id = _node_id(node)
        if not node_id:
            continue
        if not _node_title(node):
            issues.append({"kind": "missing_title", "node_id": node_id})
        if require_explanation_fields:
            has_concepts = bool(_string_list(node.get("core_concepts")) or _string_list(node.get("must_know")))
            has_points = bool(_string_list(node.get("key_points")) or _string_list(node.get("learning_objectives")))
            has_summary = bool(str(node.get("summary") or "").strip())
            if not has_concepts:
                issues.append({"kind": "missing_core_concepts", "node_id": node_id})
            if not has_points:
                issues.append({"kind": "missing_key_points", "node_id": node_id})
            if not has_summary:
                issues.append({"kind": "missing_summary", "node_id": node_id})

        for field in GRAPH_REFERENCE_FIELDS:
            for ref in _string_list(node.get(field)):
                if ref in node_id_set:
                    outbound[node_id] = outbound.get(node_id, 0) + 1
                    inbound[ref] = inbound.get(ref, 0) + 1
                    continue
                if ref in declared_external_ids:
                    issues.append({"kind": "external_node_reference", "node_id": node_id, "field": field, "target": ref})
                    continue
                issues.append({"kind": "dangling_node_reference", "node_id": node_id, "field": field, "target": ref})

    isolated_nodes = sorted(node_id for node_id in node_id_set if inbound.get(node_id, 0) == 0 and outbound.get(node_id, 0) == 0)
    for node_id in isolated_nodes:
        issues.append({"kind": "isolated_node", "node_id": node_id})

    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "duplicate_node_ids": sorted(duplicate_node_ids),
        "isolated_nodes": isolated_nodes,
        "issue_count": len(issues),
        "issues": issues,
    }


def assert_knowledge_graph_integrity(
    *,
    nodes_csv_path: str | Path | None = None,
    edges_csv_path: str | Path | None = None,
    graph_json_path: str | Path | None = None,
    allow_isolated_nodes: bool = False,
    require_explanation_fields: bool = True,
    allow_external_references: bool = True,
) -> dict[str, Any]:
    nodes, edges = load_graph_records(
        nodes_csv_path=nodes_csv_path,
        edges_csv_path=edges_csv_path,
        graph_json_path=graph_json_path,
    )
    external_references = None
    if graph_json_path is not None:
        payload = json.loads(Path(graph_json_path).read_text(encoding="utf-8-sig"))
        external_references = payload.get("external_references")
    report = audit_knowledge_graph(
        nodes,
        edges,
        require_explanation_fields=require_explanation_fields,
        external_references=external_references,
    )
    blocking = [
        issue
        for issue in report["issues"]
        if (allow_isolated_nodes or issue.get("kind") != "isolated_node")
        and (allow_external_references or issue.get("kind") != "external_node_reference")
    ]
    if blocking:
        preview = "; ".join(str(item) for item in blocking[:10])
        raise AssertionError(f"Knowledge graph integrity check failed with {len(blocking)} blocking issues: {preview}")
    return report

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from ai_tutor_agent.knowledge_map.graph_integrity import (
    assert_knowledge_graph_integrity,
    audit_knowledge_graph,
    load_graph_records,
)
from ai_tutor_agent.knowledge_map.runtime_assets import assert_media_evidence_index_ready, inspect_media_evidence_index
from ai_tutor_agent.knowledge_map.viewer_data import build_viewer_data, write_viewer_data_js

FIXTURE_NODES_CSV = Path("tests/fixtures/knowledge_map_outputs/auto_control_knowledge_map_v2_nodes.csv")
FIXTURE_EDGES_CSV = Path("tests/fixtures/knowledge_map_outputs/auto_control_knowledge_map_v2_edges.csv")
RUNTIME_NODES_CSV = Path("data/knowledge_map_outputs/auto_control_knowledge_map_v2_nodes.csv")
RUNTIME_EDGES_CSV = Path("data/knowledge_map_outputs/auto_control_knowledge_map_v2_edges.csv")
ARCHIVED_A_GRAPH_JSON = Path("docs/archive/a2-control-theory/graph.json")
ARCHIVED_A_VIEWER_DATA_JS = Path("docs/archive/a2-control-theory/viewer/data.js")


def test_fixture_graph_has_no_dangling_edges_or_node_references():
    report = assert_knowledge_graph_integrity(
        nodes_csv_path=FIXTURE_NODES_CSV,
        edges_csv_path=FIXTURE_EDGES_CSV,
    )

    assert report["node_count"] >= 4
    assert report["edge_count"] >= 4
    assert report["issue_count"] == 0


def test_runtime_main_learning_graph_uses_2026_04_27_b_assets():
    assert RUNTIME_NODES_CSV.exists()
    assert RUNTIME_EDGES_CSV.exists()

    nodes, edges = load_graph_records(
        nodes_csv_path=RUNTIME_NODES_CSV,
        edges_csv_path=RUNTIME_EDGES_CSV,
    )
    report = audit_knowledge_graph(nodes, edges, require_explanation_fields=False)

    assert report["node_count"] >= 40
    assert report["edge_count"] >= 40
    blocking = [issue for issue in report["issues"] if issue["kind"] not in {"isolated_node"}]
    assert blocking == []


def test_integrity_audit_detects_dangling_references_and_missing_explanations():
    nodes = [
        {
            "node_id": "KM001",
            "name": "稳定性基础",
            "summary": "稳定性基础概念。",
            "core_concepts": ["稳定性"],
            "key_points": ["判断响应是否收敛"],
            "recommended_next_nodes": ["KM999"],
        },
        {
            "node_id": "KM002",
            "name": "空节点",
            "summary": "",
            "core_concepts": [],
            "key_points": [],
        },
    ]
    edges = [{"edge_id": "E001", "source": "KM001", "target": "KM404"}]

    report = audit_knowledge_graph(nodes, edges)
    kinds = {issue["kind"] for issue in report["issues"]}

    assert "dangling_edge_target" in kinds
    assert "dangling_node_reference" in kinds
    assert "missing_core_concepts" in kinds
    assert "missing_key_points" in kinds
    assert "missing_summary" in kinds


def test_integrity_audit_allows_declared_external_references_without_calling_them_dangling():
    nodes = [
        {
            "node_id": "KM001",
            "name": "稳定性基础",
            "summary": "稳定性基础概念。",
            "core_concepts": ["稳定性"],
            "key_points": ["判断响应是否收敛"],
            "prerequisites": ["拉普拉斯变换", "KM002"],
        },
        {
            "node_id": "KM002",
            "name": "根轨迹",
            "summary": "根轨迹。",
            "core_concepts": ["闭环极点"],
            "key_points": ["判断轨迹变化"],
        },
    ]
    edges = [{"edge_id": "E001", "source": "KM001", "target": "KM002"}]

    report = audit_knowledge_graph(
        nodes,
        edges,
        external_reference_ids={"拉普拉斯变换"},
    )

    assert not any(
        issue["kind"] == "dangling_node_reference" and issue["target"] == "拉普拉斯变换"
        for issue in report["issues"]
    )
    assert any(
        issue["kind"] == "external_node_reference" and issue["target"] == "拉普拉斯变换"
        for issue in report["issues"]
    )


def test_graph_integrity_assertion_raises_with_actionable_preview():
    nodes = [
        {
            "node_id": "KM001",
            "name": "稳定性基础",
            "summary": "稳定性基础概念。",
            "core_concepts": ["稳定性"],
            "key_points": ["判断响应是否收敛"],
            "recommended_next_nodes": ["KM999"],
        }
    ]
    edges = []

    report = audit_knowledge_graph(nodes, edges)
    assert report["issue_count"] >= 1
    with pytest.raises(AssertionError, match="Knowledge graph integrity check failed"):
        if report["issues"]:
            raise AssertionError(f"Knowledge graph integrity check failed with {report['issue_count']} blocking issues: {report['issues'][0]}")


def test_archived_a2_control_theory_graph_json_is_kept_only_as_archive():
    nodes, edges = load_graph_records(graph_json_path=ARCHIVED_A_GRAPH_JSON)
    payload = json.loads(ARCHIVED_A_GRAPH_JSON.read_text(encoding="utf-8-sig"))
    report = audit_knowledge_graph(
        nodes,
        edges,
        require_explanation_fields=True,
        external_references=payload.get("external_references"),
    )
    missing_teaching_kinds = {"missing_core_concepts", "missing_key_points", "missing_summary"}
    missing_teaching = [issue for issue in report["issues"] if issue["kind"] in missing_teaching_kinds]
    dangling_refs = [issue for issue in report["issues"] if issue["kind"] == "dangling_node_reference"]
    dangling_edges = [issue for issue in report["issues"] if issue["kind"] in {"dangling_edge_source", "dangling_edge_target"}]
    external_refs = [issue for issue in report["issues"] if issue["kind"] == "external_node_reference"]

    assert report["node_count"] >= 80
    assert report["edge_count"] >= 200
    assert missing_teaching == []
    assert dangling_edges == []
    assert dangling_refs == []
    assert len(external_refs) >= 1


def _load_viewer_data_js(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\s*window\.A2_GRAPH_VIEWER_DATA\s*=\s*(\{.*\});?\s*$", text, re.S)
    assert match, "viewer/data.js must assign window.A2_GRAPH_VIEWER_DATA"
    return json.loads(match.group(1))


def test_archived_a2_viewer_data_js_matches_archived_graph_json_shape():
    graph_payload = json.loads(ARCHIVED_A_GRAPH_JSON.read_text(encoding="utf-8-sig"))
    viewer_payload = _load_viewer_data_js(ARCHIVED_A_VIEWER_DATA_JS)
    rebuilt = build_viewer_data(graph_payload)

    assert viewer_payload["meta"]["note_count"] == len(graph_payload["nodes"])
    assert viewer_payload["meta"]["internal_edge_count"] == len(graph_payload["edges"])
    assert viewer_payload["meta"]["generated_at"] == graph_payload["meta"]["generated_at"]
    assert {node["id"] for node in viewer_payload["graph"]["nodes"]} == {node["id"] for node in graph_payload["nodes"]}
    assert {(link["source"], link["target"]) for link in viewer_payload["graph"]["links"]} == {
        (edge["source"], edge["target"]) for edge in graph_payload["edges"]
    }
    assert set(viewer_payload["notes"]) == {node["id"] for node in graph_payload["nodes"]}
    assert viewer_payload == rebuilt


def test_viewer_data_builder_preserves_teaching_fields_used_by_27_viewer():
    graph_payload = {
        "meta": {"generated_at": "2026-04-27T00:00:00+00:00", "root_notes": ["控制系统"]},
        "nodes": [
            {
                "id": "控制系统",
                "title": "控制系统",
                "category": "0. 基础知识",
                "subcategory": "0. 基础知识",
                "summary": "系统、输入、输出和反馈。",
                "aliases": ["Control System"],
                "tags": ["control"],
                "prerequisites": ["微分方程"],
                "neighbors": ["反馈"],
                "learning_objectives": ["解释反馈作用"],
                "must_know": ["闭环控制基本结构"],
                "common_errors": [{"error": "混淆开环闭环", "cause": "反馈概念不清", "correction": "画框图"}],
                "target_mastery_level": "Understand",
                "difficulty": "easy",
                "outbound_internal_ids": ["反馈"],
                "outbound_out_of_scope_links": ["微分方程"],
                "outbound_missing_links": [],
                "headings": ["定义"],
                "content_markdown_file": "knowledge-graphs/a2-control-theory/source-notes/控制系统.md",
            },
            {
                "id": "反馈",
                "title": "反馈",
                "category": "0. 基础知识",
                "subcategory": "0. 基础知识",
                "summary": "反馈。",
                "learning_objectives": ["说明反馈"],
                "must_know": ["反馈回路"],
            },
        ],
        "edges": [{"source": "控制系统", "target": "反馈", "weight": 2, "relation_label": "关联"}],
    }

    viewer_payload = build_viewer_data(graph_payload)
    note = viewer_payload["notes"]["控制系统"]

    assert viewer_payload["meta"]["note_count"] == 2
    assert viewer_payload["graph"]["nodes"][0]["name"] == "控制系统"
    assert viewer_payload["graph"]["links"][0]["relation_label"] == "关联"
    assert note["prerequisites"] == ["微分方程"]
    assert note["neighbors"] == ["反馈"]
    assert note["learning_objectives"] == ["解释反馈作用"]
    assert note["must_know"] == ["闭环控制基本结构"]
    assert note["common_errors"][0]["correction"] == "画框图"
    assert note["viewer_markdown_path"] == "../source-notes/控制系统.md"


def test_write_viewer_data_js_is_repeatable_27_style_projection(tmp_path: Path):
    graph_payload = {
        "meta": {"generated_at": "2026-04-27T12:00:00+00:00", "root_notes": ["A"]},
        "nodes": [
            {"id": "A", "title": "节点A", "summary": "A", "learning_objectives": ["会A"], "must_know": ["A重点"]},
            {"id": "B", "title": "节点B", "summary": "B", "learning_objectives": ["会B"], "must_know": ["B重点"]},
        ],
        "edges": [{"source": "A", "target": "B", "relation_label": "next"}],
    }
    graph_path = tmp_path / "graph.json"
    data_js_path = tmp_path / "viewer" / "data.js"
    graph_path.write_text(json.dumps(graph_payload, ensure_ascii=False), encoding="utf-8")

    first = write_viewer_data_js(graph_path, data_js_path)
    second = write_viewer_data_js(graph_path, data_js_path)
    rendered = data_js_path.read_text(encoding="utf-8")

    assert first == second
    assert rendered.startswith("window.A2_GRAPH_VIEWER_DATA = ")
    assert _load_viewer_data_js(data_js_path)["notes"]["A"]["must_know"] == ["A重点"]


B_VIEWER_HTML = Path("frontend/knowledge-graph/b/viewer/index.html")
FRONTEND_APP_JS = Path("frontend/assets/app.js")


def test_b_viewer_html_exists_and_references_api_graph_b():
    assert B_VIEWER_HTML.exists(), "B viewer HTML must exist at frontend/knowledge-graph/b/viewer/index.html"
    content = B_VIEWER_HTML.read_text(encoding="utf-8")
    assert "/api/graph/b/data.json" in content, "B viewer must auto-load from /api/graph/b/data.json"
    assert "a2-graph-viewer:learn-node" in content, "B viewer must emit learn-node postMessage for parent"


def test_frontend_app_js_points_to_b_viewer():
    assert FRONTEND_APP_JS.exists()
    content = FRONTEND_APP_JS.read_text(encoding="utf-8")
    assert "/knowledge-graph/b/viewer/index.html" in content, "app.js must reference B viewer, not A"
    assert "/knowledge-graph/a2/viewer/index.html" not in content, "app.js must NOT reference old A viewer"


def test_b_viewer_does_not_reference_archived_a_graph():
    content = B_VIEWER_HTML.read_text(encoding="utf-8")
    assert "docs/archive" not in content, "B viewer must not reference archived A graph paths"


def test_b_viewer_has_relation_meaning_dropdown_without_hierarchy_language():
    content = B_VIEWER_HTML.read_text(encoding="utf-8")
    assert "关系说明" in content
    assert "relationLegendDetails" in content
    assert "prerequisite_of" in content and "前置关系" in content
    assert "parallel_to" in content and "并列关系" in content
    assert "related_to" in content and "相关关系" in content
    assert "weak_related_to" in content and "弱相关" in content
    assert "节点同级展示" in content
    assert "树状" not in content
    assert "父子" not in content


def test_media_evidence_index_inspector_detects_missing_and_ready_fixture(tmp_path: Path):
    missing_report = inspect_media_evidence_index(tmp_path / "missing")
    assert missing_report["ok"] is False
    with pytest.raises(FileNotFoundError, match="media_evidence_index 不可用"):
        assert_media_evidence_index_ready(tmp_path / "missing")

    index_dir = tmp_path / "media_evidence_index"
    index_dir.mkdir()
    (index_dir / "chapter_01_annotated_assets.jsonl").write_text(
        json.dumps({"reference": "fig-1", "asset_type": "figure"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (index_dir / "chapter_01_linked_candidates.jsonl").write_text("{}\n", encoding="utf-8")
    (index_dir / "chapter_01_filtered_candidates.jsonl").write_text("{}\n", encoding="utf-8")
    (index_dir / "batch_summary.json").write_text(
        json.dumps({"count": 1, "chapters": [{"chapter_key": "chapter_01"}]}, ensure_ascii=False),
        encoding="utf-8",
    )

    ready_report = assert_media_evidence_index_ready(index_dir)
    assert ready_report["ok"] is True
    assert ready_report["annotated_asset_count"] == 1

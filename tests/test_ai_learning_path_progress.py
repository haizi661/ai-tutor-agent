import csv
import json

from ai_tutor_agent.ai_learning_path import ai_path_service as service_module


NODE_FIELDS = [
    "node_id",
    "name",
    "chapter",
    "summary",
    "tags",
    "requirement_level",
    "mastery_threshold",
    "importance_level",
    "assessment_focus",
]


EDGE_FIELDS = [
    "edge_id",
    "source",
    "target",
    "relation",
]


def _write_csv(path, fieldnames, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as file_obj:
        writer = csv.DictWriter(file_obj, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _build_service(tmp_path, monkeypatch, student_state):
    nodes_csv = tmp_path / "ai_nodes.csv"
    edges_csv = tmp_path / "ai_edges.csv"
    state_json = tmp_path / "student_state.json"

    _write_csv(
        nodes_csv,
        NODE_FIELDS,
        [
            {"node_id": "AI001", "name": "Intro", "mastery_threshold": "75"},
            {"node_id": "AI002", "name": "Middle", "mastery_threshold": "0.75"},
            {"node_id": "AI003", "name": "Goal", "mastery_threshold": "0.75"},
        ],
    )
    _write_csv(
        edges_csv,
        EDGE_FIELDS,
        [
            {"edge_id": "E001", "source": "AI001", "target": "AI002", "relation": "prerequisite_of"},
            {"edge_id": "E002", "source": "AI002", "target": "AI003", "relation": "prerequisite_of"},
        ],
    )
    state_json.write_text(json.dumps(student_state), encoding="utf-8")

    monkeypatch.setattr(service_module, "AI_NODES_CSV", nodes_csv)
    monkeypatch.setattr(service_module, "AI_EDGES_CSV", edges_csv)
    monkeypatch.setattr(service_module, "AI_STUDENT_STATE_JSON", state_json)

    return service_module.AILearningPathService(), state_json


def test_build_plan_skips_mastered_nodes_from_all_ai_state_sources(tmp_path, monkeypatch):
    service, state_json = _build_service(
        tmp_path,
        monkeypatch,
        {
            "student_id": "student",
            "learned_nodes": {
                "AI001": {"mastery": 0.85, "status": "completed"},
            },
            "mastery_scores": {
                "AI002": 85,
            },
        },
    )

    result = service.build_plan(["AI003"], skip_mastered=True)

    assert result["status"] == "success"
    assert [node["node_id"] for node in result["skipped"]] == ["AI001", "AI002"]
    assert [node["node_id"] for node in result["path"]] == ["AI001", "AI002", "AI003"]
    assert [node["status"] for node in result["path"]] == ["mastered", "mastered", "current"]

    saved_state = json.loads(state_json.read_text(encoding="utf-8"))
    assert saved_state["current_node"] == "AI003"
    assert saved_state["current_path"] == ["AI001", "AI002", "AI003"]
    assert saved_state["path_versions"][-1]["skipped"] == ["AI001", "AI002"]


def test_advance_to_next_node_auto_skips_already_mastered_nodes(tmp_path, monkeypatch):
    service, state_json = _build_service(
        tmp_path,
        monkeypatch,
        {
            "student_id": "student",
            "current_path": ["AI001", "AI002", "AI003"],
            "current_node": "AI001",
            "learned_nodes": {},
            "mastery_scores": {
                "AI002": 85,
            },
        },
    )

    result = service.advance_to_next_node("thread")

    assert result["status"] == "success"
    assert result["current_node"] == "AI003"
    assert [node["node_id"] for node in result["skipped"]] == ["AI002"]

    saved_state = json.loads(state_json.read_text(encoding="utf-8"))
    assert saved_state["current_node"] == "AI003"
    assert saved_state["learned_nodes"]["AI001"]["status"] == "completed"

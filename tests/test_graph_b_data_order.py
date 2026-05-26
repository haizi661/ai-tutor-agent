from ai_tutor_agent.core.learning_support import graph_node_sort_key
from ai_tutor_agent.core.ports import NoopKnowledgeProvider
from ai_tutor_agent.interfaces.api.app import create_api_app
from ai_tutor_agent.interfaces.api.runtime import ApiRuntime
from ai_tutor_agent.interfaces.api.knowledge import _sanitize_graph_record
from asgi_test_client import SyncASGITestClient as TestClient

from test_api_smoke import DummyConn, FakeCheckpointStore, FakeWorkflowFactory, build_test_settings


def test_graph_node_sort_key_uses_canonical_km_number():
    assert graph_node_sort_key("KM001") == (1, "KM001")
    assert graph_node_sort_key("KM010") == (10, "KM010")
    assert graph_node_sort_key("chapter_10_KM002") == (2, "chapter_10_KM002")
    assert graph_node_sort_key("custom-node-12") == (12, "custom-node-12")
    assert graph_node_sort_key("no-number")[0] == 999999


def test_graph_record_exposes_one_based_display_index_from_km_id():
    sanitized = _sanitize_graph_record({"node_id": "chapter_10_KM002", "name": "第二节点"})

    assert sanitized["display_index"] == 2


def test_graph_record_display_index_falls_back_to_last_number_group():
    sanitized = _sanitize_graph_record({"node_id": "custom-node-12", "name": "第十二节点"})

    assert sanitized["display_index"] == 12


def test_graph_b_data_endpoint_returns_nodes_in_display_order(tmp_path):
    class FakeGraphPipeline:
        nodes = [
            {"node_id": "KM010", "name": "第十节点"},
            {"node_id": "KM001", "name": "第一节点"},
            {"node_id": "chapter_10_KM002", "name": "第二节点"},
        ]
        edges = [{"source": "KM001", "target": "chapter_10_KM002", "relation_strength": None}]

    checkpoint_store = FakeCheckpointStore()
    runtime = ApiRuntime(
        settings=build_test_settings(tmp_path),
        knowledge_provider=NoopKnowledgeProvider(),
        graph_rag_pipeline=FakeGraphPipeline(),
        workflow_factory=FakeWorkflowFactory(checkpoint_store),
        checkpoint_factory=lambda path: (checkpoint_store, DummyConn()),
    )

    with TestClient(create_api_app(runtime_factory=lambda: runtime)) as client:
        response = client.get("/api/graph/b/data.json")

    assert response.status_code == 200
    payload = response.json()
    assert [node["node_id"] for node in payload["nodes"]] == ["KM001", "chapter_10_KM002", "KM010"]
    assert [node["display_index"] for node in payload["nodes"]] == [1, 2, 10]
    assert payload["edges"][0]["relation_strength"] == 0.5
    assert payload["meta"]["node_count"] == 3

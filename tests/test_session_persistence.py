from types import SimpleNamespace

from ai_tutor_agent.application.session import _initial_state_preserving_learning_direction
from ai_tutor_agent.interfaces.api.app import create_api_app
from ai_tutor_agent.interfaces.api.runtime import SessionManager
from ai_tutor_agent.interfaces.api.session import _ensure_thread_checkpoint
from asgi_test_client import SyncASGITestClient as TestClient


class DummyConn:
    def close(self):
        return None


class FakeCheckpointStore:
    def __init__(self):
        self.states = {}
        self.records = {}

    def save(self, thread_id, state):
        self.states[thread_id] = dict(state)
        self.records[thread_id] = SimpleNamespace(
            checkpoint={"channel_values": dict(state), "id": f"{thread_id}-1", "ts": "2026-04-29T00:00:00+00:00"},
            metadata={},
            parent_config=None,
        )

    def get_tuple(self, config):
        return self.records.get(config["configurable"]["thread_id"])


class FakeGraphApp:
    def __init__(self, store):
        self.store = store

    def get_state(self, config):
        thread_id = config["configurable"]["thread_id"]
        return SimpleNamespace(values=dict(self.store.states.get(thread_id, {})))

    def update_state(self, config, patch):
        thread_id = config["configurable"]["thread_id"]
        state = dict(self.store.states.get(thread_id, {}))
        state.update(patch)
        self.store.save(thread_id, state)


def _runtime(store):
    return SimpleNamespace(
        settings=SimpleNamespace(memory_db_path="memory.sqlite"),
        knowledge_provider=None,
        graph_rag_pipeline=None,
        student_state_store=None,
        question_bank_provider=None,
        session_manager=SessionManager(),
        workflow_factory=lambda settings, runtime=None: (FakeGraphApp(store), DummyConn()),
        checkpoint_factory=lambda path: (store, DummyConn()),
    )


def test_ensure_thread_checkpoint_creates_blank_history_state():
    store = FakeCheckpointStore()
    runtime = _runtime(store)

    created = _ensure_thread_checkpoint("session-new", runtime)

    assert created is True
    saved = store.states["session-new"]
    assert saved["flow_status"] == "greeting"
    assert saved["current_topic"] == ""
    assert saved["message_history"] == []


def test_ensure_thread_checkpoint_does_not_overwrite_existing_history_state():
    store = FakeCheckpointStore()
    store.save(
        "session-existing",
        {
            "flow_status": "normal",
            "current_topic": "自动控制原理",
            "message_history": [{"role": "user", "kind": "topic_input", "content": "自动控制原理"}],
        },
    )
    runtime = _runtime(store)

    created = _ensure_thread_checkpoint("session-existing", runtime)

    assert created is False
    assert store.states["session-existing"]["flow_status"] == "normal"
    assert store.states["session-existing"]["current_topic"] == "自动控制原理"


def test_learning_direction_endpoint_locks_direction_in_checkpoint():
    store = FakeCheckpointStore()
    runtime = _runtime(store)
    app = create_api_app(runtime_factory=lambda: runtime)

    with TestClient(app) as client:
        response = client.post(
            "/api/sessions/thread-direction/learning-direction",
            json={"track": "artificial_intelligence"},
        )

    assert response.status_code == 200
    saved = store.states["thread-direction"]
    assert saved["learning_track"] == "artificial_intelligence"
    assert saved["learning_track_label"] == "人工智能"
    assert saved["learning_track_locked"] is True
    assert saved["flow_status"] == "ai_path_active"
    assert [item["kind"] for item in saved["message_history"]] == [
        "course_choice_card",
        "course_choice_selection",
    ]


def test_initial_state_preserves_locked_learning_direction_when_topic_starts():
    previous = {
        "learning_track": "control_theory",
        "learning_track_label": "自动控制原理",
        "learning_track_locked": True,
        "message_history": [
            {"role": "assistant", "kind": "course_choice_card", "content": "请选择本次学习方向"},
            {"role": "user", "kind": "course_choice_selection", "content": "自动控制原理"},
        ],
    }

    state = _initial_state_preserving_learning_direction("二阶系统时域分析", previous)

    assert state["learning_track"] == "control_theory"
    assert state["learning_track_locked"] is True
    assert [item["kind"] for item in state["message_history"]] == [
        "course_choice_card",
        "course_choice_selection",
        "topic_input",
    ]

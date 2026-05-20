from types import SimpleNamespace

from ai_tutor_agent.interfaces.api.session import _ensure_thread_checkpoint


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

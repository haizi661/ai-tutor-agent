import queue
from types import SimpleNamespace

from ai_tutor_agent.application.session import _initial_state_preserving_learning_direction
from ai_tutor_agent.interfaces.api.app import create_api_app
from ai_tutor_agent.interfaces.api import session as session_module
from ai_tutor_agent.interfaces.api.runtime import SessionManager
from ai_tutor_agent.interfaces.api.session import _ensure_thread_checkpoint, _reset_in_progress_learning_state
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


class _FakeStudentState:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class _FakeStudentStateStore:
    """Minimal stand-in for StudentStateStore used by _reset_in_progress_learning_state."""

    def __init__(self, initial_state=None):
        self.states: dict[str, _FakeStudentState] = {
            "default_student": _FakeStudentState(**(initial_state or {}))
        }
        self.update_calls: list[str] = []

    def update(self, student_id: str, mutator):
        self.update_calls.append(student_id)
        ss = self.states[student_id]
        mutator(ss)
        return ss


def test_reset_in_progress_learning_state_resets_session_index():
    """回归测试:新对话必须重置 session_index。

    旧 bug:_reset_in_progress_learning_state 清掉了 learning_plan_v2 但
    保留了 session_index,导致新对话生成路径时显示"第 N 号路径"(N 接着
    累计),违背"新对话从第 1 号开始"的预期。
    """
    store = _FakeStudentStateStore(
        initial_state={
            "session_index": 3,
            "learning_plan_v2": {"session_index": 2, "steps": []},
            "concept_mastery": {"feedback": 0.6},
        }
    )
    runtime = SimpleNamespace(student_state_store=store)

    _reset_in_progress_learning_state(runtime)

    ss = store.states["default_student"]
    assert ss.session_index == 0, (
        f"新对话 session_index 应重置为 0,实际为 {ss.session_index}"
    )
    # 画像仍要保留(用户花了时间做完自评的成果不能丢)
    assert ss.concept_mastery["feedback"] == 0.6


def test_reset_in_progress_learning_state_clears_in_progress_but_keeps_history():
    """回归测试：新对话（_reset_in_progress_learning_state）必须清掉进行中状态。

    旧 bug：default_student.json 残留 current_node_id="KM002" / learning_plan_v2 / visited_nodes，
    新会话会读这些旧值 → initial_node_selector 跳过 KM001 直接选 KM002。
    """
    store = _FakeStudentStateStore(
        initial_state={
            "current_node_id": "KM002",
            "last_question": "什么是反馈",
            "learning_plan": [{"step_index": 0, "node_ids": ["KM001", "KM002"]}],
            "learning_plan_v2": {"steps": [{"node_ids": ["KM001", "KM002"]}]},
            "learning_plan_current_step": 0,
            "learning_plan_generated_at": "2026-06-01T10:00:00",
            "learning_plan_source": "resume_v2",
            "visited_nodes": ["KM001", "KM003", "KM006", "KM004"],
            "knowledge_graph": {
                "KM003": {"status": "in_progress", "score": 40},
                "KM004": {"status": "mastered", "score": 100},
            },
            "homework": [{"assignment_id": "HW-1", "status": "assigned"}],
            "homework_assignments": [{"id": "HW-1"}],
            "homework_history": [{"id": "HW-0", "status": "completed"}],
            "wrong_question_book": [{"question_id": "Q1"}],
            "question_help_records": [{"question": "help1"}],
            "concept_mastery": {"feedback": 0.6},
            "self_assessment_scores": {"auto_basic": 3},
        }
    )
    runtime = SimpleNamespace(student_state_store=store)

    _reset_in_progress_learning_state(runtime)

    ss = store.states["default_student"]
    # 进行中字段必须清空
    assert ss.current_node_id == ""
    assert ss.last_question == ""
    assert ss.learning_plan == []
    assert ss.learning_plan_v2 == {}
    assert ss.learning_plan_current_step == 0
    assert ss.learning_plan_generated_at == ""
    assert ss.learning_plan_source == ""
    assert ss.visited_nodes == []
    # 长期记忆必须保留
    assert "KM003" in ss.knowledge_graph
    assert ss.knowledge_graph["KM004"]["status"] == "mastered"
    assert len(ss.homework) == 1
    assert ss.homework_history[0]["status"] == "completed"
    assert ss.wrong_question_book[0]["question_id"] == "Q1"
    assert ss.question_help_records[0]["question"] == "help1"
    assert ss.concept_mastery["feedback"] == 0.6
    assert ss.self_assessment_scores["auto_basic"] == 3
    # 确认 update 被调用
    assert store.update_calls == ["default_student"]


def test_reset_in_progress_learning_state_handles_no_store():
    """student_state_store 为 None 时不能抛异常（不影响新会话创建）。"""
    runtime = SimpleNamespace(student_state_store=None)
    # 不应抛任何异常
    _reset_in_progress_learning_state(runtime)


class _RecordingStudentStateStore:
    def __init__(self):
        self.load_calls = []

    def load(self, student_id):
        self.load_calls.append(student_id)
        return SimpleNamespace(to_dict=lambda: {"current_node_id": "KM001"})


def test_graph_worker_refreshes_student_snapshot_by_checkpoint_student_id(monkeypatch):
    store = FakeCheckpointStore()
    store.save(
        "thread-rich-restore",
        {
            "student_id": "student_thread-rich-restore",
            "current_topic": "自动控制原理",
            "current_node_id": "KM001",
        },
    )
    student_store = _RecordingStudentStateStore()
    runtime = _runtime(store)
    runtime.student_state_store = student_store

    monkeypatch.setattr(
        session_module,
        "run_learning_session",
        lambda graph_app, event_sink, **kwargs: None,
    )

    session_module._graph_worker(
        "thread-rich-restore",
        "",
        runtime,
        queue.Queue(),
        queue.Queue(),
    )

    assert student_store.load_calls == ["student_thread-rich-restore"]

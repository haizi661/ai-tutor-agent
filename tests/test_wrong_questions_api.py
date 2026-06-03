from types import SimpleNamespace

from ai_tutor_agent.core.ports import NoopKnowledgeProvider
from ai_tutor_agent.interfaces.api.app import create_api_app
from ai_tutor_agent.knowledge_map.student_state import StudentState, StudentStateStore
from tests.asgi_test_client import SyncASGITestClient


def _client(tmp_path):
    store = StudentStateStore(tmp_path / "student_states")
    runtime = SimpleNamespace(
        settings=SimpleNamespace(),
        knowledge_provider=NoopKnowledgeProvider(),
        student_state_store=store,
    )
    app = create_api_app(runtime_factory=lambda: runtime)
    return SyncASGITestClient(app), store


def test_master_wrong_question_returns_404_when_question_is_missing(tmp_path):
    client, store = _client(tmp_path)
    state = StudentState(student_id="s1")
    state.wb_add_or_update(
        [
            {
                "question_id": "Q1",
                "stem": "题干",
                "options": {"A": "对", "B": "错"},
                "user_answer": "B",
                "answer_key": "A",
            }
        ],
        "KM001",
        "节点",
    )
    store.save(state)

    with client:
        response = client.post(
            "/api/students/s1/wrong-questions/Q404/master",
            json={"mastered": True},
        )

    assert response.status_code == 404
    assert store.load("s1").wrong_question_book[0]["mastered"] is False


def test_wrong_question_list_filters_mastered_and_returns_summary(tmp_path):
    client, store = _client(tmp_path)
    state = StudentState(student_id="s1")
    state.wb_add_or_update(
        [
            {
                "question_id": "Q1",
                "stem": "题干1",
                "options": {"A": "对", "B": "错"},
                "user_answer": "B",
                "answer_key": "A",
            },
            {
                "question_id": "Q2",
                "stem": "题干2",
                "options": {"A": "对", "B": "错"},
                "user_answer": "B",
                "answer_key": "A",
            },
        ],
        "KM001",
        "节点",
    )
    assert state.wb_mark_mastered("Q2", True)
    store.save(state)

    with client:
        pending = client.get("/api/students/s1/wrong-questions?mastered=false")
        mastered = client.get("/api/students/s1/wrong-questions?mastered=true")

    assert pending.status_code == 200
    assert [item["question_id"] for item in pending.json()["items"]] == ["Q1"]
    assert pending.json()["total_all"] == 2
    assert pending.json()["total_unmastered"] == 1
    assert pending.json()["total_mastered"] == 1
    assert mastered.status_code == 200
    assert [item["question_id"] for item in mastered.json()["items"]] == ["Q2"]

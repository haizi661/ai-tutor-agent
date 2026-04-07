from collections import defaultdict
from types import SimpleNamespace

from fastapi.testclient import TestClient

from ai_tutor_agent.config import Settings
from ai_tutor_agent.core.events import make_event
from ai_tutor_agent.core.ports import NoopKnowledgeProvider
from ai_tutor_agent.interfaces.api.app import create_api_app
from ai_tutor_agent.interfaces.api.history import _checkpoint_summary
from ai_tutor_agent.interfaces.api.runtime import ApiRuntime


class DummyConn:
    def close(self):
        return None


class FakeCheckpointStore:
    def __init__(self):
        self.states = {}
        self.records = {}
        self.history = defaultdict(list)

    def save(self, thread_id, state, *, source="loop", step=0):
        entry = SimpleNamespace(
            checkpoint={
                "id": f"{thread_id}-{len(self.history[thread_id]) + 1}",
                "ts": "2026-03-06T00:00:00+00:00",
                "channel_values": dict(state),
            },
            metadata={"source": source, "step": step},
            parent_config=None,
        )
        self.states[thread_id] = dict(state)
        self.records[thread_id] = entry
        self.history[thread_id].insert(0, entry)

    def get_tuple(self, config):
        return self.records.get(config["configurable"]["thread_id"])

    def list(self, config, limit=None):
        thread_id = config["configurable"]["thread_id"]
        entries = list(self.history.get(thread_id, []))
        return entries if limit is None else entries[:limit]

    def delete_thread(self, thread_id):
        self.states.pop(thread_id, None)
        self.records.pop(thread_id, None)
        self.history.pop(thread_id, None)


class FakeStateSnapshot:
    def __init__(self, values):
        self.values = values


class FakeGraphApp:
    def __init__(self, checkpoint_store, runtime_context):
        self.checkpoint_store = checkpoint_store
        self.runtime_context = runtime_context

    def get_state(self, config):
        thread_id = config["configurable"]["thread_id"]
        return FakeStateSnapshot(self.checkpoint_store.states.get(thread_id, {}))

    def update_state(self, config, values):
        thread_id = config["configurable"]["thread_id"]
        state = dict(self.checkpoint_store.states.get(thread_id, {}))
        state.update(values)
        self.checkpoint_store.save(thread_id, state, source="update", step=2)

    def invoke(self, payload, config):
        thread_id = config["configurable"]["thread_id"]
        state = dict(self.checkpoint_store.states.get(thread_id, {}))
        if payload:
            state.update(payload)
            self.checkpoint_store.save(thread_id, state, source="input", step=-1)

        if state.get("flow_status") == "profiling":
            radar = {
                "dimensions": ["基础概念", "规则理解", "逻辑推理", "场景应用", "细节辨析", "表达信心"],
                "self_scores": [60, 55, 50, 45, 40, 35],
                "objective_scores": [65, 60, 55, 50, 45, 40],
            }
            state.update(
                {
                    "assessment_radar": radar,
                    "assessment_result": "## 📊 控制理论学前能力画像",
                    "is_assessed": True,
                    "flow_status": "normal",
                    "tutor_content": "开始进行 Tutor 讲解。",
                }
            )
            self.checkpoint_store.save(thread_id, state, source="loop", step=3)
            self.runtime_context.event_sink.emit(
                make_event("profile.radar_data", "user_profiler", data=radar)
            )
            self.runtime_context.event_sink.emit(
                make_event(
                    "node.stream",
                    "tutor",
                    data={"text": "开始进行 Tutor 讲解。"},
                )
            )
            return

        questions = state.get("assessment_questions") or [
            {
                "id": 1,
                "type": "self_eval",
                "dimension": "基础概念",
                "question": "你对控制系统稳定性的理解程度如何？",
                "options": ["A. 完全不懂", "B. 听说过", "C. 基本理解", "D. 熟练掌握"],
                "correct_answer": "",
            }
        ]
        state.update(
            {
                "current_topic": state.get("current_topic", "控制理论"),
                "assessment_questions": questions,
                "flow_status": "awaiting_assessment",
            }
        )
        self.checkpoint_store.save(thread_id, state, source="loop", step=1)
        self.runtime_context.event_sink.emit(
            make_event(
                "assessment.form_ready",
                "assessment_generator",
                data={"questions": questions},
            )
        )


class FakeWorkflowFactory:
    def __init__(self, checkpoint_store):
        self.checkpoint_store = checkpoint_store

    def __call__(self, settings, runtime=None):
        del settings
        return FakeGraphApp(self.checkpoint_store, runtime), DummyConn()


def build_test_settings(tmp_path):
    return Settings(
        chat_profile="custom",
        llm_provider="google",
        google_api_key="google-key",
        gemini_api_key="gemini-key",
        openai_api_key="openai-key",
        openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        qwen_api_key="qwen-key",
        deepseek_api_key="deepseek-key",
        minimax_api_key="minimax-key",
        glm_api_key="glm-key",
        model_name="gemini-2.5-pro",
        embedding_provider="local",
        embedding_model_name="sentence-transformers/all-MiniLM-L6-v2",
        tutor_temperature=0.7,
        tester_temperature=0.4,
        evaluator_temperature=0.0,
        pass_score=80,
        memory_db_path=str(tmp_path / "test-memory.sqlite"),
        knowledge_dir=str(tmp_path / "knowledge"),
        knowledge_chunk_size=1000,
        knowledge_chunk_overlap=150,
        knowledge_top_k=3,
        default_thread_id="test-thread",
        http_proxy=None,
        https_proxy=None,
        local_config_enabled=True,
        chroma_dir=str(tmp_path / "chroma_db"),
        dashscope_api_key=None,
        mineru_api_token=None,
        rag_hybrid_enabled=False,
        rag_mineru_enabled=False,
    )


def create_test_client(tmp_path):
    checkpoint_store = FakeCheckpointStore()
    runtime = ApiRuntime(
        settings=build_test_settings(tmp_path),
        knowledge_provider=NoopKnowledgeProvider(),
        workflow_factory=FakeWorkflowFactory(checkpoint_store),
        checkpoint_factory=lambda path: (checkpoint_store, DummyConn()),
    )
    app = create_api_app(runtime_factory=lambda: runtime)
    return TestClient(app)


class UploadableKnowledgeProvider:
    def __init__(self):
        self.vector_store = object()
        self.bm25 = object()
        self.items = [
            {"filename": "demo.txt", "size_bytes": 11, "chunk_count": 2},
            {"filename": "guide.pdf", "size_bytes": 2048, "chunk_count": 6},
        ]

    def query(self, query: str) -> str:
        del query
        return ""

    def add_document(self, source_path: str) -> dict:
        del source_path
        return {
            "success": True,
            "filename": "demo.txt",
            "chunks": 2,
            "message": "ok",
            "parse_backend": "text",
            "bm25_rebuilt": True,
        }

    def list_documents(self) -> list[dict]:
        return list(self.items)

    def delete_document(self, filename: str) -> dict:
        for idx, item in enumerate(self.items):
            if item["filename"] == filename:
                self.items.pop(idx)
                return {
                    "success": True,
                    "filename": filename,
                    "removed_file": True,
                    "removed_index": True,
                }
        return {"success": False, "message": f"file not found: {filename}"}

    def clear_documents(self) -> dict:
        removed = len(self.items)
        self.items = []
        return {"success": True, "removed": removed, "removed_index": removed}


def test_api_config_endpoint_allows_runtime_model_switch(tmp_path):
    with create_test_client(tmp_path) as client:
        response = client.get("/api/config")
        assert response.status_code == 200
        payload = response.json()
        assert "profiles" in payload
        assert payload["llm_provider"] == "google"
        assert any(profile["id"] == "qwen" for profile in payload["profiles"])
        assert any(profile["id"] == "minimax" for profile in payload["profiles"])
        assert any(profile["id"] == "glm" for profile in payload["profiles"])

        update = client.post(
            "/api/config",
            json={"profile_id": "deepseek"},
        )
        assert update.status_code == 200
        updated = update.json()
        assert updated["chat_profile"] == "deepseek"
        assert updated["llm_provider"] == "openai"
        assert updated["model_name"] == "deepseek-chat"
        assert updated["openai_api_base"] == "https://api.deepseek.com/v1"


def test_api_root_serves_frontend_index(tmp_path):
    with create_test_client(tmp_path) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "AI Tutor" in response.text


def test_pre_assessment_pause_submit_and_restore_flow(tmp_path):
    thread_id = "session-smoke"
    with create_test_client(tmp_path) as client:
        start = client.post("/api/start", json={"thread_id": thread_id, "topic": "控制理论"})
        assert start.status_code == 200

        stream_response = client.get(f"/api/stream?thread_id={thread_id}")
        assert stream_response.status_code == 200
        assert "event: assessment.form_ready" in stream_response.text

        history_before = client.get(f"/api/history/{thread_id}")
        assert history_before.status_code == 200
        before_payload = history_before.json()
        assert before_payload["state"]["flow_status"] == "awaiting_assessment"
        assert before_payload["runtime"]["is_running"] is False
        assert before_payload["runtime"]["awaiting_input"] is False
        assert len(before_payload["state"]["assessment_questions"]) == 1

        resume = client.post(f"/api/sessions/{thread_id}/resume")
        assert resume.status_code == 200
        resumed_stream = client.get(f"/api/stream?thread_id={thread_id}")
        assert "event: assessment.form_ready" in resumed_stream.text

        submit = client.post(
            "/api/submit_assessment",
            json={"thread_id": thread_id, "answers": {"1": "C"}},
        )
        assert submit.status_code == 200

        post_assessment_stream = client.get(f"/api/stream?thread_id={thread_id}")
        assert "event: profile.radar_data" in post_assessment_stream.text
        assert "event: node.stream" in post_assessment_stream.text

        history_after = client.get(f"/api/history/{thread_id}")
        assert history_after.status_code == 200
        after_payload = history_after.json()
        assert after_payload["state"]["is_assessed"] is True
        assert after_payload["state"]["assessment_radar"]["dimensions"][0] == "基础概念"
        assert after_payload["state"]["tutor_content"] == "开始进行 Tutor 讲解。"


def test_history_summary_uses_stage_aware_display_title(tmp_path):
    checkpoint_store = FakeCheckpointStore()
    checkpoint_store.save(
        "thread-meta",
        {
            "current_topic": "你是什么模型",
            "proposed_topic": "",
            "flow_status": "meta_qa",
            "assessment_questions": [],
            "assessment_answers": {},
        },
        source="loop",
        step=1,
    )
    checkpoint_store.save(
        "thread-confirm",
        {
            "current_topic": "",
            "proposed_topic": "高等数学",
            "flow_status": "awaiting_topic_confirmation",
            "assessment_questions": [],
            "assessment_answers": {},
        },
        source="loop",
        step=1,
    )
    meta_summary = _checkpoint_summary("thread-meta", checkpoint_store.get_tuple({"configurable": {"thread_id": "thread-meta"}}))
    confirm_summary = _checkpoint_summary("thread-confirm", checkpoint_store.get_tuple({"configurable": {"thread_id": "thread-confirm"}}))

    assert meta_summary["display_title"] == "未确认主题"
    assert confirm_summary["display_title"] == "待确认：高等数学"


def test_topic_confirmation_resume_flow(tmp_path):
    thread_id = "session-topic-confirm"
    checkpoint_store = FakeCheckpointStore()
    checkpoint_store.save(
        thread_id,
        {
            "current_topic": "",
            "proposed_topic": "控制理论",
            "flow_status": "awaiting_topic_confirmation",
            "assessment_questions": [],
            "assessment_answers": {},
        },
        source="loop",
        step=1,
    )
    runtime = ApiRuntime(
        settings=build_test_settings(tmp_path),
        knowledge_provider=NoopKnowledgeProvider(),
        workflow_factory=FakeWorkflowFactory(checkpoint_store),
        checkpoint_factory=lambda path: (checkpoint_store, DummyConn()),
    )

    with TestClient(create_api_app(runtime_factory=lambda: runtime)) as client:
        detail = client.get(f"/api/history/{thread_id}")
        assert detail.status_code == 200
        assert detail.json()["state"]["proposed_topic"] == "控制理论"
        assert "runtime" in detail.json()

        confirm = client.post(
            "/api/confirm_topic",
            json={"thread_id": thread_id, "confirmed": True, "topic": ""},
        )
        assert confirm.status_code == 200

        stream = client.get(f"/api/stream?thread_id={thread_id}")
        assert "event: session.info" in stream.text
        assert "event: assessment.form_ready" in stream.text

        updated = client.get(f"/api/history/{thread_id}").json()
        assert updated["state"]["current_topic"] == "控制理论"
        assert updated["state"]["flow_status"] == "awaiting_assessment"
        assert updated["state"]["proposed_topic"] == ""


def test_api_start_continues_running_session_that_is_waiting_for_input(tmp_path):
    runtime = ApiRuntime(
        settings=build_test_settings(tmp_path),
        knowledge_provider=NoopKnowledgeProvider(),
        workflow_factory=FakeWorkflowFactory(FakeCheckpointStore()),
        checkpoint_factory=lambda path: (FakeCheckpointStore(), DummyConn()),
    )

    with TestClient(create_api_app(runtime_factory=lambda: runtime)) as client:
        session = runtime.session_manager.get_or_create("waiting-thread")
        session["is_running"] = True
        session["awaiting_input"] = True

        response = client.post(
            "/api/start",
            json={"thread_id": "waiting-thread", "topic": "你是什么模型"},
        )

        assert response.status_code == 200
        assert response.json()["status"] == "continued"
        assert session["input_q"].get_nowait() == "你是什么模型"
        assert session["awaiting_input"] is False


def test_knowledge_status_exposes_rag2_fields(tmp_path):
    runtime = ApiRuntime(
        settings=build_test_settings(tmp_path),
        knowledge_provider=UploadableKnowledgeProvider(),
        workflow_factory=FakeWorkflowFactory(FakeCheckpointStore()),
        checkpoint_factory=lambda path: (FakeCheckpointStore(), DummyConn()),
    )
    runtime.settings = runtime.settings.__class__(
        **{**runtime.settings.__dict__, "rag_hybrid_enabled": True, "rag_mineru_enabled": True}
    )

    with TestClient(create_api_app(runtime_factory=lambda: runtime)) as client:
        response = client.get("/api/knowledge")
        assert response.status_code == 200
        payload = response.json()
        assert payload["enabled"] is True
        assert payload["supports_upload"] is True
        assert payload["retrieval_mode"] == "hybrid"
        assert payload["bm25_ready"] is True
        assert payload["rag_mineru_enabled"] is True


def test_upload_returns_optional_parse_backend_and_bm25(tmp_path):
    runtime = ApiRuntime(
        settings=build_test_settings(tmp_path),
        knowledge_provider=UploadableKnowledgeProvider(),
        workflow_factory=FakeWorkflowFactory(FakeCheckpointStore()),
        checkpoint_factory=lambda path: (FakeCheckpointStore(), DummyConn()),
    )

    with TestClient(create_api_app(runtime_factory=lambda: runtime)) as client:
        response = client.post(
            "/api/upload",
            files={"file": ("demo.txt", b"hello world", "text/plain")},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "success"
        assert payload["filename"] == "demo.txt"
        assert payload["parse_backend"] == "text"
        assert payload["bm25_rebuilt"] is True


def test_knowledge_files_list_and_delete_and_clear(tmp_path):
    runtime = ApiRuntime(
        settings=build_test_settings(tmp_path),
        knowledge_provider=UploadableKnowledgeProvider(),
        workflow_factory=FakeWorkflowFactory(FakeCheckpointStore()),
        checkpoint_factory=lambda path: (FakeCheckpointStore(), DummyConn()),
    )

    with TestClient(create_api_app(runtime_factory=lambda: runtime)) as client:
        listing = client.get("/api/knowledge/files")
        assert listing.status_code == 200
        payload = listing.json()
        assert payload["status"] == "success"
        assert len(payload["items"]) == 2

        deleted = client.delete("/api/knowledge/files/demo.txt")
        assert deleted.status_code == 200
        deleted_payload = deleted.json()
        assert deleted_payload["status"] == "success"
        assert deleted_payload["filename"] == "demo.txt"

        listing_after_delete = client.get("/api/knowledge/files")
        assert len(listing_after_delete.json()["items"]) == 1

        cleared = client.delete("/api/knowledge/files")
        assert cleared.status_code == 200
        clear_payload = cleared.json()
        assert clear_payload["status"] == "success"
        assert clear_payload["removed"] == 1

        listing_after_clear = client.get("/api/knowledge/files")
        assert listing_after_clear.status_code == 200
        assert listing_after_clear.json()["items"] == []


def test_local_config_round_trip(monkeypatch, tmp_path):
    env_path = tmp_path / ".env.test"
    env_path.write_text(
        "\n".join(
            [
                "CHAT_PROFILE=gemini",
                "GOOGLE_API_KEY=google-key",
                "GEMINI_API_KEY=gemini-key",
                "EMBEDDING_PROVIDER=local",
                "EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2",
                "LOCAL_CONFIG_ENABLED=true",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("AI_TUTOR_ENV_FILE", str(env_path))

    import ai_tutor_agent.interfaces.api.runtime as runtime_module

    monkeypatch.setattr(runtime_module, "LocalFileKnowledgeProvider", lambda settings: NoopKnowledgeProvider())

    runtime = ApiRuntime(
        settings=build_test_settings(tmp_path),
        knowledge_provider=NoopKnowledgeProvider(),
        workflow_factory=FakeWorkflowFactory(FakeCheckpointStore()),
        checkpoint_factory=lambda path: (FakeCheckpointStore(), DummyConn()),
    )

    with TestClient(create_api_app(runtime_factory=lambda: runtime)) as client:
        current = client.get("/api/config/local")
        assert current.status_code == 200
        assert current.json()["local_config_enabled"] is True
        assert any(vendor["id"] == "qwen" for vendor in current.json()["vendors"])
        assert any(vendor["id"] == "minimax" for vendor in current.json()["vendors"])
        assert any(vendor["id"] == "glm" for vendor in current.json()["vendors"])
        assert current.json()["gemini_api_key"] == "****-key"
        assert current.json()["has_gemini_api_key"] is True

        updated = client.post(
            "/api/config/local",
            json={
                "vendor_id": "qwen",
                "chat_profile": "qwen",
                "api_key": "qwen-key-new",
                "gemini_api_key": "gemini-key",
                "qwen_api_key": "",
                "deepseek_api_key": "",
                "llm_provider": "openai",
                "google_api_key": "gemini-key",
                "openai_api_key": "",
                "openai_api_base": "",
                "model_name": "qwen-plus",
                "embedding_provider": "local",
                "embedding_model_name": "sentence-transformers/all-MiniLM-L6-v2",
                "knowledge_chunk_size": 800,
                "knowledge_chunk_overlap": 100,
                "knowledge_top_k": 5,
                "http_proxy": "http://127.0.0.1:7890",
                "https_proxy": "http://127.0.0.1:7890",
            },
        )
        assert updated.status_code == 200
        payload = updated.json()
        assert payload["config"]["chat_profile"] == "qwen"
        assert payload["config"]["model_name"] == "qwen-plus"
        assert payload["local"]["qwen_api_key"] == "****-new"
        assert payload["local"]["has_qwen_api_key"] is True
        assert payload["local"]["knowledge_top_k"] == 5

        glm_update = client.post(
            "/api/config/local",
            json={
                "vendor_id": "glm",
                "chat_profile": "glm",
                "api_key": "glm-key-new",
                "gemini_api_key": "gemini-key",
                "qwen_api_key": "qwen-key-new",
                "deepseek_api_key": "",
                "minimax_api_key": "",
                "glm_api_key": "",
                "llm_provider": "openai",
                "google_api_key": "gemini-key",
                "openai_api_key": "",
                "openai_api_base": "",
                "model_name": "glm-5",
                "embedding_provider": "local",
                "embedding_model_name": "sentence-transformers/all-MiniLM-L6-v2",
                "knowledge_chunk_size": 800,
                "knowledge_chunk_overlap": 100,
                "knowledge_top_k": 5,
                "http_proxy": "http://127.0.0.1:7890",
                "https_proxy": "http://127.0.0.1:7890",
            },
        )
        assert glm_update.status_code == 200
        glm_payload = glm_update.json()
        assert glm_payload["config"]["chat_profile"] == "glm"
        assert glm_payload["config"]["openai_api_base"] == "https://open.bigmodel.cn/api/paas/v4"
        assert glm_payload["local"]["glm_api_key"] == "****-new"

        content = env_path.read_text(encoding="utf-8")
        assert "CHAT_PROFILE=glm" in content
        assert "QWEN_API_KEY=qwen-key-new" in content
        assert "GLM_API_KEY=glm-key-new" in content

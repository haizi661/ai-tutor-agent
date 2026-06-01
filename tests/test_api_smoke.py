import queue
import threading
import time
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

import pytest

from ai_tutor_agent.config import Settings
from ai_tutor_agent.core.events import make_event
from ai_tutor_agent.core.ports import NoopKnowledgeProvider
from ai_tutor_agent.interfaces.api.app import create_api_app
from ai_tutor_agent.interfaces.api.history import _checkpoint_summary
from ai_tutor_agent.interfaces.api.runtime import ApiRuntime
from asgi_test_client import SyncASGITestClient as TestClient


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
                "dimensions": ["基础概念", "规则理解", "逻辑推理", "场景应用", "细节辨析", "综合应用"],
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


class SlowResumeWorkflowFactory:
    def __init__(self, checkpoint_store, *, sleep_seconds=0.2):
        self.checkpoint_store = checkpoint_store
        self.sleep_seconds = sleep_seconds

    def __call__(self, settings, runtime=None):
        del settings
        factory = self

        class SlowResumeGraphApp(FakeGraphApp):
            def invoke(self_inner, payload, config):
                thread_id = config["configurable"]["thread_id"]
                state = dict(self_inner.checkpoint_store.states.get(thread_id, {}))
                if state.get("flow_status") == "awaiting_assessment":
                    time.sleep(factory.sleep_seconds)
                return super().invoke(payload, config)

        return SlowResumeGraphApp(self.checkpoint_store, runtime), DummyConn()


class WaitingInputWorkflowFactory:
    def __init__(self, checkpoint_store):
        self.checkpoint_store = checkpoint_store

    def __call__(self, settings, runtime=None):
        del settings
        factory = self

        class WaitingInputGraphApp:
            def __init__(self, runtime_context):
                self.runtime_context = runtime_context
                self.checkpoint_store = factory.checkpoint_store

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
                self.checkpoint_store.save(thread_id, state, source="loop", step=1)
                answer = self.runtime_context.answer_provider.get_answer(
                    "请输入回答",
                    state={"thread_id": thread_id},
                )
                state["user_answer"] = answer
                state["flow_status"] = "normal"
                self.checkpoint_store.save(thread_id, state, source="loop", step=2)
                self.runtime_context.event_sink.emit(
                    make_event("node.stream", "tester", data={"text": answer})
                )

        return WaitingInputGraphApp(runtime), DummyConn()


class SelectorResumeWorkflowFactory:
    def __init__(self, checkpoint_store):
        self.checkpoint_store = checkpoint_store

    def __call__(self, settings, runtime=None):
        del settings
        factory = self

        class SelectorResumeGraphApp:
            def __init__(self, runtime_context):
                self.runtime_context = runtime_context
                self.checkpoint_store = factory.checkpoint_store

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
                if state.get("flow_status") == "awaiting_next_step_selector" and state.get("pending_interaction_answer"):
                    state.update(
                        {
                            "flow_status": "normal",
                            "next_step_choice": state["pending_interaction_answer"],
                            "pending_interaction_answer": "",
                        }
                    )
                    self.checkpoint_store.save(thread_id, state, source="loop", step=2)
                    self.runtime_context.event_sink.emit(
                        make_event("node.complete", "next_step_selector", message="已恢复并接住这次选择。")
                    )
                    return
                self.checkpoint_store.save(thread_id, state, source="loop", step=1)

        return SelectorResumeGraphApp(runtime), DummyConn()


class PendingInteractionWorkflowFactory:
    def __init__(self, checkpoint_store):
        self.checkpoint_store = checkpoint_store

    def __call__(self, settings, runtime=None):
        del settings
        factory = self

        class PendingInteractionGraphApp:
            def __init__(self):
                self.checkpoint_store = factory.checkpoint_store

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
                state.update(
                    {
                        "flow_status": "awaiting_post_lesson_choice",
                        "pending_interaction_kind": "post_lesson_choice",
                        "pending_interaction_prompt": "讲解完成后请选择下一步。",
                        "pending_interaction_options": [
                            {"value": "temporary_question", "label": "我还有临时问题"},
                            {"value": "start_test", "label": "没有问题，开始测试"},
                        ],
                    }
                )
                self.checkpoint_store.save(thread_id, state, source="loop", step=1)

        return PendingInteractionGraphApp(), DummyConn()


class MutableKnowledgeProvider:
    def __init__(self):
        self.files = {}

    def query(self, query):
        del query
        return ""

    def list_documents(self):
        return [
            {
                "filename": name,
                "size_bytes": meta["size_bytes"],
                "chunk_count": meta["chunk_count"],
            }
            for name, meta in sorted(self.files.items())
        ]

    def add_document(self, source_path):
        path = Path(source_path)
        self.files[path.name] = {
            "size_bytes": path.stat().st_size,
            "chunk_count": 1,
        }
        return True

    def delete_document(self, filename):
        return self.files.pop(filename, None) is not None

    def clear_documents(self):
        removed = len(self.files)
        self.files = {}
        return removed


class TopicConfirmWorkflowFactory:
    def __init__(self, checkpoint_store):
        self.checkpoint_store = checkpoint_store

    def __call__(self, settings, runtime=None):
        del settings
        factory = self

        class TopicConfirmGraphApp:
            def __init__(self, runtime_context):
                self.runtime_context = runtime_context
                self.checkpoint_store = factory.checkpoint_store

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
                if state.get("flow_status") == "assessment_pending":
                    state["assessment_questions"] = state.get("assessment_questions") or [{"id": 1, "question": "Q1"}]
                    state["flow_status"] = "awaiting_assessment"
                    self.checkpoint_store.save(thread_id, state, source="loop", step=3)
                    self.runtime_context.event_sink.emit(
                        make_event(
                            "assessment.form_ready",
                            "assessment_generator",
                            data={"questions": state["assessment_questions"]},
                        )
                    )
                    return
                if state.get("learning_resume_target") == "learning_plan_generator":
                    state["learning_plan"] = [
                        {"step_index": 0, "step_name": "基础概念", "node_ids": ["KM001"], "node_names": ["自动控制的一般概念"], "status": "in_progress"},
                    ]
                    state["learning_plan_current_step"] = 0
                    state["learning_plan_source"] = "profile_based"
                    state["learning_resume_target"] = "initial_node_selector"
                    self.checkpoint_store.save(thread_id, state, source="loop", step=3)
                    self.runtime_context.event_sink.emit(
                        make_event(
                            "learning_plan.generated",
                            "learning_plan_generator",
                            message="已生成学习路径",
                            data={"plan": state["learning_plan"], "total_steps": 1, "total_nodes": 1},
                        )
                    )
                if state.get("learning_resume_target") == "initial_node_selector":
                    state["flow_status"] = "normal"
                    state["tutor_content"] = "开始直接讲解。"
                    self.checkpoint_store.save(thread_id, state, source="loop", step=3)
                    self.runtime_context.event_sink.emit(
                        make_event(
                            "node.stream",
                            "tutor",
                            data={"text": "开始直接讲解。"},
                        )
                    )
                    return
                self.checkpoint_store.save(thread_id, state, source="loop", step=3)
                self.runtime_context.event_sink.emit(
                    make_event(
                        "session.info",
                        "api",
                        message="请重新输入学习主题。",
                    )
                )

        return TopicConfirmGraphApp(runtime), DummyConn()


class InterruptConfirmWorkflowFactory:
    def __init__(self, checkpoint_store):
        self.checkpoint_store = checkpoint_store

    def __call__(self, settings, runtime=None):
        del settings
        factory = self

        class InterruptConfirmGraphApp:
            def __init__(self, runtime_context):
                self.runtime_context = runtime_context
                self.checkpoint_store = factory.checkpoint_store

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
                if state.get("resume_tester") and state.get("tester_question"):
                    state["flow_status"] = "normal"
                    self.checkpoint_store.save(thread_id, state, source="loop", step=3)
                    self.runtime_context.event_sink.emit(
                        make_event(
                            "node.stream",
                            "tester",
                            data={"text": f"回到主线，请继续回答上一题：\n{state['tester_question']}"},
                        )
                    )
                    return
                self.checkpoint_store.save(thread_id, state, source="loop", step=3)

        return InterruptConfirmGraphApp(runtime), DummyConn()


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
        embedding_model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
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
    )


def create_test_client(tmp_path, *, checkpoint_store=None, workflow_factory=None, graph_rag_pipeline=None):
    checkpoint_store = checkpoint_store or FakeCheckpointStore()
    runtime = ApiRuntime(
        settings=build_test_settings(tmp_path),
        knowledge_provider=NoopKnowledgeProvider(),
        graph_rag_pipeline=graph_rag_pipeline,
        workflow_factory=workflow_factory or FakeWorkflowFactory(checkpoint_store),
        checkpoint_factory=lambda path: (checkpoint_store, DummyConn()),
    )
    app = create_api_app(runtime_factory=lambda: runtime)
    return TestClient(app)


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
        assert updated["model_name"] == "deepseek-v4-flash"
        assert updated["openai_api_base"] == "https://api.deepseek.com/v1"


def test_api_root_serves_frontend_index(tmp_path):
    with create_test_client(tmp_path) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "AI Tutor" in response.text


def test_stream_end_includes_pending_interaction_payload_for_state_pauses(tmp_path):
    thread_id = "session-pending-end"
    checkpoint_store = FakeCheckpointStore()
    with create_test_client(
        tmp_path,
        checkpoint_store=checkpoint_store,
        workflow_factory=PendingInteractionWorkflowFactory(checkpoint_store),
    ) as client:
        start = client.post("/api/start", json={"thread_id": thread_id, "topic": "控制理论"})
        assert start.status_code == 200

        stream = client.get(f"/api/stream?thread_id={thread_id}")

    assert stream.status_code == 200
    assert "event: session.end" in stream.text
    assert '"pending_interaction_kind": "post_lesson_choice"' in stream.text
    assert '"我还有临时问题"' in stream.text
    assert '"没有问题，开始测试"' in stream.text


def test_graph_b_data_sanitizes_non_json_values(tmp_path):
    try:
        import numpy as np
    except Exception:
        np = None
    try:
        import pandas as pd
    except Exception:
        pd = None

    class FakeNAType:
        __module__ = "pandas._libs.missing"

    class FakeArray:
        def tolist(self):
            return [float("nan"), 2]

    class FakeScalar:
        def item(self):
            return float("inf")

    class DirtyGraphPipeline:
        nodes = [
            {
                "node_id": "N1",
                "name": "节点一",
                "bad": float("nan"),
                "arr": np.array([1.0, float("inf")]) if np is not None else FakeArray(),
                "path": Path("graph/node.md"),
                "missing": pd.NA if pd is not None else FakeNAType(),
                "nested": {"ratio": float("-inf")},
            }
        ]
        edges = [
            {
                "source": "N1",
                "target": "N2",
                "relation_strength": float("nan"),
                "weight": np.float64(float("inf")) if np is not None else FakeScalar(),
                "evidence": [float("nan"), Path("edge.md")],
            }
        ]

    with create_test_client(tmp_path, graph_rag_pipeline=DirtyGraphPipeline()) as client:
        response = client.get("/api/graph/b/data.json")

    assert response.status_code == 200
    assert b"NaN" not in response.content
    assert b"Infinity" not in response.content
    payload = response.json()
    assert payload["nodes"][0]["bad"] is None
    assert payload["nodes"][0]["arr"] == [1.0, None] or payload["nodes"][0]["arr"] == [None, 2]
    assert payload["nodes"][0]["path"] == "graph/node.md"
    assert payload["nodes"][0]["missing"] is None
    assert payload["nodes"][0]["nested"]["ratio"] is None
    assert payload["edges"][0]["relation_strength"] == 0.5
    assert payload["edges"][0]["weight"] == 0.5
    assert payload["edges"][0]["evidence"] == [None, "edge.md"]


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

    assert meta_summary["display_title"] == "新对话"
    assert confirm_summary["display_title"] == "待确认：高等数学"


def test_history_summary_title_from_first_user_message(tmp_path):
    """有 message_history 时，pre-topic 状态应提取首条用户消息作为标题。"""
    checkpoint_store = FakeCheckpointStore()
    checkpoint_store.save(
        "thread-msg",
        {
            "current_topic": "",
            "proposed_topic": "",
            "flow_status": "topic_intake",
            "message_history": [
                {"role": "assistant", "content": "你好，想学什么？"},
                {"role": "user", "content": "我想学自动控制原理"},
            ],
        },
        source="loop",
        step=1,
    )
    summary = _checkpoint_summary("thread-msg", checkpoint_store.get_tuple({"configurable": {"thread_id": "thread-msg"}}))
    assert summary["display_title"] == "我想学自动控制原理"


def test_history_summary_title_truncates_long_message():
    """首条用户消息超过 30 字符时应截断加省略号。"""
    from ai_tutor_agent.interfaces.api.history import _extract_topic_from_messages

    long_msg = "这是一个非常非常长的用户消息用来测试截断功能是否正常工作请务必确保超过三十个字符"
    result = _extract_topic_from_messages({"message_history": [{"role": "user", "content": long_msg}]})
    assert len(result) <= 31  # 30 chars + "…"
    assert result.endswith("…")


def test_history_summary_fallback_to_proposed_topic():
    """current_topic 为空时应 fallback 到 proposed_topic。"""
    checkpoint_store = FakeCheckpointStore()
    checkpoint_store.save(
        "thread-fallback",
        {
            "current_topic": "",
            "proposed_topic": "线性代数",
            "flow_status": "normal",
            "message_history": [],
        },
        source="loop",
        step=1,
    )
    summary = _checkpoint_summary("thread-fallback", checkpoint_store.get_tuple({"configurable": {"thread_id": "thread-fallback"}}))
    assert summary["display_title"] == "线性代数"


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
        assert updated["state"]["coach_content"] == ""
        assert updated["state"]["needs_hint"] is False


def test_confirmed_topic_can_skip_existing_assessment_without_proposed_topic(tmp_path):
    thread_id = "session-skip-confirmed-assessment"
    checkpoint_store = FakeCheckpointStore()
    checkpoint_store.save(
        thread_id,
        {
            "current_topic": "自动控制原理",
            "current_user_goal": "自动控制原理",
            "session_goal": "自动控制原理",
            "proposed_topic": "",
            "flow_status": "awaiting_assessment",
            "assessment_questions": [{"id": 1, "question": "Q1"}],
            "assessment_answers": {"1": "B"},
            "assessment_state": {"draft": True},
            "message_history": [
                {
                    "role": "assistant",
                    "kind": "assessment_form",
                    "content": "快速摸底",
                    "data": {"questions": [{"id": 1, "question": "Q1"}], "answers": {"1": "B"}},
                }
            ],
        },
        source="loop",
        step=1,
    )
    runtime = ApiRuntime(
        settings=build_test_settings(tmp_path),
        knowledge_provider=NoopKnowledgeProvider(),
        workflow_factory=TopicConfirmWorkflowFactory(checkpoint_store),
        checkpoint_factory=lambda path: (checkpoint_store, DummyConn()),
    )

    with TestClient(create_api_app(runtime_factory=lambda: runtime)) as client:
        skip = client.post(
            "/api/confirm_topic",
            json={"thread_id": thread_id, "confirmed": True, "topic": "", "start_mode": "direct_tutor"},
        )
        assert skip.status_code == 200

        stream = client.get(f"/api/stream?thread_id={thread_id}")
        assert stream.status_code == 200
        assert "event: node.stream" in stream.text
        assert "开始直接讲解" in stream.text

        updated = client.get(f"/api/history/{thread_id}").json()
        state = updated["state"]
        assert state["current_topic"] == "自动控制原理"
        assert state["proposed_topic"] == ""
        assert state["flow_status"] == "normal"
        assert checkpoint_store.states[thread_id]["learning_resume_target"] == "initial_node_selector"
        assert state["assessment_questions"] == []
        assert state["assessment_answers"] == {}
        assert state["assessment_state"] == {}
        assessment_items = [item for item in state["message_history"] if item.get("kind") == "assessment_form"]
        assert assessment_items[-1]["data"]["locked"] is True
        assert assessment_items[-1]["data"]["statusText"] == "已跳过学前测评，答案已固定"
        locked_items = [item for item in state["message_history"] if item.get("kind") == "topic_confirmation_locked"]
        assert locked_items[-1]["data"] == {
            "topic": "自动控制原理",
            "label": "已跳过摸底，直接开始",
            "start_mode": "direct_tutor",
        }


def test_confirmed_topic_skip_accepts_null_topic_from_restored_assessment_card(tmp_path):
    thread_id = "session-skip-restored-null-topic"
    checkpoint_store = FakeCheckpointStore()
    checkpoint_store.save(
        thread_id,
        {
            "current_topic": "自动控制原理",
            "current_user_goal": "自动控制原理",
            "session_goal": "自动控制原理",
            "proposed_topic": "",
            "flow_status": "awaiting_assessment",
            "assessment_questions": [{"id": 1, "question": "Q1"}],
            "assessment_answers": {"1": "B"},
            "assessment_state": {"draft": True},
        },
        source="loop",
        step=1,
    )
    runtime = ApiRuntime(
        settings=build_test_settings(tmp_path),
        knowledge_provider=NoopKnowledgeProvider(),
        workflow_factory=TopicConfirmWorkflowFactory(checkpoint_store),
        checkpoint_factory=lambda path: (checkpoint_store, DummyConn()),
    )

    with TestClient(create_api_app(runtime_factory=lambda: runtime)) as client:
        skip = client.post(
            "/api/confirm_topic",
            json={"thread_id": thread_id, "confirmed": True, "topic": None, "start_mode": "direct_tutor"},
        )
        assert skip.status_code == 200

        stream = client.get(f"/api/stream?thread_id={thread_id}")
        assert stream.status_code == 200
        assert "开始直接讲解" in stream.text

        state = client.get(f"/api/history/{thread_id}").json()["state"]
        assert state["current_topic"] == "自动控制原理"
        assert state["flow_status"] == "normal"
        assert state["assessment_questions"] == []


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


def test_api_start_rejects_new_message_while_previous_turn_is_still_running(tmp_path):
    runtime = ApiRuntime(
        settings=build_test_settings(tmp_path),
        knowledge_provider=NoopKnowledgeProvider(),
        workflow_factory=FakeWorkflowFactory(FakeCheckpointStore()),
        checkpoint_factory=lambda path: (FakeCheckpointStore(), DummyConn()),
    )

    with TestClient(create_api_app(runtime_factory=lambda: runtime)) as client:
        session = runtime.session_manager.get_or_create("busy-thread")
        session["is_running"] = True
        session["awaiting_input"] = False

        response = client.post(
            "/api/start",
            json={"thread_id": "busy-thread", "topic": "新的问题"},
        )

        assert response.status_code == 409
        assert "previous turn" in response.json()["detail"]
        with pytest.raises(queue.Empty):
            session["input_q"].get_nowait()


def test_api_start_does_not_buffer_topic_during_topic_confirmation_resume(tmp_path):
    thread_id = "session-topic-confirm-resume"
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
        workflow_factory=TopicConfirmWorkflowFactory(checkpoint_store),
        checkpoint_factory=lambda path: (checkpoint_store, DummyConn()),
    )

    with TestClient(create_api_app(runtime_factory=lambda: runtime)) as client:
        start = client.post(
            "/api/start",
            json={"thread_id": thread_id, "topic": "矩阵求逆"},
        )
        assert start.status_code == 200

        stream = client.get(f"/api/stream?thread_id={thread_id}")
        assert stream.status_code == 200
        assert "event: session.end" in stream.text

        session = runtime.session_manager.get_or_create(thread_id)
        with pytest.raises(queue.Empty):
            session["input_q"].get_nowait()


def test_submit_assessment_schedules_resume_when_worker_is_still_finishing(tmp_path):
    thread_id = "session-race-assessment"
    checkpoint_store = FakeCheckpointStore()
    checkpoint_store.save(
        thread_id,
        {
            "current_topic": "控制理论",
            "assessment_questions": [{"id": 1, "question": "Q1"}],
            "assessment_answers": {},
            "flow_status": "awaiting_assessment",
        },
        source="loop",
        step=1,
    )

    with create_test_client(
        tmp_path,
        checkpoint_store=checkpoint_store,
        workflow_factory=SlowResumeWorkflowFactory(checkpoint_store),
    ) as client:
        resume = client.post(f"/api/sessions/{thread_id}/resume")
        assert resume.status_code == 200

        submit = client.post(
            "/api/submit_assessment",
            json={"thread_id": thread_id, "answers": {"1": "C"}},
        )
        assert submit.status_code == 200

        deadline = time.time() + 2
        while time.time() < deadline:
            detail = client.get(f"/api/history/{thread_id}").json()
            if detail["state"]["is_assessed"] is True:
                break
            time.sleep(0.05)

        final_detail = client.get(f"/api/history/{thread_id}").json()
        assert final_detail["state"]["is_assessed"] is True
        assert final_detail["state"]["flow_status"] == "normal"


def test_assessment_draft_persists_partial_answers_for_history_restore(tmp_path):
    thread_id = "session-assessment-draft"
    checkpoint_store = FakeCheckpointStore()
    checkpoint_store.save(
        thread_id,
        {
            "current_topic": "控制理论",
            "assessment_questions": [{"id": 1, "question": "Q1"}],
            "assessment_answers": {},
            "flow_status": "awaiting_assessment",
        },
        source="loop",
        step=1,
    )

    with create_test_client(tmp_path, checkpoint_store=checkpoint_store) as client:
        response = client.post(
            "/api/assessment_draft",
            json={"thread_id": thread_id, "answers": {"1": "C"}},
        )

        assert response.status_code == 200
        detail = client.get(f"/api/history/{thread_id}").json()
        assert detail["state"]["assessment_answers"] == {"1": "C"}


def test_confirm_topic_with_empty_topic_falls_back_to_greeting(tmp_path):
    thread_id = "session-empty-topic-confirm"
    checkpoint_store = FakeCheckpointStore()
    checkpoint_store.save(
        thread_id,
        {
            "current_topic": "",
            "proposed_topic": "",
            "flow_status": "awaiting_topic_confirmation",
            "assessment_questions": [],
            "assessment_answers": {},
        },
        source="loop",
        step=1,
    )

    with create_test_client(
        tmp_path,
        checkpoint_store=checkpoint_store,
        workflow_factory=TopicConfirmWorkflowFactory(checkpoint_store),
    ) as client:
        confirm = client.post(
            "/api/confirm_topic",
            json={"thread_id": thread_id, "confirmed": True, "topic": "   "},
        )
        assert confirm.status_code == 200

        stream = client.get(f"/api/stream?thread_id={thread_id}")
        assert "未检测到可确认的学习主题" in stream.text
        assert "event: assessment.form_ready" not in stream.text

        updated = client.get(f"/api/history/{thread_id}").json()
        assert updated["state"]["flow_status"] == "greeting"
        assert updated["state"]["current_topic"] == ""


def test_confirm_interrupt_resumes_existing_tester_question(tmp_path):
    thread_id = "session-interrupt-confirm"
    checkpoint_store = FakeCheckpointStore()
    checkpoint_store.save(
        thread_id,
        {
            "current_topic": "控制理论",
            "flow_status": "awaiting_interrupt_confirmation",
            "is_assessed": True,
            "tester_question": "请解释闭环系统稳定性判断条件。",
            "resume_tester": True,
            "conversation_history": [
                {"role": "user", "kind": "interruption_user", "content": "为什么这里看特征根？"},
                {"role": "assistant", "kind": "interruption", "content": "因为稳定性与极点位置有关。"},
                {"role": "assistant", "kind": "tutor", "content": "主线讲解"},
            ],
        },
        source="loop",
        step=1,
    )

    with create_test_client(
        tmp_path,
        checkpoint_store=checkpoint_store,
        workflow_factory=InterruptConfirmWorkflowFactory(checkpoint_store),
    ) as client:
        confirm = client.post(
            "/api/confirm_interrupt",
            json={"thread_id": thread_id, "confirmed": True},
        )
        assert confirm.status_code == 200

        stream = client.get(f"/api/stream?thread_id={thread_id}")
        assert "已确认回到主线" in stream.text
        assert "回到主线，请继续回答上一题" in stream.text

        updated = client.get(f"/api/history/{thread_id}").json()
        assert updated["state"]["flow_status"] == "normal"
        assert updated["state"]["resume_tester"] is True
        assert updated["state"]["conversation_history"] == [
            {"role": "assistant", "kind": "tutor", "content": "主线讲解"},
        ]


def test_confirm_interrupt_false_keeps_follow_up_mode(tmp_path):
    thread_id = "session-interrupt-follow-up"
    checkpoint_store = FakeCheckpointStore()
    checkpoint_store.save(
        thread_id,
        {
            "current_topic": "控制理论",
            "flow_status": "awaiting_interrupt_confirmation",
            "is_assessed": True,
            "tester_question": "请解释闭环系统稳定性判断条件。",
            "resume_tester": True,
            "conversation_history": [
                {"role": "user", "kind": "interruption_user", "content": "为什么这里看特征根？"},
                {"role": "assistant", "kind": "interruption", "content": "因为稳定性与极点位置有关。"},
            ],
        },
        source="loop",
        step=1,
    )

    with create_test_client(
        tmp_path,
        checkpoint_store=checkpoint_store,
        workflow_factory=InterruptConfirmWorkflowFactory(checkpoint_store),
    ) as client:
        confirm = client.post(
            "/api/confirm_interrupt",
            json={"thread_id": thread_id, "confirmed": False},
        )
        assert confirm.status_code == 200

        stream = client.get(f"/api/stream?thread_id={thread_id}")
        assert "可以继续输入临时问题" in stream.text
        assert "回到主线，请继续回答上一题" not in stream.text

        updated = client.get(f"/api/history/{thread_id}").json()
        assert updated["state"]["flow_status"] == "awaiting_interrupt_confirmation"
        assert updated["state"]["resume_tester"] is True
        assert updated["state"]["conversation_history"] == [
            {"role": "user", "kind": "interruption_user", "content": "为什么这里看特征根？"},
            {"role": "assistant", "kind": "interruption", "content": "因为稳定性与极点位置有关。"},
        ]


def test_knowledge_upload_and_clear_flow(tmp_path):
    runtime = ApiRuntime(
        settings=build_test_settings(tmp_path),
        knowledge_provider=MutableKnowledgeProvider(),
        workflow_factory=FakeWorkflowFactory(FakeCheckpointStore()),
        checkpoint_factory=lambda path: (FakeCheckpointStore(), DummyConn()),
    )

    with TestClient(create_api_app(runtime_factory=lambda: runtime)) as client:
        upload = client.post(
            "/api/upload",
            files={"file": ("notes.md", b"# control theory", "text/markdown")},
        )
        assert upload.status_code == 200
        assert upload.json()["status"] == "success"

        listed = client.get("/api/knowledge/files")
        assert listed.status_code == 200
        assert listed.json()["items"][0]["filename"] == "notes.md"

        cleared = client.delete("/api/knowledge/files")
        assert cleared.status_code == 200
        assert cleared.json()["status"] == "success"
        assert cleared.json()["removed"] == 1

        listed_after = client.get("/api/knowledge/files")
        assert listed_after.status_code == 200
        assert listed_after.json()["items"] == []


def test_knowledge_upload_sanitizes_path_like_filename(tmp_path):
    runtime = ApiRuntime(
        settings=build_test_settings(tmp_path),
        knowledge_provider=MutableKnowledgeProvider(),
        workflow_factory=FakeWorkflowFactory(FakeCheckpointStore()),
        checkpoint_factory=lambda path: (FakeCheckpointStore(), DummyConn()),
    )

    with TestClient(create_api_app(runtime_factory=lambda: runtime)) as client:
        upload = client.post(
            "/api/upload",
            files={"file": (r"C:\Users\tester\Desktop\notes.md", b"# control theory", "text/markdown")},
        )
        assert upload.status_code == 200
        assert upload.json()["status"] == "success"
        assert upload.json()["filename"] == "notes.md"

        listed = client.get("/api/knowledge/files")
        assert listed.status_code == 200
        assert listed.json()["items"][0]["filename"] == "notes.md"


def test_api_answer_rejects_when_not_awaiting_input(tmp_path):
    runtime = ApiRuntime(
        settings=build_test_settings(tmp_path),
        knowledge_provider=NoopKnowledgeProvider(),
        workflow_factory=FakeWorkflowFactory(FakeCheckpointStore()),
        checkpoint_factory=lambda path: (FakeCheckpointStore(), DummyConn()),
    )

    with TestClient(create_api_app(runtime_factory=lambda: runtime)) as client:
        response = client.post(
            "/api/answer",
            json={"thread_id": "idle-thread", "answer": "hello"},
        )
        assert response.status_code == 409
        assert response.json()["detail"] == "Session is not waiting for input."


def test_api_answer_accepts_only_while_awaiting_input(tmp_path):
    runtime = ApiRuntime(
        settings=build_test_settings(tmp_path),
        knowledge_provider=NoopKnowledgeProvider(),
        workflow_factory=FakeWorkflowFactory(FakeCheckpointStore()),
        checkpoint_factory=lambda path: (FakeCheckpointStore(), DummyConn()),
    )

    with TestClient(create_api_app(runtime_factory=lambda: runtime)) as client:
        session = runtime.session_manager.get_or_create("awaiting-thread")
        session["is_running"] = True
        session["awaiting_input"] = True

        response = client.post(
            "/api/answer",
            json={"thread_id": "awaiting-thread", "answer": "hello"},
        )
        assert response.status_code == 200
        assert session["input_q"].get_nowait() == "hello"
        assert session["awaiting_input"] is False


def test_api_answer_can_resume_pending_selector_from_checkpoint(tmp_path):
    checkpoint_store = FakeCheckpointStore()
    checkpoint_store.save(
        "selector-thread",
        {
            "flow_status": "awaiting_next_step_selector",
            "pending_interaction_kind": "next_step_selector",
            "pending_interaction_prompt": "下一步怎么继续？",
            "pending_interaction_options": [
                {"value": "continue_deeper", "label": "继续深入"},
                {"value": "practice_now", "label": "来一道题"},
            ],
            "pending_interaction_recommended": "continue_deeper",
            "pending_interaction_answer": "",
        },
    )
    runtime = ApiRuntime(
        settings=build_test_settings(tmp_path),
        knowledge_provider=NoopKnowledgeProvider(),
        workflow_factory=SelectorResumeWorkflowFactory(checkpoint_store),
        checkpoint_factory=lambda path: (checkpoint_store, DummyConn()),
    )

    with TestClient(create_api_app(runtime_factory=lambda: runtime)) as client:
        response = client.post(
            "/api/answer",
            json={"thread_id": "selector-thread", "answer": "practice_now"},
        )
        assert response.status_code == 200

        deadline = time.time() + 2
        while time.time() < deadline:
            updated = checkpoint_store.states.get("selector-thread", {})
            if updated.get("flow_status") == "normal":
                break
            time.sleep(0.05)

        updated = checkpoint_store.states["selector-thread"]
        assert updated["flow_status"] == "normal"
        assert updated["next_step_choice"] == "practice_now"
        assert updated["pending_interaction_answer"] == ""


def test_api_answer_can_resume_new_pending_interaction_from_checkpoint(tmp_path):
    checkpoint_store = FakeCheckpointStore()
    checkpoint_store.save(
        "post-lesson-thread",
        {
            "flow_status": "awaiting_post_lesson_choice",
            "learning_phase": "post_lesson_choice",
            "learning_resume_target": "post_lesson_choice",
            "pending_interaction_kind": "post_lesson_choice",
            "pending_interaction_answer": "",
        },
    )
    runtime = ApiRuntime(
        settings=build_test_settings(tmp_path),
        knowledge_provider=NoopKnowledgeProvider(),
        workflow_factory=SelectorResumeWorkflowFactory(checkpoint_store),
        checkpoint_factory=lambda path: (checkpoint_store, DummyConn()),
    )

    with TestClient(create_api_app(runtime_factory=lambda: runtime)) as client:
        response = client.post(
            "/api/answer",
            json={"thread_id": "post-lesson-thread", "answer": "start_test"},
        )
        assert response.status_code == 200

        deadline = time.time() + 2
        while time.time() < deadline:
            updated = checkpoint_store.states.get("post-lesson-thread", {})
            if updated.get("pending_interaction_answer") == "start_test":
                break
            time.sleep(0.05)

        updated = checkpoint_store.states["post-lesson-thread"]
        assert updated["pending_interaction_answer"] == "start_test"


def test_api_answer_can_resume_objective_answers_from_checkpoint(tmp_path):
    checkpoint_store = FakeCheckpointStore()
    checkpoint_store.save(
        "objective-thread",
        {
            "flow_status": "awaiting_objective_answers",
            "learning_phase": "node_quiz_batch",
            "learning_resume_target": "objective_test_scorer",
            "pending_interaction_kind": "objective_test_answers",
            "pending_interaction_answer": "",
        },
    )
    runtime = ApiRuntime(
        settings=build_test_settings(tmp_path),
        knowledge_provider=NoopKnowledgeProvider(),
        workflow_factory=SelectorResumeWorkflowFactory(checkpoint_store),
        checkpoint_factory=lambda path: (checkpoint_store, DummyConn()),
    )

    with TestClient(create_api_app(runtime_factory=lambda: runtime)) as client:
        response = client.post(
            "/api/answer",
            json={"thread_id": "objective-thread", "answer": '{"Q1":"A"}'},
        )
        assert response.status_code == 200

        deadline = time.time() + 2
        while time.time() < deadline:
            updated = checkpoint_store.states.get("objective-thread", {})
            if updated.get("pending_interaction_answer") == '{"Q1":"A"}':
                break
            time.sleep(0.05)

        updated = checkpoint_store.states["objective-thread"]
        assert updated["pending_interaction_answer"] == '{"Q1":"A"}'


def test_waiting_for_input_timeout_emits_error_and_end(monkeypatch, tmp_path):
    import ai_tutor_agent.interfaces.api.adapter as adapter_module

    monkeypatch.setattr(adapter_module, "INPUT_WAIT_TIMEOUT_SECONDS", 0.05)

    checkpoint_store = FakeCheckpointStore()
    runtime = ApiRuntime(
        settings=build_test_settings(tmp_path),
        knowledge_provider=NoopKnowledgeProvider(),
        workflow_factory=WaitingInputWorkflowFactory(checkpoint_store),
        checkpoint_factory=lambda path: (checkpoint_store, DummyConn()),
    )

    with TestClient(create_api_app(runtime_factory=lambda: runtime)) as client:
        start = client.post("/api/start", json={"thread_id": "timeout-thread", "topic": "控制理论"})
        assert start.status_code == 200

        stream = client.get("/api/stream?thread_id=timeout-thread")
        assert "event: session.awaiting_input" in stream.text
        assert "event: session.error" in stream.text
        assert "Timed out while waiting for user input." in stream.text
        assert "event: session.end" in stream.text

        detail = client.get("/api/history/timeout-thread")
        assert detail.status_code == 200
        assert detail.json()["runtime"]["is_running"] is False
        assert detail.json()["runtime"]["awaiting_input"] is False


def test_assessment_stream_event_contract_includes_question_payload(tmp_path):
    thread_id = "session-assessment-contract"
    with create_test_client(tmp_path) as client:
        start = client.post("/api/start", json={"thread_id": thread_id, "topic": "控制理论"})
        assert start.status_code == 200

        stream = client.get(f"/api/stream?thread_id={thread_id}")
        assert stream.status_code == 200
        assert 'event: assessment.form_ready' in stream.text
        assert '"type": "assessment.form_ready"' in stream.text
        assert '"source": "assessment_generator"' in stream.text
        assert '"questions": [{' in stream.text
        assert '"question": "你对控制系统稳定性的理解程度如何？"' in stream.text


def test_profile_radar_stream_event_contract_includes_scores(tmp_path):
    thread_id = "session-profile-contract"
    with create_test_client(tmp_path) as client:
        client.post("/api/start", json={"thread_id": thread_id, "topic": "控制理论"})
        client.get(f"/api/stream?thread_id={thread_id}")
        submit = client.post(
            "/api/submit_assessment",
            json={"thread_id": thread_id, "answers": {"1": "C"}},
        )
        assert submit.status_code == 200

        stream = client.get(f"/api/stream?thread_id={thread_id}")
        assert stream.status_code == 200
        assert 'event: profile.radar_data' in stream.text
        assert '"type": "profile.radar_data"' in stream.text
        assert '"source": "user_profiler"' in stream.text
        assert '"dimensions": ["基础概念", "规则理解", "逻辑推理", "场景应用", "细节辨析", "综合应用"]' in stream.text
        assert '"objective_scores": [65, 60, 55, 50, 45, 40]' in stream.text


def test_session_manager_reset_queues_reuses_existing_queue_instances():
    from ai_tutor_agent.interfaces.api.runtime import SessionManager

    manager = SessionManager()
    session = manager.get_or_create("thread-queue")
    event_q = session["event_q"]
    input_q = session["input_q"]
    event_q.put("event")
    input_q.put("input")

    reset = manager.reset_queues("thread-queue")

    assert reset["event_q"] is event_q
    assert reset["input_q"] is input_q
    assert reset["awaiting_input"] is False
    with pytest.raises(queue.Empty):
        event_q.get_nowait()
    with pytest.raises(queue.Empty):
        input_q.get_nowait()


def test_session_manager_prepare_worker_start_prevents_double_start():
    from ai_tutor_agent.interfaces.api.runtime import SessionManager

    manager = SessionManager()
    worker1 = threading.Thread(target=lambda: None)
    worker2 = threading.Thread(target=lambda: None)

    first = manager.prepare_worker_start("thread-worker", worker1)
    second = manager.prepare_worker_start("thread-worker", worker2)

    assert first is not None
    assert second is None
    assert manager.get_or_create("thread-worker")["worker"] is worker1


def test_runtime_build_falls_back_when_local_embedding_cache_is_missing(monkeypatch, tmp_path):
    import ai_tutor_agent.interfaces.api.runtime as runtime_module

    monkeypatch.setattr(
        runtime_module,
        "LocalFileKnowledgeProvider",
        lambda settings: (_ for _ in ()).throw(RuntimeError("local cache missing")),
    )

    runtime = runtime_module.build_runtime(build_test_settings(tmp_path))

    assert isinstance(runtime.knowledge_provider, NoopKnowledgeProvider)


def test_local_config_round_trip(monkeypatch, tmp_path):
    for key in [
        "CHAT_PROFILE",
        "GOOGLE_API_KEY",
        "GEMINI_API_KEY",
        "QWEN_API_KEY",
        "DEEPSEEK_API_KEY",
        "OPENAI_API_KEY",
        "OPENAI_API_BASE",
        "MINIMAX_API_KEY",
        "GLM_API_KEY",
        "MODEL_NAME",
        "QUESTION_HELP_MODEL_NAME",
        "QUESTION_HELP_OPENAI_API_BASE",
        "LLM_PROVIDER",
    ]:
        monkeypatch.delenv(key, raising=False)
    env_path = tmp_path / ".env.test"
    env_path.write_text(
        "\n".join(
            [
                "CHAT_PROFILE=gemini",
                "GOOGLE_API_KEY=google-key",
                "GEMINI_API_KEY=gemini-key",
                "EMBEDDING_PROVIDER=local",
                "EMBEDDING_MODEL_NAME=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
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
        assert current.json()["question_help_model_name"] == "qwen-vl-max-latest"

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
                "question_help_model_name": "qwen-vl-plus-latest",
                "embedding_provider": "local",
                "embedding_model_name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                "pdf_parse_backend": "auto",
                "knowledge_chunk_size": 800,
                "knowledge_chunk_overlap": 100,
                "knowledge_top_k": 5,
                "vector_store_dir": "data/chroma_db",
                "proxy_host": "127.0.0.1",
                "proxy_port": "7892",
                "proxy_scheme": "http",
                "http_proxy": "http://127.0.0.1:7890",
                "https_proxy": "http://127.0.0.1:7890",
                "mineru_proxy_mode": "direct",
                "mineru_connect_timeout_seconds": 7,
            },
        )
        assert updated.status_code == 200
        payload = updated.json()
        assert payload["config"]["chat_profile"] == "qwen"
        assert payload["config"]["model_name"] == "qwen-plus"
        assert payload["local"]["qwen_api_key"] == "****-new"
        assert payload["local"]["has_qwen_api_key"] is True
        assert payload["local"]["question_help_model_name"] == "qwen-vl-plus-latest"
        assert payload["local"]["knowledge_top_k"] == 5
        assert payload["local"]["vector_store_dir"] == "data/chroma_db"
        assert payload["local"]["proxy_port"] == "7892"
        assert payload["local"]["mineru_proxy_mode"] == "direct"

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
                "question_help_model_name": "qwen-vl-plus-latest",
                "embedding_provider": "local",
                "embedding_model_name": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                "pdf_parse_backend": "local",
                "knowledge_chunk_size": 800,
                "knowledge_chunk_overlap": 100,
                "knowledge_top_k": 5,
                "vector_store_dir": "data/chroma_db",
                "proxy_host": "127.0.0.1",
                "proxy_port": "7892",
                "proxy_scheme": "http",
                "http_proxy": "http://127.0.0.1:7890",
                "https_proxy": "http://127.0.0.1:7890",
                "mineru_proxy_mode": "inherit",
                "mineru_connect_timeout_seconds": 5,
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
        assert "QUESTION_HELP_MODEL_NAME=qwen-vl-plus-latest" in content
        assert "VECTOR_STORE_DIR=data/chroma_db" in content
        assert "CHROMA_DIR=data/chroma_db" in content
        assert "PROXY_PORT=7892" in content

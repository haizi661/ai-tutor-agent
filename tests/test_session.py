from types import SimpleNamespace

from ai_tutor_agent.application.session import run_learning_session
from ai_tutor_agent.core.ports import BufferedEventSink, RuntimeContext
from ai_tutor_agent.knowledge_map.student_state import StudentStateStore


class FakeApp:
    def __init__(self, state_values):
        self.state_values = state_values
        self.updated = None
        self.invocations = []

    def get_state(self, config):
        del config
        return SimpleNamespace(values=self.state_values)

    def update_state(self, config, values):
        self.updated = (config, values)

    def invoke(self, payload, config):
        self.invocations.append((payload, config))


class StubGraphPipeline:
    def __init__(self):
        self.node_map = {
            "KM001": {
                "node_id": "KM001",
                "name": "稳定性",
                "chapter": "chapter_01",
                "core_concepts": ["稳定性定义"],
                "key_points": ["先看最终是否回到平衡点"],
                "related_nodes": ["KM002"],
                "recommended_next_nodes": ["KM002"],
                "prerequisite_nodes": [],
                "extra": {"common_errors": ["把稳定性和瞬态性能混在一起"]},
                "importance_level": "3",
            },
            "KM002": {
                "node_id": "KM002",
                "name": "负反馈",
                "chapter": "chapter_02",
                "core_concepts": ["负反馈作用"],
                "key_points": ["说明负反馈如何改善系统性能"],
                "related_nodes": [],
                "recommended_next_nodes": [],
                "prerequisite_nodes": ["KM001"],
                "extra": {"common_errors": []},
                "importance_level": "3",
            },
        }


def test_run_learning_session_uses_new_turn_for_pre_topic_history():
    sink = BufferedEventSink()
    app = FakeApp(
        {
            "current_topic": "你好，你是什么模型呢",
            "flow_status": "greeting",
            "is_assessed": False,
        }
    )

    run_learning_session(
        app,
        sink,
        thread_id="thread-1",
        topic="你是什么模型",
        current_state=app.get_state({"configurable": {"thread_id": "thread-1"}}),
    )

    assert app.updated is None
    payload, config = app.invocations[0]
    assert payload["current_topic"] == "你是什么模型"
    assert payload["flow_status"] == "greeting"
    assert payload["proposed_topic"] == ""
    assert config == {"configurable": {"thread_id": "thread-1"}}
    assert any("按你刚输入的新内容继续" in event.message for event in sink.events)


def test_run_learning_session_keeps_normal_resume_for_existing_progress():
    sink = BufferedEventSink()
    app = FakeApp(
        {
            "current_topic": "控制理论",
            "flow_status": "awaiting_assessment",
            "is_assessed": False,
        }
    )

    run_learning_session(
        app,
        sink,
        thread_id="thread-2",
        topic="你是什么模型",
        current_state=app.get_state({"configurable": {"thread_id": "thread-2"}}),
    )

    assert app.updated is None
    assert app.invocations == [(None, {"configurable": {"thread_id": "thread-2"}})]
    assert any("系统将从上次进度继续" in event.message for event in sink.events)


def test_run_learning_session_does_not_resume_empty_pre_topic_history():
    sink = BufferedEventSink()
    app = FakeApp(
        {
            "current_topic": "你是什么模型",
            "flow_status": "meta_qa",
            "is_assessed": False,
        }
    )

    run_learning_session(
        app,
        sink,
        thread_id="thread-3",
        topic="",
        current_state=app.get_state({"configurable": {"thread_id": "thread-3"}}),
    )

    assert app.updated is None
    assert app.invocations == []
    assert any("主题沟通阶段" in event.message for event in sink.events)


def test_run_learning_session_interrupt_follow_up_keeps_context_history():
    sink = BufferedEventSink()
    app = FakeApp(
        {
            "current_topic": "控制理论",
            "flow_status": "awaiting_interrupt_confirmation",
            "is_assessed": True,
            "resume_tester": True,
            "conversation_history": [
                {"role": "user", "kind": "interruption_user", "content": "上一轮追问"},
                {"role": "assistant", "kind": "interruption", "content": "上一轮解答"},
            ],
        }
    )

    run_learning_session(
        app,
        sink,
        thread_id="thread-4",
        topic="那这个闭环怎么判断稳定？",
        current_state=app.get_state({"configurable": {"thread_id": "thread-4"}}),
    )

    assert app.updated is None
    payload, config = app.invocations[0]
    assert payload["interrupt_query"] == "那这个闭环怎么判断稳定？"
    assert payload["resume_tester"] is True
    assert payload["conversation_history"][-1] == {
        "role": "user",
        "kind": "interruption_user",
        "content": "那这个闭环怎么判断稳定？",
    }
    assert config == {"configurable": {"thread_id": "thread-4"}}


def test_run_learning_session_resume_mainline_clears_interrupt_history():
    sink = BufferedEventSink()
    app = FakeApp(
        {
            "current_topic": "控制理论",
            "flow_status": "awaiting_interrupt_confirmation",
            "is_assessed": True,
            "tester_question": "请继续分析闭环系统稳定性。",
            "conversation_history": [
                {"role": "user", "kind": "interruption_user", "content": "临时追问1"},
                {"role": "assistant", "kind": "interruption", "content": "临时解答1"},
                {"role": "assistant", "kind": "tutor", "content": "主线讲解"},
            ],
        }
    )

    run_learning_session(
        app,
        sink,
        thread_id="thread-5",
        topic="继续主线",
        current_state=app.get_state({"configurable": {"thread_id": "thread-5"}}),
    )

    assert app.updated is None
    payload, config = app.invocations[0]
    assert payload["flow_status"] == "normal"
    assert payload["interrupt_query"] == ""
    assert payload["resume_tester"] is True
    assert payload["conversation_history"] == [
        {"role": "assistant", "kind": "tutor", "content": "主线讲解"},
    ]
    assert config == {"configurable": {"thread_id": "thread-5"}}


def test_run_learning_session_announces_homework_on_second_login():
    sink = BufferedEventSink()
    app = FakeApp(
        {
            "current_topic": "自动控制原理",
            "flow_status": "homework_assigned",
            "is_assessed": True,
            "homework_status": "assigned",
            "homework_items": [
                {"question_id": "HW-KM001", "prompt": "围绕“稳定性”说明核心判断依据。"},
                {"question_id": "HW-KM002", "prompt": "围绕“负反馈”说明其典型作用。"},
            ],
        }
    )

    run_learning_session(
        app,
        sink,
        thread_id="thread-6",
        topic="",
        current_state=app.get_state({"configurable": {"thread_id": "thread-6"}}),
    )

    payload, config = app.invocations[0]
    assert payload["learning_resume_target"] == "session_resume_router"
    assert payload["learning_phase"] == "homework_resume"
    assert config == {"configurable": {"thread_id": "thread-6"}}
    assert any("上次留下的作业" in event.message for event in sink.events)


def test_run_learning_session_respects_deferred_homework_choice_on_restore():
    sink = BufferedEventSink()
    app = FakeApp(
        {
            "current_topic": "自动控制原理",
            "flow_status": "normal",
            "is_assessed": True,
            "homework_status": "deferred",
            "homework_items": [{"question_id": "HW-KM001", "prompt": "围绕“稳定性”说明核心判断依据。"}],
            "learning_resume_target": "node_content_loader",
            "next_node_candidate_id": "KM002",
            "next_node_candidate_name": "负反馈",
        }
    )

    run_learning_session(
        app,
        sink,
        thread_id="thread-6b",
        topic="",
        current_state=app.get_state({"configurable": {"thread_id": "thread-6b"}}),
    )

    assert app.invocations == [(None, {"configurable": {"thread_id": "thread-6b"}})]
    assert any("按你上次的选择继续学习" in event.message for event in sink.events)


def test_run_learning_session_can_resume_next_node_from_homework_state():
    sink = BufferedEventSink()
    app = FakeApp(
        {
            "current_topic": "自动控制原理",
            "flow_status": "homework_assigned",
            "is_assessed": True,
            "homework_status": "assigned",
            "homework_items": [{"question_id": "HW-KM001", "prompt": "围绕“稳定性”说明核心判断依据。"}],
            "next_node_candidate_id": "KM002",
            "next_node_candidate_name": "负反馈",
        }
    )

    run_learning_session(
        app,
        sink,
        thread_id="thread-7",
        topic="继续学习",
        current_state=app.get_state({"configurable": {"thread_id": "thread-7"}}),
    )

    payload, config = app.invocations[0]
    assert payload["learning_resume_target"] == "tutor"
    assert payload["current_user_goal"] == "负反馈"
    assert payload["homework_status"] == "deferred"
    assert config == {"configurable": {"thread_id": "thread-7"}}


def test_run_learning_session_can_generate_consolidation_homework(tmp_path):
    sink = BufferedEventSink()
    app = FakeApp(
        {
            "current_topic": "自动控制原理",
            "flow_status": "normal",
            "is_assessed": True,
            "learning_phase": "daily_wrapup",
            "student_id": "student_a",
            "student_state_snapshot": {
                "visited_nodes": ["KM001", "KM002"],
                "wrong_nodes": ["KM001"],
            },
        }
    )
    runtime_context = RuntimeContext(
        graph_rag_pipeline=StubGraphPipeline(),
        student_state_store=StudentStateStore(tmp_path / "student_states"),
    )

    run_learning_session(
        app,
        sink,
        thread_id="thread-8",
        topic="先巩固",
        current_state=app.get_state({"configurable": {"thread_id": "thread-8"}}),
        runtime_context=runtime_context,
    )

    assert app.updated is not None
    _, values = app.updated
    assert values["homework_status"] == "assigned"
    assert len(values["homework_items"]) >= 1

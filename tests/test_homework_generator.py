from ai_tutor_agent.core.ports import BufferedEventSink, RuntimeContext
from ai_tutor_agent.nodes.homework_generator import build_homework_generator_node
from ai_tutor_agent.orchestration import workflow as workflow_module


class FakeGraphPipeline:
    def __init__(self):
        self.node_map = {
            "KM001": {
                "node_id": "KM001",
                "name": "稳定性基础",
                "core_concepts": ["稳定性定义", "有界响应"],
                "key_points": ["判断响应是否收敛"],
                "recommended_next_nodes": ["KM002"],
                "related_nodes": [],
                "prerequisite_nodes": [],
            },
            "KM002": {
                "node_id": "KM002",
                "name": "劳斯判据",
                "core_concepts": ["劳斯表"],
                "key_points": ["首列符号判断稳定性"],
                "recommended_next_nodes": [],
                "related_nodes": [],
                "prerequisite_nodes": ["KM001"],
            },
        }


class FakeStudentState:
    def __init__(self, student_id="student_a"):
        self.student_id = student_id
        self.current_node_id = "KM001"
        self.visited_nodes = ["KM001", "KM002"]
        self.completed_nodes = ["KM001"]
        self.wrong_nodes = ["KM002"]
        self.homework = []
        self.homework_assignments = []

    def add_homework(self, question_id):
        self.homework.append(question_id)

    def to_dict(self):
        return {
            "student_id": self.student_id,
            "current_node_id": self.current_node_id,
            "visited_nodes": list(self.visited_nodes),
            "completed_nodes": list(self.completed_nodes),
            "wrong_nodes": list(self.wrong_nodes),
            "homework": list(self.homework),
            "homework_assignments": list(self.homework_assignments),
        }


class FakeStudentStateStore:
    def __init__(self):
        self.state = FakeStudentState()
        self.saved = []

    def load(self, student_id):
        self.state.student_id = student_id
        return self.state

    def save(self, state):
        self.state = state
        self.saved.append(state.to_dict())


def test_homework_generator_builds_homework_and_persists_to_student_state():
    store = FakeStudentStateStore()
    sink = BufferedEventSink()
    runtime = RuntimeContext(
        event_sink=sink,
        graph_rag_pipeline=FakeGraphPipeline(),
        student_state_store=store,
    )
    node = build_homework_generator_node(runtime)

    result = node(
        {
            "student_id": "student_a",
            "current_topic": "自动控制原理",
            "student_state_snapshot": {
                "visited_nodes": ["KM001", "KM002"],
                "wrong_nodes": ["KM002"],
            },
        }
    )

    assert result["flow_status"] == "awaiting_homework_review_choice"
    assert result["learning_phase"] == "homework_resume"
    assert result["learning_resume_target"] == "homework_review"
    assert result["pending_interaction_kind"] == "homework_review_choice"
    assert [item["value"] for item in result["pending_interaction_options"]] == [
        "answer_homework",
        "save_for_later",
        "continue_learning",
    ]
    assert result["homework_status"] == "assigned"
    assert result["homework_assignment_id"].startswith("HW-student_a-")
    assert result["homework_items"]
    assert result["homework_items"][0]["question_id"].startswith("HW-")
    assert result["homework_items"][0]["graph_node_id"] == result["homework_items"][0]["node_id"]
    assert "node_key_points" in result["homework_items"][0]
    assert "homework-answer-content" in result["tutor_content"]
    assert "homework-assignment-card" in result["tutor_content"]
    assert "homework-answer-viewport" in result["tutor_content"]
    assert "参考答案" in result["tutor_content"]
    assert store.saved
    assert store.saved[-1]["homework"]
    assert any(
        event.type == "node.stream"
        and event.source == "homework_generator"
        and "今日作业" in event.data.get("text", "")
        for event in sink.events
    )


def test_homework_generator_falls_back_to_current_node_when_snapshot_empty():
    runtime = RuntimeContext(event_sink=BufferedEventSink(), graph_rag_pipeline=FakeGraphPipeline())
    node = build_homework_generator_node(runtime)

    result = node({"student_id": "student_a", "current_node_id": "KM001", "current_node_name": "稳定性基础"})

    assert result["homework_status"] == "assigned"
    assert result["homework_items"][0]["node_id"] == "KM001"
    assert result["flow_status"] == "awaiting_homework_review_choice"


def test_homework_generator_falls_back_without_question_bank_or_graph_pipeline():
    runtime = RuntimeContext(event_sink=BufferedEventSink())
    node = build_homework_generator_node(runtime)

    result = node({"student_id": "student_a", "current_node_id": "KM001", "current_node_name": "稳定性基础"})

    assert result["homework_status"] == "assigned"
    assert result["homework_items"][0]["source"] == "ai_generated_template"
    assert result["homework_items"][0]["node_id"] == "KM001"


def test_workflow_stop_today_routes_to_independent_homework_generator_node():
    assert workflow_module.route_after_continue_or_homework_selector({"continue_or_homework_choice": "stop_today"}) == "homework_generator"
    assert workflow_module.get_entry_node({"learning_resume_target": "homework_generator"}) == "homework_generator"

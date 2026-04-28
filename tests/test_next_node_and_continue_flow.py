from ai_tutor_agent.core.ports import BufferedEventSink, RuntimeContext
from ai_tutor_agent.nodes.continue_or_homework_selector import build_continue_or_homework_selector_node
from ai_tutor_agent.nodes.next_node_planner import build_next_node_planner_node
from ai_tutor_agent.orchestration import workflow as workflow_module


class FakeGraphPipeline:
    def __init__(self):
        self.node_map = {
            "KM001": {
                "node_id": "KM001",
                "name": "稳定性基础",
                "recommended_next_nodes": ["KM002"],
                "related_nodes": ["KM003"],
                "core_concepts": ["稳定性"],
            },
            "KM002": {
                "node_id": "KM002",
                "name": "劳斯判据",
                "recommended_next_nodes": [],
                "related_nodes": [],
                "core_concepts": ["劳斯表"],
            },
            "KM003": {
                "node_id": "KM003",
                "name": "根轨迹入门",
                "recommended_next_nodes": [],
                "related_nodes": [],
                "core_concepts": ["根轨迹"],
            },
        }


class FakeStudentState:
    def __init__(self, student_id="student_a"):
        self.student_id = student_id
        self.current_node_id = "KM001"
        self.visited_nodes = ["KM001"]
        self.completed_nodes = ["KM001"]
        self.wrong_nodes = []
        self.homework = []

    def to_dict(self):
        return {
            "student_id": self.student_id,
            "current_node_id": self.current_node_id,
            "visited_nodes": list(self.visited_nodes),
            "completed_nodes": list(self.completed_nodes),
            "wrong_nodes": list(self.wrong_nodes),
            "homework": list(self.homework),
        }

    def add_homework(self, question_id):
        self.homework.append(question_id)


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


class FakeAnswerProvider:
    def __init__(self, answer):
        self.answer = answer

    def get_answer(self, prompt, *, state=None):
        del prompt, state
        return self.answer


def test_next_node_planner_selects_related_unvisited_node_after_objective_pass():
    runtime = RuntimeContext(event_sink=BufferedEventSink(), graph_rag_pipeline=FakeGraphPipeline(), student_state_store=FakeStudentStateStore())
    node = build_next_node_planner_node(runtime)

    result = node({"student_id": "student_a", "current_node_id": "KM001", "current_node_status": "passed"})

    assert result["next_node_candidate_id"] == "KM002"
    assert result["next_node_candidate_name"] == "劳斯判据"
    assert result["next_node_candidate_reason"] == "related_unvisited"
    assert result["learning_phase"] == "next_node_planned"
    assert result["learning_resume_target"] == "continue_or_homework_selector"
    assert result["student_state_snapshot"]["visited_nodes"] == ["KM001"]


def test_continue_or_homework_selector_pauses_with_two_strict_options():
    runtime = RuntimeContext(event_sink=BufferedEventSink(), answer_provider=FakeAnswerProvider(""))
    node = build_continue_or_homework_selector_node(runtime)

    result = node({"next_node_candidate_id": "KM002", "next_node_candidate_name": "劳斯判据"})

    assert result["flow_status"] == "awaiting_continue_or_homework_choice"
    assert result["learning_phase"] == "continue_or_homework_choice"
    assert result["learning_resume_target"] == "continue_or_homework_selector"
    assert result["pending_interaction_kind"] == "continue_or_homework_choice"
    assert [item["value"] for item in result["pending_interaction_options"]] == ["continue_next_node", "stop_today"]


def test_continue_choice_moves_candidate_into_current_node_and_loads_content_next():
    runtime = RuntimeContext(event_sink=BufferedEventSink(), answer_provider=FakeAnswerProvider("继续学习"))
    node = build_continue_or_homework_selector_node(runtime)

    result = node(
        {
            "flow_status": "awaiting_continue_or_homework_choice",
            "pending_interaction_answer": "开始下一个节点",
            "next_node_candidate_id": "KM002",
            "next_node_candidate_name": "劳斯判据",
        }
    )

    assert result["continue_or_homework_choice"] == "continue_next_node"
    assert result["current_node_id"] == "KM002"
    assert result["current_node_name"] == "劳斯判据"
    assert result["current_node_status"] == "selected"
    assert result["learning_resume_target"] == "node_content_loader"


def test_stop_today_choice_routes_to_homework_generator():
    runtime = RuntimeContext(event_sink=BufferedEventSink(), answer_provider=FakeAnswerProvider("今天不学了"))
    node = build_continue_or_homework_selector_node(runtime)

    result = node(
        {
            "flow_status": "awaiting_continue_or_homework_choice",
            "pending_interaction_answer": "今天不学了",
            "next_node_candidate_id": "KM002",
            "next_node_candidate_name": "劳斯判据",
        }
    )

    assert result["continue_or_homework_choice"] == "stop_today"
    assert result["learning_phase"] == "homework_generation_requested"
    assert result["learning_resume_target"] == "homework_generator"


def test_workflow_routes_passed_objective_to_next_node_then_continue_selector():
    assert workflow_module.route_after_objective_test_scorer({"current_node_status": "passed"}) == "next_node_planner"
    assert workflow_module.route_after_next_node_planner({"next_node_candidate_id": "KM002"}) == "continue_or_homework_selector"
    assert workflow_module.route_after_continue_or_homework_selector({"flow_status": "awaiting_continue_or_homework_choice"}) == "pause"
    assert workflow_module.route_after_continue_or_homework_selector({"continue_or_homework_choice": "continue_next_node"}) == "node_content_loader"
    assert workflow_module.route_after_continue_or_homework_selector({"continue_or_homework_choice": "stop_today"}) == "homework_generator"
    assert workflow_module.get_entry_node({"flow_status": "awaiting_continue_or_homework_choice"}) == "continue_or_homework_selector"

from ai_tutor_agent.core.learning_flow import normalize_learning_phase
from ai_tutor_agent.nodes.assessment import build_user_profiler_node
from ai_tutor_agent.nodes.continue_or_homework_selector import build_continue_or_homework_selector_node
from ai_tutor_agent.nodes.node_content_loader import build_node_content_loader_node
from ai_tutor_agent.nodes.post_lesson_choice import build_post_lesson_choice_node
from ai_tutor_agent.nodes.temporary_question_collector import build_temporary_question_collector_node
from ai_tutor_agent.nodes.session_resume_router import build_session_resume_router_node
from ai_tutor_agent.core.ports import BufferedEventSink, RuntimeContext


class FakeAnswerProvider:
    def __init__(self, answer=""):
        self.answer = answer

    def get_answer(self, prompt, *, state=None):
        del prompt, state
        return self.answer


class FakeGraphPipeline:
    def __init__(self):
        self.node_map = {
            "KM001": {
                "node_id": "KM001",
                "name": "稳定性基础",
                "chapter": "chapter_01",
                "core_concepts": ["稳定性定义"],
                "key_points": ["能判断系统是否稳定"],
                "recommended_next_nodes": ["KM002"],
                "related_nodes": [],
                "prerequisite_nodes": [],
                "extra": {"common_errors": []},
            }
        }

    def get_node_content(self, node_id):
        return {
            "node_id": node_id,
            "content": "稳定性基础内容",
            "summary": "稳定性摘要",
            "evidence": [],
        }


class FakeChunk:
    def __init__(self, content):
        self.content = content


class FakeLLM:
    def invoke(self, messages):
        del messages
        return '{"mastery_profile": {"KM001": 0.4}, "recommended_start_node_id": "KM001", "summary": "从稳定性基础开始"}'

    def stream(self, messages):
        del messages
        yield FakeChunk("从稳定性基础开始。")


def assert_known_learning_phase(result):
    phase = result.get("learning_phase")
    assert phase
    assert normalize_learning_phase(phase) == phase


def test_new_mainflow_nodes_emit_normalized_learning_phases():
    sink = BufferedEventSink()

    profiler = build_user_profiler_node(FakeLLM(), sink, FakeGraphPipeline())
    assert_known_learning_phase(
        profiler(
            {
                "current_topic": "自动控制原理",
                "assessment_answers": {"Q1": "A"},
                "assessment_questions": [],
            }
        )
    )

    loader = build_node_content_loader_node(RuntimeContext(event_sink=sink, graph_rag_pipeline=FakeGraphPipeline()))
    assert_known_learning_phase(loader({"current_node_id": "KM001"}))

    post_choice = build_post_lesson_choice_node(sink, FakeAnswerProvider("我有个问题"))
    assert_known_learning_phase(
        post_choice(
            {
                "flow_status": "awaiting_post_lesson_choice",
                "pending_interaction_answer": "我有个问题",
                "current_node_name": "稳定性基础",
            }
        )
    )

    temp_collector = build_temporary_question_collector_node(sink)
    assert_known_learning_phase(temp_collector({"current_node_name": "稳定性基础"}))

    continue_selector = build_continue_or_homework_selector_node(
        RuntimeContext(event_sink=sink, answer_provider=FakeAnswerProvider("今天不学了"))
    )
    assert_known_learning_phase(
        continue_selector(
            {
                "flow_status": "awaiting_continue_or_homework_choice",
                "pending_interaction_answer": "今天不学了",
                "next_node_candidate_id": "KM002",
                "next_node_candidate_name": "劳斯判据",
            }
        )
    )

    resume_router = build_session_resume_router_node(RuntimeContext(event_sink=sink))
    assert_known_learning_phase(
        resume_router(
            {
                "flow_status": "awaiting_consolidation_choice",
                "pending_interaction_answer": "先巩固",
            }
        )
    )

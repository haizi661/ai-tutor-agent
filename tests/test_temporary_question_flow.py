from ai_tutor_agent.core.ports import BufferedEventSink, RuntimeContext
from ai_tutor_agent.knowledge_map.student_state import StudentStateStore
from ai_tutor_agent.nodes.node_content_loader import build_node_content_loader_node
from ai_tutor_agent.orchestration import workflow as workflow_module


class AskOnlyGraphPipeline:
    def __init__(self):
        self.node_map = {
            "KM001": {
                "node_id": "KM001",
                "name": "稳定性基础",
                "core_concepts": ["稳定性的定义"],
                "key_points": ["判断响应是否有界"],
                "explanation_teacher_style": "来自 explanation_teacher_style 的节点具体解释：稳定性关注系统响应是否收敛或保持有界。",
                "recommended_next_nodes": [],
                "related_nodes": [],
                "prerequisite_nodes": [],
                "extra": {"common_errors": ["把所有振荡都当成不稳定"]},
            }
        }
        self.ask_calls = []

    def ask(self, question, **kwargs):
        self.ask_calls.append({"question": question, "kwargs": kwargs})
        return {
            "answer": "来自 ask 的节点具体解释：稳定性关注系统响应是否收敛或保持有界。",
            "context_text": "稳定性上下文",
            "evidence_items": [
                {
                    "node_id": "KM001",
                    "node_name": "稳定性基础",
                    "attribute": "definition",
                    "text": "响应有界是稳定性判断的重要线索。",
                    "reference": "KM001.definition",
                }
            ],
            "anchor_nodes": [{"node_id": "KM001", "name": "稳定性基础"}],
            "media_items": [],
        }


def test_node_content_loader_uses_prebuilt_teacher_explanation_without_graph_rag_ask():
    graph = AskOnlyGraphPipeline()
    runtime = RuntimeContext(event_sink=BufferedEventSink(), graph_rag_pipeline=graph)
    node = build_node_content_loader_node(runtime)

    result = node({"current_topic": "自动控制原理", "current_node_id": "KM001", "current_node_name": "稳定性基础"})

    assert graph.ask_calls == []
    assert "来自 explanation_teacher_style 的节点具体解释" in result["node_content_context"]
    assert "来自 ask 的节点具体解释" not in result["node_content_context"]
    assert result["tutor_evidence"] == []
    assert result["learning_resume_target"] == "tutor"


def test_post_lesson_temporary_question_routes_to_collector_before_graph_answering():
    assert workflow_module.route_after_post_lesson_choice({"post_lesson_choice": "temporary_question"}) == "temporary_question_collector"
    assert workflow_module.route_after_temporary_question_collector({"flow_status": "awaiting_temporary_question"}) == "pause"
    assert workflow_module.route_after_temporary_question_collector({"interrupt_query": "为什么会振荡？"}) == "interruption"
    assert workflow_module.get_entry_node({"flow_status": "awaiting_temporary_question"}) == "temporary_question_collector"


def test_temporary_question_collector_pauses_then_consumes_user_question():
    from ai_tutor_agent.nodes.temporary_question_collector import build_temporary_question_collector_node

    sink = BufferedEventSink()
    node = build_temporary_question_collector_node(sink)

    first = node({"current_node_id": "KM001", "current_node_name": "稳定性基础"})
    assert first["flow_status"] == "awaiting_temporary_question"
    assert first["learning_phase"] == "temporary_question_collecting"
    assert first["learning_resume_target"] == "temporary_question_collector"
    assert first["pending_interaction_kind"] == "temporary_question"

    resumed = node(
        {
            "flow_status": "awaiting_temporary_question",
            "pending_interaction_answer": "为什么稳定系统也可能振荡？",
            "conversation_history": [],
        }
    )
    assert resumed["interrupt_query"] == "为什么稳定系统也可能振荡？"
    assert resumed["flow_status"] == "normal"
    assert resumed["learning_phase"] == "node_temp_qna"
    assert resumed["learning_resume_target"] == "interruption_tutor"
    assert resumed["conversation_history"][0]["kind"] == "interruption_user"
    assert resumed["message_history"][0]["kind"] == "interruption_user"
    assert resumed["message_history"][0]["content"] == "为什么稳定系统也可能振荡？"


def test_temporary_question_collector_dedupes_direct_post_lesson_question_in_message_history():
    from ai_tutor_agent.nodes.temporary_question_collector import build_temporary_question_collector_node

    sink = BufferedEventSink()
    node = build_temporary_question_collector_node(sink)
    question = "还是没太明白这个负反馈判断"

    resumed = node(
        {
            "interrupt_query": question,
            "message_history": [
                {
                    "role": "user",
                    "kind": "post_lesson_choice",
                    "content": question,
                    "data": {"selected_value": "temporary_question"},
                }
            ],
        }
    )

    assert [item["content"] for item in resumed["message_history"]] == [question]


def test_interruption_answer_keeps_main_tutor_content_separate():
    from ai_tutor_agent.nodes.interruption import build_interruption_node

    class GraphPipeline:
        def __init__(self):
            self.calls = []

        def ask(self, query, **kwargs):
            self.calls.append({"query": query, "kwargs": kwargs})
            return {"answer": "临时问题解答", "media_items": []}

    graph = GraphPipeline()
    sink = BufferedEventSink()
    runtime = RuntimeContext(event_sink=sink, graph_rag_pipeline=graph)
    node = build_interruption_node(None, runtime)

    result = node(
        {
            "current_topic": "自动控制原理",
            "graph_anchor_title": "稳定性基础",
            "learning_resume_target": "temporary_question_collector",
            "interrupt_query": "为什么稳定系统也可能振荡？",
            "tutor_content": "主线讲解内容",
            "conversation_history": [
                {"role": "user", "kind": "interruption_user", "content": "为什么稳定系统也可能振荡？"}
            ],
            "message_history": [],
        }
    )

    assert graph.calls
    assert "tutor_content" not in result
    assert result["flow_status"] == "awaiting_post_lesson_choice"
    assert result["learning_resume_target"] == "post_lesson_choice"
    assert result["conversation_history"][-1]["kind"] == "interruption"
    assert result["message_history"][-1]["kind"] == "interruption"


def test_interruption_records_temporary_question_as_node_evidence(tmp_path):
    from ai_tutor_agent.nodes.interruption import build_interruption_node

    class GraphPipeline:
        def ask(self, query, **kwargs):
            return {
                "answer": "稳定振荡和发散振荡要分开看。",
                "context_text": "稳定性上下文",
                "evidence_items": [{"reference": "KM001.definition", "text": "响应有界是稳定性判断的重要线索。"}],
                "anchor_nodes": [{"node_id": "KM001", "name": "稳定性基础"}],
                "media_items": [],
            }

    store = StudentStateStore(tmp_path / "student_states")
    sink = BufferedEventSink()
    runtime = RuntimeContext(event_sink=sink, graph_rag_pipeline=GraphPipeline(), student_state_store=store)
    node = build_interruption_node(None, runtime)

    result = node(
        {
            "student_id": "s1",
            "current_topic": "自动控制原理",
            "current_node_id": "KM001",
            "current_node_name": "稳定性基础",
            "interrupt_query": "为什么稳定系统也可能振荡？",
            "learning_resume_target": "temporary_question_collector",
            "conversation_history": [
                {"role": "user", "kind": "interruption_user", "content": "为什么稳定系统也可能振荡？"}
            ],
            "message_history": [],
        }
    )

    state = store.load("s1")
    entry = state.knowledge_graph["KM001"]
    evidence = entry["evidence"][-1]
    assert result["student_state_snapshot"]["knowledge_graph"]["KM001"]["evidence"][-1]["type"] == "temporary_question"
    assert entry["title"] == "稳定性基础"
    assert entry["attempts"] == 0
    assert evidence["type"] == "temporary_question"
    assert evidence["question"] == "为什么稳定系统也可能振荡？"
    assert evidence["answer_kind"] == "interruption"
    assert evidence["references"] == ["KM001.definition", "KM001"]


def test_interruption_confirmation_returns_to_post_lesson_choice_not_legacy_next_step():
    state = {"flow_status": "awaiting_interrupt_confirmation", "learning_phase": "node_temp_qna", "resume_tester": False}
    # Paused immediately after answering the temporary question.
    assert workflow_module.route_after_interruption(state) == "pause"

    # Once the app/session layer confirms return to mainline, strict mainflow should resume at post_lesson_choice.
    assert workflow_module.get_entry_node({"learning_resume_target": "post_lesson_choice"}) == "post_lesson_choice"


def test_interruption_retries_with_invoke_when_stream_breaks():
    from types import SimpleNamespace

    from ai_tutor_agent.nodes.interruption import build_interruption_node

    class FlakyLLM:
        def __init__(self):
            self.invoke_calls = 0

        def stream(self, _messages):
            raise RuntimeError("incomplete chunked read")

        def invoke(self, _messages):
            self.invoke_calls += 1
            return SimpleNamespace(content="先分清稳定振荡和发散振荡不是一回事。")

    class StubKnowledgeProvider:
        def query(self, query, *, rewrite_request=None):
            del query, rewrite_request
            return ""

    sink = BufferedEventSink()
    llm = FlakyLLM()
    node = build_interruption_node(llm, RuntimeContext(event_sink=sink, knowledge_provider=StubKnowledgeProvider()))

    result = node(
        {
            "current_topic": "自动控制原理",
            "graph_anchor_title": "稳定性基础",
            "learning_resume_target": "temporary_question_collector",
            "interrupt_query": "为什么稳定系统也会振荡？",
            "conversation_history": [
                {"role": "user", "kind": "interruption_user", "content": "为什么稳定系统也会振荡？"}
            ],
            "message_history": [],
        }
    )

    assert llm.invoke_calls == 1
    assert "先分清稳定振荡和发散振荡不是一回事" in result["conversation_history"][-1]["content"]
    assert result["llm_stream_disabled"] is True
    assert result["llm_stream_failures"] == 1
    assert not [event for event in sink.events if event.type == "session.warning"]

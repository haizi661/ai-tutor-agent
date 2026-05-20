from types import SimpleNamespace

from ai_tutor_agent.core.ports import BufferedEventSink, RuntimeContext
from ai_tutor_agent.knowledge_map.student_state import StudentStateStore
from ai_tutor_agent.nodes.post_eval import (
    build_post_eval_selector_node,
    build_post_eval_wrapup_node,
)


class FakeAnswerProvider:
    def __init__(self, answer: str):
        self.answer = answer
        self.prompts = []

    def get_answer(self, prompt: str, *, state=None) -> str:
        self.prompts.append({"prompt": prompt, "state": state})
        return self.answer


class FakeStreamingLLM:
    def __init__(self, response: str):
        self.response = response
        self.messages = []

    def stream(self, messages):
        self.messages.append(messages)
        yield SimpleNamespace(content=self.response)


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
                "related_nodes": ["KM003"],
                "recommended_next_nodes": ["KM003"],
                "prerequisite_nodes": ["KM001"],
                "extra": {"common_errors": ["把反馈结构和控制器混为一谈"]},
                "importance_level": "3",
            },
            "KM003": {
                "node_id": "KM003",
                "name": "稳态误差",
                "chapter": "chapter_03",
                "core_concepts": ["稳态误差定义"],
                "key_points": ["区分动态过程和稳态偏差"],
                "related_nodes": [],
                "recommended_next_nodes": [],
                "prerequisite_nodes": ["KM002"],
                "extra": {"common_errors": []},
                "importance_level": "3",
            },
        }


def test_post_eval_selector_waits_for_explicit_choice_and_recommends_next_node():
    sink = BufferedEventSink()
    provider = FakeAnswerProvider("继续拔高")
    node = build_post_eval_selector_node(sink, provider, graph_rag_pipeline=StubGraphPipeline())

    result = node(
        {
            "current_topic": "自动控制原理",
            "current_user_goal": "稳定性怎么判断",
            "current_node_id": "KM001",
            "graph_anchor_id": "KM001",
            "graph_anchor_title": "稳定性",
            "student_state_snapshot": {"visited_nodes": ["KM001"]},
        }
    )

    assert result["flow_status"] == "awaiting_post_eval_selector"
    assert result["pending_interaction_recommended"] in {"continue_advance", "summarize_wrapup"}
    assert result["next_node_candidate_id"] == "KM002"
    assert "开始下一个节点" in result["pending_interaction_options"][0]["label"]


def test_post_eval_selector_can_route_to_same_type_practice():
    """验证：恢复路径下，用户选"换一道同类型"能正确路由。"""
    sink = BufferedEventSink()
    provider = FakeAnswerProvider("换一道同类型")
    node = build_post_eval_selector_node(sink, provider)

    options = [dict(o) for o in [
        {"value": "continue_advance", "label": "开始下一个节点：负反馈", "graph_target_id": "KM002", "graph_target_name": "负反馈"},
        {"value": "same_type_practice", "label": "换一道同类型"},
        {"value": "summarize_wrapup", "label": "今天先到这里，生成作业"},
    ]]
    result = node(
        {
            "current_topic": "自动控制原理",
            "current_user_goal": "稳定性怎么判断",
            "flow_status": "awaiting_post_eval_selector",
            "pending_interaction_prompt": "你想怎么继续？",
            "pending_interaction_options": options,
            "pending_interaction_answer": "换一道同类型",
        }
    )

    assert result["post_eval_choice"] == "same_type_practice"
    assert result["practice_generation_mode"] == "same_type"


def test_post_eval_selector_can_route_to_advanced_tutor():
    sink = BufferedEventSink()
    provider = FakeAnswerProvider("开始下一个节点：负反馈")
    node = build_post_eval_selector_node(sink, provider, graph_rag_pipeline=StubGraphPipeline())

    options = [dict(o) for o in [
        {"value": "continue_advance", "label": "开始下一个节点：负反馈", "graph_target_id": "KM002", "graph_target_name": "负反馈"},
        {"value": "same_type_practice", "label": "换一道同类型"},
        {"value": "summarize_wrapup", "label": "今天先到这里，生成作业"},
    ]]
    result = node(
        {
            "current_topic": "自动控制原理",
            "current_user_goal": "稳定性怎么判断",
            "current_node_id": "KM001",
            "graph_anchor_id": "KM001",
            "graph_anchor_title": "稳定性",
            "flow_status": "awaiting_post_eval_selector",
            "pending_interaction_prompt": "你想怎么继续？",
            "pending_interaction_options": options,
            "pending_interaction_answer": "开始下一个节点：负反馈",
        }
    )

    assert result["post_eval_choice"] == "continue_advance"
    assert result["teaching_strategy"] == "explain"
    assert result["current_node_id"] == "KM002"
    assert result["graph_anchor_title"] == "负反馈"
    assert result["turn_goal"] == "负反馈"


def test_post_eval_wrapup_clears_selector_flags_and_assigns_homework(tmp_path):
    sink = BufferedEventSink()
    llm = FakeStreamingLLM("### 本轮收获\n- 你已经把稳定性的主线抓住了。\n- 现在更清楚先看最终趋势，再判断是否回到平衡。\n- 下次先抓主线，再代回场景。")
    runtime = RuntimeContext(
        event_sink=sink,
        graph_rag_pipeline=StubGraphPipeline(),
        student_state_store=StudentStateStore(tmp_path / "student_states"),
    )
    node = build_post_eval_wrapup_node(llm, runtime)

    result = node(
        {
            "current_topic": "自动控制原理",
            "current_user_goal": "稳定性怎么判断",
            "feedback": "这轮主线已经答对了。",
            "tutor_content": "本轮讲解聚焦稳定性判断主线。",
            "next_review_points": ["先看最终趋势"],
            "post_eval_choice": "summarize_wrapup",
            "practice_generation_mode": "same_type",
            "student_id": "student_a",
            "student_state_snapshot": {
                "visited_nodes": ["KM001", "KM002"],
                "wrong_nodes": ["KM001"],
            },
        }
    )

    assert result["post_eval_choice"] == ""
    assert result["practice_generation_mode"] == ""
    assert "本轮收获" in result["tutor_content"]
    assert "今日作业" in result["tutor_content"]
    assert result["homework_status"] == "assigned"
    assert len(result["homework_items"]) >= 1

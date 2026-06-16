"""Tests for the remediation_decision node — score‑based routing, hard limits, choice mapping."""

from ai_tutor_agent.core.ports import BufferedEventSink
from ai_tutor_agent.nodes.remediation_decision import (
    build_remediation_decision_node,
    route_after_remediation_decision,
    MAX_VARIANT_ROUNDS_PER_NODE,
    MAX_SAME_OBJECTIVE_FAILURES,
    MAX_EXTRA_REMEDIATION_QUESTIONS,
)
from ai_tutor_agent.orchestration import workflow as workflow_module


class _FakeAnswerProvider:
    """Returns a canned answer when the node calls get_answer()."""
    def __init__(self, answer: str = "continue_variant"):
        self.answer = answer

    def get_answer(self, prompt: str, *, state=None):
        del prompt, state
        return self.answer


# ──────────────────────────────────────────────
#  首次访问：分数分级 + 决策卡数据
# ──────────────────────────────────────────────


def test_first_visit_with_partial_score_60_79():
    """60–79 分 → partial 档次，选项包含 continue_variant 且推荐。"""
    sink = BufferedEventSink()
    node = build_remediation_decision_node(sink, answer_provider=None)
    result = node({
        "node_quiz_score": 70,
        "node_quiz_wrong_items": [{"question_id": "Q1"}],
    })

    assert result["flow_status"] == "awaiting_remediation_decision"
    assert result["remediation_decision"] == ""
    assert result["pending_interaction_kind"] == "remediation_decision"
    options = result["pending_interaction_options"]
    values = [o["value"] for o in options]
    assert "continue_variant" in values
    assert "review_node" in values
    assert "do_later" in values
    assert result["pending_interaction_recommended"] == "continue_variant"

    # event data carries structured info
    event = sink.events[-1]
    assert event.type == "node.start"
    assert event.data["score"] == 70
    assert event.data["tier"] == "partial"


def test_first_visit_with_low_score_below_60():
    """< 60 分 → low 档次，选项包含 still_do_variant 且推荐 review_node。"""
    sink = BufferedEventSink()
    node = build_remediation_decision_node(sink, answer_provider=None)
    result = node({
        "node_quiz_score": 50,
        "node_quiz_wrong_items": [{"question_id": "Q1"}],
    })

    assert result["flow_status"] == "awaiting_remediation_decision"
    options = result["pending_interaction_options"]
    values = [o["value"] for o in options]
    assert "review_node" in values
    assert "still_do_variant" in values  # low‐score option
    assert "do_later" in values
    assert "continue_variant" not in values
    assert result["pending_interaction_recommended"] == "review_node"

    event = sink.events[-1]
    assert event.data["tier"] == "low"
    assert event.data["score"] == 50


def test_first_visit_with_wrong_count_from_explanations():
    """wrong_question_explanations 优先用于计算 wrong_count。"""
    sink = BufferedEventSink()
    node = build_remediation_decision_node(sink, answer_provider=None)
    result = node({
        "node_quiz_score": 65,
        "wrong_question_explanations": [{"question_id": "Q1"}, {"question_id": "Q2"}, {"question_id": "Q3"}],
    })

    event = sink.events[-1]
    assert event.data["wrong_count"] == 3


# ──────────────────────────────────────────────
#  硬界限
# ──────────────────────────────────────────────


def test_paused_when_variant_rounds_exceeded():
    """variant_rounds >= MAX_VARIANT_ROUNDS_PER_NODE → paused。"""
    sink = BufferedEventSink()
    node = build_remediation_decision_node(sink, answer_provider=None)
    result = node({
        "node_quiz_score": 65,
        "node_quiz_wrong_items": [{"question_id": "Q1"}],
        "node_remediation_state": {
            "original_score": 65,
            "variant_rounds": MAX_VARIANT_ROUNDS_PER_NODE,
            "same_objective_failures": {},
            "extra_remediation_question_count": 0,
        },
    })

    assert result["flow_status"] == "awaiting_remediation_decision"
    assert result["learning_phase"] == "remediation_paused"
    options = result["pending_interaction_options"]
    values = [o["value"] for o in options]
    assert "review_node" in values
    assert "do_later" in values
    assert "continue_variant" not in values

    event = sink.events[-1]
    assert event.data["paused"] is True
    assert len(event.data["paused_reasons"]) >= 1


def test_paused_when_same_objective_failures_exceed():
    """same_objective_failures 中某考察点 >= MAX → paused。"""
    sink = BufferedEventSink()
    node = build_remediation_decision_node(sink, answer_provider=None)
    result = node({
        "node_quiz_score": 65,
        "node_quiz_wrong_items": [{"question_id": "Q1"}],
        "node_remediation_state": {
            "original_score": 65,
            "variant_rounds": 0,
            "same_objective_failures": {"判断反馈信号是否参与比较": MAX_SAME_OBJECTIVE_FAILURES},
            "extra_remediation_question_count": 0,
        },
    })

    assert result["flow_status"] == "awaiting_remediation_decision"
    assert result["learning_phase"] == "remediation_paused"
    event = sink.events[-1]
    assert event.data["paused"] is True
    assert any("判断反馈信号" in r for r in event.data["paused_reasons"])


def test_paused_when_extra_questions_exceed():
    """extra_remediation_question_count > MAX → paused。"""
    sink = BufferedEventSink()
    node = build_remediation_decision_node(sink, answer_provider=None)
    result = node({
        "node_quiz_score": 65,
        "node_quiz_wrong_items": [{"question_id": "Q1"}],
        "node_remediation_state": {
            "original_score": 65,
            "variant_rounds": 0,
            "same_objective_failures": {},
            "extra_remediation_question_count": MAX_EXTRA_REMEDIATION_QUESTIONS + 1,
        },
    })

    assert result["learning_phase"] == "remediation_paused"
    event = sink.events[-1]
    assert event.data["paused"] is True


# ──────────────────────────────────────────────
#  用户选择 → 路由
# ──────────────────────────────────────────────


def test_choice_continue_variant_routes_to_variant_generator():
    """continue_variant → variant_question_generator + 递增 variant_rounds。"""
    sink = BufferedEventSink()
    node = build_remediation_decision_node(sink, _FakeAnswerProvider("continue_variant"))
    result = node({
        "node_quiz_score": 70,
        "node_quiz_wrong_items": [{"question_id": "Q1"}],
        "flow_status": "awaiting_remediation_decision",
        "pending_interaction_answer": "continue_variant",
        "node_remediation_state": {
            "original_score": 70,
            "variant_rounds": 0,
            "same_objective_failures": {},
            "extra_remediation_question_count": 0,
        },
    })

    assert result["flow_status"] == "normal"
    assert result["remediation_decision"] == "continue_variant"
    assert result["learning_resume_target"] == "variant_question_generator"
    assert result["node_remediation_state"]["variant_rounds"] == 1


def test_choice_still_do_variant_routes_to_variant_generator():
    """still_do_variant → variant_question_generator。"""
    sink = BufferedEventSink()
    node = build_remediation_decision_node(sink, _FakeAnswerProvider("still_do_variant"))
    result = node({
        "node_quiz_score": 50,
        "node_quiz_wrong_items": [{"question_id": "Q1"}],
        "flow_status": "awaiting_remediation_decision",
        "pending_interaction_answer": "仍然做变式训练",
        "node_remediation_state": {
            "original_score": 50,
            "variant_rounds": 0,
            "same_objective_failures": {},
            "extra_remediation_question_count": 0,
        },
    })

    assert result["flow_status"] == "normal"
    assert result["remediation_decision"] == "still_do_variant"
    assert result["learning_resume_target"] == "variant_question_generator"


def test_choice_review_node_routes_to_node_content_loader():
    """review_node → node_content_loader。"""
    sink = BufferedEventSink()
    node = build_remediation_decision_node(sink, _FakeAnswerProvider("review_node"))
    result = node({
        "node_quiz_score": 70,
        "node_quiz_wrong_items": [{"question_id": "Q1"}],
        "flow_status": "awaiting_remediation_decision",
        "pending_interaction_answer": "复习本节点",
        "node_remediation_state": {
            "original_score": 70,
            "variant_rounds": 0,
            "same_objective_failures": {},
            "extra_remediation_question_count": 0,
        },
    })

    assert result["flow_status"] == "normal"
    assert result["remediation_decision"] == "review_node"
    assert result["learning_resume_target"] == "node_content_loader"
    assert result["current_node_status"] == "selected"


def test_choice_do_later_routes_to_next_node_planner():
    """do_later → next_node_planner（先推进节点，再 continue/homework）。"""
    sink = BufferedEventSink()
    node = build_remediation_decision_node(sink, _FakeAnswerProvider("do_later"))
    result = node({
        "node_quiz_score": 70,
        "node_quiz_wrong_items": [{"question_id": "Q1"}],
        "flow_status": "awaiting_remediation_decision",
        "pending_interaction_answer": "稍后复习",
        "node_remediation_state": {
            "original_score": 70,
            "variant_rounds": 0,
            "same_objective_failures": {},
            "extra_remediation_question_count": 0,
        },
    })

    assert result["flow_status"] == "normal"
    assert result["remediation_decision"] == "do_later"
    assert result["learning_resume_target"] == "next_node_planner"
    assert result["node_remediation_state"]["status"] == "deferred"


# ──────────────────────────────────────────────
#  Route 选择器
# ──────────────────────────────────────────────


def test_route_after_remediation_decision():
    """route_after_remediation_decision 按字段值正确路由。"""
    assert route_after_remediation_decision({"remediation_decision": "continue_variant"}) == "variant_question_generator"
    assert route_after_remediation_decision({"remediation_decision": "still_do_variant"}) == "variant_question_generator"
    assert route_after_remediation_decision({"remediation_decision": "review_node"}) == "node_content_loader"
    assert route_after_remediation_decision({"remediation_decision": "do_later"}) == "next_node_planner"
    assert route_after_remediation_decision({"remediation_decision": ""}) == "pause"


# ──────────────────────────────────────────────
#  Workflow 入口 / 路由整合
# ──────────────────────────────────────────────


def test_workflow_entry_and_routes_for_remediation_decision():
    """Workflow 层面能通过 learning_resume_target 和 flow_status 进入 remediation_decision。"""
    assert workflow_module.get_entry_node({"learning_resume_target": "remediation_decision"}) == "remediation_decision"
    assert workflow_module.get_entry_node({"flow_status": "awaiting_remediation_decision"}) == "remediation_decision"
    assert workflow_module.route_after_wrong_question_explainer({"learning_resume_target": "remediation_decision"}) == "remediation_decision"
    assert workflow_module.route_after_objective_test_scorer({"learning_resume_target": "remediation_decision"}) == "remediation_decision"
    assert workflow_module.route_after_session_resume_router({"learning_resume_target": "remediation_decision"}) == "remediation_decision"


# ──────────────────────────────────────────────
#  消息历史记录
# ──────────────────────────────────────────────


def test_choice_appends_to_message_history():
    """用户选择后，message_history 中追加一条 remediation_decision 记录。"""
    sink = BufferedEventSink()
    node = build_remediation_decision_node(sink, _FakeAnswerProvider("review_node"))
    result = node({
        "node_quiz_score": 65,
        "node_quiz_wrong_items": [{"question_id": "Q1"}],
        "flow_status": "awaiting_remediation_decision",
        "pending_interaction_answer": "review_node",
        "message_history": [{"role": "assistant", "kind": "wrong_question_explanations", "content": "讲解"}],
        "node_remediation_state": {
            "original_score": 65,
            "variant_rounds": 0,
            "same_objective_failures": {},
            "extra_remediation_question_count": 0,
        },
    })

    entries = list(result.get("message_history", []))
    assert len(entries) == 2
    assert entries[-1]["kind"] == "remediation_decision"
    assert entries[-1]["data"]["selected_value"] == "review_node"


# ──────────────────────────────────────────────
#  pause — 跨分支的暂停卡样式
# ──────────────────────────────────────────────


def test_paused_card_structure_does_not_include_continue_variant():
    """暂停状态下，选项只有 review_node 和 do_later。"""
    sink = BufferedEventSink()
    node = build_remediation_decision_node(sink, answer_provider=None)
    result = node({
        "node_quiz_score": 65,
        "node_quiz_wrong_items": [{"question_id": "Q1"}],
        "node_remediation_state": {
            "original_score": 65,
            "variant_rounds": MAX_VARIANT_ROUNDS_PER_NODE,
            "same_objective_failures": {},
            "extra_remediation_question_count": 0,
        },
    })

    values = [o["value"] for o in result["pending_interaction_options"]]
    assert set(values) == {"review_node", "do_later"}

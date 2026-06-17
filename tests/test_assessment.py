from types import SimpleNamespace

from ai_tutor_agent.core.ports import BufferedEventSink
from ai_tutor_agent.nodes.assessment import (
    ASSESSMENT_DIMENSIONS,
    _compute_concept_gaps,
    _decide_teaching_start,
    _generate_profile_report,
    _generate_radar_data,
    build_user_profiler_node,
)
from ai_tutor_agent.nodes.evaluator import build_evaluator_node


class FakeStreamingLLM:
    def __init__(self, responses):
        if isinstance(responses, str):
            responses = [responses]
        self.responses = list(responses)
        self.messages = []

    def stream(self, messages):
        self.messages.append(messages)
        response = self.responses.pop(0)
        yield SimpleNamespace(content=response)


class FailingStreamingLLM:
    def __init__(self, message: str):
        self.message = message

    def stream(self, messages):
        raise RuntimeError(self.message)
        yield  # pragma: no cover


def test_generate_radar_data_uses_rule_based_scores():
    questions = [
        {
            "id": 1,
            "type": "self_eval",
            "dimension": "控制系统基本概念",
            "question": "你对控制系统基本概念的掌握如何？",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "",
        },
        {
            "id": 2,
            "type": "objective",
            "dimension": "控制系统基本概念",
            "question": "基本概念题",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "C",
        },
        {
            "id": 3,
            "type": "self_eval",
            "dimension": "数学基础",
            "question": "你对数学基础的掌握如何？",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "",
        },
        {
            "id": 4,
            "type": "objective",
            "dimension": "数学基础",
            "question": "数学基础题",
            "options": ["A", "B", "C", "D"],
            "correct_answer": "A",
        },
    ]
    answers = {"1": "D", "2": "C", "3": "B", "4": "D"}

    radar = _generate_radar_data(BufferedEventSink(), "控制理论", questions, answers)

    assert radar["dimensions"] == ASSESSMENT_DIMENSIONS
    concept_index = ASSESSMENT_DIMENSIONS.index("控制系统基本概念")
    logic_index = ASSESSMENT_DIMENSIONS.index("数学基础")
    assert radar["self_scores"][concept_index] == 100
    assert radar["objective_scores"][concept_index] == 100
    assert radar["gap_scores"][concept_index] == 0
    assert radar["self_scores"][logic_index] == 50
    assert radar["objective_scores"][logic_index] == 0
    assert radar["gap_scores"][logic_index] == 50
    assert radar["breakdown"][concept_index]["objective_count"] == 1


def test_generate_radar_data_warns_when_objective_answer_key_missing():
    sink = BufferedEventSink()
    radar = _generate_radar_data(
        sink,
        "控制理论",
        [
            {
                "id": 1,
                "type": "objective",
                "dimension": "控制系统基本概念",
                "question": "缺少答案键",
                "options": ["A", "B", "C", "D"],
                "correct_answer": "",
            }
        ],
        {"1": "A"},
    )

    assert radar["objective_scores"][0] == 50
    assert any("缺少 correct_answer" in event.message for event in sink.events)


def test_generate_profile_report_returns_bridge_copy_and_streams_chunks():
    sink = BufferedEventSink()
    llm = FakeStreamingLLM("我现在大致知道从哪里开始了，你对稳定性有直觉，但边界还不稳。接下来先从稳定性的判断对象讲起。")

    report = _generate_profile_report(
        llm,
        sink,
        "控制理论",
        {"稳定性": {"gap_type": "aligned_low"}},
        3,
        "explain",
        "自动控制的一般概念",
    )

    assert report.startswith("我现在大致知道从哪里开始了")
    stream_events = [event for event in sink.events if event.type == "node.stream" and event.source == "user_profiler"]
    assert len(stream_events) >= 1
    streamed_text = "".join(event.message for event in stream_events)
    assert streamed_text == report


def test_generate_profile_report_falls_back_when_llm_balance_is_insufficient():
    sink = BufferedEventSink()
    llm = FailingStreamingLLM("Error code: 402 - {'error': {'message': 'Insufficient Balance'}}")

    report = _generate_profile_report(
        llm,
        sink,
        "自动控制原理",
        {"传递函数": {"gap_type": "aligned_low"}},
        2,
        "explain",
        "自动控制的一般概念",
    )

    assert report.startswith("我现在大致知道从哪里开始了")
    assert "自动控制的一般概念" in report
    warnings = [event for event in sink.events if event.type == "session.warning" and event.source == "user_profiler"]
    assert warnings
    assert "余额不足" in warnings[-1].message
    stream_text = "".join(
        event.message for event in sink.events
        if event.type == "node.stream" and event.source == "user_profiler"
    )
    assert report in stream_text


def test_user_profiler_continues_to_initial_node_selector_when_llm_balance_is_insufficient():
    sink = BufferedEventSink()
    llm = FailingStreamingLLM("Error code: 402 - {'error': {'message': 'Insufficient Balance'}}")

    class GraphPipeline:
        node_map = {
            "KM001": {
                "node_id": "KM001",
                "name": "自动控制的一般概念",
                "prerequisite_nodes": [],
                "source_type": "skeleton_chapter_anchor",
            }
        }

    node = build_user_profiler_node(llm, sink, GraphPipeline())
    result = node(
        {
            "current_topic": "自动控制原理",
            "assessment_questions": [
                {"id": 1, "type": "subjective_choice", "concept": "传递函数", "question": "Q", "options": ["A", "B"], "score_map": {"A": 25, "B": 75}}
            ],
            "assessment_answers": {"1": "A"},
            "turn_goal": "自动控制原理",
            "topic_focus": "",
        }
    )

    assert result["is_assessed"] is True
    # learning_resume_target 不应在画像生成阶段设置（避免 get_entry_node 跳过模式选择）
    assert not result.get("learning_resume_target")
    assert result["flow_status"] == "awaiting_learning_mode_choice"
    assert result["pending_interaction_kind"] == "learning_mode_choice"


def test_user_profiler_hands_off_to_initial_node_selector_instead_of_preselecting_gap_node():
    sink = BufferedEventSink()
    llm = FakeStreamingLLM("我现在大致知道从哪里开始了，你的基础还需要先搭框架。接下来先从自动控制的一般概念开始，把课程起点打稳。")

    class GraphPipeline:
        node_map = {
            "KM001": {
                "node_id": "KM001",
                "name": "自动控制的一般概念",
                "prerequisite_nodes": [],
                "source_type": "skeleton_chapter_anchor",
            }
        }

    node = build_user_profiler_node(llm, sink, GraphPipeline())
    result = node(
        {
            "current_topic": "自动控制原理",
            "assessment_questions": [
                {"id": 1, "type": "subjective_choice", "concept": "传递函数", "question": "Q", "options": ["A", "B"], "score_map": {"A": 25, "B": 75}}
            ],
            "assessment_answers": {"1": "A"},
            "turn_goal": "自动控制原理",
            "topic_focus": "",
        }
    )

    # learning_resume_target 不应在画像生成阶段设置（避免 get_entry_node 跳过模式选择）
    assert not result.get("learning_resume_target")
    assert result["learning_phase"] == "learning_mode_choice"
    assert result["current_node_id"] == ""
    assert result["graph_anchor_title"] == ""


# ===========================================================================
# 新测试：概念差距分析 + 教学策略决定
# ===========================================================================

def _make_paired_questions():
    """构造一个标准配对题组（2 概念，各1自评+1客观）。"""
    return [
        {
            "id": 1, "type": "self_eval", "concept": "传递函数",
            "paired_id": 3, "dimension": "基础概念",
            "question": "你对传递函数的掌握？",
            "options": ["A", "B", "C", "D"], "correct_answer": "",
        },
        {
            "id": 2, "type": "self_eval", "concept": "PID控制",
            "paired_id": 4, "dimension": "规则理解",
            "question": "你对PID控制的掌握？",
            "options": ["A", "B", "C", "D"], "correct_answer": "",
        },
        {
            "id": 3, "type": "objective", "concept": "传递函数",
            "paired_id": 1, "dimension": "基础概念",
            "question": "传递函数的定义？",
            "options": ["A", "B", "C", "D"], "correct_answer": "B",
        },
        {
            "id": 4, "type": "objective", "concept": "PID控制",
            "paired_id": 2, "dimension": "规则理解",
            "question": "PID 的积分项作用？",
            "options": ["A", "B", "C", "D"], "correct_answer": "A",
        },
    ]


def test_compute_concept_gaps_overconfident():
    """自评 D(100) 但客观答错(0) → gap > 30 → overconfident。"""
    questions = _make_paired_questions()
    answers = {"1": "D", "2": "B", "3": "A", "4": "A"}  # Q3 wrong, Q4 correct
    gaps = _compute_concept_gaps(questions, answers)

    assert "传递函数" in gaps
    assert gaps["传递函数"]["gap_type"] == "overconfident"
    assert gaps["传递函数"]["self_score"] == 100
    assert gaps["传递函数"]["actual_score"] == 0
    assert gaps["传递函数"]["calibrated"] == round(0.3 * 100 + 0.7 * 0)


def test_compute_concept_gaps_underconfident():
    """自评 A(25) 但客观答对(100) → gap < -30 → underconfident。"""
    questions = _make_paired_questions()
    answers = {"1": "A", "2": "B", "3": "B", "4": "B"}  # Q3 correct(B), Q4 wrong(B≠A)
    gaps = _compute_concept_gaps(questions, answers)

    assert gaps["传递函数"]["gap_type"] == "underconfident"
    assert gaps["传递函数"]["actual_score"] == 100


def test_compute_concept_gaps_aligned_high():
    """自评 C(75) 且客观答对(100) → gap = -25 (<=30) → aligned_high（实测>=60）。"""
    questions = _make_paired_questions()
    answers = {"1": "C", "2": "B", "3": "B", "4": "B"}  # Q3 correct(B), Q4 wrong
    gaps = _compute_concept_gaps(questions, answers)

    assert gaps["传递函数"]["gap_type"] == "aligned_high"


def test_compute_concept_gaps_aligned_low():
    """自评 B(50) 且客观答错(0) → gap = 50 > 30？不对，B=50, actual=0 → gap=50 → overconfident。
    改为 A(25) 且客观也错 → gap <= 30, actual < 60 → aligned_low。"""
    questions = _make_paired_questions()
    answers = {"1": "A", "2": "B", "3": "C", "4": "B"}  # Q3: C≠B → wrong; Q4: B≠A → wrong
    gaps = _compute_concept_gaps(questions, answers)

    # self=25, actual=0, gap=25 ≤ 30, actual<60 → aligned_low
    assert gaps["传递函数"]["gap_type"] == "aligned_low"


def test_decide_teaching_start_socratic():
    """多数概念 overconfident → 苏格拉底引导策略。"""
    # 构造 4 个 overconfident 概念（gap=100, calibrated=30）
    concept_gaps = {
        f"概念{i}": {"gap_type": "overconfident", "calibrated": 30}
        for i in range(4)
    }
    level, strategy = _decide_teaching_start(concept_gaps)
    assert strategy == "socratic"
    assert level == 2  # avg calibrated = 30 → ≤40 → level 2


def test_decide_teaching_start_analogy():
    """多数概念 underconfident → 类比教学。"""
    concept_gaps = {
        f"概念{i}": {"gap_type": "underconfident", "calibrated": 85}
        for i in range(4)
    }
    level, strategy = _decide_teaching_start(concept_gaps)
    assert strategy == "analogy"
    assert level == 5  # avg = 85 → >80 → level 5


def test_decide_teaching_start_returns_explain_when_mixed():
    """混杂结果且无明显主导类型 → 直接讲解。"""
    concept_gaps = {
        "A": {"gap_type": "overconfident", "calibrated": 50},
        "B": {"gap_type": "aligned_low", "calibrated": 40},
        "C": {"gap_type": "underconfident", "calibrated": 60},
        "D": {"gap_type": "aligned_low", "calibrated": 45},
        "E": {"gap_type": "aligned_low", "calibrated": 55},
        "F": {"gap_type": "aligned_low", "calibrated": 50},
    }
    level, strategy = _decide_teaching_start(concept_gaps)
    assert strategy == "explain"


def test_decide_teaching_start_empty():
    """无数据时返回默认 level=3, explain。"""
    level, strategy = _decide_teaching_start({})
    assert level == 3
    assert strategy == "explain"


class FakeEvaluatorLLM:
    def __init__(self, result):
        self.result = result
        self.messages = []

    def with_structured_output(self, _schema):
        return self

    def invoke(self, messages):
        self.messages.append(messages)
        return self.result


def test_evaluator_emits_assessment_result_contract_and_updates_state(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _seconds: None)

    sink = BufferedEventSink()
    result = SimpleNamespace(
        total_score=52,
        logic_score=55,
        concept_score=49,
        is_correct_direction=True,
        misconceptions=["把闭环稳定性和瞬态性能混为一谈"],
        rubric_feedback=["概念: 混淆稳定性与性能指标（-12）"],
        model_answer="稳定性描述系统是否收敛，瞬态性能描述响应快慢与超调。",
        encouragement="你已经抓到部分关键点了，再把两个指标分清会更稳。",
        next_review_points=["稳定性", "瞬态性能"],
        needs_hint=True,
    )
    node = build_evaluator_node(FakeEvaluatorLLM(result), sink, 80)

    updated = node(
        {
            "current_topic": "控制理论",
            "tutor_content": "讲解内容",
            "tester_question": "什么是稳定性？",
            "user_answer": "我不会",
            "attempt_count": 1,
            "score_history": [(45, 40, 42, "上轮反馈")],
        }
    )

    assessment_event = next(event for event in sink.events if event.type == "assessment.result")
    assert assessment_event.source == "evaluator"
    assert assessment_event.data["total_score"] == 35
    assert assessment_event.data["logic_score"] == 55
    assert assessment_event.data["concept_score"] == 49
    assert assessment_event.data["needs_hint"] is True
    assert assessment_event.data["misconceptions"] == ["把闭环稳定性和瞬态性能混为一谈"]
    assert assessment_event.data["next_review_points"] == ["稳定性", "瞬态性能"]
    assert any(event.type == "node.stream" for event in sink.events)
    assert sink.events[-1].type == "node.complete"

    assert updated["score"] == 35
    assert updated["attempt_count"] == 2
    assert updated["needs_hint"] is True
    assert updated["score_history"][-1] == (35, 55, 49, "你已经抓到部分关键点了，再把两个指标分清会更稳。")
    assert updated["model_answer"] == "稳定性描述系统是否收敛，瞬态性能描述响应快慢与超调。"
    assert updated["misconceptions"] == ["把闭环稳定性和瞬态性能混为一谈"]
    assert updated["next_review_points"] == ["稳定性", "瞬态性能"]


def test_evaluator_builds_teacher_like_feedback_when_model_returns_empty_encouragement(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _seconds: None)

    sink = BufferedEventSink()
    result = SimpleNamespace(
        total_score=61,
        logic_score=66,
        concept_score=58,
        is_correct_direction=True,
        misconceptions=["把稳定性和瞬态性能混在一起了"],
        rubric_feedback=["概念边界不清（-10）"],
        model_answer="稳定性关注是否收敛，瞬态性能关注响应过程。",
        encouragement="",
        next_review_points=["先分开稳定性和瞬态性能"],
        needs_hint=True,
    )
    node = build_evaluator_node(FakeEvaluatorLLM(result), sink, 80)

    updated = node(
        {
            "current_topic": "控制理论",
            "tutor_content": "讲解内容",
            "tester_question": "什么是稳定性？",
            "user_answer": "稳定性和瞬态性能差不多吧。",
            "attempt_count": 0,
            "score_history": [],
        }
    )

    assert updated["feedback"]
    assert "方向基本是对的" in updated["feedback"]
    assert "稳定性和瞬态性能" in updated["feedback"]


def test_evaluator_injects_graph_objectives_and_errors_into_prompt(monkeypatch):
    monkeypatch.setattr("time.sleep", lambda _seconds: None)

    sink = BufferedEventSink()
    llm = FakeEvaluatorLLM(
        SimpleNamespace(
            total_score=82,
            logic_score=84,
            concept_score=80,
            is_correct_direction=True,
            misconceptions=[],
            rubric_feedback=[],
            model_answer="反馈用于改善系统性能。",
            encouragement="主线是对的。",
            next_review_points=[],
            needs_hint=False,
        )
    )
    node = build_evaluator_node(llm, sink, 80)

    updated = node(
        {
            "current_topic": "反馈",
            "tester_question": "反馈有什么作用？",
            "user_answer": "反馈能改善系统表现。",
            "graph_learning_objectives": ["能解释反馈的作用"],
            "graph_common_errors": ["把反馈和闭环画法混为一谈"],
            "graph_must_know": ["输出回到输入形成比较"],
            "attempt_count": 0,
            "score_history": [],
        }
    )

    human_content = llm.messages[0][1].content
    assert "该节点学习目标：能解释反馈的作用" in human_content
    assert "该节点常见误区：把反馈和闭环画法混为一谈" in human_content
    assert updated["next_review_points"] == ["能解释反馈的作用"]
    assert updated["rubric_feedback"] == ["图谱误区参考：把反馈和闭环画法混为一谈"]

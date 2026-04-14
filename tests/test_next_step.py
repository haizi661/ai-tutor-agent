from ai_tutor_agent.core.ports import BufferedEventSink
from ai_tutor_agent.nodes.next_step import build_next_step_node


class FakeAnswerProvider:
    def __init__(self, answer: str):
        self.answer = answer
        self.prompts = []

    def get_answer(self, prompt: str, *, state=None) -> str:
        self.prompts.append({"prompt": prompt, "state": state})
        return self.answer


def test_next_step_selector_routes_to_practice():
    """验证：向 awaiting 恢复路径提供"来一道题"，能路由到 practice_now。"""
    sink = BufferedEventSink()
    provider = FakeAnswerProvider("来一道题")
    node = build_next_step_node(sink, provider)

    # 模拟用户通过按钮选择 practice_now（恢复路径）
    options = [
        {"value": "continue_current", "label": "继续当前"},
        {"value": "practice_now", "label": "来一道题"},
    ]
    result = node(
        {
            "current_topic": "自动控制原理",
            "current_user_goal": "先理解稳定性",
            "flow_status": "awaiting_next_step_selector",
            "pending_interaction_prompt": "你想怎么继续？",
            "pending_interaction_options": options,
            "pending_interaction_recommended": "continue_current",
            "pending_interaction_answer": "来一道题",
        }
    )

    assert result["next_step_choice"] == "practice_now"
    assert result["flow_status"] == "normal"


def test_next_step_selector_auto_advances():
    """验证：正常路径下节点直接自动推进，不再暂停。"""
    sink = BufferedEventSink()
    provider = FakeAnswerProvider("来一道题")
    node = build_next_step_node(sink, provider)

    result = node({"current_topic": "自动控制原理", "current_user_goal": "先理解稳定性"})

    # 自动推进：不会产生 awaiting 状态
    assert result["flow_status"] == "normal"
    assert "next_step_choice" in result
    # 有发出 node.start 事件（包含 auto_advance 标记）
    start_events = [e for e in sink.events if e.type == "node.start"]
    assert any(e.data.get("auto_advance") for e in start_events)


def test_next_step_selector_treats_question_as_interruption():
    sink = BufferedEventSink()
    provider = FakeAnswerProvider("为什么这里要看极点分布？")
    node = build_next_step_node(sink, provider)

    options = [
        {"value": "continue_current", "label": "继续当前"},
        {"value": "practice_now", "label": "来一道题"},
    ]
    result = node(
        {
            "current_topic": "自动控制原理",
            "current_user_goal": "先理解稳定性",
            "conversation_history": [],
            "flow_status": "awaiting_next_step_selector",
            "pending_interaction_prompt": "你想怎么继续？",
            "pending_interaction_options": options,
            "pending_interaction_recommended": "continue_current",
            "pending_interaction_answer": "为什么这里要看极点分布？",
        }
    )

    assert result["interrupt_query"] == "为什么这里要看极点分布？"
    assert result["resume_tester"] is False


def test_next_step_selector_can_switch_to_example_mode():
    sink = BufferedEventSink()
    provider = FakeAnswerProvider("换个例子")
    node = build_next_step_node(sink, provider)

    options = [
        {"value": "example_first", "label": "换个例子"},
        {"value": "continue_current", "label": "继续当前"},
    ]
    result = node(
        {
            "current_topic": "自动控制原理",
            "current_user_goal": "先理解稳定性",
            "flow_status": "awaiting_next_step_selector",
            "pending_interaction_prompt": "你想怎么继续？",
            "pending_interaction_options": options,
            "pending_interaction_recommended": "continue_current",
            "pending_interaction_answer": "换个例子",
        }
    )

    assert result["next_step_choice"] == "example_first"
    assert result["teaching_strategy"] == "analogy"


def test_next_step_selector_uses_practice_specific_prompt_after_coach():
    """验证：有 coach_content 时，自动推进选 example_first（have_recent_coach=True 逻辑）。"""
    sink = BufferedEventSink()
    provider = FakeAnswerProvider("先总结一下")
    node = build_next_step_node(sink, provider)

    result = node(
        {
            "current_topic": "自动控制原理",
            "current_user_goal": "先理解稳定性",
            "turn_goal": "先理解稳定性",
            "tester_question": "什么样的系统是稳定的？",
            "coach_content": "先别急着给完整答案，先看最终趋势。",
        }
    )

    # 有 coach 时推荐 example_first，且自动推进
    assert result["flow_status"] == "normal"
    assert result["next_step_choice"] in {"example_first", "summarize_now", "continue_current", "practice_now"}
    # 自动推进不会等用户
    assert result.get("pending_interaction_kind", "") == ""


def test_next_step_selector_prefers_example_for_zero_base_user():
    """验证：零基础用户，推荐 example_first 并自动推进。"""
    sink = BufferedEventSink()
    provider = FakeAnswerProvider("先换个直观例子")
    node = build_next_step_node(sink, provider)

    result = node(
        {
            "current_topic": "控制原理",
            "current_user_goal": "有哪些核心概念",
            "turn_goal": "先搞懂传递函数和框图",
            "topic_background": "零基础入门",
        }
    )

    assert result["flow_status"] == "normal"
    # 零基础时节点应广播了"零基础"信息的 start 事件
    start_events = [e for e in sink.events if e.type == "node.start"]
    assert start_events, "应该有 node.start 事件"
    assert result["next_step_choice"] == "example_first"
    assert result["teaching_strategy"] == "analogy"


def test_next_step_selector_can_follow_graph_prerequisite_or_related_target():
    """验证：图谱有前置/相关节点时，用户通过恢复路径选"转到相关"，能正确导航。"""
    sink = BufferedEventSink()
    provider = FakeAnswerProvider("转到相关：负反馈")
    node = build_next_step_node(sink, provider)

    # 构造图谱选项（模拟图谱上下文的恢复路径）
    options = [
        {"value": "review_prerequisite", "label": "先补前置：系统", "graph_target": "系统", "graph_relation": "prerequisite"},
        {"value": "continue_current", "label": "继续当前：反馈", "graph_target": "反馈", "graph_relation": "current"},
        {"value": "branch_related", "label": "转到相关：负反馈", "graph_target": "负反馈", "graph_relation": "neighbor"},
        {"value": "practice_now", "label": "围绕反馈来一道题", "graph_target": "反馈", "graph_relation": "practice"},
    ]
    result = node(
        {
            "current_topic": "反馈",
            "current_user_goal": "先理解反馈作用",
            "graph_anchor_title": "反馈",
            "graph_prerequisites": ["系统"],
            "graph_neighbors": ["负反馈"],
            "flow_status": "awaiting_next_step_selector",
            "pending_interaction_prompt": "\u5f53\u524d\u8282\u70b9\u662f\u3010\u53cd\u9988\u3011\u3002\u524d\u7f6e\u662f\u3010\u7cfb\u7edf\u3011\uff0c\u76f8\u5173\u70b9\u662f\u3010\u8d1f\u53cd\u9988\u3011\u6211\u5efa\u8bae\u5148\u9009\u201c\u7ee7\u7eed\u5f53\u524d\uff1a\u53cd\u9988\u201d\u3002",
            "pending_interaction_options": options,
            "pending_interaction_recommended": "continue_current",
            "pending_interaction_answer": "转到相关：负反馈",
        }
    )

    assert result["next_step_choice"] == "branch_related"
    assert result["current_topic"] == "负反馈"
    assert "反馈" in result["current_user_goal"]

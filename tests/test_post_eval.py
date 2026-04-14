from types import SimpleNamespace

from ai_tutor_agent.core.ports import BufferedEventSink
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


def test_post_eval_selector_auto_advances():
    """验证：正常路径下，node 直接自动推进，不暂停等用户。"""
    sink = BufferedEventSink()
    provider = FakeAnswerProvider("继续拔高")
    node = build_post_eval_selector_node(sink, provider)

    result = node({"current_topic": "自动控制原理", "current_user_goal": "稳定性怎么判断"})

    assert result["flow_status"] == "normal"
    assert result["post_eval_choice"] in {"continue_advance", "same_type_practice", "summarize_wrapup"}


def test_post_eval_selector_can_route_to_same_type_practice():
    """验证：恢复路径下，用户选"换一道同类型"能正确路由。"""
    sink = BufferedEventSink()
    provider = FakeAnswerProvider("换一道同类型")
    node = build_post_eval_selector_node(sink, provider)

    options = [dict(o) for o in [
        {"value": "continue_advance", "label": "继续拔高"},
        {"value": "same_type_practice", "label": "换一道同类型"},
        {"value": "summarize_wrapup", "label": "总结本轮收获"},
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
    provider = FakeAnswerProvider("继续拔高")
    node = build_post_eval_selector_node(sink, provider)

    options = [dict(o) for o in [
        {"value": "continue_advance", "label": "继续拔高"},
        {"value": "same_type_practice", "label": "换一道同类型"},
        {"value": "summarize_wrapup", "label": "总结本轮收获"},
    ]]
    result = node(
        {
            "current_topic": "自动控制原理",
            "current_user_goal": "稳定性怎么判断",
            "flow_status": "awaiting_post_eval_selector",
            "pending_interaction_prompt": "你想怎么继续？",
            "pending_interaction_options": options,
            "pending_interaction_answer": "继续拔高",
        }
    )

    assert result["post_eval_choice"] == "continue_advance"
    assert result["teaching_strategy"] == "socratic"
    assert "继续往更高一层" in result["current_user_goal"]


def test_post_eval_wrapup_clears_selector_flags():
    sink = BufferedEventSink()
    llm = FakeStreamingLLM("### 本轮收获\n- 你已经把稳定性的主线抓住了。\n- 现在更清楚先看最终趋势，再判断是否回到平衡。\n- 下次先抓主线，再代回场景。")
    node = build_post_eval_wrapup_node(llm, sink)

    result = node(
        {
            "current_topic": "自动控制原理",
            "current_user_goal": "稳定性怎么判断",
            "feedback": "这轮主线已经答对了。",
            "tutor_content": "本轮讲解聚焦稳定性判断主线。",
            "next_review_points": ["先看最终趋势"],
            "post_eval_choice": "summarize_wrapup",
            "practice_generation_mode": "same_type",
        }
    )

    assert result["post_eval_choice"] == ""
    assert result["practice_generation_mode"] == ""
    assert "本轮收获" in result["tutor_content"]

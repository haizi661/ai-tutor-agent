from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from ..core.events import make_event
from ..core.ports import AnswerProvider, EventSink
from ..core.state import AgentState
from ..core.teacher_voice import build_teacher_voice
from ..core.text import content_to_text


POST_EVAL_OPTIONS = [
    {"value": "continue_advance", "label": "继续拔高"},
    {"value": "same_type_practice", "label": "换一道同类型"},
    {"value": "summarize_wrapup", "label": "总结本轮收获"},
]


def _normalize_choice(text: str) -> str:
    lowered = (text or "").strip().lower()
    mapping = {
        "继续拔高": "continue_advance",
        "拔高": "continue_advance",
        "继续深入": "continue_advance",
        "换一道同类型": "same_type_practice",
        "同类型": "same_type_practice",
        "同类练习": "same_type_practice",
        "再来一题同类型": "same_type_practice",
        "总结本轮收获": "summarize_wrapup",
        "总结": "summarize_wrapup",
        "收获总结": "summarize_wrapup",
        "总结一下": "summarize_wrapup",
    }
    return mapping.get(lowered, lowered)


def _auto_pick_post_eval_choice(state: AgentState) -> str:
    """根据状态启发式决定过关后的下一步，无需用户干预。"""
    score_history: list = list(state.get("score_history") or [])
    attempt_count = int(state.get("attempt_count") or 0)
    difficulty_level = int(state.get("difficulty_level") or 3)

    # 如果同一分数连续高分 ≥ 2 次，倾向总结收束
    if len(score_history) >= 2 and all(s >= 85 for s in score_history[-2:]):
        return "summarize_wrapup"
    # 如果难度已经很高，倾向总结
    if difficulty_level >= 5:
        return "summarize_wrapup"
    # 首次过关或尝试次数少，倾向继续拔高
    if attempt_count <= 1:
        return "continue_advance"
    # 默认：继续拔高
    return "continue_advance"


def build_post_eval_selector_node(event_sink: EventSink, answer_provider: AnswerProvider):
    def node(state: AgentState) -> dict:
        topic = str(state.get("current_topic", "") or "").strip()
        current_goal = str(state.get("current_user_goal", "") or topic).strip()
        awaiting_selector = state.get("flow_status") == "awaiting_post_eval_selector"

        # ── 恢复路径：用户通过按钮显式回传了选择 ──
        if awaiting_selector:
            prompt = str(state.get("pending_interaction_prompt", "") or "").strip()
            options = list(state.get("pending_interaction_options") or [])
            choice = str(state.get("pending_interaction_answer", "") or "").strip()
            if not choice:
                choice = answer_provider.get_answer(
                    prompt,
                    state={
                        "interaction_kind": "post_eval_selector",
                        "options": options,
                        "current_topic": topic,
                        "current_user_goal": current_goal,
                    },
                ).strip()
            normalized_choice = _normalize_choice(choice)
        else:
            # ── 自动推进路径：AI 自主决策 ──
            normalized_choice = _auto_pick_post_eval_choice(state)
            choice = normalized_choice
            event_sink.emit(
                make_event(
                    "node.start",
                    "post_eval_selector",
                    message="这轮已经过关了，我帮你决定下一步。",
                    data={"topic": topic, "auto_choice": normalized_choice},
                )
            )

        if normalized_choice == "same_type_practice":
            event_sink.emit(
                make_event(
                    "node.complete",
                    "post_eval_selector",
                    message="好，我保持同一类题型，再换一道相近练习给你稳一下。",
                )
            )
            return {
                "post_eval_choice": normalized_choice,
                "practice_generation_mode": "same_type",
                "flow_status": "normal",
                "pending_interaction_kind": "",
                "pending_interaction_prompt": "",
                "pending_interaction_options": [],
                "pending_interaction_recommended": "",
                "pending_interaction_answer": "",
                "message_history": list(state.get("message_history", []))
                + [{"role": "user", "kind": "post_eval_choice", "content": choice or normalized_choice}],
            }

        if normalized_choice == "summarize_wrapup":
            event_sink.emit(
                make_event(
                    "node.complete",
                    "post_eval_selector",
                    message="好，我先把这一轮真正拿稳的东西压成一个短总结。",
                )
            )
            return {
                "post_eval_choice": normalized_choice,
                "practice_generation_mode": "",
                "flow_status": "normal",
                "pending_interaction_kind": "",
                "pending_interaction_prompt": "",
                "pending_interaction_options": [],
                "pending_interaction_recommended": "",
                "pending_interaction_answer": "",
                "message_history": list(state.get("message_history", []))
                + [{"role": "user", "kind": "post_eval_choice", "content": choice or normalized_choice}],
            }

        event_sink.emit(
            make_event(
                "node.complete",
                "post_eval_selector",
                message="好，那我就在你已经掌握的基础上，再往前推半步。",
            )
        )
        refined_goal = current_goal
        if refined_goal:
            refined_goal = f"{refined_goal}，继续往更高一层的理解和应用上拔高"
        return {
            "post_eval_choice": "continue_advance",
            "practice_generation_mode": "",
            "flow_status": "normal",
            "pending_interaction_kind": "",
            "pending_interaction_prompt": "",
            "pending_interaction_options": [],
            "pending_interaction_recommended": "",
            "pending_interaction_answer": "",
            "current_user_goal": refined_goal or topic,
            "teaching_strategy": "socratic",
            "next_step_choice": "continue_deeper",
            "message_history": list(state.get("message_history", []))
            + [{"role": "user", "kind": "post_eval_choice", "content": choice or normalized_choice or "继续拔高"}],
        }

    return node


def build_post_eval_wrapup_node(llm, event_sink: EventSink):
    def node(state: AgentState) -> dict:
        topic = str(state.get("current_topic", "") or "").strip()
        current_goal = str(state.get("current_user_goal", "") or topic).strip()
        feedback = str(state.get("feedback", "") or "").strip()
        tutor_content = str(state.get("tutor_content", "") or "").strip()
        review_points = [str(item).strip() for item in (state.get("next_review_points") or []) if str(item).strip()]

        event_sink.emit(
            make_event(
                "node.start",
                "post_eval_wrapup",
                message="我先替你把这一轮真正拿到手的东西收一收。",
                data={"topic": topic},
            )
        )

        system_msg = SystemMessage(
            content=build_teacher_voice(
                """你现在不是继续讲新内容，而是在一次通过后的收束阶段帮学生把收获定型。

输出要求：
1. 标题直接说明“本轮收获”
2. 用 3 个短点收束：这次真正掌握了什么、一个关键判断抓手、下一次再遇到同类问题怎么先下手
3. 全文控制在 180 字以内，不要展开新知识点，不要再出题
4. 语气像老师收尾，不要像系统公告"""
            )
        )
        human_msg = HumanMessage(
            content=(
                f"学习主题：{topic}\n"
                f"当前这轮主要目标：{current_goal}\n"
                f"最近一轮评估反馈：{feedback}\n"
                f"刚才讲解的内容：{tutor_content}\n"
                f"下一步复习点：{'；'.join(review_points) if review_points else '无'}\n"
                "请输出一段短收束，让学生知道这轮到底拿到了什么。"
            )
        )

        full_text = ""
        for chunk in llm.stream([system_msg, human_msg]):
            text = content_to_text(chunk.content)
            full_text += text
            event_sink.emit(make_event("node.stream", "post_eval_wrapup", data={"text": text}))

        full_text = (full_text or "").strip() or "### 本轮收获\n- 这一步的判断主线已经拿稳了。\n- 你现在更清楚先看什么、再判断什么。\n- 下次遇到同类问题，先抓主线，再代回场景。"

        event_sink.emit(
            make_event(
                "node.complete",
                "post_eval_wrapup",
                message="这轮我先替你收束到这里。",
            )
        )
        return {
            "tutor_content": full_text,
            "tutor_citations": [],
            "tutor_evidence": [],
            "post_eval_choice": "",
            "next_step_choice": "",
            "practice_generation_mode": "",
        }

    return node

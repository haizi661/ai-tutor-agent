from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from ..core.homework_bank import build_curated_homework_items
from ..core.learning_support import (
    assign_homework_items,
    build_graph_state_patch,
    recommend_next_node,
)
from ..core.events import make_event
from ..core.ports import AnswerProvider, EventSink, RuntimeContext
from ..core.state import AgentState
from ..core.teacher_voice import build_teacher_voice
from ..core.text import content_to_text
from ..infrastructure.llm import build_llms


POST_EVAL_OPTIONS = [
    {"value": "continue_advance", "label": "继续拔高"},
    {"value": "same_type_practice", "label": "换一道同类型"},
    {"value": "summarize_wrapup", "label": "总结本轮收获"},
]


def _build_selector_llm(runtime: RuntimeContext) -> object | None:
    settings = getattr(runtime, "settings", None)
    if settings is None:
        return None
    try:
        tutor_llm, _, _ = build_llms(settings)
        return tutor_llm
    except Exception:
        return None


def _homework_query_terms(state: AgentState) -> list[str]:
    values = [
        state.get("current_user_goal"),
        state.get("turn_goal"),
        state.get("topic_focus"),
        state.get("current_topic"),
        state.get("current_node_name"),
        state.get("graph_anchor_title"),
        state.get("feedback"),
    ]
    seen: list[str] = []
    for raw in values:
        text = " ".join(str(raw or "").split()).strip()
        if text and text not in seen:
            seen.append(text)
    return seen


def _normalize_choice(text: str) -> str:
    lowered = (text or "").strip().lower()
    mapping = {
        "继续拔高": "continue_advance",
        "开始下一个节点": "continue_advance",
        "开始下一节点": "continue_advance",
        "拔高": "continue_advance",
        "继续深入": "continue_advance",
        "换一道同类型": "same_type_practice",
        "同类型": "same_type_practice",
        "同类练习": "same_type_practice",
        "再来一题同类型": "same_type_practice",
        "总结本轮收获": "summarize_wrapup",
        "今天先到这里": "summarize_wrapup",
        "生成作业": "summarize_wrapup",
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


def _build_post_eval_options(
    state: AgentState,
    graph_rag_pipeline=None,
) -> tuple[list[dict], str, dict[str, str]]:
    current_node_id = str(state.get("current_node_id") or state.get("graph_anchor_id") or "").strip()
    student_state_snapshot = dict(state.get("student_state_snapshot") or {})
    next_candidate = recommend_next_node(
        graph_pipeline=graph_rag_pipeline,
        student_state_snapshot=student_state_snapshot,
        current_node_id=current_node_id,
    )

    if next_candidate:
        continue_label = f"开始下一个节点：{next_candidate.get('name') or next_candidate.get('node_id')}"
    else:
        continue_label = "继续拔高当前节点"

    options = [
        {
            "value": "continue_advance",
            "label": continue_label,
            "graph_target_id": str(next_candidate.get("node_id") or current_node_id).strip(),
            "graph_target_name": str(next_candidate.get("name") or state.get("graph_anchor_title") or state.get("current_node_name") or "").strip(),
        },
        {"value": "same_type_practice", "label": "换一道同类型"},
        {"value": "summarize_wrapup", "label": "今天先到这里，生成作业"},
    ]

    recommended = _auto_pick_post_eval_choice(state)
    if not next_candidate and recommended == "continue_advance":
        recommended = "summarize_wrapup"
    return options, recommended, next_candidate


def build_post_eval_selector_node(
    event_sink: EventSink,
    answer_provider: AnswerProvider,
    graph_rag_pipeline=None,
):
    def node(state: AgentState) -> dict:
        topic = str(state.get("current_topic", "") or "").strip()
        current_goal = str(state.get("current_user_goal", "") or topic).strip()
        awaiting_selector = state.get("flow_status") == "awaiting_post_eval_selector"
        options, recommended, next_candidate = _build_post_eval_options(state, graph_rag_pipeline)
        option_map = {
            str(item.get("value") or "").strip(): item
            for item in options
            if str(item.get("value") or "").strip()
        }

        # ── 恢复路径：用户通过按钮显式回传了选择 ──
        if awaiting_selector:
            prompt = str(state.get("pending_interaction_prompt", "") or "").strip()
            options = list(state.get("pending_interaction_options") or options)
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
            recommended_label = next((item["label"] for item in options if item["value"] == recommended), options[0]["label"])
            next_node_label = str(next_candidate.get("name") or next_candidate.get("node_id") or "").strip()
            suffix = (
                f" 我建议下一步进入【{next_node_label}】。"
                if next_node_label
                else " 我建议先收尾并布置作业。"
            )
            message = f"这一节点已经通过了。{suffix}"
            event_sink.emit(
                make_event(
                    "node.start",
                    "post_eval_selector",
                    message=message,
                    data={
                        "topic": topic,
                        "recommended": recommended,
                        "recommended_label": recommended_label,
                        "options": options,
                        "next_node_candidate": next_candidate,
                        "requires_input": True,
                    },
                )
            )
            prompt = (
                f"这一节点已经通过。当前建议：{recommended_label}。"
                "你可以选择开始下一个节点、换一道同类型题，或者今天先到这里生成作业。"
            )
            return {
                "flow_status": "awaiting_post_eval_selector",
                "learning_phase": "node_passed",
                "learning_resume_target": "post_eval_selector",
                "learning_resume_reason": "post_eval_choice_required",
                "next_node_candidate_id": str(next_candidate.get("node_id") or "").strip(),
                "next_node_candidate_name": str(next_candidate.get("name") or "").strip(),
                "pending_interaction_kind": "post_eval_selector",
                "pending_interaction_prompt": prompt,
                "pending_interaction_options": options,
                "pending_interaction_recommended": recommended,
                "pending_interaction_answer": "",
            }

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
                "learning_phase": "node_quiz_remediation",
                "learning_resume_target": "tester",
                "learning_resume_reason": "post_eval_same_type",
                "current_node_status": "quizzing",
                "pending_interaction_kind": "",
                "pending_interaction_prompt": "",
                "pending_interaction_options": [],
                "pending_interaction_recommended": "",
                "pending_interaction_answer": "",
                "message_history": list(state.get("message_history", []))
                + [
                    {
                        "role": "user",
                        "kind": "post_eval_choice",
                        "content": choice or normalized_choice,
                        "data": {"selected_value": normalized_choice},
                    }
                ],
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
                "learning_phase": "daily_wrapup",
                "learning_resume_target": "post_eval_wrapup",
                "learning_resume_reason": "post_eval_wrapup",
                "current_node_status": "passed",
                "pending_interaction_kind": "",
                "pending_interaction_prompt": "",
                "pending_interaction_options": [],
                "pending_interaction_recommended": "",
                "pending_interaction_answer": "",
                "message_history": list(state.get("message_history", []))
                + [
                    {
                        "role": "user",
                        "kind": "post_eval_choice",
                        "content": choice or normalized_choice,
                        "data": {"selected_value": normalized_choice},
                    }
                ],
            }

        chosen_option = option_map.get(normalized_choice, {})
        next_node_id = str(
            chosen_option.get("graph_target_id")
            or state.get("next_node_candidate_id")
            or next_candidate.get("node_id")
            or state.get("graph_anchor_id")
            or ""
        ).strip()
        next_node_name = str(
            chosen_option.get("graph_target_name")
            or state.get("next_node_candidate_name")
            or next_candidate.get("name")
            or state.get("graph_anchor_title")
            or ""
        ).strip()
        graph_state_patch = build_graph_state_patch(graph_rag_pipeline, next_node_id)

        event_sink.emit(
            make_event(
                "node.complete",
                "post_eval_selector",
                message=(
                    f"好，我们转到下一个节点【{next_node_name or next_node_id}】继续学习。"
                    if next_node_id and next_node_id != str(state.get('graph_anchor_id') or '').strip()
                    else "好，我就在你已经掌握的基础上，再往前推半步。"
                ),
            )
        )
        return {
            "post_eval_choice": "continue_advance",
            "practice_generation_mode": "",
            "flow_status": "normal",
            "learning_phase": "node_selected",
            "learning_resume_target": "tutor",
            "learning_resume_reason": "post_eval_continue_advance",
            "current_node_status": "selected",
            "pending_interaction_kind": "",
            "pending_interaction_prompt": "",
            "pending_interaction_options": [],
            "pending_interaction_recommended": "",
            "pending_interaction_answer": "",
            "current_user_goal": next_node_name or current_goal or topic,
            "turn_goal": next_node_name or current_goal or topic,
            "topic_focus": next_node_name or current_goal or topic,
            "teaching_strategy": "explain",
            "next_step_choice": "continue_deeper",
            "next_node_candidate_id": next_node_id,
            "next_node_candidate_name": next_node_name,
            **graph_state_patch,
            "message_history": list(state.get("message_history", []))
            + [
                {
                    "role": "user",
                    "kind": "post_eval_choice",
                    "content": choice or normalized_choice or "继续拔高",
                    "data": {"selected_value": "continue_advance"},
                }
            ],
        }

    return node


def build_post_eval_wrapup_node(llm, runtime_or_event_sink: RuntimeContext | EventSink):
    if isinstance(runtime_or_event_sink, RuntimeContext):
        runtime = runtime_or_event_sink
        event_sink = runtime_or_event_sink.event_sink
        graph_rag_pipeline = getattr(runtime_or_event_sink, "graph_rag_pipeline", None)
        student_state_store = getattr(runtime_or_event_sink, "student_state_store", None)
    else:
        runtime = None
        event_sink = runtime_or_event_sink
        graph_rag_pipeline = None
        student_state_store = None

    def node(state: AgentState) -> dict:
        topic = str(state.get("current_topic", "") or "").strip()
        current_goal = str(state.get("current_user_goal", "") or topic).strip()
        feedback = str(state.get("feedback", "") or "").strip()
        tutor_content = str(state.get("tutor_content", "") or "").strip()
        review_points = [str(item).strip() for item in (state.get("next_review_points") or []) if str(item).strip()]
        student_id = str(state.get("student_id") or "default_student").strip() or "default_student"
        student_state_snapshot = dict(state.get("student_state_snapshot") or {})

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
        homework_items = build_curated_homework_items(
            question_bank_provider=getattr(runtime, "question_bank_provider", None),
            graph_pipeline=graph_rag_pipeline,
            student_state_snapshot=student_state_snapshot,
            query_terms=_homework_query_terms(state),
            llm=_build_selector_llm(runtime),
            current_node_id=str(state.get("current_node_id") or "").strip(),
            graph_anchor_id=str(state.get("graph_anchor_id") or "").strip(),
            limit=2,
        )
        updated_snapshot = assign_homework_items(
            student_state_store,
            student_id=student_id,
            homework_items=homework_items,
        )
        if updated_snapshot:
            student_state_snapshot = updated_snapshot
        if homework_items:
            homework_lines = ["### 今日作业"]
            for index, item in enumerate(homework_items, start=1):
                homework_lines.append(f"{index}. {item.get('prompt')}")
            full_text = f"{full_text}\n\n" + "\n".join(homework_lines)

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
            "flow_status": "homework_assigned" if homework_items else "normal",
            "homework_items": homework_items,
            "homework_status": "assigned" if homework_items else "",
            "student_state_snapshot": student_state_snapshot,
            "learning_phase": "daily_wrapup",
            "learning_resume_reason": "homework_assigned" if homework_items else "daily_wrapup_completed",
        }

    return node

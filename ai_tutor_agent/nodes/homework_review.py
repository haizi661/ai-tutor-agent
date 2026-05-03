from __future__ import annotations

from ..core.events import make_event
from ..core.ports import RuntimeContext
from ..core.state import AgentState

HOMEWORK_REVIEW_OPTIONS = [
    {"value": "answer_homework", "label": "现在做作业"},
    {"value": "save_for_later", "label": "保存，下次再做"},
    {"value": "continue_learning", "label": "保留作业，继续学习"},
]


def _normalize_choice(text: str) -> str:
    lowered = str(text or "").strip().lower()
    mapping = {
        "先做作业": "answer_homework",
        "现在做": "answer_homework",
        "现在做作业": "answer_homework",
        "处理作业": "answer_homework",
        "做作业": "answer_homework",
        "作业": "answer_homework",
        "answer_homework": "answer_homework",
        "稍后做": "save_for_later",
        "晚点做": "save_for_later",
        "下次做": "save_for_later",
        "保存下次做": "save_for_later",
        "保存，下次再做": "save_for_later",
        "save_for_later": "save_for_later",
        "继续": "continue_learning",
        "继续学习": "continue_learning",
        "下一节点": "continue_learning",
        "开始下一节点": "continue_learning",
        "暂缓作业": "continue_learning",
        "保留作业，继续学习": "continue_learning",
        "continue_learning": "continue_learning",
    }
    return mapping.get(lowered, lowered)


def _format_homework_prompt(items: list[dict]) -> str:
    lines = ["这份作业已按当前图谱节点保存。请选择：现在做、保存下次再做，或保留作业继续学习。"]
    for index, item in enumerate(items[:3], start=1):
        prompt = str(item.get("prompt") or "").strip()
        if prompt:
            lines.append(f"{index}. {prompt}")
    if len(items) > 3:
        lines.append(f"另外还有 {len(items) - 3} 道作业题保存在记录中。")
    return "\n".join(lines)


def build_homework_review_node(runtime: RuntimeContext):
    event_sink = runtime.event_sink
    answer_provider = runtime.answer_provider

    def node(state: AgentState) -> dict:
        homework_items = list(state.get("homework_items") or [])
        awaiting_choice = state.get("flow_status") == "awaiting_homework_review_choice"

        if not awaiting_choice:
            prompt = _format_homework_prompt(homework_items)
            event_sink.emit(
                make_event(
                    "node.start",
                    "homework_review",
                    message=prompt,
                    data={"homework_count": len(homework_items), "options": HOMEWORK_REVIEW_OPTIONS},
                )
            )
            return {
                "flow_status": "awaiting_homework_review_choice",
                "learning_phase": "homework_resume",
                "learning_resume_target": "homework_review",
                "learning_resume_reason": "homework_review_choice_required",
                "pending_interaction_kind": "homework_review_choice",
                "pending_interaction_prompt": prompt,
                "pending_interaction_options": HOMEWORK_REVIEW_OPTIONS,
                "pending_interaction_recommended": "answer_homework",
                "pending_interaction_answer": "",
            }

        choice = str(state.get("pending_interaction_answer") or "").strip()
        if not choice:
            choice = answer_provider.get_answer(
                str(state.get("pending_interaction_prompt") or ""),
                state={
                    "interaction_kind": "homework_review_choice",
                    "options": HOMEWORK_REVIEW_OPTIONS,
                    "homework_count": len(homework_items),
                },
            ).strip()
        normalized_choice = _normalize_choice(choice) or "answer_homework"
        if normalized_choice not in {"answer_homework", "save_for_later", "continue_learning"}:
            normalized_choice = "answer_homework"
        message_history = list(state.get("message_history", []))
        message_history.append(
            {
                "role": "user",
                "kind": "homework_review_choice",
                "content": choice or normalized_choice,
                "data": {"selected_value": normalized_choice},
            }
        )

        if normalized_choice == "save_for_later":
            event_sink.emit(
                make_event(
                    "node.complete",
                    "homework_review",
                    message="好，作业已保存。下次恢复这个学习页时会继续显示，不会重新生成。",
                    data={"homework_count": len(homework_items)},
                )
            )
            return {
                "flow_status": "homework_assigned",
                "homework_status": "assigned",
                "learning_phase": "daily_wrapup",
                "learning_resume_target": "session_resume_router",
                "learning_resume_reason": "homework_saved_for_later",
                "pending_interaction_kind": "",
                "pending_interaction_prompt": "",
                "pending_interaction_options": [],
                "pending_interaction_recommended": "",
                "pending_interaction_answer": "",
                "message_history": message_history,
            }

        if normalized_choice == "continue_learning":
            next_node_id = str(state.get("next_node_candidate_id") or "").strip()
            next_node_name = str(state.get("next_node_candidate_name") or next_node_id).strip()
            event_sink.emit(
                make_event(
                    "node.complete",
                    "homework_review",
                    message="好，作业先保留为暂缓状态，我们继续学习。",
                    data={"next_node_id": next_node_id},
                )
            )
            return {
                "flow_status": "normal",
                "homework_status": "deferred",
                "learning_phase": "node_selected",
                "learning_resume_target": "node_content_loader" if next_node_id else "next_node_planner",
                "learning_resume_reason": "homework_deferred_continue_learning",
                "current_node_id": next_node_id,
                "current_node_name": next_node_name,
                "current_node_status": "selected" if next_node_id else state.get("current_node_status", ""),
                "current_user_goal": next_node_name or state.get("current_user_goal", ""),
                "turn_goal": next_node_name or state.get("turn_goal", ""),
                "topic_focus": next_node_name or state.get("topic_focus", ""),
                "pending_interaction_kind": "",
                "pending_interaction_prompt": "",
                "pending_interaction_options": [],
                "pending_interaction_recommended": "",
                "pending_interaction_answer": "",
                "message_history": message_history,
            }

        event_sink.emit(
            make_event(
                "node.complete",
                "homework_review",
                message="好，我们先处理上次作业。请提交你的作业答案。",
                data={"homework_count": len(homework_items)},
            )
        )
        return {
            "flow_status": "awaiting_homework_answers",
            "homework_status": "in_progress",
            "learning_phase": "homework_resume",
            "learning_resume_target": "homework_answer_dialog",
            "learning_resume_reason": "homework_answer_required",
            "pending_interaction_kind": "homework_answers",
            "pending_interaction_prompt": "请按题号提交你的作业答案。",
            "pending_interaction_options": [],
            "pending_interaction_recommended": "",
            "pending_interaction_answer": "",
            "message_history": message_history,
        }

    return node

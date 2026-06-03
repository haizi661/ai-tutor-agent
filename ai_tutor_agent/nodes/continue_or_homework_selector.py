from __future__ import annotations

from ..core.events import make_event
from ..core.ports import RuntimeContext
from ..core.state import AgentState


CONTINUE_OR_HOMEWORK_OPTIONS = [
    {"value": "continue_next_node", "label": "开始下一个节点"},
    {"value": "stop_today", "label": "今天不学了，生成作业"},
]


def _normalize_choice(text: str) -> str:
    lowered = str(text or "").strip().lower()
    mapping = {
        "继续": "continue_next_node",
        "继续学习": "continue_next_node",
        "开始下一个节点": "continue_next_node",
        "开始下一节点": "continue_next_node",
        "下一个节点": "continue_next_node",
        "continue": "continue_next_node",
        "continue_next_node": "continue_next_node",
        "今天不学了": "stop_today",
        "今天先到这里": "stop_today",
        "不学了": "stop_today",
        "生成作业": "stop_today",
        "作业": "stop_today",
        "stop": "stop_today",
        "stop_today": "stop_today",
        "开始新一轮": "start_next_round",
        "新一轮": "start_next_round",
        "继续下一轮": "start_next_round",
        "start_next_round": "start_next_round",
    }
    if lowered in mapping:
        return mapping[lowered]
    if "生成作业" in lowered or "不学了" in lowered or "先到这里" in lowered:
        return "stop_today"
    if "继续学习" in lowered or "下一个节点" in lowered or "下一节点" in lowered:
        return "continue_next_node"
    return lowered


def build_continue_or_homework_selector_node(runtime: RuntimeContext):
    event_sink = runtime.event_sink
    answer_provider = runtime.answer_provider

    def node(state: AgentState) -> dict:
        awaiting_choice = state.get("flow_status") == "awaiting_continue_or_homework_choice"
        candidate_id = str(state.get("next_node_candidate_id") or "").strip()
        candidate_name = str(state.get("next_node_candidate_name") or "").strip()
        is_plan_completed = state.get("learning_plan_source") == "plan_completed"

        # ── Build options & prompt based on context ──
        if is_plan_completed:
            session_index = str(state.get("student_state_snapshot", {}).get("session_index", "") or "")
            index_tag = f"（第{session_index}次）" if session_index else ""
            options = [
                {"value": "start_next_round", "label": "开始新一轮学习"},
                {"value": "stop_today", "label": "今天就到这里"},
            ]
            recommended = "start_next_round"
            prompt = f"本次学习路径{index_tag}已完成！你可以开始新一轮学习，或今天就到这里。"
        else:
            options = list(CONTINUE_OR_HOMEWORK_OPTIONS)
            if not candidate_id:
                options = [item for item in options if item["value"] != "continue_next_node"]
            recommended = "continue_next_node" if candidate_id else "stop_today"

        if not awaiting_choice:
            if not is_plan_completed:
                next_label = candidate_name or candidate_id or "暂无可继续的新节点"
                prompt = (
                    f"当前节点已经通过。下一候选节点：{next_label}。"
                    "你现在只需要做一个选择：开始下一个节点，或今天不学了并生成作业。"
                )
            event_sink.emit(
                make_event(
                    "node.start",
                    "continue_or_homework_selector",
                    message=prompt,
                    data={"options": options, "recommended": recommended, "next_node_id": candidate_id},
                )
            )
            return {
                "flow_status": "awaiting_continue_or_homework_choice",
                "learning_phase": "continue_or_homework_choice",
                "learning_resume_target": "continue_or_homework_selector",
                "learning_resume_reason": "continue_or_homework_choice_required",
                "pending_interaction_kind": "continue_or_homework_choice",
                "pending_interaction_prompt": prompt,
                "pending_interaction_options": options,
                "pending_interaction_recommended": recommended,
                "pending_interaction_answer": "",
            }

        choice = str(state.get("pending_interaction_answer") or "").strip()
        if not choice:
            choice = answer_provider.get_answer(
                str(state.get("pending_interaction_prompt") or ""),
                state={
                    "interaction_kind": "continue_or_homework_choice",
                    "options": options,
                    "recommended": recommended,
                    "next_node_id": candidate_id,
                    "next_node_name": candidate_name,
                },
            ).strip()
        normalized_choice = _normalize_choice(choice) or recommended
        valid_choices = {"continue_next_node", "stop_today", "start_next_round"}
        if normalized_choice not in valid_choices:
            normalized_choice = recommended
        if normalized_choice == "continue_next_node" and not candidate_id:
            normalized_choice = "stop_today"

        if normalized_choice == "start_next_round":
            event_sink.emit(
                make_event(
                    "node.complete",
                    "continue_or_homework_selector",
                    message="好，我们开始新一轮学习！",
                )
            )
            return {
                "continue_or_homework_choice": "start_next_round",
                "flow_status": "normal",
                "learning_phase": "next_round_requested",
                "learning_resume_target": "learning_plan_generator",
                "learning_resume_reason": "start_next_round_selected",
                "pending_interaction_kind": "",
                "pending_interaction_prompt": "",
                "pending_interaction_options": [],
                "pending_interaction_recommended": "",
                "pending_interaction_answer": "",
                "message_history": list(state.get("message_history", []))
                + [
                    {
                        "role": "user",
                        "kind": "continue_or_homework_choice",
                        "content": choice or normalized_choice,
                        "data": {"selected_value": normalized_choice},
                    }
                ],
            }
        elif normalized_choice == "continue_next_node":
            event_sink.emit(
                make_event(
                    "node.complete",
                    "continue_or_homework_selector",
                    message=f"好，我们进入下一个节点【{candidate_name or candidate_id}】。",
                )
            )
            return {
                "continue_or_homework_choice": "continue_next_node",
                "flow_status": "normal",
                "learning_phase": "node_selected",
                "learning_resume_target": "node_content_loader",
                "learning_resume_reason": "continue_next_node_selected",
                "current_node_id": candidate_id,
                "current_node_name": candidate_name or candidate_id,
                "current_node_status": "selected",
                "current_user_goal": candidate_name or candidate_id,
                "turn_goal": candidate_name or candidate_id,
                "topic_focus": candidate_name or candidate_id,
                "post_lesson_choice": "",
                "node_quiz_items": [],
                "node_quiz_answers": {},
                "node_quiz_wrong_items": [],
                "node_quiz_score": 0,
                "variant_questions": [],
                "wrong_question_explanations": [],
                "pending_interaction_kind": "",
                "pending_interaction_prompt": "",
                "pending_interaction_options": [],
                "pending_interaction_recommended": "",
                "pending_interaction_answer": "",
                "message_history": list(state.get("message_history", []))
                + [
                    {
                        "role": "user",
                        "kind": "continue_or_homework_choice",
                        "content": choice or normalized_choice,
                        "data": {"selected_value": normalized_choice},
                    }
                ],
            }

        event_sink.emit(
            make_event(
                "node.complete",
                "continue_or_homework_selector",
                message="好，今天先到这里。接下来我会根据今天和此前的学习记录生成作业。",
            )
        )
        return {
            "continue_or_homework_choice": "stop_today",
            "flow_status": "normal",
            "learning_phase": "homework_generation_requested",
            "learning_resume_target": "homework_generator",
            "learning_resume_reason": "stop_today_selected",
            "pending_interaction_kind": "",
            "pending_interaction_prompt": "",
            "pending_interaction_options": [],
            "pending_interaction_recommended": "",
            "pending_interaction_answer": "",
            "message_history": list(state.get("message_history", []))
            + [
                {
                    "role": "user",
                    "kind": "continue_or_homework_choice",
                    "content": choice or normalized_choice,
                    "data": {"selected_value": normalized_choice},
                }
            ],
        }

    return node

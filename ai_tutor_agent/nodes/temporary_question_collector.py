from __future__ import annotations

from ..core.events import make_event
from ..core.ports import EventSink
from ..core.state import AgentState


def _clean_question(text: str) -> str:
    value = str(text or "").strip()
    if value.lower().startswith("/ask"):
        value = value[4:].strip()
    return value


def _append_interrupt_user_message(history: list, query: str) -> list:
    updated = list(history or [])
    updated.append({"role": "user", "kind": "interruption_user", "content": query})
    return updated


def build_temporary_question_collector_node(event_sink: EventSink):
    def node(state: AgentState) -> dict:
        awaiting_question = state.get("flow_status") == "awaiting_temporary_question"
        raw_answer = str(state.get("pending_interaction_answer") or "").strip()
        direct_query = str(state.get("interrupt_query") or "").strip()
        query = _clean_question(raw_answer or direct_query)

        if not awaiting_question and not query:
            node_name = str(state.get("current_node_name") or state.get("graph_anchor_title") or state.get("current_node_id") or "当前节点").strip()
            prompt = f"围绕【{node_name}】，把你卡住的地方直接说出来就行；可以是一句话、一个反例、一个公式或一个图上的疑问。"
            options = [
                {"id": "temporary_question", "label": "直接输入追问"},
                {"id": "example_question", "label": "比如：这一步为什么成立？"},
            ]
            event_sink.emit(
                make_event(
                    "node.start",
                    "temporary_question_collector",
                    message=prompt,
                    data={"options": options, "node_id": state.get("current_node_id", "")},
                )
            )
            return {
                "flow_status": "awaiting_temporary_question",
                "learning_phase": "temporary_question_collecting",
                "learning_resume_target": "temporary_question_collector",
                "learning_resume_reason": "temporary_question_required",
                "pending_interaction_kind": "temporary_question",
                "pending_interaction_prompt": prompt,
                "pending_interaction_options": options,
                "pending_interaction_recommended": "temporary_question",
                "pending_interaction_answer": "",
            }

        if not query:
            prompt = str(state.get("pending_interaction_prompt") or "请直接输入你的临时问题。")
            event_sink.emit(
                make_event(
                    "node.start",
                    "temporary_question_collector",
                    message=prompt,
                    data={"requires_question": True},
                )
            )
            return {
                "flow_status": "awaiting_temporary_question",
                "learning_phase": "temporary_question_collecting",
                "learning_resume_target": "temporary_question_collector",
                "learning_resume_reason": "temporary_question_empty_retry",
                "pending_interaction_kind": "temporary_question",
                "pending_interaction_prompt": prompt,
                "pending_interaction_answer": "",
            }

        event_sink.emit(
            make_event(
                "node.complete",
                "temporary_question_collector",
                message="已收到这个临时问题，马上调用图谱 2.2 检索并解释。",
                data={"query": query},
            )
        )
        return {
            "interrupt_query": query,
            "flow_status": "normal",
            "learning_phase": "node_temp_qna",
            "learning_resume_target": "interruption_tutor",
            "learning_resume_reason": "temporary_question_collected",
            "pending_interaction_kind": "",
            "pending_interaction_prompt": "",
            "pending_interaction_options": [],
            "pending_interaction_recommended": "",
            "pending_interaction_answer": "",
            "resume_tester": bool(state.get("resume_tester", False)),
            "conversation_history": _append_interrupt_user_message(state.get("conversation_history", []), query),
        }

    return node

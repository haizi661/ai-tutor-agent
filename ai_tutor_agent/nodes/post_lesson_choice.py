from __future__ import annotations

from ..core.events import make_event
from ..core.ports import AnswerProvider, EventSink
from ..core.state import AgentState


OPTIONS = [
    {"value": "temporary_question", "label": "继续追问"},
    {"value": "start_test", "label": "我懂了，进入小测"},
]


def _normalize_choice(text: str) -> str:
    value = str(text or "").strip().lower()
    mapping = {
        "1": "temporary_question",
        "临时问题": "temporary_question",
        "我还有临时问题": "temporary_question",
        "继续追问": "temporary_question",
        "还有问题": "temporary_question",
        "提问": "temporary_question",
        "2": "start_test",
        "开始测试": "start_test",
        "我懂了，进入小测": "start_test",
        "进入小测": "start_test",
        "没有问题，开始测试": "start_test",
        "没有问题": "start_test",
        "没问题": "start_test",
        "测试": "start_test",
        "start_test": "start_test",
        "temporary_question": "temporary_question",
    }
    return mapping.get(value, value)


def _looks_like_direct_question(text: str) -> bool:
    value = str(text or "").strip()
    if not value:
        return False
    if "?" in value or "？" in value:
        return True
    question_markers = (
        "为什么",
        "怎么",
        "如何",
        "什么",
        "能不能",
        "是不是",
        "区别",
        "联系",
        "解释",
        "举例",
        "不懂",
        "没懂",
        "没太明白",
        "不太明白",
        "还是",
        "卡住",
        "疑惑",
        "看不懂",
        "听不懂",
        "没理解",
        "不理解",
    )
    if any(marker in value for marker in question_markers):
        return True
    start_test_markers = ("开始测试", "进入小测", "没有问题", "没问题", "懂了", "会了", "测试", "start_test", "temporary_question")
    if any(marker in value for marker in start_test_markers):
        return False
    # 课后选择阶段的自由输入通常不是命令，而是在描述卡点；不要把“没带问号的追问”误判成开始测试。
    return len(value) >= 8


def _compute_recommendation(state: AgentState) -> str:
    """根据教学上下文动态推荐课后行为。

    推荐规则:
    - 学生复学(attempt_count > 0)或情绪信号显示受挫 → 推荐继续追问
    - 节点交互轮次超过 2 轮 → 推荐进入小测(已有足够学习深度)
    - 默认:推荐进入小测
    """
    attempt_count = int(state.get("attempt_count") or 0)
    if attempt_count > 0:
        return "temporary_question"

    current_node = str(state.get("current_node_name") or state.get("graph_anchor_title") or "").strip()
    user_kg: dict = dict(state.get("user_knowledge_graph") or {})
    node_entry = user_kg.get(current_node, {})
    if isinstance(node_entry, dict) and int(node_entry.get("turn_count") or 0) > 2:
        return "start_test"

    affect_str = str(state.get("last_affect") or "").strip()
    if affect_str in ("困惑", "confused", "焦虑", "anxious", "受挫"):
        return "temporary_question"

    return "start_test"


def build_post_lesson_choice_node(event_sink: EventSink, answer_provider: AnswerProvider):
    def node(state: AgentState) -> dict:
        current_node_name = str(state.get("current_node_name") or state.get("graph_anchor_title") or state.get("current_topic") or "当前节点").strip()
        awaiting = state.get("flow_status") == "awaiting_post_lesson_choice"

        if not awaiting:
            recommended = _compute_recommendation(state)
            prompt = f"节点【{current_node_name}】先讲到这里。你可以直接追问，也可以一句话说卡点；如果已经顺了，就进入小测。"
            event_sink.emit(
                make_event(
                    "node.start",
                    "post_lesson_choice",
                    message=prompt,
                    data={"options": OPTIONS, "recommended": recommended, "requires_input": True},
                )
            )
            return {
                "flow_status": "awaiting_post_lesson_choice",
                "post_lesson_choice": "",
                "learning_phase": "post_lesson_choice",
                "learning_resume_target": "post_lesson_choice",
                "learning_resume_reason": "post_lesson_choice_required",
                "pending_interaction_kind": "post_lesson_choice",
                "pending_interaction_prompt": prompt,
                "pending_interaction_options": OPTIONS,
                "pending_interaction_recommended": recommended,
                "pending_interaction_answer": "",
                "current_node_status": "taught",
            }

        prompt = str(state.get("pending_interaction_prompt") or "讲解完成后请选择下一步。").strip()
        choice = str(state.get("pending_interaction_answer") or "").strip()
        if not choice:
            choice = answer_provider.get_answer(
                prompt,
                state={
                    "interaction_kind": "post_lesson_choice",
                    "options": state.get("pending_interaction_options") or OPTIONS,
                    "current_node_id": state.get("current_node_id") or state.get("graph_anchor_id") or "",
                },
            ).strip()
        normalized = _normalize_choice(choice)
        direct_question = _looks_like_direct_question(choice)
        selected_value = normalized if normalized in {"temporary_question", "start_test"} else ""
        if direct_question and not selected_value:
            selected_value = "temporary_question"

        base = {
            "flow_status": "normal",
            "post_lesson_choice": normalized,
            "pending_interaction_kind": "",
            "pending_interaction_prompt": "",
            "pending_interaction_options": [],
            "pending_interaction_recommended": "",
            "pending_interaction_answer": "",
            "message_history": list(state.get("message_history", []))
            + [
                {
                    "role": "user",
                    "kind": "post_lesson_choice",
                    "content": choice or normalized,
                    "data": {
                        "selected_value": selected_value,
                        "direct_question": direct_question,
                        "question": choice if direct_question else "",
                    },
                }
            ],
        }

        if normalized == "temporary_question" or direct_question:
            event_sink.emit(make_event("node.complete", "post_lesson_choice", message="好，先处理你的临时问题。"))
            patch = {
                **base,
                "post_lesson_choice": "temporary_question",
                "learning_phase": "temporary_question_collecting",
                "learning_resume_target": "temporary_question_collector",
                "learning_resume_reason": "post_lesson_temporary_question",
            }
            if normalized != "temporary_question":
                patch["interrupt_query"] = choice
            return patch

        event_sink.emit(make_event("node.complete", "post_lesson_choice", message="好，进入本节点的客观题测试。"))
        return {
            **base,
            "post_lesson_choice": "start_test",
            "learning_phase": "node_quiz_batch",
            "learning_resume_target": "objective_test_generator",
            "learning_resume_reason": "post_lesson_start_test",
            "current_node_status": "quizzing",
        }

    return node

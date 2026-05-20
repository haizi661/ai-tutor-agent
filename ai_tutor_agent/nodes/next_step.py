from __future__ import annotations

import json
import logging

from ..core.events import make_event
from ..core.graph_service import GraphQueryService
from ..core.ports import AnswerProvider, EventSink
from ..core.state import AgentState

logger = logging.getLogger(__name__)


NEXT_STEP_OPTIONS = [
    {"value": "continue_deeper", "label": "继续深入"},
    {"value": "example_first", "label": "换个例子"},
    {"value": "practice_now", "label": "来一道题"},
    {"value": "summarize_now", "label": "先总结一下"},
]

QUESTION_HINTS = (
    "为什么",
    "怎么",
    "如何",
    "请问",
    "是什么",
    "什么意思",
    "能不能",
    "可不可以",
    "请解释",
    "解释一下",
    "举个例子",
)


def _normalize_choice(text: str) -> str:
    lowered = (text or "").strip().lower()
    if lowered.startswith("先补前置"):
        return "review_prerequisite"
    if lowered.startswith("转到相关"):
        return "branch_related"
    if lowered.startswith("继续当前"):
        return "continue_current"
    if lowered.startswith("围绕") and "来一道题" in lowered:
        return "practice_now"
    mapping = {
        "继续深入": "continue_deeper",
        "继续": "continue_deeper",
        "深入": "continue_deeper",
        "继续当前": "continue_current",
        "换个例子": "example_first",
        "先换个直观例子": "example_first",
        "换个讲法再看一遍": "example_first",
        "例子": "example_first",
        "举个例子": "example_first",
        "先补前置": "review_prerequisite",
        "补前置": "review_prerequisite",
        "前置": "review_prerequisite",
        "转到相关": "branch_related",
        "相关": "branch_related",
        "来一道题": "practice_now",
        "来一道轻一点的题": "practice_now",
        "来题": "practice_now",
        "练习": "practice_now",
        "做题": "practice_now",
        "先总结一下": "summarize_now",
        "先把框架收一下": "summarize_now",
        "先把整体地图列出来": "summarize_now",
        "先收住这一步": "summarize_now",
        "总结": "summarize_now",
        "回顾": "summarize_now",
        "顺着这个点继续讲": "continue_deeper",
        "顺着这个卡点继续讲": "continue_deeper",
    }
    return mapping.get(lowered, lowered)


def _looks_like_question(text: str) -> bool:
    cleaned = (text or "").strip()
    if not cleaned:
        return False
    if any(mark in cleaned for mark in ["?", "？"]):
        return True
    return any(hint in cleaned for hint in QUESTION_HINTS)


def _normalize_text(text: str) -> str:
    return " ".join(str(text or "").strip().split())


def _graph_options(state: AgentState) -> tuple[list[dict], str]:
    current_topic = _normalize_text(state.get("graph_anchor_title", ""))
    prerequisites = [_normalize_text(item) for item in (state.get("graph_prerequisites") or []) if _normalize_text(item)]
    neighbors = [_normalize_text(item) for item in (state.get("graph_neighbors") or []) if _normalize_text(item)]
    learning_objectives = state.get("graph_learning_objectives", [])
    common_errors = state.get("graph_common_errors", [])
    must_know = state.get("graph_must_know", [])
    difficulty_level = state.get("difficulty_level", 3)
    has_recent_coach = bool(_normalize_text(state.get("coach_content", "")))
    score = state.get("score", 0)
    node_status = str(((state.get("user_knowledge_graph") or {}).get(current_topic) or {}).get("status") or "").strip()

    if not current_topic:
        return [], ""

    options = []

    # 智能推荐逻辑：根据学生当前状态决定推荐
    # 情况1：刚被coach辅导过或分数很低 → 优先补前置
    # 情况2：有common_errors且还没练过 → 优先练习
    # 情况3：难度低/零基础 → 优先继续讲或看例子
    # 情况4：默认 → 继续当前
    if (node_status == "mastered" or score >= 85) and neighbors:
        recommended = "branch_related"
    elif has_recent_coach and prerequisites:
        recommended = "review_prerequisite"
    elif common_errors and score <= 40:
        recommended = "practice_now"
    elif difficulty_level <= 2 and prerequisites:
        recommended = "review_prerequisite"
    else:
        recommended = "continue_current"

    if prerequisites:
        # 如果有多个前置，展示最多2个
        for i, prereq in enumerate(prerequisites[:2]):
            options.append(
                {
                    "value": "review_prerequisite" if i == 0 else f"review_prerequisite_{i}",
                    "label": f"先补前置：{prereq}",
                    "graph_target": prereq,
                    "graph_relation": "prerequisite",
                }
            )

    options.append(
        {
            "value": "continue_current",
            "label": f"继续当前：{current_topic}",
            "graph_target": current_topic,
            "graph_relation": "current",
        }
    )
    if neighbors:
        # 展示最多2个相关节点
        for i, neighbor in enumerate(neighbors[:2]):
            options.append(
                {
                    "value": "branch_related" if i == 0 else f"branch_related_{i}",
                    "label": f"转到相关：{neighbor}",
                    "graph_target": neighbor,
                    "graph_relation": "neighbor",
                }
            )

    # 练习选项：如果有learning_objectives，用其来丰富描述
    practice_label = f"围绕{current_topic}来一道题"
    if learning_objectives:
        obj_text = learning_objectives[0] if isinstance(learning_objectives[0], str) else str(learning_objectives[0])
        if len(obj_text) <= 20:
            practice_label = f"练一道：{obj_text}"
    options.append(
        {
            "value": "practice_now",
            "label": practice_label,
            "graph_target": current_topic,
            "graph_relation": "practice",
        }
    )
    options.append(
        {
            "value": "summarize_now",
            "label": "先收束当前点",
            "graph_target": current_topic,
            "graph_relation": "summary",
        }
    )
    return options, recommended


def _build_dynamic_next_step_options(state: AgentState) -> tuple[list[dict], str]:
    graph_options, graph_recommended = _graph_options(state)
    if graph_options:
        return graph_options, graph_recommended

    background = _normalize_text(state.get("topic_background", ""))
    current_goal = _normalize_text(state.get("current_user_goal", ""))
    turn_goal = _normalize_text(state.get("turn_goal", ""))
    has_recent_practice = bool(_normalize_text(state.get("tester_question", "")))
    has_recent_coach = bool(_normalize_text(state.get("coach_content", "")))
    goal_text = turn_goal or current_goal

    options = [dict(item) for item in NEXT_STEP_OPTIONS]
    recommended = "continue_deeper"

    if "零基础" in background:
        options = [
            {"value": "example_first", "label": "先换个直观例子"},
            {"value": "continue_deeper", "label": "顺着这个点继续讲"},
            {"value": "summarize_now", "label": "先把框架收一下"},
            {"value": "practice_now", "label": "来一道轻一点的题"},
        ]
        recommended = "example_first"
    elif has_recent_practice or has_recent_coach:
        options = [
            {"value": "example_first", "label": "换个讲法再看一遍"},
            {"value": "summarize_now", "label": "先收住这一步"},
            {"value": "practice_now", "label": "马上再试一题"},
            {"value": "continue_deeper", "label": "顺着这个卡点继续讲"},
        ]
        recommended = "example_first"
    elif any(token in goal_text for token in ("有哪些", "从哪开始", "框架", "整体", "重点")):
        options = [
            {"value": "summarize_now", "label": "先把整体地图列出来"},
            {"value": "example_first", "label": "先用例子带入"},
            {"value": "continue_deeper", "label": "挑一个点往下讲"},
            {"value": "practice_now", "label": "直接来一道题"},
        ]
        recommended = "summarize_now"

    return options, recommended


def _build_next_step_prompt(state: AgentState, options: list[dict], recommended: str) -> tuple[str, str]:
    has_recent_practice = bool(_normalize_text(state.get("tester_question", "")))
    has_recent_coach = bool(_normalize_text(state.get("coach_content", "")))
    background = _normalize_text(state.get("topic_background", ""))
    topic = _normalize_text(state.get("current_topic", ""))
    turn_goal = _normalize_text(state.get("turn_goal", ""))
    target_text = turn_goal or _normalize_text(state.get("current_user_goal", "")) or topic
    recommended_label = next((item["label"] for item in options if item["value"] == recommended), options[0]["label"])
    graph_anchor = _normalize_text(state.get("graph_anchor_title", ""))
    graph_prerequisites = [_normalize_text(item) for item in (state.get("graph_prerequisites") or []) if _normalize_text(item)]
    graph_neighbors = [_normalize_text(item) for item in (state.get("graph_neighbors") or []) if _normalize_text(item)]

    if recommended == "branch_related":
        transition_line = f"{graph_anchor or target_text or topic}这一步基本立住了，顺着相关节点往前推更自然。"
    elif recommended == "review_prerequisite":
        transition_line = "先把前置垫稳，不然后面的判断会一直打滑。"
    elif recommended == "practice_now":
        transition_line = "这块先别再堆解释了，拿一个具体情境试一下更快。"
    elif recommended == "summarize_now":
        transition_line = "先把主线收紧，再往下走会更稳。"
    else:
        transition_line = "这一步先不断线，顺着当前概念继续推进。"

    if graph_anchor:
        relation_bits = []
        if graph_prerequisites:
            relation_bits.append(f"前置是【{graph_prerequisites[0]}】")
        if graph_neighbors:
            relation_bits.append(f"相关点是【{graph_neighbors[0]}】")
        start_message = transition_line
        prompt = f"当前节点是【{graph_anchor}】。{'，'.join(relation_bits) if relation_bits else ''}我建议先走“{recommended_label}”。"
        return start_message, prompt

    if has_recent_practice or has_recent_coach:
        start_message = transition_line
        prompt = (
            f"围绕【{target_text or topic}】这个点，我建议你先走“{recommended_label}”。"
            "如果你已经想直接再试题，也可以自己选。"
        )
        return start_message, prompt

    if "零基础" in background:
        start_message = transition_line
        prompt = (
            f"围绕【{target_text or topic}】这个点，我建议你先走“{recommended_label}”。"
            "如果你更想直接练一题，也可以自己改。"
        )
        return start_message, prompt

    start_message = transition_line
    prompt = (
        f"围绕【{target_text or topic}】这个点，我更推荐先走“{recommended_label}”。"
        "当然你也可以按你现在的状态自己改。"
    )
    return start_message, prompt


def _execute_next_step_choice(
    state: AgentState,
    normalized_choice: str,
    choice: str,
    options: list,
    topic: str,
    current_goal: str,
    graph_anchor: str,
    event_sink: EventSink,
) -> dict:
    """执行已确定的下一步选择，返回状态更新字典。"""
    option_map = {
        str(item.get("value") or ""): item
        for item in options
        if str(item.get("value") or "").strip()
    }
    chosen_option = option_map.get(normalized_choice, {})
    graph_target = str(chosen_option.get("graph_target") or graph_anchor or topic).strip()

    if normalized_choice == "practice_now":
        event_sink.emit(
            make_event(
                "node.complete",
                "next_step_selector",
                message="理论先收住，我切一个具体情境给你落地试一下。",
            )
        )
        return {
            "next_step_choice": normalized_choice,
            "teaching_strategy": "explain",
            "current_topic": graph_target or topic,
            "current_user_goal": f"围绕{graph_target or topic}做一道练习",
            "turn_goal": graph_target or current_goal or topic,
            "topic_focus": graph_target or topic,
            "flow_status": "normal",
            "learning_phase": "node_quiz_batch",
            "learning_resume_target": "tester",
            "learning_resume_reason": "node_practice_selected",
            "current_node_name": graph_target or graph_anchor or topic,
            "current_node_status": "quizzing",
            "pending_interaction_kind": "",
            "pending_interaction_prompt": "",
            "pending_interaction_options": [],
            "pending_interaction_recommended": "",
            "pending_interaction_answer": "",
        }

    if normalized_choice == "review_prerequisite" or normalized_choice.startswith("review_prerequisite_"):
        strategy = "explain"
        message = f"先回到前置节点【{graph_target}】，把这块地基补稳，再回来会顺很多。"
        next_topic = graph_target or topic
        next_goal = f"先补前置：{next_topic}，再回来理解{graph_anchor or topic}"
        choice_value = "review_prerequisite"
    elif normalized_choice == "branch_related" or normalized_choice.startswith("branch_related_"):
        strategy = "socratic"
        message = f"{graph_anchor or topic}这一步基本立住了，我转到相关节点【{graph_target}】继续往前推。"
        next_topic = graph_target or topic
        next_goal = f"沿着相关节点{next_topic}继续扩展，并和{graph_anchor or topic}建立联系"
        choice_value = "branch_related"
    elif normalized_choice == "continue_current":
        strategy = "stepbystep"
        message = f"就围绕【{graph_target or topic}】继续往下讲，这次把判断依据再压实一层。"
        next_topic = graph_target or topic
        next_goal = current_goal or next_topic
        choice_value = "continue_current"
    elif normalized_choice == "example_first":
        strategy = "analogy"
        message = "我换一个更直观的例子，把这一步重新搭起来。"
        next_topic = topic
        next_goal = current_goal or topic
        choice_value = "example_first"
    elif normalized_choice == "summarize_now":
        strategy = "summary"
        message = "我先把主线压成一个短总结，让你先抓住该记的判断骨架。"
        next_topic = topic
        next_goal = current_goal or topic
        choice_value = "summarize_now"
    else:
        normalized_choice = "continue_deeper"
        strategy = "stepbystep"
        message = "我顺着刚才那一步继续展开，但会把边界和判断条件讲得更清楚。"
        next_topic = topic
        next_goal = current_goal or topic
        choice_value = "continue_deeper"

    event_sink.emit(
        make_event(
            "node.complete",
            "next_step_selector",
            message=message,
        )
    )
    return {
        "next_step_choice": choice_value,
        "teaching_strategy": strategy,
        "current_topic": next_topic,
        "current_user_goal": next_goal,
        "turn_goal": next_topic if choice_value in {"review_prerequisite", "branch_related"} else (state.get("turn_goal") or next_goal),
        "topic_focus": next_topic if choice_value in {"review_prerequisite", "branch_related"} else state.get("topic_focus", ""),
        "flow_status": "normal",
        "learning_phase": "node_teaching",
        "learning_resume_target": "tutor",
        "learning_resume_reason": f"next_step:{choice_value}",
        "current_node_name": next_topic or graph_anchor or topic,
        "current_node_status": "teaching",
        "next_node_candidate_name": graph_target if choice_value in {"review_prerequisite", "branch_related"} else "",
        "pending_interaction_kind": "",
        "pending_interaction_prompt": "",
        "pending_interaction_options": [],
        "pending_interaction_recommended": "",
        "pending_interaction_answer": "",
        "message_history": list(state.get("message_history", []))
        + [{"role": "user", "kind": "next_step_choice", "content": choice or choice_value}],
    }


def _llm_select_next_step(llm, state: AgentState, options: list[dict], rule_recommended: str) -> str:
    """当规则推荐信心不足时，用轻量 LLM 调用做二次裁决。"""
    if llm is None:
        return rule_recommended
    topic = _normalize_text(state.get("current_topic", ""))
    kg = state.get("user_knowledge_graph") or {}
    recent_history = (state.get("message_history") or [])[-4:]

    option_lines = "\n".join(
        f'- {opt["value"]}: {opt["label"]}' for opt in options
    )
    history_lines = "\n".join(
        f'[{m.get("role", "?")}] {str(m.get("content", ""))[:120]}'
        for m in recent_history
    )
    prompt = (
        f"当前学生在学【{topic}】。\n"
        f"最近对话:\n{history_lines}\n\n"
        f"可选下一步:\n{option_lines}\n\n"
        f"规则推荐: {rule_recommended}\n\n"
        f"请根据学生的实际情况，返回一个最适合的 value（仅返回 value 字符串，不要解释）。"
    )
    try:
        from langchain_core.messages import HumanMessage
        resp = llm.invoke([HumanMessage(content=prompt)])
        raw = str(resp.content if hasattr(resp, 'content') else resp).strip()
        valid_values = {str(opt["value"]) for opt in options}
        # 尝试直接匹配
        if raw in valid_values:
            return raw
        # 尝试在返回文本中寻找匹配
        for v in valid_values:
            if v in raw:
                return v
    except Exception as e:
        logger.warning("LLM next-step fallback failed: %s", e)
    return rule_recommended


def _should_use_llm_fallback(state: AgentState, options: list[dict], recommended: str) -> bool:
    """判断是否需要 LLM 辅助决策——当多个选项竞争激烈时。"""
    # 简单启发式：如果有 >=3 个选项且用户最近轮次有明显意图表达
    recent = (state.get("message_history") or [])[-2:]
    for m in recent:
        content = str(m.get("content") or "").strip()
        if m.get("role") == "user" and len(content) > 20:
            return True
    return False


def build_next_step_node(event_sink: EventSink, answer_provider: AnswerProvider, tutor_llm=None, knowledge_provider=None):
    def node(state: AgentState) -> dict:
        topic = str(state.get("current_topic", "") or "").strip()
        current_goal = str(state.get("current_user_goal", "") or topic).strip()
        graph_anchor = str(state.get("graph_anchor_title", "") or topic).strip()

        # ── 恢复路径：用户通过按钮显式回传了选择 ──
        awaiting_selector = state.get("flow_status") == "awaiting_next_step_selector"
        if awaiting_selector:
            options = list(state.get("pending_interaction_options") or [])
            recommended = str(state.get("pending_interaction_recommended", "") or "").strip()
            prompt = str(state.get("pending_interaction_prompt", "") or "").strip()

            choice = str(state.get("pending_interaction_answer", "") or "").strip()
            if not choice:
                choice = answer_provider.get_answer(
                    prompt,
                    state={
                        "interaction_kind": "next_step_selector",
                        "options": options,
                        "recommended": recommended,
                        "current_topic": topic,
                        "current_user_goal": current_goal,
                    },
                ).strip()

            if _looks_like_question(choice) and _normalize_choice(choice) not in {item["value"] for item in options}:
                event_sink.emit(
                    make_event(
                        "node.complete",
                        "next_step_selector",
                        message="你这一步更像是在追问，我先接住这个卡点。",
                    )
                )
                history = list(state.get("conversation_history", []))
                history.append({"role": "user", "kind": "interruption_user", "content": choice})
                message_history = list(state.get("message_history", []))
                message_history.append({"role": "user", "kind": "interruption_user", "content": choice})
                return {
                    "interrupt_query": choice,
                    "resume_tester": False,
                    "next_step_choice": "",
                    "flow_status": "normal",
                    "learning_phase": "node_temp_qna",
                    "learning_resume_target": "interruption_tutor",
                    "learning_resume_reason": "question_from_next_step_selector",
                    "pending_interaction_kind": "",
                    "pending_interaction_prompt": "",
                    "pending_interaction_options": [],
                    "pending_interaction_recommended": "",
                    "pending_interaction_answer": "",
                    "conversation_history": history,
                    "message_history": message_history,
                }

            normalized_choice = _normalize_choice(choice) or recommended
            return _execute_next_step_choice(
                state, normalized_choice, choice, options, topic, current_goal, graph_anchor, event_sink
            )

        # ── 自动推进路径：AI 自主决策，无需用户点按钮 ──
        options, recommended = _build_dynamic_next_step_options(state)

        # ── 盲区检测：在 next_step 决策点插入图谱盲区推荐 ──
        _course_nodes = getattr(knowledge_provider, "course_graph_nodes", None) or {}
        if _course_nodes and graph_anchor:
            user_kg = state.get("user_knowledge_graph") or {}
            gqs = GraphQueryService(_course_nodes)
            blind_spots = gqs.detect_blind_spots(
                user_kg, current_node=graph_anchor, top_k=2
            )
            if blind_spots:
                hint = gqs.format_blind_spots_hint(blind_spots)
                if hint:
                    event_sink.emit(
                        make_event(
                            "graph.blind_spot",
                            "next_step_selector",
                            message=hint,
                            data={"blind_spots": blind_spots},
                        )
                    )

        _, announcement = _build_next_step_prompt(state, options, recommended)

        # 广播当前决策，但不等待用户输入
        event_sink.emit(
            make_event(
                "node.start",
                "next_step_selector",
                message=announcement,
                data={
                    "topic": topic,
                    "recommended": recommended,
                    "auto_advance": True,
                    "options": options,
                },
            )
        )

        # ── LLM 辅助裁决（规则信心不足时）──
        normalized_choice = recommended
        if _should_use_llm_fallback(state, options, recommended) and tutor_llm is not None:
            normalized_choice = _llm_select_next_step(tutor_llm, state, options, recommended)

        return _execute_next_step_choice(
            state, normalized_choice, "", options, topic, current_goal, graph_anchor, event_sink
        )

    return node

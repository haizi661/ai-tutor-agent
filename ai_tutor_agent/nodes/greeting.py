import json
import re

from langchain_core.messages import HumanMessage, SystemMessage

from ..core.events import make_event
from ..core.ports import EventSink, AnswerProvider
from ..core.state import AgentState
from ..core.text import content_to_text


AMBIGUOUS_INPUTS = {
    "",
    "hi",
    "hello",
    "你好",
    "您好",
    "嗨",
    "哈喽",
    "在吗",
    "有人吗",
    "额",
    "呃",
    "嗯",
    "em",
    "emm",
    "emmm",
    "?",
    "？",
}

MAX_TOPIC_DETAIL_ROUNDS = 4


def _looks_ambiguous(text: str) -> bool:
    cleaned = text.strip().lower()
    if cleaned in AMBIGUOUS_INPUTS:
        return True
    if len(cleaned) <= 2 and not re.search(r"[a-zA-Z0-9\u4e00-\u9fff]{3,}", cleaned):
        return True
    if cleaned in {"不知道", "随便", "没想好", "先聊聊", "先看看"}:
        return True
    return False


def _looks_exploratory_request(text: str) -> bool:
    cleaned = _normalize_text(text)
    if not cleaned:
        return False
    patterns = (
        "有哪些",
        "有什么",
        "哪些核心",
        "核心概念",
        "从哪开始",
        "先学什么",
        "先讲什么",
        "怎么开始",
        "怎么入门",
        "你推荐",
        "给我推荐",
        "有哪些重点",
    )
    return any(pattern in cleaned for pattern in patterns)


def _looks_like_actionable_question(text: str) -> bool:
    cleaned = _normalize_text(text)
    if not cleaned:
        return False
    if "？" in cleaned or "?" in cleaned:
        return True
    patterns = (
        "为什么",
        "怎么",
        "如何",
        "区别",
        "联系",
        "什么原理",
        "工作原理",
        "推导",
        "证明",
        "怎么看",
        "怎么画",
        "怎么求",
        "怎么判断",
        "卡在",
        "不会",
        "做题",
        "作业",
        "考试",
        "重点",
        "难点",
    )
    return any(pattern in cleaned for pattern in patterns)


def _infer_goal_from_turns(topic: str, goal: str, focus: str, turns: list[str]) -> str:
    if _normalize_text(goal):
        return _normalize_text(goal)
    if _normalize_text(focus):
        return _normalize_text(focus)
    for turn in reversed(turns):
        normalized = _normalize_text(turn)
        if not normalized:
            continue
        if _looks_exploratory_request(normalized) or _looks_like_actionable_question(normalized):
            return normalized
    return ""


def _has_minimum_intake_context(topic: str, goal: str, background: str, focus: str, turns: list[str]) -> bool:
    normalized_topic = _normalize_text(topic)
    normalized_goal = _normalize_text(goal)
    normalized_background = _normalize_text(background)
    normalized_focus = _normalize_text(focus)
    if not normalized_topic:
        return False
    if normalized_focus or normalized_goal or normalized_background:
        return True
    return any(
        _looks_exploratory_request(turn) or _looks_like_actionable_question(turn)
        for turn in turns
        if _normalize_text(turn)
    )


def _should_stop_topic_intake(
    *,
    topic: str,
    goal: str,
    focus: str,
    background: str,
    turns: list[str],
    clarify_rounds: int,
    follow_up_mode: str = "none",
) -> bool:
    if clarify_rounds >= MAX_TOPIC_DETAIL_ROUNDS:
        return True
    if not _has_minimum_intake_context(topic, goal, background, focus, turns):
        return False
    latest_turn = _normalize_text(turns[-1] if turns else "")
    if (
        _normalize_text(follow_up_mode).lower() == "suggest_options"
        and not _normalize_text(goal)
        and not _normalize_text(focus)
        and not (_looks_exploratory_request(latest_turn) or _looks_like_actionable_question(latest_turn))
    ):
        return False
    if _looks_exploratory_request(latest_turn) or _looks_like_actionable_question(latest_turn):
        return True
    return bool(_normalize_text(background) or _normalize_text(goal) or _normalize_text(focus))


def _sanitize_options(options) -> list[str]:
    normalized: list[str] = []
    for option in options or []:
        cleaned = _normalize_text(option)
        if not cleaned or cleaned in normalized:
            continue
        normalized.append(cleaned)
        if len(normalized) >= 4:
            break
    return normalized


def _default_starter_options(topic: str) -> list[str]:
    normalized = _normalize_text(topic)
    if "控制" in normalized:
        return [
            "先搭传递函数和框图这条主线",
            "先搞懂稳定性到底在看什么",
            "先看一阶/二阶系统响应的直觉",
        ]
    return [
        "先搭一个整体框架",
        "先抓最核心的定义",
        "先用一个例子入门",
    ]


def _build_option_prompt(topic: str, options: list[str], assistant_reply: str) -> str:
    intro = _normalize_text(assistant_reply) or "先别急着自己组织表述，你从这几个入口里挑一个更快。"
    option_lines = "\n".join(f"- {option}" for option in options)
    return f"{intro}\n{option_lines}\n你先挑一个最顺手的入口，或者直接说你现在最困惑的地方。"


def _clean_json_response(raw_text: str) -> dict:
    cleaned = str(raw_text or "").strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:].split("```")[0].strip()
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:].split("```")[0].strip()
    if cleaned.startswith("{") and cleaned.endswith("}"):
        return json.loads(cleaned)
    raise ValueError("response is not valid json")


def _collect_llm_json(llm, messages) -> dict:
    full_response = ""
    for chunk in llm.stream(messages):
        full_response += content_to_text(chunk.content)
    return _clean_json_response(full_response)


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _topic_transcript(turns: list[str]) -> str:
    return "\n".join(
        f"用户第{index + 1}句：{_normalize_text(turn)}"
        for index, turn in enumerate(turns)
        if _normalize_text(turn)
    )


def _fallback_detail_summary(topic: str, goal: str, background: str) -> str:
    topic = _normalize_text(topic)
    goal = _normalize_text(goal)
    background = _normalize_text(background)
    if goal and background:
        return f"这次先围绕【{topic or goal}】解决【{goal}】，当前背景是：{background}。"
    if goal:
        return f"这次先围绕【{topic or goal}】解决【{goal}】。"
    if background:
        return f"这次先围绕【{topic}】继续，当前背景是：{background}。"
    if topic:
        return f"这次先从【{topic}】开始。"
    return ""


def _merge_user_turns_into_history(existing: list, turns: list[str]) -> list[dict]:
    history = list(existing or [])
    existing_keys = {
        (str(item.get("role", "")), str(item.get("kind", "")), _normalize_text(item.get("content", "")))
        for item in history
    }
    for turn in turns:
        normalized = _normalize_text(turn)
        if not normalized:
            continue
        key = ("user", "topic_input", normalized)
        if key in existing_keys:
            continue
        history.append({"role": "user", "kind": "topic_input", "content": normalized})
        existing_keys.add(key)
    return history


def _build_topic_analysis(llm, turns: list[str], *, clarify_round: int) -> dict:
    system_msg = SystemMessage(
        content=(
            "你是一位伴学导师的开场规划助手，目标是在不拖沓的前提下，把学习方向收准。"
            "你必须输出 JSON，不要输出其他内容。JSON schema:\n"
            "{\n"
            '  "status": "confirmed" | "clarify",\n'
            '  "topic": "课程/知识点核心主题",\n'
            '  "goal": "这次最想先解决的问题或子目标，没有则空字符串",\n'
            '  "focus": "更细的卡点/章节/题型，没有则空字符串",\n'
            '  "background": "当前背景，如零基础/考前复习/作业卡住/想快速入门，没有则空字符串",\n'
            '  "detail_summary": "一句话概括当前已知的学习目标和背景",\n'
            '  "needs_follow_up": true,\n'
            '  "follow_up_mode": "ask_user" | "suggest_options" | "none",\n'
            '  "suggested_options": ["如果适合给用户几个起步切口，就给 2 到 4 个具体选项"],\n'
            '  "assistant_reply": "如果还需要追问，只问一个最关键的问题；否则空字符串"\n'
            "}\n\n"
            "规则：\n"
            "1. 只要能确认大主题，就用 confirmed，不要为了追求完美一直 clarify。\n"
            "2. 只有在缺少当前最关键的起点信息时才 needs_follow_up=true。优先补：现在想先解决哪一块、目前处于什么状态。\n"
            "3. 如果用户明显是在问“有哪些重点/从哪开始/你推荐哪个”，不要再问宽泛问题，改用 suggest_options 给 2 到 3 个贴着主题的起步点。\n"
            "4. 如果用户已经给出具体知识点、卡点、题型或场景，就不要再追问背景。\n"
            "5. 如果用户直接丢来一个知识问题，可以把该问题收成 goal 或 focus，不要把它误判成闲聊。\n"
            "6. 一次只问一个问题，问题必须短、具体，不能出现“你的学习目标是什么”这种空泛问法。\n"
            "7. 不要追问教学模式、流程偏好或工具偏好，这些不是开场必须信息。\n"
            f"8. 当前已经追问过 {clarify_round} 轮；当轮次达到 {MAX_TOPIC_DETAIL_ROUNDS} 时，禁止继续追问，直接综合输出。\n"
            "9. 对零基础用户，优先给“从哪块先入门”的选项，不要让他先自己命名概念。\n"
            "10. assistant_reply 不要寒暄，不要超过 28 个字。"
        )
    )
    human_msg = HumanMessage(content=f"当前对话记录：\n{_topic_transcript(turns)}")
    try:
        return _collect_llm_json(llm, [system_msg, human_msg])
    except Exception:
        latest = _normalize_text(turns[-1] if turns else "")
        return {
            "status": "confirmed" if latest else "clarify",
            "topic": latest,
            "goal": latest,
            "focus": "",
            "background": "",
            "detail_summary": latest,
            "needs_follow_up": False,
            "follow_up_mode": "none",
            "suggested_options": [],
            "assistant_reply": "",
        }


# ---------------------------------------------------------------------------
# Greeter Node - Figure out what the user wants to learn
# ---------------------------------------------------------------------------
def build_greeting_node(llm, event_sink: EventSink, answer_provider: AnswerProvider):
    def node(state: AgentState) -> dict:
        user_input = state.get("current_topic", "").strip()
        
        event_sink.emit(
            make_event(
                "node.start",
                "greeter",
                message="我先听听你这次到底想学什么，再帮你把主题收准。",
            )
        )

        turns: list[str] = []
        clarify_rounds = 0

        if _normalize_text(user_input):
            turns.append(user_input)

        if _looks_ambiguous(user_input):
            clarified = answer_provider.get_answer(
                prompt="先把方向收一下：你这次最想先学哪一块？是基础入门、补某个具体知识点，还是解决一道题？",
                state={
                    **state,
                    "interaction_kind": "topic_detail_prompt",
                    "clarify_round": 1,
                    "prompt_kind": "topic_anchor",
                },
            )
            clarified = _normalize_text(clarified)
            if clarified:
                turns.append(clarified)
            clarify_rounds += 1

        analysis = {}
        starter_options: list[str] = []
        while True:
            analysis = _build_topic_analysis(llm, turns, clarify_round=clarify_rounds)
            topic = _normalize_text(analysis.get("topic"))
            goal = _normalize_text(analysis.get("goal"))
            focus = _normalize_text(analysis.get("focus"))
            background = _normalize_text(analysis.get("background"))
            detail_summary = _normalize_text(analysis.get("detail_summary"))
            needs_follow_up = bool(analysis.get("needs_follow_up"))
            follow_up_mode = _normalize_text(analysis.get("follow_up_mode")).lower() or "none"
            assistant_reply = _normalize_text(analysis.get("assistant_reply"))
            starter_options = _sanitize_options(analysis.get("suggested_options"))
            effective_goal = _infer_goal_from_turns(topic, goal, focus, turns)

            if _should_stop_topic_intake(
                topic=topic,
                goal=effective_goal,
                focus=focus,
                background=background,
                turns=turns,
                clarify_rounds=clarify_rounds,
                follow_up_mode=follow_up_mode,
            ):
                goal = effective_goal
                break

            if (
                needs_follow_up
                and clarify_rounds < MAX_TOPIC_DETAIL_ROUNDS
                and (assistant_reply or topic or goal)
            ):
                wants_options = follow_up_mode == "suggest_options" or _looks_exploratory_request(turns[-1] if turns else "")
                if wants_options:
                    starter_options = starter_options or _default_starter_options(topic or goal)
                    follow_up_prompt = _build_option_prompt(topic or goal, starter_options, assistant_reply)
                    prompt_kind = "topic_options"
                else:
                    follow_up_prompt = (
                        assistant_reply
                        or f"主题先收成【{topic or goal or '这块内容'}】。这次你更想先解决哪一部分？"
                    )
                    prompt_kind = "topic_refine"
                follow_up_answer = answer_provider.get_answer(
                    prompt=follow_up_prompt,
                    state={
                        **state,
                        "interaction_kind": "topic_detail_prompt",
                        "clarify_round": clarify_rounds + 1,
                        "prompt_kind": prompt_kind,
                        "topic_hint": topic,
                        "starter_options": starter_options,
                    },
                )
                follow_up_answer = _normalize_text(follow_up_answer)
                if follow_up_answer:
                    turns.append(follow_up_answer)
                clarify_rounds += 1
                continue
            break

        topic = _normalize_text(analysis.get("topic")) or _normalize_text(turns[-1] if turns else "")
        goal = _infer_goal_from_turns(
            topic,
            _normalize_text(analysis.get("goal")),
            _normalize_text(analysis.get("focus")),
            turns,
        )
        focus = _normalize_text(analysis.get("focus"))
        background = _normalize_text(analysis.get("background"))
        detail_summary = _normalize_text(analysis.get("detail_summary")) or _fallback_detail_summary(
            topic,
            focus or goal,
            background,
        )
        starter_options = starter_options or _sanitize_options(analysis.get("suggested_options"))
        current_goal = goal or focus or topic

        complete_message = f"已收准候选主题：{topic}" if topic else "我先把这次主题收成一句更清楚的话。"
        if focus:
            complete_message += f"；当前先抓：{focus}"
        event_sink.emit(make_event("node.complete", "greeter", message=complete_message))

        return {
            "proposed_topic": topic,
            "current_user_goal": current_goal,
            "session_goal": current_goal,
            "turn_goal": focus or current_goal,
            "topic_focus": focus or current_goal,
            "topic_background": background,
            "topic_detail_summary": detail_summary,
            "topic_starter_options": starter_options,
            "topic_clarify_rounds": clarify_rounds,
            "message_history": _merge_user_turns_into_history(state.get("message_history", []), turns),
            "flow_status": "topic_confirmation_pending",
        }

    return node

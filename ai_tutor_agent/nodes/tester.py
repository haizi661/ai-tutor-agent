from langchain_core.messages import HumanMessage, SystemMessage

from ..core.events import make_event
from ..core.ports import AnswerProvider, EventSink
from ..core.state import AgentState
from ..core.text import content_to_text


# ─────────────────────────────────────────────────────
# 题目规格：根据难度和失败次数动态生成
# 失败2次后，题目难度自动降一级，避免学生陷入挫败感
# ─────────────────────────────────────────────────────
_QUESTION_SPECS = {
    1: {
        "type": "基础识别题",
        "instruction": (
            "出一道概念识别题：给出一个简单场景，让学生判断对错或在空白处填入核心概念名称。"
            "题目要清晰，有唯一正确答案，不涉及计算。"
        ),
        "hint": "答案的关键词一定在刚才的讲解中出现过，可以回去找一找。",
    },
    2: {
        "type": "基础应用题",
        "instruction": (
            "出一道基础应用题：给出一个具体情境，让学生选择或说明如何应用刚学的概念。不需要计算。"
        ),
        "hint": "先回忆讲解中的实际应用场景，对比题目情境，找出最关键的对应点。",
    },
    3: {
        "type": "分析判断题",
        "instruction": (
            "出一道分析题：给出一个包含典型错误或争议的场景/代码/设计，"
            "让学生找出问题所在并用自己的话解释原因。"
        ),
        "hint": "把场景拆解成步骤，逐步检查每一步是否符合核心原理，找到第一个出错的环节。",
    },
    4: {
        "type": "综合推理题",
        "instruction": (
            "出一道综合题：需要学生组合多个概念进行推理或定量计算，并清晰说明解题步骤和理由。"
        ),
        "hint": "先梳理题中涉及哪几个知识点，分别回忆对应公式/原理，再依次组合推导。",
    },
    5: {
        "type": "设计评估题",
        "instruction": (
            "出一道高阶思考题：让学生评估一个方案的优劣，或者设计一个解决方案并论证选择理由，"
            "鼓励学生展示批判性思考。"
        ),
        "hint": "从效率、准确性、边界条件、实际约束等多个维度分析，聚焦最能体现理解深度的角度。",
    },
}


def _effective_level(difficulty_level: int, attempt_count: int) -> int:
    """失败次数每满2次，题目难度降一级，最低为1级。"""
    drop = attempt_count // 2
    return max(1, difficulty_level - drop)


def build_tester_node(
    tester_llm,
    event_sink: EventSink,
    answer_provider: AnswerProvider,
):
    def tester_node(state: AgentState):
        topic = state["current_topic"]
        difficulty_level = state.get("difficulty_level", 3)
        attempt_count = state.get("attempt_count", 0)
        coach_content = state.get("coach_content", "").strip()
        eff_level = _effective_level(difficulty_level, attempt_count)
        spec = _QUESTION_SPECS[eff_level]

        event_sink.emit(
            make_event(
                "node.start",
                "tester",
                message=f"正在为【{topic}】出题（题目难度 Lv.{eff_level}）...",
                data={"topic": topic, "difficulty": eff_level},
            )
        )

        system_msg = SystemMessage(
            content=f"""你是一位专业的出题老师。根据教授的讲解内容，出一道且仅一道考核题。

题目类型：{spec["type"]}
出题要求：{spec["instruction"]}

输出格式（严格遵守）：
1. 直接输出题目正文，不加任何前言（禁止说"好的"、"当然"等）
2. 题目正文结束后空一行
3. 最后一行固定输出：「💡 思路提示：{spec["hint"]}」

附加规则：
- 题目必须直接考察刚才讲解的核心知识点，不得超纲
- 场景要真实、具体，避免过于抽象
- 题目字数控制在 80~150 字之间"""
        )
        extra = ""
        if coach_content:
            extra = f"\n\n这是补救教练刚给出的纠偏卡片（请优先围绕其误区点出题）：\n{coach_content}"
        human_msg = HumanMessage(
            content=f"这是教授刚才针对【{topic}】的讲解内容：\n\n{state['tutor_content']}{extra}"
        )

        full_question = ""
        for chunk in tester_llm.stream([system_msg, human_msg]):
            chunk_text = content_to_text(chunk.content)
            full_question += chunk_text
            event_sink.emit(
                make_event(
                    "node.stream",
                    "tester",
                    data={"text": chunk_text},
                )
            )

        event_sink.emit(
            make_event(
                "node.complete",
                "tester",
                message="题目已出好，等待你的解答。",
                data={"question": full_question, "difficulty_level": eff_level},
            )
        )

        user_input = answer_provider.get_answer(
            ">> 请输入你的解答（可以直接作答，无需完美，尽力即可）：",
            state={
                "current_topic": state["current_topic"],
                "tester_question": full_question,
            },
        ).strip()

        event_sink.emit(
            make_event(
                "answer.received",
                "tester",
                message="已收到你的解答，正在评估…",
                data={"answer_length": len(user_input)},
            )
        )

        return {"tester_question": full_question, "user_answer": user_input, "coach_content": ""}

    return tester_node

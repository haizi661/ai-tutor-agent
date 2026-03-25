import json
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage

from ..core.events import make_event
from ..core.ports import EventSink
from ..core.state import AgentState
from ..core.text import content_to_text


class EvaluationResult(BaseModel):
    total_score: int = Field(ge=0, le=100, description="整数 (0-100)，综合总分")
    logic_score: int = Field(ge=0, le=100, description="整数 (0-100)，推演逻辑严密程度")
    concept_score: int = Field(ge=0, le=100, description="整数 (0-100)，专业概念准确程度")
    is_correct_direction: bool = Field(description="学生的思路方向是否基本正确")
    misconceptions: list[str] = Field(default_factory=list, description="学生答案中存在的具体误区列表，每条一句话，没有则为空列表")
    rubric_feedback: list[str] = Field(default_factory=list, description="按评分量表给出的扣分依据与证据，每条形如“维度: 扣分原因（-x）”")
    model_answer: str = Field(description="这道题的完整参考答案，200字以内，清晰准确")
    encouragement: str = Field(description="针对本次作答的一句个性化鼓励或点评，温暖但诚实")
    next_review_points: list[str] = Field(default_factory=list, description="建议学生下一步重点复习的 1~3 个知识点，没有则为空列表")
    needs_hint: bool = Field(description="是否建议先给思路提示再让学生重试")


def _clamp_score(value: object, default: int = 60) -> int:
    try:
        parsed = int(value)
    except Exception:
        parsed = default
    return max(0, min(100, parsed))


def _normalize_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _looks_like_help_request(answer: str) -> bool:
    text = (answer or "").strip().lower()
    if not text:
        return True
    trigger_phrases = [
        "我不会",
        "不会",
        "不懂",
        "没思路",
        "不知道",
        "不会做",
        "看不懂",
        "i don't know",
        "idk",
    ]
    return any(phrase in text for phrase in trigger_phrases)


def _build_system_prompt(attempt_count: int) -> str:
    if attempt_count >= 3:
        tone = "这位学生已经努力了好几轮，请语气格外温暖。哪怕答案偏差较大，也要先肯定努力，再指出具体问题。"
    elif attempt_count >= 1:
        tone = "学生已经历了失败，请在给出准确评分的同时，顾及其信心，肯定进步之处。"
    else:
        tone = "直接、准确地评估即可。对好的地方给予肯定，对错误之处直接指出。"

    return f"""你是一位专业且有温度的阅卷老师。你的任务是全面评估学生的作答，并给出有价值的学习反馈。

{tone}

评分量表（必须按此量表裁决，禁止主观漂移）：
- total_score：综合评分 (0-100)
  * 80-100：核心思路正确，细节表达准确
  * 60-79：方向对，有一些关键细节遗漏或表述不准确
  * 40-59：部分理解正确，但核心概念有明显混淆
  * 0-39：偏离核心概念，需要重新理解
- logic_score：推理链条是否严密
- concept_score：专业术语/概念使用是否准确

扣分规则（rubric_feedback 必须逐条列出）：
- 漏掉一个核心公式/核心判断条件：-10
- 关键推理步骤缺失或跳步严重：-8
- 核心概念混淆（如把 A 说成 B）：每处 -12
- 术语不准确但不影响主结论：每处 -4
- 最终结论错误：-15
- 若答案基本为空或仅写“不会/不懂/不知道”：total_score 不高于 35，needs_hint=true

needs_hint 判定：
- 当 total_score < 45，或学生明确表达“不会/不懂/没思路”时，needs_hint=true
- 否则 needs_hint=false

model_answer 要求：
- 写出这道题的完整、标准参考答案
- 不超过200字，清晰易懂，学生可以直接学习
- 如果有公式，用文字描述，不用 LaTeX

encouragement 要求：
- 一句话，温暖但诚实
- 不要泛泛而谈，要针对本次作答的具体情况"""


def _format_rich_feedback(result: EvaluationResult, attempt_count: int) -> str:
    """生成格式化的完整反馈 Markdown 文本推送给前端。"""
    lines = []

    # 评分仪表盘
    bar_total = "█" * (result.total_score // 10) + "░" * (10 - result.total_score // 10)
    lines.append(f"### 📊 本轮评估结果\n")
    lines.append(f"| 维度 | 得分 | 进度条 |")
    lines.append(f"|:--|:--|:--|")
    lines.append(f"| 综合总分 | **{result.total_score}** | `{bar_total}` |")
    lines.append(f"| 逻辑严密性 | {result.logic_score} | |")
    lines.append(f"| 概念准确性 | {result.concept_score} | |")
    lines.append("")

    # 个性化点评
    lines.append(f"**{result.encouragement}**\n")

    # 思路方向
    direction_icon = "✅" if result.is_correct_direction else "⚠️"
    direction_text = "思路方向基本正确！" if result.is_correct_direction else "解题方向还需要调整。"
    lines.append(f"{direction_icon} {direction_text}\n")

    # 具体误区
    if result.misconceptions:
        lines.append("#### ❌ 需要纠正的具体误区\n")
        for m in result.misconceptions:
            lines.append(f"- {m}")
        lines.append("")

    # 量表依据
    if result.rubric_feedback:
        lines.append("#### 🧭 评分依据（量表）\n")
        for item in result.rubric_feedback:
            lines.append(f"- {item}")
        lines.append("")

    if result.needs_hint:
        lines.append("#### 💡 下一步建议\n")
        lines.append("- 你可以先看一条思路提示，再尝试独立作答一次。")
        lines.append("")

    # 参考答案
    lines.append("#### 📖 参考答案\n")
    lines.append(f"> {result.model_answer}\n")

    # 下一步复习建议
    if result.next_review_points:
        lines.append("#### 🔍 建议接下来重点复习\n")
        for point in result.next_review_points:
            lines.append(f"- {point}")
        lines.append("")

    return "\n".join(lines)


def build_evaluator_node(evaluator_llm, event_sink: EventSink, pass_score: int):
    try:
        structured_llm = evaluator_llm.with_structured_output(EvaluationResult)
    except Exception:
        structured_llm = None

    def evaluator_node(state: AgentState):
        topic = state["current_topic"]
        attempt_count = state.get("attempt_count", 0)
        score_history = state.get("score_history", [])
        user_answer = state.get("user_answer", "")
        needs_hint_from_answer = _looks_like_help_request(user_answer)

        event_sink.emit(
            make_event(
                "node.start",
                "evaluator",
                message="正在评估你的解答，稍等一下…",
                data={"topic": topic, "attempt": attempt_count},
            )
        )

        system_msg = SystemMessage(content=_build_system_prompt(attempt_count))
        human_msg = HumanMessage(
            content=f"""考核主题：{topic}
原始讲解内容（供参考）：
{state.get("tutor_content", "")}

考核题目：
{state["tester_question"]}

学生的作答：
{state["user_answer"]}"""
        )

        result: EvaluationResult | None = None
        if structured_llm:
            try:
                result = structured_llm.invoke([system_msg, human_msg])
            except Exception as e:
                event_sink.emit(
                    make_event("session.warning", "evaluator", message=f"结构化输出失败，降级到 JSON 解析: {e}")
                )

        if result is None:
            result = _fallback_eval(evaluator_llm, system_msg, human_msg, event_sink)

        if needs_hint_from_answer and not result.needs_hint:
            result.needs_hint = True
            result.rubric_feedback = result.rubric_feedback + ["作答内容显示当前无清晰思路，建议先提示后重试（-0）"]

        if needs_hint_from_answer:
            result.total_score = min(result.total_score, 35)
            result.is_correct_direction = False

        # 更新 attempt_count 和 score_history
        new_score_history = score_history + [(result.total_score, result.logic_score, result.concept_score, result.encouragement)]
        new_attempt_count = 0 if result.total_score >= pass_score else attempt_count + 1

        # 生成完整反馈文本并模拟流式推送
        rich_feedback = _format_rich_feedback(result, attempt_count)
        
        # Simulate streaming for better UX
        import time
        chunk_size = 15
        for i in range(0, len(rich_feedback), chunk_size):
            chunk = rich_feedback[i:i+chunk_size]
            event_sink.emit(
                make_event("node.stream", "evaluator", data={"text": chunk})
            )
            time.sleep(0.02)

        event_sink.emit(
            make_event(
                "assessment.result",
                "evaluator",
                data={
                    "total_score": result.total_score,
                    "logic_score": result.logic_score,
                    "concept_score": result.concept_score,
                    "feedback": result.encouragement,
                    "rubric_feedback": result.rubric_feedback,
                    "model_answer": result.model_answer,
                    "misconceptions": result.misconceptions,
                    "next_review_points": result.next_review_points,
                    "is_correct_direction": result.is_correct_direction,
                    "needs_hint": result.needs_hint,
                },
            )
        )

        event_sink.emit(
            make_event(
                "node.complete",
                "evaluator",
                message="评估完成。",
            )
        )

        return {
            "score": result.total_score,
            "logic_score": result.logic_score,
            "concept_score": result.concept_score,
            "feedback": result.encouragement,
            "rubric_feedback": result.rubric_feedback,
            "model_answer": result.model_answer,
            "misconceptions": result.misconceptions,
            "next_review_points": result.next_review_points,
            "is_correct_direction": result.is_correct_direction,
            "needs_hint": result.needs_hint,
            "attempt_count": new_attempt_count,
            "score_history": new_score_history,
        }

    return evaluator_node


def _fallback_eval(llm, system_msg, human_msg, event_sink) -> EvaluationResult:
    """JSON 手动解析降级方案。"""
    prompt = (
        f"{system_msg.content}\n\n"
        "请严格以 JSON 对象格式输出，字段名与以下完全一致：\n"
        "total_score (int), logic_score (int), concept_score (int), "
        "is_correct_direction (bool), misconceptions (list[str]), "
        "rubric_feedback (list[str]), model_answer (str), encouragement (str), "
        "next_review_points (list[str]), needs_hint (bool)\n\n"
        f"待评内容：\n{human_msg.content}"
    )
    response = llm.invoke(prompt)
    raw = content_to_text(response.content).strip()

    # 清理 markdown 代码块
    for prefix in ("```json", "```"):
        if raw.startswith(prefix):
            raw = raw[len(prefix):]
            break
    if raw.endswith("```"):
        raw = raw[:-3]
    raw = raw.strip()

    try:
        data = json.loads(raw)
        total_score = _clamp_score(data.get("total_score", 60))
        logic_score = _clamp_score(data.get("logic_score", 60))
        concept_score = _clamp_score(data.get("concept_score", 60))
        misconceptions = _normalize_list(data.get("misconceptions", []))
        rubric_feedback = _normalize_list(data.get("rubric_feedback", []))
        next_review_points = _normalize_list(data.get("next_review_points", []))[:3]
        raw_needs_hint = data.get("needs_hint", total_score < 45)
        return EvaluationResult(
            total_score=total_score,
            logic_score=logic_score,
            concept_score=concept_score,
            is_correct_direction=bool(data.get("is_correct_direction", True)),
            misconceptions=misconceptions,
            rubric_feedback=rubric_feedback,
            model_answer=str(data.get("model_answer", "参考答案解析暂时无法获取。")),
            encouragement=str(data.get("encouragement", "你已经尽力了，继续加油！")),
            next_review_points=next_review_points,
            needs_hint=bool(raw_needs_hint),
        )
    except Exception:
        event_sink.emit(
            make_event("session.warning", "evaluator", message="JSON 解析失败，使用默认兜底评分")
        )
        return EvaluationResult(
            total_score=60,
            logic_score=60,
            concept_score=60,
            is_correct_direction=True,
            misconceptions=["系统无法解析本次作答，建议重新作答。"],
            rubric_feedback=["系统解析失败，暂无法给出量表依据（-0）"],
            model_answer="系统评估暂时无法获取参考答案，请查阅讲解内容。",
            encouragement="系统解析遇到了问题，但你的认真态度值得肯定！",
            next_review_points=[],
            needs_hint=False,
        )

"""
学前测评节点 —— 无阻塞异步表单方案
==============================================
- AssessmentGenerator: 生成 20 道题 → emit form_ready → 返回并暂停图
- UserProfiler:       读取提交答案 → 规则化生成 6 维雷达数据 + Markdown 报告
"""

import json

from langchain_core.messages import HumanMessage, SystemMessage

from ..core.events import make_event
from ..core.ports import EventSink, RuntimeContext
from ..core.state import AgentState
from ..core.text import content_to_text


ASSESSMENT_DIMENSIONS = [
    "基础概念",
    "规则理解",
    "逻辑推理",
    "场景应用",
    "细节辨析",
    "表达信心",
]

SELF_EVAL_SCORE_MAP = {"A": 25, "B": 50, "C": 75, "D": 100}


# ---------------------------------------------------------------------------
# AssessmentGenerator  —— 生成 20 题，通过 SSE 发给前端，节点即刻返回
# ---------------------------------------------------------------------------

def build_assessment_generator_node(llm, event_sink: EventSink):
    """
    调用 LLM 生成 20 道学前测评题（10 自评 + 10 客观），
    通过 event_sink 以 `assessment.form_ready` 事件将 JSON 推送给前端，
    随后设置 flow_status='awaiting_assessment' 由条件边路由到 END，暂停图。
    """

    def node(state: AgentState) -> dict:
        topic = state["current_topic"]

        # ── 幂等保护：如果题目已存在（浏览器刷新场景），直接重发事件 ──
        existing = state.get("assessment_questions", [])
        if existing:
            event_sink.emit(
                make_event(
                    "assessment.form_ready",
                    "assessment_generator",
                    message="学前测评量表已就绪，请在前端完成作答。",
                    data={"questions": existing},
                )
            )
            return {"flow_status": "awaiting_assessment"}

        event_sink.emit(
            make_event(
                "node.start",
                "assessment_generator",
                message=f"正在为【{topic}】生成学前测评量表…",
                data={"topic": topic},
            )
        )

        system_msg = SystemMessage(
            content="你是一位资深的教育测评专家，擅长设计精准的学习前评估量表。"
        )
        human_msg = HumanMessage(
            content=f"""请针对学习主题【{topic}】，设计一份包含 20 道题目的测评量表。

固定评估维度（每题必须只归属其中一个）：
{", ".join(ASSESSMENT_DIMENSIONS)}

量表结构：
1. 第一部分：用户自我评估（10 题，题号 1-10）
   - type 标记为 "self_eval"
   - 每题必须包含字段 "dimension"
   - 选项为程度递进，例如 A.完全不懂  B.听说过  C.了解基本概念  D.熟练掌握

2. 第二部分：客观基础测试（10 题，题号 11-20）
   - type 标记为 "objective"
   - 每题必须包含字段 "dimension"
   - 均为单项选择题，4 个选项
   - 每题必须包含字段 "correct_answer"，值只能是 "A" / "B" / "C" / "D"

请直接输出合法 JSON，不含 Markdown 代码块标记。Schema:
{{
  "questions": [
    {{
      "id": 1,
      "type": "self_eval",
      "dimension": "基础概念",
      "question": "...",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "correct_answer": ""
    }},
    ...
  ]
}}"""
        )

        # 流式获取 LLM 输出（不推送给前端，仅用于收集完整 JSON）
        raw = ""
        for chunk in llm.stream([system_msg, human_msg]):
            raw += content_to_text(chunk.content)

        # ── 解析 JSON ──
        questions: list = []
        try:
            cleaned = raw.strip()
            for prefix in ("```json", "```"):
                if cleaned.startswith(prefix):
                    cleaned = cleaned[len(prefix):]
                    break
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            parsed = json.loads(cleaned.strip())
            questions = parsed.get("questions", [])
        except Exception as exc:
            event_sink.emit(
                make_event(
                    "session.warning",
                    "assessment_generator",
                    message=f"测评量表 JSON 解析失败: {exc}",
                )
            )

        # ── 通过 SSE 推送表单数据给前端 ──
        event_sink.emit(
            make_event(
                "assessment.form_ready",
                "assessment_generator",
                message="学前测评量表已生成，请在前端完成作答。",
                data={"questions": questions},
            )
        )

        event_sink.emit(
            make_event(
                "node.complete",
                "assessment_generator",
                message="测评量表生成完毕。",
                data={"count": len(questions)},
            )
        )

        # 核心：设置 flow_status 让条件边将图路由到 END（暂停）
        return {
            "assessment_questions": questions,
            "flow_status": "awaiting_assessment",
        }

    return node


# ---------------------------------------------------------------------------
# UserProfiler  —— 收到答案后被唤醒，生成 6 维雷达 + Markdown 报告
# ---------------------------------------------------------------------------

def build_user_profiler_node(llm, runtime: RuntimeContext):
    """
    读取 state 中的 assessment_questions + assessment_answers,
    分两步处理:
      1) 规则打分 → 6 维雷达数据 → emit profile.radar_data
      2) LLM 只负责流式生成 Markdown 画像报告
    """

    def node(state: AgentState) -> dict:
        event_sink = runtime.event_sink
        knowledge_provider = runtime.knowledge_provider
        topic = state["current_topic"]
        questions = state.get("assessment_questions", [])
        answers = state.get("assessment_answers", {})

        event_sink.emit(
            make_event(
                "node.start",
                "user_profiler",
                message="正在分析用户能力画像…",
                data={"topic": topic},
            )
        )

        # ── 序列化 QA 对 ──
        qa_text = ""
        for q in questions:
            qid = str(q["id"])
            ans = answers.get(qid, answers.get(q["id"], "未作答"))
            qa_text += (
                f"Q{qid} [{q['type']}]: {q['question']}\n"
                f"  选项: {q['options']}\n"
                f"  用户答案: {ans}\n\n"
            )

        # ━━━ Step 1: 规则化雷达数据（非流式） ━━━
        radar_data = _generate_radar_data(event_sink, topic, questions, answers)

        # 推送给前端用于绘制 Chart.js 雷达图
        event_sink.emit(
            make_event("profile.radar_data", "user_profiler", data=radar_data)
        )

        # ━━━ Step 2: 检索知识库中的针对性建议依据 ━━━
        weakness_dimensions = [
            item["dimension"]
            for item in radar_data.get("breakdown", [])
            if item.get("objective_score", 0) < 60
        ]
        profile_query = f"{topic} 学习建议 {' '.join(weakness_dimensions)}".strip()
        knowledge_context = knowledge_provider.query(profile_query) if profile_query else ""

        # ━━━ Step 3: 流式 Markdown 画像报告 ━━━
        full_report = _generate_profile_report(
            llm, event_sink, topic, qa_text, radar_data, knowledge_context
        )

        event_sink.emit(
            make_event(
                "node.complete",
                "user_profiler",
                message="用户画像生成完毕。",
            )
        )

        return {
            "assessment_radar": radar_data,
            "assessment_result": full_report,
            "is_assessed": True,
            "flow_status": "normal",
        }

    return node


# ───────────── 内部辅助函数 ─────────────


def _normalize_answer(value: str) -> str:
    cleaned = (value or "").strip().upper()
    return cleaned[:1] if cleaned else ""


def _question_dimension(question: dict, fallback_index: int) -> str:
    dimension = (question.get("dimension") or "").strip()
    if dimension in ASSESSMENT_DIMENSIONS:
        return dimension
    return ASSESSMENT_DIMENSIONS[fallback_index % len(ASSESSMENT_DIMENSIONS)]


def _generate_radar_data(event_sink: EventSink, topic: str, questions: list, answers: dict) -> dict:
    del topic
    aggregates = {
        dimension: {
            "self_total": 0,
            "self_count": 0,
            "objective_total": 0,
            "objective_count": 0,
        }
        for dimension in ASSESSMENT_DIMENSIONS
    }

    for index, question in enumerate(questions):
        dimension = _question_dimension(question, index)
        qid = str(question.get("id"))
        answer = _normalize_answer(answers.get(qid, answers.get(question.get("id"), "")))

        if question.get("type") == "self_eval":
            score = SELF_EVAL_SCORE_MAP.get(answer)
            if score is None:
                continue
            aggregates[dimension]["self_total"] += score
            aggregates[dimension]["self_count"] += 1
            continue

        if question.get("type") == "objective":
            correct_answer = _normalize_answer(question.get("correct_answer", ""))
            if not correct_answer:
                event_sink.emit(
                    make_event(
                        "session.warning",
                        "user_profiler",
                        message=f"题目 {qid} 缺少 correct_answer，已跳过规则评分。",
                    )
                )
                continue
            score = 100 if answer == correct_answer else 0
            aggregates[dimension]["objective_total"] += score
            aggregates[dimension]["objective_count"] += 1

    self_scores = []
    objective_scores = []
    gaps = []
    breakdown = []

    for dimension in ASSESSMENT_DIMENSIONS:
        bucket = aggregates[dimension]
        self_score = (
            round(bucket["self_total"] / bucket["self_count"])
            if bucket["self_count"]
            else 50
        )
        objective_score = (
            round(bucket["objective_total"] / bucket["objective_count"])
            if bucket["objective_count"]
            else 50
        )
        gap = self_score - objective_score
        self_scores.append(self_score)
        objective_scores.append(objective_score)
        gaps.append(gap)
        breakdown.append(
            {
                "dimension": dimension,
                "self_score": self_score,
                "objective_score": objective_score,
                "gap": gap,
                "self_count": bucket["self_count"],
                "objective_count": bucket["objective_count"],
            }
        )

    return {
        "dimensions": ASSESSMENT_DIMENSIONS,
        "self_scores": self_scores,
        "objective_scores": objective_scores,
        "gap_scores": gaps,
        "breakdown": breakdown,
    }


def _generate_profile_report(
    llm,
    event_sink: EventSink,
    topic: str,
    qa_text: str,
    radar_data: dict,
    knowledge_context: str,
) -> str:
    """流式生成 Markdown 能力画像报告。"""
    system_msg = SystemMessage(
        content="你是一位教育心理学专家，擅长撰写清晰深刻的学生能力分析报告。"
    )
    kb_section = ""
    if knowledge_context:
        kb_section = (
            "\n\n知识库参考资料（请优先据此给出可执行建议）：\n"
            f"---\n{knowledge_context}\n---\n"
        )

    human_msg = HumanMessage(
        content=f"""根据以下关于【{topic}】的测评数据和能力评分，生成详细的 Markdown 能力画像报告。

测评数据:
{qa_text}

6 维能力评分:
{json.dumps(radar_data, ensure_ascii=False, indent=2)}
{kb_section}

报告要求:
1. 标题: ## 📊 【{topic}】学前能力画像
2. 列出 6 个维度的自我评估 vs 客观评价对比
3. 重点分析 self_scores 与 objective_scores 的差值（认知偏差）
4. 针对薄弱点给出具体学习建议，优先引用知识库材料中的术语、步骤和案例
5. 字数控制在 500 字左右
6. 评分已经是规则化计算结果，请不要重新改分，只做解释。"""
    )

    full_report = ""
    for chunk in llm.stream([system_msg, human_msg]):
        text = content_to_text(chunk.content)
        full_report += text
        event_sink.emit(
            make_event("node.stream", "user_profiler", data={"text": text})
        )

    return full_report

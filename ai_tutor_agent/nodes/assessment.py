"""
学前测评节点 —— 无阻塞异步表单方案
==============================================
- AssessmentGenerator: 生成 20 道题 → emit form_ready → 返回并暂停图
- UserProfiler:       读取提交答案 → 生成 6 维雷达数据 + Markdown 报告
"""

import json

from langchain_core.messages import HumanMessage, SystemMessage

from ..core.events import make_event
from ..core.ports import EventSink
from ..core.state import AgentState
from ..core.text import content_to_text


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

量表结构：
1. 第一部分：用户自我评估（10 题，题号 1-10）
   - type 标记为 "self_eval"
   - 选项为程度递进，例如 A.完全不懂  B.听说过  C.了解基本概念  D.熟练掌握

2. 第二部分：客观基础测试（10 题，题号 11-20）
   - type 标记为 "objective"
   - 均为单项选择题，4 个选项

请直接输出合法 JSON，不含 Markdown 代码块标记。Schema:
{{
  "questions": [
    {{"id": 1, "type": "self_eval", "question": "...", "options": ["A. ...", "B. ...", "C. ...", "D. ..."]}},
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

def build_user_profiler_node(llm, event_sink: EventSink):
    """
    读取 state 中的 assessment_questions + assessment_answers,
    两步 LLM 调用:
      1) 结构化 JSON → 6 维雷达数据 → emit profile.radar_data
      2) 流式 Markdown → 能力画像报告
    """

    def node(state: AgentState) -> dict:
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

        # ━━━ Step 1: 结构化雷达数据（非流式） ━━━
        radar_data = _generate_radar_data(llm, event_sink, topic, qa_text)

        # 推送给前端用于绘制 Chart.js 雷达图
        event_sink.emit(
            make_event("profile.radar_data", "user_profiler", data=radar_data)
        )

        # ━━━ Step 2: 流式 Markdown 画像报告 ━━━
        full_report = _generate_profile_report(
            llm, event_sink, topic, qa_text, radar_data
        )

        event_sink.emit(
            make_event(
                "node.complete",
                "user_profiler",
                message="用户画像生成完毕。",
            )
        )

        return {
            "assessment_result": full_report,
            "is_assessed": True,
            "flow_status": "normal",
        }

    return node


# ───────────── 内部辅助函数 ─────────────


def _generate_radar_data(
    llm, event_sink: EventSink, topic: str, qa_text: str
) -> dict:
    """调用 LLM 生成结构化 6 维雷达 JSON。"""
    system_msg = SystemMessage(
        content="你是一位教育数据分析师，擅长量化学生能力维度。"
    )
    human_msg = HumanMessage(
        content=f"""根据以下关于【{topic}】的测评数据，划分 6 个核心能力维度并打分（0-100）。
必须分别给出【自我评估得分】和【客观评价得分】。
- 自我评估得分基于 self_eval 类题目的回答。
- 客观评价得分基于 objective 类题目（需要你自行判断正确答案）。

测评数据:
{qa_text}

请直接输出合法 JSON，不含 Markdown 代码块标记。Schema:
{{
  "dimensions": ["维度1", "维度2", "维度3", "维度4", "维度5", "维度6"],
  "self_scores": [80, 70, 60, 50, 40, 30],
  "objective_scores": [75, 65, 55, 45, 35, 25]
}}"""
    )

    raw = content_to_text(llm.invoke([system_msg, human_msg]).content)

    try:
        cleaned = raw.strip()
        for prefix in ("```json", "```"):
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):]
                break
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]
        return json.loads(cleaned.strip())
    except Exception as exc:
        event_sink.emit(
            make_event(
                "session.warning",
                "user_profiler",
                message=f"雷达数据 JSON 解析失败: {exc}",
            )
        )
        return {
            "dimensions": [
                "基础概念",
                "逻辑推理",
                "应用能力",
                "工程素养",
                "创新思维",
                "综合素质",
            ],
            "self_scores": [50, 50, 50, 50, 50, 50],
            "objective_scores": [50, 50, 50, 50, 50, 50],
        }


def _generate_profile_report(
    llm, event_sink: EventSink, topic: str, qa_text: str, radar_data: dict
) -> str:
    """流式生成 Markdown 能力画像报告。"""
    system_msg = SystemMessage(
        content="你是一位教育心理学专家，擅长撰写清晰深刻的学生能力分析报告。"
    )
    human_msg = HumanMessage(
        content=f"""根据以下关于【{topic}】的测评数据和能力评分，生成详细的 Markdown 能力画像报告。

测评数据:
{qa_text}

6 维能力评分:
{json.dumps(radar_data, ensure_ascii=False, indent=2)}

报告要求:
1. 标题: ## 📊 【{topic}】学前能力画像
2. 列出 6 个维度的自我评估 vs 客观评价对比
3. 综合分析自我认知与客观水平的差异
4. 针对薄弱点给出具体学习建议
5. 字数控制在 500 字左右"""
    )

    full_report = ""
    for chunk in llm.stream([system_msg, human_msg]):
        text = content_to_text(chunk.content)
        full_report += text
        event_sink.emit(
            make_event("node.stream", "user_profiler", data={"text": text})
        )

    return full_report

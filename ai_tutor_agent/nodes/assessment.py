"""
学前测评节点 —— 对话式逐题配对方案
======================================================
设计思路
--------
1. AssessmentGenerator：
   - 从知识图谱中选出 10 个核心概念
   - 为每个概念生成 1 道自评题 + 1 道配对客观题
   - 组装成 10 组 pair，存入 assessment_state
   - 发出第 1 道自评题，进入对话式逐题追问

2. AssessmentDialog（状态机）：
   - 收到自评回答 → 发配对客观题
   - 收到客观回答 → 如果差距大，可追问一句 → 发下一组自评
   - 全部 10 组完成 → flow_status = "profiling" → 进入 UserProfiler

3. UserProfiler：
   - 按配对关系计算差距 → gap_type → 教学策略 → 画像报告
"""

import json
import re
from typing import Optional

from langchain_core.messages import HumanMessage, SystemMessage

from ..core.events import make_event
from ..core.ports import EventSink
from ..core.state import AgentState
from ..core.teacher_voice import build_teacher_voice
from ..core.text import content_to_text


ASSESSMENT_DIMENSIONS = [
    "数学基础",
    "控制系统基本概念",
    "系统建模能力",
    "稳定性分析能力",
    "时域性能分析能力",
    "稳态误差分析能力",
    "根轨迹分析能力",
    "频域分析与校正能力",
]

SELF_SCORE_MAP = {"A": 25, "B": 50, "C": 75, "D": 100}


def _is_insufficient_balance_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return "insufficient balance" in text or "error code: 402" in text or "余额不足" in text


def _friendly_llm_error_message(exc: Exception) -> str:
    if _is_insufficient_balance_error(exc):
        return "模型服务余额不足，本次先使用本地规则完成分析；请在设置中切换可用模型或充值后再继续使用 AI 增强。"
    return "模型服务暂时不可用，本次先使用本地规则完成分析；你可以稍后重试或检查 API Key、模型和网络配置。"

# ===========================================================================
# 内部辅助：从图谱节点构建概念候选列表
# ===========================================================================

def _build_concept_candidates(graph_nodes: dict) -> list[dict]:
    """从已加载的图谱节点中提取概念候选，供 LLM 选择。"""
    candidates = []
    for title, node in (graph_nodes or {}).items():
        objectives = (node.get("learning_objectives") or [])[:1]
        must = (node.get("must_know") or [])[:1]
        if not objectives and not must:
            continue
        entry: dict = {
            "concept": title,
            "concept_id": str(node.get("node_id") or node.get("id") or title).strip(),
            "concept_title": title,
        }
        if objectives:
            entry["objective"] = str(objectives[0])[:60]
        if must:
            entry["must_know"] = str(must[0])[:60]
        candidates.append(entry)
    # 无结构数据时直接用标题列表
    if not candidates:
        candidates = [{"concept": t, "concept_id": t, "concept_title": t} for t in list((graph_nodes or {}).keys())[:80]]
    return candidates[:80]


# ===========================================================================
# AssessmentGenerator — 生成 10 自评 + 10 配对客观题
# ===========================================================================

def build_assessment_generator_node(llm, event_sink: EventSink, *, graph_nodes: Optional[dict] = None, question_bank_provider=None):
    """
    Parameters
    ----------
    graph_nodes : dict[str, dict] | None
        由 retriever.course_graph_nodes 提供，key 为节点标题。
        为 None 时由 LLM 自行从领域知识中选概念。
    question_bank_provider : QuestionBankProvider | None
        本地题库。优先从题库取题，不足时再用 LLM 补充。
    """

    def node(state: AgentState) -> dict:
        topic = state["current_topic"]

        # ── 幂等保护：题目已存在时直接重发（刷新场景）──
        existing = state.get("assessment_questions", [])
        if existing:
            event_sink.emit(
                make_event(
                    "assessment.batch",
                    "assessment_generator",
                    message="测评题目已就绪，请作答。",
                    data={"questions": existing},
                )
            )
            return {
                "flow_status": "awaiting_assessment",
                "assessment_questions": existing,
            }

        event_sink.emit(
            make_event(
                "node.start",
                "assessment_generator",
                message=f"我先为【{topic}】准备一轮概念配对测评，用来精准定位起点。",
                data={"topic": topic},
            )
        )

        # ── 构建概念候选提示 ──
        candidates = _build_concept_candidates(graph_nodes or {})

        # ── 1) 优先从题库取题 ──
        bank_questions: list = []
        if question_bank_provider is not None and hasattr(question_bank_provider, "get_assessment_questions"):
            try:
                bank_questions = list(question_bank_provider.get_assessment_questions([], k=10) or [])
            except Exception:
                bank_questions = []
            if bank_questions:
                bank_questions = _adapt_bank_questions(bank_questions)

        # ── 2) 题库不足时用 LLM 补充 ──
        questions: list = []
        if len(bank_questions) >= 10:
            questions = bank_questions[:10]
            event_sink.emit(
                make_event(
                    "node.stream",
                    "assessment_generator",
                    data={"text": "（本轮测评使用题库中的标准题目）\n"},
                )
            )
        else:
            questions = list(bank_questions)
            remaining = 10 - len(questions)
            llm_questions = _generate_llm_assessment_questions(llm, event_sink, topic, candidates, remaining)
            questions.extend(llm_questions)
            if bank_questions:
                event_sink.emit(
                    make_event(
                        "node.stream",
                        "assessment_generator",
                        data={"text": f"（题库提供 {len(bank_questions)} 题，AI 补充 {len(llm_questions)} 题）\n"},
                    )
                )

        questions = _normalize_subjective_questions(questions, candidates)

        # ── 发出引导语 ──
        event_sink.emit(
            make_event(
                "node.stream",
                "assessment_generator",
                data={"text": f"接下来请完成 {len(questions)} 道自评题，帮我快速了解你的起点。\n\n"},
            )
        )

        # ── 批量推送所有题目，由前端步进器处理翻页 ──
        event_sink.emit(
            make_event(
                "assessment.batch",
                "assessment_generator",
                message="测评题目已就绪，请作答。",
                data={"questions": questions},
            )
        )

        event_sink.emit(
            make_event(
                "node.complete",
                "assessment_generator",
                message="学前测评题已生成，等待用户作答。",
                data={"count": len(questions)},
            )
        )

        return {
            "assessment_questions": questions,
            "flow_status": "awaiting_assessment",
            "message_history": list(state.get("message_history", []))
            + [
                {
                    "role": "assistant",
                    "kind": "assessment_intro",
                    "content": f"学前自评开始，共 {len(questions)} 道题。",
                }
            ],
        }

    return node


# ===========================================================================
# 辅助：题库题目 → 标准评估格式
# ===========================================================================

def _adapt_bank_questions(bank_items: list) -> list[dict]:
    """把题库 JSONL 格式的题目转换成 assessment_generator 内部格式。"""
    adapted = []
    for item in bank_items:
        qid = item.get("question_id") or item.get("id") or f"BANK-{len(adapted) + 1}"
        question_text = str(item.get("question") or item.get("stem") or item.get("prompt") or "").strip()
        if not question_text:
            continue
        options = item.get("options", [])
        if isinstance(options, dict):
            options = [f"{k}. {v}" for k, v in sorted(options.items())]
        score_map = item.get("score_map") or dict(SELF_SCORE_MAP)
        if isinstance(score_map, dict):
            score_map = {str(k).upper(): int(v) for k, v in score_map.items()}
        adapted.append({
            "id": len(adapted) + 1,
            "type": item.get("type", "subjective_choice"),
            "concept": str(item.get("concept") or item.get("concept_title") or "").strip(),
            "concept_id": str(item.get("concept_id") or item.get("node_id") or "").strip(),
            "concept_title": str(item.get("concept_title") or item.get("concept") or "").strip(),
            "dimension": str(item.get("dimension") or "").strip(),
            "question": question_text,
            "options": options,
            "score_map": score_map,
        })
    return adapted


def _generate_llm_assessment_questions(llm, event_sink: EventSink, topic: str, candidates: list[dict], count: int) -> list:
    """用 LLM 生成指定数量的主观选择题（当题库不足时调用）。"""
    if llm is None or count <= 0:
        return []

    concept_hint = ""
    if candidates:
        concept_list = json.dumps(candidates, ensure_ascii=False)
        concept_hint = (
            f"\n可用知识图谱概念（共 {len(candidates)} 个，请从中选出最能代表【{topic}】整体掌握水平的概念）：\n"
            f"{concept_list}\n"
        )

    system_msg = SystemMessage(
        content=(
            "你是一位经验丰富的教育测评专家，擅长设计精准的诊断性测评量表。"
            "你的输出必须是合法 JSON，不含任何 Markdown 代码块标记。"
        )
    )
    human_msg = HumanMessage(
        content=f"""请为学习主题【{topic}】设计 {count} 道自我评估选择题用于学前摸底。
{concept_hint}
任务说明：
1. 选出 {count} 个能覆盖【{topic}】学习范围的核心概念（分散在数学基础、基本概念、建模、稳定性等不同能力维度）
2. 每题让学生评估自己对某个概念的了解和熟悉程度（例如"关于「XX」，你目前的了解程度如何？"）
3. 四个选项 A/B/C/D 从低到高依次为：没接触过 → 有所耳闻但模糊 → 比较了解 → 非常熟悉能运用
4. 每题必须提供 score_map，A/B/C/D 分别映射为 25/50/75/100
5. 选项描述要贴合该概念的学习场景，帮助学生准确定位自己的水平

dimension 必须是以下八者之一（对应自动控制理论的核心能力）：
数学基础 / 控制系统基本概念 / 系统建模能力 / 稳定性分析能力 / 时域性能分析能力 / 稳态误差分析能力 / 根轨迹分析能力 / 频域分析与校正能力

输出 JSON Schema（直接输出，不加任何说明）：
{{{{
  "questions": [
    {{{{
      "id": 1,
      "type": "subjective_choice",
      "concept": "概念名称",
      "concept_id": "node_id",
      "concept_title": "概念名称",
      "dimension": "数学基础",
      "question": "题干",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "score_map": {{{{"A": 25, "B": 50, "C": 75, "D": 100}}}}
    }}}}
  ]
}}}}"""
    )

    raw = ""
    try:
        for chunk in llm.stream([system_msg, human_msg]):
            raw += content_to_text(chunk.content)
    except Exception as exc:
        event_sink.emit(
            make_event(
                "session.warning",
                "assessment_generator",
                message=f"{_friendly_llm_error_message(exc)}（测评题将使用本地兜底模板补齐。）",
            )
        )
        return []

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

    return questions[:count]


# ===========================================================================
# 辅助：从 20 题中组装 10 组配对
# ===========================================================================

def _build_pairs(questions: list) -> list[dict]:
    """从 Q1-Q10 (self_eval) + Q11-Q20 (objective) 组装 10 组配对。"""
    if _is_subjective_assessment(questions):
        pairs = []
        for question in questions[:10]:
            concept = _question_concept_title(question) or f"概念{question.get('id', len(pairs) + 1)}"
            pairs.append({
                "index": len(pairs),
                "concept": concept,
                "concept_id": str(question.get("concept_id") or concept).strip(),
                "subjective": {
                    "id": question["id"],
                    "question": question.get("question", ""),
                    "options": question.get("options", []),
                    "dimension": str(question.get("dimension") or "").strip(),
                    "score_map": question.get("score_map") or dict(SELF_SCORE_MAP),
                },
            })
        return pairs

    self_qs = {q["id"]: q for q in questions if q.get("type") == "self_eval"}
    obj_qs = {q["id"]: q for q in questions if q.get("type") == "objective"}

    pairs = []
    for qid, sq in sorted(self_qs.items(), key=lambda x: int(x[0])):
        paired_id = sq.get("paired_id")
        oq = obj_qs.get(paired_id, {})
        concept = str(sq.get("concept_title") or sq.get("concept") or f"概念{qid}").strip()
        pairs.append({
            "index": len(pairs),
            "concept": concept,
            "concept_id": str(sq.get("concept_id") or concept).strip(),
            "self_eval": {
                "id": sq["id"],
                "question": sq.get("question", ""),
                "options": sq.get("options", []),
                "dimension": str(sq.get("dimension") or "").strip(),
            },
            "objective": {
                "id": oq.get("id", paired_id),
                "question": oq.get("question", ""),
                "options": oq.get("options", []),
                "correct": _normalize_answer(str(oq.get("correct_answer") or oq.get("correct") or "")),
                "dimension": str(oq.get("dimension") or "").strip(),
            },
        })
    return pairs


def _is_subjective_assessment(questions: list) -> bool:
    return bool(questions) and all(q.get("type") == "subjective_choice" for q in questions[:10])


def _normalize_subjective_questions(questions: list, candidates: list[dict]) -> list[dict]:
    normalized: list[dict] = []
    for index, raw in enumerate([q for q in questions if isinstance(q, dict)], start=1):
        if len(normalized) >= 10:
            break
        if raw.get("type") == "objective":
            continue
        concept = str(raw.get("concept_title") or raw.get("concept") or "").strip()
        question_text = str(raw.get("question") or "").strip()
        if not concept and index - 1 < len(candidates):
            concept = str(candidates[index - 1].get("concept_title") or candidates[index - 1].get("concept") or "").strip()
        if not concept:
            concept = f"概念{index}"
        if not question_text:
            question_text = f"关于「{concept}」，你目前的了解和掌握程度如何？"
        options = _normalize_subjective_options(raw.get("options"))
        score_map = _normalize_score_map(raw.get("score_map"))
        normalized.append(
            {
                "id": len(normalized) + 1,
                "type": "subjective_choice",
                "concept": concept,
                "concept_id": str(raw.get("concept_id") or concept).strip(),
                "concept_title": concept,
                "dimension": str(raw.get("dimension") or ASSESSMENT_DIMENSIONS[(len(normalized)) % len(ASSESSMENT_DIMENSIONS)]).strip(),
                "question": question_text,
                "options": options,
                "score_map": score_map,
            }
        )

    while len(normalized) < 10:
        index = len(normalized)
        candidate = candidates[index] if index < len(candidates) else {}
        concept = str(candidate.get("concept_title") or candidate.get("concept") or f"概念{index + 1}").strip()
        normalized.append(
            {
                "id": index + 1,
                "type": "subjective_choice",
                "concept": concept,
                "concept_id": str(candidate.get("concept_id") or concept).strip(),
                "concept_title": concept,
                "dimension": ASSESSMENT_DIMENSIONS[index % len(ASSESSMENT_DIMENSIONS)],
                "question": f"关于「{concept}」，你目前的了解和掌握程度如何？",
                "options": _normalize_subjective_options([]),
                "score_map": dict(SELF_SCORE_MAP),
            }
        )
    return normalized


def _normalize_subjective_options(options: object) -> list[str]:
    values = [str(item).strip() for item in options or [] if str(item).strip()] if isinstance(options, list) else []
    defaults = [
        "A. 基本没接触过，不太清楚这个概念",
        "B. 有所耳闻，但理解比较模糊",
        "C. 比较了解，能说出核心要点",
        "D. 非常熟悉，能灵活运用",
    ]
    merged = values[:4] + defaults[len(values[:4]):]
    result = []
    for idx, text in enumerate(merged[:4]):
        key = "ABCD"[idx]
        if text[:1].upper() in {"A", "B", "C", "D"}:
            result.append(text)
        else:
            result.append(f"{key}. {text}")
    return result


def _normalize_score_map(score_map: object) -> dict[str, int]:
    if isinstance(score_map, dict):
        result = {}
        for key in ("A", "B", "C", "D"):
            try:
                result[key] = int(score_map.get(key, SELF_SCORE_MAP[key]))
            except Exception:
                result[key] = SELF_SCORE_MAP[key]
        return result
    return dict(SELF_SCORE_MAP)


def _emit_current_question(event_sink: EventSink, pairs: list, pair_idx: int, phase: str, total_pairs: int):
    """通过 SSE 事件发出当前待答的一道题。"""
    if pair_idx >= len(pairs):
        return
    pair = pairs[pair_idx]
    if phase == "subjective_choice":
        q = pair["subjective"]
        event_sink.emit(
            make_event(
                "assessment.question",
                "assessment_dialog",
                message=q["question"],
                data={
                    "pair_index": pair_idx,
                    "total_pairs": total_pairs,
                    "phase": "subjective_choice",
                    "concept": pair["concept"],
                    "question_id": q["id"],
                    "question": q["question"],
                    "options": q["options"],
                    "score_map": q.get("score_map") or dict(SELF_SCORE_MAP),
                },
            )
        )
        return

    if phase == "self_eval":
        q = pair["self_eval"]
        event_sink.emit(
            make_event(
                "assessment.question",
                "assessment_dialog",
                message=q["question"],
                data={
                    "pair_index": pair_idx,
                    "total_pairs": total_pairs,
                    "phase": "self_eval",
                    "concept": pair["concept"],
                    "question_id": q["id"],
                    "question": q["question"],
                    "options": q["options"],
                },
            )
        )
    else:
        q = pair["objective"]
        event_sink.emit(
            make_event(
                "assessment.question",
                "assessment_dialog",
                message=q["question"],
                data={
                    "pair_index": pair_idx,
                    "total_pairs": total_pairs,
                    "phase": "objective",
                    "concept": pair["concept"],
                    "question_id": q["id"],
                    "question": q["question"],
                    "options": q["options"],
                },
            )
        )


# ===========================================================================
# AssessmentDialog — 对话式逐题状态机
# ===========================================================================

def build_assessment_dialog_node(event_sink: EventSink):
    """
    每次收到用户一个回答 → 推进状态机 → 发下一题或进入 profiling。

    状态机流程：
      self_eval → (收回答) → objective → (收回答) → [下一组 self_eval | done]
    """

    def node(state: AgentState) -> dict:
        as_dict = dict(state.get("assessment_state") or {})
        phase = str(as_dict.get("phase") or "self_eval")
        pair_idx = int(as_dict.get("current_pair_index") or 0)
        pairs = list(as_dict.get("pairs") or [])
        answers = dict(as_dict.get("answers") or {})
        pending_self_score = as_dict.get("pending_self_score")
        total = len(pairs)

        # 用户本轮回答（由 API 层写入 pending_interaction_answer）
        user_answer = _normalize_answer(
            str(state.get("pending_interaction_answer") or "").strip()
        )

        if not pairs or pair_idx >= total:
            # 异常保护：直接进 profiling
            return {"flow_status": "profiling", "assessment_state": as_dict}

        pair = pairs[pair_idx]
        message_history = list(state.get("message_history", []))

        if phase == "subjective_choice":
            question = pair["subjective"]
            answers[str(question["id"])] = user_answer
            message_history.append({
                "role": "user",
                "kind": "assessment_answer",
                "content": user_answer,
                "data": {"question_id": question["id"], "phase": "subjective_choice"},
            })

            next_idx = pair_idx + 1
            as_dict["current_pair_index"] = next_idx
            as_dict["answers"] = answers

            if next_idx >= total:
                as_dict["phase"] = "done"
                event_sink.emit(
                    make_event(
                        "node.stream",
                        "assessment_dialog",
                        data={"text": "\n10 道题完成了！我现在来分析你的起点……\n"},
                    )
                )
                event_sink.emit(
                    make_event(
                        "node.complete",
                        "assessment_dialog",
                        message="主观选择测评完成，进入画像分析。",
                        data={"total_answered": len(answers)},
                    )
                )
                return {
                    "assessment_state": as_dict,
                    "assessment_answers": answers,
                    "flow_status": "profiling",
                    "pending_interaction_answer": "",
                    "message_history": message_history,
                }

            as_dict["phase"] = "subjective_choice"
            event_sink.emit(
                make_event(
                    "node.stream",
                    "assessment_dialog",
                    data={"text": f"\n好，第 {next_idx + 1}/{total} 题——\n\n"},
                )
            )
            _emit_current_question(event_sink, pairs, next_idx, "subjective_choice", total)
            return {
                "assessment_state": as_dict,
                "assessment_answers": answers,
                "flow_status": "assessment_dialog",
                "pending_interaction_answer": "",
                "message_history": message_history,
            }

        if phase == "self_eval":
            # 收到自评回答
            answers[str(pair["self_eval"]["id"])] = user_answer
            self_score = SELF_SCORE_MAP.get(user_answer, 50)
            message_history.append({
                "role": "user",
                "kind": "assessment_answer",
                "content": user_answer,
                "data": {"question_id": pair["self_eval"]["id"], "phase": "self_eval"},
            })

            # 给反馈 + 发配对客观题
            self_desc = _self_score_desc(user_answer)
            event_sink.emit(
                make_event(
                    "node.stream",
                    "assessment_dialog",
                    data={"text": f"好，你觉得自己{self_desc}。来看一道对应的判断题——\n\n"},
                )
            )

            as_dict["phase"] = "objective"
            as_dict["pending_self_score"] = self_score
            as_dict["answers"] = answers

            _emit_current_question(event_sink, pairs, pair_idx, "objective", total)

            return {
                "assessment_state": as_dict,
                "assessment_answers": answers,
                "flow_status": "assessment_dialog",
                "pending_interaction_answer": "",
                "message_history": message_history,
            }

        elif phase == "objective":
            # 收到客观题回答
            answers[str(pair["objective"]["id"])] = user_answer
            correct = pair["objective"].get("correct", "")
            is_correct = user_answer == correct
            message_history.append({
                "role": "user",
                "kind": "assessment_answer",
                "content": user_answer,
                "data": {"question_id": pair["objective"]["id"], "phase": "objective"},
            })

            # 计算差距，给简短反馈
            self_score = pending_self_score if pending_self_score is not None else 50
            actual_score = 100 if is_correct else 0
            gap = self_score - actual_score

            feedback_text = _build_pair_feedback(
                pair["concept"], is_correct, correct, gap, pair["objective"]["options"]
            )
            event_sink.emit(
                make_event(
                    "assessment.feedback",
                    "assessment_dialog",
                    message=feedback_text,
                    data={
                        "pair_index": pair_idx,
                        "concept": pair["concept"],
                        "is_correct": is_correct,
                        "correct_answer": correct,
                        "chosen": user_answer,
                        "gap": gap,
                    },
                )
            )
            message_history.append({
                "role": "assistant",
                "kind": "assessment_feedback",
                "content": feedback_text,
                "data": {"pair_index": pair_idx, "is_correct": is_correct},
            })

            # 推进到下一组
            next_idx = pair_idx + 1
            as_dict["current_pair_index"] = next_idx
            as_dict["pending_self_score"] = None
            as_dict["answers"] = answers

            if next_idx >= total:
                # 全部完成，进入 profiling
                as_dict["phase"] = "done"
                event_sink.emit(
                    make_event(
                        "node.stream",
                        "assessment_dialog",
                        data={"text": "\n所有题目完成了！我现在来分析你的起点……\n"},
                    )
                )
                event_sink.emit(
                    make_event(
                        "node.complete",
                        "assessment_dialog",
                        message="测评对话全部完成，进入画像分析。",
                        data={"total_answered": len(answers)},
                    )
                )
                return {
                    "assessment_state": as_dict,
                    "assessment_answers": answers,
                    "flow_status": "profiling",
                    "pending_interaction_answer": "",
                    "message_history": message_history,
                }
            else:
                # 发下一组自评题
                as_dict["phase"] = "self_eval"
                transition = f"\n好，第 {next_idx + 1}/{total} 组——\n\n"
                event_sink.emit(
                    make_event(
                        "node.stream",
                        "assessment_dialog",
                        data={"text": transition},
                    )
                )
                _emit_current_question(event_sink, pairs, next_idx, "self_eval", total)

                return {
                    "assessment_state": as_dict,
                    "assessment_answers": answers,
                    "flow_status": "assessment_dialog",
                    "pending_interaction_answer": "",
                    "message_history": message_history,
                }

        # 未知 phase，兜底进 profiling
        return {"flow_status": "profiling", "assessment_state": as_dict}

    return node


def _self_score_desc(answer: str) -> str:
    return {
        "A": "从没接触过这块",
        "B": "听说过但说不太清",
        "C": "理解基本概念",
        "D": "能熟练应用",
    }.get(answer, "有一定了解")


def _build_pair_feedback(concept: str, is_correct: bool, correct: str, gap: int, options: list) -> str:
    """为一组配对生成简短反馈（答对/答错 + 差距提示）。"""
    correct_text = ""
    for opt in (options or []):
        opt_str = str(opt or "").strip()
        if opt_str and opt_str[0].upper() == correct:
            correct_text = opt_str
            break

    if is_correct:
        if gap > 30:
            return f"答对了，但你之前觉得自己不太行——其实「{concept}」你比想象中掌握得好。"
        return f"答对了。「{concept}」这块你的判断和实际表现一致。"
    else:
        if gap < -30:
            return f"答错了，正确答案是 {correct_text or correct}。你之前觉得自己挺确定的——「{concept}」这里有盲点，等会儿重点看。"
        return f"答错了，正确答案是 {correct_text or correct}。「{concept}」需要补一下，不过你自评也比较谨慎，后面重点带你过。"


# ===========================================================================
# UserProfiler — 差距分析 + 教学策略决定
# ===========================================================================

def _resolve_course_start_label(graph_pipeline: Optional[object], topic: str) -> str:
    node_map = dict(getattr(graph_pipeline, "node_map", {}) or {})
    if not node_map:
        return topic

    def string_list(values) -> list[str]:
        if isinstance(values, list):
            return [str(item).strip() for item in values if str(item).strip()]
        return []

    def source_type(node: dict) -> str:
        return str(node.get("source_type") or "").strip().lower()

    def numeric_key(node_id: str) -> tuple[int, str]:
        digits = "".join(ch for ch in str(node_id or "") if ch.isdigit())
        return (int(digits) if digits else 999999, str(node_id or ""))

    candidates = []
    for node_id, node in node_map.items():
        if string_list(node.get("prerequisite_nodes")):
            continue
        name = str(node.get("name") or node_id).strip()
        candidates.append(
            (
                0 if "一般概念" in name else 1,
                0 if "chapter_anchor" in source_type(node) else 1,
                numeric_key(str(node_id)),
                name,
            )
        )
    if not candidates:
        return topic
    candidates.sort()
    return candidates[0][3] or topic


def build_user_profiler_node(llm, event_sink: EventSink, graph_pipeline=None):
    def _find_node_id_by_name(node_map: dict, name: str) -> str:
        """通过节点名称查找节点 ID（模糊匹配）。"""
        target = str(name or "").strip()
        if not target:
            return ""
        # 精确匹配
        for node_id, node in node_map.items():
            if target == str(node.get("name") or "").strip():
                return str(node_id).strip()
        # 包含匹配
        for node_id, node in node_map.items():
            node_name = str(node.get("name") or "").strip()
            if target in node_name or node_name in target:
                return str(node_id).strip()
        return ""

    def node(state: AgentState) -> dict:
        topic = state["current_topic"]
        questions = state.get("assessment_questions", [])
        answers = state.get("assessment_answers", {})

        event_sink.emit(
            make_event(
                "node.start",
                "user_profiler",
                message="我在分析你的自评与实测之间的差距，马上就知道从哪里切进去最合适。",
                data={"topic": topic},
            )
        )

        # ── Step 1: 概念差距分析（核心逻辑）──
        concept_gaps = _compute_concept_gaps(questions, answers)
        radar_data = _generate_radar_data(event_sink, topic, questions, answers)
        difficulty_level, teaching_strategy = _decide_teaching_start(concept_gaps)
        start_label = _resolve_course_start_label(graph_pipeline, topic)

        # 推送雷达图（前端兼容）
        event_sink.emit(
            make_event("profile.radar_data", "user_profiler", data=radar_data)
        )

        # ── Step 2: 流式生成画像报告 ──
        full_report = _generate_profile_report(
            llm,
            event_sink,
            topic,
            concept_gaps,
            difficulty_level,
            teaching_strategy,
            start_label,
        )

        # ── Step 3: 广播教学起点决策 ──
        event_sink.emit(
            make_event(
                "profile.difficulty_level",
                "user_profiler",
                message=(
                    f"综合校准后，我把起始难度定在 Lv.{difficulty_level}，"
                    f"采用「{_strategy_label(teaching_strategy)}」进入讲解。"
                ),
                data={
                    "difficulty_level": difficulty_level,
                    "teaching_strategy": teaching_strategy,
                },
            )
        )
        # ── Step 4: 初始化用户知识图谱（测评完成即有初始状态）──
        # 所有被测概念设为 not_started，携带校准分供 UI 展示
        # 使用节点 ID 作为 key，以便图谱界面正确匹配
        node_map = dict(getattr(graph_pipeline, "node_map", {}) or {})
        user_knowledge_graph = {}
        for concept, v in concept_gaps.items():
            concept_id = str(v.get("concept_id") or "").strip()
            # 尝试通过名称查找节点 ID
            node_id = _find_node_id_by_name(node_map, concept) or _find_node_id_by_name(node_map, concept_id) or concept_id or concept
            node_name = concept
            # 如果找到了节点 ID，使用节点名称作为显示名称
            if node_id in node_map:
                node_name = str(node_map[node_id].get("name") or concept).strip()
            user_knowledge_graph[node_name] = {
                "status": "not_started",
                "id": node_id,
                "name": node_name,
                "calibrated": v.get("calibrated", 50),
                "gap_type": v.get("gap_type", ""),
                "turn_count": 0,
            }
        event_sink.emit(
            make_event(
                "user_knowledge_graph.sync",
                "user_profiler",
                message="学情图谱初始化完成。",
                data=user_knowledge_graph,
            )
        )
        event_sink.emit(
            make_event(
                "node.complete",
                "user_profiler",
                message="学前摸底完成，我们直接进入正式教学。",
            )
        )

        return {
            "assessment_radar": radar_data,
            "assessment_result": full_report,
            "assessment_concept_gaps": concept_gaps,
            "user_knowledge_graph": user_knowledge_graph,
            "is_assessed": True,
            "flow_status": "normal",
            "learning_phase": "profiled",
            "learning_resume_target": "initial_node_selector",
            "learning_resume_reason": "profiling_complete_select_course_root",
            "difficulty_level": difficulty_level,
            "teaching_strategy": teaching_strategy,
            "attempt_count": 0,
            "score_history": [],
            "graph_anchor_id": "",
            "graph_anchor_title": "",
            "current_node_id": "",
            "current_node_name": "",
            "current_node_status": "",
            "turn_goal": state.get("turn_goal", "") or topic,
            "topic_focus": state.get("topic_focus", ""),
            # 透传自评数据，确保下游 learning_plan_generator 能读到
            "self_assessment_scores": state.get("self_assessment_scores") or {},
            "skip_self_assessment": state.get("skip_self_assessment", False),
        }

    return node


# ===========================================================================
# 核心计算：概念差距分析
# ===========================================================================

def _normalize_answer(value: str) -> str:
    cleaned = (value or "").strip().upper()
    return cleaned[:1] if cleaned else ""


def _question_concept_title(question: dict) -> str:
    return str(question.get("concept_title") or question.get("concept") or "").strip()


def _question_correct_answer(question: dict) -> str:
    return _normalize_answer(str(question.get("correct_answer") or question.get("correct") or ""))


def _compute_concept_gaps(questions: list, answers: dict) -> dict:
    """
    计算每个概念的自评-实测差距（概念级诊断）。

    Returns
    -------
    dict[concept_name, {
        self_score, actual_score, gap, gap_type, calibrated, dimension
    }]
    gap_type: overconfident | underconfident | aligned_high | aligned_low
    """
    concept_gaps: dict = {}
    subjective_qs = [q for q in questions if q.get("type") == "subjective_choice"]
    if subjective_qs:
        for index, q in enumerate(subjective_qs, start=1):
            qid = q.get("id", index)
            concept = _question_concept_title(q) or f"概念{qid}"
            answer = _normalize_answer(answers.get(str(qid), answers.get(qid, "")))
            score = _subjective_choice_score(q, answer)
            # 纯主观题无配对实测，按自评分段标记掌握水平
            if score >= 75:
                gap_type = "aligned_high"    # 自评掌握良好
            elif score >= 50:
                gap_type = "aligned_low"     # 自评有基础但仍需加强
            else:
                gap_type = "underconfident"  # 自评薄弱，需要重点补
            concept_gaps[concept] = {
                "concept_id": str(q.get("concept_id") or concept).strip(),
                "self_score": score,
                "actual_score": score,
                "gap": 0,
                "gap_type": gap_type,
                "calibrated": score,
                "dimension": str(q.get("dimension") or "").strip(),
            }
        return concept_gaps

    self_qs = {q["id"]: q for q in questions if q.get("type") == "self_eval"}
    obj_qs = {q["id"]: q for q in questions if q.get("type") == "objective"}

    for qid, q in self_qs.items():
        concept = _question_concept_title(q) or f"概念{qid}"
        paired_id = q.get("paired_id")

        # 自评得分 (A=25, B=50, C=75, D=100)
        self_ans = _normalize_answer(answers.get(str(qid), answers.get(qid, "")))
        self_score = SELF_SCORE_MAP.get(self_ans, 50)

        # 实测得分
        actual_score = 50  # 无配对题时默认中性
        if paired_id:
            obj_q = obj_qs.get(paired_id)
            if obj_q:
                actual_ans = _normalize_answer(answers.get(str(paired_id), answers.get(paired_id, "")))
                correct = _question_correct_answer(obj_q)
                if correct and actual_ans:
                    actual_score = 100 if actual_ans == correct else 0

        gap = self_score - actual_score

        if gap > 30:
            gap_type = "overconfident"   # 高估自己
        elif gap < -30:
            gap_type = "underconfident"  # 低估自己（实测更好）
        elif actual_score >= 60:
            gap_type = "aligned_high"   # 评估准确且掌握良好
        else:
            gap_type = "aligned_low"    # 评估准确但仍需加强

        # 校准分：偏重实测表现
        calibrated = round(0.3 * self_score + 0.7 * actual_score)

        concept_gaps[concept] = {
            "concept_id": str(q.get("concept_id") or concept).strip(),
            "self_score": self_score,
            "actual_score": actual_score,
            "gap": gap,
            "gap_type": gap_type,
            "calibrated": calibrated,
            "dimension": str(q.get("dimension") or "").strip(),
        }

    return concept_gaps


def _subjective_choice_score(question: dict, answer: str) -> int:
    score_map = _normalize_score_map(question.get("score_map"))
    return int(score_map.get(_normalize_answer(answer), 50))


def _decide_teaching_start(concept_gaps: dict) -> tuple[int, str]:
    """
    根据概念差距分析决定教学起点。

    Returns
    -------
    (difficulty_level: 1-5, teaching_strategy: str)
    """
    if not concept_gaps:
        return 3, "explain"

    values = list(concept_gaps.values())
    calibrated_scores = [v["calibrated"] for v in values]
    avg = sum(calibrated_scores) / len(calibrated_scores)

    overconfident = sum(1 for v in values if v["gap_type"] == "overconfident")
    underconfident = sum(1 for v in values if v["gap_type"] == "underconfident")
    aligned_high = sum(1 for v in values if v["gap_type"] == "aligned_high")
    total = len(values)
    threshold = max(3, total // 3)

    # 难度级别（校准得分 → 1-5）
    if avg <= 20:
        level = 1
    elif avg <= 40:
        level = 2
    elif avg <= 60:
        level = 3
    elif avg <= 80:
        level = 4
    else:
        level = 5

    # 教学策略（差距模式 → 策略）
    if overconfident >= threshold:
        strategy = "socratic"      # 多处高估 → 苏格拉底法暴露盲点
    elif underconfident >= threshold:
        strategy = "analogy"       # 多处低估 → 类比法先建信心
    elif aligned_high >= total // 2:
        strategy = "stepbystep"    # 整体掌握良好 → 分步推进
    else:
        strategy = "explain"       # 一般情况 → 直接讲解

    return level, strategy


def _strategy_label(strategy: str) -> str:
    return {
        "socratic": "苏格拉底引导法",
        "analogy": "类比教学",
        "stepbystep": "分步推进",
        "explain": "直接讲解",
    }.get(strategy, strategy)


def _select_initial_teaching_anchor(concept_gaps: dict) -> tuple[str, str]:
    if not concept_gaps:
        return "", ""

    priority = {
        "overconfident": 0,
        "aligned_low": 1,
        "underconfident": 2,
        "aligned_high": 3,
    }
    ranked = sorted(
        concept_gaps.items(),
        key=lambda item: (
            priority.get(str(item[1].get("gap_type") or ""), 9),
            float(item[1].get("calibrated", 50)),
            str(item[0]),
        ),
    )
    concept, payload = ranked[0]
    return str(concept or "").strip(), str(payload.get("concept_id") or concept or "").strip()


# ===========================================================================
# 雷达数据（8 维能力，匹配 V2 ability_mapper 的 A-H）
# ===========================================================================

def _question_dimension(question: dict, fallback_index: int) -> str:
    dimension = (question.get("dimension") or "").strip()
    if dimension in ASSESSMENT_DIMENSIONS:
        return dimension
    return ASSESSMENT_DIMENSIONS[fallback_index % len(ASSESSMENT_DIMENSIONS)]


def _generate_radar_data(event_sink: EventSink, topic: str, questions: list, answers: dict) -> dict:
    """生成 8 维雷达图数据（对应 V2 能力体系 A-H，供前端 Chart.js 渲染）。"""
    del topic
    aggregates = {
        dim: {"self_total": 0, "self_count": 0, "objective_total": 0, "objective_count": 0}
        for dim in ASSESSMENT_DIMENSIONS
    }

    for index, question in enumerate(questions):
        dimension = _question_dimension(question, index)
        qid = str(question.get("id"))
        answer = _normalize_answer(answers.get(qid, answers.get(question.get("id"), "")))

        if question.get("type") == "subjective_choice":
            score = _subjective_choice_score(question, answer)
            aggregates[dimension]["self_total"] += score
            aggregates[dimension]["self_count"] += 1
            aggregates[dimension]["objective_total"] += score
            aggregates[dimension]["objective_count"] += 1
            continue

        if question.get("type") == "self_eval":
            score = SELF_SCORE_MAP.get(answer)
            if score is None:
                continue
            aggregates[dimension]["self_total"] += score
            aggregates[dimension]["self_count"] += 1
            continue

        if question.get("type") == "objective":
            correct_answer = _question_correct_answer(question)
            if not correct_answer:
                event_sink.emit(
                    make_event(
                        "session.warning",
                        "user_profiler",
                        message=f"题目 {qid} 缺少 correct_answer/correct，已跳过规则评分。",
                    )
                )
                aggregates[dimension]["objective_total"] += 50
                aggregates[dimension]["objective_count"] += 1
                continue
            score = 100 if answer == correct_answer else 0
            aggregates[dimension]["objective_total"] += score
            aggregates[dimension]["objective_count"] += 1

    self_scores, objective_scores, gaps, breakdown = [], [], [], []
    for dim in ASSESSMENT_DIMENSIONS:
        bucket = aggregates[dim]
        self_score = round(bucket["self_total"] / bucket["self_count"]) if bucket["self_count"] else 50
        obj_score = round(bucket["objective_total"] / bucket["objective_count"]) if bucket["objective_count"] else 50
        gap = self_score - obj_score
        self_scores.append(self_score)
        objective_scores.append(obj_score)
        gaps.append(gap)
        breakdown.append({
            "dimension": dim,
            "self_score": self_score,
            "objective_score": obj_score,
            "gap": gap,
            "self_count": bucket["self_count"],
            "objective_count": bucket["objective_count"],
        })

    return {
        "dimensions": ASSESSMENT_DIMENSIONS,
        "self_scores": self_scores,
        "objective_scores": objective_scores,
        "gap_scores": gaps,
        "breakdown": breakdown,
    }


# ===========================================================================
# 流式生成画像报告
# ===========================================================================

def _generate_profile_report(
    llm,
    event_sink: EventSink,
    topic: str,
    concept_gaps: dict,
    difficulty_level: int,
    strategy: str,
    start_label: str,
) -> str:
    # 分类整理差距
    overconfident = [c for c, v in concept_gaps.items() if v["gap_type"] == "overconfident"]
    underconfident = [c for c, v in concept_gaps.items() if v["gap_type"] == "underconfident"]
    aligned_high = [c for c, v in concept_gaps.items() if v["gap_type"] == "aligned_high"]
    aligned_low = [c for c, v in concept_gaps.items() if v["gap_type"] == "aligned_low"]

    gap_lines = []
    if overconfident:
        gap_lines.append(f"以为掌握但实测有盲点：{'、'.join(overconfident)}")
    if underconfident:
        gap_lines.append(f"低估了自己（实测比自评好）：{'、'.join(underconfident)}")
    if aligned_high:
        gap_lines.append(f"真正掌握的：{'、'.join(aligned_high)}")
    if aligned_low:
        gap_lines.append(f"自评和实测都偏弱，需重点补：{'、'.join(aligned_low)}")

    gap_text = "\n".join(gap_lines) if gap_lines else "整体情况有待进一步观察。"

    strategy_desc = {
        "socratic": "苏格拉底引导（通过提问帮你发现自己的盲点，而不是直接告诉答案）",
        "analogy": "类比教学（先用直觉对应物建立感知，再深化理解）",
        "stepbystep": "分步推进（你的基础不错，我们直接往深度走）",
        "explain": "直接讲解（系统性补齐基础后再做提升）",
    }.get(strategy, strategy)

    system_msg = SystemMessage(
        content=build_teacher_voice(
            "你是一位刚刚完成学前摸底测评的老师。"
            "你的任务不是写测评报告，而是把测评结果压成一句自然过渡，帮教学无缝接上。"
            "口吻直接、简洁、有教学判断，不要写标题，不要写列表，不要写评分汇报。"
        )
    )
    human_msg = HumanMessage(
        content=(
            f"学习主题：【{topic}】\n"
            f"综合校准水平：Lv.{difficulty_level}（1-5，5最高）\n"
            f"决定采用的起点策略：{strategy_desc}\n\n"
            f"概念差距发现：\n{gap_text}\n\n"
            "请输出 2 句自然中文，总长不超过 80 字：\n"
            "1. 第一句必须以“我现在大致知道从哪里开始了”开头，并点出一个关键发现。\n"
            f"2. 第二句必须明确说接下来先从「{start_label or topic}」开始，把课程起点打稳，再自然接入后续讲解。\n"
            "禁止输出标题、列表、emoji、分数、报告式总结。"
        )
    )

    fallback_report = _fallback_profile_report(topic, concept_gaps, difficulty_level, strategy, start_label)
    if llm is None:
        event_sink.emit(make_event("node.stream", "user_profiler", message=fallback_report))
        return fallback_report

    full_report = ""
    try:
        for chunk in llm.stream([system_msg, human_msg]):
            text = content_to_text(chunk.content)
            if text:
                full_report += text
                event_sink.emit(
                    make_event("node.stream", "user_profiler", message=text)
                )
    except Exception as exc:
        warning = _friendly_llm_error_message(exc)
        event_sink.emit(
            make_event(
                "session.warning",
                "user_profiler",
                message=warning,
            )
        )
        event_sink.emit(make_event("node.stream", "user_profiler", message=fallback_report))
        return fallback_report

    if not full_report.strip():
        event_sink.emit(make_event("node.stream", "user_profiler", message=fallback_report))
        return fallback_report

    return full_report


def _fallback_profile_report(
    topic: str,
    concept_gaps: dict,
    difficulty_level: int,
    strategy: str,
    start_label: str,
) -> str:
    del strategy
    weak = [c for c, v in concept_gaps.items() if v.get("gap_type") in {"overconfident", "aligned_low", "underconfident"}]
    if weak:
        finding = f"你在「{weak[0]}」附近还需要校准理解"
    else:
        finding = f"你对「{topic}」已有一定基础"
    return (
        f"我现在大致知道从哪里开始了，{finding}。"
        f"接下来先从「{start_label or topic}」开始，把课程起点打稳。"
    )

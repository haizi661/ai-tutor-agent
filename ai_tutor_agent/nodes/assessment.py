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
    "基础概念",
    "规则理解",
    "逻辑推理",
    "场景应用",
    "细节辨析",
    "综合应用",
]

SELF_SCORE_MAP = {"A": 25, "B": 50, "C": 75, "D": 100}

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
            "concept_id": str(node.get("id") or title).strip(),
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

def build_assessment_generator_node(llm, event_sink: EventSink, *, graph_nodes: Optional[dict] = None):
    """
    Parameters
    ----------
    graph_nodes : dict[str, dict] | None
        由 retriever.course_graph_nodes 提供，key 为节点标题。
        为 None 时由 LLM 自行从领域知识中选概念。
    """

    def node(state: AgentState) -> dict:
        topic = state["current_topic"]

        # ── 幂等保护：题目已存在时直接推第一道未答题（刷新场景）──
        existing = state.get("assessment_questions", [])
        existing_as = dict(state.get("assessment_state") or {})
        if existing and existing_as.get("pairs"):
            # 恢复场景：重推当前待答题
            pair_idx = int(existing_as.get("current_pair_index") or 0)
            phase = str(existing_as.get("phase") or "self_eval")
            pairs = existing_as["pairs"]
            if pair_idx < len(pairs):
                _emit_current_question(event_sink, pairs, pair_idx, phase, len(pairs))
            return {
                "flow_status": "assessment_dialog",
                "assessment_state": existing_as,
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
            content=f"""请为学习主题【{topic}】设计一份「概念配对双测量表」。
{concept_hint}
任务说明：
1. 选出 10 个能全面覆盖【{topic}】学习范围的核心概念（分散在基础/规则/推理/应用等不同层次）
2. 为每个概念生成：
   - 1 道自我评价题（Q1-Q10）：让学生判断自己能不能处理一个具体情境，不要像打分表
   - 1 道配对客观题（Q11-Q20）：考察同一概念的实际掌握，必须放进具体工程/应用情境
3. 配对关系固定：Q1↔Q11, Q2↔Q12, ..., Q10↔Q20

自评题选项（固定，所有自评题相同）：
A. 从没接触过  B. 听说过，但说不清  C. 理解基本概念，能说出来  D. 能熟练应用或推导

客观题要求：
- 四选一，有干扰项
- 包含 correct 与 correct_answer（A/B/C/D 之一，二者相同）
- 题干必须落在具体场景里，不能写成纯名词解释

dimension 必须是以下六者之一（每道题都要有）：
基础概念 / 规则理解 / 逻辑推理 / 场景应用 / 细节辨析 / 综合应用

额外要求：
- concept / concept_title 使用节点名称
- concept_id 优先使用图谱里的 concept_id；没有时可回填 concept_title
- 自评题不要写“请打分 1-5”
- 不要一次性像卷子说明那样解释流程，题干本身要像老师在摸底
- 客观题的错误选项要像学生真的会选的干扰项，而不是明显错误

输出 JSON Schema（直接输出，不加任何说明）：
{{
  "questions": [
    {{
      "id": 1,
      "type": "self_eval",
      "concept": "概念名称",
      "concept_id": "node_id",
      "concept_title": "概念名称",
      "paired_id": 11,
      "dimension": "基础概念",
      "question": "如果有人让你用一个具体场景解释「概念名称」，你现在能处理到什么程度？",
      "options": ["A. 从没接触过", "B. 听说过，但说不清", "C. 理解基本概念，能说出来", "D. 能熟练应用或推导"],
      "correct": "",
      "correct_answer": ""
    }},
    ...（Q1-Q10 自评）
    {{
      "id": 11,
      "type": "objective",
      "concept": "概念名称",
      "concept_id": "node_id",
      "concept_title": "概念名称",
      "paired_id": 1,
      "dimension": "基础概念",
      "question": "给出一个具体工程或应用情境，问关于「概念名称」的判断题。",
      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
      "correct": "B",
      "correct_answer": "B"
    }},
    ...（Q11-Q20 客观）
  ]
}}"""
        )

        raw = ""
        for chunk in llm.stream([system_msg, human_msg]):
            raw += content_to_text(chunk.content)

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

        # ── 组装 10 组配对 pair ──
        pairs = _build_pairs(questions)
        assessment_state_dict = {
            "phase": "self_eval",
            "current_pair_index": 0,
            "pairs": pairs,
            "answers": {},
            "pending_self_score": None,
        }

        # ── 发出对话式引导语 + 第一道自评题 ──
        event_sink.emit(
            make_event(
                "node.stream",
                "assessment_generator",
                data={"text": "接下来我会一题一题地问你，先是自我评价，然后是对应的实际判断题。我们开始吧。\n\n"},
            )
        )
        if pairs:
            _emit_current_question(event_sink, pairs, 0, "self_eval", len(pairs))

        event_sink.emit(
            make_event(
                "node.complete",
                "assessment_generator",
                message="概念配对量表已生成，开始逐题追问。",
                data={"count": len(questions), "pair_count": len(pairs)},
            )
        )

        return {
            "assessment_questions": questions,
            "assessment_state": assessment_state_dict,
            "flow_status": "assessment_dialog",
            "message_history": list(state.get("message_history", []))
            + [
                {
                    "role": "assistant",
                    "kind": "assessment_intro",
                    "content": "学前小测开始，我会一题一题地追问你。",
                }
            ],
        }

    return node


# ===========================================================================
# 辅助：从 20 题中组装 10 组配对
# ===========================================================================

def _build_pairs(questions: list) -> list[dict]:
    """从 Q1-Q10 (self_eval) + Q11-Q20 (objective) 组装 10 组配对。"""
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


def _emit_current_question(event_sink: EventSink, pairs: list, pair_idx: int, phase: str, total_pairs: int):
    """通过 SSE 事件发出当前待答的一道题。"""
    if pair_idx >= len(pairs):
        return
    pair = pairs[pair_idx]
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

def build_user_profiler_node(llm, event_sink: EventSink):
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
        start_anchor_title, start_anchor_id = _select_initial_teaching_anchor(concept_gaps)

        # 推送雷达图（前端兼容）
        event_sink.emit(
            make_event("profile.radar_data", "user_profiler", data=radar_data)
        )

        # ── Step 2: 流式生成画像报告 ──
        full_report = _generate_profile_report(
            llm, event_sink, topic, concept_gaps, difficulty_level, teaching_strategy
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
        user_knowledge_graph = {
            concept: {
                "status": "not_started",
                "id": v.get("concept_id") or concept,
                "calibrated": v.get("calibrated", 50),
                "gap_type": v.get("gap_type", ""),
                "turn_count": 0,
            }
            for concept, v in concept_gaps.items()
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
            "difficulty_level": difficulty_level,
            "teaching_strategy": teaching_strategy,
            "attempt_count": 0,
            "score_history": [],
            "graph_anchor_id": start_anchor_id,
            "graph_anchor_title": start_anchor_title,
            "turn_goal": start_anchor_title or state.get("turn_goal", "") or topic,
            "topic_focus": start_anchor_title or state.get("topic_focus", ""),
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
    self_qs = {q["id"]: q for q in questions if q.get("type") == "self_eval"}
    obj_qs = {q["id"]: q for q in questions if q.get("type") == "objective"}

    concept_gaps: dict = {}
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
# 兼容层：6 维雷达数据（保持前端兼容）
# ===========================================================================

def _question_dimension(question: dict, fallback_index: int) -> str:
    dimension = (question.get("dimension") or "").strip()
    if dimension in ASSESSMENT_DIMENSIONS:
        return dimension
    return ASSESSMENT_DIMENSIONS[fallback_index % len(ASSESSMENT_DIMENSIONS)]


def _generate_radar_data(event_sink: EventSink, topic: str, questions: list, answers: dict) -> dict:
    """生成 6 维雷达图数据（供前端 Chart.js 渲染，保持原有格式）。"""
    del topic
    aggregates = {
        dim: {"self_total": 0, "self_count": 0, "objective_total": 0, "objective_count": 0}
        for dim in ASSESSMENT_DIMENSIONS
    }

    for index, question in enumerate(questions):
        dimension = _question_dimension(question, index)
        qid = str(question.get("id"))
        answer = _normalize_answer(answers.get(qid, answers.get(question.get("id"), "")))

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
            "2. 第二句直接说接下来先从什么点切入，让后续讲解自然接上。\n"
            "禁止输出标题、列表、emoji、分数、报告式总结。"
        )
    )

    full_report = ""
    for chunk in llm.stream([system_msg, human_msg]):
        text = content_to_text(chunk.content)
        full_report += text

    return full_report

from __future__ import annotations

from typing import TypedDict


class AgentState(TypedDict):
    current_topic: str
    proposed_topic: str
    tutor_content: str
    tester_question: str
    tester_question_type: str
    tester_question_template: str
    user_answer: str
    score: int
    logic_score: int
    concept_score: int
    feedback: str
    rubric_feedback: list             # 评估量表依据列表
    # ── 学前测评扩展字段 ──
    assessment_questions: list          # LLM 生成的 20 道题 JSON 列表
    assessment_answers: dict            # 用户前端提交的答题结果 {"1": "A", ...}
    assessment_radar: dict              # 6 维雷达图结构化数据
    assessment_result: str              # UserProfiler 生成的 Markdown 画像报告
    is_assessed: bool                   # 是否已完成学前画像评估
    flow_status: str                    # 图流转控制: greeting/topic_intake/meta_qa/smalltalk/topic_confirmation_pending/awaiting_topic_confirmation/assessment_pending/awaiting_assessment/profiling/normal
    # ── 自适应学习字段 ──
    difficulty_level: int               # 1=非常基础 2=基础 3=中等 4=进阶 5=专家，由画像自动计算
    attempt_count: int                  # 当前主题连续失败次数，失败+1, 通过归零
    score_history: list                 # 历史得分记录 [(total, logic, concept, feedback_str), ...]
    teaching_strategy: str             # 当前教学策略: explain/analogy/stepbystep/socratic
    tutor_citations: list             # Tutor 节点引用来源列表
    model_answer: str                   # 评估节点提供的参考答案，评估后推送给学生
    misconceptions: list               # 评估节点识别到的误区列表
    next_review_points: list           # 下一步建议复习点
    is_correct_direction: bool         # 作答方向是否正确
    needs_hint: bool                  # 是否应先给思路提示再重试
    coach_content: str                 # 补救教练节点生成的短讲解
    # --- 知识库功能拓展字段 ---
    student_id: str                    # 学生唯一 ID
    skip_reason: str                   # 跳过原因（用于控制指令）
    interrupt_query: str               # 临时提问内容
    resume_tester: bool                # 临时提问后是否回到原测题
    conversation_history: list         # 临时问答历史


def build_initial_state(topic: str = "") -> AgentState:
    return {
        "student_id": "default_student",
        "skip_reason": "",
        "interrupt_query": "",
        "resume_tester": False,
        "current_topic": topic,
        "proposed_topic": "",
        "tutor_content": "",
        "tester_question": "",
        "tester_question_type": "",
        "tester_question_template": "",
        "user_answer": "",
        "score": 0,
        "logic_score": 0,
        "concept_score": 0,
        "feedback": "",
        "rubric_feedback": [],
        "assessment_questions": [],
        "assessment_answers": {},
        "assessment_radar": {},
        "assessment_result": "",
        "is_assessed": False,
        "flow_status": "greeting",
        "difficulty_level": 3,
        "attempt_count": 0,
        "score_history": [],
        "teaching_strategy": "explain",
        "tutor_citations": [],
        "model_answer": "",
        "misconceptions": [],
        "next_review_points": [],
        "is_correct_direction": True,
        "needs_hint": False,
        "coach_content": "",
        "conversation_history": [],
    }

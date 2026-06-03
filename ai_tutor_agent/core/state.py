from __future__ import annotations

from typing import TypedDict


class AgentState(TypedDict):
    learning_phase: str                # 新主流程阶段: topic_init/pre_assessment/node_teaching/...
    learning_resume_target: str        # 会话恢复时优先进入的节点
    learning_resume_reason: str        # 为什么恢复到该节点
    current_node_id: str               # 当前正在学习的图谱节点 ID
    current_node_name: str             # 当前正在学习的图谱节点名称
    current_node_status: str           # 当前节点状态: selected/teaching/quizzing/passed
    next_node_candidate_id: str        # 候选下一节点 ID
    next_node_candidate_name: str      # 候选下一节点名称
    node_quiz_items: list              # 节点客观题批量题目
    node_quiz_answers: dict            # 节点客观题作答
    node_quiz_wrong_items: list        # 节点客观题错题
    node_quiz_score: int               # 节点客观题得分
    node_content_context: str           # 当前图谱节点抽取出的结构化讲解上下文
    node_teaching_contract: dict        # 当前节点教学契约: goal/must_know/misconceptions/assessment_targets/exit_criteria
    node_quiz_coverage_plan: list       # 当前节点测验覆盖计划，来自教学契约或节点字段
    next_node_candidate_reason: str     # 初始/下一节点选择原因
    homework_items: list               # 本轮布置的作业题
    homework_answers: dict             # 作业作答缓存
    homework_results: list             # 作业评分结果
    homework_score: int                # 作业总分
    homework_status: str               # none/pending/completed
    homework_assignment_id: str         # 当前作业批次 ID
    student_state_snapshot: dict       # StudentStateStore 读取到的快照
    learning_track: str                # 当前会话学习方向: control_theory/artificial_intelligence
    learning_track_label: str          # 当前会话学习方向中文名
    learning_track_locked: bool        # 学习方向是否已固定
    current_topic: str
    current_user_goal: str
    session_goal: str
    turn_goal: str
    proposed_topic: str
    topic_focus: str
    topic_background: str
    topic_detail_summary: str
    topic_starter_options: list
    topic_clarify_rounds: int
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
    assessment_concept_gaps: dict       # 概念级差距分析 {concept: {self_score, actual_score, gap, gap_type, calibrated}}
    user_knowledge_graph: dict          # 用户知识掌握图谱 {node_title: {status, turn_count, calibrated}} status: not_started|in_progress|mastered|skipped
    assessment_state: dict              # 对话式测评状态机 {phase, current_pair_index, pairs, answers, pending_self_score}
    is_assessed: bool                   # 是否已完成学前画像评估
    flow_status: str                    # 图流转控制: greeting/topic_intake/meta_qa/smalltalk/topic_confirmation_pending/awaiting_topic_confirmation/assessment_pending/awaiting_assessment/assessment_dialog/profiling/normal
    # ── 自适应学习字段 ──
    difficulty_level: int               # 1=非常基础 2=基础 3=中等 4=进阶 5=专家，由画像自动计算
    attempt_count: int                  # 当前主题连续失败次数，失败+1, 通过归零
    score_history: list                 # 历史得分记录 [(total, logic, concept, feedback_str), ...]
    teaching_strategy: str             # 当前教学策略: explain/analogy/stepbystep/socratic
    next_step_choice: str              # 讲解后的下一步选择
    post_lesson_choice: str            # 节点讲解后的严格选择: temporary_question/start_test
    continue_or_homework_choice: str    # 节点通过后的严格选择: continue_next_node/stop_today
    post_eval_choice: str              # 通过评估后的下一步选择
    practice_generation_mode: str      # 练习生成模式: ""/same_type
    variant_questions: list            # 错题变式题
    wrong_question_explanations: list  # 错题讲解
    pending_interaction_kind: str      # 挂起中的交互类型
    pending_interaction_prompt: str    # 挂起中的交互提示
    pending_interaction_options: list  # 挂起中的交互选项
    pending_interaction_recommended: str  # 挂起中的推荐选项
    pending_interaction_answer: str    # 挂起中的交互答案
    tutor_citations: list             # Tutor 节点引用来源列表
    tutor_evidence: list              # Tutor 节点实际引用的证据列表
    graph_anchor_id: str              # 当前课程图谱锚点 ID
    graph_anchor_title: str           # 当前课程图谱锚点
    graph_anchor_filename: str        # 当前课程图谱节点文件
    graph_prerequisites: list         # 当前节点前置知识
    graph_neighbors: list             # 当前节点关联知识
    graph_learning_objectives: list   # 当前节点学习目标
    graph_must_know: list             # 当前节点必会点
    graph_common_errors: list         # 当前节点常见误区
    graph_target_mastery_level: str   # 当前节点目标掌握层级
    graph_difficulty: str             # 当前节点难度标签
    graph_next_steps: list            # 当前节点推荐下一步
    message_history: list             # 用户侧对话记录，用于恢复时间线
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
    affect_signals: dict               # 最近一轮情绪信号 {frustrated: 0.8, curious: 0.4}
    llm_stream_disabled: bool          # 当前会话是否禁用流式输出
    llm_stream_failures: int           # 当前会话累计流式失败次数
    thinking_mode: bool                # 教学推理透明模式开关
    # ── 节点补救闭环状态 ──
    node_remediation_state: dict       # {original_score, variant_rounds, same_objective_failures, extra_count, status}
    remediation_decision: str          # 用户选择的补救决策: continue_variant/review_node/do_later/still_do_variant
    # ── 学习路径（Learning Plan）──
    learning_plan: list                # 多步学习计划 [{step_index, step_name, node_ids, status, reason, ...}]
    learning_plan_current_step: int    # 当前在学习路径的第几步
    learning_plan_generated_at: str    # 路径生成时间 ISO
    learning_plan_source: str          # 生成来源: "profile_based" | "resume_reuse" | "manual"


def build_initial_state(topic: str = "") -> AgentState:
    return {
        "learning_phase": "topic_init",
        "learning_resume_target": "intake_router",
        "learning_resume_reason": "new_session",
        "current_node_id": "",
        "current_node_name": "",
        "current_node_status": "",
        "next_node_candidate_id": "",
        "next_node_candidate_name": "",
        "node_quiz_items": [],
        "node_quiz_answers": {},
        "node_quiz_wrong_items": [],
        "node_quiz_score": 0,
        "node_content_context": "",
        "node_teaching_contract": {},
        "node_quiz_coverage_plan": [],
        "next_node_candidate_reason": "",
        "homework_items": [],
        "homework_answers": {},
        "homework_results": [],
        "homework_score": 0,
        "homework_status": "none",
        "homework_assignment_id": "",
        "student_state_snapshot": {},
        "learning_track": "",
        "learning_track_label": "",
        "learning_track_locked": False,
        "student_id": "default_student",
        "skip_reason": "",
        "interrupt_query": "",
        "resume_tester": False,
        "current_topic": topic,
        "current_user_goal": topic,
        "session_goal": topic,
        "turn_goal": topic,
        "proposed_topic": "",
        "topic_focus": "",
        "topic_background": "",
        "topic_detail_summary": "",
        "topic_starter_options": [],
        "topic_clarify_rounds": 0,
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
        "assessment_concept_gaps": {},
        "user_knowledge_graph": {},
        "assessment_state": {},
        "is_assessed": False,
        "flow_status": "greeting",
        "difficulty_level": 3,
        "attempt_count": 0,
        "score_history": [],
        "teaching_strategy": "explain",
        "next_step_choice": "",
        "post_lesson_choice": "",
        "continue_or_homework_choice": "",
        "post_eval_choice": "",
        "practice_generation_mode": "",
        "variant_questions": [],
        "wrong_question_explanations": [],
        "pending_interaction_kind": "",
        "pending_interaction_prompt": "",
        "pending_interaction_options": [],
        "pending_interaction_recommended": "",
        "pending_interaction_answer": "",
        "tutor_citations": [],
        "tutor_evidence": [],
        "graph_anchor_id": "",
        "graph_anchor_title": "",
        "graph_anchor_filename": "",
        "graph_prerequisites": [],
        "graph_neighbors": [],
        "graph_learning_objectives": [],
        "graph_must_know": [],
        "graph_common_errors": [],
        "graph_target_mastery_level": "",
        "graph_difficulty": "",
        "graph_next_steps": [],
        "message_history": (
            [{"role": "user", "kind": "topic_input", "content": topic}] if topic.strip() else []
        ),
        "model_answer": "",
        "misconceptions": [],
        "next_review_points": [],
        "is_correct_direction": True,
        "needs_hint": False,
        "coach_content": "",
        "conversation_history": [],
        "affect_signals": {},
        "llm_stream_disabled": False,
        "llm_stream_failures": 0,
        "thinking_mode": False,
        "node_remediation_state": {},
        "remediation_decision": "",
        "learning_plan": [],
        "learning_plan_current_step": 0,
        "learning_plan_generated_at": "",
        "learning_plan_source": "",
    }

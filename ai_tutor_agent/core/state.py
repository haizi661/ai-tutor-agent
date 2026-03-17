from typing import TypedDict, List, Dict, Any


class AgentState(TypedDict):
    current_topic: str
    proposed_topic: str
    tutor_content: str
    tester_question: str
    user_answer: str
    score: int
    logic_score: int
    concept_score: int
    feedback: str
    # ── 学前测评扩展字段 ──
    assessment_questions: list          # LLM 生成的 20 道题 JSON 列表
    assessment_answers: dict            # 用户前端提交的答题结果 {"1": "A", ...}
    assessment_radar: dict              # 6 维雷达图结构化数据
    assessment_result: str              # UserProfiler 生成的 Markdown 画像报告
    is_assessed: bool                   # 是否已完成学前画像评估
    flow_status: str                    # 图流转控制: greeting/topic_intake/meta_qa/smalltalk/topic_confirmation_pending/awaiting_topic_confirmation/awaiting_assessment/profiling/normal
    conversation_history: list          # 对话历史 [{"role":"user|assistant","kind":"...","content":"..."}]


def build_initial_state(topic: str = "") -> AgentState:
    return {
        "current_topic": topic,
        "proposed_topic": "",
        "tutor_content": "",
        "tester_question": "",
        "user_answer": "",
        "score": 0,
        "logic_score": 0,
        "concept_score": 0,
        "feedback": "",
        "assessment_questions": [],
        "assessment_answers": {},
        "assessment_radar": {},
        "assessment_result": "",
        "is_assessed": False,
        "flow_status": "greeting",
        "conversation_history": [],
    }

from typing import TypedDict


class AgentState(TypedDict):
    current_topic: str
    tutor_content: str
    tester_question: str
    user_answer: str
    score: int
    logic_score: int
    concept_score: int
    feedback: str
    # New fields for assessment
    assessment_questions: list[dict]
    assessment_answers: dict[int, str]
    assessment_result: str
    is_assessed: bool


def build_initial_state(topic: str) -> AgentState:
    return {
        "current_topic": topic,
        "tutor_content": "",
        "tester_question": "",
        "user_answer": "",
        "score": 0,
        "logic_score": 0,
        "concept_score": 0,
        "feedback": "",
        "assessment_questions": [],
        "assessment_answers": {},
        "assessment_result": "",
        "is_assessed": False,
    }

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
    }

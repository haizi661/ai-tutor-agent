from langchain_google_genai import ChatGoogleGenerativeAI

from ..config import Settings


def build_llms(settings: Settings):
    common = {
        "model": settings.model_name,
        "google_api_key": settings.google_api_key,
    }

    tutor_llm = ChatGoogleGenerativeAI(
        **common,
        temperature=settings.tutor_temperature,
    )
    tester_llm = ChatGoogleGenerativeAI(
        **common,
        temperature=settings.tester_temperature,
    )
    evaluator_llm = ChatGoogleGenerativeAI(
        **common,
        temperature=settings.evaluator_temperature,
    )
    return tutor_llm, tester_llm, evaluator_llm

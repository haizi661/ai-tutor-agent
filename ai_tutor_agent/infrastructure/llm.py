from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

from ..config import Settings


def build_llms(settings: Settings):
    if settings.llm_provider == "openai":
        def make_llm(temperature):
            kwargs = {
                "model": settings.model_name,
                "api_key": settings.openai_api_key,
                "temperature": temperature,
            }
            if settings.openai_api_base:
                kwargs["base_url"] = settings.openai_api_base
            return ChatOpenAI(**kwargs)
            
        tutor_llm = make_llm(settings.tutor_temperature)
        tester_llm = make_llm(settings.tester_temperature)
        evaluator_llm = make_llm(settings.evaluator_temperature)
        
    else: # Default to google
        def make_llm(temperature):
            return ChatGoogleGenerativeAI(
                model=settings.model_name,
                google_api_key=settings.google_api_key,
                temperature=temperature,
            )
            
        tutor_llm = make_llm(settings.tutor_temperature)
        tester_llm = make_llm(settings.tester_temperature)
        evaluator_llm = make_llm(settings.evaluator_temperature)

    return tutor_llm, tester_llm, evaluator_llm

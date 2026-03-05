from langchain_community.chat_models import ChatTongyi

from ..config import Settings


def build_llms(settings: Settings):
    # DashScope (Qwen) uses 'dashscope_api_key' and 'model'
    common = {
        "model_name": settings.model_name,
        "dashscope_api_key": settings.dashscope_api_key,
    }

    tutor_llm = ChatTongyi(
        **common,
        temperature=settings.tutor_temperature,
    )
    tester_llm = ChatTongyi(
        **common,
        temperature=settings.tester_temperature,
    )
    evaluator_llm = ChatTongyi(
        **common,
        temperature=settings.evaluator_temperature,
    )
    return tutor_llm, tester_llm, evaluator_llm

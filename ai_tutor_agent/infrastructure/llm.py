import httpx

from ..config import Settings


def _build_http_client(settings: Settings):
    proxy_url = settings.http_proxy or settings.https_proxy
    if not proxy_url:
        return None
    return httpx.Client(proxy=proxy_url)


def _build_openai_chat(settings: Settings, *, temperature: float, client=None):
    from langchain_openai import ChatOpenAI

    kwargs = {
        "model": settings.model_name,
        "api_key": settings.openai_api_key,
        "temperature": temperature,
    }
    if settings.openai_api_base:
        kwargs["base_url"] = settings.openai_api_base
    if client:
        kwargs["http_client"] = client
    return ChatOpenAI(**kwargs)


def _build_google_chat(settings: Settings, *, temperature: float, client=None):
    from langchain_google_genai import ChatGoogleGenerativeAI

    kwargs = {
        "model": settings.model_name,
        "google_api_key": settings.google_api_key,
        "temperature": temperature,
        "transport": "rest",
    }
    if client:
        kwargs["client"] = client
    return ChatGoogleGenerativeAI(**kwargs)


def build_retrieval_planner_llm(settings: Settings):
    client = _build_http_client(settings)
    if settings.llm_provider == "openai":
        return _build_openai_chat(settings, temperature=0.0, client=client)
    return _build_google_chat(settings, temperature=0.0, client=client)


def build_llms(settings: Settings):
    client = _build_http_client(settings)

    if settings.llm_provider == "openai":
        tutor_llm = _build_openai_chat(settings, temperature=settings.tutor_temperature, client=client)
        tester_llm = _build_openai_chat(settings, temperature=settings.tester_temperature, client=client)
        evaluator_llm = _build_openai_chat(settings, temperature=settings.evaluator_temperature, client=client)
    else:  # Default to google
        tutor_llm = _build_google_chat(settings, temperature=settings.tutor_temperature, client=client)
        tester_llm = _build_google_chat(settings, temperature=settings.tester_temperature, client=client)
        evaluator_llm = _build_google_chat(settings, temperature=settings.evaluator_temperature, client=client)

    return tutor_llm, tester_llm, evaluator_llm

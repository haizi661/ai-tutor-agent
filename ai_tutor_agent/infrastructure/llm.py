import httpx

from ..config import Settings


def build_llms(settings: Settings):
    # 构建全局代理客户端
    proxy_url = settings.http_proxy or settings.https_proxy
    client = None
    if proxy_url:
        client = httpx.Client(proxy=proxy_url)

    if settings.llm_provider == "openai":
        from langchain_openai import ChatOpenAI

        def make_llm(temperature):
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
            
        tutor_llm = make_llm(settings.tutor_temperature)
        tester_llm = make_llm(settings.tester_temperature)
        evaluator_llm = make_llm(settings.evaluator_temperature)
        
    else: # Default to google
        from langchain_google_genai import ChatGoogleGenerativeAI

        def make_llm(temperature):
            kwargs = {
                "model": settings.model_name,
                "google_api_key": settings.google_api_key,
                "temperature": temperature,
                "transport": "rest"
            }
            if client:
                kwargs["client"] = client
            return ChatGoogleGenerativeAI(**kwargs)
            
        tutor_llm = make_llm(settings.tutor_temperature)
        tester_llm = make_llm(settings.tester_temperature)
        evaluator_llm = make_llm(settings.evaluator_temperature)

    return tutor_llm, tester_llm, evaluator_llm

from __future__ import annotations

import socket
import urllib.parse

import httpx

from ..config import Settings, should_bypass_smart_proxy


def _needs_proxy(api_base: str | None) -> bool:
    if not api_base:
        return True
    try:
        parsed = urllib.parse.urlparse(api_base)
        host = parsed.hostname or api_base
    except Exception:
        return True
    return not should_bypass_smart_proxy(host)


def _proxy_reachable(proxy_url: str, timeout: float = 1.5) -> bool:
    try:
        parsed = urllib.parse.urlparse(proxy_url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 7897
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (OSError, socket.timeout):
        return False


def _build_http_client(settings: Settings):
    proxy_url = settings.http_proxy or settings.https_proxy
    if not proxy_url:
        return httpx.Client(trust_env=False, follow_redirects=True)
    if not _needs_proxy(settings.openai_api_base):
        # Domestic API — return an explicit no-proxy client so that the
        # OpenAI SDK ignores HTTP_PROXY / HTTPS_PROXY env vars.
        return httpx.Client(
            transport=httpx.HTTPTransport(), follow_redirects=True, trust_env=False
        )
    if not _proxy_reachable(proxy_url):
        print(f"⚠️ 代理 {proxy_url} 不可达，LLM 将直连（不走代理）。")
        return httpx.Client(trust_env=False, follow_redirects=True)
    return httpx.Client(proxy=proxy_url, trust_env=False)


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

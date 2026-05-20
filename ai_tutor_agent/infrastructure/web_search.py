from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx


@dataclass(frozen=True)
class WebSearchResult:
    title: str
    url: str
    domain: str
    snippet: str
    published_date: str = ""
    score: float = 0.0


class TavilySearchClient:
    def __init__(
        self,
        *,
        api_key: str,
        max_results: int = 5,
        proxy_url: str | None = None,
        timeout_seconds: float = 15.0,
    ) -> None:
        self.api_key = api_key.strip()
        self.max_results = max(1, int(max_results))
        client_kwargs: dict[str, Any] = {"timeout": timeout_seconds}
        if proxy_url:
            client_kwargs["proxy"] = proxy_url
        self._client = httpx.Client(**client_kwargs)

    def search(self, query: str, *, max_results: int | None = None) -> list[WebSearchResult]:
        cleaned_query = str(query or "").strip()
        if not cleaned_query:
            return []

        response = self._client.post(
            "https://api.tavily.com/search",
            json={
                "api_key": self.api_key,
                "query": cleaned_query,
                "max_results": max(1, int(max_results or self.max_results)),
                "search_depth": "advanced",
                "include_answer": False,
                "include_images": False,
                "include_raw_content": False,
            },
        )
        response.raise_for_status()
        payload = response.json()
        raw_results = payload.get("results", [])
        if not isinstance(raw_results, list):
            return []

        results: list[WebSearchResult] = []
        for item in raw_results:
            if not isinstance(item, dict):
                continue
            title = str(item.get("title") or "").strip()
            url = str(item.get("url") or "").strip()
            domain = str(item.get("domain") or "").strip()
            snippet = str(
                item.get("content")
                or item.get("snippet")
                or item.get("raw_content")
                or ""
            ).strip()
            if not url or not snippet:
                continue
            results.append(
                WebSearchResult(
                    title=title or domain or url,
                    url=url,
                    domain=domain,
                    snippet=snippet,
                    published_date=str(item.get("published_date") or "").strip(),
                    score=float(item.get("score") or 0.0),
                )
            )
        return results

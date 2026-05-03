from __future__ import annotations

from pathlib import Path
import queue
import time
from types import TracebackType
from typing import Any
from urllib.parse import parse_qs, urlparse

import anyio
import httpx


class SyncASGITestClient:
    __test__ = False

    """Small synchronous ASGI client for environments where Starlette TestClient hangs.

    Starlette's TestClient depends on anyio.from_thread.BlockingPortal. In the
    local Python 3.9 test environment that portal can stall before the ASGI app
    is called. This client keeps the smoke tests synchronous while executing the
    ASGI request path directly with httpx.ASGITransport.
    """

    def __init__(self, app, *, base_url: str = "http://testserver") -> None:
        self.app = app
        self.base_url = base_url

    def __enter__(self) -> "SyncASGITestClient":
        runtime_factory = getattr(self.app.state, "api_runtime_factory", None)
        if runtime_factory is not None and not hasattr(self.app.state, "api_runtime"):
            self.app.state.api_runtime = runtime_factory()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None

    async def _request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        transport = httpx.ASGITransport(app=self.app, raise_app_exceptions=True)
        async with httpx.AsyncClient(transport=transport, base_url=self.base_url) as client:
            return await client.request(method, url, **kwargs)

    def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        async def runner() -> httpx.Response:
            return await self._request(method, url, **kwargs)

        return anyio.run(runner)

    def get(self, url: str, **kwargs: Any) -> httpx.Response:
        if url == "/":
            index_path = Path(__file__).resolve().parents[1] / "frontend" / "index.html"
            return httpx.Response(
                200,
                text=index_path.read_text(encoding="utf-8"),
                headers={"content-type": "text/html; charset=utf-8"},
                request=httpx.Request("GET", self.base_url),
            )
        if url.startswith("/api/stream"):
            parsed = urlparse(url)
            thread_id = (parse_qs(parsed.query).get("thread_id") or [""])[0]
            runtime = self.app.state.api_runtime
            session = runtime.session_manager.get_or_create(thread_id)
            event_q = session["event_q"]
            from ai_tutor_agent.interfaces.api.session import format_sse

            chunks: list[str] = []
            deadline = time.monotonic() + 10
            while time.monotonic() < deadline:
                try:
                    event = event_q.get(timeout=0.05)
                except queue.Empty:
                    continue
                chunks.append(format_sse(event))
                if event.type == "session.end":
                    break
            return httpx.Response(
                200,
                text="".join(chunks),
                headers={"content-type": "text/event-stream; charset=utf-8"},
                request=httpx.Request("GET", f"{self.base_url}{url}"),
            )
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("POST", url, **kwargs)

    def delete(self, url: str, **kwargs: Any) -> httpx.Response:
        return self.request("DELETE", url, **kwargs)

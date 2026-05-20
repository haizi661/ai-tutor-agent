import os
import socket
from typing import Callable, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import router as config_router
from .error_correction import router as error_correction_router
from .history import messages_router, router as history_router
from .knowledge import router as knowledge_router
from .runtime import ApiRuntime, create_lifespan, get_frontend_dir
from .session import router as session_router
from ai_tutor_agent.ai_learning_path.ai_path_routes import (
    router as ai_path_bp,
)

def create_api_app(
    runtime_factory: Optional[Callable[[], ApiRuntime]] = None,
) -> FastAPI:
    app = FastAPI(lifespan=create_lifespan(runtime_factory))
    app.state.api_runtime_factory = runtime_factory

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health", tags=["meta"])
    async def healthcheck():
        return {"status": "ok"}

    app.include_router(config_router)
    app.include_router(error_correction_router)
    app.include_router(history_router)
    app.include_router(messages_router)
    app.include_router(knowledge_router)
    app.include_router(session_router)
    app.include_router(ai_path_bp)

    frontend_dir = get_frontend_dir()
    os.makedirs(frontend_dir, exist_ok=True)
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
    return app


app = create_api_app()

WEB_UI_PORT = 8000


def _is_port_available(host: str, port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind((host, port))
        return True
    except OSError:
        return False


def _ensure_api_port_available(host: str, port: int) -> None:
    if _is_port_available(host, port):
        return
    raise RuntimeError(
        f"Web UI 端口 {port} 已被占用。请先关闭旧服务后再启动；本项目固定使用 http://localhost:{port}。"
    )


def _display_host(host: str) -> str:
    return "localhost" if host in {"0.0.0.0", "::", ""} else host


def run_api():
    import uvicorn

    host = (os.getenv("AI_TUTOR_HOST") or "0.0.0.0").strip() or "0.0.0.0"
    port = WEB_UI_PORT
    _ensure_api_port_available(host, port)
    print(f"🚀 启动 Web UI: http://{_display_host(host)}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="warning")

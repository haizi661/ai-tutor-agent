import os
from typing import Callable, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .auth import router as auth_router
from .config import router as config_router
from .history import router as history_router
from .knowledge import router as knowledge_router
from .runtime import ApiRuntime, create_lifespan, get_frontend_dir
from .session import router as session_router


def create_api_app(
    runtime_factory: Optional[Callable[[], ApiRuntime]] = None,
) -> FastAPI:
    app = FastAPI(lifespan=create_lifespan(runtime_factory))

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

    app.include_router(auth_router)
    app.include_router(config_router)
    app.include_router(history_router)
    app.include_router(knowledge_router)
    app.include_router(session_router)

    frontend_dir = get_frontend_dir()
    os.makedirs(frontend_dir, exist_ok=True)
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
    return app


app = create_api_app()


def run_api():
    import uvicorn

    print("🚀 启动 Web UI: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")

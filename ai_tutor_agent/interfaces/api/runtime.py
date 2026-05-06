from __future__ import annotations

import os
import queue
import threading
from contextlib import asynccontextmanager
from dataclasses import dataclass, field, replace
from typing import Callable, Optional

from fastapi import FastAPI, Request

from ...config import Settings, apply_network_environment, get_settings
from ...core.ports import KnowledgeProvider, NoopKnowledgeProvider, RuntimeContext
from ...infrastructure.checkpoint import create_sqlite_checkpointer
from ...infrastructure.question_bank import LocalQuestionBankProvider
from ...infrastructure.retriever import LocalFileKnowledgeProvider
from ...knowledge_map.graph_rag_pipeline import GraphRAGPipeline
from ...knowledge_map.student_state import StudentStateStore
from ...platform_paths import resolve_project_path
from ...orchestration.workflow import create_app_with_sqlite_checkpointer


CHAT_PROFILES = {
    "gemini": {
        "id": "gemini",
        "label": "Gemini",
        "description": "Google Gemini via OpenAI-compatible endpoint.",
        "llm_provider": "openai",
        "default_model": "gemini-2.5-pro",
        "openai_api_base": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "models": [
            {"id": "gemini-2.5-pro", "label": "Gemini 2.5 Pro"},
            {"id": "gemini-2.5-flash", "label": "Gemini 2.5 Flash"},
            {"id": "gemini-2.5-flash-lite", "label": "Gemini 2.5 Flash-Lite"},
            {"id": "gemini-3-pro-preview", "label": "Gemini 3 Pro Preview"},
            {"id": "gemini-3-flash-preview", "label": "Gemini 3 Flash Preview"},
        ],
        "api_key_label": "Gemini API Key",
    },
    "qwen": {
        "id": "qwen",
        "label": "Qwen",
        "description": "Alibaba DashScope compatible endpoint.",
        "llm_provider": "openai",
        "default_model": "qwen-plus",
        "openai_api_base": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "models": [
            {"id": "qwen-max", "label": "Qwen Max"},
            {"id": "qwen-max-latest", "label": "Qwen Max Latest"},
            {"id": "qwen-plus", "label": "Qwen Plus"},
            {"id": "qwen-plus-latest", "label": "Qwen Plus Latest"},
            {"id": "qwen-turbo", "label": "Qwen Turbo"},
            {"id": "qwen-turbo-latest", "label": "Qwen Turbo Latest"},
            {"id": "qwen3-max-preview", "label": "Qwen3 Max Preview"},
        ],
        "api_key_label": "Qwen API Key",
    },
    "deepseek": {
        "id": "deepseek",
        "label": "DeepSeek",
        "description": "DeepSeek official OpenAI-compatible endpoint.",
        "llm_provider": "openai",
        "default_model": "deepseek-v4-flash",
        "openai_api_base": "https://api.deepseek.com/v1",
        "models": [
            {"id": "deepseek-v4-flash", "label": "DeepSeek V4 Flash"},
            {"id": "deepseek-v4-pro", "label": "DeepSeek V4 Pro"},
            {"id": "deepseek-chat", "label": "DeepSeek Chat (legacy)"},
            {"id": "deepseek-reasoner", "label": "DeepSeek Reasoner (legacy)"},
        ],
        "api_key_label": "DeepSeek API Key",
    },
    "openai": {
        "id": "openai",
        "label": "OpenAI",
        "description": "OpenAI official API endpoint.",
        "llm_provider": "openai",
        "default_model": "gpt-5-mini",
        "openai_api_base": "https://api.openai.com/v1",
        "models": [
            {"id": "gpt-5.1", "label": "GPT-5.1"},
            {"id": "gpt-5.4", "label": "GPT-5.4"},
            {"id": "gpt-5", "label": "GPT-5"},
            {"id": "gpt-5-mini", "label": "GPT-5 mini"},
            {"id": "gpt-5-nano", "label": "GPT-5 nano"},
            {"id": "gpt-4.1", "label": "GPT-4.1"},
            {"id": "gpt-4.1-mini", "label": "GPT-4.1 mini"},
            {"id": "gpt-4o", "label": "GPT-4o"},
            {"id": "gpt-4o-mini", "label": "GPT-4o mini"},
        ],
        "api_key_label": "OpenAI API Key",
    },
    "minimax": {
        "id": "minimax",
        "label": "MiniMax",
        "description": "MiniMax OpenAI-compatible endpoint.",
        "llm_provider": "openai",
        "default_model": "MiniMax-M2.5",
        "openai_api_base": "https://api.minimaxi.com/v1",
        "models": [
            {"id": "MiniMax-M2.5", "label": "MiniMax M2.5"},
            {"id": "MiniMax-M2.5-Highspeed", "label": "MiniMax M2.5 Highspeed"},
            {"id": "MiniMax-M2.1", "label": "MiniMax M2.1"},
            {"id": "MiniMax-M2.1-Highspeed", "label": "MiniMax M2.1 Highspeed"},
            {"id": "MiniMax-M2", "label": "MiniMax M2"},
        ],
        "api_key_label": "MiniMax API Key",
    },
    "glm": {
        "id": "glm",
        "label": "GLM",
        "description": "Zhipu GLM OpenAI-compatible endpoint.",
        "llm_provider": "openai",
        "default_model": "glm-5",
        "openai_api_base": "https://open.bigmodel.cn/api/paas/v4",
        "models": [
            {"id": "glm-5", "label": "GLM-5"},
            {"id": "glm-4.7", "label": "GLM-4.7"},
            {"id": "glm-4.7-flashx", "label": "GLM-4.7 FlashX"},
            {"id": "glm-4.7-flash", "label": "GLM-4.7 Flash"},
            {"id": "glm-4.6", "label": "GLM-4.6"},
            {"id": "glm-4.5-air", "label": "GLM-4.5 Air"},
            {"id": "glm-4.5-airx", "label": "GLM-4.5 AirX"},
        ],
        "api_key_label": "GLM API Key",
    },
    "custom": {
        "id": "custom",
        "label": "Custom",
        "description": "Manually configure provider/base URL/model.",
        "llm_provider": "openai",
        "default_model": "",
        "openai_api_base": "",
        "models": [],
        "api_key_label": "Custom API Key",
        "custom": True,
    },
}


def _base_matches(settings: Settings, pattern: str) -> bool:
    return pattern in (settings.openai_api_base or "")


def _profile_api_key(settings: Settings, profile_id: str) -> Optional[str]:
    if profile_id == "gemini":
        return (
            settings.gemini_api_key
            or settings.google_api_key
            or (settings.openai_api_key if _base_matches(settings, "generativelanguage.googleapis.com") else None)
        )
    if profile_id == "qwen":
        return settings.qwen_api_key
    if profile_id == "deepseek":
        return settings.deepseek_api_key
    if profile_id == "openai":
        return settings.openai_api_key if _base_matches(settings, "api.openai.com") or settings.chat_profile == "openai" else None
    if profile_id == "minimax":
        return settings.minimax_api_key
    if profile_id == "glm":
        return settings.glm_api_key
    return None


def build_chat_profiles(settings: Settings) -> list[dict]:
    profiles = []
    for profile_id, profile in CHAT_PROFILES.items():
        if profile.get("custom"):
            continue
        api_key = _profile_api_key(settings, profile_id)
        profiles.append(
            {
                **profile,
                "model_name": settings.model_name if settings.chat_profile == profile_id else profile["default_model"],
                "configured": bool(api_key),
            }
        )
    return profiles


def apply_chat_profile(settings: Settings, profile_id: str) -> Settings:
    profile = CHAT_PROFILES.get(profile_id)
    if profile is None or profile.get("custom"):
        raise ValueError(f"Unsupported profile: {profile_id}")

    api_key = _profile_api_key(settings, profile_id)
    if not api_key:
        raise RuntimeError(f"Profile {profile_id} is not configured on the server.")

    return replace(
        settings,
        chat_profile=profile_id,
        llm_provider=profile["llm_provider"],
        model_name=profile["default_model"],
        openai_api_base=profile["openai_api_base"],
        openai_api_key=api_key,
    )


def build_vendor_catalogs(settings: Settings) -> list[dict]:
    catalogs = []
    for vendor_id, vendor in CHAT_PROFILES.items():
        api_key = _profile_api_key(settings, vendor_id)
        catalogs.append(
            {
                "id": vendor_id,
                "label": vendor["label"],
                "description": vendor["description"],
                "configured": bool(api_key) if not vendor.get("custom") else True,
                "default_model": vendor["default_model"],
                "api_key_label": vendor["api_key_label"],
                "models": vendor["models"],
                "custom": bool(vendor.get("custom")),
            }
        )
    return catalogs


class SessionManager:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self.sessions: dict[str, dict[str, object]] = {}

    def get_or_create(self, thread_id: str) -> dict[str, object]:
        with self._lock:
            if thread_id not in self.sessions:
                self.sessions[thread_id] = {
                    "event_q": queue.Queue(),
                    "input_q": queue.Queue(),
                    "worker": None,
                    "is_running": False,
                    "awaiting_input": False,
                    "awaiting_input_state": None,
                }
            return self.sessions[thread_id]

    def refresh_status(self, thread_id: str) -> dict[str, object]:
        with self._lock:
            session = self.get_or_create(thread_id)
            worker = session.get("worker")
            if worker is not None and worker.ident is not None and not worker.is_alive():
                session["worker"] = None
                session["is_running"] = False
                session["awaiting_input"] = False
                session["awaiting_input_state"] = None
            return session

    def mark_running(self, thread_id: str, worker: threading.Thread) -> dict[str, object]:
        with self._lock:
            session = self.get_or_create(thread_id)
            session["worker"] = worker
            session["is_running"] = True
            session["awaiting_input"] = False
            session["awaiting_input_state"] = None
            return session

    def prepare_worker_start(self, thread_id: str, worker: threading.Thread) -> Optional[dict[str, object]]:
        with self._lock:
            session = self.refresh_status(thread_id)
            if session["is_running"]:
                return None
            session = self.reset_queues(thread_id)
            session["worker"] = worker
            session["is_running"] = True
            session["awaiting_input"] = False
            session["awaiting_input_state"] = None
            return session

    def mark_finished(self, thread_id: str) -> None:
        with self._lock:
            session = self.get_or_create(thread_id)
            session["worker"] = None
            session["is_running"] = False
            session["awaiting_input"] = False
            session["awaiting_input_state"] = None

    def mark_awaiting_input(
        self,
        thread_id: str,
        awaiting: bool,
        payload: Optional[dict[str, object]] = None,
    ) -> dict[str, object]:
        with self._lock:
            session = self.get_or_create(thread_id)
            session["awaiting_input"] = awaiting
            session["awaiting_input_state"] = payload if awaiting else None
            return session

    def remove(self, thread_id: str) -> None:
        with self._lock:
            self.sessions.pop(thread_id, None)

    def reset_queues(self, thread_id: str) -> dict[str, object]:
        with self._lock:
            session = self.get_or_create(thread_id)
            for queue_name in ("event_q", "input_q"):
                session_queue = session[queue_name]
                while True:
                    try:
                        session_queue.get_nowait()
                    except queue.Empty:
                        break
            session["awaiting_input"] = False
            session["awaiting_input_state"] = None
            return session


@dataclass
class ApiRuntime:
    settings: Settings
    knowledge_provider: KnowledgeProvider
    graph_rag_pipeline: GraphRAGPipeline | None = None
    student_state_store: StudentStateStore | None = None
    question_bank_provider: object | None = None
    session_manager: SessionManager = field(default_factory=SessionManager)
    workflow_factory: Callable[[Settings, Optional[RuntimeContext]], tuple[object, object]] = (
        create_app_with_sqlite_checkpointer
    )
    checkpoint_factory: Callable[[str], tuple[object, object]] = create_sqlite_checkpointer

    def update_settings(self, **changes) -> Settings:
        self.settings = replace(self.settings, **changes)
        return self.settings


def _build_readonly_knowledge_provider(settings: Settings) -> KnowledgeProvider:
    """只读加载已有普通 RAG 索引，禁止扫描 data/knowledge 和触发 MinerU。

    这个函数用于“知识图谱主库 + 普通 RAG 补充库”模式：
    - 主教学仍以 GraphRAGPipeline 为核心；
    - 普通 RAG 只尝试读取已经存在的 chroma_db / bm25_cache / retrieval_state；
    - 启动 main.py 时不扫描 data/knowledge，不解析 PDF，不上传 MinerU，不重建索引。
    """
    try:
        original_sync = getattr(LocalFileKnowledgeProvider, "_sync_knowledge_dir", None)
        original_add = getattr(LocalFileKnowledgeProvider, "add_local_file", None)
        original_parse = getattr(LocalFileKnowledgeProvider, "_parse_file", None)

        def _skip_sync(self):
            print("📚 Web: 普通补充资料 RAG 只读模式：跳过 data/knowledge 扫描，不触发 MinerU。")

        def _blocked_add(self, source_path: str):
            print(f"📚 Web: 普通补充资料 RAG 只读模式：忽略新增文件 {source_path}。")
            return {"success": False, "chunks": 0, "readonly": True}

        def _blocked_parse(self, file_path: str):
            raise RuntimeError("普通补充资料 RAG 当前为只读模式，禁止启动 MinerU 解析。")

        # 部分旧版 LocalFileKnowledgeProvider 会在 __init__ 中直接调用 _sync_knowledge_dir。
        # 临时猴子补丁可以阻断扫描；实例化完成后立即恢复，避免影响其他调试脚本。
        if original_sync is not None:
            LocalFileKnowledgeProvider._sync_knowledge_dir = _skip_sync
        if original_add is not None:
            LocalFileKnowledgeProvider.add_local_file = _blocked_add
        if original_parse is not None:
            LocalFileKnowledgeProvider._parse_file = _blocked_parse
        try:
            provider = LocalFileKnowledgeProvider(settings)
        finally:
            if original_sync is not None:
                LocalFileKnowledgeProvider._sync_knowledge_dir = original_sync
            if original_add is not None:
                LocalFileKnowledgeProvider.add_local_file = original_add
            if original_parse is not None:
                LocalFileKnowledgeProvider._parse_file = original_parse

        has_vector = bool(getattr(provider, "vector_store", None))
        if has_vector:
            print("📚 Web: 普通补充资料 RAG 已以只读方式加载已有索引。")
        else:
            print("⚠️ Web: 普通补充资料 RAG 只读加载完成，但未检测到可用向量库。")
        return provider
    except Exception as exc:
        print(f"⚠️ Web: 普通补充资料 RAG 只读加载失败，主流程继续使用知识图谱: {exc}")
        return NoopKnowledgeProvider()


def _build_graph_rag_pipeline(settings: Settings) -> GraphRAGPipeline | None:
    try:
        graph_llm_profile = settings.graph_rag_llm_profile or settings.chat_profile
        graph_rag_pipeline = GraphRAGPipeline(
            enable_llm=settings.graph_rag_enable_llm,
            llm_profile=graph_llm_profile,
        )
        mode = f"LLM={'开启' if settings.graph_rag_enable_llm else '关闭'}"
        print(f"🕸️ Web: 图谱搜索 2.2 已加载（{mode}, profile={graph_llm_profile or 'default'}）。")
        return graph_rag_pipeline
    except Exception as exc:
        print(f"⚠️ Web: 图谱搜索 2.2 加载失败，将只保留普通检索回退: {exc}")
        return None


def _build_question_bank_provider(settings: Settings):
    try:
        provider = LocalQuestionBankProvider(
            settings.question_bank_dir,
            course_id=settings.default_course_id,
        )
        print("🧾 Web: 本地题库 Provider 已加载。")
        return provider
    except Exception as exc:
        print(f"⚠️ Web: 本地题库 Provider 加载失败，将使用 AI/fallback 出题: {exc}")
        return None


def build_runtime(settings: Optional[Settings] = None) -> ApiRuntime:
    settings = settings or get_settings()
    apply_network_environment(settings)

    student_state_store = StudentStateStore()

    # 主库：知识图谱运行资产。
    graph_rag_pipeline = _build_graph_rag_pipeline(settings)

    # 补充库：只读加载已有普通 RAG 索引。
    # 注意：不会扫描 data/knowledge，不会解析 PDF，不会调用 MinerU。
    knowledge_provider = _build_readonly_knowledge_provider(settings)

    question_bank_provider = _build_question_bank_provider(settings)

    return ApiRuntime(
        settings=settings,
        knowledge_provider=knowledge_provider,
        graph_rag_pipeline=graph_rag_pipeline,
        student_state_store=student_state_store,
        question_bank_provider=question_bank_provider,
    )


def refresh_runtime(runtime: ApiRuntime) -> Settings:
    get_settings.cache_clear()
    runtime.settings = get_settings()
    apply_network_environment(runtime.settings)

    runtime.graph_rag_pipeline = _build_graph_rag_pipeline(runtime.settings)
    runtime.knowledge_provider = _build_readonly_knowledge_provider(runtime.settings)
    runtime.question_bank_provider = _build_question_bank_provider(runtime.settings)
    runtime.student_state_store = StudentStateStore()
    return runtime.settings


def create_lifespan(runtime_factory: Optional[Callable[[], ApiRuntime]] = None):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.api_runtime = runtime_factory() if runtime_factory else build_runtime()
        yield

    return lifespan


def get_runtime(request: Request) -> ApiRuntime:
    return request.app.state.api_runtime


def get_frontend_dir() -> str:
    return str(resolve_project_path("frontend"))


def serialize_runtime_config(settings: Settings) -> dict:
    current = {
        "chat_profile": settings.chat_profile,
        "llm_provider": settings.llm_provider,
        "model_name": settings.model_name,
        "openai_api_base": settings.openai_api_base or "",
    }
    return {
        **current,
        "current": current,
        "profiles": build_chat_profiles(settings),
        "vendors": build_vendor_catalogs(settings),
        "credentials": {
            "gemini": bool(_profile_api_key(settings, "gemini")),
            "qwen": bool(_profile_api_key(settings, "qwen")),
            "deepseek": bool(_profile_api_key(settings, "deepseek")),
            "openai": bool(_profile_api_key(settings, "openai")),
            "minimax": bool(_profile_api_key(settings, "minimax")),
            "glm": bool(_profile_api_key(settings, "glm")),
        },
        "managed_by": {
            "api_keys": ".env",
            "runtime_switchable": ["chat_profile"],
        },
    }

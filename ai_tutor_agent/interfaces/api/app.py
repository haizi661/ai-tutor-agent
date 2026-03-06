import queue
import threading
import tempfile
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, File, UploadFile, BackgroundTasks
from fastapi.responses import StreamingResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ...application.session import run_learning_session
from ...config import get_settings
from ...core.events import make_event
from ...core.ports import RuntimeContext
from ...infrastructure.retriever import LocalFileKnowledgeProvider
from ...orchestration.workflow import create_app_with_sqlite_checkpointer
from ..sse import format_sse
from .adapter import WebAnswerProvider, WebEventSink


class SessionManager:
    def __init__(self):
        self.sessions = {} # thread_id -> dict with queues and thread

    def get_or_create(self, thread_id: str):
        if thread_id not in self.sessions:
            self.sessions[thread_id] = {
                "event_q": queue.Queue(),
                "input_q": queue.Queue(),
                "worker": None,
                "is_running": False
            }
        return self.sessions[thread_id]

session_manager = SessionManager()

# Global state for knowledge provider
app_state = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    try:
        knowledge_provider = LocalFileKnowledgeProvider(settings)
        print("📚 Web: 知识库加载成功，已启用 RAG 增强。")
    except Exception as e:
        from ...core.ports import NoopKnowledgeProvider
        knowledge_provider = NoopKnowledgeProvider()
        print(f"⚠️ Web: 知识库加载失败: {e}")
        
    app_state["settings"] = settings
    app_state["knowledge_provider"] = knowledge_provider
    yield

app = FastAPI(lifespan=lifespan)

# Allow CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    thread_id: str
    topic: str = ""

def graph_worker(thread_id: str, topic: str, event_q: queue.Queue, input_q: queue.Queue):
    settings = app_state["settings"]
    knowledge_provider = app_state["knowledge_provider"]
    
    event_sink = WebEventSink(event_q)
    answer_provider = WebAnswerProvider(input_q, event_sink)
    
    runtime = RuntimeContext(
        event_sink=event_sink,
        answer_provider=answer_provider,
        knowledge_provider=knowledge_provider
    )
    
    graph_app, conn = create_app_with_sqlite_checkpointer(settings, runtime=runtime)
    
    try:
        current_state = graph_app.get_state({"configurable": {"thread_id": thread_id}})
        run_learning_session(
            graph_app,
            event_sink,
            thread_id=thread_id,
            topic=topic,
            current_state=current_state,
        )
    except Exception as e:
        event_sink.emit(make_event("session.error", "api", message=str(e)))
    finally:
        event_sink.emit(make_event("session.end", "api", message="Session ended."))
        conn.close()
        session_manager.sessions[thread_id]["is_running"] = False

@app.post("/api/start")
async def start_session(req: ChatRequest):
    sess = session_manager.get_or_create(req.thread_id)
    if not sess["is_running"]:
        sess["is_running"] = True
        worker = threading.Thread(
            target=graph_worker, 
            args=(req.thread_id, req.topic, sess["event_q"], sess["input_q"])
        )
        worker.daemon = True
        worker.start()
        sess["worker"] = worker
    return {"status": "started", "thread_id": req.thread_id}

@app.get("/api/stream")
async def stream_session(thread_id: str):
    sess = session_manager.get_or_create(thread_id)
    event_q = sess["event_q"]

    def event_generator():
        while True:
            event = event_q.get()
            yield format_sse(event)
            if event.type == "session.end":
                break

    return StreamingResponse(event_generator(), media_type="text/event-stream")

class AnswerRequest(BaseModel):
    thread_id: str
    answer: str

@app.post("/api/answer")
async def provide_answer(req: AnswerRequest):
    sess = session_manager.get_or_create(req.thread_id)
    sess["input_q"].put(req.answer)
    return {"status": "ok"}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    knowledge_provider = app_state.get("knowledge_provider")
    if not hasattr(knowledge_provider, "add_document"):
        return {"status": "error", "message": "Knowledge provider does not support uploads."}
        
    temp_dir = tempfile.mkdtemp()
    file_path = os.path.join(temp_dir, file.filename)
    with open(file_path, "wb") as buffer:
        content = await file.read()
        buffer.write(content)
        
    success = knowledge_provider.add_document(file_path)
    return {"status": "success" if success else "error", "filename": file.filename}

# Serve static files for frontend
# Ensure frontend dir exists
os.makedirs("frontend", exist_ok=True)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

def run_api():
    import uvicorn
    print("🚀 启动 Web UI: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="warning")

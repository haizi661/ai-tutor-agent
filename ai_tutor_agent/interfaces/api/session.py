import queue
import threading
import time
from typing import Dict

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ...application.session import run_learning_session
from ...core.events import make_event
from ...core.ports import RuntimeContext
from ..sse import format_sse
from .adapter import WebAnswerProvider, WebEventSink
from .runtime import get_runtime


router = APIRouter(prefix="/api", tags=["session"])

SSE_POLL_TIMEOUT_SECONDS = 15
RESUME_POLL_INTERVAL_SECONDS = 0.05
RESUME_POLL_TIMEOUT_SECONDS = 3


class ChatRequest(BaseModel):
    thread_id: str
    topic: str = ""


class AnswerRequest(BaseModel):
    thread_id: str
    answer: str


class AssessmentSubmitRequest(BaseModel):
    thread_id: str
    answers: Dict[str, str]


class TopicConfirmRequest(BaseModel):
    thread_id: str
    confirmed: bool
    topic: str = ""


class InterruptConfirmRequest(BaseModel):
    thread_id: str
    confirmed: bool


def _thread_config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


def _clear_interrupt_history(history: list) -> list:
    cleaned = []
    for msg in history or []:
        kind = str(msg.get("kind", ""))
        if kind in {"interruption", "interruption_user"}:
            continue
        if kind.startswith("interruption"):
            continue
        cleaned.append(msg)
    return cleaned


def _build_runtime_context(thread_id: str, runtime, event_q: queue.Queue, input_q: queue.Queue) -> RuntimeContext:
    event_sink = WebEventSink(event_q)
    answer_provider = WebAnswerProvider(
        input_q,
        event_sink,
        on_awaiting_input=lambda awaiting: runtime.session_manager.mark_awaiting_input(thread_id, awaiting),
    )
    return RuntimeContext(
        event_sink=event_sink,
        answer_provider=answer_provider,
        knowledge_provider=runtime.knowledge_provider,
    )


def _run_graph_session(
    thread_id: str,
    runtime,
    event_q: queue.Queue,
    input_q: queue.Queue,
    runner,
):
    runtime_context = _build_runtime_context(thread_id, runtime, event_q, input_q)
    graph_app, conn = runtime.workflow_factory(runtime.settings, runtime=runtime_context)
    thread_config = _thread_config(thread_id)

    try:
        runner(graph_app, runtime_context, thread_config)
    except Exception as exc:
        runtime_context.event_sink.emit(make_event("session.error", "api", message=str(exc)))
    finally:
        runtime_context.event_sink.emit(make_event("session.end", "api", message="Session ended."))
        conn.close()
        runtime.session_manager.mark_finished(thread_id)


def _graph_worker(thread_id: str, topic: str, runtime, event_q: queue.Queue, input_q: queue.Queue):
    def runner(graph_app, runtime_context, thread_config):
        current_state = graph_app.get_state(thread_config)
        run_learning_session(
            graph_app,
            runtime_context.event_sink,
            thread_id=thread_id,
            topic=topic,
            current_state=current_state,
        )

    _run_graph_session(thread_id, runtime, event_q, input_q, runner)


def _resume_assessment_worker(
    thread_id: str,
    answers: dict,
    runtime,
    event_q: queue.Queue,
    input_q: queue.Queue,
):
    def runner(graph_app, runtime_context, thread_config):
        graph_app.update_state(
            thread_config,
            {
                "assessment_answers": answers,
                "flow_status": "profiling",
            },
        )
        runtime_context.event_sink.emit(
            make_event(
                "session.info",
                "api",
                message="📝 已收到学前测评答案，正在生成能力画像…",
            )
        )
        graph_app.invoke(None, config=thread_config)

    _run_graph_session(thread_id, runtime, event_q, input_q, runner)


def _resume_topic_confirmation_worker(
    thread_id: str,
    confirmed: bool,
    topic: str,
    runtime,
    event_q: queue.Queue,
    input_q: queue.Queue,
):
    def runner(graph_app, runtime_context, thread_config):
        state = graph_app.get_state(thread_config).values or {}
        proposed_topic = state.get("proposed_topic", "").strip()
        next_topic = (topic or "").strip()

        if confirmed:
            confirmed_topic = proposed_topic or next_topic
            if not confirmed_topic:
                graph_app.update_state(
                    thread_config,
                    {
                        "current_topic": "",
                        "proposed_topic": "",
                        "flow_status": "greeting",
                    },
                )
                runtime_context.event_sink.emit(
                    make_event(
                        "session.info",
                        "api",
                        message="⚠️ 未检测到可确认的学习主题，请重新输入要学习的主题。",
                    )
                )
            else:
                graph_app.update_state(
                    thread_config,
                    {
                        "current_topic": confirmed_topic,
                        "proposed_topic": "",
                        "flow_status": "assessment_pending",
                    },
                )
                runtime_context.event_sink.emit(
                    make_event(
                        "session.info",
                        "api",
                        message=f"✅ 已确认学习主题：{confirmed_topic}",
                    )
                )
        else:
            graph_app.update_state(
                thread_config,
                {
                    "current_topic": next_topic,
                    "proposed_topic": "",
                    "flow_status": "greeting",
                },
            )
            runtime_context.event_sink.emit(
                make_event(
                    "session.info",
                    "api",
                    message="🔄 已退回主题确认阶段，请重新描述要学习的主题。",
                )
            )

        graph_app.invoke(None, config=thread_config)

    _run_graph_session(thread_id, runtime, event_q, input_q, runner)


def _resume_interrupt_confirmation_worker(
    thread_id: str,
    confirmed: bool,
    runtime,
    event_q: queue.Queue,
    input_q: queue.Queue,
):
    def runner(graph_app, runtime_context, thread_config):
        state = graph_app.get_state(thread_config).values or {}
        if confirmed:
            cleaned_history = _clear_interrupt_history(state.get("conversation_history", []))
            resume_tester = bool(state.get("tester_question"))
            graph_app.update_state(
                thread_config,
                {
                    "flow_status": "normal",
                    "interrupt_query": "",
                    "resume_tester": resume_tester,
                    "skip_reason": "",
                    "user_answer": "",
                    "conversation_history": cleaned_history,
                },
            )
            runtime_context.event_sink.emit(
                make_event(
                    "session.info",
                    "api",
                    message="✅ 已确认回到主线，继续教学与测评。",
                )
            )
            graph_app.invoke(None, config=thread_config)
        else:
            graph_app.update_state(
                thread_config,
                {"flow_status": "awaiting_interrupt_confirmation"},
            )
            runtime_context.event_sink.emit(
                make_event(
                    "session.info",
                    "api",
                    message="📝 你可以继续输入临时问题；完成后会再次询问是否回到主线。",
                    data={"requires_interrupt_confirmation": False},
                )
            )

    _run_graph_session(thread_id, runtime, event_q, input_q, runner)


def _start_worker(thread_id: str, runtime, target, *worker_args):
    thread_args = {}

    def runner():
        target(*thread_args["args"])

    worker = threading.Thread(target=runner, daemon=True)
    session = runtime.session_manager.prepare_worker_start(thread_id, worker)
    if session is None:
        return runtime.session_manager.refresh_status(thread_id)
    thread_args["args"] = (*worker_args, runtime, session["event_q"], session["input_q"])
    worker.start()
    return session


def _schedule_resume_worker(thread_id: str, runtime, target, *worker_args) -> str:
    session = runtime.session_manager.refresh_status(thread_id)
    if not session["is_running"]:
        _start_worker(thread_id, runtime, target, *worker_args)
        return "started"

    def delayed_resume():
        deadline = time.monotonic() + RESUME_POLL_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            current_session = runtime.session_manager.refresh_status(thread_id)
            if not current_session["is_running"]:
                _start_worker(thread_id, runtime, target, *worker_args)
                return
            time.sleep(RESUME_POLL_INTERVAL_SECONDS)

    watcher = threading.Thread(target=delayed_resume, daemon=True)
    watcher.start()
    return "scheduled"


@router.post("/start")
async def start_session(req: ChatRequest, request: Request):
    runtime = get_runtime(request)
    session = runtime.session_manager.refresh_status(req.thread_id)
    if session["is_running"] and session.get("awaiting_input") and req.topic.strip():
        session["input_q"].put(req.topic)
        runtime.session_manager.mark_awaiting_input(req.thread_id, False)
        return {"status": "continued", "thread_id": req.thread_id}
    if session["is_running"] and req.topic.strip():
        raise HTTPException(
            status_code=409,
            detail="Session is still processing the previous turn. Wait for the current step to finish before sending a new message.",
        )
    if not session["is_running"]:
        _start_worker(req.thread_id, runtime, _graph_worker, req.thread_id, req.topic)
        return {"status": "started", "thread_id": req.thread_id}
    return {"status": "running", "thread_id": req.thread_id}


@router.post("/sessions/{thread_id}/resume")
async def resume_session(thread_id: str, request: Request):
    runtime = get_runtime(request)
    session = runtime.session_manager.refresh_status(thread_id)
    if not session["is_running"]:
        _start_worker(thread_id, runtime, _graph_worker, thread_id, "")
        return {"status": "started", "thread_id": thread_id}
    return {"status": "running", "thread_id": thread_id}


@router.get("/stream")
async def stream_session(thread_id: str, request: Request):
    runtime = get_runtime(request)
    session = runtime.session_manager.get_or_create(thread_id)
    event_q = session["event_q"]

    def event_generator():
        while True:
            try:
                event = event_q.get(timeout=SSE_POLL_TIMEOUT_SECONDS)
            except queue.Empty:
                yield format_sse(make_event("session.ping", "api", message="keepalive"))
                continue
            yield format_sse(event)
            if event.type == "session.end":
                break

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/answer")
async def provide_answer(req: AnswerRequest, request: Request):
    runtime = get_runtime(request)
    session = runtime.session_manager.refresh_status(req.thread_id)
    if not session.get("awaiting_input"):
        raise HTTPException(status_code=409, detail="Session is not waiting for input.")
    session["input_q"].put(req.answer)
    runtime.session_manager.mark_awaiting_input(req.thread_id, False)
    return {"status": "ok"}


@router.post("/submit_assessment")
async def submit_assessment(req: AssessmentSubmitRequest, request: Request):
    runtime = get_runtime(request)
    _schedule_resume_worker(
        req.thread_id,
        runtime,
        _resume_assessment_worker,
        req.thread_id,
        req.answers,
    )
    return {"status": "ok", "message": "Assessment answers received, profiling started."}


@router.post("/confirm_topic")
async def confirm_topic(req: TopicConfirmRequest, request: Request):
    runtime = get_runtime(request)

    if not req.confirmed and not req.topic.strip():
        return {"status": "error", "message": "A revised topic is required when confirmation is rejected."}

    _schedule_resume_worker(
        req.thread_id,
        runtime,
        _resume_topic_confirmation_worker,
        req.thread_id,
        req.confirmed,
        req.topic,
    )
    return {"status": "ok", "message": "Topic confirmation received."}


@router.post("/confirm_interrupt")
async def confirm_interrupt(req: InterruptConfirmRequest, request: Request):
    runtime = get_runtime(request)
    _schedule_resume_worker(
        req.thread_id,
        runtime,
        _resume_interrupt_confirmation_worker,
        req.thread_id,
        req.confirmed,
    )
    return {"status": "ok", "message": "Interrupt confirmation received."}

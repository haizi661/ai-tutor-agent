import queue
import threading
from typing import Dict

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ...application.session import run_learning_session
from ...core.events import make_event
from ...core.ports import RuntimeContext
from ..sse import format_sse
from .adapter import WebAnswerProvider, WebEventSink
from .runtime import get_runtime


router = APIRouter(prefix="/api", tags=["session"])


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


def _graph_worker(thread_id: str, topic: str, runtime, event_q: queue.Queue, input_q: queue.Queue):
    runtime_context = _build_runtime_context(thread_id, runtime, event_q, input_q)
    graph_app, conn = runtime.workflow_factory(runtime.settings, runtime=runtime_context)

    try:
        current_state = graph_app.get_state({"configurable": {"thread_id": thread_id}})
        state_values = (current_state.values or {}) if current_state else {}

        # When resuming from topic confirmation, the newly sent chat text should be
        # consumed by answer_provider.get_answer() instead of being dropped.
        if topic.strip() and state_values.get("flow_status") == "awaiting_topic_confirmation":
            input_q.put(topic)

        run_learning_session(
            graph_app,
            runtime_context.event_sink,
            thread_id=thread_id,
            topic=topic,
            current_state=current_state,
        )
    except Exception as exc:
        runtime_context.event_sink.emit(make_event("session.error", "api", message=str(exc)))
    finally:
        runtime_context.event_sink.emit(make_event("session.end", "api", message="Session ended."))
        conn.close()
        runtime.session_manager.mark_finished(thread_id)


def _resume_assessment_worker(
    thread_id: str,
    answers: dict,
    runtime,
    event_q: queue.Queue,
    input_q: queue.Queue,
):
    runtime_context = _build_runtime_context(thread_id, runtime, event_q, input_q)
    graph_app, conn = runtime.workflow_factory(runtime.settings, runtime=runtime_context)
    thread_config = {"configurable": {"thread_id": thread_id}}

    try:
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
    except Exception as exc:
        runtime_context.event_sink.emit(make_event("session.error", "api", message=str(exc)))
    finally:
        runtime_context.event_sink.emit(make_event("session.end", "api", message="Session ended."))
        conn.close()
        runtime.session_manager.mark_finished(thread_id)


def _resume_topic_confirmation_worker(
    thread_id: str,
    confirmed: bool,
    topic: str,
    runtime,
    event_q: queue.Queue,
    input_q: queue.Queue,
):
    runtime_context = _build_runtime_context(thread_id, runtime, event_q, input_q)
    graph_app, conn = runtime.workflow_factory(runtime.settings, runtime=runtime_context)
    thread_config = {"configurable": {"thread_id": thread_id}}

    try:
        state = graph_app.get_state(thread_config).values or {}
        proposed_topic = state.get("proposed_topic", "").strip()
        next_topic = (topic or "").strip()

        if confirmed:
            confirmed_topic = proposed_topic or next_topic
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
    except Exception as exc:
        runtime_context.event_sink.emit(make_event("session.error", "api", message=str(exc)))
    finally:
        runtime_context.event_sink.emit(make_event("session.end", "api", message="Session ended."))
        conn.close()
        runtime.session_manager.mark_finished(thread_id)


def _resume_interrupt_confirmation_worker(
    thread_id: str,
    confirmed: bool,
    runtime,
    event_q: queue.Queue,
    input_q: queue.Queue,
):
    del input_q
    runtime_context = _build_runtime_context(thread_id, runtime, event_q, queue.Queue())
    graph_app, conn = runtime.workflow_factory(runtime.settings, runtime=runtime_context)
    thread_config = {"configurable": {"thread_id": thread_id}}

    try:
        if confirmed:
            state = graph_app.get_state(thread_config).values or {}
            cleaned_history = _clear_interrupt_history(state.get("conversation_history", []))
            graph_app.invoke(
                {
                    "flow_status": "normal",
                    "interrupt_query": "",
                    "resume_tester": False,
                    "skip_reason": "",
                    "user_answer": "",
                    "conversation_history": cleaned_history,
                },
                config=thread_config,
            )
            runtime_context.event_sink.emit(
                make_event(
                    "session.info",
                    "api",
                    message="✅ 已确认回到主线，继续教学与测评。",
                )
            )
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
    except Exception as exc:
        runtime_context.event_sink.emit(make_event("session.error", "api", message=str(exc)))
    finally:
        runtime_context.event_sink.emit(make_event("session.end", "api", message="Session ended."))
        conn.close()
        runtime.session_manager.mark_finished(thread_id)


def _start_worker(thread_id: str, runtime, target, *worker_args):
    session = runtime.session_manager.reset_queues(thread_id)
    worker = threading.Thread(
        target=target,
        args=(*worker_args, runtime, session["event_q"], session["input_q"]),
        daemon=True,
    )
    runtime.session_manager.mark_running(thread_id, worker)
    worker.start()
    return session


@router.post("/start")
async def start_session(req: ChatRequest, request: Request):
    runtime = get_runtime(request)
    session = runtime.session_manager.refresh_status(req.thread_id)
    if session["is_running"] and session.get("awaiting_input") and req.topic.strip():
        session["input_q"].put(req.topic)
        runtime.session_manager.mark_awaiting_input(req.thread_id, False)
        return {"status": "continued", "thread_id": req.thread_id}
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
            event = event_q.get()
            yield format_sse(event)
            if event.type == "session.end":
                break

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/answer")
async def provide_answer(req: AnswerRequest, request: Request):
    runtime = get_runtime(request)
    session = runtime.session_manager.refresh_status(req.thread_id)
    session["input_q"].put(req.answer)
    runtime.session_manager.mark_awaiting_input(req.thread_id, False)
    return {"status": "ok"}


@router.post("/submit_assessment")
async def submit_assessment(req: AssessmentSubmitRequest, request: Request):
    runtime = get_runtime(request)
    session = runtime.session_manager.refresh_status(req.thread_id)

    if not session["is_running"]:
        _start_worker(
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
    session = runtime.session_manager.refresh_status(req.thread_id)

    if not req.confirmed and not req.topic.strip():
        return {"status": "error", "message": "A revised topic is required when confirmation is rejected."}

    if not session["is_running"]:
        _start_worker(
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
    session = runtime.session_manager.refresh_status(req.thread_id)

    if not session["is_running"]:
        _start_worker(
            req.thread_id,
            runtime,
            _resume_interrupt_confirmation_worker,
            req.thread_id,
            req.confirmed,
        )

    return {"status": "ok", "message": "Interrupt confirmation received."}

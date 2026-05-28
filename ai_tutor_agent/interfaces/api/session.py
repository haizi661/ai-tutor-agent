import queue
import threading
import time
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ...application.session import run_learning_session
from ...core.events import make_event
from ...core.learning_flow import infer_resume_target
from ...core.ports import RuntimeContext
from ...core.state import build_initial_state
from ..sse import format_sse
from .adapter import WebAnswerProvider, WebEventSink
from .runtime import get_runtime


router = APIRouter(prefix="/api", tags=["session"])

SSE_POLL_TIMEOUT_SECONDS = 15
RESUME_POLL_INTERVAL_SECONDS = 0.05
RESUME_POLL_TIMEOUT_SECONDS = 3

PENDING_INTERACTION_FLOW_STATUSES = {
    "awaiting_next_step_selector",
    "awaiting_post_eval_selector",
    "awaiting_post_lesson_choice",
    "awaiting_temporary_question",
    "awaiting_objective_answers",
    "awaiting_variant_answers",
    "awaiting_remediation_decision",
    "awaiting_continue_or_homework_choice",
    "awaiting_consolidation_choice",
    "awaiting_homework_review_choice",
    "awaiting_homework_answers",
}


class ChatRequest(BaseModel):
    thread_id: str
    topic: str = ""


class CreateSessionRequest(BaseModel):
    thread_id: str


class LearningDirectionRequest(BaseModel):
    track: str
    label: Optional[str] = ""


class AnswerRequest(BaseModel):
    thread_id: str
    answer: str


class AssessmentSubmitRequest(BaseModel):
    thread_id: str
    answers: Dict[str, str]


class AssessmentDraftRequest(BaseModel):
    thread_id: str
    answers: Dict[str, str]


class AssessmentAnswerRequest(BaseModel):
    thread_id: str
    answer: str  # A/B/C/D


class TopicConfirmRequest(BaseModel):
    thread_id: str
    confirmed: bool
    topic: Optional[str] = ""
    start_mode: str = "assessment"


class InterruptConfirmRequest(BaseModel):
    thread_id: str
    confirmed: bool


class ThinkingModeRequest(BaseModel):
    thread_id: str
    thinking_mode: bool


def _thread_config(thread_id: str) -> dict:
    return {"configurable": {"thread_id": thread_id}}


LEARNING_DIRECTIONS = {
    "control_theory": {
        "track": "control_theory",
        "label": "自动控制原理",
        "topic": "自动控制原理",
    },
    "artificial_intelligence": {
        "track": "artificial_intelligence",
        "label": "人工智能",
        "topic": "人工智能学习路径",
    },
}

LEARNING_DIRECTION_ALIASES = {
    "control": "control_theory",
    "auto_control": "control_theory",
    "control_theory": "control_theory",
    "a2-control-theory": "control_theory",
    "自动控制": "control_theory",
    "自动控制原理": "control_theory",
    "ai": "artificial_intelligence",
    "artificial_intelligence": "artificial_intelligence",
    "artificial-intelligence": "artificial_intelligence",
    "人工智能": "artificial_intelligence",
}


def _normalize_learning_direction(track: str) -> dict:
    normalized = str(track or "").strip().lower()
    normalized = LEARNING_DIRECTION_ALIASES.get(normalized, normalized)
    if normalized not in LEARNING_DIRECTIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported learning direction: {track}")
    return LEARNING_DIRECTIONS[normalized]


def _append_learning_direction_history(history: list, direction: dict) -> list:
    track = direction["track"]
    label = direction["label"]
    filtered = [
        item
        for item in list(history or [])
        if not (
            isinstance(item, dict)
            and str(item.get("kind") or "").strip() in {"course_choice_card", "course_choice_selection"}
        )
    ]
    return filtered + [
        {
            "role": "assistant",
            "kind": "course_choice_card",
            "content": "请选择本次学习方向",
            "data": {
                "selected_track": track,
                "selected_label": label,
                "locked": True,
                "statusText": f"已选择：{label}",
                "options": [
                    {"track": "control_theory", "label": "自动控制原理"},
                    {"track": "artificial_intelligence", "label": "人工智能"},
                ],
            },
        },
        {
            "role": "user",
            "kind": "course_choice_selection",
            "content": label,
            "data": {"track": track, "label": label},
        },
    ]


def _checkpoint_state_patch(thread_id: str, runtime, patch: dict) -> None:
    runtime_context = RuntimeContext(
        knowledge_provider=runtime.knowledge_provider,
        settings=runtime.settings,
        graph_rag_pipeline=runtime.graph_rag_pipeline,
        student_state_store=runtime.student_state_store,
        question_bank_provider=getattr(runtime, "question_bank_provider", None),
    )
    graph_app, conn = runtime.workflow_factory(runtime.settings, runtime=runtime_context)
    try:
        graph_app.update_state(_thread_config(thread_id), patch)
    finally:
        conn.close()


def _checkpoint_exists(thread_id: str, runtime) -> bool:
    checkpoint_store, saver_conn = runtime.checkpoint_factory(runtime.settings.memory_db_path)
    try:
        return checkpoint_store.get_tuple(_thread_config(thread_id)) is not None
    finally:
        saver_conn.close()


def _ensure_thread_checkpoint(thread_id: str, runtime) -> bool:
    if _checkpoint_exists(thread_id, runtime):
        return False
    _checkpoint_state_patch(thread_id, runtime, build_initial_state(""))
    return True


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
        on_awaiting_input=lambda awaiting, payload=None: runtime.session_manager.mark_awaiting_input(
            thread_id,
            awaiting,
            payload,
        ),
    )
    return RuntimeContext(
        event_sink=event_sink,
        answer_provider=answer_provider,
        knowledge_provider=runtime.knowledge_provider,
        settings=runtime.settings,
        graph_rag_pipeline=runtime.graph_rag_pipeline,
        student_state_store=runtime.student_state_store,
        question_bank_provider=getattr(runtime, "question_bank_provider", None),
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
        import traceback
        tb = traceback.format_exc()
        print(f"[session:{thread_id}] Graph run error: {exc}\n{tb}")
        err_type = type(exc).__name__
        err_msg = str(exc).strip() or "未知错误"
        hint = ""
        if "Connection" in err_type or "connection" in err_msg.lower():
            hint = "\n💡 提示：LLM 服务连接失败，请检查网络或在设置中确认 API Key 和模型配置。"
        elif "auth" in err_msg.lower() or "api key" in err_msg.lower() or "401" in err_msg:
            hint = "\n💡 提示：API Key 无效或已过期，请在设置中更新。"
        elif "rate" in err_msg.lower() or "429" in err_msg:
            hint = "\n💡 提示：API 调用频率超限，请稍后重试。"
        runtime_context.event_sink.emit(
            make_event("session.error", "api", message=f"{err_msg}{hint}")
        )
    finally:
        end_data = {}
        try:
            final_state = graph_app.get_state(thread_config)
            values = dict(getattr(final_state, "values", {}) or {})
            pending_kind = str(values.get("pending_interaction_kind") or "").strip()
            if pending_kind or values.get("flow_status") in PENDING_INTERACTION_FLOW_STATUSES:
                end_data = {
                    "flow_status": values.get("flow_status", ""),
                    "pending_interaction_kind": pending_kind,
                    "interaction_kind": pending_kind,
                    "prompt": values.get("pending_interaction_prompt", ""),
                    "options": values.get("pending_interaction_options", []),
                    "recommended": values.get("pending_interaction_recommended", ""),
                }
                if pending_kind == "remediation_decision":
                    rem_state = values.get("node_remediation_state") or {}
                    wrong_explanations = values.get("wrong_question_explanations") or []
                    end_data["data"] = {
                        "score": rem_state.get("original_score", values.get("node_quiz_score", 0)),
                        "pass_score": 80,
                        "tier": "pass" if (rem_state.get("original_score", values.get("node_quiz_score", 0))) >= 80
                                else "partial" if (rem_state.get("original_score", values.get("node_quiz_score", 0))) >= 60
                                else "low",
                        "wrong_count": len(wrong_explanations) or len(values.get("node_quiz_wrong_items") or []),
                        "variant_rounds": rem_state.get("variant_rounds", 0),
                        "max_variant_rounds": 2,
                        "extra_remediation_question_count": rem_state.get("extra_remediation_question_count", 0),
                        "max_extra_questions": 10,
                        "same_objective_failures": rem_state.get("same_objective_failures", {}),
                        "paused": False,
                    }
        except Exception:
            end_data = {}
        runtime_context.event_sink.emit(make_event("session.end", "api", message="这一轮处理完成。", data=end_data))
        conn.close()
        runtime.session_manager.mark_finished(thread_id)


def _graph_worker(thread_id: str, topic: str, runtime, event_q: queue.Queue, input_q: queue.Queue):
    def runner(graph_app, runtime_context, thread_config):
        current_state = graph_app.get_state(thread_config)
        # Refresh student_state_snapshot from JSON to recover from server restarts
        # where the JSON file may be newer than the last checkpoint save.
        _store = getattr(runtime, "student_state_store", None)
        if _store is not None and current_state and current_state.values:
            try:
                _snap = _store.load(thread_id)
                if _snap is not None:
                    graph_app.update_state(
                        thread_config,
                        {"student_state_snapshot": _snap.to_dict()},
                    )
                    current_state = graph_app.get_state(thread_config)
            except Exception:
                pass  # best-effort; fall back to checkpoint snapshot
        run_learning_session(
            graph_app,
            runtime_context.event_sink,
            thread_id=thread_id,
            topic=topic,
            current_state=current_state,
            runtime_context=runtime_context,
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
                "learning_phase": "profile_complete",
                "learning_resume_target": "user_profiler",
                "learning_resume_reason": "assessment_submitted",
            },
        )
        runtime_context.event_sink.emit(
            make_event(
                "session.info",
                "api",
                message="📝 已收到学前测评答案，正在校准起点，随后直接进入讲解…",
            )
        )
        graph_app.invoke(None, config=thread_config)

    _run_graph_session(thread_id, runtime, event_q, input_q, runner)


def _resume_assessment_dialog_worker(
    thread_id: str,
    answer: str,
    runtime,
    event_q: queue.Queue,
    input_q: queue.Queue,
):
    def runner(graph_app, runtime_context, thread_config):
        graph_app.update_state(
            thread_config,
            {
                "pending_interaction_answer": answer,
                "flow_status": "assessment_dialog",
                "learning_phase": "pre_assessment",
                "learning_resume_target": "assessment_dialog",
                "learning_resume_reason": "assessment_dialog_answer",
            },
        )
        graph_app.invoke(None, config=thread_config)

    _run_graph_session(thread_id, runtime, event_q, input_q, runner)


def _resume_topic_confirmation_worker(
    thread_id: str,
    confirmed: bool,
    topic: str,
    start_mode: str,
    runtime,
    event_q: queue.Queue,
    input_q: queue.Queue,
):
    def runner(graph_app, runtime_context, thread_config):
        state = graph_app.get_state(thread_config).values or {}
        proposed_topic = state.get("proposed_topic", "").strip()
        current_goal = (state.get("current_user_goal") or "").strip()
        session_goal = (state.get("session_goal") or current_goal).strip()
        turn_goal = (state.get("turn_goal") or current_goal).strip()
        topic_focus = (state.get("topic_focus") or "").strip()
        topic_background = (state.get("topic_background") or "").strip()
        topic_detail_summary = (state.get("topic_detail_summary") or "").strip()
        topic_starter_options = list(state.get("topic_starter_options") or [])
        next_topic = (topic or "").strip()
        requested_mode = (start_mode or "assessment").strip().lower()
        if requested_mode not in {"assessment", "direct_tutor", "analogy_tutor"}:
            requested_mode = "assessment"

        if confirmed:
            # A topic may be confirmed only once, while later UI actions (for example
            # "先不测，直接开始" on an already-generated assessment card) reuse this
            # endpoint with start_mode=direct_tutor. In that resume path proposed_topic
            # has already been cleared, so fall back to the durable current/session
            # topic instead of treating the session as missing a topic.
            confirmed_topic = proposed_topic or next_topic or current_goal or session_goal or state.get("current_topic", "").strip()
            if not confirmed_topic:
                graph_app.update_state(
                    thread_config,
                    {
                        "current_topic": "",
                        "current_user_goal": "",
                        "proposed_topic": "",
                        "flow_status": "greeting",
                        "learning_phase": "topic_init",
                        "learning_resume_target": "greeter",
                        "learning_resume_reason": "missing_confirmed_topic",
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
                existing_message_history = list(state.get("message_history") or [])
                if requested_mode != "assessment":
                    existing_message_history = [
                        {
                            **item,
                            "data": {
                                **(item.get("data") or {}),
                                "locked": True,
                                "statusText": "已跳过学前测评，答案已固定",
                            },
                        }
                        if isinstance(item, dict) and item.get("kind") == "assessment_form"
                        else item
                        for item in existing_message_history
                    ]
                locked_label = {
                    "assessment": "已确认，开始摸底",
                    "direct_tutor": "已跳过摸底，直接开始",
                    "analogy_tutor": "已跳过摸底，示例入门",
                }[requested_mode]
                graph_app.update_state(
                    thread_config,
                    {
                        "current_topic": confirmed_topic,
                        "current_user_goal": current_goal or confirmed_topic,
                        "session_goal": session_goal or current_goal or confirmed_topic,
                        "turn_goal": turn_goal or topic_focus or current_goal or confirmed_topic,
                        "proposed_topic": "",
                        "flow_status": "assessment_pending" if requested_mode == "assessment" else "normal",
                        "learning_phase": "pre_assessment" if requested_mode == "assessment" else "node_selection",
                        "learning_resume_target": "assessment_generator" if requested_mode == "assessment" else "initial_node_selector",
                        "learning_resume_reason": "topic_confirmed",
                        "teaching_strategy": "analogy" if requested_mode == "analogy_tutor" else "explain",
                        "topic_focus": topic_focus,
                        "topic_background": topic_background,
                        "topic_detail_summary": topic_detail_summary,
                        "topic_starter_options": topic_starter_options,
                        "assessment_questions": [] if requested_mode != "assessment" else state.get("assessment_questions", []),
                        "assessment_answers": {} if requested_mode != "assessment" else state.get("assessment_answers", {}),
                        "assessment_state": {} if requested_mode != "assessment" else state.get("assessment_state", {}),
                        "message_history": existing_message_history + [
                            {
                                "role": "assistant",
                                "kind": "topic_confirmation_locked",
                                "content": f"学习主题【{confirmed_topic}】{locked_label}。",
                                "data": {"topic": confirmed_topic, "label": locked_label, "start_mode": requested_mode},
                            }
                        ],
                    },
                )
                start_message = {
                    "assessment": f"✅ 已确认学习主题：{confirmed_topic}。我们先快速摸一下起点，再开始正式讲解。",
                    "direct_tutor": f"✅ 已确认学习主题：{confirmed_topic}。跳过测评，我先从知识图谱选一个起点节点开始讲。",
                    "analogy_tutor": f"✅ 已确认学习主题：{confirmed_topic}。跳过测评，我先用更直观的例子从第一个节点带你入门。",
                }[requested_mode]
                runtime_context.event_sink.emit(
                    make_event(
                        "session.info",
                        "api",
                        message=start_message,
                    )
                )
        else:
            graph_app.update_state(
                thread_config,
                {
                    "current_topic": next_topic,
                    "current_user_goal": next_topic,
                    "session_goal": next_topic,
                    "turn_goal": next_topic,
                    "proposed_topic": "",
                    "topic_focus": "",
                    "topic_background": "",
                    "topic_detail_summary": "",
                    "topic_starter_options": [],
                    "topic_clarify_rounds": 0,
                    "flow_status": "greeting",
                    "learning_phase": "topic_init",
                    "learning_resume_target": "greeter",
                    "learning_resume_reason": "topic_rejected",
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
                    "learning_phase": "node_quiz_batch" if resume_tester else "node_teaching",
                    "learning_resume_target": "tester" if resume_tester else "next_step_selector",
                    "learning_resume_reason": "interrupt_confirmed",
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
                {
                    "flow_status": "awaiting_interrupt_confirmation",
                    "learning_phase": "node_temp_qna",
                    "learning_resume_target": "interruption_tutor",
                    "learning_resume_reason": "interrupt_followup_continues",
                },
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


def _resume_pending_interaction_worker(
    thread_id: str,
    answer: str,
    runtime,
    event_q: queue.Queue,
    input_q: queue.Queue,
):
    def runner(graph_app, runtime_context, thread_config):
        state = graph_app.get_state(thread_config).values or {}
        flow_status = str(state.get("flow_status", "") or "")
        if flow_status not in PENDING_INTERACTION_FLOW_STATUSES:
            runtime_context.event_sink.emit(
                make_event(
                    "session.warning",
                    "api",
                    message="当前没有可恢复的待处理交互。",
                )
            )
            return

        graph_app.invoke(
            {
                "pending_interaction_answer": answer,
                "learning_resume_target": infer_resume_target(state),
                "learning_resume_reason": "api_pending_interaction_answered",
            },
            config=thread_config,
        )

    _run_graph_session(thread_id, runtime, event_q, input_q, runner)


# Backward-compatible alias for older tests/imports that still use selector wording.
_resume_pending_selector_worker = _resume_pending_interaction_worker


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


@router.post("/sessions")
async def create_session(req: CreateSessionRequest, request: Request):
    runtime = get_runtime(request)
    thread_id = req.thread_id.strip()
    if not thread_id:
        raise HTTPException(status_code=400, detail="thread_id is required")
    created = _ensure_thread_checkpoint(thread_id, runtime)
    runtime.session_manager.get_or_create(thread_id)
    return {"status": "created" if created else "exists", "thread_id": thread_id}


@router.post("/sessions/{thread_id}/learning-direction")
async def set_learning_direction(thread_id: str, req: LearningDirectionRequest, request: Request):
    runtime = get_runtime(request)
    thread_id = thread_id.strip()
    if not thread_id:
        raise HTTPException(status_code=400, detail="thread_id is required")

    direction = dict(_normalize_learning_direction(req.track))
    if req.label and req.label.strip():
        direction["label"] = req.label.strip()

    _ensure_thread_checkpoint(thread_id, runtime)
    runtime.session_manager.get_or_create(thread_id)

    runtime_context = RuntimeContext(
        knowledge_provider=runtime.knowledge_provider,
        settings=runtime.settings,
        graph_rag_pipeline=runtime.graph_rag_pipeline,
        student_state_store=runtime.student_state_store,
        question_bank_provider=getattr(runtime, "question_bank_provider", None),
    )
    graph_app, conn = runtime.workflow_factory(runtime.settings, runtime=runtime_context)
    try:
        thread_config = _thread_config(thread_id)
        state = graph_app.get_state(thread_config).values or {}
        existing_flow_status = str(state.get("flow_status") or "greeting").strip() or "greeting"
        flow_status = (
            "ai_path_active"
            if direction["track"] == "artificial_intelligence"
            and existing_flow_status in {"greeting", "topic_intake", "meta_qa", "smalltalk"}
            else existing_flow_status
        )
        topic = str(state.get("current_topic") or "").strip()
        if not topic:
            topic = direction["topic"]

        graph_app.update_state(
            thread_config,
            {
                "learning_track": direction["track"],
                "learning_track_label": direction["label"],
                "learning_track_locked": True,
                "current_topic": topic,
                "current_user_goal": state.get("current_user_goal") or topic,
                "session_goal": state.get("session_goal") or topic,
                "turn_goal": state.get("turn_goal") or topic,
                "flow_status": flow_status,
                "message_history": _append_learning_direction_history(
                    state.get("message_history") or [],
                    direction,
                ),
            },
        )
    finally:
        conn.close()

    return {
        "status": "success",
        "thread_id": thread_id,
        "learning_track": direction["track"],
        "learning_track_label": direction["label"],
        "locked": True,
    }


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
        db_path = runtime.settings.memory_db_path
        checkpoint_store, saver_conn = runtime.checkpoint_factory(db_path)
        try:
            checkpoint_tuple = checkpoint_store.get_tuple(_thread_config(req.thread_id))
            state = checkpoint_tuple.checkpoint.get("channel_values", {}) if checkpoint_tuple else {}
        finally:
            saver_conn.close()

        if state.get("flow_status") in PENDING_INTERACTION_FLOW_STATUSES:
            _schedule_resume_worker(
                req.thread_id,
                runtime,
                _resume_pending_interaction_worker,
                req.thread_id,
                req.answer,
            )
            return {"status": "ok"}

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


@router.post("/assessment_draft")
async def save_assessment_draft(req: AssessmentDraftRequest, request: Request):
    runtime = get_runtime(request)
    _checkpoint_state_patch(
        req.thread_id,
        runtime,
        {"assessment_answers": req.answers},
    )
    return {"status": "ok", "message": "Assessment draft saved."}


@router.post("/assessment_answer")
async def assessment_answer(req: AssessmentAnswerRequest, request: Request):
    """对话式测评：用户逐题作答，每次提交一道题的答案。"""
    runtime = get_runtime(request)
    _schedule_resume_worker(
        req.thread_id,
        runtime,
        _resume_assessment_dialog_worker,
        req.thread_id,
        req.answer,
    )
    return {"status": "ok", "message": "Answer received, proceeding."}


@router.post("/confirm_topic")
async def confirm_topic(req: TopicConfirmRequest, request: Request):
    runtime = get_runtime(request)

    topic = (req.topic or "").strip()
    if not req.confirmed and not topic:
        return {"status": "error", "message": "A revised topic is required when confirmation is rejected."}

    _schedule_resume_worker(
        req.thread_id,
        runtime,
        _resume_topic_confirmation_worker,
        req.thread_id,
        req.confirmed,
        topic,
        req.start_mode,
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


@router.post("/sessions/{thread_id}/thinking-mode")
async def set_thinking_mode(thread_id: str, req: ThinkingModeRequest, request: Request):
    """Toggle teaching reasoning transparency mode on/off."""
    runtime = get_runtime(request)
    _checkpoint_state_patch(
        thread_id,
        runtime,
        {"thinking_mode": req.thinking_mode},
    )
    return {
        "status": "ok",
        "thinking_mode": req.thinking_mode,
        "message": "已切换到思考模式" if req.thinking_mode else "已切换到标准模式",
    }


@router.get("/students/{student_id}/knowledge-graph")
async def get_knowledge_graph(student_id: str, request: Request):
    """Return the user's knowledge graph — only nodes they have learned."""
    runtime = get_runtime(request)
    store = getattr(runtime, "student_state_store", None)
    if store is None:
        return {"knowledge_graph": {}, "summary": {"total": 0, "mastered": 0, "in_progress": 0}}
    try:
        student_state = store.load(student_id)
    except Exception:
        return {"knowledge_graph": {}, "summary": {"total": 0, "mastered": 0, "in_progress": 0}}
    kg = student_state.knowledge_graph if hasattr(student_state, "knowledge_graph") else {}
    mastered = sum(1 for v in kg.values() if v.get("status") == "mastered")
    in_progress = sum(1 for v in kg.values() if v.get("status") == "in_progress")
    return {
        "knowledge_graph": kg,
        "summary": {
            "total": len(kg),
            "mastered": mastered,
            "in_progress": in_progress,
        },
    }

from __future__ import annotations

import mimetypes
import threading
import time
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse, JSONResponse, Response

from ...infrastructure.matlab_experiment import MatlabExperimentService


router = APIRouter(prefix="/api/matlab-experiment", tags=["matlab-experiment"])
_service = MatlabExperimentService()
_jobs: dict[str, dict] = {}
_jobs_lock = threading.RLock()


def get_matlab_experiment_service() -> MatlabExperimentService:
    return _service


def _error_response(message: str, *, status_code: int = 400) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"status": "error", "message": message})


@router.get("/status")
async def get_matlab_experiment_status():
    return get_matlab_experiment_service().status()


@router.get("/records")
async def list_matlab_experiment_records():
    try:
        return get_matlab_experiment_service().list_records()
    except Exception as exc:
        return _error_response(str(exc), status_code=500)


@router.post("/records")
async def create_matlab_experiment_record(request: Request):
    payload = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    try:
        return get_matlab_experiment_service().create_record(
            title=str(payload.get("title") or ""),
            user_prompt=str(payload.get("user_prompt") or ""),
        )
    except Exception as exc:
        return _error_response(str(exc), status_code=500)


@router.get("/records/{record_id}")
async def get_matlab_experiment_record(record_id: str):
    try:
        return get_matlab_experiment_service().get_record(record_id)
    except FileNotFoundError:
        return _error_response("MATLAB experiment record not found.", status_code=404)
    except ValueError as exc:
        return _error_response(str(exc))
    except Exception as exc:
        return _error_response(str(exc), status_code=500)


@router.post("/run")
async def run_matlab_experiment(request: Request):
    payload = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    preset = str(payload.get("preset") or "first_order_step").strip()
    if preset != "first_order_step":
        return _error_response("Only the first_order_step preset is supported in this prototype.")

    try:
        return get_matlab_experiment_service().run_first_order_step(
            gain=float(payload.get("gain", 1.0)),
            time_constant=float(payload.get("time_constant", 1.0)),
            duration=float(payload.get("duration", 8.0)),
            step_size=float(payload.get("step_size", 0.02)),
            timeout_seconds=int(payload.get("timeout_seconds", 120)),
        )
    except ValueError as exc:
        return _error_response(str(exc))
    except RuntimeError as exc:
        return _error_response(str(exc), status_code=503)
    except Exception as exc:
        return _error_response(str(exc), status_code=500)


@router.post("/agent-run")
async def run_matlab_agent_experiment(request: Request):
    from .runtime import get_runtime

    runtime = get_runtime(request)
    payload = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    user_prompt = str(payload.get("user_prompt") or "").strip()
    if not user_prompt:
        return _error_response("user_prompt is required.")
    try:
        return get_matlab_experiment_service().run_agent_experiment(
            user_prompt=user_prompt,
            record_id=str(payload.get("record_id") or ""),
            settings=runtime.settings,
            max_iterations=int(payload.get("max_iterations", 3)),
            timeout_seconds=int(payload.get("timeout_seconds", 300)),
        )
    except ValueError as exc:
        return _error_response(str(exc))
    except RuntimeError as exc:
        return _error_response(str(exc), status_code=503)
    except Exception as exc:
        return _error_response(str(exc), status_code=500)


@router.post("/agent-jobs")
async def start_matlab_agent_job(request: Request):
    from .runtime import get_runtime

    runtime = get_runtime(request)
    payload = await request.json() if request.headers.get("content-type", "").startswith("application/json") else {}
    user_prompt = str(payload.get("user_prompt") or "").strip()
    if not user_prompt:
        return _error_response("user_prompt is required.")
    record_id = str(payload.get("record_id") or "").strip()

    job_id = f"matlab_job_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    with _jobs_lock:
        _jobs[job_id] = {
            "job_id": job_id,
            "status": "running",
            "trace": [],
            "result": None,
            "error": "",
            "record_id": record_id,
            "cancel_event": threading.Event(),
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }

    def append_trace(entry: dict) -> None:
        with _jobs_lock:
            job = _jobs.get(job_id)
            if not job:
                return
            job.setdefault("trace", []).append(entry)
            job["latest_phase"] = entry.get("phase", "")
            job["latest_message"] = entry.get("message", "")

    def worker() -> None:
        try:
            with _jobs_lock:
                cancel_event = _jobs[job_id]["cancel_event"]
            result = get_matlab_experiment_service().run_agent_experiment(
                user_prompt=user_prompt,
                record_id=record_id,
                settings=runtime.settings,
                max_iterations=int(payload.get("max_iterations", 3)),
                timeout_seconds=int(payload.get("timeout_seconds", 300)),
                progress_callback=append_trace,
                cancel_event=cancel_event,
            )
            with _jobs_lock:
                job = _jobs.get(job_id)
                if job:
                    if result.get("status") == "success":
                        job["status"] = "completed"
                    elif result.get("status") == "cancelled":
                        job["status"] = "cancelled"
                    else:
                        job["status"] = "failed"
                    job["result"] = result
                    job["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        except Exception as exc:
            with _jobs_lock:
                job = _jobs.get(job_id)
                if job:
                    job["status"] = "failed"
                    job["error"] = str(exc)
                    job["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")

    thread = threading.Thread(target=worker, name=f"matlab-agent-{job_id}", daemon=True)
    thread.start()
    return {"status": "success", "job_id": job_id}


@router.get("/agent-jobs/{job_id}")
async def get_matlab_agent_job(job_id: str):
    with _jobs_lock:
        job = dict(_jobs.get(job_id) or {})
    if not job:
        return _error_response("MATLAB agent job not found.", status_code=404)
    job.pop("cancel_event", None)
    return {"status": "success", **job}


@router.post("/agent-jobs/{job_id}/cancel")
async def cancel_matlab_agent_job(job_id: str):
    with _jobs_lock:
        job = _jobs.get(job_id)
        if not job:
            return _error_response("MATLAB agent job not found.", status_code=404)
        if job.get("status") not in {"running", "cancelling"}:
            safe_job = dict(job)
            safe_job.pop("cancel_event", None)
            return {"status": "success", **safe_job}
        cancel_event = job.get("cancel_event")
        if cancel_event is not None:
            cancel_event.set()
        job["status"] = "cancelling"
        job["latest_phase"] = "cancelled"
        job["latest_message"] = "已请求中断 MATLAB Agent。"
        job.setdefault("trace", []).append(
            {
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "phase": "cancelled",
                "message": "用户请求中断 MATLAB Agent。",
            }
        )
        safe_job = dict(job)
        safe_job.pop("cancel_event", None)
    return {"status": "success", **safe_job}


@router.get("/runs/{run_id}/report")
async def download_matlab_experiment_report(run_id: str):
    service = get_matlab_experiment_service()
    try:
        html = service.build_run_report_html(run_id)
    except ValueError as exc:
        return _error_response(str(exc))
    except FileNotFoundError:
        return _error_response("MATLAB experiment report not found.", status_code=404)
    safe_run_id = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in run_id)
    return Response(
        content=html,
        media_type="text/html; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{safe_run_id}_report.html"'},
    )


@router.get("/runs/{run_id}/assets/{filename:path}")
async def get_matlab_experiment_asset(run_id: str, filename: str):
    service = get_matlab_experiment_service()
    try:
        file_path = service.resolve_asset_path(run_id, filename)
    except ValueError as exc:
        return _error_response(str(exc))
    except FileNotFoundError:
        return _error_response("MATLAB experiment asset not found.", status_code=404)

    media_type, _ = mimetypes.guess_type(str(file_path))
    return FileResponse(
        file_path,
        media_type=media_type or "application/octet-stream",
        filename=file_path.name,
    )

from __future__ import annotations

import json
import html
import os
import re
import subprocess
import time
import uuid
import base64
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


Runner = Callable[..., subprocess.CompletedProcess[str]]


@dataclass(frozen=True)
class MatlabInstall:
    root: Path
    executable: Path
    available: bool


class MatlabExperimentService:
    """Run isolated MATLAB smoke experiments and collect machine-readable output."""

    def __init__(
        self,
        *,
        workspace_dir: str | Path = "data/matlab_experiments",
        matlab_root: str | Path | None = None,
        runner: Runner | None = None,
    ) -> None:
        self.workspace_dir = Path(workspace_dir)
        self.matlab_root = Path(
            matlab_root
            or os.getenv("AI_TUTOR_MATLAB_ROOT")
            or os.getenv("MATLABROOT")
            or "D:/MATLAB/R2024b"
        )
        self.runner = runner or subprocess.run
        self._environment_cache: dict[str, Any] | None = None

    def detect_install(self) -> MatlabInstall:
        candidates = [
            self.matlab_root / "bin" / "matlab.exe",
            self.matlab_root / "bin" / "win64" / "MATLAB.exe",
            self.matlab_root / "bin" / "matlab",
        ]
        for executable in candidates:
            if executable.exists():
                return MatlabInstall(
                    root=self.matlab_root,
                    executable=executable,
                    available=True,
                )
        return MatlabInstall(
            root=self.matlab_root,
            executable=candidates[0],
            available=False,
        )

    def status(self) -> dict[str, Any]:
        install = self.detect_install()
        environment = self.probe_environment(timeout_seconds=90) if install.available else {}
        return {
            "status": "success",
            "matlab_root": str(install.root),
            "matlab_executable": str(install.executable),
            "available": install.available,
            "workspace_dir": str(self.workspace_dir),
            "preset": "first_order_step",
            "environment": environment,
        }

    @property
    def records_index_path(self) -> Path:
        return self.workspace_dir / "matlab_records.json"

    def list_records(self) -> dict[str, Any]:
        records = self._read_records_index()
        indexed_ids = {str(item.get("record_id")) for item in records}
        for run_summary in sorted(
            self.workspace_dir.glob("matlab_agent_*/run_summary.json"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        ):
            try:
                payload = json.loads(run_summary.read_text(encoding="utf-8"))
            except Exception:
                continue
            record_id = str(payload.get("record_id") or f"run:{payload.get('run_id') or run_summary.parent.name}")
            if record_id in indexed_ids:
                continue
            indexed_ids.add(record_id)
            records.append(self._record_from_run_payload(payload, run_summary.parent))
        records.sort(key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""), reverse=True)
        return {"status": "success", "records": records}

    def create_record(self, *, title: str = "", user_prompt: str = "") -> dict[str, Any]:
        records = self._read_records_index()
        now = time.strftime("%Y-%m-%dT%H:%M:%S")
        record_id = f"matlab_record_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        prompt = str(user_prompt or "").strip()
        record = {
            "record_id": record_id,
            "title": str(title or "").strip() or self._title_from_prompt(prompt) or "新仿真",
            "created_at": now,
            "updated_at": now,
            "user_prompt": prompt,
            "runs": [],
            "status": "draft",
        }
        records.insert(0, record)
        self._write_records_index(records)
        return {"status": "success", "record": record}

    def get_record(self, record_id: str) -> dict[str, Any]:
        record_id = str(record_id or "").strip()
        if not record_id:
            raise ValueError("record_id is required.")
        record = self._find_record(record_id)
        if record is None and record_id.startswith("run:"):
            run_id = record_id.split(":", 1)[1]
            payload = self._load_run_summary(run_id)
            if payload:
                record = self._record_from_run_payload(payload, self.workspace_dir / run_id)
        if record is None:
            raise FileNotFoundError(record_id)
        runs = []
        for run_id in record.get("runs") or []:
            payload = self._load_run_summary(str(run_id))
            if payload:
                runs.append(payload)
        latest = runs[-1] if runs else None
        return {"status": "success", "record": record, "runs": runs, "latest": latest}

    def probe_environment(self, *, timeout_seconds: int = 90, force: bool = False) -> dict[str, Any]:
        if self._environment_cache is not None and not force:
            return self._environment_cache
        install = self.detect_install()
        if not install.available:
            return {"available": False, "error": f"MATLAB executable not found under {install.root}"}
        probe_id = f"matlab_probe_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        probe_dir = self.workspace_dir / probe_id
        probe_dir.mkdir(parents=True, exist_ok=True)
        result_path = probe_dir / "environment.json"
        script_path = probe_dir / "probe_environment.m"
        script_path.write_text(self._build_environment_probe_script(result_path), encoding="utf-8")
        try:
            execution = self._run_matlab_script(
                install=install,
                script_path=script_path,
                run_dir=probe_dir,
                timeout_seconds=timeout_seconds,
            )
        except Exception as exc:
            env = {"available": False, "error": str(exc), "returncode": None}
            self._write_json(result_path, env)
            self._environment_cache = env
            return env
        if execution["status"] != "success" or not result_path.exists():
            env = {
                "available": False,
                "error": execution.get("stderr") or execution.get("stdout") or execution.get("message"),
                "returncode": execution.get("returncode"),
                "execution": execution,
            }
            self._write_json(result_path, env)
            self._write_json(probe_dir / "probe_execution.json", execution)
            self._environment_cache = env
            return env
        env = json.loads(result_path.read_text(encoding="utf-8"))
        env["available"] = True
        self._environment_cache = env
        return env

    def _recover_last_successful_environment(self) -> dict[str, Any] | None:
        candidates = sorted(
            self.workspace_dir.glob("matlab_probe_*/environment.json"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        for path in candidates:
            try:
                env = json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            if env.get("available") is False:
                continue
            if not env.get("toolboxes") and not env.get("function_checks"):
                continue
            env["available"] = True
            env["source_environment_json"] = str(path)
            return env
        return None

    def run_first_order_step(
        self,
        *,
        gain: float = 1.0,
        time_constant: float = 1.0,
        duration: float = 8.0,
        step_size: float = 0.02,
        timeout_seconds: int = 120,
    ) -> dict[str, Any]:
        params = self._normalize_params(
            gain=gain,
            time_constant=time_constant,
            duration=duration,
            step_size=step_size,
        )
        install = self.detect_install()
        if not install.available:
            raise RuntimeError(f"MATLAB executable not found under {install.root}")

        run_id = f"matlab_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        run_dir = self.workspace_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        script_path = run_dir / "run_first_order_step.m"
        result_path = run_dir / "result.json"
        plot_path = run_dir / "step_response.png"
        script_path.write_text(
            self._build_first_order_script(
                params=params,
                result_path=result_path,
                plot_path=plot_path,
            ),
            encoding="utf-8",
        )

        started = time.monotonic()
        command = [
            str(install.executable),
            "-batch",
            f"run('{self._matlab_path(script_path)}')",
        ]
        try:
            completed = self.runner(
                command,
                cwd=str(run_dir),
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            elapsed_ms = int((time.monotonic() - started) * 1000)
            return {
                "status": "error",
                "run_id": run_id,
                "message": f"MATLAB execution timed out after {timeout_seconds} seconds.",
                "returncode": None,
                "stdout": exc.stdout or "",
                "stderr": exc.stderr or "",
                "elapsed_ms": elapsed_ms,
                "script_path": str(script_path),
            }
        elapsed_ms = int((time.monotonic() - started) * 1000)
        if completed.returncode != 0:
            return {
                "status": "error",
                "run_id": run_id,
                "message": "MATLAB execution failed.",
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "elapsed_ms": elapsed_ms,
                "script_path": str(script_path),
            }

        if not result_path.exists():
            return {
                "status": "error",
                "run_id": run_id,
                "message": "MATLAB finished but did not create result.json.",
                "returncode": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "elapsed_ms": elapsed_ms,
                "script_path": str(script_path),
            }

        result = json.loads(result_path.read_text(encoding="utf-8"))
        return {
            "status": "success",
            "run_id": run_id,
            "preset": "first_order_step",
            "parameters": params,
            "result": self._compact_result_for_response(result),
            "artifacts": {
                "script": f"/api/matlab-experiment/runs/{run_id}/assets/{script_path.name}",
                "result_json": f"/api/matlab-experiment/runs/{run_id}/assets/{result_path.name}",
                "plot_png": f"/api/matlab-experiment/runs/{run_id}/assets/{plot_path.name}" if plot_path.exists() else "",
            },
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "elapsed_ms": elapsed_ms,
        }

    def run_agent_experiment(
        self,
        *,
        user_prompt: str,
        record_id: str = "",
        settings: Any | None = None,
        max_iterations: int = 3,
        timeout_seconds: int = 300,
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
        cancel_event: Any | None = None,
    ) -> dict[str, Any]:
        prompt = str(user_prompt or "").strip()
        if not prompt:
            raise ValueError("user_prompt is required.")
        install = self.detect_install()
        if not install.available:
            raise RuntimeError(f"MATLAB executable not found under {install.root}")

        run_id = f"matlab_agent_{time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        run_dir = self.workspace_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        result_path = run_dir / "result.json"
        plot_path = run_dir / "result_plot.png"
        record_id = str(record_id or "").strip()
        if not record_id:
            record_id = str(self.create_record(user_prompt=prompt)["record"]["record_id"])
        continuation_context = self._build_continuation_context(record_id)

        attempts: list[dict[str, Any]] = []
        trace: list[dict[str, Any]] = []
        previous_code = ""
        previous_error = ""
        generated_notes = ""
        raw_environment = self.probe_environment(timeout_seconds=min(timeout_seconds, 120), force=True)
        environment = raw_environment
        if raw_environment.get("available") is not True:
            recovered_environment = self._recover_last_successful_environment()
            if recovered_environment:
                environment = {
                    **recovered_environment,
                    "probe_available": False,
                    "probe_error": raw_environment.get("error", ""),
                    "recovered_from_last_successful_probe": True,
                }
        environment_snapshot_path = run_dir / "environment.json"
        environment_snapshot_path.write_text(json.dumps(environment, ensure_ascii=False, indent=2), encoding="utf-8")

        def emit(phase: str, message: str, **data: Any) -> None:
            entry = {
                "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "phase": phase,
                "message": message,
                **data,
            }
            trace.append(entry)
            self._write_json(run_dir / "run_trace.json", trace)
            if progress_callback:
                progress_callback(entry)

        emit("start", "收到自然语言仿真需求，创建本地运行目录。", run_id=run_id)

        emit(
            "environment",
            "已完成 MATLAB 可用环境检查，后续代码生成会按当前工具箱授权约束执行。",
            toolbox_count=len(environment.get("toolboxes") or []),
            unavailable_functions=environment.get("unavailable_functions") or [],
        )

        for attempt_index in range(1, max(1, int(max_iterations)) + 1):
            if cancel_event is not None and cancel_event.is_set():
                emit("cancelled", "用户已中断 MATLAB Agent 流程。")
                payload = {
                    "status": "cancelled",
                    "run_id": run_id,
                    "record_id": record_id,
                    "mode": "agent",
                    "user_prompt": prompt,
                    "message": "MATLAB agent cancelled by user.",
                    "attempts": attempts,
                    "trace": trace,
                }
                self._write_json(run_dir / "run_summary.json", payload)
                self._append_run_to_record(record_id, payload)
                return payload
            emit("generate_code", f"第 {attempt_index} 轮：正在生成 MATLAB 仿真代码。", attempt=attempt_index)
            code_payload = self._generate_agent_matlab_code(
                user_prompt=prompt,
                settings=settings,
                run_dir=run_dir,
                result_path=result_path,
                default_plot_path=plot_path,
                previous_code=previous_code,
                previous_error=previous_error,
                attempt_index=attempt_index,
                environment=environment,
                continuation_context=continuation_context,
            )
            code = code_payload["code"]
            generated_notes = code_payload.get("notes", "")
            script_path = run_dir / f"simulation_attempt_{attempt_index}.m"
            script_path.write_text(code, encoding="utf-8")
            active_script_path = run_dir / "run_generated_simulation.m"
            active_script_path.write_text(code, encoding="utf-8")
            policy_error = self._validate_generated_code_against_environment(code, environment)
            attempt_audit_path = run_dir / f"attempt_{attempt_index}_execution.json"
            self._write_json(
                attempt_audit_path,
                {
                    "attempt": attempt_index,
                    "status": "generated",
                    "script_path": str(script_path),
                    "active_script_path": str(active_script_path),
                    "notes": generated_notes,
                    "policy_warning": policy_error,
                },
            )
            emit(
                "code_saved",
                f"第 {attempt_index} 轮：MATLAB 代码已保存。",
                attempt=attempt_index,
                script_name=script_path.name,
            )

            emit("execute", f"第 {attempt_index} 轮：正在调用 MATLAB 执行代码。", attempt=attempt_index)
            if cancel_event is not None and cancel_event.is_set():
                emit("cancelled", "用户已中断，MATLAB 执行前停止。", attempt=attempt_index)
                self._write_json(
                    attempt_audit_path,
                    {
                        "attempt": attempt_index,
                        "status": "cancelled",
                        "message": "Cancelled before MATLAB execution.",
                        "script_path": str(script_path),
                        "active_script_path": str(active_script_path),
                        "notes": generated_notes,
                        "policy_warning": policy_error,
                    },
                )
                payload = {
                    "status": "cancelled",
                    "run_id": run_id,
                    "record_id": record_id,
                    "mode": "agent",
                    "user_prompt": prompt,
                    "message": "MATLAB agent cancelled by user.",
                    "attempts": attempts,
                    "trace": trace,
                }
                self._write_json(run_dir / "run_summary.json", payload)
                self._append_run_to_record(record_id, payload)
                return payload
            if policy_error:
                emit(
                    "policy_warning",
                    f"第 {attempt_index} 轮：静态检查发现可能不可用的函数，但不会拦截；交由 MATLAB 实际执行验证。",
                    attempt=attempt_index,
                    error_summary=policy_error,
                )
            execution = self._run_matlab_script(
                install=install,
                script_path=active_script_path,
                run_dir=run_dir,
                timeout_seconds=timeout_seconds,
                cancel_event=cancel_event,
            )
            if execution["status"] == "cancelled":
                emit("cancelled", "用户已中断 MATLAB 执行。", attempt=attempt_index)
                self._write_json(
                    attempt_audit_path,
                    {
                        "attempt": attempt_index,
                        "status": "cancelled",
                        "script_path": str(script_path),
                        "active_script_path": str(active_script_path),
                        "notes": generated_notes,
                        "policy_warning": policy_error,
                        "execution": execution,
                    },
                )
                payload = {
                    "status": "cancelled",
                    "run_id": run_id,
                    "record_id": record_id,
                    "mode": "agent",
                    "user_prompt": prompt,
                    "message": execution.get("message", "MATLAB agent cancelled by user."),
                    "attempts": attempts,
                    "trace": trace,
                }
                self._write_json(run_dir / "run_summary.json", payload)
                self._append_run_to_record(record_id, payload)
                return payload
            png_paths = sorted(run_dir.glob("*.png"))
            has_result = result_path.exists()
            success = execution["status"] == "success" and has_result and bool(png_paths)
            attempt_record = {
                "attempt": attempt_index,
                "script": f"/api/matlab-experiment/runs/{run_id}/assets/{script_path.name}",
                "active_script": f"/api/matlab-experiment/runs/{run_id}/assets/{active_script_path.name}",
                "code": code,
                "status": "success" if success else "error",
                "returncode": execution.get("returncode"),
                "stdout": execution.get("stdout", ""),
                "stderr": execution.get("stderr", ""),
                "message": execution.get("message", ""),
                "notes": generated_notes,
                "policy_warning": policy_error,
            }
            attempts.append(attempt_record)
            self._write_json(
                attempt_audit_path,
                {
                    **attempt_record,
                    "script_path": str(script_path),
                    "active_script_path": str(active_script_path),
                    "result_json_exists": has_result,
                    "png_plots": [str(path) for path in png_paths],
                    "execution": execution,
                },
            )
            if success:
                emit(
                    "collect_results",
                    f"第 {attempt_index} 轮：MATLAB 执行成功，已收集 result.json 和图像。",
                    attempt=attempt_index,
                    plot_count=len(png_paths),
                )
                raw_result = json.loads(result_path.read_text(encoding="utf-8"))
                compact_result = self._compact_result_for_response(raw_result)
                plot_assets = [
                    f"/api/matlab-experiment/runs/{run_id}/assets/{path.name}"
                    for path in png_paths
                ]
                emit("analyze", "正在调用 MATLAB Agent 专属分析器解释实验结果。")
                analysis = self._analyze_agent_result(
                    user_prompt=prompt,
                    settings=settings,
                    result=compact_result,
                    plot_paths=png_paths,
                )
                emit("done", "MATLAB 仿真 Agent 流程完成。")
                payload = {
                    "status": "success",
                    "run_id": run_id,
                    "record_id": record_id,
                    "mode": "agent",
                    "user_prompt": prompt,
                    "attempts": attempts,
                    "trace": trace,
                    "result": compact_result,
                    "analysis": analysis,
                    "artifacts": {
                        "active_script": f"/api/matlab-experiment/runs/{run_id}/assets/{active_script_path.name}",
                        "environment": f"/api/matlab-experiment/runs/{run_id}/assets/{environment_snapshot_path.name}",
                        "result_json": f"/api/matlab-experiment/runs/{run_id}/assets/{result_path.name}",
                        "plots": plot_assets,
                    },
                }
                self._write_json(run_dir / "run_summary.json", payload)
                self._append_run_to_record(record_id, payload)
                return payload

            # Distinguish startup crashes from script-level errors.
            # A startup crash means MATLAB never reached the user script —
            # do NOT feed it to the LLM as a code bug.
            if self._is_startup_crash(execution):
                emit(
                    "execution_error",
                    f"第 {attempt_index} 轮：MATLAB 启动失败（{execution.get('elapsed_ms')}ms），"
                    "非脚本代码问题，将在下一轮直接重试运行而不是让 LLM 修改代码。",
                    attempt=attempt_index,
                    error_summary=execution.get("stderr", "")[-800:],
                )
                # Re-use the same code; keep previous_error empty so the LLM
                # does not try to "fix" the runtime environment.
                previous_code = ""
                previous_error = ""
            else:
                previous_code = code
                previous_error = "\n".join(
                    part
                    for part in [
                        execution.get("message", ""),
                        execution.get("stdout", ""),
                        execution.get("stderr", ""),
                        "result.json missing" if not has_result else "",
                        "png plot missing" if not png_paths else "",
                    ]
                    if part
                )
                emit(
                    "execution_error",
                    f"第 {attempt_index} 轮：MATLAB 执行未通过，准备把错误反馈给代码生成器修复。",
                    attempt=attempt_index,
                    error_summary=previous_error[-1200:],
                )

        emit("failed", "MATLAB Agent 达到最大重试次数，仍未得到完整仿真产物。")
        payload = {
            "status": "error",
            "run_id": run_id,
            "record_id": record_id,
            "mode": "agent",
            "user_prompt": prompt,
            "message": "MATLAB agent could not produce a successful simulation within the retry budget.",
            "attempts": attempts,
            "trace": trace,
        }
        self._write_json(run_dir / "run_summary.json", payload)
        self._append_run_to_record(record_id, payload)
        return payload

    def resolve_asset_path(self, run_id: str, filename: str) -> Path:
        safe_run_id = Path(run_id).name
        safe_filename = Path(filename).name
        path = (self.workspace_dir / safe_run_id / safe_filename).resolve()
        root = self.workspace_dir.resolve()
        if root not in path.parents:
            raise ValueError("Invalid MATLAB experiment asset path.")
        if not path.exists():
            raise FileNotFoundError(safe_filename)
        return path

    def build_run_report_html(self, run_id: str) -> str:
        safe_run_id = Path(str(run_id or "")).name
        if not safe_run_id:
            raise ValueError("run_id is required.")
        run_dir = (self.workspace_dir / safe_run_id).resolve()
        root = self.workspace_dir.resolve()
        if root not in run_dir.parents and run_dir != root:
            raise ValueError("Invalid MATLAB experiment run path.")
        summary = self._load_run_summary(safe_run_id)
        if not summary:
            raise FileNotFoundError(safe_run_id)

        def esc(value: Any) -> str:
            return html.escape(str(value if value is not None else ""), quote=True)

        def pretty_json(value: Any) -> str:
            return esc(json.dumps(value, ensure_ascii=False, indent=2, default=str))

        result = summary.get("result") or {}
        metrics = result.get("metrics") or {}
        trace = summary.get("trace") or []
        attempts = summary.get("attempts") or []
        artifacts = summary.get("artifacts") or {}
        plot_names: list[str] = []
        for href in [artifacts.get("plot_png"), *(artifacts.get("plots") or [])]:
            if href:
                plot_names.append(Path(str(href)).name)
        if not plot_names:
            plot_names = [path.name for path in sorted(run_dir.glob("*.png"))]
        plot_html = []
        for name in dict.fromkeys(plot_names):
            path = run_dir / name
            if not path.exists():
                continue
            try:
                src = self._image_to_data_uri(path)
            except Exception:
                continue
            plot_html.append(
                f'<figure><img src="{esc(src)}" alt="{esc(name)}"><figcaption>{esc(name)}</figcaption></figure>'
            )

        metric_rows = "".join(
            f"<tr><th>{esc(key)}</th><td>{esc(value)}</td></tr>"
            for key, value in metrics.items()
        ) or '<tr><td colspan="2">未提供关键指标。</td></tr>'
        trace_rows = "".join(
            "<tr>"
            f"<td>{esc(item.get('ts', ''))}</td>"
            f"<td>{esc(item.get('phase', ''))}</td>"
            f"<td>{esc(item.get('message', ''))}"
            + (f"<pre>{esc(item.get('error_summary'))}</pre>" if item.get("error_summary") else "")
            + "</td></tr>"
            for item in trace
            if isinstance(item, dict)
        ) or '<tr><td colspan="3">未记录执行过程。</td></tr>'
        attempt_blocks = []
        for item in attempts:
            if not isinstance(item, dict):
                continue
            log = "\n".join(
                str(part)
                for part in [
                    item.get("policy_warning", ""),
                    item.get("message", ""),
                    item.get("stderr", ""),
                    item.get("stdout", ""),
                ]
                if part
            )
            attempt_blocks.append(
                "<section class=\"attempt\">"
                f"<h3>第 {esc(item.get('attempt', '-'))} 次：{esc(item.get('status', 'unknown'))}</h3>"
                + (f"<pre>{esc(log)}</pre>" if log else "")
                + f"<pre>{esc(item.get('code') or '本次未返回代码内容。')}</pre>"
                "</section>"
            )
        attempts_html = "".join(attempt_blocks) or "<p>未记录代码尝试。</p>"

        raw_result_path = run_dir / "result.json"
        raw_result = ""
        if raw_result_path.exists():
            try:
                raw_result = raw_result_path.read_text(encoding="utf-8")
            except Exception:
                raw_result = ""

        return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>MATLAB 仿真报告 - {esc(safe_run_id)}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif; margin: 32px; color: #20212a; line-height: 1.65; }}
h1 {{ font-size: 24px; margin-bottom: 4px; }}
h2 {{ font-size: 18px; margin-top: 28px; border-bottom: 1px solid #d8d6e3; padding-bottom: 6px; }}
h3 {{ font-size: 15px; margin-top: 18px; }}
.meta {{ color: #666879; margin-bottom: 22px; }}
table {{ width: 100%; border-collapse: collapse; margin: 12px 0; }}
th, td {{ border: 1px solid #d8d6e3; padding: 8px 10px; vertical-align: top; text-align: left; }}
th {{ width: 220px; background: #f4f2f8; }}
pre {{ white-space: pre-wrap; word-break: break-word; background: #f7f6fa; border: 1px solid #d8d6e3; border-radius: 6px; padding: 12px; font-size: 12px; line-height: 1.5; }}
figure {{ margin: 14px 0 24px; border: 1px solid #d8d6e3; border-radius: 8px; padding: 10px; }}
img {{ max-width: 100%; height: auto; display: block; margin: 0 auto; }}
figcaption {{ margin-top: 8px; color: #666879; font-size: 13px; text-align: center; }}
.analysis {{ white-space: pre-wrap; background: #f4f2ff; border: 1px solid #c9c2ec; border-radius: 8px; padding: 14px; }}
</style>
</head>
<body>
<h1>MATLAB 仿真报告</h1>
<div class="meta">运行编号：{esc(safe_run_id)} · 状态：{esc(summary.get('status', 'unknown'))}</div>

<h2>一、仿真需求</h2>
<p>{esc(summary.get('user_prompt', '')) or '未记录仿真需求。'}</p>

<h2>二、执行过程</h2>
<table><thead><tr><th>时间</th><th>阶段</th><th>说明</th></tr></thead><tbody>{trace_rows}</tbody></table>

<h2>三、图表结果</h2>
{''.join(plot_html) or '<p>未生成图像文件。</p>'}

<h2>四、关键指标</h2>
<table><tbody>{metric_rows}</tbody></table>

<h2>五、结果分析</h2>
<div class="analysis">{esc(summary.get('analysis', '未记录分析。'))}</div>

<h2>六、MATLAB 代码与执行输出</h2>
{attempts_html}

<h2>七、原始 result.json</h2>
<pre>{esc(raw_result) if raw_result else pretty_json(result)}</pre>
</body>
</html>
"""

    @staticmethod
    def _write_json(path: Path, payload: Any) -> None:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    def _read_records_index(self) -> list[dict[str, Any]]:
        if not self.records_index_path.exists():
            return []
        try:
            payload = json.loads(self.records_index_path.read_text(encoding="utf-8"))
        except Exception:
            return []
        records = payload if isinstance(payload, list) else payload.get("records", [])
        return [item for item in records if isinstance(item, dict)]

    def _write_records_index(self, records: list[dict[str, Any]]) -> None:
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        self._write_json(self.records_index_path, {"records": records})

    @staticmethod
    def _title_from_prompt(prompt: str) -> str:
        text = re.sub(r"\s+", " ", str(prompt or "")).strip()
        if not text:
            return ""
        return text[:34] + ("..." if len(text) > 34 else "")

    def _find_record(self, record_id: str) -> dict[str, Any] | None:
        for record in self._read_records_index():
            if str(record.get("record_id") or "") == record_id:
                return record
        return None

    def _load_run_summary(self, run_id: str) -> dict[str, Any] | None:
        safe_run_id = Path(str(run_id or "")).name
        if not safe_run_id:
            return None
        summary_path = self.workspace_dir / safe_run_id / "run_summary.json"
        if not summary_path.exists():
            return None
        try:
            payload = json.loads(summary_path.read_text(encoding="utf-8"))
        except Exception:
            return None
        if isinstance(payload, dict):
            payload.setdefault("run_id", safe_run_id)
            return payload
        return None

    def _record_from_run_payload(self, payload: dict[str, Any], run_dir: Path) -> dict[str, Any]:
        run_id = str(payload.get("run_id") or run_dir.name)
        record_id = str(payload.get("record_id") or f"run:{run_id}")
        updated_at = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(run_dir.stat().st_mtime))
        prompt = str(payload.get("user_prompt") or "")
        return {
            "record_id": record_id,
            "title": self._title_from_prompt(prompt) or run_id,
            "created_at": updated_at,
            "updated_at": updated_at,
            "user_prompt": prompt,
            "runs": [run_id],
            "status": payload.get("status") or "unknown",
        }

    @staticmethod
    def _truncate_text(value: Any, limit: int) -> str:
        text = str(value or "")
        return text[-limit:] if len(text) > limit else text

    def _build_continuation_context(self, record_id: str) -> dict[str, Any]:
        if not record_id:
            return {}
        try:
            detail = self.get_record(record_id)
        except Exception:
            return {}
        runs = detail.get("runs") or []
        if not runs:
            return {}
        compact_runs: list[dict[str, Any]] = []
        for run in runs[-3:]:
            attempts = run.get("attempts") or []
            compact_attempts = []
            for attempt in attempts[-3:]:
                compact_attempts.append(
                    {
                        "attempt": attempt.get("attempt"),
                        "status": attempt.get("status"),
                        "message": self._truncate_text(attempt.get("message", ""), 1200),
                        "stderr": self._truncate_text(attempt.get("stderr", ""), 2000),
                        "notes": self._truncate_text(attempt.get("notes", ""), 1200),
                    }
                )
            latest_code = ""
            if attempts:
                latest_code = self._truncate_text(attempts[-1].get("code", ""), 12000)
            compact_runs.append(
                {
                    "run_id": run.get("run_id"),
                    "status": run.get("status"),
                    "user_prompt": run.get("user_prompt"),
                    "metrics": (run.get("result") or {}).get("metrics") or {},
                    "analysis": self._truncate_text(run.get("analysis", ""), 4000),
                    "attempts": compact_attempts,
                    "latest_code": latest_code,
                }
            )
        record = detail.get("record") or {}
        return {
            "record_id": record_id,
            "title": record.get("title", ""),
            "record_user_prompt": record.get("user_prompt", ""),
            "prior_runs": compact_runs,
            "instruction": (
                "This is a continuation of an existing MATLAB simulation record. "
                "Use the prior code, errors, metrics, and analysis as reference, "
                "then write a complete new script for the current run."
            ),
        }

    def _append_run_to_record(self, record_id: str, payload: dict[str, Any]) -> None:
        run_id = str(payload.get("run_id") or "")
        if not record_id or not run_id:
            return
        records = self._read_records_index()
        record = None
        for item in records:
            if str(item.get("record_id") or "") == record_id:
                record = item
                break
        if record is None:
            seed_runs: list[str] = []
            seed_payload: dict[str, Any] | None = None
            if record_id.startswith("run:"):
                seed_run_id = record_id.split(":", 1)[1]
                seed_payload = self._load_run_summary(seed_run_id)
                if seed_payload:
                    seed_runs.append(seed_run_id)
            record = {
                "record_id": record_id,
                "title": self._title_from_prompt(
                    str(payload.get("user_prompt") or (seed_payload or {}).get("user_prompt") or "")
                )
                or run_id,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "updated_at": "",
                "user_prompt": str(payload.get("user_prompt") or (seed_payload or {}).get("user_prompt") or ""),
                "runs": seed_runs,
                "status": "draft",
            }
            records.insert(0, record)
        runs = [str(item) for item in record.get("runs") or []]
        had_runs = bool(runs)
        if run_id not in runs:
            runs.append(run_id)
        prompt = str(payload.get("user_prompt") or "")
        record["runs"] = runs
        record["user_prompt"] = prompt or record.get("user_prompt", "")
        default_titles = {"New simulation", "新仿真"}
        if (
            not record.get("title")
            or str(record.get("title")) in default_titles
            or (not had_runs and record.get("status") == "draft")
        ):
            record["title"] = self._title_from_prompt(prompt) or run_id
        record["status"] = payload.get("status") or record.get("status") or "unknown"
        record["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        records.sort(key=lambda item: str(item.get("updated_at") or item.get("created_at") or ""), reverse=True)
        self._write_records_index(records)

    # Maximum retries for MATLAB startup failures (fast crashes before script runs)
    _STARTUP_RETRY_LIMIT = 2
    # If MATLAB exits this fast, it likely never reached the user script
    _STARTUP_CRASH_THRESHOLD_MS = 5000
    # Seconds to wait between startup retries
    _STARTUP_RETRY_DELAY_S = 3.0
    # Error patterns that indicate a MATLAB startup/runtime crash (not script bug)
    _STARTUP_CRASH_PATTERNS = [
        "Fatal Startup Error",
        "File system inconsistency",
        "failed to load settings",
        "System Error",
    ]

    @classmethod
    def _is_startup_crash(cls, execution: dict[str, Any]) -> bool:
        """Return True if the execution looks like a MATLAB runtime crash,
        not a user-script error."""
        elapsed = execution.get("elapsed_ms") or 0
        if elapsed >= cls._STARTUP_CRASH_THRESHOLD_MS:
            return False
        if execution.get("returncode") in (None, 0):
            return False
        stderr = str(execution.get("stderr") or "")
        return any(pattern.lower() in stderr.lower() for pattern in cls._STARTUP_CRASH_PATTERNS)

    def _run_matlab_script(
        self,
        *,
        install: MatlabInstall,
        script_path: Path,
        run_dir: Path,
        timeout_seconds: int,
        cancel_event: Any | None = None,
    ) -> dict[str, Any]:
        command = [
            str(install.executable),
            "-batch",
            f"run('{self._matlab_path(script_path)}')",
        ]

        for retry in range(self._STARTUP_RETRY_LIMIT + 1):
            started = time.monotonic()
            if cancel_event is not None and cancel_event.is_set():
                return {
                    "status": "cancelled",
                    "message": "MATLAB execution cancelled by user.",
                    "returncode": None,
                    "stdout": "",
                    "stderr": "",
                    "elapsed_ms": 0,
                }
            if cancel_event is not None and self.runner is subprocess.run:
                process = subprocess.Popen(
                    command,
                    cwd=str(run_dir),
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                try:
                    while process.poll() is None:
                        if cancel_event.is_set():
                            process.kill()
                            stdout, stderr = process.communicate(timeout=5)
                            return {
                                "status": "cancelled",
                                "message": "MATLAB execution cancelled by user.",
                                "returncode": process.returncode,
                                "stdout": stdout or "",
                                "stderr": stderr or "",
                                "elapsed_ms": int((time.monotonic() - started) * 1000),
                            }
                        if time.monotonic() - started > timeout_seconds:
                            process.kill()
                            stdout, stderr = process.communicate(timeout=5)
                            return {
                                "status": "error",
                                "message": f"MATLAB execution timed out after {timeout_seconds} seconds.",
                                "returncode": process.returncode,
                                "stdout": stdout or "",
                                "stderr": stderr or "",
                                "elapsed_ms": int((time.monotonic() - started) * 1000),
                            }
                        time.sleep(0.5)
                    stdout, stderr = process.communicate(timeout=5)
                except Exception:
                    process.kill()
                    raise
                elapsed_ms = int((time.monotonic() - started) * 1000)
                result = {
                    "status": "success" if process.returncode == 0 else "error",
                    "message": "" if process.returncode == 0 else "MATLAB execution failed.",
                    "returncode": process.returncode,
                    "stdout": stdout or "",
                    "stderr": stderr or "",
                    "elapsed_ms": elapsed_ms,
                }
            else:
                try:
                    completed = self.runner(
                        command,
                        cwd=str(run_dir),
                        text=True,
                        capture_output=True,
                        timeout=timeout_seconds,
                    )
                except subprocess.TimeoutExpired as exc:
                    elapsed_ms = int((time.monotonic() - started) * 1000)
                    result = {
                        "status": "error",
                        "message": f"MATLAB execution timed out after {timeout_seconds} seconds.",
                        "returncode": None,
                        "stdout": exc.stdout or "",
                        "stderr": exc.stderr or "",
                        "elapsed_ms": elapsed_ms,
                    }
                else:
                    elapsed_ms = int((time.monotonic() - started) * 1000)
                    result = {
                        "status": "success" if completed.returncode == 0 else "error",
                        "message": "" if completed.returncode == 0 else "MATLAB execution failed.",
                        "returncode": completed.returncode,
                        "stdout": completed.stdout,
                        "stderr": completed.stderr,
                        "elapsed_ms": elapsed_ms,
                    }

            # If MATLAB ran long enough to reach the user script, do not retry —
            # the error (if any) belongs to the generated code, not the runtime.
            if result["status"] == "success":
                return result
            if elapsed_ms >= self._STARTUP_CRASH_THRESHOLD_MS:
                return result

            # Fast crash: retry after a short delay to let transient file‑system
            # contention (preference dir locks, AV scanning) resolve.
            if retry < self._STARTUP_RETRY_LIMIT:
                time.sleep(self._STARTUP_RETRY_DELAY_S)

        return result

    def _generate_agent_matlab_code(
        self,
        *,
        user_prompt: str,
        settings: Any | None,
        run_dir: Path,
        result_path: Path,
        default_plot_path: Path,
        previous_code: str,
        previous_error: str,
        attempt_index: int,
        environment: dict[str, Any] | None = None,
        continuation_context: dict[str, Any] | None = None,
    ) -> dict[str, str]:
        fallback = {
            "code": self._build_agent_fallback_script(
                user_prompt=user_prompt,
                result_path=result_path,
                plot_path=default_plot_path,
            ),
            "notes": "fallback first-order simulation",
        }
        if settings is None:
            return fallback
        try:
            from langchain_core.messages import HumanMessage, SystemMessage

            tutor_llm = self._build_matlab_agent_llm(settings, temperature=0.1)
            system_msg = SystemMessage(
                content=(
                    "You are a MATLAB simulation coding agent. Generate one complete MATLAB script. "
                    "Return strict JSON only: {\"code\":\"...\",\"notes\":\"...\"}. "
                    "The script must be self-contained, must not require interactive UI, must run with matlab -batch, "
                    "must save numeric/raw results as JSON to the exact result_json path, and must save at least one PNG plot. "
                    "Use only local files under the provided run_dir. "
                    "Select the implementation strategy from the detected MATLAB environment: use available official toolboxes "
                    "when they materially improve correctness, clarity, or scientific standardness; fall back to base MATLAB "
                    "only for unavailable functions or when a toolbox adds no value."
                )
            )
            repair_block = ""
            if previous_code or previous_error:
                repair_block = (
                    "\nPrevious MATLAB code:\n"
                    f"{previous_code[-8000:]}\n\nPrevious error/output:\n{previous_error[-6000:]}\n"
                    "Revise the code to fix the failure while preserving the user's intent.\n"
                )
            continuation_block = ""
            if continuation_context:
                continuation_block = (
                    "\nExisting simulation record context:\n"
                    f"{json.dumps(continuation_context, ensure_ascii=False)[:14000]}\n"
                    "When the current user request modifies or extends that record, use this context as the baseline. "
                    "Keep useful prior modeling choices, correct prior mistakes, and generate a complete new MATLAB script "
                    "for the current run. Do not overwrite or depend on prior run directories.\n"
                )
            human_msg = HumanMessage(
                content=(
                    f"User simulation request:\n{user_prompt}\n\n"
                    f"run_dir: {self._matlab_path(run_dir)}\n"
                    f"result_json: {self._matlab_path(result_path)}\n"
                    f"default_plot_png: {self._matlab_path(default_plot_path)}\n"
                    f"attempt_index: {attempt_index}\n"
                    f"MATLAB environment JSON:\n{json.dumps(environment or {}, ensure_ascii=False)[:6000]}\n\n"
                    "Hard constraints from environment:\n"
                    "- If environment.probe_available is false, the latest MATLAB startup probe failed; do not treat that startup failure as proof that installed toolboxes are unavailable.\n"
                    "- If environment.recovered_from_last_successful_probe is true, use the recovered toolbox/function list as the best available capability snapshot.\n"
                    "- Use detected available toolboxes and functions deliberately; do not be unnecessarily conservative.\n"
                    "- Do not use functions listed in environment.unavailable_functions.\n"
                    "- If Control System Toolbox functions are available, prefer tf, ss, feedback, step, lsim, bode, margin, rlocus, c2d, d2c, and zpk for standard control-system workflows.\n"
                    "- If Signal Processing Toolbox is available, use it when the task involves filtering, spectra, sampled signals, or frequency-domain data processing.\n"
                    "- If System Identification Toolbox is available, use it for model estimation/validation tasks from input-output data.\n"
                    "- If Simulink or Simulink Control Design is available, use script-driven Simulink APIs only when the user explicitly asks for block-diagram/model-based simulation; otherwise prefer MATLAB scripts.\n"
                    "- If a useful function is unavailable, write a base-MATLAB replacement with analytic formulas, ode45, or explicit numerical integration.\n"
                    "- Always keep the script noninteractive and batch-safe: no open UI, no manual prompts, close figures, and write all artifacts under run_dir.\n"
                    "Required JSON fields inside result_json: model, parameters, metrics, series_preview or arrays. "
                    "Make the script robust: close figures, check file handles, and document which toolbox-backed functions are used in comments."
                    f"{continuation_block}"
                    f"{repair_block}"
                )
            )
            response = tutor_llm.invoke([system_msg, human_msg])
            raw = str(getattr(response, "content", response) or "")
            parsed = self._extract_json_object(raw)
            code = str(parsed.get("code") or "").strip()
            if not code:
                return fallback
            return {"code": code, "notes": str(parsed.get("notes") or "")}
        except Exception as exc:
            return {**fallback, "notes": f"{fallback['notes']}; LLM unavailable: {exc}"}

    def _analyze_agent_result(
        self,
        *,
        user_prompt: str,
        settings: Any | None,
        result: dict[str, Any],
        plot_paths: list[Path],
    ) -> str:
        fallback = (
            "仿真已完成。系统已保存 MATLAB 代码、result.json 和图像文件。"
            f"关键指标：{json.dumps(result.get('metrics') or {}, ensure_ascii=False)}"
        )
        qwen_api_key = None
        if settings is not None:
            qwen_api_key = getattr(settings, "qwen_api_key", None) or getattr(
                settings, "dashscope_api_key", None
            )
        if not qwen_api_key:
            return (
                f"{fallback}\n\n"
                "Qwen-VL 视觉分析暂不可用：未配置 QWEN_API_KEY 或 DASHSCOPE_API_KEY。"
            )
        try:
            from openai import OpenAI

            client = OpenAI(
                api_key=qwen_api_key,
                base_url=os.getenv(
                    "MATLAB_AGENT_VISION_BASE_URL",
                    "https://dashscope.aliyuncs.com/compatible-mode/v1",
                ),
                timeout=float(os.getenv("MATLAB_AGENT_VISION_TIMEOUT", "90")),
            )
            content: list[dict[str, Any]] = [
                {
                    "type": "text",
                    "text": (
                        "请以自动控制/系统仿真的科研实验报告风格，用中文分析本次 MATLAB 仿真结果。\n"
                        "输出格式必须是可直接放入实验报告的纯文本，不使用 Markdown 或富文本标记。\n"
                        "格式要求：\n"
                        "1. 禁止输出 #、##、**、__、```、$$、\\[、\\]、项目符号 emoji 等排版符号。\n"
                        "2. 小标题使用普通中文编号，例如“一、实验目的”“二、模型与参数”“三、图像判读”“四、关键指标”“五、结论与局限”。\n"
                        "3. 每个小标题后写 1 到 3 个完整自然段；不要使用 Markdown 列表。若必须列举，用“第一，第二，第三”写成句子。\n"
                        "4. 公式使用行内纯文本表达，例如 T(s)=10/(s^2+2s+15)，不要使用 LaTeX 环境、美元符号或反斜杠命令。\n"
                        "5. 指标必须说明单位或物理含义；图像判读必须基于传入图片中的曲线形态、峰值、振荡、稳定区间、频域特征或采样特征。\n"
                        "6. 如果结构化指标与图像不一致、命名不规范或计算可能有误，直接指出并给出修正建议。\n"
                        "7. 不编造未给出的实验条件；无法从图片或 JSON 判断的内容要明确说明。\n"
                        "8. 语言应严谨、克制、客观，不输出寒暄语，不写“以下是”。\n\n"
                        f"用户仿真需求：{user_prompt}\n"
                        f"结构化结果 JSON 摘要：{json.dumps(result, ensure_ascii=False)[:10000]}"
                    ),
                }
            ]
            for path in plot_paths[:3]:
                content.append(
                    {
                        "type": "image_url",
                        "image_url": {"url": self._image_to_data_uri(path)},
                    }
                )
            response = client.chat.completions.create(
                model=os.getenv("MATLAB_AGENT_VISION_MODEL", "qwen-vl-max"),
                temperature=0.2,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an independent MATLAB simulation result analyst for research workflows. "
                            "Use the provided plots and JSON data to write precise Chinese analysis. "
                            "Return plain report text only. Do not use Markdown headings, bold markers, code fences, "
                            "display-math delimiters, or raw LaTeX wrapper syntax. "
                            "This client is dedicated to MATLAB result analysis and must not affect other tutor prompts."
                        ),
                    },
                    {"role": "user", "content": content},
                ],
            )
            text = self._extract_openai_message_text(response).strip()
            return self._normalize_agent_analysis_text(text) or fallback
        except Exception as exc:
            return f"{fallback}\n\nQwen-VL 视觉分析暂不可用：{exc}"

    @staticmethod
    def _normalize_agent_analysis_text(text: str) -> str:
        """Remove presentation markup that is unsuitable for the plain report panel."""
        clean = str(text or "").strip()
        if not clean:
            return ""
        replacements = {
            "```": "",
            "$$": "",
            "\\[": "",
            "\\]": "",
            "**": "",
            "__": "",
        }
        for old, new in replacements.items():
            clean = clean.replace(old, new)
        lines: list[str] = []
        for raw_line in clean.splitlines():
            line = raw_line.strip()
            line = re.sub(r"^#{1,6}\s*", "", line)
            line = re.sub(r"^\s*[-*]\s+", "", line)
            line = re.sub(r"^\s*>\s*", "", line)
            lines.append(line)
        clean = "\n".join(lines)
        clean = re.sub(r"\n{3,}", "\n\n", clean)
        return clean.strip()

    @staticmethod
    def _extract_openai_message_text(response: Any) -> str:
        choices = getattr(response, "choices", None) or []
        if not choices:
            return ""
        message = getattr(choices[0], "message", None)
        content = getattr(message, "content", "") if message is not None else ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, dict):
                    text = item.get("text")
                else:
                    text = getattr(item, "text", None)
                if text:
                    parts.append(str(text))
            return "\n".join(parts)
        return str(content or "")

    @staticmethod
    def _build_matlab_agent_llm(settings: Any, *, temperature: float):
        from .llm import _build_http_client, _build_openai_chat, _build_google_chat

        client = _build_http_client(settings)
        if getattr(settings, "llm_provider", "") == "openai":
            return _build_openai_chat(settings, temperature=temperature, client=client)
        return _build_google_chat(settings, temperature=temperature, client=client)

    @staticmethod
    def _normalize_params(
        *,
        gain: float,
        time_constant: float,
        duration: float,
        step_size: float,
    ) -> dict[str, float]:
        params = {
            "gain": float(gain),
            "time_constant": float(time_constant),
            "duration": float(duration),
            "step_size": float(step_size),
        }
        if params["time_constant"] <= 0:
            raise ValueError("time_constant must be greater than 0.")
        if params["duration"] <= 0:
            raise ValueError("duration must be greater than 0.")
        if params["step_size"] <= 0:
            raise ValueError("step_size must be greater than 0.")
        if params["step_size"] > params["duration"]:
            raise ValueError("step_size must not exceed duration.")
        return params

    @staticmethod
    def _compact_result_for_response(result: dict[str, Any]) -> dict[str, Any]:
        """Keep the API response light; full arrays remain available in result.json."""
        time_values = result.get("time") if isinstance(result.get("time"), list) else []
        output_values = result.get("output") if isinstance(result.get("output"), list) else []
        existing_preview = result.get("series_preview") if isinstance(result.get("series_preview"), dict) else {}
        sample_count = min(len(time_values), len(output_values))
        if not sample_count and existing_preview:
            return {
                "metrics": result.get("metrics") or {},
                "model": result.get("model") or {},
                "parameters": result.get("parameters") or {},
                "series_preview": existing_preview,
            }
        if sample_count <= 120:
            sampled_time = time_values[:sample_count]
            sampled_output = output_values[:sample_count]
        else:
            stride = max(1, sample_count // 120)
            indices = list(range(0, sample_count, stride))
            if indices[-1] != sample_count - 1:
                indices.append(sample_count - 1)
            sampled_time = [time_values[index] for index in indices]
            sampled_output = [output_values[index] for index in indices]
        return {
            "metrics": result.get("metrics") or {},
            "model": result.get("model") or {},
            "parameters": result.get("parameters") or {},
            "series_preview": {
                "time": sampled_time,
                "output": sampled_output,
                "sample_count": sample_count,
            },
        }

    @staticmethod
    def _extract_json_object(raw: str) -> dict[str, Any]:
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}")
            if start >= 0 and end > start:
                return json.loads(text[start : end + 1])
            raise

    @staticmethod
    def _image_to_data_uri(path: Path) -> str:
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:image/png;base64,{encoded}"

    @classmethod
    def _build_agent_fallback_script(
        cls,
        *,
        user_prompt: str,
        result_path: Path,
        plot_path: Path,
    ) -> str:
        result_matlab_path = cls._matlab_path(result_path)
        plot_matlab_path = cls._matlab_path(plot_path)
        escaped_prompt = user_prompt.replace("'", "''")
        return f"""% Auto-generated fallback MATLAB agent script.
% User request: {escaped_prompt}
K = 1;
tau = 1;
duration = 8;
dt = 0.02;
t = 0:dt:duration;
y = 1 - exp(-t / tau);
fig = figure('Visible', 'off');
plot(t, y, 'LineWidth', 1.8);
grid on;
xlabel('Time (s)');
ylabel('Output y(t)');
title('Fallback first-order step response');
exportgraphics(fig, '{plot_matlab_path}', 'Resolution', 160);
close(fig);
result = struct();
result.model = struct('type', 'fallback_first_order', 'equation', 'y = 1 - exp(-t/tau)');
result.parameters = struct('K', K, 'tau', tau, 'duration', duration, 'dt', dt);
result.time = t;
result.output = y;
result.metrics = struct('final_value', y(end), 'steady_state_error', abs(1 - y(end)), 'sample_count', numel(t));
fid = fopen('{result_matlab_path}', 'w');
fwrite(fid, jsonencode(result), 'char');
fclose(fid);
"""

    @staticmethod
    def _build_environment_probe_script(result_path: Path) -> str:
        result_matlab_path = MatlabExperimentService._matlab_path(result_path)
        functions = [
            "tf",
            "step",
            "ss",
            "lsim",
            "bode",
            "feedback",
            "pid",
            "pidtune",
            "c2d",
            "d2c",
            "zpk",
            "tfdata",
            "margin",
            "rlocus",
            "ode45",
            "jsonencode",
            "exportgraphics",
        ]
        checks = "\n".join(
            f"function_checks.{name} = exist('{name}', 'file') > 0 || exist('{name}', 'builtin') > 0;"
            for name in functions
        )
        return f"""toolboxes = ver;
toolbox_names = {{toolboxes.Name}};
toolbox_versions = {{toolboxes.Version}};
function_checks = struct();
{checks}
result = struct();
result.version = version;
result.toolboxes = toolbox_names;
result.toolbox_versions = toolbox_versions;
result.function_checks = function_checks;
result.unavailable_functions = {{}};
names = fieldnames(function_checks);
for i = 1:numel(names)
    if ~function_checks.(names{{i}})
        result.unavailable_functions{{end+1}} = names{{i}};
    end
end
fid = fopen('{result_matlab_path}', 'w');
fwrite(fid, jsonencode(result), 'char');
fclose(fid);
"""

    @staticmethod
    def _validate_generated_code_against_environment(code: str, environment: dict[str, Any]) -> str:
        if environment.get("available") is not True:
            return ""
        unavailable = {str(item).lower() for item in (environment.get("unavailable_functions") or [])}
        control_functions = {
            "tf",
            "step",
            "ss",
            "lsim",
            "bode",
            "feedback",
            "pid",
            "pidtune",
            "c2d",
            "d2c",
            "zpk",
            "tfdata",
            "margin",
            "rlocus",
        }
        toolbox_names = {str(item).lower() for item in (environment.get("toolboxes") or [])}
        if toolbox_names and "control system toolbox" not in toolbox_names:
            unavailable.update(control_functions)
        lowered = code.lower()
        hits = [
            name
            for name in sorted(unavailable)
            if re.search(rf"(?<![a-zA-Z0-9_\.]){re.escape(name)}\s*\(", lowered)
        ]
        if not hits:
            return ""
        return (
            "Generated MATLAB code uses functions unavailable in the current MATLAB environment: "
            + ", ".join(hits)
            + ". Rewrite using base MATLAB, analytic formulas, ode45, or explicit numerical integration."
        )

    @staticmethod
    def _matlab_path(path: Path) -> str:
        return str(path.resolve()).replace("\\", "/").replace("'", "''")

    @classmethod
    def _build_first_order_script(
        cls,
        *,
        params: dict[str, float],
        result_path: Path,
        plot_path: Path,
    ) -> str:
        result_matlab_path = cls._matlab_path(result_path)
        plot_matlab_path = cls._matlab_path(plot_path)
        return f"""% Auto-generated by AI Tutor MATLAB experiment workbench.
K = {params['gain']:.12g};
tau = {params['time_constant']:.12g};
duration = {params['duration']:.12g};
dt = {params['step_size']:.12g};

t = 0:dt:duration;
y = zeros(size(t));
u = ones(size(t));
for k = 2:numel(t)
    dydt = (-y(k - 1) + K * u(k - 1)) / tau;
    y(k) = y(k - 1) + dt * dydt;
end

target = K;
final_value = y(end);
max_value = max(y);
steady_state_error = abs(target - final_value);
idx10 = find(y >= 0.1 * target, 1, 'first');
idx90 = find(y >= 0.9 * target, 1, 'first');
if isempty(idx10) || isempty(idx90)
    rise_time = NaN;
else
    rise_time = t(idx90) - t(idx10);
end
overshoot_percent = max(0, (max_value - target) / max(abs(target), eps) * 100);

fig = figure('Visible', 'off');
plot(t, y, 'LineWidth', 1.8);
grid on;
xlabel('Time (s)');
ylabel('Output y(t)');
title('First-order step response');
exportgraphics(fig, '{plot_matlab_path}', 'Resolution', 160);
close(fig);

result = struct();
result.time = t;
result.output = y;
result.input = u;
result.metrics = struct( ...
    'final_value', final_value, ...
    'steady_state_error', steady_state_error, ...
    'rise_time', rise_time, ...
    'overshoot_percent', overshoot_percent, ...
    'sample_count', numel(t) ...
);
result.model = struct('equation', 'dy/dt = (-y + K*u)/tau', 'gain', K, 'time_constant', tau);
fid = fopen('{result_matlab_path}', 'w');
fwrite(fid, jsonencode(result), 'char');
fclose(fid);
"""

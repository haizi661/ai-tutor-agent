from __future__ import annotations

import json
import shutil
import subprocess
import uuid
from pathlib import Path
from types import SimpleNamespace

from ai_tutor_agent.infrastructure.matlab_experiment import MatlabExperimentService
from ai_tutor_agent.interfaces.api.app import create_api_app
from asgi_test_client import SyncASGITestClient as TestClient


def _make_test_workspace() -> Path:
    root = Path("data/matlab_experiment_test_runtime") / uuid.uuid4().hex
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_matlab_experiment_status_detects_local_install():
    workspace = _make_test_workspace()
    root = workspace / "MATLAB" / "R2024b"
    executable = root / "bin" / "matlab.exe"
    executable.parent.mkdir(parents=True)
    executable.write_text("", encoding="utf-8")

    try:
        service = MatlabExperimentService(workspace_dir=workspace / "runs", matlab_root=root)

        status = service.status()

        assert status["status"] == "success"
        assert status["available"] is True
        assert status["matlab_executable"].endswith("matlab.exe")
        assert status["preset"] == "first_order_step"
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def test_matlab_experiment_run_collects_fake_matlab_result():
    workspace = _make_test_workspace()
    root = workspace / "MATLAB" / "R2024b"
    executable = root / "bin" / "matlab.exe"
    executable.parent.mkdir(parents=True)
    executable.write_text("", encoding="utf-8")

    def fake_runner(command, cwd, text, capture_output, timeout):
        del text, capture_output, timeout
        run_dir = Path(cwd)
        (run_dir / "result.json").write_text(
            json.dumps(
                {
                    "metrics": {
                        "final_value": 0.99,
                        "steady_state_error": 0.01,
                        "rise_time": 2.2,
                        "overshoot_percent": 0,
                        "sample_count": 401,
                    }
                }
            ),
            encoding="utf-8",
        )
        (run_dir / "step_response.png").write_bytes(b"png")
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    try:
        service = MatlabExperimentService(
            workspace_dir=workspace / "runs",
            matlab_root=root,
            runner=fake_runner,
        )

        payload = service.run_first_order_step(gain=2, time_constant=1.5, duration=5, step_size=0.05)

        assert payload["status"] == "success"
        assert payload["parameters"]["gain"] == 2
        assert payload["result"]["metrics"]["sample_count"] == 401
        assert payload["artifacts"]["script"].endswith("/run_first_order_step.m")
        assert payload["artifacts"]["plot_png"].endswith("/step_response.png")

        script_path = next((workspace / "runs").glob("*/run_first_order_step.m"))
        script = script_path.read_text(encoding="utf-8")
        assert "dy/dt = (-y + K*u)/tau" in script
        assert "jsonencode(result)" in script
        assert "exportgraphics" in script
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def test_matlab_experiment_run_reports_timeout():
    workspace = _make_test_workspace()
    root = workspace / "MATLAB" / "R2024b"
    executable = root / "bin" / "matlab.exe"
    executable.parent.mkdir(parents=True)
    executable.write_text("", encoding="utf-8")

    def timeout_runner(command, cwd, text, capture_output, timeout):
        del cwd, text, capture_output
        raise subprocess.TimeoutExpired(command, timeout, output="started", stderr="timeout")

    try:
        service = MatlabExperimentService(
            workspace_dir=workspace / "runs",
            matlab_root=root,
            runner=timeout_runner,
        )

        payload = service.run_first_order_step(timeout_seconds=1)

        assert payload["status"] == "error"
        assert "timed out" in payload["message"]
        assert payload["stdout"] == "started"
        assert payload["stderr"] == "timeout"
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def test_matlab_probe_failure_writes_environment_audit():
    workspace = _make_test_workspace()
    root = workspace / "MATLAB" / "R2024b"
    executable = root / "bin" / "matlab.exe"
    executable.parent.mkdir(parents=True)
    executable.write_text("", encoding="utf-8")

    def failing_runner(command, cwd, text, capture_output, timeout):
        del command, cwd, text, capture_output, timeout
        return subprocess.CompletedProcess("matlab", 1, stdout="", stderr="Fatal Startup Error")

    try:
        service = MatlabExperimentService(
            workspace_dir=workspace / "runs",
            matlab_root=root,
            runner=failing_runner,
        )

        env = service.probe_environment(force=True)

        assert env["available"] is False
        env_path = next((workspace / "runs").glob("matlab_probe_*/environment.json"))
        assert "Fatal Startup Error" in env_path.read_text(encoding="utf-8")
        assert next((workspace / "runs").glob("matlab_probe_*/probe_execution.json")).exists()
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def test_matlab_agent_run_uses_fallback_and_collects_artifacts():
    workspace = _make_test_workspace()
    root = workspace / "MATLAB" / "R2024b"
    executable = root / "bin" / "matlab.exe"
    executable.parent.mkdir(parents=True)
    executable.write_text("", encoding="utf-8")

    def fake_runner(command, cwd, text, capture_output, timeout):
        del text, capture_output, timeout
        run_dir = Path(cwd)
        (run_dir / "result.json").write_text(
            json.dumps(
                {
                    "time": [0, 1, 2],
                    "output": [0, 0.6, 0.9],
                    "metrics": {"final_value": 0.9, "sample_count": 3},
                    "model": {"type": "fake"},
                }
            ),
            encoding="utf-8",
        )
        (run_dir / "result_plot.png").write_bytes(b"png")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    try:
        service = MatlabExperimentService(workspace_dir=workspace / "runs", matlab_root=root, runner=fake_runner)

        payload = service.run_agent_experiment(user_prompt="仿真一个二阶系统", settings=None)

        assert payload["status"] == "success"
        assert payload["mode"] == "agent"
        assert payload["attempts"][0]["status"] == "success"
        assert payload["artifacts"]["active_script"].endswith("/run_generated_simulation.m")
        assert payload["artifacts"]["environment"].endswith("/environment.json")
        assert payload["artifacts"]["plots"][0].endswith("/result_plot.png")
        assert payload["result"]["series_preview"]["sample_count"] == 3
        assert "仿真已完成" in payload["analysis"]
        run_dir = next((workspace / "runs").glob("matlab_agent_*"))
        assert (run_dir / "environment.json").exists()
        assert (run_dir / "run_trace.json").exists()
        assert (run_dir / "run_summary.json").exists()
        assert (run_dir / "attempt_1_execution.json").exists()
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def test_matlab_agent_repairs_after_execution_error():
    workspace = _make_test_workspace()
    root = workspace / "MATLAB" / "R2024b"
    executable = root / "bin" / "matlab.exe"
    executable.parent.mkdir(parents=True)
    executable.write_text("", encoding="utf-8")

    class RepairService(MatlabExperimentService):
        def _generate_agent_matlab_code(self, **kwargs):
            if kwargs["attempt_index"] == 1:
                return {"code": "bad_symbol", "notes": "bad"}
            assert "Undefined function" in kwargs["previous_error"]
            return {"code": "fixed_code", "notes": "fixed"}

    def fake_runner(command, cwd, text, capture_output, timeout):
        del command, text, capture_output, timeout
        run_dir = Path(cwd)
        code = (run_dir / "run_generated_simulation.m").read_text(encoding="utf-8")
        if "bad_symbol" in code:
            return subprocess.CompletedProcess("matlab", 1, stdout="", stderr="Undefined function 'bad_symbol'.")
        (run_dir / "result.json").write_text(
            json.dumps({"time": [0], "output": [1], "metrics": {"final_value": 1}, "model": {}}),
            encoding="utf-8",
        )
        (run_dir / "result_plot.png").write_bytes(b"png")
        return subprocess.CompletedProcess("matlab", 0, stdout="", stderr="")

    try:
        service = RepairService(workspace_dir=workspace / "runs", matlab_root=root, runner=fake_runner)

        payload = service.run_agent_experiment(user_prompt="先失败再修复", settings=None, max_iterations=2)

        assert payload["status"] == "success"
        assert [item["status"] for item in payload["attempts"]] == ["error", "success"]
        assert payload["attempts"][1]["notes"] == "fixed"
        run_dir = next((workspace / "runs").glob("matlab_agent_*"))
        attempt_1 = json.loads((run_dir / "attempt_1_execution.json").read_text(encoding="utf-8"))
        assert "Undefined function" in attempt_1["stderr"]
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def test_matlab_agent_records_history_and_passes_continuation_context():
    workspace = _make_test_workspace()
    root = workspace / "MATLAB" / "R2024b"
    executable = root / "bin" / "matlab.exe"
    executable.parent.mkdir(parents=True)
    executable.write_text("", encoding="utf-8")
    captured_contexts: list[dict] = []

    class RecordService(MatlabExperimentService):
        def probe_environment(self, *, timeout_seconds=90, force=False):
            return {"available": True, "toolboxes": ["Control System Toolbox"], "unavailable_functions": []}

        def _generate_agent_matlab_code(self, **kwargs):
            captured_contexts.append(kwargs.get("continuation_context") or {})
            code = "disp('first run code')" if len(captured_contexts) == 1 else "disp('second run code')"
            return {"code": code, "notes": "record-test"}

    def fake_runner(command, cwd, text, capture_output, timeout):
        del command, text, capture_output, timeout
        run_dir = Path(cwd)
        code = (run_dir / "run_generated_simulation.m").read_text(encoding="utf-8")
        (run_dir / "result.json").write_text(
            json.dumps(
                {
                    "metrics": {"final_value": 1.0, "run_code_length": len(code)},
                    "series_preview": {"time": [0], "output": [1]},
                    "model": {"name": "record test"},
                }
            ),
            encoding="utf-8",
        )
        (run_dir / "result_plot.png").write_bytes(b"png")
        return subprocess.CompletedProcess("matlab", 0, stdout="", stderr="")

    try:
        service = RecordService(workspace_dir=workspace / "runs", matlab_root=root, runner=fake_runner)
        record = service.create_record(user_prompt="first requirement")["record"]

        first = service.run_agent_experiment(
            user_prompt="first requirement",
            record_id=record["record_id"],
            settings=None,
        )
        second = service.run_agent_experiment(
            user_prompt="extend requirement",
            record_id=record["record_id"],
            settings=None,
        )

        assert first["status"] == "success"
        assert second["status"] == "success"
        assert first["record_id"] == record["record_id"]
        assert second["record_id"] == record["record_id"]
        detail = service.get_record(record["record_id"])
        assert [run["run_id"] for run in detail["runs"]] == [first["run_id"], second["run_id"]]
        assert detail["record"]["runs"] == [first["run_id"], second["run_id"]]
        assert (workspace / "runs" / "matlab_records.json").exists()
        assert captured_contexts[0] == {}
        assert captured_contexts[1]["record_id"] == record["record_id"]
        assert captured_contexts[1]["prior_runs"][0]["run_id"] == first["run_id"]
        assert "first run code" in captured_contexts[1]["prior_runs"][0]["latest_code"]
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def test_matlab_agent_continues_legacy_run_record_without_losing_original_run():
    workspace = _make_test_workspace()
    root = workspace / "MATLAB" / "R2024b"
    executable = root / "bin" / "matlab.exe"
    executable.parent.mkdir(parents=True)
    executable.write_text("", encoding="utf-8")
    legacy_run_dir = workspace / "runs" / "matlab_agent_legacy"
    legacy_run_dir.mkdir(parents=True)
    (legacy_run_dir / "run_summary.json").write_text(
        json.dumps(
            {
                "status": "success",
                "run_id": "matlab_agent_legacy",
                "mode": "agent",
                "user_prompt": "legacy requirement",
                "attempts": [{"attempt": 1, "status": "success", "code": "disp('legacy')"}],
                "result": {"metrics": {"final_value": 1}},
                "trace": [],
            }
        ),
        encoding="utf-8",
    )

    class LegacyRecordService(MatlabExperimentService):
        def probe_environment(self, *, timeout_seconds=90, force=False):
            return {"available": True, "toolboxes": [], "unavailable_functions": []}

        def _generate_agent_matlab_code(self, **kwargs):
            assert kwargs["continuation_context"]["prior_runs"][0]["run_id"] == "matlab_agent_legacy"
            return {"code": "disp('new')", "notes": "new"}

    def fake_runner(command, cwd, text, capture_output, timeout):
        del command, text, capture_output, timeout
        run_dir = Path(cwd)
        (run_dir / "result.json").write_text(
            json.dumps({"metrics": {"final_value": 2}, "series_preview": {}, "model": {}}),
            encoding="utf-8",
        )
        (run_dir / "result_plot.png").write_bytes(b"png")
        return subprocess.CompletedProcess("matlab", 0, stdout="", stderr="")

    try:
        service = LegacyRecordService(workspace_dir=workspace / "runs", matlab_root=root, runner=fake_runner)
        record_id = "run:matlab_agent_legacy"

        payload = service.run_agent_experiment(
            user_prompt="extend legacy",
            record_id=record_id,
            settings=None,
        )

        detail = service.get_record(record_id)
        assert payload["status"] == "success"
        assert detail["record"]["runs"] == ["matlab_agent_legacy", payload["run_id"]]
        assert [run["run_id"] for run in detail["runs"]] == ["matlab_agent_legacy", payload["run_id"]]
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def test_matlab_agent_analysis_text_normalizer_removes_report_markup():
    raw = (
        "## **实验目的**\n"
        "$$\n"
        "T(s)=\\frac{10}{s^2+2s+15}\n"
        "$$\n"
        "- 曲线存在超调。\n"
    )

    clean = MatlabExperimentService._normalize_agent_analysis_text(raw)

    assert "##" not in clean
    assert "**" not in clean
    assert "$$" not in clean
    assert "\\[" not in clean
    assert "实验目的" in clean
    assert "曲线存在超调。" in clean


def test_matlab_agent_static_policy_warning_does_not_block_execution():
    workspace = _make_test_workspace()
    root = workspace / "MATLAB" / "R2024b"
    executable = root / "bin" / "matlab.exe"
    executable.parent.mkdir(parents=True)
    executable.write_text("", encoding="utf-8")

    class WarningService(MatlabExperimentService):
        def probe_environment(self, *, timeout_seconds=90, force=False):
            return {
                "available": True,
                "toolboxes": [],
                "unavailable_functions": ["tf", "step"],
            }

        def _generate_agent_matlab_code(self, **kwargs):
            return {"code": "G = tf([1], [1 1]); step(G);", "notes": "uses toolbox syntax"}

    def fake_runner(command, cwd, text, capture_output, timeout):
        del command, text, capture_output, timeout
        run_dir = Path(cwd)
        (run_dir / "result.json").write_text(
            json.dumps({"time": [0], "output": [1], "metrics": {"final_value": 1}, "model": {}}),
            encoding="utf-8",
        )
        (run_dir / "result_plot.png").write_bytes(b"png")
        return subprocess.CompletedProcess("matlab", 0, stdout="", stderr="")

    try:
        service = WarningService(workspace_dir=workspace / "runs", matlab_root=root, runner=fake_runner)

        payload = service.run_agent_experiment(user_prompt="允许 MATLAB 实际验证", settings=None)

        assert payload["status"] == "success"
        assert any(item["phase"] == "policy_warning" for item in payload["trace"])
        assert payload["attempts"][0]["status"] == "success"
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def test_matlab_agent_recovers_last_successful_environment_after_probe_failure():
    workspace = _make_test_workspace()
    root = workspace / "MATLAB" / "R2024b"
    executable = root / "bin" / "matlab.exe"
    executable.parent.mkdir(parents=True)
    executable.write_text("", encoding="utf-8")
    probe_dir = workspace / "runs" / "matlab_probe_previous"
    probe_dir.mkdir(parents=True)
    (probe_dir / "environment.json").write_text(
        json.dumps(
            {
                "toolboxes": ["Control System Toolbox"],
                "function_checks": {"tf": True, "feedback": True, "step": True},
                "unavailable_functions": [],
            }
        ),
        encoding="utf-8",
    )
    captured: dict[str, object] = {}

    class RecoveryService(MatlabExperimentService):
        def probe_environment(self, *, timeout_seconds=90, force=False):
            return {"available": False, "error": "startup failed"}

        def _generate_agent_matlab_code(self, **kwargs):
            captured["environment"] = kwargs["environment"]
            return {"code": "disp('ok')", "notes": "ok"}

    def fake_runner(command, cwd, text, capture_output, timeout):
        del command, text, capture_output, timeout
        run_dir = Path(cwd)
        (run_dir / "result.json").write_text(
            json.dumps({"time": [0], "output": [1], "metrics": {"final_value": 1}, "model": {}}),
            encoding="utf-8",
        )
        (run_dir / "result_plot.png").write_bytes(b"png")
        return subprocess.CompletedProcess("matlab", 0, stdout="", stderr="")

    try:
        service = RecoveryService(workspace_dir=workspace / "runs", matlab_root=root, runner=fake_runner)

        payload = service.run_agent_experiment(user_prompt="使用控制工具箱", settings=None)

        assert payload["status"] == "success"
        env = captured["environment"]
        assert env["available"] is True
        assert env["probe_available"] is False
        assert env["recovered_from_last_successful_probe"] is True
        assert "Control System Toolbox" in env["toolboxes"]
        snapshot = next((workspace / "runs").glob("matlab_agent_*/environment.json"))
        assert "startup failed" in snapshot.read_text(encoding="utf-8")
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def test_matlab_agent_result_analysis_uses_qwen_vision(monkeypatch):
    workspace = _make_test_workspace()
    plot_path = workspace / "plot.png"
    plot_path.write_bytes(b"fake-png")
    captured: dict[str, object] = {}

    class FakeCompletions:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="Qwen vision analysis"))]
            )

    class FakeClient:
        def __init__(self, **kwargs):
            captured["client"] = kwargs
            self.chat = SimpleNamespace(completions=FakeCompletions())

    monkeypatch.setattr("openai.OpenAI", FakeClient)
    monkeypatch.setenv("MATLAB_AGENT_VISION_MODEL", "qwen-vl-test")

    try:
        service = MatlabExperimentService(workspace_dir=workspace / "runs")
        settings = SimpleNamespace(qwen_api_key="qwen-key", dashscope_api_key=None)

        analysis = service._analyze_agent_result(
            user_prompt="分析阶跃响应",
            settings=settings,
            result={"metrics": {"overshoot_percent": 12.3}},
            plot_paths=[plot_path],
        )

        assert analysis == "Qwen vision analysis"
        assert captured["model"] == "qwen-vl-test"
        assert captured["client"]["base_url"] == "https://dashscope.aliyuncs.com/compatible-mode/v1"
        assert captured["messages"][1]["content"][1]["type"] == "image_url"
        assert captured["messages"][1]["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def test_matlab_environment_validator_does_not_match_function_suffixes():
    code = "fprintf('hello');\npoly2str([1 2], 's');\n"
    error = MatlabExperimentService._validate_generated_code_against_environment(
        code,
        {"toolboxes": [], "unavailable_functions": ["tf"]},
    )

    assert error == ""


def test_matlab_environment_validator_skips_failed_probe():
    code = "G = tf([1], [1 2 1]); y = step(G);"
    error = MatlabExperimentService._validate_generated_code_against_environment(
        code,
        {"available": False, "error": "probe failed", "unavailable_functions": ["tf", "step"]},
    )

    assert error == ""


def test_matlab_experiment_api_status_and_validation(monkeypatch):
    import ai_tutor_agent.interfaces.api.matlab_experiment as matlab_api

    workspace = _make_test_workspace()
    root = workspace / "missing-matlab"
    try:
        service = MatlabExperimentService(workspace_dir=workspace / "runs", matlab_root=root)
        monkeypatch.setattr(matlab_api, "_service", service)

        with TestClient(create_api_app()) as client:
            status = client.get("/api/matlab-experiment/status")
            assert status.status_code == 200
            assert status.json()["available"] is False

            invalid = client.post("/api/matlab-experiment/run", json={"time_constant": 0})
            assert invalid.status_code == 400
            assert invalid.json()["status"] == "error"
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def test_matlab_experiment_api_records(monkeypatch):
    import ai_tutor_agent.interfaces.api.matlab_experiment as matlab_api

    workspace = _make_test_workspace()
    root = workspace / "missing-matlab"
    try:
        service = MatlabExperimentService(workspace_dir=workspace / "runs", matlab_root=root)
        monkeypatch.setattr(matlab_api, "_service", service)

        with TestClient(create_api_app()) as client:
            created = client.post(
                "/api/matlab-experiment/records",
                json={"user_prompt": "simulate a closed-loop system"},
            )
            assert created.status_code == 200
            record = created.json()["record"]

            listed = client.get("/api/matlab-experiment/records")
            assert listed.status_code == 200
            assert listed.json()["records"][0]["record_id"] == record["record_id"]

            detail = client.get(f"/api/matlab-experiment/records/{record['record_id']}")
            assert detail.status_code == 200
            assert detail.json()["record"]["record_id"] == record["record_id"]
            assert detail.json()["runs"] == []
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def test_frontend_exposes_matlab_experiment_workbench():
    html = Path("frontend/index.html").read_text(encoding="utf-8")
    script = Path("frontend/assets/js/matlab_experiment.js").read_text(encoding="utf-8")
    styles = Path("frontend/assets/styles.css").read_text(encoding="utf-8")
    app_js = Path("frontend/assets/app.js").read_text(encoding="utf-8")

    assert "openMatlabExperimentPanel()" in html
    assert 'id="matlab-experiment-overlay"' in html
    assert "/assets/js/matlab_experiment.js" in html
    assert "/api/matlab-experiment/status" in script
    assert "/api/matlab-experiment/records" in script
    assert "/api/matlab-experiment/run" in script
    assert "/api/matlab-experiment/agent-jobs" in script
    assert "/cancel" in script
    assert "app.runMatlabExperiment = runExperiment;" in script
    assert "app.runMatlabPresetExperiment = runPresetExperiment;" in script
    assert "app.cancelMatlabExperiment = cancelExperiment;" in script
    assert "app.createMatlabRecord = createMatlabRecord;" in script
    assert "app.selectMatlabRecord = selectMatlabRecord;" in script
    assert "renderTrace" in script
    assert "buildTracePanel" in script
    assert "lastAgentTrace" in script
    assert "执行过程（未返回）" in script
    assert "matlab-experiment-code" in script
    assert 'id="matlab-cancel-btn"' in html
    assert 'id="matlab-record-list"' in html
    assert 'id="matlab-new-record-btn"' in html
    assert "开始新仿真" in html
    assert "历史仿真" in html
    assert "MATLAB 仿真 Agent" in html
    assert "根据自然语言需求生成 MATLAB 代码" in html
    assert "matlab-trace-panel-1" in html
    assert "MATLAB Experiment Workbench" in styles
    assert "library-upload-btn--danger" in styles
    assert ".matlab-experiment-trace-panel" in styles
    assert ".matlab-experiment-trace-missing" in styles
    assert ".matlab-experiment-trace" in styles
    assert "matlab-experiment-overlay" in app_js
    assert "runMatlabPresetExperiment" in app_js

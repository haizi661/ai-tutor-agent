"""
Test the post-generation MATLAB simulation pipeline.

Covers the flow AFTER the LLM has generated the .m file:
  1. MATLAB subprocess execution of the .m script
  2. Verification that result.json is created with valid content
  3. Verification that plot PNG(s) are created
  4. Result compacting for API response
  5. (Optional) Qwen-VL visual analysis

Uses the real generated .m file from:
  data/matlab_experiments/matlab_agent_20260521_162806_66aeedcc/run_generated_simulation.m

The primary test runs against a REAL MATLAB installation.
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/test_matlab_post_generation_pipeline.py -q -v -s
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import uuid
from pathlib import Path

import pytest

from ai_tutor_agent.infrastructure.matlab_experiment import MatlabExperimentService


# ---------------------------------------------------------------------------
# Path to the real generated .m file we want to test
# ---------------------------------------------------------------------------
_GENERATED_M_FILE = Path(
    "data/matlab_experiments/matlab_agent_20260521_162806_66aeedcc/"
    "run_generated_simulation.m"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_test_workspace() -> Path:
    root = Path("data/matlab_experiment_test_runtime") / uuid.uuid4().hex
    root.mkdir(parents=True, exist_ok=True)
    return root


def _read_generated_m_file() -> str:
    if not _GENERATED_M_FILE.exists():
        raise FileNotFoundError(
            f"Generated .m file not found at {_GENERATED_M_FILE}. "
            "Run the MATLAB agent first to generate this file."
        )
    return _GENERATED_M_FILE.read_text(encoding="utf-8")


def _require_matlab(service: MatlabExperimentService) -> None:
    """Fail the test immediately if MATLAB is not installed."""
    install = service.detect_install()
    if not install.available:
        pytest.fail(
            f"MATLAB executable not found under {install.root}. "
            "Install MATLAB R2024b or set AI_TUTOR_MATLAB_ROOT environment variable "
            "to point to your MATLAB installation."
        )


# ---------------------------------------------------------------------------
# Primary test: real MATLAB pipeline
# ---------------------------------------------------------------------------


class TestRealMatlabPostGenerationPipeline:
    """Test the post-generation pipeline against a real MATLAB installation.

    These tests actually invoke MATLAB via subprocess to execute the
    generated .m file and verify the resulting artifacts.
    """

    def test_execute_generated_m_file_with_real_matlab(self):
        """Run the real generated .m file through real MATLAB and verify
        all expected artifacts are produced."""
        workspace = _make_test_workspace()
        try:
            service = MatlabExperimentService(workspace_dir=workspace / "runs")
            _require_matlab(service)
            install = service.detect_install()

            run_dir = workspace / "runs" / "real_test_run"
            run_dir.mkdir(parents=True)
            result_path = run_dir / "result.json"

            # Copy the generated .m file and point its paths at our test run_dir
            code = _read_generated_m_file()
            code = code.replace(
                "D:/learning-agent/ai-tutor-agent/data/matlab_experiments/"
                "matlab_agent_20260521_162806_66aeedcc",
                str(run_dir.resolve()).replace("\\", "/"),
            )

            active_script = run_dir / "run_generated_simulation.m"
            active_script.write_text(code, encoding="utf-8")

            print(f"\nRunning MATLAB script: {active_script}")
            execution = service._run_matlab_script(
                install=install,
                script_path=active_script,
                run_dir=run_dir,
                timeout_seconds=300,
            )

            print(f"MATLAB stdout:\n{execution.get('stdout', '')}")
            if execution.get("stderr"):
                print(f"MATLAB stderr:\n{execution['stderr']}")

            assert execution["status"] == "success", (
                f"MATLAB failed with returncode={execution.get('returncode')}\n"
                f"stderr: {execution.get('stderr', '')[:2000]}"
            )

            # Verify result.json
            assert result_path.exists(), (
                f"result.json was not created. Files in run_dir: "
                f"{list(run_dir.iterdir())}"
            )
            raw_result = json.loads(result_path.read_text(encoding="utf-8"))
            print(f"result.json keys: {list(raw_result.keys())}")

            assert "metrics" in raw_result, "result.json missing 'metrics'"
            assert "model" in raw_result or "parameters" in raw_result, (
                "result.json missing model/parameters"
            )

            metrics = raw_result["metrics"]
            print(f"Metrics: {json.dumps(metrics, ensure_ascii=False, indent=2)}")

            # Verify plot PNG(s)
            png_paths = sorted(run_dir.glob("*.png"))
            assert len(png_paths) >= 1, f"No PNG files found in {run_dir}"
            for png in png_paths:
                assert png.stat().st_size > 100, (
                    f"PNG file {png.name} is too small ({png.stat().st_size} bytes)"
                )
            print(f"Generated {len(png_paths)} plot(s): {[p.name for p in png_paths]}")

            # Compact result
            compact = service._compact_result_for_response(raw_result)
            assert "metrics" in compact
            print("Pipeline completed successfully with real MATLAB.")

        finally:
            shutil.rmtree(workspace, ignore_errors=True)

    def test_environment_probe(self):
        """Verify the MATLAB environment probe works and detects toolboxes."""
        workspace = _make_test_workspace()
        try:
            service = MatlabExperimentService(workspace_dir=workspace / "runs")
            _require_matlab(service)

            env = service.probe_environment(force=True, timeout_seconds=120)
            print(f"Environment: {json.dumps(env, ensure_ascii=False, indent=2)}")

            assert env.get("available") is True, (
                f"Environment probe failed: {env.get('error', 'unknown')}"
            )

            toolboxes = env.get("toolboxes", [])
            print(f"Detected toolboxes: {toolboxes}")

            func_checks = env.get("function_checks", {})
            key_funcs = ["tf", "step", "feedback", "jsonencode", "exportgraphics"]
            for func in key_funcs:
                status = func_checks.get(func, False)
                print(f"  {func}: {'available' if status else 'NOT available'}")

        finally:
            shutil.rmtree(workspace, ignore_errors=True)

    def test_static_validation_passes_for_generated_code(self):
        """Static validation: the generated code only uses functions in a
        healthy Control System Toolbox environment."""
        code = _read_generated_m_file()

        environment = {
            "available": True,
            "toolboxes": [
                "Control System Toolbox",
                "MATLAB",
                "Signal Processing Toolbox",
            ],
            "unavailable_functions": [],
        }

        error = MatlabExperimentService._validate_generated_code_against_environment(
            code, environment
        )
        assert error == "", f"Generated code uses unavailable functions: {error}"

    def test_generated_m_file_contains_required_artifacts(self):
        """The real generated .m file writes to result_json and saves a plot PNG."""
        code = _read_generated_m_file()

        assert "result_json" in code, (
            "Generated .m must reference result_json for output"
        )
        assert "jsonencode" in code, (
            "Generated .m must use jsonencode to write structured results"
        )
        assert ("exportgraphics" in code or "saveas" in code or "print(" in code), (
            "Generated .m must export at least one plot image"
        )


# ---------------------------------------------------------------------------
# Supplementary tests: pipeline logic (no MATLAB required)
# ---------------------------------------------------------------------------


class TestPostGenerationPipelineLogic:
    """Tests for pipeline logic that do not require a MATLAB installation.

    These exercise result compacting, error handling, and fallback
    analysis using mock runners or pure function calls.
    """

    def test_result_compact_subsamples_large_arrays(self):
        """Large time series arrays are subsampled to ~120 points."""
        workspace = _make_test_workspace()
        try:
            service = MatlabExperimentService(workspace_dir=workspace / "runs")

            large_result = {
                "time": [i * 0.01 for i in range(5000)],
                "output": [i * 0.01 * 0.5 for i in range(5000)],
                "metrics": {"final_value": 1.0},
            }

            compact = service._compact_result_for_response(large_result)

            preview = compact["series_preview"]
            assert len(preview["time"]) < 200
            assert len(preview["output"]) < 200
            assert len(preview["time"]) < 5000
            assert preview["sample_count"] == 5000

        finally:
            shutil.rmtree(workspace, ignore_errors=True)

    def test_missing_result_json_reports_error(self):
        """When MATLAB returns non-zero, result.json is absent and status=error."""
        workspace = _make_test_workspace()
        try:

            def failing_runner(command, cwd, text, capture_output, timeout):
                del cwd, text, capture_output, timeout
                return subprocess.CompletedProcess(
                    command, 1, stdout="", stderr="Undefined function 'tf'."
                )

            service = MatlabExperimentService(
                workspace_dir=workspace / "runs",
                runner=failing_runner,
            )

            run_dir = workspace / "runs" / "test_run"
            run_dir.mkdir(parents=True)
            result_path = run_dir / "result.json"

            code = _read_generated_m_file()
            active_script = run_dir / "run_generated_simulation.m"
            active_script.write_text(code, encoding="utf-8")

            execution = service._run_matlab_script(
                install=service.detect_install(),
                script_path=active_script,
                run_dir=run_dir,
                timeout_seconds=120,
            )

            assert execution["status"] == "error"
            assert not result_path.exists()

        finally:
            shutil.rmtree(workspace, ignore_errors=True)

    def test_analysis_without_qwen_key_returns_fallback(self):
        """When no Qwen API key is configured, analysis returns fallback text."""
        workspace = _make_test_workspace()
        plot_path = workspace / "plot.png"
        plot_path.write_bytes(b"fake-png")
        try:
            service = MatlabExperimentService(workspace_dir=workspace / "runs")

            analysis = service._analyze_agent_result(
                user_prompt="test",
                settings=None,
                result={"metrics": {"overshoot_percent": 12.3}},
                plot_paths=[plot_path],
            )

            assert "仿真已完成" in analysis
            assert "overshoot_percent" in analysis
        finally:
            shutil.rmtree(workspace, ignore_errors=True)

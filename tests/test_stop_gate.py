"""Tests for hooks/stop-gate.sh."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess

STOP_GATE = Path(__file__).parent.parent / "hooks" / "stop-gate.sh"
PLUGIN_ROOT = str(Path(__file__).parent.parent)


def run_stop_gate(cwd: Path, stdin_data: dict, env: dict | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(STOP_GATE)],
        input=json.dumps(stdin_data),
        capture_output=True,
        text=True,
        cwd=cwd,
        env={**os.environ, "CLAUDE_PLUGIN_ROOT": PLUGIN_ROOT, **(env or {})},
    )


def write_eval_config(cwd: Path, tier: int, test_cmd: str | None,
                      fast: bool, lint_cmd: str | None = None) -> None:
    acumen_dir = cwd / ".acumen"
    acumen_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "tier": tier,
        "confidence": "HIGH" if tier == 1 else "MEDIUM" if tier == 2 else "LOW",
        "test_cmd": test_cmd,
        "lint_cmd": lint_cmd,
        "test_latency_ms": 400 if fast else 5000,
        "fast_for_stop_gate": fast,
    }
    (acumen_dir / "eval-config.json").write_text(json.dumps(data))


def write_baseline(cwd: Path, pass_count: int, fail_count: int) -> None:
    acumen_dir = cwd / ".acumen"
    acumen_dir.mkdir(parents=True, exist_ok=True)
    (acumen_dir / "session-baseline.json").write_text(
        json.dumps({"pass_count": pass_count, "fail_count": fail_count})
    )


def test_exits_0_when_no_eval_config(tmp_path):
    """No eval-config.json -> exit 0 (fail-open)."""
    result = run_stop_gate(tmp_path, {"stop_hook_active": False})
    assert result.returncode == 0


def test_exits_0_when_loop_guard_active(tmp_path):
    """stop_hook_active=True -> exit 0 (prevent infinite blocking)."""
    write_eval_config(tmp_path, 1, "python3 -m pytest", True)
    result = run_stop_gate(tmp_path, {"stop_hook_active": True})
    assert result.returncode == 0


def test_blocks_when_new_failures_introduced(tmp_path):
    """Tests failing with 0 baseline failures -> exit 2 with stderr feedback."""
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    (test_dir / "test_fail.py").write_text("def test_always_fails():\n    assert False\n")
    write_eval_config(tmp_path, 1, "python3 -m pytest", True)
    write_baseline(tmp_path, pass_count=5, fail_count=0)
    result = run_stop_gate(tmp_path, {"stop_hook_active": False})
    assert result.returncode == 2
    assert "Acumen" in result.stderr
    assert "new failure" in result.stderr


def test_allows_when_failures_are_preexisting(tmp_path):
    """Pre-existing failures (same count as baseline) -> exit 0, don't block."""
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    (test_dir / "test_fail.py").write_text("def test_always_fails():\n    assert False\n")
    write_eval_config(tmp_path, 1, "python3 -m pytest", True)
    write_baseline(tmp_path, pass_count=5, fail_count=1)  # baseline already had 1 failure
    result = run_stop_gate(tmp_path, {"stop_hook_active": False})
    assert result.returncode == 0


def test_allows_when_fast_tests_pass(tmp_path):
    """Fast test suite passes -> exit 0."""
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    (test_dir / "test_pass.py").write_text("def test_always_passes():\n    assert True\n")
    write_eval_config(tmp_path, 1, "python3 -m pytest", True)
    result = run_stop_gate(tmp_path, {"stop_hook_active": False})
    assert result.returncode == 0


def test_allows_for_slow_tests(tmp_path):
    """Slow test command (fast_for_stop_gate=False) -> exit 0 (deferred)."""
    write_eval_config(tmp_path, 1, "python3 -m pytest", False)
    result = run_stop_gate(tmp_path, {"stop_hook_active": False})
    assert result.returncode == 0


def test_exits_0_on_corrupted_config(tmp_path):
    """Corrupted eval-config.json -> exit 0 (fail-open)."""
    acumen_dir = tmp_path / ".acumen"
    acumen_dir.mkdir()
    (acumen_dir / "eval-config.json").write_text("CORRUPTED {{{{")
    result = run_stop_gate(tmp_path, {"stop_hook_active": False})
    assert result.returncode == 0


def test_exits_0_when_no_plugin_root(tmp_path):
    """No CLAUDE_PLUGIN_ROOT set -> exit 0 (fail-open)."""
    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PLUGIN_ROOT"}
    result = subprocess.run(
        ["bash", str(STOP_GATE)],
        input=json.dumps({"stop_hook_active": False}),
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env=env,
    )
    assert result.returncode == 0

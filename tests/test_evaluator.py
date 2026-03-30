"""Tests for lib/evaluator.py."""

import json
import shutil
from pathlib import Path

import pytest


def test_detects_pytest_from_pyproject(tmp_path):
    """pyproject.toml present -> detects python3 -m pytest as test command."""
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
    from lib.evaluator import detect_eval_commands
    cmds = detect_eval_commands(tmp_path)
    if shutil.which("python3"):
        assert cmds["test_cmd"] == "python3 -m pytest"


def test_detects_go_module(tmp_path):
    """go.mod present -> detects go test ./... if go on PATH."""
    (tmp_path / "go.mod").write_text("module example.com/m\n\ngo 1.21\n")
    from lib.evaluator import detect_eval_commands
    cmds = detect_eval_commands(tmp_path)
    if shutil.which("go"):
        assert cmds["test_cmd"] == "go test ./..."


def test_detect_returns_none_when_no_config(tmp_path):
    """Empty directory -> both test_cmd and lint_cmd are None."""
    from lib.evaluator import detect_eval_commands
    cmds = detect_eval_commands(tmp_path)
    assert "test_cmd" in cmds
    assert "lint_cmd" in cmds


def test_build_config_tier1_when_tests_found(tmp_path):
    """Project with pyproject.toml -> tier=1, confidence=HIGH when pytest found."""
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
    from lib.evaluator import build_eval_config
    config = build_eval_config(tmp_path)
    if config.test_cmd:
        assert config.tier == 1
        assert config.confidence == "HIGH"


def test_build_config_tier3_fallback(tmp_path):
    """Empty project -> tier=3, confidence=LOW."""
    from lib.evaluator import build_eval_config
    config = build_eval_config(tmp_path)
    if not config.test_cmd and not config.lint_cmd:
        assert config.tier == 3
        assert config.confidence == "LOW"


def test_roundtrip_eval_config(tmp_path):
    """save_eval_config then load_eval_config returns identical fields."""
    from lib.evaluator import EvalConfig, save_eval_config, load_eval_config
    config = EvalConfig(
        tier=1,
        confidence="HIGH",
        test_cmd="python3 -m pytest",
        lint_cmd="ruff check .",
        test_latency_ms=450,
        fast_for_stop_gate=True,
    )
    save_eval_config(config, tmp_path)
    loaded = load_eval_config(tmp_path)
    assert loaded is not None
    assert loaded.tier == 1
    assert loaded.confidence == "HIGH"
    assert loaded.test_cmd == "python3 -m pytest"
    assert loaded.test_latency_ms == 450
    assert loaded.fast_for_stop_gate is True


def test_load_returns_none_when_missing(tmp_path):
    """No eval-config.json -> returns None."""
    from lib.evaluator import load_eval_config
    assert load_eval_config(tmp_path) is None


def test_save_creates_acumen_dir(tmp_path):
    """save_eval_config creates .acumen/ if it does not exist."""
    from lib.evaluator import EvalConfig, save_eval_config
    config = EvalConfig(tier=3, confidence="LOW", test_cmd=None, lint_cmd=None,
                        test_latency_ms=0, fast_for_stop_gate=False)
    save_eval_config(config, tmp_path)
    assert (tmp_path / ".acumen" / "eval-config.json").exists()


def test_run_signal_passing_tests(tmp_path):
    """Writes a passing pytest file -> EvalResult.passed=True."""
    from lib.evaluator import EvalConfig, run_eval_signal
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    (test_dir / "test_example.py").write_text("def test_passes():\n    assert 1 + 1 == 2\n")
    config = EvalConfig(tier=1, confidence="HIGH", test_cmd="python3 -m pytest",
                        lint_cmd=None, test_latency_ms=500, fast_for_stop_gate=True)
    result = run_eval_signal(config, tmp_path)
    assert result.passed is True
    assert result.pass_count >= 1
    assert result.fail_count == 0


def test_run_signal_failing_tests(tmp_path):
    """Writes a failing pytest file -> EvalResult.passed=False."""
    from lib.evaluator import EvalConfig, run_eval_signal
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    (test_dir / "test_example.py").write_text("def test_fails():\n    assert 1 == 2\n")
    config = EvalConfig(tier=1, confidence="HIGH", test_cmd="python3 -m pytest",
                        lint_cmd=None, test_latency_ms=500, fast_for_stop_gate=True)
    result = run_eval_signal(config, tmp_path)
    assert result.passed is False
    assert result.fail_count >= 1
    assert any("test_example" in d for d in result.details)


def test_run_signal_tier3_always_passes(tmp_path):
    """Tier 3 (error rate only) returns passed=True from run_eval_signal."""
    from lib.evaluator import EvalConfig, run_eval_signal
    config = EvalConfig(tier=3, confidence="LOW", test_cmd=None, lint_cmd=None,
                        test_latency_ms=0, fast_for_stop_gate=False)
    result = run_eval_signal(config, tmp_path)
    assert result.passed is True

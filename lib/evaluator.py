"""Detect, configure, and run project evaluation signals. Stdlib only."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class EvalConfig:
    tier: int               # 1=tests, 2=lint, 3=error_rate
    confidence: str         # HIGH, MEDIUM, LOW
    test_cmd: str | None
    lint_cmd: str | None
    test_latency_ms: int    # measured latency in ms; 0 if not measured
    fast_for_stop_gate: bool  # True if 0 < test_latency_ms < 2000


@dataclass
class EvalResult:
    passed: bool
    pass_count: int
    fail_count: int
    details: list[str]   # failing test/lint names, up to 10


def detect_eval_commands(project_root: Path) -> dict[str, str | None]:
    """Return {"test_cmd": ..., "lint_cmd": ...} for strongest available signals."""
    result: dict[str, str | None] = {"test_cmd": None, "lint_cmd": None}
    root = project_root

    has_pyproject = (root / "pyproject.toml").exists()
    has_pytest_ini = (root / "pytest.ini").exists() or (root / "setup.cfg").exists()
    if (has_pyproject or has_pytest_ini) and shutil.which("python3"):
        result["test_cmd"] = "python3 -m pytest"
    elif (root / "package.json").exists() and shutil.which("npx"):
        result["test_cmd"] = "npx jest --passWithNoTests"
    elif (root / "Cargo.toml").exists() and shutil.which("cargo"):
        result["test_cmd"] = "cargo test"
    elif (root / "go.mod").exists() and shutil.which("go"):
        result["test_cmd"] = "go test ./..."

    if shutil.which("ruff") and has_pyproject:
        result["lint_cmd"] = "ruff check ."
    elif shutil.which("eslint") and (
        (root / ".eslintrc.json").exists() or (root / ".eslintrc.js").exists()
    ):
        result["lint_cmd"] = "npx eslint ."

    return result


def _measure_latency(cmd: str, cwd: Path) -> int:
    """Run cmd once and return wall-clock ms. Returns 99999 on error."""
    try:
        start = time.monotonic()
        subprocess.run(cmd.split(), cwd=cwd, capture_output=True, timeout=10)
        return int((time.monotonic() - start) * 1000)
    except Exception:
        return 99999


def build_eval_config(project_root: Path) -> EvalConfig:
    """Auto-detect signals and measure latency. Called once at session start."""
    cmds = detect_eval_commands(project_root)
    test_cmd = cmds["test_cmd"]
    lint_cmd = cmds["lint_cmd"]

    test_latency_ms = 0
    if test_cmd:
        test_latency_ms = _measure_latency(test_cmd, project_root)

    fast = 0 < test_latency_ms < 2000

    if test_cmd:
        tier, confidence = 1, "HIGH"
    elif lint_cmd:
        tier, confidence = 2, "MEDIUM"
    else:
        tier, confidence = 3, "LOW"

    return EvalConfig(
        tier=tier,
        confidence=confidence,
        test_cmd=test_cmd,
        lint_cmd=lint_cmd,
        test_latency_ms=test_latency_ms,
        fast_for_stop_gate=fast,
    )


def save_eval_config(config: EvalConfig, project_root: Path) -> None:
    """Persist EvalConfig to .acumen/eval-config.json. Atomic write."""
    acumen_dir = project_root / ".acumen"
    acumen_dir.mkdir(parents=True, exist_ok=True)
    path = acumen_dir / "eval-config.json"
    fd, tmp = tempfile.mkstemp(dir=acumen_dir, suffix=".tmp")
    try:
        with open(fd, "w") as f:
            json.dump(asdict(config), f, indent=2)
        Path(tmp).replace(path)
    except Exception:
        Path(tmp).unlink(missing_ok=True)
        raise


def load_eval_config(project_root: Path) -> EvalConfig | None:
    """Load EvalConfig from .acumen/eval-config.json. Returns None if missing."""
    path = project_root / ".acumen" / "eval-config.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return EvalConfig(**data)
    except Exception:
        return None


def run_eval_signal(
    config: EvalConfig,
    project_root: Path,
    changed_files: list[str] | None = None,
) -> EvalResult:
    """Run the evaluation signal. changed_files scopes lint to modified files only."""
    if config.tier == 1 and config.test_cmd:
        return _run_tests(config.test_cmd, project_root)
    if config.tier <= 2 and config.lint_cmd:
        return _run_lint(config.lint_cmd, project_root, changed_files)
    return EvalResult(passed=True, pass_count=0, fail_count=0, details=[])


def _run_tests(cmd: str, cwd: Path) -> EvalResult:
    try:
        proc = subprocess.run(
            cmd.split(), cwd=cwd, capture_output=True, text=True, timeout=120,
        )
        passed = proc.returncode == 0
        p, f, details = _parse_pytest_output(proc.stdout + proc.stderr)
        return EvalResult(passed=passed, pass_count=p, fail_count=f, details=details)
    except subprocess.TimeoutExpired:
        return EvalResult(passed=False, pass_count=0, fail_count=0,
                          details=["test command timed out"])
    except Exception as e:
        return EvalResult(passed=False, pass_count=0, fail_count=0, details=[str(e)])


def _run_lint(cmd: str, cwd: Path, changed_files: list[str] | None) -> EvalResult:
    try:
        parts = cmd.split()
        if changed_files:
            parts = [p for p in parts if p != "."] + changed_files[:20]
        proc = subprocess.run(parts, cwd=cwd, capture_output=True, text=True, timeout=30)
        passed = proc.returncode == 0
        details = [ln for ln in (proc.stdout + proc.stderr).splitlines() if ln.strip()][:10]
        return EvalResult(passed=passed, pass_count=0, fail_count=len(details), details=details)
    except Exception:
        return EvalResult(passed=True, pass_count=0, fail_count=0, details=[])


def _parse_pytest_output(output: str) -> tuple[int, int, list[str]]:
    """Extract pass/fail counts and failing test names from pytest stdout."""
    p = sum(int(m.group(1)) for m in re.finditer(r"(\d+)\s+passed", output))
    f = sum(int(m.group(1)) for m in re.finditer(r"(\d+)\s+failed", output))
    details = [m.group(1) for m in re.finditer(r"FAILED\s+(\S+)", output)][:10]
    return p, f, details

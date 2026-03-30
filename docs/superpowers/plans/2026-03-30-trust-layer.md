# Acumen v0.3 Trust Layer — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the trust layer: Stop gate (blocks false "done" claims), InstructionsLoaded + StopFailure hooks (close attribution gaps), `lib/evaluator.py` (auto-detected evaluation signal), evaluator-backed effectiveness measurement, and `/acumen-effectiveness` command.

**Architecture:** `lib/evaluator.py` is the new foundation — it auto-detects available signals (test suite > lint > error rate), measures test latency, and runs signals for both the Stop gate and effectiveness measurement. The Stop gate (`hooks/stop-gate.sh`) calls into the evaluator, blocks the agent from stopping when evaluation fails, and defers slow test suite verification to session-end. Effectiveness measurement in `lib/improver.py` is extended to use the evaluator instead of raw error rates, adding confidence labels.

**Tech Stack:** Python 3.11+ stdlib only (subprocess, shutil, dataclasses, json, re, tempfile). Pure bash for hook scripts. pytest for test suite. All file I/O atomic via write-tmp-rename. No pip packages.

---

## File Map

```
New files:
  hooks/stop-gate.sh              (~40 lines)  Stop hook: evaluation signal gating
  hooks/instructions-loaded.sh    (~20 lines)  InstructionsLoaded hook: rule activation log
  hooks/stop-failure.sh           (~20 lines)  StopFailure hook: API error session marker
  lib/evaluator.py                (~150 lines) Evaluation signal detection, latency, running
  commands/effectiveness.md       (~30 lines)  /acumen-effectiveness command
  tests/test_evaluator.py         New test file
  tests/test_stop_gate.py         New test file

Modified files:
  plugin.json                     Register 3 new hooks (Stop, InstructionsLoaded, StopFailure)
  hooks/session-start.sh          Add baseline capture (eval config detection + fast test run)
  lib/improver.py                 Use evaluator for effectiveness; filter by attribution
  agents/reflector.md             Add attribution-aware analysis instructions
  commands/status.md              Display evaluation tier and confidence label
```

---

## Task 0: Stop Gate Proof-of-Concept

**Goal:** Validate the Stop hook mechanism BEFORE writing production code. This is an experiment.

**Files:**
- Create: `hooks/stop-gate-poc.sh`
- Modify: `plugin.json`

- [ ] **Step 1: Write the minimal PoC hook**

```bash
#!/usr/bin/env bash
# hooks/stop-gate-poc.sh -- PoC only, not production
input=$(cat)
stop_hook_active=$(python3 -c "import json,sys; d=json.loads(sys.argv[1]); print(d.get('stop_hook_active', False))" "$input" 2>/dev/null || echo "True")
if [ "$stop_hook_active" = "True" ]; then
  exit 0
fi
echo "Acumen stop-gate-poc: blocking stop to verify hook works. Say 'continue' to proceed." >&2
exit 2
```

```bash
chmod +x hooks/stop-gate-poc.sh
```

- [ ] **Step 2: Register the PoC hook in plugin.json**

Add a `Stop` entry to the `hooks` object in `plugin.json`:

```json
"Stop": [{"hooks": [{"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/stop-gate-poc.sh"}]}]
```

- [ ] **Step 3: Test in a real Claude Code session**

Start a new Claude Code session in the acumen repo. Give the agent a trivial task. When it stops, verify:
1. The hook fires — you see the blocking message
2. The agent receives stderr feedback and continues
3. When `stop_hook_active=True` fires, the hook exits 0 (loop guard works)

- [ ] **Step 4: Measure test command latency**

```bash
time python3 -m pytest tests/ -q 2>&1 | tail -3
```

Record: does it complete in under 2 seconds? This determines whether Stop gate runs tests inline or defers to session-end.

- [ ] **Step 5: Commit**

```bash
git add hooks/stop-gate-poc.sh plugin.json
git commit -m "feat: stop gate PoC for mechanism validation"
```

---

## Task 1: `lib/evaluator.py` — Evaluation Signal Detection and Running

**Goal:** Create the evaluation signal module. Everything in Phase 1 depends on this.

**Files:**
- Create: `lib/evaluator.py`
- Create: `tests/test_evaluator.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_evaluator.py
"""Tests for lib/evaluator.py."""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from lib.evaluator import (
    EvalConfig,
    EvalResult,
    build_eval_config,
    detect_eval_commands,
    load_eval_config,
    run_eval_signal,
    save_eval_config,
)


def test_detects_pytest_from_pyproject(tmp_path):
    """pyproject.toml present -> detects python3 -m pytest as test command."""
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
    cmds = detect_eval_commands(tmp_path)
    if shutil.which("python3"):
        assert cmds["test_cmd"] == "python3 -m pytest"


def test_detects_go_module(tmp_path):
    """go.mod present -> detects go test ./... if go on PATH."""
    (tmp_path / "go.mod").write_text("module example.com/m\n\ngo 1.21\n")
    cmds = detect_eval_commands(tmp_path)
    if shutil.which("go"):
        assert cmds["test_cmd"] == "go test ./..."


def test_detect_returns_none_when_no_config(tmp_path):
    """Empty directory -> both test_cmd and lint_cmd are None."""
    cmds = detect_eval_commands(tmp_path)
    assert "test_cmd" in cmds
    assert "lint_cmd" in cmds


def test_build_config_tier1_when_tests_found(tmp_path):
    """Project with pyproject.toml -> tier=1, confidence=HIGH when pytest found."""
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
    config = build_eval_config(tmp_path)
    if config.test_cmd:
        assert config.tier == 1
        assert config.confidence == "HIGH"


def test_build_config_tier3_fallback(tmp_path):
    """Empty project -> tier=3, confidence=LOW."""
    config = build_eval_config(tmp_path)
    if not config.test_cmd and not config.lint_cmd:
        assert config.tier == 3
        assert config.confidence == "LOW"


def test_roundtrip_eval_config(tmp_path):
    """save_eval_config then load_eval_config returns identical fields."""
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
    assert load_eval_config(tmp_path) is None


def test_save_creates_acumen_dir(tmp_path):
    """save_eval_config creates .acumen/ if it does not exist."""
    config = EvalConfig(tier=3, confidence="LOW", test_cmd=None, lint_cmd=None,
                        test_latency_ms=0, fast_for_stop_gate=False)
    save_eval_config(config, tmp_path)
    assert (tmp_path / ".acumen" / "eval-config.json").exists()


def test_run_signal_passing_tests(tmp_path):
    """Writes a passing pytest file -> EvalResult.passed=True."""
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
    config = EvalConfig(tier=3, confidence="LOW", test_cmd=None, lint_cmd=None,
                        test_latency_ms=0, fast_for_stop_gate=False)
    result = run_eval_signal(config, tmp_path)
    assert result.passed is True
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
python3 -m pytest tests/test_evaluator.py -v 2>&1 | head -15
```

Expected: `ModuleNotFoundError: No module named 'lib.evaluator'`.

- [ ] **Step 3: Write `lib/evaluator.py`**

```python
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
        details = [l for l in (proc.stdout + proc.stderr).splitlines() if l.strip()][:10]
        return EvalResult(passed=passed, pass_count=0, fail_count=len(details), details=details)
    except Exception:
        return EvalResult(passed=True, pass_count=0, fail_count=0, details=[])


def _parse_pytest_output(output: str) -> tuple[int, int, list[str]]:
    """Extract pass/fail counts and failing test names from pytest stdout."""
    p = sum(int(m.group(1)) for m in re.finditer(r"(\d+)\s+passed", output))
    f = sum(int(m.group(1)) for m in re.finditer(r"(\d+)\s+failed", output))
    details = [m.group(1) for m in re.finditer(r"FAILED\s+(\S+)", output)][:10]
    return p, f, details
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
python3 -m pytest tests/test_evaluator.py -v
```

Expected: All tests pass.

- [ ] **Step 5: Commit**

```bash
git add lib/evaluator.py tests/test_evaluator.py
git commit -m "feat: add lib/evaluator.py -- auto-detect and run evaluation signals"
```

---

## Task 2: Baseline Capture at Session Start

**Goal:** At session start, detect and save the evaluation config so the stop gate and effectiveness measurement know what tier they're working with.

**Files:**
- Modify: `hooks/session-start.sh`
- Modify: `tests/test_session_hooks.py`

- [ ] **Step 1: Write failing tests**

Add to the `TestSessionStart` class in `tests/test_session_hooks.py`:

```python
def test_session_start_creates_eval_config(tmp_path):
    """Session start creates .acumen/eval-config.json when pyproject.toml present."""
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
    plugin_root = str(Path(__file__).parent.parent)
    result = run_hook(SESSION_START, tmp_path, env={"CLAUDE_PLUGIN_ROOT": plugin_root})
    assert result.returncode == 0
    assert (tmp_path / ".acumen" / "eval-config.json").exists()


def test_session_start_eval_config_has_required_fields(tmp_path):
    """eval-config.json written by session-start has tier and confidence fields."""
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
    plugin_root = str(Path(__file__).parent.parent)
    run_hook(SESSION_START, tmp_path, env={"CLAUDE_PLUGIN_ROOT": plugin_root})
    data = json.loads((tmp_path / ".acumen" / "eval-config.json").read_text())
    assert "tier" in data
    assert data["confidence"] in ("HIGH", "MEDIUM", "LOW")
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
python3 -m pytest tests/test_session_hooks.py::TestSessionStart::test_session_start_creates_eval_config -v
```

Expected: FAIL — session-start.sh doesn't write eval-config yet.

- [ ] **Step 3: Add evaluation detection to `hooks/session-start.sh`**

Append the following block before the final `exit 0` in `hooks/session-start.sh`:

```bash
# --- Job 3: Detect evaluation signal and write eval-config.json ---
# Rebuilds once per 24 hours or on first run.
plugin_root="${CLAUDE_PLUGIN_ROOT:-}"
if [ -n "$plugin_root" ] && [ -f "$plugin_root/lib/evaluator.py" ]; then
  python3 << PYEOF 2>/dev/null || true
import sys, time
sys.path.insert(0, '${plugin_root}/lib')
try:
    from evaluator import build_eval_config, save_eval_config, load_eval_config
    from pathlib import Path
    project_root = Path('.')
    config_path = project_root / '.acumen' / 'eval-config.json'
    should_rebuild = not config_path.exists()
    if not should_rebuild:
        age_s = time.time() - config_path.stat().st_mtime
        should_rebuild = age_s > 86400
    if should_rebuild:
        config = build_eval_config(project_root)
        save_eval_config(config, project_root)
except Exception:
    pass
PYEOF
fi
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
python3 -m pytest tests/test_session_hooks.py -v
```

- [ ] **Step 5: Commit**

```bash
git add hooks/session-start.sh tests/test_session_hooks.py
git commit -m "feat: session-start detects evaluation signal and writes eval-config.json"
```

---

## Task 3: Production `hooks/stop-gate.sh`

**Goal:** Replace the PoC with a production stop gate that uses the evaluator.

**Files:**
- Create: `hooks/stop-gate.sh`
- Create: `tests/test_stop_gate.py`
- Delete: `hooks/stop-gate-poc.sh`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_stop_gate.py
"""Tests for hooks/stop-gate.sh."""

import json
import os
import subprocess
from pathlib import Path

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


def write_eval_config_file(cwd: Path, tier: int, test_cmd: str | None,
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


def test_exits_0_when_no_eval_config(tmp_path):
    """No eval-config.json -> exit 0 (fail-open)."""
    result = run_stop_gate(tmp_path, {"stop_hook_active": False})
    assert result.returncode == 0


def test_exits_0_when_loop_guard_active(tmp_path):
    """stop_hook_active=True -> exit 0 (prevent infinite blocking)."""
    write_eval_config_file(tmp_path, 1, "python3 -m pytest", True)
    result = run_stop_gate(tmp_path, {"stop_hook_active": True})
    assert result.returncode == 0


def test_blocks_when_fast_tests_fail(tmp_path):
    """Fast test suite fails -> exit 2 with stderr feedback."""
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    (test_dir / "test_fail.py").write_text("def test_always_fails():\n    assert False\n")
    write_eval_config_file(tmp_path, 1, "python3 -m pytest", True)
    result = run_stop_gate(tmp_path, {"stop_hook_active": False})
    assert result.returncode == 2
    assert "Acumen" in result.stderr


def test_allows_when_fast_tests_pass(tmp_path):
    """Fast test suite passes -> exit 0."""
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
    test_dir = tmp_path / "tests"
    test_dir.mkdir()
    (test_dir / "test_pass.py").write_text("def test_always_passes():\n    assert True\n")
    write_eval_config_file(tmp_path, 1, "python3 -m pytest", True)
    result = run_stop_gate(tmp_path, {"stop_hook_active": False})
    assert result.returncode == 0


def test_allows_for_slow_tests(tmp_path):
    """Slow test command (fast_for_stop_gate=False) -> exit 0 (deferred)."""
    write_eval_config_file(tmp_path, 1, "python3 -m pytest", False)
    result = run_stop_gate(tmp_path, {"stop_hook_active": False})
    assert result.returncode == 0


def test_exits_0_on_corrupted_config(tmp_path):
    """Corrupted eval-config.json -> exit 0 (fail-open)."""
    acumen_dir = tmp_path / ".acumen"
    acumen_dir.mkdir()
    (acumen_dir / "eval-config.json").write_text("CORRUPTED JSON {{{{")
    result = run_stop_gate(tmp_path, {"stop_hook_active": False})
    assert result.returncode == 0
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
python3 -m pytest tests/test_stop_gate.py -v 2>&1 | head -20
```

Expected: FAIL — `stop-gate.sh` doesn't exist.

- [ ] **Step 3: Write `hooks/stop-gate.sh`**

```bash
#!/usr/bin/env bash
# Acumen Stop hook -- checks evaluation signals before allowing the agent to stop.
# Fails open on any error. Loop guard via stop_hook_active.

set -uo pipefail

input=$(cat 2>/dev/null || echo "{}")
plugin_root="${CLAUDE_PLUGIN_ROOT:-}"
[ -n "$plugin_root" ] || exit 0

# Parse stop_hook_active from stdin JSON
stop_active=$(python3 -c "
import json, sys
try:
    d = json.loads(sys.argv[1])
    print('true' if d.get('stop_hook_active', False) else 'false')
except Exception:
    print('true')
" "$input" 2>/dev/null || echo "true")

# Loop guard: always allow on second invocation in same stop cycle
if [ "$stop_active" = "true" ]; then
  exit 0
fi

# Run evaluation and decide whether to block
decision=$(python3 -c "
import sys, json
sys.path.insert(0, '$plugin_root/lib')
try:
    from evaluator import load_eval_config, run_eval_signal
    from pathlib import Path
    config = load_eval_config(Path('.'))
    if config is None:
        print(json.dumps({'action': 'allow', 'reason': 'no_config'}))
        sys.exit(0)
    if not config.fast_for_stop_gate:
        print(json.dumps({'action': 'allow', 'reason': 'deferred'}))
        sys.exit(0)
    result = run_eval_signal(config, Path('.'))
    if result.passed:
        print(json.dumps({'action': 'allow', 'reason': 'passed'}))
    else:
        print(json.dumps({
            'action': 'block',
            'fail_count': result.fail_count,
            'details': result.details,
        }))
except Exception as e:
    print(json.dumps({'action': 'allow', 'reason': 'error'}))
" 2>/dev/null || echo '{"action":"allow","reason":"py_error"}')

action=$(python3 -c "
import json, sys
try:
    print(json.loads(sys.argv[1]).get('action', 'allow'))
except Exception:
    print('allow')
" "$decision" 2>/dev/null || echo "allow")

if [ "$action" = "block" ]; then
  fail_count=$(python3 -c "
import json, sys
try:
    print(json.loads(sys.argv[1]).get('fail_count', 0))
except Exception:
    print(0)
" "$decision" 2>/dev/null || echo "0")
  details=$(python3 -c "
import json, sys
try:
    d = json.loads(sys.argv[1])
    for x in d.get('details', [])[:5]:
        print(f'  - {x}')
except Exception:
    pass
" "$decision" 2>/dev/null || echo "")
  printf "Acumen: stop blocked. %s failure(s) detected:\n%s\nFix the failures or describe what is still broken.\n" \
    "$fail_count" "$details" >&2
  exit 2
fi

exit 0
```

```bash
chmod +x hooks/stop-gate.sh
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
python3 -m pytest tests/test_stop_gate.py -v
```

Expected: All tests pass.

- [ ] **Step 5: Remove PoC, update plugin.json to production hook**

```bash
git rm hooks/stop-gate-poc.sh
```

In `plugin.json`, change the `Stop` entry command from `stop-gate-poc.sh` to `stop-gate.sh`.

- [ ] **Step 6: Run full suite**

```bash
python3 -m pytest tests/ -v
```

- [ ] **Step 7: Commit**

```bash
git add hooks/stop-gate.sh tests/test_stop_gate.py plugin.json
git commit -m "feat: production stop gate with fast-signal evaluation and loop guard"
```

---

## Task 4: `hooks/instructions-loaded.sh`

**Goal:** Record which acumen rules entered context each session — closes the "rule generated vs rule active" attribution gap.

**Files:**
- Create: `hooks/instructions-loaded.sh`
- Modify: `tests/test_session_hooks.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_session_hooks.py` (outside of any class, as module-level functions):

```python
INSTRUCTIONS_LOADED = Path(__file__).parent.parent / "hooks" / "instructions-loaded.sh"


def run_instructions_loaded(cwd: Path, stdin_data: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(INSTRUCTIONS_LOADED)],
        input=json.dumps(stdin_data),
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def test_instructions_loaded_records_acumen_rules(tmp_path):
    """Records acumen-* rules that entered context."""
    (tmp_path / ".acumen").mkdir()
    result = run_instructions_loaded(tmp_path, {
        "session_id": "sess123",
        "files": [".claude/rules/acumen-use-python3.md", "CLAUDE.md"],
    })
    assert result.returncode == 0
    records = [json.loads(l) for l in
               (tmp_path / ".acumen" / "rule-activity.jsonl").read_text().splitlines()
               if l.strip()]
    assert len(records) == 1
    assert "use-python3" in records[0]["rules_loaded"]


def test_instructions_loaded_skips_non_acumen_files(tmp_path):
    """No record written when no acumen-* rules are loaded."""
    (tmp_path / ".acumen").mkdir()
    result = run_instructions_loaded(tmp_path, {
        "session_id": "sess456",
        "files": ["CLAUDE.md", ".claude/rules/custom-rule.md"],
    })
    assert result.returncode == 0
    activity = tmp_path / ".acumen" / "rule-activity.jsonl"
    if activity.exists():
        records = [json.loads(l) for l in activity.read_text().splitlines() if l.strip()]
        assert not any(r.get("rules_loaded") for r in records)


def test_instructions_loaded_fails_open_on_bad_json(tmp_path):
    """Malformed input -> exit 0."""
    result = subprocess.run(
        ["bash", str(INSTRUCTIONS_LOADED)],
        input="INVALID JSON",
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert result.returncode == 0
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
python3 -m pytest tests/test_session_hooks.py::test_instructions_loaded_records_acumen_rules -v
```

- [ ] **Step 3: Write `hooks/instructions-loaded.sh`**

```bash
#!/usr/bin/env bash
# Acumen InstructionsLoaded hook.
# Appends record to .acumen/rule-activity.jsonl showing which acumen rules entered context.

input=$(cat 2>/dev/null || echo "{}")
mkdir -p ".acumen" 2>/dev/null || true

python3 -c "
import json, sys
from datetime import datetime, timezone
from pathlib import Path
try:
    d = json.loads(sys.argv[1])
    files = d.get('files', [])
    session_id = d.get('session_id', '')
    acumen_rules = [
        Path(f).stem.removeprefix('acumen-')
        for f in files
        if '/acumen-' in f or Path(f).stem.startswith('acumen-')
    ]
    if not acumen_rules:
        sys.exit(0)
    record = {
        'session_id': session_id,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'rules_loaded': acumen_rules,
    }
    with open(Path('.acumen') / 'rule-activity.jsonl', 'a') as f:
        f.write(json.dumps(record) + '\n')
except Exception:
    pass
" "$input" 2>/dev/null || true

exit 0
```

```bash
chmod +x hooks/instructions-loaded.sh
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
python3 -m pytest tests/test_session_hooks.py -v
```

- [ ] **Step 5: Commit**

```bash
git add hooks/instructions-loaded.sh tests/test_session_hooks.py
git commit -m "feat: InstructionsLoaded hook records rule activation"
```

---

## Task 5: `hooks/stop-failure.sh`

**Goal:** Mark sessions that ended with an API/tool failure so the reflection pipeline excludes them.

**Files:**
- Create: `hooks/stop-failure.sh`
- Modify: `tests/test_session_hooks.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_session_hooks.py`:

```python
STOP_FAILURE = Path(__file__).parent.parent / "hooks" / "stop-failure.sh"


def run_stop_failure(cwd: Path, stdin_data: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(STOP_FAILURE)],
        input=json.dumps(stdin_data),
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def test_stop_failure_writes_session_marker(tmp_path):
    """StopFailure hook writes record to .acumen/stop-failures.jsonl."""
    (tmp_path / ".acumen").mkdir()
    result = run_stop_failure(tmp_path, {"session_id": "sess789", "error": "API timeout"})
    assert result.returncode == 0
    records = [json.loads(l) for l in
               (tmp_path / ".acumen" / "stop-failures.jsonl").read_text().splitlines()
               if l.strip()]
    assert len(records) == 1
    assert records[0]["session_id"] == "sess789"


def test_stop_failure_fails_open(tmp_path):
    """Malformed input -> exit 0."""
    result = subprocess.run(
        ["bash", str(STOP_FAILURE)],
        input="INVALID JSON",
        capture_output=True,
        text=True,
        cwd=tmp_path,
    )
    assert result.returncode == 0
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
python3 -m pytest tests/test_session_hooks.py::test_stop_failure_writes_session_marker -v
```

- [ ] **Step 3: Write `hooks/stop-failure.sh`**

```bash
#!/usr/bin/env bash
# Acumen StopFailure hook.
# Marks sessions that ended due to API/tool failures.
# Reflection skips these sessions to avoid learning from noise.

input=$(cat 2>/dev/null || echo "{}")
mkdir -p ".acumen" 2>/dev/null || true

python3 -c "
import json, sys
from datetime import datetime, timezone
from pathlib import Path
try:
    d = json.loads(sys.argv[1])
    record = {
        'session_id': d.get('session_id', ''),
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'error': d.get('error', 'unknown'),
    }
    with open(Path('.acumen') / 'stop-failures.jsonl', 'a') as f:
        f.write(json.dumps(record) + '\n')
except Exception:
    pass
" "$input" 2>/dev/null || true

exit 0
```

```bash
chmod +x hooks/stop-failure.sh
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
python3 -m pytest tests/test_session_hooks.py -v
```

- [ ] **Step 5: Commit**

```bash
git add hooks/stop-failure.sh tests/test_session_hooks.py
git commit -m "feat: StopFailure hook marks API-error sessions for reflection exclusion"
```

---

## Task 6: Register All Hooks in `plugin.json` + Version Bump

**Files:**
- Modify: `plugin.json`

- [ ] **Step 1: Update `plugin.json`**

Replace the full contents of `plugin.json` with:

```json
{
  "name": "acumen",
  "version": "0.3.0",
  "description": "Self-improving agent harness. Observes sessions, extracts insights, applies improvements.",
  "hooks": {
    "PostToolUse": [
      {"hooks": [{"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/observe.sh"}]}
    ],
    "PostToolUseFailure": [
      {"hooks": [{"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/observe.sh"}]}
    ],
    "SessionEnd": [
      {"hooks": [{"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/session-end.sh"}]}
    ],
    "SessionStart": [
      {"hooks": [{"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh"}]}
    ],
    "Stop": [
      {"hooks": [{"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/stop-gate.sh"}]}
    ],
    "InstructionsLoaded": [
      {"hooks": [{"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/instructions-loaded.sh"}]}
    ],
    "StopFailure": [
      {"hooks": [{"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/stop-failure.sh"}]}
    ]
  }
}
```

- [ ] **Step 2: Run full suite**

```bash
python3 -m pytest tests/ -v
```

Expected: All tests pass.

- [ ] **Step 3: Commit**

```bash
git add plugin.json
git commit -m "feat: register all v0.3 hooks; bump version to 0.3.0"
```

---

## Task 7: Attribution-Aware Reflection

**Goal:** Update the reflector agent to skip API-error sessions and classify failures correctly.

**Files:**
- Modify: `agents/reflector.md`

- [ ] **Step 1: Add attribution section to `agents/reflector.md`**

After the `## Input` section, insert the following new section:

```markdown
## Attribution (read before analysis)

Before generating insights, exclude sessions that should not feed learning:

1. Read `.acumen/stop-failures.jsonl` (if it exists). Extract all `session_id` values. Skip all observations from those session IDs.

2. For each error pattern detected, classify before generating an insight:

**Generate an insight** (agent-attributable):
- Agent ran wrong command syntax that a correct agent would not
- Agent skipped a required step in a procedure

**Do NOT generate an insight — add a BLOCKER note instead** (environment-attributable):
- Error message contains "command not found", "No such file or directory", exit code 127 → `env_missing`
- Error message contains "Permission denied", "EACCES" → `env_permission`
- Error message contains connection errors, "ECONNREFUSED", network timeouts → `env_external`
- Error message contains version mismatch language → `env_version`

**When uncertain, skip the insight entirely.** Do not guess.

Format environment blockers at the end of your output:
`[BLOCKER] env_missing: redis-server not found (N sessions affected)`
```

- [ ] **Step 2: Verify in a real session**

Start a Claude Code session. Run `/acumen-reflect`. Check:
1. Reflector reads stop-failures.jsonl (inspect its Bash calls)
2. If any env_missing errors are in recent observations, they generate BLOCKER notes not insights

- [ ] **Step 3: Commit**

```bash
git add agents/reflector.md
git commit -m "feat: attribution-aware reflection -- skip API errors, classify env failures"
```

---

## Task 8: Evaluator-Backed Effectiveness in `lib/improver.py`

**Goal:** Add `measure_effectiveness_with_confidence()` that attaches an eval tier confidence label to effectiveness verdicts.

**Files:**
- Modify: `lib/improver.py`
- Modify: `tests/test_improver.py`

- [ ] **Step 1: Write failing tests**

Add to `tests/test_improver.py`:

```python
from lib.improver import measure_effectiveness_with_confidence


def _make_dated_obs(tool_name: str, outcome: str, days_ago: float) -> dict:
    from datetime import datetime, timezone, timedelta
    ts = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()
    return {"tool_name": tool_name, "outcome": outcome, "timestamp": ts}


def test_measure_effectiveness_with_confidence_high_tier(tmp_path):
    """Tier 1 eval config -> effectiveness verdict has eval_confidence='HIGH'."""
    from lib.evaluator import EvalConfig, save_eval_config
    save_eval_config(
        EvalConfig(tier=1, confidence="HIGH", test_cmd="python3 -m pytest",
                   lint_cmd=None, test_latency_ms=400, fast_for_stop_gate=True),
        tmp_path,
    )
    from datetime import datetime, timezone, timedelta
    applied_at = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    proposal = {
        "description": "Run pytest with -v",
        "status": "auto-applied",
        "applied_at": applied_at,
        "tools": ["Bash"],
    }
    before_obs = [_make_dated_obs("Bash", "error", 2) for _ in range(6)]
    after_obs = [_make_dated_obs("Bash", "success" if i > 0 else "error", i * 0.1)
                 for i in range(6)]
    changed = measure_effectiveness_with_confidence([proposal], before_obs + after_obs, tmp_path)
    assert len(changed) == 1
    assert proposal["effectiveness"] == "effective"
    assert proposal["eval_confidence"] == "HIGH"


def test_measure_effectiveness_with_confidence_low_tier(tmp_path):
    """Tier 3 eval config -> effectiveness verdict has eval_confidence='LOW'."""
    from lib.evaluator import EvalConfig, save_eval_config
    save_eval_config(
        EvalConfig(tier=3, confidence="LOW", test_cmd=None, lint_cmd=None,
                   test_latency_ms=0, fast_for_stop_gate=False),
        tmp_path,
    )
    from datetime import datetime, timezone, timedelta
    applied_at = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    proposal = {
        "description": "Some rule",
        "status": "auto-applied",
        "applied_at": applied_at,
        "tools": ["Bash"],
    }
    before_obs = [_make_dated_obs("Bash", "error", 2) for _ in range(6)]
    after_obs = [_make_dated_obs("Bash", "success", i * 0.1) for i in range(6)]
    changed = measure_effectiveness_with_confidence([proposal], before_obs + after_obs, tmp_path)
    if changed:
        assert proposal["eval_confidence"] == "LOW"


def test_measure_effectiveness_with_confidence_no_config(tmp_path):
    """No eval config -> falls back gracefully, confidence='LOW'."""
    from datetime import datetime, timezone, timedelta
    applied_at = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    proposal = {
        "description": "Some rule",
        "status": "auto-applied",
        "applied_at": applied_at,
        "tools": ["Bash"],
    }
    before_obs = [_make_dated_obs("Bash", "error", 2) for _ in range(6)]
    after_obs = [_make_dated_obs("Bash", "success", i * 0.1) for i in range(6)]
    # Should not raise even with no eval config
    changed = measure_effectiveness_with_confidence([proposal], before_obs + after_obs, tmp_path)
    if changed:
        assert "eval_confidence" in proposal
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
python3 -m pytest tests/test_improver.py::test_measure_effectiveness_with_confidence_high_tier -v
```

Expected: ImportError on `measure_effectiveness_with_confidence`.

- [ ] **Step 3: Add `measure_effectiveness_with_confidence` to `lib/improver.py`**

Append to `lib/improver.py`:

```python
def measure_effectiveness_with_confidence(
    proposals: list[dict],
    observations: list[dict],
    project_root: Path,
) -> list[dict]:
    """Score applied proposals using before/after error rates, with eval tier confidence label.

    Wraps measure_effectiveness() and adds eval_confidence to each updated proposal.
    Falls back to confidence='LOW' if no eval config exists.
    """
    try:
        from evaluator import load_eval_config
        config = load_eval_config(project_root)
        confidence = config.confidence if config else "LOW"
    except Exception:
        confidence = "LOW"

    changed = measure_effectiveness(proposals, observations)
    for p in changed:
        p["eval_confidence"] = confidence
    return changed
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
python3 -m pytest tests/test_improver.py -v
```

- [ ] **Step 5: Update `agents/reflector.md` effectiveness section**

In `agents/reflector.md`, replace the effectiveness measurement Python snippet with one using the new function:

```python
python3 -c "
import sys, json, tempfile
sys.path.insert(0, 'lib')
from pathlib import Path
from store import resolve_scope_path, read_observations
from improver import read_proposals, measure_effectiveness_with_confidence

scope = resolve_scope_path('project')
observations = read_observations(scope, days=30)
proposals = read_proposals(scope)
changed = measure_effectiveness_with_confidence(proposals, observations, Path('.'))
if changed:
    fd, tmp = tempfile.mkstemp(dir=scope, suffix='.tmp')
    with open(fd, 'w') as f:
        json.dump(proposals, f, indent=2)
    Path(tmp).replace(scope / 'proposals.json')
    for p in changed:
        conf = p.get('eval_confidence', 'LOW')
        print(f'  [{p[\"effectiveness\"].upper()} confidence:{conf}] {p[\"description\"]}')
else:
    print('Effectiveness: no proposals with sufficient data yet')
"
```

- [ ] **Step 6: Commit**

```bash
git add lib/improver.py tests/test_improver.py agents/reflector.md
git commit -m "feat: evaluator-backed effectiveness with confidence labels"
```

---

## Task 9: Evaluation Tier Display in `/acumen-status`

**Goal:** Show eval tier and confidence in the status command.

**Files:**
- Modify: `lib/formatter.py`
- Modify: `tests/test_formatter.py`
- Modify: `commands/status.md`

- [ ] **Step 1: Write failing test**

Add to `tests/test_formatter.py`:

```python
def test_format_status_shows_eval_tier(tmp_path):
    """format_status shows eval tier when eval-config.json exists."""
    import json
    acumen_dir = tmp_path / ".acumen"
    acumen_dir.mkdir()
    (acumen_dir / "eval-config.json").write_text(json.dumps({
        "tier": 1, "confidence": "HIGH", "test_cmd": "python3 -m pytest",
        "lint_cmd": None, "test_latency_ms": 800, "fast_for_stop_gate": True,
    }))
    from lib.formatter import format_status
    output = format_status([], [], project_root=tmp_path)
    assert "HIGH" in output or "Test suite" in output


def test_format_status_tier3_shows_suggestion(tmp_path):
    """Tier 3 config shows 'Add tests' suggestion in status output."""
    import json
    acumen_dir = tmp_path / ".acumen"
    acumen_dir.mkdir()
    (acumen_dir / "eval-config.json").write_text(json.dumps({
        "tier": 3, "confidence": "LOW", "test_cmd": None,
        "lint_cmd": None, "test_latency_ms": 0, "fast_for_stop_gate": False,
    }))
    from lib.formatter import format_status
    output = format_status([], [], project_root=tmp_path)
    assert "test" in output.lower() or "LOW" in output
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
python3 -m pytest tests/test_formatter.py::test_format_status_shows_eval_tier -v
```

Expected: TypeError — `format_status` doesn't accept `project_root`.

- [ ] **Step 3: Update `lib/formatter.py`**

Read `lib/formatter.py` first, then add the `project_root` parameter to `format_status()`. Add before the final `return` in `format_status`:

```python
def format_status(
    observations: list[dict],
    insights: list[dict],
    project_root: "Path | None" = None,
) -> str:
```

And append to the function body, before the return statement:

```python
    # Append evaluation tier information
    if project_root is not None:
        try:
            from evaluator import load_eval_config
            config = load_eval_config(project_root)
            if config:
                tier_names = {1: "Test suite", 2: "Lint/typecheck", 3: "Error rate"}
                label = tier_names.get(config.tier, "Unknown")
                lines.append(f"\nEval signal: {label} (confidence: {config.confidence})")
                if config.tier == 3:
                    lines.append("  Tip: add tests for stronger improvement evidence.")
        except Exception:
            pass
```

Also add `from pathlib import Path` to imports at the top of `formatter.py` if not already present.

- [ ] **Step 4: Run tests — verify they pass**

```bash
python3 -m pytest tests/test_formatter.py -v
```

- [ ] **Step 5: Update `commands/status.md`**

Find the Python one-liner in `commands/status.md` that calls `format_status(obs, insights)` and add `project_root=Path('.')`:

```python
python3 -c "
import sys; sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/lib')
from pathlib import Path
from store import resolve_scope_path, read_observations, read_insights
from formatter import format_status
scope = resolve_scope_path('project')
obs = read_observations(scope)
insights = read_insights(scope)
print(format_status(obs, insights, project_root=Path('.')))
"
```

- [ ] **Step 6: Commit**

```bash
git add lib/formatter.py tests/test_formatter.py commands/status.md
git commit -m "feat: show evaluation tier and confidence in /acumen-status"
```

---

## Task 10: `/acumen-effectiveness` Command

**Goal:** Phase 2 completion — a command showing per-rule effectiveness verdicts with confidence labels.

**Files:**
- Create: `commands/effectiveness.md`

- [ ] **Step 1: Write `commands/effectiveness.md`**

```markdown
---
name: acumen-effectiveness
description: Show effectiveness verdicts for applied Acumen rules, with eval confidence labels.
---

Run the following to display effectiveness of applied rules:

` `` `python
python3 -c "
import sys; sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/lib')
from pathlib import Path
from store import resolve_scope_path, read_observations
from improver import read_proposals, measure_effectiveness_with_confidence

scope = resolve_scope_path('project')
proposals = read_proposals(scope)
observations = read_observations(scope, days=30)
changed = measure_effectiveness_with_confidence(proposals, observations, Path('.'))

applied = [p for p in proposals if p.get('status') in ('auto-applied', 'approved')]
if not applied:
    print('No applied rules yet. Run /acumen-reflect to generate proposals.')
    import sys; sys.exit(0)

print(f'Rule effectiveness ({len(applied)} rules):')
icons = {'effective': '[+]', 'neutral': '[~]', 'harmful': '[-]', 'pending': '[?]'}
for p in applied:
    verdict = p.get('effectiveness', 'pending')
    confidence = p.get('eval_confidence', 'LOW')
    icon = icons.get(verdict, '[?]')
    print(f'  {icon} [{confidence}] {p[\"description\"]}')

if any(p.get('effectiveness') == 'pending' for p in applied):
    print()
    print('  [?] = pending (need 5+ observations before and after)')
"
` `` `
```

- [ ] **Step 2: Test the command manually in the acumen repo**

```bash
python3 -c "
import sys; sys.path.insert(0, 'lib')
from pathlib import Path
from store import resolve_scope_path, read_observations
from improver import read_proposals, measure_effectiveness_with_confidence

scope = resolve_scope_path('project')
proposals = read_proposals(scope)
observations = read_observations(scope, days=30)
changed = measure_effectiveness_with_confidence(proposals, observations, Path('.'))
applied = [p for p in proposals if p.get('status') in ('auto-applied', 'approved')]
print(f'Applied: {len(applied)}')
for p in applied:
    print(f\"  {p.get('effectiveness', 'pending')} [{p.get('eval_confidence', 'LOW')}] {p['description']}\")
"
```

Expected: Shows the python3 rule with `[?] [HIGH]` or similar (pending until enough post-application observations accumulate).

- [ ] **Step 3: Run full test suite**

```bash
python3 -m pytest tests/ -v
```

Expected: All tests pass.

- [ ] **Step 4: Commit**

```bash
git add commands/effectiveness.md
git commit -m "feat: add /acumen-effectiveness command -- v0.3 trust layer complete"
```

---

## Final: Integration Verification + CAPABILITIES.md

- [ ] **Step 1: Test stop gate in a real session**

Start a Claude Code session. Ask the agent to write a failing test without fixing it, then say "done". Verify the stop gate fires and blocks.

- [ ] **Step 2: Verify eval config after session start**

```bash
cat .acumen/eval-config.json
```

Expected output includes `"confidence": "HIGH"` and `"test_cmd": "python3 -m pytest"`.

- [ ] **Step 3: Run /acumen-effectiveness**

Expected: Shows applied rules with confidence labels.

- [ ] **Step 4: Run full test suite**

```bash
python3 -m pytest tests/ -v
```

- [ ] **Step 5: Update CAPABILITIES.md**

Add entries for new capabilities:
- `CAP-TRUST-001`: Stop gate hooks — `hooks/stop-gate.sh`
- `CAP-TRUST-002`: InstructionsLoaded hook — `hooks/instructions-loaded.sh`
- `CAP-TRUST-003`: StopFailure hook — `hooks/stop-failure.sh`
- `CAP-EVAL-001`: Evaluation signal detection and running — `lib/evaluator.py`
- `CAP-IMP-007`: Effectiveness measurement with eval confidence — `lib/improver.py:measure_effectiveness_with_confidence`

```bash
git add CAPABILITIES.md
git commit -m "docs: update CAPABILITIES.md for v0.3 trust layer"
```

---

## Out of Scope (Plan 2)

Phase 3 (Skill synthesis) and Phase 4 (Evolution engine) are separate plans written after v0.3 ships:
- `docs/superpowers/plans/2026-MM-DD-skill-synthesis.md`
- `docs/superpowers/plans/2026-MM-DD-evolution-engine.md`

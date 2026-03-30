"""Tests for hooks/session-end.sh and hooks/session-start.sh."""

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Optional

SESSION_END = Path(__file__).parent.parent / "hooks" / "session-end.sh"
SESSION_START = Path(__file__).parent.parent / "hooks" / "session-start.sh"
INSTRUCTIONS_LOADED = Path(__file__).parent.parent / "hooks" / "instructions-loaded.sh"
STOP_FAILURE = Path(__file__).parent.parent / "hooks" / "stop-failure.sh"


def run_instructions_loaded(cwd: Path, stdin_data: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(INSTRUCTIONS_LOADED)],
        input=json.dumps(stdin_data),
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def run_stop_failure(cwd: Path, stdin_data: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(STOP_FAILURE)],
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


def run_hook(script: Path, cwd: Path, env: Optional[dict] = None) -> subprocess.CompletedProcess:
    """Run a hook script in the given working directory."""
    return subprocess.run(
        ["bash", str(script)],
        input="{}",
        capture_output=True,
        text=True,
        cwd=cwd,
        env={**os.environ, **(env or {})},
    )


def write_observations(cwd: Path, count: int) -> None:
    """Write count observation lines to today's JSONL file."""
    obs_dir = cwd / ".acumen" / "observations"
    obs_dir.mkdir(parents=True, exist_ok=True)
    lines = []
    for i in range(count):
        lines.append(json.dumps({"tool_name": f"Tool{i}", "outcome": "success"}))
    (obs_dir / "2026-03-29.jsonl").write_text("\n".join(lines) + "\n")


# -- session-end.sh tests --


class TestSessionEnd:

    def test_no_observations_dir_exits_clean(self, tmp_path):
        """No .acumen/observations dir -> exit 0, no flag."""
        result = run_hook(SESSION_END, tmp_path)
        assert result.returncode == 0
        assert not (tmp_path / ".acumen" / "should-reflect").exists()

    def test_below_threshold_no_flag(self, tmp_path):
        """Fewer observations than threshold -> no flag file."""
        write_observations(tmp_path, 5)
        result = run_hook(SESSION_END, tmp_path)
        assert result.returncode == 0
        assert not (tmp_path / ".acumen" / "should-reflect").exists()

    def test_at_threshold_creates_flag(self, tmp_path):
        """Exactly threshold observations -> flag file created."""
        write_observations(tmp_path, 10)
        result = run_hook(SESSION_END, tmp_path)
        assert result.returncode == 0
        assert (tmp_path / ".acumen" / "should-reflect").exists()

    def test_above_threshold_creates_flag(self, tmp_path):
        """More than threshold observations -> flag file created."""
        write_observations(tmp_path, 15)
        result = run_hook(SESSION_END, tmp_path)
        assert result.returncode == 0
        assert (tmp_path / ".acumen" / "should-reflect").exists()

    def test_custom_threshold_via_env(self, tmp_path):
        """ACUMEN_REFLECT_THRESHOLD env var overrides default."""
        write_observations(tmp_path, 3)
        result = run_hook(SESSION_END, tmp_path, env={"ACUMEN_REFLECT_THRESHOLD": "3"})
        assert result.returncode == 0
        assert (tmp_path / ".acumen" / "should-reflect").exists()

    def test_only_counts_observations_newer_than_insights(self, tmp_path):
        """Only observations newer than insights.json count."""
        write_observations(tmp_path, 15)
        # Create insights.json with a timestamp AFTER observations
        insights_path = tmp_path / ".acumen" / "insights.json"
        insights_path.write_text("[]")
        # Touch insights.json to be newer than observations
        time.sleep(0.1)
        insights_path.touch()

        result = run_hook(SESSION_END, tmp_path)
        assert result.returncode == 0
        assert not (tmp_path / ".acumen" / "should-reflect").exists()

    def test_counts_new_observations_after_reflection(self, tmp_path):
        """Observations written after insights.json are counted."""
        # Create insights.json first
        acumen_dir = tmp_path / ".acumen"
        acumen_dir.mkdir(parents=True, exist_ok=True)
        insights_path = acumen_dir / "insights.json"
        insights_path.write_text("[]")
        time.sleep(0.1)
        # Now write observations (newer than insights)
        write_observations(tmp_path, 10)

        result = run_hook(SESSION_END, tmp_path)
        assert result.returncode == 0
        assert (tmp_path / ".acumen" / "should-reflect").exists()

    def test_completes_fast(self, tmp_path):
        """Hook completes well under 1.5s timeout."""
        write_observations(tmp_path, 100)
        start = time.monotonic()
        run_hook(SESSION_END, tmp_path)
        elapsed = time.monotonic() - start
        assert elapsed < 1.0


# -- session-start.sh tests --


class TestSessionStart:

    def test_no_flag_exits_clean(self, tmp_path):
        """No flag file -> exit 0, no output."""
        result = run_hook(SESSION_START, tmp_path)
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_flag_present_outputs_context(self, tmp_path):
        """Flag file exists -> outputs context with reflect + auto-apply instructions."""
        flag = tmp_path / ".acumen" / "should-reflect"
        flag.parent.mkdir(parents=True, exist_ok=True)
        flag.touch()

        result = run_hook(SESSION_START, tmp_path)
        assert result.returncode == 0
        assert "/acumen-reflect" in result.stdout
        assert "auto_apply_proposals" in result.stdout
        assert "/acumen-review" in result.stdout

    def test_flag_removed_after_read(self, tmp_path):
        """Flag file is deleted after being consumed."""
        flag = tmp_path / ".acumen" / "should-reflect"
        flag.parent.mkdir(parents=True, exist_ok=True)
        flag.touch()

        run_hook(SESSION_START, tmp_path)
        assert not flag.exists()

    def test_second_run_no_output(self, tmp_path):
        """After flag consumed, second run produces no output."""
        flag = tmp_path / ".acumen" / "should-reflect"
        flag.parent.mkdir(parents=True, exist_ok=True)
        flag.touch()

        run_hook(SESSION_START, tmp_path)
        result = run_hook(SESSION_START, tmp_path)
        assert result.stdout.strip() == ""

    def test_shows_rule_count_when_rules_exist(self, tmp_path):
        """Shows improvement summary when acumen rules exist and no flag."""
        rules_dir = tmp_path / ".claude" / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        (rules_dir / "acumen-use-python3.md").write_text("rule")
        (rules_dir / "acumen-run-tests.md").write_text("rule")

        result = run_hook(SESSION_START, tmp_path)
        assert result.returncode == 0
        assert "2 active rule" in result.stdout
        assert "/acumen-status" in result.stdout

    def test_no_summary_without_rules(self, tmp_path):
        """No summary output when no acumen rules exist."""
        result = run_hook(SESSION_START, tmp_path)
        assert result.returncode == 0
        assert result.stdout.strip() == ""

    def test_session_start_creates_eval_config(self, tmp_path):
        """Session start creates .acumen/eval-config.json when pyproject.toml present."""
        (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
        plugin_root = str(Path(__file__).parent.parent)
        result = run_hook(SESSION_START, tmp_path, env={"CLAUDE_PLUGIN_ROOT": plugin_root})
        assert result.returncode == 0
        assert (tmp_path / ".acumen" / "eval-config.json").exists()

    def test_session_start_eval_config_has_required_fields(self, tmp_path):
        """eval-config.json written by session-start has tier and confidence fields."""
        (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
        plugin_root = str(Path(__file__).parent.parent)
        run_hook(SESSION_START, tmp_path, env={"CLAUDE_PLUGIN_ROOT": plugin_root})
        data = json.loads((tmp_path / ".acumen" / "eval-config.json").read_text())
        assert "tier" in data
        assert data["confidence"] in ("HIGH", "MEDIUM", "LOW")

    def test_session_start_captures_baseline_when_fast(self, tmp_path):
        """Session start captures baseline pass/fail counts when tests are fast."""
        (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\n")
        test_dir = tmp_path / "tests"
        test_dir.mkdir()
        (test_dir / "test_pass.py").write_text("def test_ok():\n    assert True\n")
        plugin_root = str(Path(__file__).parent.parent)
        run_hook(SESSION_START, tmp_path, env={"CLAUDE_PLUGIN_ROOT": plugin_root})
        baseline_path = tmp_path / ".acumen" / "session-baseline.json"
        assert baseline_path.exists()
        data = json.loads(baseline_path.read_text())
        assert "pass_count" in data
        assert "fail_count" in data
        assert data["pass_count"] >= 1
        assert data["fail_count"] == 0

    def test_session_start_skips_baseline_rebuild_within_24h(self, tmp_path):
        """Existing fresh eval-config.json is not rebuilt within 24h."""
        import json as _json
        acumen_dir = tmp_path / ".acumen"
        acumen_dir.mkdir()
        config_data = {
            "tier": 3, "confidence": "LOW", "test_cmd": None,
            "lint_cmd": None, "test_latency_ms": 0, "fast_for_stop_gate": False
        }
        (acumen_dir / "eval-config.json").write_text(_json.dumps(config_data))
        plugin_root = str(Path(__file__).parent.parent)
        result = run_hook(SESSION_START, tmp_path, env={"CLAUDE_PLUGIN_ROOT": plugin_root})
        assert result.returncode == 0
        # Config should not change (tier still 3, no rebuild)
        data = _json.loads((acumen_dir / "eval-config.json").read_text())
        assert data["tier"] == 3

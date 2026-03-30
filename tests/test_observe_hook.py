"""Tests for hooks/observe.sh -- handles both PostToolUse and PostToolUseFailure events."""

import json
import os
import subprocess
from pathlib import Path
from typing import Union

HOOK = Path(__file__).parent.parent / "hooks" / "observe.sh"


def run_hook(input_data: Union[dict, str], cwd: Path) -> subprocess.CompletedProcess:
    """Run observe.sh with given JSON on stdin, in the given working directory."""
    payload = input_data if isinstance(input_data, str) else json.dumps(input_data)
    return subprocess.run(
        ["bash", str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        cwd=cwd,
    )


def read_observations(cwd: Path) -> list[dict]:
    """Read all JSONL observation files from .acumen/observations/."""
    obs_dir = cwd / ".acumen" / "observations"
    if not obs_dir.exists():
        return []
    lines = []
    for f in sorted(obs_dir.glob("*.jsonl")):
        for line in f.read_text().strip().splitlines():
            lines.append(json.loads(line))
    return lines


# -- Basic functionality --


def test_produces_valid_jsonl(tmp_path):
    """Hook produces a valid JSONL line from a normal PostToolUse event."""
    event = {
        "tool_name": "Write",
        "session_id": "sess-001",
        "tool_input": {"file_path": "/tmp/foo.py", "content": "print('hi')"},
        "tool_response": {"filePath": "/tmp/foo.py", "success": True},
    }
    result = run_hook(event, tmp_path)
    assert result.returncode == 0

    obs = read_observations(tmp_path)
    assert len(obs) == 1
    assert obs[0]["tool_name"] == "Write"
    assert obs[0]["session_id"] == "sess-001"
    assert obs[0]["outcome"] == "success"
    assert obs[0]["error_type"] is None
    assert "timestamp" in obs[0]


def test_creates_directory_if_missing(tmp_path):
    """Hook creates .acumen/observations/ if it doesn't exist."""
    assert not (tmp_path / ".acumen").exists()
    event = {"tool_name": "Read", "session_id": "s1", "tool_input": {}, "tool_response": {}}
    run_hook(event, tmp_path)
    assert (tmp_path / ".acumen" / "observations").is_dir()
    assert len(read_observations(tmp_path)) == 1


def test_bash_error_detected(tmp_path):
    """Hook detects errors via PostToolUseFailure event (how Claude Code sends failures)."""
    event = {
        "hook_event_name": "PostToolUseFailure",
        "tool_name": "Bash",
        "session_id": "s2",
        "tool_input": {"command": "false"},
        "error": "Command exited with non-zero status code 1",
    }
    run_hook(event, tmp_path)
    obs = read_observations(tmp_path)
    assert obs[0]["outcome"] == "error"
    assert obs[0]["error_type"] == "tool_failure"


def test_bash_success_detected(tmp_path):
    """Hook detects Bash success via exit_code == 0."""
    event = {
        "tool_name": "Bash",
        "session_id": "s3",
        "tool_input": {"command": "true"},
        "tool_response": {"exit_code": 0, "stdout": "ok"},
    }
    run_hook(event, tmp_path)
    obs = read_observations(tmp_path)
    assert obs[0]["outcome"] == "success"
    assert obs[0]["error_type"] is None


def test_tool_error_field(tmp_path):
    """Hook detects errors from top-level .error field (PostToolUseFailure format)."""
    event = {
        "hook_event_name": "PostToolUseFailure",
        "tool_name": "Read",
        "session_id": "s4",
        "tool_input": {"file_path": "/nonexistent"},
        "error": "File not found",
    }
    run_hook(event, tmp_path)
    obs = read_observations(tmp_path)
    assert obs[0]["outcome"] == "error"
    assert obs[0]["error_type"] == "tool_failure"


# -- Security tests --


def test_does_not_capture_tool_input(tmp_path):
    """SECURITY: observation must NOT contain tool_input values."""
    event = {
        "tool_name": "Write",
        "session_id": "s5",
        "tool_input": {"file_path": "/secret.txt", "content": "SECRET_API_KEY=abc123"},
        "tool_response": {"success": True},
    }
    run_hook(event, tmp_path)
    obs = read_observations(tmp_path)
    raw = (tmp_path / ".acumen" / "observations").glob("*.jsonl")
    raw_text = "".join(f.read_text() for f in raw)

    assert "SECRET_API_KEY" not in raw_text
    assert "secret.txt" not in raw_text
    assert "tool_input" not in obs[0]


def test_does_not_capture_tool_response_content(tmp_path):
    """SECURITY: observation must NOT contain tool_response content."""
    event = {
        "tool_name": "Read",
        "session_id": "s6",
        "tool_input": {"file_path": "/etc/passwd"},
        "tool_response": {"content": "root:x:0:0:root:/root:/bin/bash"},
    }
    run_hook(event, tmp_path)
    raw = (tmp_path / ".acumen" / "observations").glob("*.jsonl")
    raw_text = "".join(f.read_text() for f in raw)

    assert "root:x:0:0" not in raw_text
    assert "/etc/passwd" not in raw_text
    assert "tool_response" not in raw_text


# -- Graceful failure --


def test_malformed_json_no_crash(tmp_path):
    """Hook handles malformed JSON gracefully (exit 0, no output)."""
    result = run_hook("not valid json {{{{", tmp_path)
    assert result.returncode == 0
    assert read_observations(tmp_path) == []


def test_empty_stdin_no_crash(tmp_path):
    """Hook handles empty stdin gracefully."""
    result = run_hook("", tmp_path)
    assert result.returncode == 0
    assert read_observations(tmp_path) == []


def test_missing_tool_name_skipped(tmp_path):
    """Hook skips events without tool_name."""
    event = {"session_id": "s7", "tool_input": {}, "tool_response": {}}
    run_hook(event, tmp_path)
    assert read_observations(tmp_path) == []


def test_missing_session_id_defaults(tmp_path):
    """Hook defaults session_id to 'unknown' when missing."""
    event = {"tool_name": "Glob", "tool_input": {}, "tool_response": {}}
    run_hook(event, tmp_path)
    obs = read_observations(tmp_path)
    assert obs[0]["session_id"] == "unknown"


def test_multiple_observations_append(tmp_path):
    """Multiple hook invocations append to the same daily file."""
    for i in range(3):
        event = {"tool_name": f"Tool{i}", "session_id": "s8", "tool_input": {}, "tool_response": {}}
        run_hook(event, tmp_path)
    obs = read_observations(tmp_path)
    assert len(obs) == 3
    assert [o["tool_name"] for o in obs] == ["Tool0", "Tool1", "Tool2"]


# -- jq fallback --


def test_no_jq_exits_cleanly(tmp_path):
    """Hook exits cleanly (0) when jq is not available."""
    event = {"tool_name": "Bash", "session_id": "s9", "tool_input": {}, "tool_response": {"exit_code": 0}}
    # Use absolute bash path, set PATH to dir without jq
    result = subprocess.run(
        ["/bin/bash", str(HOOK)],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        cwd=tmp_path,
        env={**os.environ, "PATH": "/nonexistent"},
    )
    assert result.returncode == 0
    assert read_observations(tmp_path) == []

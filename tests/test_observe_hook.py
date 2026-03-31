"""Tests for hooks/observe.sh -- Tier 0.5 observation with per-session JSONL."""

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
    """Hook produces valid JSONL with Tier 0.5 fields."""
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
    # Tier 0.5 fields present
    assert "command_family" in obs[0]
    assert "command_signature" in obs[0]
    assert "file_basename" in obs[0]
    assert "burst_count" in obs[0]
    assert obs[0]["burst_count"] == 1


def test_creates_directory_if_missing(tmp_path):
    """Hook creates .acumen/observations/ if it doesn't exist."""
    assert not (tmp_path / ".acumen").exists()
    event = {"tool_name": "Read", "session_id": "s1", "tool_input": {}, "tool_response": {}}
    run_hook(event, tmp_path)
    assert (tmp_path / ".acumen" / "observations").is_dir()
    assert len(read_observations(tmp_path)) == 1


def test_writes_to_session_file(tmp_path):
    """Hook writes to per-session JSONL file (<session_id>.jsonl)."""
    event = {
        "tool_name": "Bash",
        "session_id": "my-session",
        "tool_input": {"command": "ls"},
        "tool_response": {"exit_code": 0},
    }
    run_hook(event, tmp_path)
    session_file = tmp_path / ".acumen" / "observations" / "my-session.jsonl"
    assert session_file.exists()


def test_bash_error_detected(tmp_path):
    """Hook detects errors via PostToolUseFailure and classifies error_class."""
    event = {
        "hook_event_name": "PostToolUseFailure",
        "tool_name": "Bash",
        "session_id": "s2",
        "tool_input": {"command": "python foo.py"},
        "error": "zsh: command not found: python",
    }
    run_hook(event, tmp_path)
    obs = read_observations(tmp_path)
    assert obs[0]["outcome"] == "error"
    assert obs[0]["error_type"] == "tool_failure"
    assert obs[0]["error_class"] == "command_not_found"
    # No raw error_message field
    assert "error_message" not in obs[0]


def test_bash_success_detected(tmp_path):
    """Hook detects Bash success and classifies command_family."""
    event = {
        "tool_name": "Bash",
        "session_id": "s3",
        "tool_input": {"command": "git status"},
        "tool_response": {"exit_code": 0, "stdout": "ok"},
    }
    run_hook(event, tmp_path)
    obs = read_observations(tmp_path)
    assert obs[0]["outcome"] == "success"
    assert obs[0]["error_type"] is None
    assert obs[0]["command_family"] == "git"


def test_tool_error_field(tmp_path):
    """Hook classifies error_class from error field."""
    event = {
        "hook_event_name": "PostToolUseFailure",
        "tool_name": "Read",
        "session_id": "s4",
        "tool_input": {"file_path": "/nonexistent"},
        "error": "No such file or directory",
    }
    run_hook(event, tmp_path)
    obs = read_observations(tmp_path)
    assert obs[0]["outcome"] == "error"
    assert obs[0]["error_type"] == "tool_failure"
    assert obs[0]["error_class"] == "file_not_found"


# -- Tier 0.5 field classification --


def test_bash_command_classification(tmp_path):
    """Bash commands are classified into family and signature."""
    event = {
        "tool_name": "Bash",
        "session_id": "s-cls",
        "tool_input": {"command": "python3 -m pytest tests/ -v"},
        "tool_response": {"exit_code": 0},
    }
    run_hook(event, tmp_path)
    obs = read_observations(tmp_path)
    assert obs[0]["command_family"] == "test"
    assert obs[0]["command_signature"] == "pytest"


def test_write_tool_file_classification(tmp_path):
    """Write tool events get file_basename and path_pattern."""
    event = {
        "tool_name": "Write",
        "session_id": "s-file",
        "tool_input": {"file_path": "/project/tests/test_foo.py", "content": "pass"},
        "tool_response": {"success": True},
    }
    run_hook(event, tmp_path)
    obs = read_observations(tmp_path)
    assert obs[0]["file_basename"] == "test_foo.py"
    assert obs[0]["path_pattern"] == "tests_root"


def test_edit_tool_write_kind(tmp_path):
    """Edit tool always has write_kind='edit'."""
    event = {
        "tool_name": "Edit",
        "session_id": "s-edit",
        "tool_input": {"file_path": "/project/lib/foo.py"},
        "tool_response": {"success": True},
    }
    run_hook(event, tmp_path)
    obs = read_observations(tmp_path)
    assert obs[0]["write_kind"] == "edit"


def test_environment_tag(tmp_path):
    """Environment tag is derived from project root files."""
    # Create a pyproject.toml in the working directory
    (tmp_path / "pyproject.toml").write_text("[project]")
    event = {
        "tool_name": "Bash",
        "session_id": "s-env",
        "tool_input": {"command": "ls"},
        "tool_response": {"exit_code": 0},
    }
    run_hook(event, tmp_path)
    obs = read_observations(tmp_path)
    assert obs[0]["environment_tag"] == "python"


# -- Burst count tracking --


def test_burst_count_single_call(tmp_path):
    """Single call has burst_count=1."""
    event = {
        "tool_name": "Bash",
        "session_id": "s-burst",
        "tool_input": {"command": "ls"},
        "tool_response": {"exit_code": 0},
    }
    run_hook(event, tmp_path)
    obs = read_observations(tmp_path)
    assert obs[0]["burst_count"] == 1


def test_burst_count_consecutive_same_tool(tmp_path):
    """Consecutive same-tool calls increment burst_count."""
    for i in range(3):
        event = {
            "tool_name": "Bash",
            "session_id": "s-burst2",
            "tool_input": {"command": "ls"},
            "tool_response": {"exit_code": 0},
        }
        run_hook(event, tmp_path)
    obs = read_observations(tmp_path)
    assert obs[0]["burst_count"] == 1
    assert obs[1]["burst_count"] == 2
    assert obs[2]["burst_count"] == 3


def test_burst_count_resets_on_tool_change(tmp_path):
    """Burst count resets when tool_name changes."""
    run_hook({
        "tool_name": "Bash", "session_id": "s-reset",
        "tool_input": {"command": "ls"}, "tool_response": {"exit_code": 0},
    }, tmp_path)
    run_hook({
        "tool_name": "Read", "session_id": "s-reset",
        "tool_input": {"file_path": "/tmp/x"}, "tool_response": {},
    }, tmp_path)
    run_hook({
        "tool_name": "Bash", "session_id": "s-reset",
        "tool_input": {"command": "ls"}, "tool_response": {"exit_code": 0},
    }, tmp_path)
    obs = read_observations(tmp_path)
    assert obs[0]["burst_count"] == 1  # first Bash
    assert obs[1]["burst_count"] == 1  # Read (different tool)
    assert obs[2]["burst_count"] == 1  # Bash again (reset after Read)


# -- Security tests --


def test_does_not_capture_raw_command(tmp_path):
    """SECURITY: observation must NOT contain raw command text."""
    event = {
        "tool_name": "Bash",
        "session_id": "s-sec1",
        "tool_input": {"command": "curl -H 'Authorization: Bearer sk-secret123' https://api.example.com"},
        "tool_response": {"exit_code": 0},
    }
    run_hook(event, tmp_path)
    raw = (tmp_path / ".acumen" / "observations").glob("*.jsonl")
    raw_text = "".join(f.read_text() for f in raw)
    assert "sk-secret123" not in raw_text
    assert "curl" not in raw_text
    assert "api.example.com" not in raw_text
    assert "tool_input" not in raw_text


def test_does_not_capture_raw_path(tmp_path):
    """SECURITY: observation must NOT contain full file paths."""
    event = {
        "tool_name": "Write",
        "session_id": "s-sec2",
        "tool_input": {"file_path": "/Users/tom/secret-project/lib/foo.py", "content": "SECRET"},
        "tool_response": {"success": True},
    }
    run_hook(event, tmp_path)
    raw = (tmp_path / ".acumen" / "observations").glob("*.jsonl")
    raw_text = "".join(f.read_text() for f in raw)
    assert "/Users/tom/secret-project" not in raw_text
    assert "SECRET" not in raw_text
    assert "tool_input" not in raw_text
    # file_basename IS captured (Tier 0.5 derived field)
    obs = read_observations(tmp_path)
    assert obs[0]["file_basename"] == "foo.py"


def test_does_not_capture_tool_response_content(tmp_path):
    """SECURITY: observation must NOT contain tool_response content."""
    event = {
        "tool_name": "Read",
        "session_id": "s-sec3",
        "tool_input": {"file_path": "/etc/passwd"},
        "tool_response": {"content": "root:x:0:0:root:/root:/bin/bash"},
    }
    run_hook(event, tmp_path)
    raw = (tmp_path / ".acumen" / "observations").glob("*.jsonl")
    raw_text = "".join(f.read_text() for f in raw)
    assert "root:x:0:0" not in raw_text
    assert "/etc/passwd" not in raw_text
    assert "tool_response" not in raw_text


def test_does_not_capture_raw_error_message(tmp_path):
    """SECURITY: observation must NOT contain raw error message text."""
    event = {
        "hook_event_name": "PostToolUseFailure",
        "tool_name": "Bash",
        "session_id": "s-sec4",
        "tool_input": {"command": "cat /etc/shadow"},
        "error": "Permission denied: /etc/shadow contains sensitive data",
    }
    run_hook(event, tmp_path)
    raw = (tmp_path / ".acumen" / "observations").glob("*.jsonl")
    raw_text = "".join(f.read_text() for f in raw)
    assert "/etc/shadow" not in raw_text
    assert "sensitive data" not in raw_text
    assert "error_message" not in raw_text
    obs = read_observations(tmp_path)
    assert obs[0]["error_class"] == "permission_denied"


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
    """Multiple hook invocations append to the same session file."""
    for i in range(3):
        event = {"tool_name": f"Tool{i}", "session_id": "s8", "tool_input": {}, "tool_response": {}}
        run_hook(event, tmp_path)
    obs = read_observations(tmp_path)
    assert len(obs) == 3
    assert [o["tool_name"] for o in obs] == ["Tool0", "Tool1", "Tool2"]


# -- Index file --


def test_index_file_updated(tmp_path):
    """Hook updates index.json with session metadata."""
    event = {
        "tool_name": "Bash",
        "session_id": "idx-test",
        "tool_input": {"command": "ls"},
        "tool_response": {"exit_code": 0},
    }
    run_hook(event, tmp_path)
    index_path = tmp_path / ".acumen" / "observations" / "index.json"
    assert index_path.exists()
    index = json.loads(index_path.read_text())
    assert "idx-test" in index
    assert "first_seen" in index["idx-test"]
    assert "last_seen" in index["idx-test"]

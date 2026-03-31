"""Tier 0.5 field derivation. Classifies raw hook data into categorical fields.

Reads raw commands/paths/errors to derive categories, then the caller discards
the raw data. Only derived fields are persisted. Stdlib only.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

# (first_token, second_token_or_None) → signature
_SIGNATURE_MAP = {
    ("pytest", None): "pytest",
    ("jest", None): "jest",
    ("cargo", "test"): "cargo_test",
    ("go", "test"): "go_test",
    ("npm", "test"): "npm_test",
    ("npx", "jest"): "jest",
    ("ruff", "check"): "ruff_check",
    ("ruff", "format"): "ruff_format",
}

# Signatures that count as "test" family
_TEST_SIGS = {"pytest", "uv_pytest", "npm_test", "jest", "cargo_test", "go_test"}

_ERROR_PATTERNS = [
    ("command_not_found", re.compile(r"command not found|exit code 127", re.IGNORECASE)),
    ("file_not_found", re.compile(r"no such file|FileNotFoundError|ENOENT", re.IGNORECASE)),
    ("permission_denied", re.compile(r"permission denied|EACCES", re.IGNORECASE)),
    ("syntax_error", re.compile(r"SyntaxError|syntax error", re.IGNORECASE)),
    ("timeout", re.compile(r"timed? ?out|TimeoutError", re.IGNORECASE)),
    ("test_failure", re.compile(r"FAILED|failed,?\s+\d+\s+passed|\d+\s+failed", re.IGNORECASE)),
]


def classify_command_signature(tool_name: str, command: str | None) -> str | None:
    """Derive command_signature for test/build/lint/format commands."""
    if tool_name != "Bash" or not command:
        return None
    tokens = command.split()
    if not tokens:
        return None
    first = tokens[0]
    second = tokens[1] if len(tokens) > 1 else None

    # python/python3 -m pytest
    if first in ("python", "python3") and second == "-m" and len(tokens) > 2 and tokens[2] == "pytest":
        return "pytest"
    # uv run pytest
    if first == "uv" and second == "run" and len(tokens) > 2 and tokens[2] == "pytest":
        return "uv_pytest"

    # Table-driven lookup
    return _SIGNATURE_MAP.get((first, second)) or _SIGNATURE_MAP.get((first, None))


def classify_command_family(tool_name: str, command: str | None) -> str | None:
    """Derive command_family from tool_name and command string."""
    if tool_name != "Bash" or not command:
        return None
    tokens = command.split()
    if not tokens:
        return None
    first = tokens[0]

    # Signature-based: test, lint, format
    sig = classify_command_signature(tool_name, command)
    if sig in _TEST_SIGS:
        return "test"
    if sig in ("ruff_check",):
        return "lint"
    if sig in ("ruff_format",):
        return "format"

    # Build
    if first == "make":
        return "build"
    if first == "cargo" and len(tokens) > 1 and tokens[1] == "build":
        return "build"
    if first in ("npm", "npx") and len(tokens) > 2 and tokens[1] == "run" and tokens[2] == "build":
        return "build"

    # Lint (non-ruff)
    if first in ("eslint", "mypy", "pylint", "flake8"):
        return "lint"
    # Format (non-ruff)
    if first in ("black", "prettier", "autopep8", "yapf"):
        return "format"

    if first in ("python", "python3"):
        return "python"
    if first in ("npm", "npx", "node", "yarn", "pnpm"):
        return "node"
    if first == "git":
        return "git"
    if first in ("docker", "docker-compose"):
        return "docker"
    return "shell"


def classify_file_basename(tool_name: str, file_path: str | None) -> str | None:
    """Extract basename from file path for Write/Edit/Read tools."""
    if tool_name not in ("Write", "Edit", "Read") or not file_path:
        return None
    return os.path.basename(file_path) or None


def classify_path_pattern(tool_name: str, file_path: str | None) -> str | None:
    """Derive directory classification from full path for Write/Edit tools."""
    if tool_name not in ("Write", "Edit") or not file_path:
        return None
    for part in Path(file_path).parts:
        p = part.lower()
        if p in ("tests", "test"):
            return "tests_root"
        if p == "integration":
            return "integration_dir"
        if p == "src":
            return "src_dir"
        if p == "lib":
            return "lib_dir"
    return None


def classify_write_kind(tool_name: str, file_path: str | None) -> str | None:
    """Determine if a write operation is create or edit."""
    if tool_name == "Edit":
        return "edit"
    if tool_name != "Write" or not file_path:
        return None
    return "edit" if os.path.exists(file_path) else "create"


def classify_environment_tag(project_root: Path) -> str | None:
    """Detect project environment from project root files."""
    if (project_root / "pyproject.toml").exists() or (project_root / "setup.py").exists():
        return "python"
    if (project_root / "package.json").exists():
        return "node"
    if (project_root / "Cargo.toml").exists():
        return "rust"
    if (project_root / "go.mod").exists():
        return "go"
    return None


def classify_error_class(error_type: str | None, error_message: str | None) -> str | None:
    """Normalize error_type + error_message into an error_class tag."""
    if not error_type or not error_message:
        return None
    for class_name, pattern in _ERROR_PATTERNS:
        if pattern.search(error_message):
            return class_name
    return None


if __name__ == "__main__":
    # Hook entry point: reads raw event JSON from stdin, derives Tier 0.5
    # fields, discards raw data, writes per-session JSONL observation.
    import json
    import sys
    from datetime import datetime, timezone
    from pathlib import Path

    from store import append_observation, read_last_observation, update_index

    raw = sys.stdin.read().strip()
    if not raw:
        sys.exit(0)
    try:
        event = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    tool_name = event.get("tool_name", "")
    if not tool_name:
        sys.exit(0)

    session_id = event.get("session_id") or "unknown"
    hook_event = event.get("hook_event_name", "")
    error_msg = event.get("error", "")

    if hook_event == "PostToolUseFailure" or error_msg:
        outcome = "error"
        error_type = "tool_failure" if hook_event == "PostToolUseFailure" else "tool_error"
    else:
        outcome = "success"
        error_type = None

    # Extract raw values for classification only — NOT persisted
    tool_input = event.get("tool_input") or {}
    command = tool_input.get("command") if tool_name == "Bash" else None
    file_path = tool_input.get("file_path")
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    project_root = Path.cwd()
    scope_path = Path(".acumen")

    obs = {
        "tool_name": tool_name,
        "session_id": session_id,
        "timestamp": timestamp,
        "outcome": outcome,
        "error_type": error_type,
        "command_family": classify_command_family(tool_name, command),
        "command_signature": classify_command_signature(tool_name, command),
        "file_basename": classify_file_basename(tool_name, file_path),
        "path_pattern": classify_path_pattern(tool_name, file_path),
        "write_kind": classify_write_kind(tool_name, file_path),
        "environment_tag": classify_environment_tag(project_root),
        "error_class": classify_error_class(error_type, error_msg),
        "burst_count": 1,
    }

    # Burst tracking: check last observation in this session
    last = read_last_observation(scope_path, session_id)
    if last and last.get("tool_name") == tool_name:
        last_ts = last.get("timestamp", "")
        if last_ts:
            try:
                fmt = "%Y-%m-%dT%H:%M:%SZ"
                curr = datetime.strptime(timestamp, fmt).replace(tzinfo=timezone.utc)
                prev = datetime.strptime(last_ts, fmt).replace(tzinfo=timezone.utc)
                if (curr - prev).total_seconds() < 60:
                    obs["burst_count"] = last.get("burst_count", 1) + 1
            except (ValueError, TypeError):
                pass

    append_observation(scope_path, session_id, obs)
    update_index(scope_path, session_id, timestamp)

"""Tests for lib/store.py -- observation and insight storage."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from lib.store import (
    read_observations, write_insight, read_insights, resolve_scope_path,
    append_observation, read_last_observation, update_index, rotate_observations,
)


# -- read_observations --


def test_read_observations_empty_dir(tmp_path):
    """Returns empty list when observations directory doesn't exist."""
    obs, errors = read_observations(tmp_path)
    assert obs == []
    assert errors == 0


def test_read_observations_empty_file(tmp_path):
    """Returns empty list when JSONL file exists but is empty."""
    obs_dir = tmp_path / "observations"
    obs_dir.mkdir(parents=True)
    (obs_dir / "2026-03-29.jsonl").write_text("")
    obs, errors = read_observations(tmp_path)
    assert obs == []
    assert errors == 0


def test_read_observations_single_file(tmp_path):
    """Reads observations from a single daily JSONL file."""
    obs_dir = tmp_path / "observations"
    obs_dir.mkdir(parents=True)
    records = [
        {"tool_name": "Bash", "outcome": "success", "timestamp": "2026-03-29T10:00:00Z"},
        {"tool_name": "Read", "outcome": "error", "timestamp": "2026-03-29T10:01:00Z"},
    ]
    (obs_dir / "2026-03-29.jsonl").write_text(
        "\n".join(json.dumps(r) for r in records) + "\n"
    )
    result, errors = read_observations(tmp_path)
    assert len(result) == 2
    assert result[0]["tool_name"] == "Bash"
    assert result[1]["tool_name"] == "Read"
    assert errors == 0


def test_read_observations_multiple_files(tmp_path):
    """Reads across multiple daily files, sorted by filename."""
    obs_dir = tmp_path / "observations"
    obs_dir.mkdir(parents=True)
    (obs_dir / "2026-03-28.jsonl").write_text(
        json.dumps({"tool_name": "A", "timestamp": "2026-03-28T00:00:00Z"}) + "\n"
    )
    (obs_dir / "2026-03-29.jsonl").write_text(
        json.dumps({"tool_name": "B", "timestamp": "2026-03-29T00:00:00Z"}) + "\n"
    )
    result, errors = read_observations(tmp_path)
    assert len(result) == 2
    assert result[0]["tool_name"] == "A"
    assert result[1]["tool_name"] == "B"
    assert errors == 0


def test_read_observations_days_filter(tmp_path):
    """Only reads files within the specified days window."""
    obs_dir = tmp_path / "observations"
    obs_dir.mkdir(parents=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    old = (datetime.now(timezone.utc) - timedelta(days=10)).strftime("%Y-%m-%d")
    (obs_dir / f"{old}.jsonl").write_text(
        json.dumps({"tool_name": "Old"}) + "\n"
    )
    (obs_dir / f"{today}.jsonl").write_text(
        json.dumps({"tool_name": "Recent"}) + "\n"
    )
    result, errors = read_observations(tmp_path, days=7)
    assert len(result) == 1
    assert result[0]["tool_name"] == "Recent"
    assert errors == 0


def test_read_observations_skips_corrupted_lines(tmp_path, capsys):
    """Skips corrupted JSONL lines and reports error count."""
    obs_dir = tmp_path / "observations"
    obs_dir.mkdir(parents=True)
    content = (
        json.dumps({"tool_name": "Good"}) + "\n"
        + "not valid json\n"
        + json.dumps({"tool_name": "AlsoGood"}) + "\n"
    )
    (obs_dir / "2026-03-29.jsonl").write_text(content)
    result, errors = read_observations(tmp_path)
    assert len(result) == 2
    assert result[0]["tool_name"] == "Good"
    assert result[1]["tool_name"] == "AlsoGood"
    assert errors == 1


# -- write_insight / read_insights --


def test_write_insight_creates_file(tmp_path):
    """Creates insights.json if it doesn't exist."""
    insight = {"id": "i1", "description": "Use Read before Edit", "score": 0.8}
    write_insight(tmp_path, insight)
    assert (tmp_path / "insights.json").exists()
    data = json.loads((tmp_path / "insights.json").read_text())
    assert len(data) == 1
    assert data[0]["id"] == "i1"


def test_write_insight_appends(tmp_path):
    """Appends without overwriting existing insights."""
    write_insight(tmp_path, {"id": "i1", "description": "first"})
    write_insight(tmp_path, {"id": "i2", "description": "second"})
    data = json.loads((tmp_path / "insights.json").read_text())
    assert len(data) == 2
    assert data[0]["id"] == "i1"
    assert data[1]["id"] == "i2"


def test_write_insight_atomic(tmp_path):
    """Write uses tmp-rename pattern (file should be valid JSON after write)."""
    for i in range(10):
        write_insight(tmp_path, {"id": f"i{i}", "description": f"insight {i}"})
    data = json.loads((tmp_path / "insights.json").read_text())
    assert len(data) == 10


def test_read_insights_empty(tmp_path):
    """Returns empty list when insights.json doesn't exist."""
    assert read_insights(tmp_path) == []


def test_read_insights_corrupted_file(tmp_path):
    """Returns empty list when insights.json is corrupted."""
    (tmp_path / "insights.json").write_text("not json")
    assert read_insights(tmp_path) == []


def test_read_insights_roundtrip(tmp_path):
    """Write then read returns the same data."""
    insight = {"id": "i1", "description": "test", "score": 0.5}
    write_insight(tmp_path, insight)
    result = read_insights(tmp_path)
    assert len(result) == 1
    assert result[0] == insight


# -- resolve_scope_path --


def test_resolve_scope_path_project():
    """Project scope returns .acumen/ in current directory."""
    path = resolve_scope_path("project")
    assert path == Path(".acumen")


def test_resolve_scope_path_global():
    """Global scope returns ~/.claude/acumen/."""
    path = resolve_scope_path("global")
    assert path == Path.home() / ".claude" / "acumen"


def test_resolve_scope_path_default():
    """Default scope is project."""
    assert resolve_scope_path() == resolve_scope_path("project")


def test_resolve_scope_path_invalid():
    """Invalid scope raises ValueError."""
    try:
        resolve_scope_path("invalid")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


# -- append_observation --


def test_append_observation_creates_session_file(tmp_path):
    """Creates per-session JSONL file in observations/."""
    obs = {"tool_name": "Bash", "session_id": "sess-1", "timestamp": "2026-03-30T10:00:00Z"}
    append_observation(tmp_path, "sess-1", obs)
    f = tmp_path / "observations" / "sess-1.jsonl"
    assert f.exists()
    lines = f.read_text().strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["tool_name"] == "Bash"


def test_append_observation_appends(tmp_path):
    """Multiple appends to same session file."""
    for i in range(3):
        obs = {"tool_name": f"Tool{i}", "session_id": "s1", "timestamp": f"2026-03-30T10:0{i}:00Z"}
        append_observation(tmp_path, "s1", obs)
    f = tmp_path / "observations" / "s1.jsonl"
    lines = f.read_text().strip().splitlines()
    assert len(lines) == 3
    assert json.loads(lines[2])["tool_name"] == "Tool2"


def test_append_observation_creates_dir(tmp_path):
    """Creates observations/ directory if missing."""
    obs = {"tool_name": "Read", "session_id": "s1", "timestamp": "2026-03-30T10:00:00Z"}
    append_observation(tmp_path, "s1", obs)
    assert (tmp_path / "observations").is_dir()


# -- read_last_observation --


def test_read_last_observation_empty(tmp_path):
    """Returns None when session file doesn't exist."""
    assert read_last_observation(tmp_path, "nonexistent") is None


def test_read_last_observation_returns_last(tmp_path):
    """Returns the last valid observation from a session file."""
    append_observation(tmp_path, "s1", {"tool_name": "A", "timestamp": "2026-03-30T10:00:00Z"})
    append_observation(tmp_path, "s1", {"tool_name": "B", "timestamp": "2026-03-30T10:01:00Z"})
    last = read_last_observation(tmp_path, "s1")
    assert last["tool_name"] == "B"


def test_read_last_observation_skips_corrupted(tmp_path):
    """Skips corrupted trailing lines, returns last valid record."""
    obs_dir = tmp_path / "observations"
    obs_dir.mkdir(parents=True)
    f = obs_dir / "s1.jsonl"
    f.write_text(json.dumps({"tool_name": "Good"}) + "\nnot json\n")
    last = read_last_observation(tmp_path, "s1")
    assert last["tool_name"] == "Good"


# -- update_index --


def test_update_index_creates_file(tmp_path):
    """Creates index.json with session entry."""
    (tmp_path / "observations").mkdir(parents=True)
    update_index(tmp_path, "sess-1", "2026-03-30T10:00:00Z")
    idx = json.loads((tmp_path / "observations" / "index.json").read_text())
    assert "sess-1" in idx
    assert idx["sess-1"]["first_seen"] == "2026-03-30T10:00:00Z"
    assert idx["sess-1"]["last_seen"] == "2026-03-30T10:00:00Z"


def test_update_index_updates_last_seen(tmp_path):
    """Second update changes last_seen but preserves first_seen."""
    (tmp_path / "observations").mkdir(parents=True)
    update_index(tmp_path, "sess-1", "2026-03-30T10:00:00Z")
    update_index(tmp_path, "sess-1", "2026-03-30T11:00:00Z")
    idx = json.loads((tmp_path / "observations" / "index.json").read_text())
    assert idx["sess-1"]["first_seen"] == "2026-03-30T10:00:00Z"
    assert idx["sess-1"]["last_seen"] == "2026-03-30T11:00:00Z"


def test_update_index_multiple_sessions(tmp_path):
    """Index tracks multiple sessions independently."""
    (tmp_path / "observations").mkdir(parents=True)
    update_index(tmp_path, "s1", "2026-03-30T10:00:00Z")
    update_index(tmp_path, "s2", "2026-03-30T11:00:00Z")
    idx = json.loads((tmp_path / "observations" / "index.json").read_text())
    assert "s1" in idx
    assert "s2" in idx


def test_update_index_creates_obs_dir(tmp_path):
    """Creates observations/ directory if needed."""
    update_index(tmp_path, "s1", "2026-03-30T10:00:00Z")
    assert (tmp_path / "observations" / "index.json").exists()


# -- read_observations with per-session files --


def test_read_observations_session_files(tmp_path):
    """Reads observations from per-session JSONL files."""
    now = datetime.now(timezone.utc).isoformat()
    append_observation(tmp_path, "s1", {"tool_name": "Bash", "timestamp": now})
    append_observation(tmp_path, "s1", {"tool_name": "Read", "timestamp": now})
    result, errors = read_observations(tmp_path)
    assert len(result) == 2
    assert errors == 0


def test_read_observations_session_files_filtered(tmp_path):
    """Session file records are filtered by their timestamp field."""
    now = datetime.now(timezone.utc)
    old = (now - timedelta(days=10)).isoformat()
    append_observation(tmp_path, "s1", {"tool_name": "Old", "timestamp": old})
    append_observation(tmp_path, "s1", {"tool_name": "New", "timestamp": now.isoformat()})
    result, errors = read_observations(tmp_path, days=7)
    assert len(result) == 1
    assert result[0]["tool_name"] == "New"
    assert errors == 0


def test_read_observations_mixed_formats(tmp_path):
    """Reads both date-based and session-based JSONL files."""
    obs_dir = tmp_path / "observations"
    obs_dir.mkdir(parents=True)
    now = datetime.now(timezone.utc)
    today = now.strftime("%Y-%m-%d")
    # Date-based file
    (obs_dir / f"{today}.jsonl").write_text(
        json.dumps({"tool_name": "DateBased", "timestamp": now.isoformat()}) + "\n"
    )
    # Session-based file
    (obs_dir / "sess-1.jsonl").write_text(
        json.dumps({"tool_name": "SessionBased", "timestamp": now.isoformat()}) + "\n"
    )
    result, errors = read_observations(tmp_path)
    names = [r["tool_name"] for r in result]
    assert "DateBased" in names
    assert "SessionBased" in names
    assert errors == 0


# -- rotate_observations --


def test_rotate_moves_old_sessions(tmp_path):
    """Archives session files older than max_age_days."""
    obs_dir = tmp_path / "observations"
    obs_dir.mkdir(parents=True)
    old_ts = (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
    (obs_dir / "old-sess.jsonl").write_text(json.dumps({"tool_name": "X"}) + "\n")
    index = {"old-sess": {"path": "old-sess.jsonl", "first_seen": old_ts, "last_seen": old_ts}}
    (obs_dir / "index.json").write_text(json.dumps(index))

    count = rotate_observations(tmp_path, max_age_days=30)
    assert count == 1
    assert not (obs_dir / "old-sess.jsonl").exists()
    assert (obs_dir / "archive" / "old-sess.jsonl").exists()
    idx = json.loads((obs_dir / "index.json").read_text())
    assert "old-sess" not in idx


def test_rotate_keeps_recent(tmp_path):
    """Does not archive recent session files."""
    obs_dir = tmp_path / "observations"
    obs_dir.mkdir(parents=True)
    now = datetime.now(timezone.utc).isoformat()
    (obs_dir / "recent.jsonl").write_text(json.dumps({"tool_name": "X"}) + "\n")
    index = {"recent": {"path": "recent.jsonl", "first_seen": now, "last_seen": now}}
    (obs_dir / "index.json").write_text(json.dumps(index))

    count = rotate_observations(tmp_path)
    assert count == 0
    assert (obs_dir / "recent.jsonl").exists()


def test_rotate_no_index(tmp_path):
    """Returns 0 when no index file exists."""
    assert rotate_observations(tmp_path) == 0

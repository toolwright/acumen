"""Tests for lib/store.py -- observation and insight storage."""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from lib.store import read_observations, write_insight, read_insights, resolve_scope_path


# -- read_observations --


def test_read_observations_empty_dir(tmp_path):
    """Returns empty list when observations directory doesn't exist."""
    assert read_observations(tmp_path) == []


def test_read_observations_empty_file(tmp_path):
    """Returns empty list when JSONL file exists but is empty."""
    obs_dir = tmp_path / "observations"
    obs_dir.mkdir(parents=True)
    (obs_dir / "2026-03-29.jsonl").write_text("")
    assert read_observations(tmp_path) == []


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
    result = read_observations(tmp_path)
    assert len(result) == 2
    assert result[0]["tool_name"] == "Bash"
    assert result[1]["tool_name"] == "Read"


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
    result = read_observations(tmp_path)
    assert len(result) == 2
    assert result[0]["tool_name"] == "A"
    assert result[1]["tool_name"] == "B"


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
    result = read_observations(tmp_path, days=7)
    assert len(result) == 1
    assert result[0]["tool_name"] == "Recent"


def test_read_observations_skips_corrupted_lines(tmp_path, capsys):
    """Skips corrupted JSONL lines without crashing."""
    obs_dir = tmp_path / "observations"
    obs_dir.mkdir(parents=True)
    content = (
        json.dumps({"tool_name": "Good"}) + "\n"
        + "not valid json\n"
        + json.dumps({"tool_name": "AlsoGood"}) + "\n"
    )
    (obs_dir / "2026-03-29.jsonl").write_text(content)
    result = read_observations(tmp_path)
    assert len(result) == 2
    assert result[0]["tool_name"] == "Good"
    assert result[1]["tool_name"] == "AlsoGood"


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

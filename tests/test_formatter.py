"""Tests for lib/formatter.py -- CLI output formatting."""

from lib.formatter import format_insights, format_status


def _obs(tool="Bash", outcome="success", session="s1", ts="2026-03-29T12:00:00"):
    return {"tool_name": tool, "outcome": outcome, "session_id": session, "timestamp": ts}


def _insight(description="Bash fails during tests", combined=0.75, category="error_pattern", evidence_count=8):
    return {
        "description": description,
        "combined": combined,
        "category": category,
        "evidence_count": evidence_count,
    }


# --- format_status ---


def test_status_no_data():
    result = format_status([], [])
    assert "No observation data yet" in result


def test_status_with_observations():
    obs = [_obs(session="s1"), _obs(session="s2"), _obs(outcome="error", session="s1")]
    result = format_status(obs, [])
    assert "Sessions observed: 2" in result
    assert "Total observations: 3" in result
    assert "Error rate: 33%" in result


def test_status_with_insights():
    obs = [_obs()]
    insights = [_insight("Fix test runner", combined=0.82)]
    result = format_status(obs, insights)
    assert "Active insights: 1" in result
    assert "[0.82]" in result
    assert "Fix test runner" in result


def test_status_shows_daily_activity():
    obs = [
        _obs(ts="2026-03-28T10:00:00"),
        _obs(ts="2026-03-28T11:00:00"),
        _obs(ts="2026-03-29T09:00:00"),
    ]
    result = format_status(obs, [])
    assert "2026-03-28: 2" in result
    assert "2026-03-29: 1" in result


def test_status_shows_last_reflection():
    result = format_status([_obs()], [], last_reflection="2026-03-29T14:00:00")
    assert "Last reflection: 2026-03-29T14:00:00" in result


def test_status_top_insights_limited_to_5():
    obs = [_obs()]
    insights = [_insight(f"Insight {i}", combined=i / 10) for i in range(8)]
    result = format_status(obs, insights)
    # Should show first 5 only
    assert "Insight 4" in result
    assert "Insight 5" not in result


def test_format_status_shows_eval_tier(tmp_path):
    """format_status shows eval tier when eval-config.json exists."""
    import json
    acumen_dir = tmp_path / ".acumen"
    acumen_dir.mkdir()
    (acumen_dir / "eval-config.json").write_text(json.dumps({
        "tier": 1, "confidence": "HIGH", "test_cmd": "python3 -m pytest",
        "lint_cmd": None, "test_latency_ms": 800, "fast_for_stop_gate": True,
    }))
    output = format_status([], [], project_root=tmp_path)
    assert "HIGH" in output or "Test suite" in output


def test_format_status_tier3_shows_suggestion(tmp_path):
    """Tier 3 config shows low-confidence note in status output."""
    import json
    acumen_dir = tmp_path / ".acumen"
    acumen_dir.mkdir()
    (acumen_dir / "eval-config.json").write_text(json.dumps({
        "tier": 3, "confidence": "LOW", "test_cmd": None,
        "lint_cmd": None, "test_latency_ms": 0, "fast_for_stop_gate": False,
    }))
    output = format_status([], [], project_root=tmp_path)
    assert "test" in output.lower() or "LOW" in output


# --- format_insights ---


def test_insights_empty():
    result = format_insights([])
    assert "No insights yet" in result


def test_insights_with_data():
    insights = [
        _insight("Bash fails during tests", combined=0.75, evidence_count=8),
        _insight("Write tool retries often", combined=0.50, category="retry_pattern", evidence_count=3),
    ]
    result = format_insights(insights)
    assert "2 insight(s)" in result
    assert "1. [0.75] (error_pattern) Bash fails during tests" in result
    assert "Evidence: 8 observations" in result
    assert "2. [0.50] (retry_pattern) Write tool retries often" in result
    assert "Evidence: 3 observations" in result

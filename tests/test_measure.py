"""Tests for lib/measure.py -- failure recurrence tracking."""

import json
from pathlib import Path

from lib.measure import (
    EffectivenessRecord,
    measure_effectiveness,
    read_effectiveness,
    save_effectiveness,
)


def _obs(tool_name="Bash", command_family="python", outcome="success",
         error_class=None, session_id="s1", timestamp="2026-03-20T10:00:00Z"):
    return {
        "tool_name": tool_name,
        "command_family": command_family,
        "outcome": outcome,
        "error_class": error_class,
        "session_id": session_id,
        "timestamp": timestamp,
    }


def _rule(rule_id="rule-1", pattern_kind="python_launcher",
          target_tool="Bash", trigger_class="command_not_found",
          applied_at="2026-03-15T00:00:00Z"):
    return {
        "id": rule_id, "type": "failure",
        "pattern_kind": pattern_kind, "target_tool": target_tool,
        "trigger_class": trigger_class, "scope": "project",
        "status": "applied", "applied": applied_at,
    }


def _make_obs_list(total, error_count, command_family="python",
                   tool_name="Bash", error_class="command_not_found",
                   session_prefix="s", day_base=20):
    """Build a list with `total` observations, `error_count` of which are errors."""
    obs = []
    for i in range(total):
        is_err = i < error_count
        obs.append(_obs(
            tool_name=tool_name,
            command_family=command_family,
            outcome="error" if is_err else "success",
            error_class=error_class if is_err else None,
            session_id=f"{session_prefix}{i % 5}",
            timestamp=f"2026-03-{day_base + (i % 10):02d}T10:00:00Z",
        ))
    return obs


# --- Effective verdict ---

def test_effective_verdict():
    """After rate < before rate * 0.5 → effective."""
    rule = _rule()
    before = _make_obs_list(100, 20, day_base=1)   # 20% error rate
    after = _make_obs_list(100, 5, day_base=22)     # 5% error rate
    rec = measure_effectiveness(rule, before, after, after_days=7)
    assert rec.verdict == "effective"
    assert rec.target_pattern_before == 20.0
    assert rec.target_pattern_after == 5.0


# --- Harmful verdict ---

def test_harmful_verdict():
    """After rate > before rate * 1.1 → harmful."""
    rule = _rule()
    before = _make_obs_list(100, 10, day_base=1)    # 10% error rate
    after = _make_obs_list(100, 15, day_base=22)     # 15% error rate
    rec = measure_effectiveness(rule, before, after, after_days=7)
    assert rec.verdict == "harmful"


# --- Neutral verdict ---

def test_neutral_verdict():
    """Rate stayed about the same → neutral."""
    rule = _rule()
    before = _make_obs_list(100, 10, day_base=1)    # 10% error rate
    after = _make_obs_list(100, 9, day_base=22)      # 9% error rate
    rec = measure_effectiveness(rule, before, after, after_days=7)
    assert rec.verdict == "neutral"


# --- Pending: insufficient events ---

def test_pending_insufficient_events_before():
    """< 50 events in before window → pending."""
    rule = _rule()
    before = _make_obs_list(30, 5, day_base=1)
    after = _make_obs_list(100, 5, day_base=22)
    rec = measure_effectiveness(rule, before, after, after_days=7)
    assert rec.verdict == "pending"


def test_pending_insufficient_events_after():
    """< 50 events in after window → pending."""
    rule = _rule()
    before = _make_obs_list(100, 10, day_base=1)
    after = _make_obs_list(30, 2, day_base=22)
    rec = measure_effectiveness(rule, before, after, after_days=7)
    assert rec.verdict == "pending"


# --- Pending: insufficient time ---

def test_pending_insufficient_time():
    """< 7 days in after window → pending."""
    rule = _rule()
    before = _make_obs_list(100, 10, day_base=1)
    after = _make_obs_list(100, 2, day_base=22)
    rec = measure_effectiveness(rule, before, after, after_days=5)
    assert rec.verdict == "pending"


# --- Denominator uses command_family ---

def test_denominator_uses_command_family():
    """Only events with matching command_family count toward denominator."""
    rule = _rule(target_tool="Bash", trigger_class="command_not_found")
    # 50 python events (10 errors) + 50 node events (0 errors)
    before_python = _make_obs_list(50, 10, command_family="python", day_base=1)
    before_node = _make_obs_list(50, 0, command_family="node", day_base=1)
    after_python = _make_obs_list(50, 2, command_family="python", day_base=22)
    after_node = _make_obs_list(50, 0, command_family="node", day_base=22)

    rec = measure_effectiveness(
        rule, before_python + before_node, after_python + after_node, after_days=7)
    # Rate should be based on python events only: 10/50*100=20, 2/50*100=4
    assert rec.target_pattern_before == 20.0
    assert rec.target_pattern_after == 4.0
    assert rec.verdict == "effective"


# --- Denominator falls back to tool_name ---

def test_denominator_fallback_to_tool_name():
    """When no command_family on observations, filter by tool_name only."""
    rule = _rule(target_tool="Edit", trigger_class="file_not_found",
                 pattern_kind="file_not_found")
    before = _make_obs_list(60, 12, tool_name="Edit", command_family=None,
                            error_class="file_not_found", day_base=1)
    after = _make_obs_list(60, 3, tool_name="Edit", command_family=None,
                           error_class="file_not_found", day_base=22)
    rec = measure_effectiveness(rule, before, after, after_days=7)
    assert rec.target_pattern_before == 20.0
    assert rec.target_pattern_after == 5.0
    assert rec.verdict == "effective"


# --- Sessions observed ---

def test_sessions_observed():
    """sessions_observed counts distinct session_ids in after window."""
    rule = _rule()
    before = _make_obs_list(50, 10, day_base=1)
    after = _make_obs_list(50, 2, session_prefix="after_s", day_base=22)
    rec = measure_effectiveness(rule, before, after, after_days=7)
    assert rec.sessions_observed == 5  # after_s0..after_s4


# --- Retained at 2 weeks ---

def test_retained_at_2_weeks_true():
    """If after_days >= 14 and status is still applied → True."""
    rule = _rule()
    before = _make_obs_list(100, 20, day_base=1)
    after = _make_obs_list(100, 5, day_base=22)
    rec = measure_effectiveness(rule, before, after, after_days=14)
    assert rec.retained_at_2_weeks is True


def test_retained_at_2_weeks_none():
    """If after_days < 14 → None (not yet determinable)."""
    rule = _rule()
    before = _make_obs_list(100, 20, day_base=1)
    after = _make_obs_list(100, 5, day_base=22)
    rec = measure_effectiveness(rule, before, after, after_days=10)
    assert rec.retained_at_2_weeks is None


# --- EffectivenessRecord fields ---

def test_record_has_rule_id_and_applied_at():
    rule = _rule(rule_id="r-42", applied_at="2026-03-10T00:00:00Z")
    before = _make_obs_list(100, 10, day_base=1)
    after = _make_obs_list(100, 2, day_base=22)
    rec = measure_effectiveness(rule, before, after, after_days=7)
    assert rec.rule_id == "r-42"
    assert rec.applied_at == "2026-03-10T00:00:00Z"


# --- Read/save roundtrip ---

def test_read_effectiveness_empty(tmp_path):
    """No file → empty list."""
    assert read_effectiveness(tmp_path) == []


def test_save_and_read_roundtrip(tmp_path):
    """Save then read returns same records."""
    rec = EffectivenessRecord(
        rule_id="r-1", applied_at="2026-03-15T00:00:00Z",
        sessions_observed=5, target_pattern_before=20.0,
        target_pattern_after=5.0, adherence_rate=None,
        verdict="effective", retained_at_2_weeks=True,
    )
    save_effectiveness(tmp_path, [rec])
    loaded = read_effectiveness(tmp_path)
    assert len(loaded) == 1
    assert loaded[0].rule_id == "r-1"
    assert loaded[0].verdict == "effective"


def test_save_effectiveness_atomic(tmp_path):
    """No .tmp files left behind after save."""
    rec = EffectivenessRecord(
        rule_id="r-1", applied_at="2026-03-15T00:00:00Z",
        sessions_observed=5, target_pattern_before=20.0,
        target_pattern_after=5.0, adherence_rate=None,
        verdict="effective", retained_at_2_weeks=None,
    )
    save_effectiveness(tmp_path, [rec])
    assert list(tmp_path.glob("*.tmp")) == []
    assert (tmp_path / "effectiveness.json").exists()

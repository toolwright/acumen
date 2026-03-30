"""Tests for lib/scorer.py -- confidence/impact scoring and dedup."""

from datetime import datetime, timedelta, timezone

from lib.scorer import dedup_insights, filter_valid_insights, rank_insights, score_insight, validate_insight


def _obs(tool="Bash", outcome="success", days_ago=0):
    """Helper: create a minimal observation dict."""
    ts = (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat()
    return {"tool_name": tool, "outcome": outcome, "timestamp": ts}


def _insight(description="use git status", evidence_count=5, category="pattern"):
    return {
        "description": description,
        "evidence_count": evidence_count,
        "category": category,
    }


# --- score_insight ---


def test_more_observations_score_higher():
    obs_10 = [_obs() for _ in range(10)]
    obs_2 = [_obs() for _ in range(2)]
    s10 = score_insight(_insight(evidence_count=10), obs_10)
    s2 = score_insight(_insight(evidence_count=2), obs_2)
    assert s10["combined"] > s2["combined"]


def test_recent_observations_score_higher():
    recent = [_obs(days_ago=0) for _ in range(5)]
    old = [_obs(days_ago=6) for _ in range(5)]
    sr = score_insight(_insight(), recent)
    so = score_insight(_insight(), old)
    assert sr["confidence"] > so["confidence"]


def test_failure_patterns_score_higher():
    failures = [_obs(outcome="error") for _ in range(5)]
    successes = [_obs(outcome="success") for _ in range(5)]
    sf = score_insight(_insight(category="error_pattern"), failures)
    ss = score_insight(_insight(category="pattern"), successes)
    assert sf["impact"] > ss["impact"]


def test_score_zero_observations():
    s = score_insight(_insight(), [])
    assert s["confidence"] == 0.0
    assert s["impact"] == 0.0
    assert s["combined"] == 0.0


def test_score_returns_bounded_values():
    obs = [_obs(outcome="error") for _ in range(100)]
    s = score_insight(_insight(evidence_count=100, category="error_pattern"), obs)
    assert 0.0 <= s["confidence"] <= 1.0
    assert 0.0 <= s["impact"] <= 1.0
    assert 0.0 <= s["combined"] <= 1.0


# --- rank_insights ---


def test_rank_sorts_by_combined_desc():
    insights = [
        {"description": "low", "combined": 0.2},
        {"description": "high", "combined": 0.9},
        {"description": "mid", "combined": 0.5},
    ]
    ranked = rank_insights(insights)
    assert [i["description"] for i in ranked] == ["high", "mid", "low"]


def test_rank_empty_list():
    assert rank_insights([]) == []


# --- dedup_insights ---


def test_dedup_merges_matching_descriptions():
    new = [_insight("use git status", evidence_count=3)]
    existing = [_insight("use git status", evidence_count=5)]
    merged = dedup_insights(new, existing)
    assert len(merged) == 1
    assert merged[0]["evidence_count"] == 8


def test_dedup_keeps_distinct():
    new = [_insight("use ruff")]
    existing = [_insight("use git status")]
    merged = dedup_insights(new, existing)
    assert len(merged) == 2


def test_dedup_empty_inputs():
    assert dedup_insights([], []) == []
    assert len(dedup_insights([_insight()], [])) == 1
    assert len(dedup_insights([], [_insight()])) == 1


# --- validate_insight ---


def test_validate_valid_insight():
    ins = {"description": "Use python3", "category": "correction", "evidence_count": 5, "tools": ["Bash"]}
    assert validate_insight(ins) is True


def test_validate_missing_description():
    ins = {"category": "correction", "evidence_count": 5, "tools": ["Bash"]}
    assert validate_insight(ins) is False


def test_validate_empty_description():
    ins = {"description": "", "category": "correction", "evidence_count": 5, "tools": ["Bash"]}
    assert validate_insight(ins) is False


def test_validate_missing_category():
    ins = {"description": "test", "evidence_count": 5, "tools": ["Bash"]}
    assert validate_insight(ins) is False


def test_validate_negative_evidence():
    ins = {"description": "test", "category": "correction", "evidence_count": -1, "tools": ["Bash"]}
    assert validate_insight(ins) is False


def test_validate_non_dict():
    assert validate_insight("not a dict") is False
    assert validate_insight(None) is False
    assert validate_insight(42) is False


def test_validate_tools_not_list():
    ins = {"description": "test", "category": "correction", "evidence_count": 5, "tools": "Bash"}
    assert validate_insight(ins) is False


def test_filter_valid_insights_drops_invalid():
    insights = [
        {"description": "good", "category": "correction", "evidence_count": 5, "tools": ["Bash"]},
        {"description": "", "category": "bad", "evidence_count": 0, "tools": []},
        "not a dict",
        {"missing": "fields"},
    ]
    valid = filter_valid_insights(insights)
    assert len(valid) == 1
    assert valid[0]["description"] == "good"

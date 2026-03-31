"""Tests for lib/cluster.py -- failure clustering for rule proposals."""

from lib.cluster import cluster_failures


def _err(tool_name="Bash", error_class="command_not_found",
         command_family="shell", session_id="s1", day="28"):
    """Shorthand for an error observation."""
    return {
        "tool_name": tool_name,
        "outcome": "error",
        "error_type": "tool_failure",
        "error_class": error_class,
        "command_family": command_family,
        "session_id": session_id,
        "timestamp": f"2026-03-{day}T10:00:00Z",
    }


def _ok(tool_name="Bash", command_family="shell", session_id="s1", day="28"):
    """Shorthand for a success observation."""
    return {
        "tool_name": tool_name,
        "outcome": "success",
        "error_type": None,
        "error_class": None,
        "command_family": command_family,
        "session_id": session_id,
        "timestamp": f"2026-03-{day}T10:00:00Z",
    }


def test_empty_observations():
    """Empty input returns empty list."""
    assert cluster_failures([]) == []


def test_passes_all_guardrails():
    """5 observations, 3 sessions, 2+ days → cluster returned."""
    obs = [
        _err(session_id="s1", day="28"),
        _err(session_id="s1", day="28"),
        _err(session_id="s2", day="29"),
        _err(session_id="s2", day="29"),
        _err(session_id="s3", day="30"),
    ]
    clusters = cluster_failures(obs)
    assert len(clusters) == 1
    c = clusters[0]
    assert c.tool_name == "Bash"
    assert c.error_class == "command_not_found"
    assert c.pattern_kind == "command_not_found"
    assert c.observation_count == 5
    assert c.session_count == 3
    assert c.day_count == 3


def test_below_min_observations():
    """Only 3 observations → no cluster (needs 5)."""
    obs = [
        _err(session_id="s1", day="28"),
        _err(session_id="s2", day="29"),
        _err(session_id="s3", day="30"),
    ]
    assert cluster_failures(obs) == []


def test_below_min_sessions():
    """5 observations but only 1 session → no cluster (needs 3)."""
    obs = [
        _err(session_id="s1", day="28"),
        _err(session_id="s1", day="29"),
        _err(session_id="s1", day="30"),
        _err(session_id="s1", day="30"),
        _err(session_id="s1", day="30"),
    ]
    assert cluster_failures(obs) == []


def test_below_min_days():
    """5 observations, 3 sessions, but all on 1 day → no cluster (needs 2)."""
    obs = [
        _err(session_id="s1", day="30"),
        _err(session_id="s2", day="30"),
        _err(session_id="s3", day="30"),
        _err(session_id="s3", day="30"),
        _err(session_id="s3", day="30"),
    ]
    assert cluster_failures(obs) == []


def test_only_errors_clustered():
    """Success observations are ignored; only errors count."""
    obs = [
        _ok(session_id="s1", day="28"),
        _ok(session_id="s2", day="29"),
        _ok(session_id="s3", day="30"),
        _err(session_id="s1", day="28"),
        _err(session_id="s2", day="29"),
    ]
    # Only 2 errors → below threshold
    assert cluster_failures(obs) == []


def test_multiple_distinct_clusters():
    """Two different error_class groups each passing guardrails → two clusters."""
    obs = []
    for sid, day in [("s1", "28"), ("s2", "29"), ("s3", "30"), ("s3", "30"), ("s3", "30")]:
        obs.append(_err(error_class="command_not_found", session_id=sid, day=day))
        obs.append(_err(error_class="file_not_found", session_id=sid, day=day))
    clusters = cluster_failures(obs)
    assert len(clusters) == 2
    kinds = {c.error_class for c in clusters}
    assert kinds == {"command_not_found", "file_not_found"}


def test_python_launcher_pattern_kind():
    """error_class=command_not_found + command_family=python → pattern_kind=python_launcher."""
    obs = [
        _err(command_family="python", session_id="s1", day="28"),
        _err(command_family="python", session_id="s1", day="28"),
        _err(command_family="python", session_id="s2", day="29"),
        _err(command_family="python", session_id="s2", day="29"),
        _err(command_family="python", session_id="s3", day="30"),
    ]
    clusters = cluster_failures(obs)
    assert len(clusters) == 1
    assert clusters[0].pattern_kind == "python_launcher"


def test_sample_command_families_collected():
    """Cluster collects distinct command_family values from its observations."""
    obs = [
        _err(command_family="python", session_id="s1", day="28"),
        _err(command_family="python", session_id="s1", day="28"),
        _err(command_family="shell", session_id="s2", day="29"),
        _err(command_family="shell", session_id="s2", day="29"),
        _err(command_family="python", session_id="s3", day="30"),
    ]
    clusters = cluster_failures(obs)
    assert len(clusters) == 1
    assert set(clusters[0].sample_command_families) == {"python", "shell"}


def test_none_error_class_ignored():
    """Observations with error_class=None are not clustered."""
    obs = [
        {**_err(session_id="s1", day="28"), "error_class": None},
        {**_err(session_id="s2", day="29"), "error_class": None},
        {**_err(session_id="s3", day="30"), "error_class": None},
        {**_err(session_id="s3", day="30"), "error_class": None},
        {**_err(session_id="s3", day="30"), "error_class": None},
    ]
    assert cluster_failures(obs) == []


def test_different_tools_separate_clusters():
    """Same error_class but different tool_names → separate clusters."""
    obs = []
    for sid, day in [("s1", "28"), ("s2", "29"), ("s3", "30"), ("s3", "30"), ("s3", "30")]:
        obs.append(_err(tool_name="Bash", error_class="file_not_found", session_id=sid, day=day))
        obs.append(_err(tool_name="Read", error_class="file_not_found", session_id=sid, day=day))
    clusters = cluster_failures(obs)
    assert len(clusters) == 2
    tools = {c.tool_name for c in clusters}
    assert tools == {"Bash", "Read"}

"""Clustering: group error observations and extract success conventions.

Groups errors by (tool_name, error_class), extracts success conventions
for test_command, file_naming, test_placement. Applies guardrails. Stdlib only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# All failure pattern_kinds share the same guardrails in Phase 1.
MIN_OBSERVATIONS = 5
MIN_SESSIONS = 3
MIN_DAYS = 2

# Convention guardrails (from spec guardrails table)
_CONVENTION_GUARDRAILS = {
    "test_command":   {"min_obs": 5,  "min_sessions": 3, "min_days": 2, "min_pct": 80.0},
    "file_naming":    {"min_obs": 10, "min_sessions": 3, "min_days": 2, "min_pct": 85.0},
    "test_placement": {"min_obs": 6,  "min_sessions": 3, "min_days": 2, "min_pct": 80.0},
}
AMBIGUITY_GAP = 15.0  # If gap between top two < 15%, propose nothing


@dataclass
class FailureCluster:
    tool_name: str
    error_class: str
    pattern_kind: str
    observation_count: int
    session_count: int
    day_count: int
    sample_command_families: list[str] = field(default_factory=list)


def _derive_pattern_kind(error_class: str, command_families: set[str]) -> str:
    """Map error_class to pattern_kind, with python_launcher special case."""
    if error_class == "command_not_found" and command_families == {"python"}:
        return "python_launcher"
    return error_class


def cluster_failures(observations: list[dict]) -> list[FailureCluster]:
    """Group error observations by (tool_name, error_class) and apply guardrails.

    Returns clusters that pass: ≥5 observations, ≥3 sessions, ≥2 days.
    """
    # Accumulate per-group evidence
    groups: dict[tuple[str, str], list[dict]] = {}
    for obs in observations:
        if obs.get("outcome") != "error":
            continue
        ec = obs.get("error_class")
        if not ec:
            continue
        key = (obs["tool_name"], ec)
        groups.setdefault(key, []).append(obs)

    results = []
    for (tool_name, error_class), group in groups.items():
        sessions = {o.get("session_id") for o in group}
        days = {o.get("timestamp", "")[:10] for o in group}
        families = {o.get("command_family") for o in group if o.get("command_family")}

        if len(group) < MIN_OBSERVATIONS:
            continue
        if len(sessions) < MIN_SESSIONS:
            continue
        if len(days) < MIN_DAYS:
            continue

        results.append(FailureCluster(
            tool_name=tool_name,
            error_class=error_class,
            pattern_kind=_derive_pattern_kind(error_class, families),
            observation_count=len(group),
            session_count=len(sessions),
            day_count=len(days),
            sample_command_families=sorted(families),
        ))

    return results


@dataclass
class ConventionCandidate:
    pattern_kind: str
    dominant_value: str
    consistency_pct: float
    observation_count: int
    session_count: int
    day_count: int


def _classify_naming(basename: str) -> str | None:
    """Classify a .py filename as snake_case, camelCase, or None."""
    stem = basename.rsplit(".", 1)[0]
    if not stem:
        return None
    if re.match(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$", stem):
        return "snake_case"
    if re.match(r"^[a-z][a-zA-Z0-9]*$", stem) and any(c.isupper() for c in stem):
        return "camelCase"
    return None


def _is_test_file(basename: str) -> bool:
    stem = basename.rsplit(".", 1)[0]
    return stem.startswith("test_") or stem.endswith("_test")


def _top_two(counts: dict[str, int]) -> tuple[str | None, float, float]:
    """Return (winner, winner_pct, runner_up_pct) from a frequency dict."""
    total = sum(counts.values())
    if total == 0:
        return None, 0.0, 0.0
    ranked = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    winner, winner_n = ranked[0]
    winner_pct = winner_n / total * 100
    runner_up_pct = ranked[1][1] / total * 100 if len(ranked) > 1 else 0.0
    return winner, winner_pct, runner_up_pct


def _check_convention(
    pattern_kind: str,
    values: list[str],
    sessions: set[str],
    days: set[str],
) -> ConventionCandidate | None:
    """Check if a frequency distribution passes convention guardrails."""
    guard = _CONVENTION_GUARDRAILS[pattern_kind]
    if len(values) < guard["min_obs"]:
        return None
    if len(sessions) < guard["min_sessions"]:
        return None
    if len(days) < guard["min_days"]:
        return None

    counts: dict[str, int] = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1

    winner, winner_pct, runner_up_pct = _top_two(counts)
    if winner is None:
        return None
    if winner_pct < guard["min_pct"]:
        return None
    if winner_pct - runner_up_pct < AMBIGUITY_GAP:
        return None

    return ConventionCandidate(
        pattern_kind=pattern_kind,
        dominant_value=winner,
        consistency_pct=winner_pct,
        observation_count=len(values),
        session_count=len(sessions),
        day_count=len(days),
    )


def extract_conventions(observations: list[dict]) -> list[ConventionCandidate]:
    """Extract convention candidates from successful observations.

    Three categories: test_command, file_naming, test_placement.
    """
    # Accumulators
    tc_values: list[str] = []
    tc_sessions: set[str] = set()
    tc_days: set[str] = set()

    fn_values: list[str] = []
    fn_sessions: set[str] = set()
    fn_days: set[str] = set()

    tp_values: list[str] = []
    tp_sessions: set[str] = set()
    tp_days: set[str] = set()

    for obs in observations:
        if obs.get("outcome") != "success":
            continue
        sid = obs.get("session_id", "")
        day = obs.get("timestamp", "")[:10]

        # test_command: successful Bash with command_family=test
        if (obs.get("tool_name") == "Bash"
                and obs.get("command_family") == "test"
                and obs.get("command_signature")):
            tc_values.append(obs["command_signature"])
            tc_sessions.add(sid)
            tc_days.add(day)

        # file_naming: successful Write with write_kind=create, .py files
        if (obs.get("tool_name") == "Write"
                and obs.get("write_kind") == "create"
                and obs.get("file_basename", "").endswith(".py")):
            style = _classify_naming(obs["file_basename"])
            if style:
                fn_values.append(style)
                fn_sessions.add(sid)
                fn_days.add(day)

        # test_placement: successful Write with write_kind=create, test file
        if (obs.get("tool_name") == "Write"
                and obs.get("write_kind") == "create"
                and obs.get("file_basename")
                and _is_test_file(obs["file_basename"])
                and obs.get("path_pattern")):
            tp_values.append(obs["path_pattern"])
            tp_sessions.add(sid)
            tp_days.add(day)

    results = []
    for kind, vals, sids, dys in [
        ("test_command", tc_values, tc_sessions, tc_days),
        ("file_naming", fn_values, fn_sessions, fn_days),
        ("test_placement", tp_values, tp_sessions, tp_days),
    ]:
        candidate = _check_convention(kind, vals, sids, dys)
        if candidate:
            results.append(candidate)

    return results

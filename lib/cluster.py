"""Failure clustering: group error observations and apply guardrails.

Groups by (tool_name, error_class), counts evidence dimensions,
and filters clusters that don't meet proposal thresholds. Stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# All failure pattern_kinds share the same guardrails in Phase 1.
MIN_OBSERVATIONS = 5
MIN_SESSIONS = 3
MIN_DAYS = 2


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

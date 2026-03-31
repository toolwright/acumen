"""Failure recurrence tracking: measure whether applied rules reduce errors.

Computes per-rule effectiveness with explicit denominators. Stdlib only.
"""

from __future__ import annotations

import json
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

MIN_EVENTS = 50
MIN_AFTER_DAYS = 7


@dataclass
class EffectivenessRecord:
    rule_id: str
    applied_at: str
    sessions_observed: int
    target_pattern_before: float
    target_pattern_after: float
    adherence_rate: float | None
    verdict: str
    retained_at_2_weeks: bool | None


def _filter_relevant(observations: list[dict], rule: dict) -> list[dict]:
    """Filter observations to those matching the rule's denominator scope.

    Uses command_family if available on the observations, else falls back to tool_name.
    """
    tool = rule.get("target_tool")
    # First pass: find observations for this tool
    tool_obs = [o for o in observations if o.get("tool_name") == tool]
    # Check if any have a command_family set
    families = {o.get("command_family") for o in tool_obs if o.get("command_family")}
    if not families:
        return tool_obs
    # Filter to same command_family as the errors in this tool set
    error_families = {o.get("command_family") for o in tool_obs
                      if o.get("error_class") == rule.get("trigger_class")
                      and o.get("command_family")}
    if not error_families:
        return tool_obs
    return [o for o in tool_obs if o.get("command_family") in error_families]


def _error_rate(observations: list[dict], trigger_class: str) -> float:
    """Compute error rate per 100 relevant events."""
    if not observations:
        return 0.0
    errors = sum(1 for o in observations if o.get("error_class") == trigger_class)
    return errors / len(observations) * 100


def _compute_verdict(before_rate: float, after_rate: float) -> str:
    if after_rate < before_rate * 0.5:
        return "effective"
    if after_rate > before_rate * 1.1:
        return "harmful"
    return "neutral"


def measure_effectiveness(
    rule: dict,
    observations_before: list[dict],
    observations_after: list[dict],
    after_days: int,
) -> EffectivenessRecord:
    """Measure whether a rule reduced its targeted failure class."""
    trigger = rule.get("trigger_class", "")
    before = _filter_relevant(observations_before, rule)
    after = _filter_relevant(observations_after, rule)

    before_rate = _error_rate(before, trigger)
    after_rate = _error_rate(after, trigger)

    sessions = {o.get("session_id") for o in after if o.get("session_id")}
    insufficient = len(before) < MIN_EVENTS or len(after) < MIN_EVENTS or after_days < MIN_AFTER_DAYS
    verdict = "pending" if insufficient else _compute_verdict(before_rate, after_rate)

    retained = True if after_days >= 14 else None

    return EffectivenessRecord(
        rule_id=rule["id"],
        applied_at=rule.get("applied", ""),
        sessions_observed=len(sessions),
        target_pattern_before=before_rate,
        target_pattern_after=after_rate,
        adherence_rate=None,
        verdict=verdict,
        retained_at_2_weeks=retained,
    )


def read_effectiveness(scope_path: Path) -> list[EffectivenessRecord]:
    """Read effectiveness.json. Returns [] if missing/corrupted."""
    path = scope_path / "effectiveness.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        if not isinstance(data, list):
            return []
        return [EffectivenessRecord(**d) for d in data]
    except (json.JSONDecodeError, TypeError, OSError):
        return []


def save_effectiveness(scope_path: Path, records: list[EffectivenessRecord]) -> None:
    """Atomic write of effectiveness records."""
    scope_path.mkdir(parents=True, exist_ok=True)
    path = scope_path / "effectiveness.json"
    fd, tmp = tempfile.mkstemp(dir=scope_path, suffix=".tmp")
    try:
        with open(fd, "w") as f:
            json.dump([asdict(r) for r in records], f, indent=2)
        Path(tmp).replace(path)
    except Exception:
        Path(tmp).unlink(missing_ok=True)
        raise

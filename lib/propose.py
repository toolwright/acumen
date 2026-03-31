"""Proposal generation: turns clusters and conventions into AcumenRule proposals.

Handles confidence scoring, contradiction detection, and quality guardrails.
Stdlib only.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from lib.cluster import ConventionCandidate, FailureCluster

MIN_CONFIDENCE = 0.4
MAX_PENDING = 5

# pattern_kind → action template
# {tool} = target_tool, {family} = most common command_family
_ACTION_TEMPLATES = {
    "python_launcher": "Use python3 instead of python",
    "command_not_found": "Verify command exists before running: {family} commands",
    "file_not_found": "Check file exists before using {tool} tool",
    "permission_denied": "Check file permissions before {tool} operations",
    "syntax_error": "Verify command syntax for {family} commands",
    "test_failure": "Review test setup for {family} tests",
}


@dataclass
class AcumenRule:
    id: str
    type: str
    pattern_kind: str
    target_tool: str | None
    trigger_class: str | None
    pattern: str
    action: str
    evidence_summary: str
    supporting_observations: int
    supporting_sessions: int
    supporting_days: int
    confidence: float
    scope: str
    status: str
    created: str
    decided: str | None
    applied: str | None
    reverted: str | None
    human_edited: bool


def _compute_confidence(obs: int, sessions: int, days: int) -> float:
    return min(obs / 20, 1.0) * 0.5 + min(sessions / 10, 1.0) * 0.3 + min(days / 7, 1.0) * 0.2


def _build_action(cluster: FailureCluster) -> str:
    template = _ACTION_TEMPLATES.get(cluster.pattern_kind)
    if not template:
        return (f"Review recurring {cluster.error_class} errors "
                f"with {cluster.tool_name}")
    family = cluster.sample_command_families[0] if cluster.sample_command_families else "unknown"
    return template.format(tool=cluster.tool_name, family=family)


def _build_evidence(cluster: FailureCluster) -> str:
    return (f"{cluster.observation_count} failures across "
            f"{cluster.session_count} sessions, {cluster.day_count} days")


def _has_contradiction(proposal: AcumenRule, existing: list[AcumenRule]) -> bool:
    active_statuses = ("proposed", "approved", "applied")
    for rule in existing:
        if (rule.scope == proposal.scope
                and rule.pattern_kind == proposal.pattern_kind
                and rule.action != proposal.action
                and rule.status in active_statuses):
            return True
    return False


def _count_pending(rules: list[AcumenRule]) -> int:
    return sum(1 for r in rules if r.status == "proposed")


def generate_proposals(
    clusters: list[FailureCluster],
    existing_rules: list[AcumenRule],
) -> tuple[list[AcumenRule], list[AcumenRule]]:
    """Generate AcumenRule proposals from failure clusters.

    Returns (proposals, conflicts) where conflicts are proposals blocked
    by contradiction with existing rules.
    """
    if _count_pending(existing_rules) >= MAX_PENDING:
        return [], []

    proposals = []
    conflicts = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for cluster in clusters:
        confidence = _compute_confidence(
            cluster.observation_count, cluster.session_count, cluster.day_count)
        if confidence < MIN_CONFIDENCE:
            continue

        rule = AcumenRule(
            id=str(uuid.uuid4()),
            type="failure",
            pattern_kind=cluster.pattern_kind,
            target_tool=cluster.tool_name,
            trigger_class=cluster.error_class,
            pattern=f"{cluster.error_class} errors",
            action=_build_action(cluster),
            evidence_summary=_build_evidence(cluster),
            supporting_observations=cluster.observation_count,
            supporting_sessions=cluster.session_count,
            supporting_days=cluster.day_count,
            confidence=confidence,
            scope="project",
            status="proposed",
            created=now,
            decided=None,
            applied=None,
            reverted=None,
            human_edited=False,
        )

        if _has_contradiction(rule, existing_rules):
            conflicts.append(rule)
        else:
            proposals.append(rule)
            if _count_pending(existing_rules) + len(proposals) >= MAX_PENDING:
                break

    return proposals, conflicts


# --- Convention proposals ---

_CONVENTION_ACTION_TEMPLATES = {
    "test_command": "Use {value} for running tests in this project",
    "file_naming": "New Python files use {value} naming",
    "test_placement": "Test files go in {value} directory pattern",
}

_PLACEMENT_LABELS = {
    "tests_root": "tests/ at project root",
    "tests_mirror": "tests/ mirroring source structure",
    "colocated": "the same directory as source files",
    "integration_dir": "integration/ directory",
}


def _build_convention_action(candidate: ConventionCandidate) -> str:
    template = _CONVENTION_ACTION_TEMPLATES.get(candidate.pattern_kind, "")
    value = candidate.dominant_value
    if candidate.pattern_kind == "test_placement":
        value = _PLACEMENT_LABELS.get(value, value)
    return template.format(value=value)


def _build_convention_evidence(candidate: ConventionCandidate) -> str:
    return (f"{candidate.observation_count} observations across "
            f"{candidate.session_count} sessions, "
            f"{candidate.consistency_pct:.0f}% consistent")


def _compute_convention_confidence(candidate: ConventionCandidate) -> float:
    base = _compute_confidence(
        candidate.observation_count, candidate.session_count, candidate.day_count)
    consistency_bonus = (candidate.consistency_pct / 100) * 0.1
    return min(base + consistency_bonus, 1.0)


def generate_convention_proposals(
    candidates: list[ConventionCandidate],
    existing_rules: list[AcumenRule],
) -> tuple[list[AcumenRule], list[AcumenRule]]:
    """Generate AcumenRule proposals from convention candidates.

    Returns (proposals, conflicts).
    """
    if _count_pending(existing_rules) >= MAX_PENDING:
        return [], []

    proposals = []
    conflicts = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    for candidate in candidates:
        confidence = _compute_convention_confidence(candidate)
        if confidence < MIN_CONFIDENCE:
            continue

        rule = AcumenRule(
            id=str(uuid.uuid4()),
            type="convention",
            pattern_kind=candidate.pattern_kind,
            target_tool=None,
            trigger_class=None,
            pattern=f"{candidate.pattern_kind}: {candidate.dominant_value} "
                    f"({candidate.consistency_pct:.0f}%)",
            action=_build_convention_action(candidate),
            evidence_summary=_build_convention_evidence(candidate),
            supporting_observations=candidate.observation_count,
            supporting_sessions=candidate.session_count,
            supporting_days=candidate.day_count,
            confidence=confidence,
            scope="project",
            status="proposed",
            created=now,
            decided=None,
            applied=None,
            reverted=None,
            human_edited=False,
        )

        if _has_contradiction(rule, existing_rules):
            conflicts.append(rule)
        else:
            proposals.append(rule)
            if _count_pending(existing_rules) + len(proposals) >= MAX_PENDING:
                break

    return proposals, conflicts

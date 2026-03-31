"""Proposal generation: turns FailureClusters into AcumenRule proposals.

Handles confidence scoring, contradiction detection, and quality guardrails.
Stdlib only.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from lib.cluster import FailureCluster

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

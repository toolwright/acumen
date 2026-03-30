"""Confidence/impact scoring and dedup for insights. Pure math, stdlib only."""

import math
from datetime import datetime, timezone

REQUIRED_INSIGHT_FIELDS = {"description", "category", "evidence_count", "tools"}


def validate_insight(insight: dict) -> bool:
    """Check that an insight has all required fields with valid types.

    Returns True if valid. Logs reason and returns False otherwise.
    Drops invalid insights rather than crashing the pipeline.
    """
    if not isinstance(insight, dict):
        return False
    for field in REQUIRED_INSIGHT_FIELDS:
        if field not in insight:
            return False
    if not isinstance(insight["description"], str) or not insight["description"]:
        return False
    if not isinstance(insight["evidence_count"], (int, float)) or insight["evidence_count"] < 0:
        return False
    if not isinstance(insight["tools"], list):
        return False
    return True


def filter_valid_insights(insights: list) -> list[dict]:
    """Filter a list to only valid insights. Drops invalid entries silently."""
    return [i for i in insights if isinstance(i, dict) and validate_insight(i)]


def score_insight(insight: dict, observations: list[dict]) -> dict:
    """Compute confidence (0-1), impact (0-1), combined score for an insight.

    Returns dict with keys: confidence, impact, combined.
    """
    if not observations:
        return {"confidence": 0.0, "impact": 0.0, "combined": 0.0}

    now = datetime.now(timezone.utc)
    evidence = insight.get("evidence_count", len(observations))

    # Confidence: based on evidence count with recency weighting
    # More evidence + more recent = higher confidence
    recency_weights = []
    for obs in observations:
        ts = obs.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(ts)
            days_old = max((now - dt).total_seconds() / 86400, 0)
        except (ValueError, TypeError):
            days_old = 7  # default to a week old if unparseable
        # Exponential decay: half-life of 3 days
        recency_weights.append(math.exp(-0.231 * days_old))

    weighted_evidence = sum(recency_weights)
    # Saturating curve: approaches 1.0 as evidence grows
    confidence = min(1.0, 1 - math.exp(-weighted_evidence / 5))

    # Impact: higher for error patterns and failure-heavy observations
    error_count = sum(1 for o in observations if o.get("outcome") in ("error", "failure"))
    error_ratio = error_count / len(observations)
    category_boost = 1.5 if insight.get("category") == "error_pattern" else 1.0
    impact = min(1.0, error_ratio * category_boost + (evidence / 50))

    combined = confidence * 0.4 + impact * 0.6
    return {"confidence": round(confidence, 4), "impact": round(impact, 4), "combined": round(combined, 4)}


def rank_insights(insights: list[dict]) -> list[dict]:
    """Sort insights by combined score descending."""
    return sorted(insights, key=lambda i: i.get("combined", 0), reverse=True)


def dedup_insights(new_insights: list[dict], existing_insights: list[dict]) -> list[dict]:
    """Merge new insights into existing. Matches on description, sums evidence_count."""
    by_desc = {}
    for ins in existing_insights:
        by_desc[ins["description"]] = dict(ins)
    for ins in new_insights:
        desc = ins["description"]
        if desc in by_desc:
            by_desc[desc]["evidence_count"] = (
                by_desc[desc].get("evidence_count", 0) + ins.get("evidence_count", 0)
            )
        else:
            by_desc[desc] = dict(ins)
    return list(by_desc.values())

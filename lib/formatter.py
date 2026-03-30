"""Format observation/insight data for CLI display. Stdlib only."""

from collections import Counter
from typing import Optional


def format_status(observations: list[dict], insights: list[dict], last_reflection: Optional[str] = None) -> str:
    """Format status summary for /acumen-status. Returns plain text."""
    if not observations and not insights:
        return "No observation data yet. Acumen collects data as you work -- check back after a few sessions."

    sessions = len({o.get("session_id", "") for o in observations})
    total_obs = len(observations)
    errors = sum(1 for o in observations if o.get("outcome") in ("error", "failure"))
    error_rate = f"{errors / total_obs * 100:.0f}%" if total_obs else "0%"

    # Observations per day (last 7 days)
    day_counts: Counter[str] = Counter()
    for o in observations:
        ts = o.get("timestamp", "")
        day_counts[ts[:10]] += 1
    daily = " | ".join(f"{d}: {c}" for d, c in sorted(day_counts.items())[-7:])

    lines = [
        "ACUMEN STATUS",
        f"  Sessions observed: {sessions}",
        f"  Total observations: {total_obs}",
        f"  Error rate: {error_rate}",
        f"  Active insights: {len(insights)}",
    ]
    if last_reflection:
        lines.append(f"  Last reflection: {last_reflection}")
    if daily:
        lines.append(f"  Daily activity: {daily}")
    if insights:
        lines.append("  Top insights:")
        for ins in insights[:5]:
            score = ins.get("combined", 0)
            lines.append(f"    - [{score:.2f}] {ins['description']}")
    return "\n".join(lines)


def format_review(proposals: list[dict]) -> str:
    """Format applied improvements for /acumen-review. Returns plain text."""
    applied = [p for p in proposals if p.get("status") in ("approved", "auto-applied")]
    if not applied:
        return "No applied improvements. Run /acumen-reflect first."

    lines = [f"{len(applied)} applied improvement(s):", ""]
    global_candidates = []
    for i, p in enumerate(applied, 1):
        eff = f" [{p['effectiveness'].upper()}]" if p.get("effectiveness") else ""
        lines.append(f"  {i}. [RULE]{eff} {p['description']}")
        if p.get("scope") == "global_candidate" and p.get("scope") != "global":
            global_candidates.append(p)

    if global_candidates:
        lines.append("")
        lines.append("GLOBAL PROMOTION CANDIDATES (would apply across all projects):")
        for p in global_candidates:
            proven = " -- proven effective" if p.get("effectiveness") == "effective" else ""
            lines.append(f"  * {p['description']}{proven}")

    return "\n".join(lines)


def format_insights(insights: list[dict]) -> str:
    """Format ranked insight list for /acumen-insights. Returns plain text."""
    if not insights:
        return "No insights yet. Run /acumen-reflect after a few sessions to extract patterns."

    lines = ["ACUMEN INSIGHTS", f"  {len(insights)} insight(s), ranked by score:", ""]
    for i, ins in enumerate(insights, 1):
        score = ins.get("combined", 0)
        cat = ins.get("category", "unknown")
        evidence = ins.get("evidence_count", 0)
        desc = ins["description"]
        lines.append(f"  {i}. [{score:.2f}] ({cat}) {desc}")
        lines.append(f"     Evidence: {evidence} observations")
    return "\n".join(lines)

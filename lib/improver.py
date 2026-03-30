"""Generate, store, and apply improvement proposals. Stdlib only."""

from __future__ import annotations

import json
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def list_applied_rule_slugs(project_root: Path) -> set[str]:
    """Return slugs of already-applied acumen rule files."""
    rules_dir = project_root / ".claude" / "rules"
    if not rules_dir.exists():
        return set()
    return {p.stem.removeprefix("acumen-") for p in rules_dir.glob("acumen-*.md")}


def generate_proposals(insights: list[dict], existing_rule_slugs: set[str] | None = None) -> list[dict]:
    """Convert insights into proposals. Corrections -> rules, others -> memory.

    existing_rule_slugs: slugs of already-applied acumen rules to skip.
    """
    existing_rule_slugs = existing_rule_slugs or set()
    proposals = []
    now = datetime.now(timezone.utc).isoformat()
    for ins in insights:
        desc = ins["description"]
        slug = _slugify(desc)
        if slug in existing_rule_slugs:
            continue  # rule already applied, skip
        rule_text = f"# Acumen insight\n\n{desc}"
        p = {
            "description": desc,
            "rule_text": rule_text,
            "target": "rule",
            "status": "proposed",
            "created": now,
            "tools": ins.get("tools", []),
        }
        if ins.get("scope_hint") == "global":
            p["scope"] = "global_candidate"
        proposals.append(p)
    return proposals


def read_proposals(scope_path: Path) -> list[dict]:
    """Read proposals.json from scope_path. Empty list if missing."""
    path = scope_path / "proposals.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, ValueError):
        return []


def write_proposal(scope_path: Path, proposal: dict) -> None:
    """Append a proposal to proposals.json. Atomic write."""
    scope_path.mkdir(parents=True, exist_ok=True)
    path = scope_path / "proposals.json"
    existing = read_proposals(scope_path)
    existing.append(proposal)
    fd, tmp = tempfile.mkstemp(dir=scope_path, suffix=".tmp")
    try:
        with open(fd, "w") as f:
            json.dump(existing, f, indent=2)
        Path(tmp).replace(path)
    except Exception:
        Path(tmp).unlink(missing_ok=True)
        raise


def _slugify(text: str) -> str:
    """Convert text to a filename-safe slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:40] or "insight"


def apply_proposal(project_root: Path, proposal: dict) -> Path:
    """Apply an approved proposal. Returns path of created file.

    Rules -> .claude/rules/acumen-<slug>.md
    Memory -> .claude/memory/acumen/<slug>.md
    Raises ValueError if proposal is not approved.
    """
    if proposal.get("status") not in ("approved", "auto-applied"):
        raise ValueError(f"Cannot apply proposal with status '{proposal.get('status')}' -- must be approved or auto-applied")

    slug = _slugify(proposal["description"])
    rule_text = proposal.get("rule_text", proposal["description"])

    out_dir = project_root / ".claude" / "rules"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"acumen-{slug}.md"
    out_path.write_text(rule_text + "\n")

    return out_path


def auto_apply_proposals(project_root: Path, proposals: list[dict]) -> list[dict]:
    """Auto-apply all proposed proposals. Sets status to 'auto-applied', writes files.

    Returns list of dicts with 'description', 'target', and 'path' for each applied proposal.
    Skips proposals that already have a terminal status (approved, auto-applied, rejected).
    """
    applied = []
    now = datetime.now(timezone.utc).isoformat()
    for p in proposals:
        if p.get("status") not in ("proposed",):
            continue
        p["status"] = "auto-applied"
        p["applied_at"] = now
        path = apply_proposal(project_root, p)
        applied.append({"description": p["description"], "target": p["target"], "path": str(path)})
    return applied


def measure_effectiveness_with_confidence(
    proposals: list[dict],
    observations: list[dict],
    project_root: Path,
) -> list[dict]:
    """Score applied proposals using before/after error rates, with eval tier confidence label.

    Wraps measure_effectiveness() and adds eval_confidence to each updated proposal.
    Falls back to confidence='LOW' if no eval config exists.
    """
    try:
        try:
            from evaluator import load_eval_config
        except ImportError:
            from lib.evaluator import load_eval_config
        config = load_eval_config(project_root)
        confidence = config.confidence if config else "LOW"
    except Exception:
        confidence = "LOW"

    changed = measure_effectiveness(proposals, observations)
    for p in changed:
        p["eval_confidence"] = confidence
    return changed


def promote_to_global(proposal: dict) -> Path:
    """Copy an effective project rule to global Claude Code rules (~/.claude/rules/).

    Writes to ~/.claude/rules/acumen-{slug}.md so it applies in all projects.
    Updates proposal in-place: scope='global', promoted_at=now.
    Returns the path written.
    """
    slug = _slugify(proposal["description"])
    rule_text = proposal.get("rule_text", proposal["description"])
    out_dir = Path.home() / ".claude" / "rules"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"acumen-{slug}.md"
    out_path.write_text(rule_text + "\n")
    proposal["scope"] = "global"
    proposal["promoted_at"] = datetime.now(timezone.utc).isoformat()
    return out_path


def expire_stale_proposals(proposals: list[dict], max_age_days: int = 30) -> list[dict]:
    """Remove proposals older than max_age_days that were never applied.

    Removes proposals with status 'rejected' or 'proposed' whose created
    timestamp is older than max_age_days. Applied/auto-applied proposals
    are never expired (they're the historical record).

    Returns the filtered list (in-place modification).
    """
    now = datetime.now(timezone.utc)
    keep = []
    for p in proposals:
        if p.get("status") in ("rejected", "proposed"):
            created = p.get("created", "")
            try:
                dt = datetime.fromisoformat(created)
                age_days = (now - dt).total_seconds() / 86400
                if age_days > max_age_days:
                    continue  # expired, drop
            except (ValueError, TypeError):
                pass  # unparseable date, keep it
        keep.append(p)
    proposals.clear()
    proposals.extend(keep)
    return proposals


def revert_proposal(project_root: Path, proposal: dict) -> str:
    """Revert an applied proposal by deleting its rule file.

    Updates proposal status to 'reverted' in-place.
    Returns a message describing what was reverted.
    """
    slug = _slugify(proposal["description"])
    path = project_root / ".claude" / "rules" / f"acumen-{slug}.md"
    if path.exists():
        path.unlink()
        msg = f"Reverted: {path}"
    else:
        msg = f"File already removed: {path}"
    proposal["status"] = "reverted"
    return msg


def measure_effectiveness(proposals: list[dict], observations: list[dict]) -> list[dict]:
    """Score applied proposals as effective/neutral/harmful using before/after error rates.

    Compares tool error rate before and after applied_at timestamp.
    Requires 5+ observations on each side; skips otherwise (insufficient data).
    Returns list of proposals that had their effectiveness updated.
    """
    changed = []
    for p in proposals:
        if p.get("status") != "auto-applied" or not p.get("applied_at") or not p.get("tools"):
            continue
        applied_at = p["applied_at"]
        tools = set(p["tools"])
        before = [o for o in observations if o["timestamp"] < applied_at and o["tool_name"] in tools]
        after = [o for o in observations if o["timestamp"] >= applied_at and o["tool_name"] in tools]
        if len(before) < 5 or len(after) < 5:
            continue  # not enough data yet
        before_rate = sum(1 for o in before if o["outcome"] == "error") / len(before)
        after_rate = sum(1 for o in after if o["outcome"] == "error") / len(after)
        delta = before_rate - after_rate
        verdict = "effective" if delta > 0.1 else ("harmful" if delta < -0.1 else "neutral")
        if p.get("effectiveness") != verdict:
            p["effectiveness"] = verdict
            changed.append(p)
    return changed

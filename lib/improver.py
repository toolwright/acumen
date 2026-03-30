"""Generate, store, and apply improvement proposals. Stdlib only."""

import json
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def generate_proposals(insights: list[dict]) -> list[dict]:
    """Convert insights into proposals. Corrections -> rules, others -> memory."""
    proposals = []
    now = datetime.now(timezone.utc).isoformat()
    for ins in insights:
        desc = ins["description"]
        is_correction = ins.get("category") == "correction"
        rule_text = f"# Acumen insight\n\n{desc}"
        proposals.append({
            "description": desc,
            "rule_text": rule_text,
            "target": "rule" if is_correction else "memory",
            "status": "proposed",
            "created": now,
        })
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
    if proposal.get("status") != "approved":
        raise ValueError(f"Cannot apply proposal with status '{proposal.get('status')}' -- must be approved")

    slug = _slugify(proposal["description"])
    rule_text = proposal.get("rule_text", proposal["description"])

    if proposal["target"] == "rule":
        out_dir = project_root / ".claude" / "rules"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"acumen-{slug}.md"
        out_path.write_text(rule_text + "\n")
    else:
        out_dir = project_root / ".claude" / "memory" / "acumen"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{slug}.md"
        out_path.write_text(rule_text + "\n")

    return out_path

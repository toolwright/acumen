"""Rule application and revert. Reads/writes rules.json and .claude/rules/ files.

Stdlib only.
"""

from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_rules(scope_path: Path) -> list[dict]:
    """Read rules.json from scope_path. Returns [] if missing/corrupted."""
    path = scope_path / "rules.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def save_rules(scope_path: Path, rules: list[dict]) -> None:
    """Atomic write of rules list to rules.json."""
    scope_path.mkdir(parents=True, exist_ok=True)
    path = scope_path / "rules.json"
    fd, tmp = tempfile.mkstemp(dir=scope_path, suffix=".tmp")
    try:
        with open(fd, "w") as f:
            json.dump(rules, f, indent=2)
        Path(tmp).replace(path)
    except Exception:
        Path(tmp).unlink(missing_ok=True)
        raise


def _rule_file_path(project_root: Path, rule_id: str) -> Path:
    return project_root / ".claude" / "rules" / f"acumen-{rule_id}.md"


def _render_rule(rule: dict) -> str:
    return (f"# Acumen rule\n\n"
            f"{rule['action']}\n\n"
            f"Observed: {rule['pattern']} ({rule['evidence_summary']})\n")


def apply_rule(scope_path: Path, rule: dict, project_root: Path) -> str:
    """Write rule file to .claude/rules/ and update status in rules.json."""
    rule_path = _rule_file_path(project_root, rule["id"])
    rule_path.parent.mkdir(parents=True, exist_ok=True)

    # Atomic write of rule file
    fd, tmp = tempfile.mkstemp(dir=rule_path.parent, suffix=".tmp")
    try:
        with open(fd, "w") as f:
            f.write(_render_rule(rule))
        Path(tmp).replace(rule_path)
    except Exception:
        Path(tmp).unlink(missing_ok=True)
        raise

    # Update status in rules.json
    now = _now()
    rules = read_rules(scope_path)
    for r in rules:
        if r["id"] == rule["id"]:
            r["status"] = "applied"
            r["decided"] = now
            r["applied"] = now
            break
    save_rules(scope_path, rules)

    return str(rule_path)


def reject_rule(scope_path: Path, rule_id: str) -> None:
    """Mark a rule as rejected in rules.json."""
    rules = read_rules(scope_path)
    for r in rules:
        if r["id"] == rule_id:
            r["status"] = "rejected"
            r["decided"] = _now()
            break
    save_rules(scope_path, rules)


def revert_rule(scope_path: Path, rule_id: str, project_root: Path) -> bool:
    """Delete rule file and mark as reverted. Returns False if file missing."""
    rule_path = _rule_file_path(project_root, rule_id)
    if not rule_path.exists():
        return False

    # Find the rule in rules.json
    rules = read_rules(scope_path)
    found = False
    for r in rules:
        if r["id"] == rule_id:
            r["status"] = "reverted"
            r["reverted"] = _now()
            found = True
            break
    if not found:
        return False

    rule_path.unlink()
    save_rules(scope_path, rules)
    return True

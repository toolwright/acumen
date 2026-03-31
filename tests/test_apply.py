"""Tests for lib/apply.py -- rule application and revert."""

import json
from pathlib import Path

from lib.apply import apply_rule, read_rules, revert_rule, save_rules


def _rule(id="rule-1", action="Use python3 instead of python",
          pattern="command_not_found errors",
          evidence="47 failures across 12 sessions, 4 days",
          status="proposed"):
    return {
        "id": id, "type": "failure", "pattern_kind": "python_launcher",
        "target_tool": "Bash", "trigger_class": "command_not_found",
        "pattern": pattern, "action": action,
        "evidence_summary": evidence,
        "supporting_observations": 47, "supporting_sessions": 12,
        "supporting_days": 4, "confidence": 0.9,
        "scope": "project", "status": status,
        "created": "2026-03-28T00:00:00Z",
        "decided": None, "applied": None, "reverted": None,
        "human_edited": False,
    }


# --- read_rules / save_rules ---

def test_read_rules_empty(tmp_path):
    """No rules.json → empty list."""
    assert read_rules(tmp_path) == []


def test_save_and_read_roundtrip(tmp_path):
    """Save then read returns same rules."""
    rules = [_rule()]
    save_rules(tmp_path, rules)
    assert read_rules(tmp_path) == rules


def test_save_rules_atomic(tmp_path):
    """save_rules uses atomic write (no .tmp left behind)."""
    save_rules(tmp_path, [_rule()])
    tmp_files = list(tmp_path.glob("*.tmp"))
    assert tmp_files == []
    assert (tmp_path / "rules.json").exists()


# --- apply_rule ---

def test_apply_creates_rule_file(tmp_path):
    """apply_rule writes .claude/rules/acumen-<id>.md."""
    scope = tmp_path / ".acumen"
    scope.mkdir()
    rules = [_rule(id="abc-123")]
    save_rules(scope, rules)

    path = apply_rule(scope, rules[0], tmp_path)

    rule_file = tmp_path / ".claude" / "rules" / "acumen-abc-123.md"
    assert Path(path) == rule_file
    assert rule_file.exists()


def test_apply_rule_file_content(tmp_path):
    """Rule file has correct format: heading, action, observed line."""
    scope = tmp_path / ".acumen"
    scope.mkdir()
    rules = [_rule(id="abc-123")]
    save_rules(scope, rules)

    apply_rule(scope, rules[0], tmp_path)

    content = (tmp_path / ".claude" / "rules" / "acumen-abc-123.md").read_text()
    assert "# Acumen rule" in content
    assert "Use python3 instead of python" in content
    assert "Observed:" in content
    assert "command_not_found errors" in content
    assert "47 failures across 12 sessions, 4 days" in content


def test_apply_updates_status(tmp_path):
    """apply_rule sets status=applied and applied timestamp in rules.json."""
    scope = tmp_path / ".acumen"
    scope.mkdir()
    rules = [_rule(id="abc-123")]
    save_rules(scope, rules)

    apply_rule(scope, rules[0], tmp_path)

    updated = read_rules(scope)
    assert updated[0]["status"] == "applied"
    assert updated[0]["applied"] is not None


def test_apply_sets_decided_timestamp(tmp_path):
    """apply_rule sets decided timestamp."""
    scope = tmp_path / ".acumen"
    scope.mkdir()
    rules = [_rule(id="abc-123")]
    save_rules(scope, rules)

    apply_rule(scope, rules[0], tmp_path)

    updated = read_rules(scope)
    assert updated[0]["decided"] is not None


def test_apply_only_acumen_namespace(tmp_path):
    """Rule files are always under acumen-* prefix."""
    scope = tmp_path / ".acumen"
    scope.mkdir()
    rules = [_rule(id="my-rule")]
    save_rules(scope, rules)

    path = apply_rule(scope, rules[0], tmp_path)
    assert "acumen-" in Path(path).name


def test_apply_atomic_write(tmp_path):
    """apply_rule doesn't leave .tmp files behind."""
    scope = tmp_path / ".acumen"
    scope.mkdir()
    rules = [_rule(id="abc-123")]
    save_rules(scope, rules)

    apply_rule(scope, rules[0], tmp_path)

    rules_dir = tmp_path / ".claude" / "rules"
    tmp_files = list(rules_dir.glob("*.tmp"))
    assert tmp_files == []


# --- revert_rule ---

def test_revert_deletes_file(tmp_path):
    """revert_rule removes the .claude/rules/acumen-<id>.md file."""
    scope = tmp_path / ".acumen"
    scope.mkdir()
    rules = [_rule(id="abc-123", status="applied")]
    save_rules(scope, rules)
    # Create the rule file
    rules_dir = tmp_path / ".claude" / "rules"
    rules_dir.mkdir(parents=True)
    (rules_dir / "acumen-abc-123.md").write_text("# Acumen rule\n")

    result = revert_rule(scope, "abc-123", tmp_path)

    assert result is True
    assert not (rules_dir / "acumen-abc-123.md").exists()


def test_revert_updates_status(tmp_path):
    """revert_rule sets status=reverted and reverted timestamp."""
    scope = tmp_path / ".acumen"
    scope.mkdir()
    rules = [_rule(id="abc-123", status="applied")]
    save_rules(scope, rules)
    rules_dir = tmp_path / ".claude" / "rules"
    rules_dir.mkdir(parents=True)
    (rules_dir / "acumen-abc-123.md").write_text("# Acumen rule\n")

    revert_rule(scope, "abc-123", tmp_path)

    updated = read_rules(scope)
    assert updated[0]["status"] == "reverted"
    assert updated[0]["reverted"] is not None


def test_revert_returns_false_no_file(tmp_path):
    """revert_rule returns False if the rule file doesn't exist."""
    scope = tmp_path / ".acumen"
    scope.mkdir()
    rules = [_rule(id="abc-123", status="applied")]
    save_rules(scope, rules)

    result = revert_rule(scope, "abc-123", tmp_path)
    assert result is False


def test_revert_unknown_id(tmp_path):
    """revert_rule returns False if rule_id not in rules.json."""
    scope = tmp_path / ".acumen"
    scope.mkdir()
    save_rules(scope, [_rule(id="abc-123")])

    result = revert_rule(scope, "nonexistent", tmp_path)
    assert result is False


# --- reject helper ---

def test_reject_updates_status(tmp_path):
    """Rejecting a rule sets status=rejected and decided timestamp."""
    scope = tmp_path / ".acumen"
    scope.mkdir()
    rules = [_rule(id="abc-123")]
    save_rules(scope, rules)

    # Simulate rejection (done by the command, not a lib function)
    from lib.apply import reject_rule
    reject_rule(scope, "abc-123")

    updated = read_rules(scope)
    assert updated[0]["status"] == "rejected"
    assert updated[0]["decided"] is not None

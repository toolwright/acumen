"""Tests for lib/improver.py -- proposal generation and application."""

from datetime import datetime

from lib.improver import generate_proposals, read_proposals, write_proposal, apply_proposal, auto_apply_proposals


def _insight(description="Bash fails on test commands", category="correction", evidence_count=5, **kw):
    return {"description": description, "category": category, "evidence_count": evidence_count, **kw}


# -- generate_proposals --


def test_generate_proposals_correction_produces_rule():
    """Correction insights generate a rule proposal."""
    insights = [_insight("Always run pytest with -v flag", category="correction")]
    proposals = generate_proposals(insights)

    assert len(proposals) == 1
    p = proposals[0]
    assert p["target"] == "rule"
    assert p["status"] == "proposed"
    assert p["description"] == "Always run pytest with -v flag"
    assert "rule_text" in p
    assert "created" in p


def test_generate_proposals_non_correction_produces_memory():
    """Non-correction insights generate a memory proposal."""
    insights = [_insight("Bash tool used heavily for file listing", category="best_practice")]
    proposals = generate_proposals(insights)

    assert len(proposals) == 1
    assert proposals[0]["target"] == "memory"


def test_generate_proposals_multiple():
    """Multiple insights produce multiple proposals."""
    insights = [
        _insight("Use python3 not python", category="correction"),
        _insight("Read tool rarely fails", category="best_practice"),
        _insight("Edit retries indicate path issues", category="error_pattern"),
    ]
    proposals = generate_proposals(insights)
    assert len(proposals) == 3
    assert proposals[0]["target"] == "rule"
    assert proposals[1]["target"] == "memory"
    assert proposals[2]["target"] == "memory"


def test_generate_proposals_empty():
    """Empty insights produce empty proposals."""
    assert generate_proposals([]) == []


def test_generate_proposals_rule_text_contains_description():
    """Rule text includes the insight description."""
    proposals = generate_proposals([_insight("Always check exit codes")])
    assert "Always check exit codes" in proposals[0]["rule_text"]


def test_generate_proposals_has_timestamp():
    """Each proposal has a created timestamp."""
    proposals = generate_proposals([_insight()])
    ts = proposals[0]["created"]
    # Should be parseable ISO format
    datetime.fromisoformat(ts)


# -- read_proposals / write_proposal --


def test_read_proposals_empty(tmp_path):
    """Returns empty list when no proposals.json exists."""
    assert read_proposals(tmp_path) == []


def test_write_and_read_proposal(tmp_path):
    """Write then read roundtrips correctly."""
    proposal = {"description": "test", "target": "rule", "status": "proposed"}
    write_proposal(tmp_path, proposal)
    result = read_proposals(tmp_path)
    assert len(result) == 1
    assert result[0]["description"] == "test"


def test_write_proposal_appends(tmp_path):
    """Multiple writes append, not overwrite."""
    write_proposal(tmp_path, {"description": "first", "status": "proposed"})
    write_proposal(tmp_path, {"description": "second", "status": "proposed"})
    result = read_proposals(tmp_path)
    assert len(result) == 2


# -- apply_proposal --


def test_apply_rule_proposal(tmp_path):
    """Approved rule proposal writes .claude/rules/acumen-*.md."""
    proposal = {
        "description": "Use python3 not python",
        "target": "rule",
        "status": "approved",
        "rule_text": "Always use python3 instead of python for running scripts.",
    }
    apply_proposal(tmp_path, proposal)

    rules_dir = tmp_path / ".claude" / "rules"
    rule_files = list(rules_dir.glob("acumen-*.md"))
    assert len(rule_files) == 1
    content = rule_files[0].read_text()
    assert "python3" in content


def test_apply_memory_proposal(tmp_path):
    """Approved memory proposal writes .claude/memory/acumen/*.md."""
    proposal = {
        "description": "Bash tool used heavily for file listing",
        "target": "memory",
        "status": "approved",
        "rule_text": "Bash is the most commonly used tool in this project.",
    }
    apply_proposal(tmp_path, proposal)

    mem_dir = tmp_path / ".claude" / "memory" / "acumen"
    mem_files = list(mem_dir.glob("*.md"))
    assert len(mem_files) == 1
    content = mem_files[0].read_text()
    assert "Bash" in content


def test_apply_proposal_refuses_non_approved(tmp_path):
    """Refuses to apply proposals that aren't approved or auto-applied."""
    proposal = {
        "description": "test",
        "target": "rule",
        "status": "proposed",
        "rule_text": "some rule",
    }
    try:
        apply_proposal(tmp_path, proposal)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "approved" in str(e).lower()


def test_apply_proposal_accepts_auto_applied(tmp_path):
    """Auto-applied status is accepted by apply_proposal."""
    proposal = {
        "description": "Auto test rule",
        "target": "rule",
        "status": "auto-applied",
        "rule_text": "Auto-applied rule content.",
    }
    path = apply_proposal(tmp_path, proposal)
    assert path.exists()
    assert "Auto-applied" in path.read_text()


def test_apply_rule_namespacing(tmp_path):
    """All rule files are prefixed with acumen-."""
    proposal = {
        "description": "Test rule",
        "target": "rule",
        "status": "approved",
        "rule_text": "Test rule content.",
    }
    apply_proposal(tmp_path, proposal)

    rules_dir = tmp_path / ".claude" / "rules"
    for f in rules_dir.iterdir():
        assert f.name.startswith("acumen-"), f"Rule file {f.name} not namespaced"


def test_apply_memory_namespacing(tmp_path):
    """All memory files are in acumen/ subdirectory."""
    proposal = {
        "description": "Test memory",
        "target": "memory",
        "status": "approved",
        "rule_text": "Test memory content.",
    }
    apply_proposal(tmp_path, proposal)

    mem_dir = tmp_path / ".claude" / "memory" / "acumen"
    assert mem_dir.is_dir()
    assert len(list(mem_dir.glob("*.md"))) == 1


def test_apply_multiple_proposals_unique_files(tmp_path):
    """Multiple applied proposals create separate files."""
    for desc in ["Rule one", "Rule two"]:
        apply_proposal(tmp_path, {
            "description": desc,
            "target": "rule",
            "status": "approved",
            "rule_text": f"Content for {desc}.",
        })

    rules_dir = tmp_path / ".claude" / "rules"
    assert len(list(rules_dir.glob("acumen-*.md"))) == 2


# -- auto_apply_proposals --


def test_auto_apply_sets_status_and_writes_files(tmp_path):
    """Auto-apply sets status to auto-applied and creates files."""
    proposals = [
        {"description": "Use python3", "target": "rule", "status": "proposed", "rule_text": "Use python3."},
        {"description": "Bash is common", "target": "memory", "status": "proposed", "rule_text": "Bash is common."},
    ]
    applied = auto_apply_proposals(tmp_path, proposals)

    assert len(applied) == 2
    assert proposals[0]["status"] == "auto-applied"
    assert proposals[1]["status"] == "auto-applied"
    assert (tmp_path / ".claude" / "rules").exists()
    assert (tmp_path / ".claude" / "memory" / "acumen").exists()


def test_auto_apply_skips_non_proposed(tmp_path):
    """Auto-apply skips proposals that already have a terminal status."""
    proposals = [
        {"description": "Already done", "target": "rule", "status": "approved", "rule_text": "Done."},
        {"description": "Rejected one", "target": "rule", "status": "rejected", "rule_text": "Nope."},
        {"description": "New one", "target": "rule", "status": "proposed", "rule_text": "New."},
    ]
    applied = auto_apply_proposals(tmp_path, proposals)

    assert len(applied) == 1
    assert applied[0]["description"] == "New one"
    # Original statuses unchanged for non-proposed
    assert proposals[0]["status"] == "approved"
    assert proposals[1]["status"] == "rejected"


def test_auto_apply_empty_list(tmp_path):
    """Auto-apply with no proposals returns empty list."""
    assert auto_apply_proposals(tmp_path, []) == []


def test_auto_apply_returns_paths(tmp_path):
    """Applied entries include the file path."""
    proposals = [
        {"description": "Test path", "target": "rule", "status": "proposed", "rule_text": "Content."},
    ]
    applied = auto_apply_proposals(tmp_path, proposals)
    assert len(applied) == 1
    assert "path" in applied[0]
    from pathlib import Path
    assert Path(applied[0]["path"]).exists()

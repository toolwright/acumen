"""Tests for lib/improver.py -- proposal generation and application."""

from datetime import datetime

from lib.improver import (
    generate_proposals,
    read_proposals,
    write_proposal,
    apply_proposal,
    auto_apply_proposals,
    list_applied_rule_slugs,
    measure_effectiveness,
    promote_to_global,
)


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


def test_generate_proposals_non_correction_produces_rule():
    """All insights generate rule proposals (no memory target)."""
    insights = [_insight("Bash tool used heavily for file listing", category="best_practice")]
    proposals = generate_proposals(insights)

    assert len(proposals) == 1
    assert proposals[0]["target"] == "rule"


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
    assert proposals[1]["target"] == "rule"
    assert proposals[2]["target"] == "rule"


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


def test_apply_non_correction_proposal_writes_rule(tmp_path):
    """All proposals write to .claude/rules/acumen-*.md regardless of target."""
    proposal = {
        "description": "Bash tool used heavily for file listing",
        "target": "rule",
        "status": "approved",
        "rule_text": "Bash is the most commonly used tool in this project.",
    }
    apply_proposal(tmp_path, proposal)

    rules_dir = tmp_path / ".claude" / "rules"
    rule_files = list(rules_dir.glob("acumen-*.md"))
    assert len(rule_files) == 1
    content = rule_files[0].read_text()
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


def test_apply_legacy_memory_target_writes_to_rules(tmp_path):
    """Legacy proposals with target='memory' still write to rules directory."""
    proposal = {
        "description": "Test legacy memory",
        "target": "memory",
        "status": "approved",
        "rule_text": "Test legacy memory content.",
    }
    apply_proposal(tmp_path, proposal)

    # Should write to rules, not memory
    rules_dir = tmp_path / ".claude" / "rules"
    assert len(list(rules_dir.glob("acumen-*.md"))) == 1
    mem_dir = tmp_path / ".claude" / "memory" / "acumen"
    assert not mem_dir.exists()


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
    """Auto-apply sets status to auto-applied and creates rule files."""
    proposals = [
        {"description": "Use python3", "target": "rule", "status": "proposed", "rule_text": "Use python3."},
        {"description": "Bash is common", "target": "rule", "status": "proposed", "rule_text": "Bash is common."},
    ]
    applied = auto_apply_proposals(tmp_path, proposals)

    assert len(applied) == 2
    assert proposals[0]["status"] == "auto-applied"
    assert proposals[1]["status"] == "auto-applied"
    assert (tmp_path / ".claude" / "rules").exists()
    assert len(list((tmp_path / ".claude" / "rules").glob("acumen-*.md"))) == 2


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


def test_auto_apply_records_applied_at(tmp_path):
    """Auto-apply records applied_at timestamp on each applied proposal."""
    proposals = [
        {"description": "Timestamped rule", "target": "rule", "status": "proposed", "rule_text": "Rule."},
    ]
    auto_apply_proposals(tmp_path, proposals)
    assert "applied_at" in proposals[0]
    datetime.fromisoformat(proposals[0]["applied_at"])


# -- list_applied_rule_slugs --


def test_list_applied_rule_slugs_empty(tmp_path):
    """Returns empty set when no rules directory exists."""
    assert list_applied_rule_slugs(tmp_path) == set()


def test_list_applied_rule_slugs_with_rules(tmp_path):
    """Returns slugs of existing acumen-*.md rule files."""
    rules_dir = tmp_path / ".claude" / "rules"
    rules_dir.mkdir(parents=True)
    (rules_dir / "acumen-use-python3.md").write_text("rule")
    (rules_dir / "acumen-run-tests-first.md").write_text("rule")
    (rules_dir / "other-rule.md").write_text("not acumen")

    slugs = list_applied_rule_slugs(tmp_path)
    assert slugs == {"use-python3", "run-tests-first"}


# -- generate_proposals dedup --


def test_generate_proposals_skips_existing_rule_slug(tmp_path):
    """Skips insights whose slug matches an already-applied rule."""
    insights = [_insight("Use python3 not python", category="correction")]
    # The slug for this would be "use-python3-not-python"
    existing = {"use-python3-not-python"}
    proposals = generate_proposals(insights, existing_rule_slugs=existing)
    assert proposals == []


def test_generate_proposals_partial_dedup():
    """Only skips insights that match existing slugs, not all."""
    insights = [
        _insight("Use python3 not python", category="correction"),
        _insight("Run tests before committing", category="correction"),
    ]
    existing = {"use-python3-not-python"}
    proposals = generate_proposals(insights, existing_rule_slugs=existing)
    assert len(proposals) == 1
    assert "Run tests" in proposals[0]["description"]


def test_generate_proposals_stores_tools():
    """Tools from insight are carried into the proposal."""
    insights = [_insight("Use python3 not python", category="correction", tools=["Bash"])]
    proposals = generate_proposals(insights)
    assert proposals[0]["tools"] == ["Bash"]


def test_generate_proposals_tools_default_empty():
    """Proposals have empty tools list when insight has none."""
    insights = [_insight("Some insight without tools")]
    proposals = generate_proposals(insights)
    assert proposals[0]["tools"] == []


# -- measure_effectiveness --


def _obs(tool, outcome, timestamp):
    return {"tool_name": tool, "outcome": outcome, "timestamp": timestamp, "error_type": None}


def test_measure_effectiveness_insufficient_data():
    """Returns empty list when insufficient observations on either side."""
    proposals = [{
        "status": "auto-applied",
        "applied_at": "2026-03-20T12:00:00+00:00",
        "tools": ["Bash"],
        "description": "Use python3",
    }]
    # Only 3 observations before -- below threshold of 5
    obs = [_obs("Bash", "error", "2026-03-19T10:00:00+00:00") for _ in range(3)]
    changed = measure_effectiveness(proposals, obs)
    assert changed == []


def test_measure_effectiveness_effective():
    """Detects effective rule: error rate dropped >10% after application."""
    applied_at = "2026-03-20T12:00:00+00:00"
    proposals = [{
        "status": "auto-applied",
        "applied_at": applied_at,
        "tools": ["Bash"],
        "description": "Use python3",
    }]
    before = [_obs("Bash", "error", "2026-03-19T10:00:00+00:00") for _ in range(8)]
    after = [_obs("Bash", "success", "2026-03-21T10:00:00+00:00") for _ in range(8)]
    changed = measure_effectiveness(proposals, before + after)
    assert len(changed) == 1
    assert changed[0]["effectiveness"] == "effective"


def test_measure_effectiveness_harmful():
    """Detects harmful rule: error rate increased >10% after application."""
    applied_at = "2026-03-20T12:00:00+00:00"
    proposals = [{
        "status": "auto-applied",
        "applied_at": applied_at,
        "tools": ["Bash"],
        "description": "Some rule",
    }]
    before = [_obs("Bash", "success", "2026-03-19T10:00:00+00:00") for _ in range(8)]
    after = [_obs("Bash", "error", "2026-03-21T10:00:00+00:00") for _ in range(8)]
    changed = measure_effectiveness(proposals, before + after)
    assert len(changed) == 1
    assert changed[0]["effectiveness"] == "harmful"


def test_measure_effectiveness_neutral():
    """Rates within 10% delta produce neutral verdict."""
    applied_at = "2026-03-20T12:00:00+00:00"
    proposals = [{
        "status": "auto-applied",
        "applied_at": applied_at,
        "tools": ["Bash"],
        "description": "Some rule",
    }]
    # 20% error rate before and after -- no significant change
    before = [_obs("Bash", "error" if i < 2 else "success", "2026-03-19T10:00:00+00:00") for i in range(10)]
    after = [_obs("Bash", "error" if i < 2 else "success", "2026-03-21T10:00:00+00:00") for i in range(10)]
    changed = measure_effectiveness(proposals, before + after)
    assert len(changed) == 1
    assert changed[0]["effectiveness"] == "neutral"


def test_measure_effectiveness_skips_non_applied():
    """Only measures proposals with status auto-applied."""
    proposals = [
        {"status": "proposed", "applied_at": "2026-03-20T12:00:00+00:00", "tools": ["Bash"], "description": "x"},
        {"status": "reverted", "applied_at": "2026-03-20T12:00:00+00:00", "tools": ["Bash"], "description": "y"},
    ]
    obs = [_obs("Bash", "error", "2026-03-19T10:00:00+00:00") for _ in range(10)]
    assert measure_effectiveness(proposals, obs) == []


def test_measure_effectiveness_no_change_if_same_verdict():
    """Does not add to changed list if verdict is already the same."""
    applied_at = "2026-03-20T12:00:00+00:00"
    proposals = [{
        "status": "auto-applied",
        "applied_at": applied_at,
        "tools": ["Bash"],
        "description": "Use python3",
        "effectiveness": "effective",  # already recorded
    }]
    before = [_obs("Bash", "error", "2026-03-19T10:00:00+00:00") for _ in range(8)]
    after = [_obs("Bash", "success", "2026-03-21T10:00:00+00:00") for _ in range(8)]
    changed = measure_effectiveness(proposals, before + after)
    assert changed == []  # verdict didn't change


# -- scope_hint -> global_candidate --


def test_generate_proposals_scope_hint_sets_global_candidate():
    """Insights with scope_hint='global' produce proposals with scope='global_candidate'."""
    insights = [_insight("Use python3 not python", category="correction", scope_hint="global")]
    proposals = generate_proposals(insights)
    assert proposals[0]["scope"] == "global_candidate"


def test_generate_proposals_no_scope_hint_no_scope_field():
    """Insights without scope_hint produce proposals without scope field."""
    insights = [_insight("Run tests before commit", category="correction")]
    proposals = generate_proposals(insights)
    assert "scope" not in proposals[0]


# -- promote_to_global --


def test_promote_to_global_writes_to_home_claude_rules(tmp_path, monkeypatch):
    """promote_to_global writes rule to ~/.claude/rules/acumen-{slug}.md."""
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    proposal = {
        "description": "Use python3 not python",
        "rule_text": "# Acumen insight\n\nUse python3 not python",
        "status": "auto-applied",
        "target": "rule",
    }
    path = promote_to_global(proposal)

    assert path == tmp_path / ".claude" / "rules" / "acumen-use-python3-not-python.md"
    assert path.exists()
    assert "python3" in path.read_text()


def test_promote_to_global_updates_proposal_in_place(tmp_path, monkeypatch):
    """promote_to_global sets scope='global' and promoted_at on the proposal dict."""
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    proposal = {
        "description": "Use python3 not python",
        "rule_text": "# Acumen insight\n\nUse python3",
        "status": "auto-applied",
        "target": "rule",
    }
    promote_to_global(proposal)

    assert proposal["scope"] == "global"
    assert "promoted_at" in proposal
    datetime.fromisoformat(proposal["promoted_at"])


def test_promote_to_global_creates_dir_if_missing(tmp_path, monkeypatch):
    """promote_to_global creates ~/.claude/rules/ if it doesn't exist."""
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    proposal = {
        "description": "Some universal rule",
        "rule_text": "# Rule\n\nContent",
        "status": "auto-applied",
        "target": "rule",
    }
    path = promote_to_global(proposal)
    assert path.parent.is_dir()
    assert path.exists()

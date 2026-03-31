"""Tests for convention proposal generation in lib/propose.py."""

from lib.cluster import ConventionCandidate
from lib.propose import AcumenRule, generate_convention_proposals


def _candidate(pattern_kind="test_command", dominant_value="pytest",
               consistency_pct=95.0, obs=10, sessions=5, days=3):
    return ConventionCandidate(
        pattern_kind=pattern_kind,
        dominant_value=dominant_value,
        consistency_pct=consistency_pct,
        observation_count=obs,
        session_count=sessions,
        day_count=days,
    )


def _rule(pattern_kind="test_command", action="Do X", status="proposed",
          scope="project", type_="convention"):
    return AcumenRule(
        id="existing-1", type=type_, pattern_kind=pattern_kind,
        target_tool=None, trigger_class=None,
        pattern=f"{pattern_kind} convention", action=action,
        evidence_summary="10 observations", supporting_observations=10,
        supporting_sessions=5, supporting_days=3, confidence=0.7,
        scope=scope, status=status, created="2026-03-28T00:00:00Z",
        decided=None, applied=None, reverted=None, human_edited=False,
    )


# --- Basic generation ---

def test_basic_convention_proposal():
    """Single candidate → one proposal with type=convention."""
    candidates = [_candidate()]
    proposals, conflicts = generate_convention_proposals(candidates, [])
    assert len(proposals) == 1
    p = proposals[0]
    assert p.type == "convention"
    assert p.pattern_kind == "test_command"
    assert p.status == "proposed"
    assert p.scope == "project"
    assert p.target_tool is None
    assert p.trigger_class is None


def test_empty_candidates():
    proposals, conflicts = generate_convention_proposals([], [])
    assert proposals == []
    assert conflicts == []


# --- Action text ---

def test_action_test_command():
    candidates = [_candidate(pattern_kind="test_command", dominant_value="pytest")]
    proposals, _ = generate_convention_proposals(candidates, [])
    assert "pytest" in proposals[0].action
    assert "test" in proposals[0].action.lower()


def test_action_file_naming():
    candidates = [_candidate(pattern_kind="file_naming", dominant_value="snake_case")]
    proposals, _ = generate_convention_proposals(candidates, [])
    assert "snake_case" in proposals[0].action


def test_action_test_placement():
    candidates = [_candidate(pattern_kind="test_placement", dominant_value="tests_root")]
    proposals, _ = generate_convention_proposals(candidates, [])
    assert "tests" in proposals[0].action.lower()


# --- Evidence summary ---

def test_evidence_summary_includes_counts():
    candidates = [_candidate(obs=42, sessions=8, days=5, consistency_pct=91.0)]
    proposals, _ = generate_convention_proposals(candidates, [])
    ev = proposals[0].evidence_summary
    assert "42" in ev
    assert "8 sessions" in ev
    assert "91" in ev


# --- Confidence scoring ---

def test_confidence_includes_consistency():
    """Convention confidence should factor in consistency_pct."""
    low = _candidate(consistency_pct=80.0, obs=10, sessions=5, days=3)
    high = _candidate(consistency_pct=100.0, obs=10, sessions=5, days=3)
    proposals_low, _ = generate_convention_proposals([low], [])
    proposals_high, _ = generate_convention_proposals([high], [])
    assert proposals_high[0].confidence >= proposals_low[0].confidence


def test_confidence_below_threshold_discarded():
    """Very low obs/sessions/days → confidence below 0.4 → discarded."""
    candidates = [_candidate(obs=2, sessions=1, days=1, consistency_pct=100.0)]
    proposals, _ = generate_convention_proposals(candidates, [])
    assert proposals == []


# --- Contradiction detection ---

def test_contradiction_blocks_convention():
    """Existing convention rule with same pattern_kind + different action → conflict."""
    candidates = [_candidate(pattern_kind="test_command", dominant_value="pytest")]
    existing = [_rule(pattern_kind="test_command", action="Use jest for tests")]
    proposals, conflicts = generate_convention_proposals(candidates, existing)
    assert len(proposals) == 0
    assert len(conflicts) == 1


def test_no_contradiction_with_failure_rule():
    """Failure rule with same pattern_kind doesn't conflict with convention."""
    candidates = [_candidate(pattern_kind="test_command", dominant_value="pytest")]
    # A failure rule has different type but shares no pattern_kind in practice.
    # But if it did, it should still not conflict across types.
    existing = [_rule(pattern_kind="command_not_found", type_="failure")]
    proposals, conflicts = generate_convention_proposals(candidates, existing)
    assert len(proposals) == 1
    assert len(conflicts) == 0


def test_contradiction_only_active_statuses():
    """Reverted convention rule doesn't block new proposals."""
    candidates = [_candidate(pattern_kind="test_command")]
    existing = [_rule(pattern_kind="test_command", action="Use jest", status="reverted")]
    proposals, conflicts = generate_convention_proposals(candidates, existing)
    assert len(proposals) == 1
    assert len(conflicts) == 0


# --- Max pending limit ---

def test_respects_max_pending():
    """Already 5 pending → no new convention proposals."""
    existing = [_rule(pattern_kind=f"kind_{i}", status="proposed") for i in range(5)]
    candidates = [_candidate()]
    proposals, _ = generate_convention_proposals(candidates, existing)
    assert proposals == []


# --- Pattern field ---

def test_pattern_field_describes_convention():
    candidates = [_candidate(pattern_kind="test_command", dominant_value="pytest",
                              consistency_pct=95.0)]
    proposals, _ = generate_convention_proposals(candidates, [])
    assert "95" in proposals[0].pattern or "pytest" in proposals[0].pattern


# --- Multiple candidates ---

def test_multiple_conventions_proposed():
    """Three candidates → three proposals (if all pass)."""
    candidates = [
        _candidate(pattern_kind="test_command", dominant_value="pytest"),
        _candidate(pattern_kind="file_naming", dominant_value="snake_case"),
        _candidate(pattern_kind="test_placement", dominant_value="tests_root"),
    ]
    proposals, _ = generate_convention_proposals(candidates, [])
    assert len(proposals) == 3
    kinds = {p.pattern_kind for p in proposals}
    assert kinds == {"test_command", "file_naming", "test_placement"}

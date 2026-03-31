"""Tests for lib/propose.py -- proposal generation + contradiction detection."""

from lib.cluster import FailureCluster
from lib.propose import AcumenRule, generate_proposals


def _cluster(tool_name="Bash", error_class="command_not_found",
             pattern_kind="command_not_found", obs=20, sessions=10, days=4,
             families=None):
    """Shorthand for a FailureCluster."""
    return FailureCluster(
        tool_name=tool_name,
        error_class=error_class,
        pattern_kind=pattern_kind,
        observation_count=obs,
        session_count=sessions,
        day_count=days,
        sample_command_families=families or ["shell"],
    )


def _rule(pattern_kind="command_not_found", action="Do X", status="proposed",
          scope="project"):
    """Shorthand for an existing AcumenRule."""
    return AcumenRule(
        id="existing-1", type="failure", pattern_kind=pattern_kind,
        target_tool="Bash", trigger_class="command_not_found",
        pattern="command_not_found errors", action=action,
        evidence_summary="10 failures", supporting_observations=10,
        supporting_sessions=5, supporting_days=3, confidence=0.7,
        scope=scope, status=status, created="2026-03-28T00:00:00Z",
        decided=None, applied=None, reverted=None, human_edited=False,
    )


# --- Basic proposal generation ---

def test_basic_proposal_from_cluster():
    """Single cluster → one proposal with correct fields."""
    clusters = [_cluster()]
    proposals, conflicts = generate_proposals(clusters, [])
    assert len(proposals) == 1
    assert len(conflicts) == 0
    p = proposals[0]
    assert p.type == "failure"
    assert p.pattern_kind == "command_not_found"
    assert p.target_tool == "Bash"
    assert p.trigger_class == "command_not_found"
    assert p.scope == "project"
    assert p.status == "proposed"
    assert p.decided is None
    assert p.applied is None
    assert p.reverted is None
    assert p.human_edited is False
    assert p.id  # non-empty UUID


def test_empty_clusters():
    """No clusters → no proposals."""
    proposals, conflicts = generate_proposals([], [])
    assert proposals == []
    assert conflicts == []


# --- Confidence scoring ---

def test_confidence_formula_max():
    """20+ obs, 10+ sessions, 7+ days → confidence 1.0."""
    clusters = [_cluster(obs=20, sessions=10, days=7)]
    proposals, _ = generate_proposals(clusters, [])
    assert proposals[0].confidence == 1.0


def test_confidence_formula_partial():
    """10 obs, 5 sessions, 3 days → 0.5*0.5 + 0.5*0.3 + (3/7)*0.2 ≈ 0.486."""
    clusters = [_cluster(obs=10, sessions=5, days=3)]
    proposals, _ = generate_proposals(clusters, [])
    expected = min(10/20, 1.0) * 0.5 + min(5/10, 1.0) * 0.3 + min(3/7, 1.0) * 0.2
    assert abs(proposals[0].confidence - expected) < 0.001


def test_confidence_below_threshold_discarded():
    """Confidence < 0.4 → proposal discarded."""
    # 3 obs, 1 session, 1 day → very low confidence
    clusters = [_cluster(obs=3, sessions=1, days=1)]
    proposals, _ = generate_proposals(clusters, [])
    assert proposals == []


# --- Contradiction detection ---

def test_contradiction_blocks_proposal():
    """Existing rule with same pattern_kind + different action → conflict."""
    clusters = [_cluster(pattern_kind="command_not_found")]
    existing = [_rule(pattern_kind="command_not_found", action="Different action")]
    proposals, conflicts = generate_proposals(clusters, existing)
    assert len(proposals) == 0
    assert len(conflicts) == 1
    assert conflicts[0].pattern_kind == "command_not_found"


def test_no_contradiction_same_action():
    """Existing rule with same pattern_kind + same action → no conflict."""
    clusters = [_cluster(pattern_kind="command_not_found")]
    # Action matches what generate_proposals would produce
    expected_action = "Verify command exists before running: shell commands"
    existing = [_rule(pattern_kind="command_not_found", action=expected_action)]
    proposals, conflicts = generate_proposals(clusters, existing)
    assert len(conflicts) == 0
    # Proposal is still generated (same action = not a conflict)
    assert len(proposals) == 1


def test_contradiction_only_active_statuses():
    """Reverted rules don't count as conflicts."""
    clusters = [_cluster(pattern_kind="command_not_found")]
    existing = [_rule(pattern_kind="command_not_found", action="Old", status="reverted")]
    proposals, conflicts = generate_proposals(clusters, existing)
    assert len(conflicts) == 0
    assert len(proposals) == 1


# --- Max 5 pending proposals ---

def test_max_five_pending():
    """Already 5 pending → new proposals skipped."""
    existing = [_rule(pattern_kind=f"kind_{i}", status="proposed") for i in range(5)]
    clusters = [_cluster(pattern_kind="command_not_found")]
    proposals, _ = generate_proposals(clusters, existing)
    assert proposals == []


def test_max_five_counts_only_proposed():
    """Applied/reverted rules don't count toward the 5 pending limit."""
    existing = [_rule(pattern_kind=f"kind_{i}", status="applied") for i in range(5)]
    clusters = [_cluster(pattern_kind="command_not_found")]
    proposals, _ = generate_proposals(clusters, existing)
    assert len(proposals) == 1


# --- Evidence summary format ---

def test_evidence_summary_format():
    """Evidence summary cites counts in expected format."""
    clusters = [_cluster(obs=47, sessions=12, days=4)]
    proposals, _ = generate_proposals(clusters, [])
    assert "47 failures" in proposals[0].evidence_summary
    assert "12 sessions" in proposals[0].evidence_summary
    assert "4 days" in proposals[0].evidence_summary


# --- Action text for known pattern_kinds ---

def test_action_python_launcher():
    clusters = [_cluster(pattern_kind="python_launcher", families=["python"])]
    proposals, _ = generate_proposals(clusters, [])
    assert proposals[0].action == "Use python3 instead of python"


def test_action_command_not_found():
    clusters = [_cluster(pattern_kind="command_not_found", families=["shell"])]
    proposals, _ = generate_proposals(clusters, [])
    assert "Verify command exists before running" in proposals[0].action
    assert "shell" in proposals[0].action


def test_action_file_not_found():
    clusters = [_cluster(pattern_kind="file_not_found", tool_name="Edit",
                         error_class="file_not_found")]
    proposals, _ = generate_proposals(clusters, [])
    assert "Check file exists" in proposals[0].action
    assert "Edit" in proposals[0].action


def test_action_permission_denied():
    clusters = [_cluster(pattern_kind="permission_denied", tool_name="Write",
                         error_class="permission_denied")]
    proposals, _ = generate_proposals(clusters, [])
    assert "Check file permissions" in proposals[0].action
    assert "Write" in proposals[0].action


def test_action_syntax_error():
    clusters = [_cluster(pattern_kind="syntax_error", error_class="syntax_error",
                         families=["python"])]
    proposals, _ = generate_proposals(clusters, [])
    assert "Verify command syntax" in proposals[0].action
    assert "python" in proposals[0].action


def test_action_test_failure():
    clusters = [_cluster(pattern_kind="test_failure", error_class="test_failure",
                         families=["test"])]
    proposals, _ = generate_proposals(clusters, [])
    assert "Review test setup" in proposals[0].action
    assert "test" in proposals[0].action


def test_action_unknown_pattern():
    clusters = [_cluster(pattern_kind="something_new", error_class="something_new")]
    proposals, _ = generate_proposals(clusters, [])
    assert "Review recurring" in proposals[0].action
    assert "something_new" in proposals[0].action
    assert "Bash" in proposals[0].action

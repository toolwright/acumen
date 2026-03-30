"""Integration tests for the reflection pipeline: observations -> scoring -> storage -> display."""

import json
import shutil
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

from lib.store import read_observations, write_insight, read_insights
from lib.scorer import score_insight, dedup_insights, rank_insights
from lib.formatter import format_status, format_insights
from lib.improver import generate_proposals, apply_proposal

FIXTURES_DIR = Path(__file__).parent / "fixtures"
HOOK_PATH = Path(__file__).parent.parent / "hooks" / "observe.sh"


def _make_observations(tmp_path, entries):
    """Write observation entries to JSONL files in tmp_path/observations/."""
    obs_dir = tmp_path / "observations"
    obs_dir.mkdir(parents=True, exist_ok=True)
    by_date = {}
    for entry in entries:
        date = entry["timestamp"][:10]
        by_date.setdefault(date, []).append(entry)
    for date, obs_list in by_date.items():
        with open(obs_dir / f"{date}.jsonl", "a") as f:
            for obs in obs_list:
                f.write(json.dumps(obs) + "\n")


def _sample_observations(n_success=10, n_error=5):
    """Generate realistic sample observations."""
    now = datetime.now(timezone.utc)
    obs = []
    for i in range(n_success):
        obs.append({
            "tool_name": "Bash",
            "session_id": "sess-1",
            "timestamp": (now - timedelta(hours=i)).isoformat() + "Z",
            "outcome": "success",
            "error_type": None,
        })
    for i in range(n_error):
        obs.append({
            "tool_name": "Bash",
            "session_id": "sess-1",
            "timestamp": (now - timedelta(hours=i + 1)).isoformat() + "Z",
            "outcome": "error",
            "error_type": "nonzero_exit",
        })
    return obs


# -- Insight format compatibility with scorer and store --


def test_insight_format_scores_correctly(tmp_path):
    """Insight in the reflector's output format can be scored by scorer.py."""
    insight = {
        "description": "Bash tool fails frequently with nonzero exit codes",
        "category": "error_pattern",
        "evidence_count": 5,
        "tools": ["Bash"],
    }
    observations = _sample_observations(n_success=10, n_error=5)
    scores = score_insight(insight, observations)

    assert "confidence" in scores
    assert "impact" in scores
    assert "combined" in scores
    assert 0 <= scores["confidence"] <= 1
    assert 0 <= scores["impact"] <= 1
    assert 0 <= scores["combined"] <= 1


def test_insight_format_stores_correctly(tmp_path):
    """Insight in the reflector's output format can be written/read by store.py."""
    insight = {
        "description": "Read tool called repeatedly on same file",
        "category": "retry_pattern",
        "evidence_count": 4,
        "tools": ["Read"],
        "confidence": 0.6,
        "impact": 0.3,
        "combined": 0.42,
    }
    write_insight(tmp_path, insight)
    stored = read_insights(tmp_path)

    assert len(stored) == 1
    assert stored[0]["description"] == insight["description"]
    assert stored[0]["evidence_count"] == 4


def test_insight_dedup_with_existing(tmp_path):
    """New insights dedup correctly against existing insights from store."""
    existing = [
        {
            "description": "Bash tool fails frequently with nonzero exit codes",
            "category": "error_pattern",
            "evidence_count": 5,
            "tools": ["Bash"],
            "confidence": 0.5,
            "impact": 0.6,
            "combined": 0.56,
        }
    ]
    new = [
        {
            "description": "Bash tool fails frequently with nonzero exit codes",
            "category": "error_pattern",
            "evidence_count": 3,
            "tools": ["Bash"],
        }
    ]
    merged = dedup_insights(new, existing)

    assert len(merged) == 1
    assert merged[0]["evidence_count"] == 8  # 5 + 3


def test_full_pipeline_observe_score_rank(tmp_path):
    """Full pipeline: observations -> insights -> score -> rank -> store."""
    observations = _sample_observations(n_success=10, n_error=8)
    _make_observations(tmp_path, observations)

    # Read back observations through store
    read_obs = read_observations(tmp_path)
    assert len(read_obs) == 18

    # Simulate reflector output
    new_insights = [
        {
            "description": "Bash tool fails frequently with nonzero exit codes",
            "category": "error_pattern",
            "evidence_count": 8,
            "tools": ["Bash"],
        },
        {
            "description": "Bash tool shows recovery pattern: errors followed by success",
            "category": "recovery_pattern",
            "evidence_count": 3,
            "tools": ["Bash"],
        },
    ]

    # Score each
    for ins in new_insights:
        relevant = [o for o in read_obs if o.get("tool_name") in ins["tools"]]
        scores = score_insight(ins, relevant)
        ins.update(scores)

    # Rank
    ranked = rank_insights(new_insights)
    assert ranked[0]["combined"] >= ranked[1]["combined"]

    # Dedup against empty existing
    merged = dedup_insights(ranked, [])
    assert len(merged) == 2

    # Store
    for ins in merged:
        write_insight(tmp_path, ins)
    stored = read_insights(tmp_path)
    assert len(stored) == 2


def test_pipeline_with_no_observations(tmp_path):
    """Pipeline handles empty observation directory gracefully."""
    read_obs = read_observations(tmp_path)
    assert read_obs == []

    insight = {
        "description": "No patterns detected",
        "category": "best_practice",
        "evidence_count": 0,
        "tools": [],
    }
    scores = score_insight(insight, [])
    assert scores["confidence"] == 0.0
    assert scores["impact"] == 0.0
    assert scores["combined"] == 0.0


def test_error_pattern_scores_higher_than_informational(tmp_path):
    """Error patterns score higher than best practice patterns with same evidence."""
    observations = _sample_observations(n_success=5, n_error=5)

    error_insight = {
        "description": "Bash fails on test runs",
        "category": "error_pattern",
        "evidence_count": 5,
        "tools": ["Bash"],
    }
    info_insight = {
        "description": "Bash used frequently for file listing",
        "category": "best_practice",
        "evidence_count": 5,
        "tools": ["Bash"],
    }

    error_scores = score_insight(error_insight, observations)
    info_scores = score_insight(info_insight, observations)

    assert error_scores["impact"] >= info_scores["impact"]


# -- Step 6: End-to-end pipeline tests --


def _load_fixture_observations():
    """Load the 20 sample observations from fixtures/sample_observations.jsonl."""
    path = FIXTURES_DIR / "sample_observations.jsonl"
    obs = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            obs.append(json.loads(line))
    return obs


def test_fixture_file_has_20_observations():
    """Fixture file contains exactly 20 realistic observations."""
    obs = _load_fixture_observations()
    assert len(obs) == 20
    for o in obs:
        assert "tool_name" in o
        assert "session_id" in o
        assert "timestamp" in o
        assert "outcome" in o


def test_observe_hook_produces_valid_jsonl(tmp_path):
    """Feed sample PostToolUse events through observe.sh and verify JSONL output."""
    # observe.sh is now pure bash -- no jq dependency

    # observe.sh writes to .acumen/observations/ relative to cwd
    hook_events = [
        {"tool_name": "Bash", "session_id": "hook-test", "tool_response": {"exit_code": 0}},
        {"tool_name": "Bash", "session_id": "hook-test", "tool_response": {"exit_code": 1}},
        {"tool_name": "Read", "session_id": "hook-test", "tool_response": {"stdout": "ok"}},
    ]
    for event in hook_events:
        subprocess.run(
            ["bash", str(HOOK_PATH)],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )

    obs_dir = tmp_path / ".acumen" / "observations"
    assert obs_dir.is_dir()
    jsonl_files = list(obs_dir.glob("*.jsonl"))
    assert len(jsonl_files) >= 1

    all_obs = []
    for f in jsonl_files:
        for line in f.read_text().splitlines():
            obj = json.loads(line)
            all_obs.append(obj)

    assert len(all_obs) == 3
    # Verify metadata fields present, no tool_input/tool_response content
    for obs in all_obs:
        assert "tool_name" in obs
        assert "timestamp" in obs
        assert "outcome" in obs
        assert "tool_input" not in obs
        assert "tool_response" not in obs


def test_full_pipeline_with_fixture_data(tmp_path):
    """End-to-end: fixture observations -> store -> score -> format status + insights."""
    obs = _load_fixture_observations()
    _make_observations(tmp_path, obs)

    # 1. Read via store
    read_obs = read_observations(tmp_path)
    assert len(read_obs) == 20

    # 2. Simulate reflector insights
    insights = [
        {
            "description": "Bash tool has high error rate with nonzero exits",
            "category": "error_pattern",
            "evidence_count": 6,
            "tools": ["Bash"],
        },
        {
            "description": "Edit tool occasionally fails with tool_error",
            "category": "error_pattern",
            "evidence_count": 1,
            "tools": ["Edit"],
        },
        {
            "description": "Read tool used frequently without errors",
            "category": "best_practice",
            "evidence_count": 4,
            "tools": ["Read"],
        },
    ]

    # 3. Score via scorer
    for ins in insights:
        relevant = [o for o in read_obs if o.get("tool_name") in ins["tools"]]
        scores = score_insight(ins, relevant)
        ins.update(scores)

    # 4. Rank
    ranked = rank_insights(insights)
    assert ranked[0]["combined"] >= ranked[-1]["combined"]

    # 5. Dedup + store
    merged = dedup_insights(ranked, [])
    for ins in merged:
        write_insight(tmp_path, ins)
    stored = read_insights(tmp_path)
    assert len(stored) == 3

    # 6. Format via formatter -- verify coherent output
    status = format_status(read_obs, stored)
    assert "ACUMEN STATUS" in status
    assert "Sessions observed: 2" in status
    assert "Total observations: 20" in status
    assert "Error rate:" in status
    assert "Active insights: 3" in status
    assert "Top insights:" in status
    # At least one insight description shows up
    assert "Bash tool has high error rate" in status

    insights_output = format_insights(stored)
    assert "ACUMEN INSIGHTS" in insights_output
    assert "3 insight(s)" in insights_output
    # All three insights appear
    assert "Bash tool has high error rate" in insights_output
    assert "Edit tool occasionally fails" in insights_output
    assert "Read tool used frequently" in insights_output


# -- Phase 2: insight -> proposal -> approve -> applied file --


def test_insight_to_proposal_to_rule(tmp_path):
    """Full pipeline: insight -> generate proposal -> approve -> apply -> rule file exists."""
    insight = {
        "description": "Use python3 not python in Bash commands",
        "category": "correction",
        "evidence_count": 7,
        "tools": ["Bash"],
    }
    proposals = generate_proposals([insight])
    assert len(proposals) == 1
    assert proposals[0]["target"] == "rule"

    # Approve and apply
    proposals[0]["status"] = "approved"
    path = apply_proposal(tmp_path, proposals[0])

    assert path.exists()
    assert path.parent == tmp_path / ".claude" / "rules"
    assert path.name.startswith("acumen-")
    assert "python3" in path.read_text()


def test_insight_to_proposal_to_rule(tmp_path):
    """Full pipeline: non-correction insight -> rule file (all insights become rules)."""
    insight = {
        "description": "Read tool is heavily used without errors",
        "category": "best_practice",
        "evidence_count": 12,
        "tools": ["Read"],
    }
    proposals = generate_proposals([insight])
    assert proposals[0]["target"] == "rule"

    proposals[0]["status"] = "approved"
    path = apply_proposal(tmp_path, proposals[0])

    assert path.exists()
    assert path.name.startswith("acumen-")
    assert "Read tool" in path.read_text()


def test_full_pipeline_observe_to_apply(tmp_path):
    """End-to-end: observations -> score -> insights -> proposals -> apply."""
    observations = _sample_observations(n_success=10, n_error=8)
    _make_observations(tmp_path, observations)
    read_obs = read_observations(tmp_path)

    # Simulate reflector output
    insights = [
        {
            "description": "Bash commands frequently fail with nonzero exit",
            "category": "correction",
            "evidence_count": 8,
            "tools": ["Bash"],
        },
        {
            "description": "Error recovery follows a retry-then-succeed pattern",
            "category": "recovery_pattern",
            "evidence_count": 4,
            "tools": ["Bash"],
        },
    ]
    # Score
    for ins in insights:
        relevant = [o for o in read_obs if o.get("tool_name") in ins["tools"]]
        scores = score_insight(ins, relevant)
        ins.update(scores)

    # Generate proposals
    proposals = generate_proposals(insights)
    assert len(proposals) == 2
    assert proposals[0]["target"] == "rule"      # correction
    assert proposals[1]["target"] == "rule"      # all insights become rules

    # Approve and apply both
    for p in proposals:
        p["status"] = "approved"
        apply_proposal(tmp_path, p)

    # Verify files -- all go to rules
    rules = list((tmp_path / ".claude" / "rules").glob("acumen-*.md"))
    assert len(rules) == 2


def test_pipeline_observe_hook_to_format(tmp_path):
    """Full pipeline through observe.sh: hook -> store.read -> score -> format."""
    # observe.sh is now pure bash -- no jq dependency

    # Feed events through the actual hook
    events = [
        {"tool_name": "Bash", "session_id": "e2e", "tool_response": {"exit_code": 0}},
        {"tool_name": "Bash", "session_id": "e2e", "tool_response": {"exit_code": 1}},
        {"tool_name": "Bash", "session_id": "e2e", "tool_response": {"exit_code": 1}},
        {"tool_name": "Read", "session_id": "e2e", "tool_response": {"stdout": "data"}},
        {"tool_name": "Edit", "session_id": "e2e", "tool_response": {"error": "file not found"}},
    ]
    for event in events:
        subprocess.run(
            ["bash", str(HOOK_PATH)],
            input=json.dumps(event),
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
        )

    # Read from the .acumen directory that observe.sh created
    scope = tmp_path / ".acumen"
    obs = read_observations(scope)
    assert len(obs) == 5

    # Score a synthetic insight against these observations
    insight = {
        "description": "Bash errors on test commands",
        "category": "error_pattern",
        "evidence_count": 2,
        "tools": ["Bash"],
    }
    bash_obs = [o for o in obs if o.get("tool_name") == "Bash"]
    scores = score_insight(insight, bash_obs)
    insight.update(scores)
    assert insight["combined"] > 0

    # Format output
    status = format_status(obs, [insight])
    assert "ACUMEN STATUS" in status
    assert "Total observations: 5" in status
    assert "Active insights: 1" in status

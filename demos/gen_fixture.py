"""Generate fixture data for Acumen demo recordings.

Creates realistic .acumen/ data in a target directory so the real Python
lib code can run against it and produce genuine output for VHS recordings.

Usage:
    python3 demos/gen_fixture.py --state 1 --dir /tmp/acumen-demo1
    python3 demos/gen_fixture.py --state 2 --dir /tmp/acumen-demo2
    python3 demos/gen_fixture.py --state 3 --dir /tmp/acumen-demo3
"""

import argparse
import json
import uuid
from pathlib import Path

# --- Observation helpers ---

def _obs(tool, sid, ts, outcome="success", **kw):
    return {
        "tool_name": tool, "session_id": sid, "timestamp": ts,
        "outcome": outcome, "error_type": kw.get("error_type"),
        "command_family": kw.get("cf"), "command_signature": kw.get("cs"),
        "file_basename": kw.get("fb"), "path_pattern": None,
        "write_kind": kw.get("wk"), "environment_tag": None,
        "error_class": kw.get("ec"), "burst_count": 1,
    }

# Realistic success patterns per day
_SUCCESS = [
    ("Bash", "python", "python3", None, None),
    ("Bash", "python", "python3", None, None),
    ("Bash", "git", None, None, None),
    ("Bash", "git", None, None, None),
    ("Bash", "shell", None, None, None),
    ("Bash", "test", "pytest", None, None),
    ("Bash", "test", "pytest", None, None),
    ("Read", None, None, "store.py", None),
    ("Read", None, None, "classify.py", None),
    ("Read", None, None, "test_store.py", None),
    ("Read", None, None, "main.py", None),
    ("Edit", None, None, "store.py", "edit"),
    ("Edit", None, None, "main.py", "edit"),
    ("Edit", None, None, "config.py", "edit"),
    ("Write", None, None, "test_classify.py", "create"),
    ("Grep", None, None, None, None),
    ("Glob", None, None, None, None),
    ("Bash", "test", "pytest", None, None),
]


def _gen_session(sid, dates, n_python_err=0, n_edit_err=0):
    """Generate a session's observations: successes per day + errors."""
    records = []
    h, m = 9, 0
    for date in dates:
        for tool, cf, cs, fb, wk in _SUCCESS:
            ts = f"{date}T{h:02d}:{m:02d}:00Z"
            records.append(_obs(tool, sid, ts, cf=cf, cs=cs, fb=fb, wk=wk))
            m += 2
            if m >= 60:
                m = 0; h += 1
    # Python command_not_found errors (spread across first days)
    for i in range(n_python_err):
        date = dates[i % len(dates)]
        ts = f"{date}T{h:02d}:{m:02d}:00Z"
        records.append(_obs("Bash", sid, ts, "error",
                           ec="command_not_found", cf="python",
                           cs="python", error_type="exit_code"))
        m += 1
        if m >= 60:
            m = 0; h += 1
    # Edit file_not_found errors
    for i in range(n_edit_err):
        date = dates[i % len(dates)]
        ts = f"{date}T{h:02d}:{m:02d}:00Z"
        records.append(_obs("Edit", sid, ts, "error",
                           ec="file_not_found", fb="missing.py",
                           error_type="tool_error", wk="edit"))
        m += 1
        if m >= 60:
            m = 0; h += 1
    return records


# --- State builders ---

SESSIONS = {
    "s1": ("a1b2c3d4", ["2026-03-25", "2026-03-26"]),
    "s2": ("e5f6g7h8", ["2026-03-27"]),
    "s3": ("i9j0k1l2", ["2026-03-28", "2026-03-29"]),
    "s4": ("m3n4o5p6", ["2026-03-30", "2026-03-31"]),
}

# Extra early sessions for state 3 (14-day report)
EARLY_SESSIONS = {
    "e1": ("q1r2s3t4", ["2026-03-17", "2026-03-18"]),
    "e2": ("u5v6w7x8", ["2026-03-19", "2026-03-20"]),
    "e3": ("y9z0a1b2", ["2026-03-21", "2026-03-22", "2026-03-23"]),
}


def _write_observations(acumen_dir, sessions_data):
    """Write session JSONL files and index.json."""
    obs_dir = acumen_dir / "observations"
    obs_dir.mkdir(parents=True, exist_ok=True)
    index = {}
    for sid, records in sessions_data.items():
        if not records:
            continue
        path = obs_dir / f"{sid}.jsonl"
        lines = [json.dumps(r, separators=(",", ":")) for r in records]
        path.write_text("\n".join(lines) + "\n")
        timestamps = [r["timestamp"] for r in records]
        index[sid] = {
            "path": f"{sid}.jsonl",
            "first_seen": min(timestamps),
            "last_seen": max(timestamps),
        }
    (obs_dir / "index.json").write_text(json.dumps(index, indent=2))


def _make_rule(pattern_kind, tool, trigger, action, evidence, obs_n, sess_n, days_n,
               confidence, status="proposed", decided=None, applied=None):
    return {
        "id": str(uuid.uuid4()),
        "type": "failure",
        "pattern_kind": pattern_kind,
        "target_tool": tool,
        "trigger_class": trigger,
        "pattern": f"{trigger} errors",
        "action": action,
        "evidence_summary": evidence,
        "supporting_observations": obs_n,
        "supporting_sessions": sess_n,
        "supporting_days": days_n,
        "confidence": confidence,
        "scope": "project",
        "status": status,
        "created": "2026-03-28T12:00:00Z",
        "decided": decided,
        "applied": applied,
        "reverted": None,
        "human_edited": False,
    }


def setup_state_1(demo_dir):
    """Observations only. For Demo 1: observe -> reflect -> propose."""
    acumen = demo_dir / ".acumen"
    acumen.mkdir(parents=True, exist_ok=True)

    sid1, dates1 = SESSIONS["s1"]
    sid2, dates2 = SESSIONS["s2"]
    sid3, dates3 = SESSIONS["s3"]
    sid4, dates4 = SESSIONS["s4"]

    _write_observations(acumen, {
        sid1: _gen_session(sid1, dates1, n_python_err=3, n_edit_err=2),
        sid2: _gen_session(sid2, dates2, n_python_err=2, n_edit_err=2),
        sid3: _gen_session(sid3, dates3, n_python_err=2, n_edit_err=2),
        sid4: _gen_session(sid4, dates4, n_python_err=1, n_edit_err=2),
    })
    print(f"State 1: observations written to {acumen}")


def setup_state_2(demo_dir):
    """Observations + proposed rules. For Demo 2: review -> approve."""
    setup_state_1(demo_dir)
    acumen = demo_dir / ".acumen"

    rules = [
        _make_rule("python_launcher", "Bash", "command_not_found",
                   "Use python3 instead of python",
                   "8 failures across 4 sessions, 5 days",
                   8, 4, 5, 0.55),
        _make_rule("file_not_found", "Edit", "file_not_found",
                   "Check file exists before using Edit tool",
                   "6 failures across 3 sessions, 3 days",
                   6, 3, 3, 0.43),
    ]
    (acumen / "rules.json").write_text(json.dumps(rules, indent=2))
    # Create .claude dir for rule application target
    (demo_dir / ".claude" / "rules").mkdir(parents=True, exist_ok=True)
    print(f"State 2: rules.json written with {len(rules)} proposals")


def setup_state_3(demo_dir):
    """Full state: applied rules + effectiveness. For Demo 3: report."""
    acumen = demo_dir / ".acumen"
    acumen.mkdir(parents=True, exist_ok=True)

    sid1, dates1 = SESSIONS["s1"]
    sid2, dates2 = SESSIONS["s2"]
    sid3, dates3 = SESSIONS["s3"]
    sid4, dates4 = SESSIONS["s4"]
    # Early sessions (before rule) for 14-day span
    e1_sid, e1_dates = EARLY_SESSIONS["e1"]
    e2_sid, e2_dates = EARLY_SESSIONS["e2"]
    e3_sid, e3_dates = EARLY_SESSIONS["e3"]

    # Before rule: high error rate. After rule (Mar 28+): low error rate.
    _write_observations(acumen, {
        e1_sid: _gen_session(e1_sid, e1_dates, n_python_err=4, n_edit_err=2),
        e2_sid: _gen_session(e2_sid, e2_dates, n_python_err=3, n_edit_err=2),
        e3_sid: _gen_session(e3_sid, e3_dates, n_python_err=3, n_edit_err=2),
        sid1: _gen_session(sid1, dates1, n_python_err=3, n_edit_err=2),
        sid2: _gen_session(sid2, dates2, n_python_err=2, n_edit_err=1),
        sid3: _gen_session(sid3, dates3, n_python_err=0, n_edit_err=0),
        sid4: _gen_session(sid4, dates4, n_python_err=0, n_edit_err=0),
    })

    rule1_id = str(uuid.uuid4())
    rule2_id = str(uuid.uuid4())

    rules = [
        _make_rule("python_launcher", "Bash", "command_not_found",
                   "Use python3 instead of python",
                   "7 failures across 3 sessions, 4 days",
                   7, 3, 4, 0.55, status="applied",
                   decided="2026-03-28T14:00:00Z",
                   applied="2026-03-28T14:00:00Z"),
        _make_rule("file_not_found", "Edit", "file_not_found",
                   "Check file exists before using Edit tool",
                   "5 failures across 3 sessions, 3 days",
                   5, 3, 3, 0.43, status="applied",
                   decided="2026-03-28T14:00:00Z",
                   applied="2026-03-28T14:00:00Z"),
        _make_rule("command_not_found", "Bash", "command_not_found",
                   "Verify command exists before running: npm commands",
                   "5 failures across 3 sessions, 2 days",
                   5, 3, 2, 0.40, status="applied",
                   decided="2026-03-29T10:00:00Z",
                   applied="2026-03-29T10:00:00Z"),
        _make_rule("syntax_error", "Bash", "syntax_error",
                   "Review test setup for pytest tests",
                   "6 failures across 3 sessions, 3 days",
                   6, 3, 3, 0.45, status="applied",
                   decided="2026-03-29T11:00:00Z",
                   applied="2026-03-29T11:00:00Z"),
        _make_rule("file_not_found", "Read", "file_not_found",
                   "Use Glob to verify file path before Read",
                   "5 failures across 3 sessions, 2 days",
                   5, 3, 2, 0.42, status="proposed"),
    ]
    # Fix IDs for the first two so effectiveness can reference them
    rules[0]["id"] = rule1_id
    rules[1]["id"] = rule2_id

    (acumen / "rules.json").write_text(json.dumps(rules, indent=2))

    # Effectiveness data
    effectiveness = [
        {
            "rule_id": rule1_id,
            "applied_at": "2026-03-28T14:00:00Z",
            "sessions_observed": 4,
            "target_pattern_before": 9.4,
            "target_pattern_after": 0.4,
            "adherence_rate": None,
            "verdict": "effective",
            "retained_at_2_weeks": None,
        },
        {
            "rule_id": rule2_id,
            "applied_at": "2026-03-28T14:00:00Z",
            "sessions_observed": 4,
            "target_pattern_before": 4.6,
            "target_pattern_after": 1.6,
            "adherence_rate": None,
            "verdict": "effective",
            "retained_at_2_weeks": None,
        },
    ]
    (acumen / "effectiveness.json").write_text(json.dumps(effectiveness, indent=2))

    # Create .claude dir with applied rule files
    rules_dir = demo_dir / ".claude" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    (rules_dir / f"acumen-{rule1_id}.md").write_text(
        "# Acumen rule\n\nUse python3 instead of python\n\n"
        "Observed: command_not_found errors (7 failures across 3 sessions, 4 days)\n")
    (rules_dir / f"acumen-{rule2_id}.md").write_text(
        "# Acumen rule\n\nCheck file exists before using Edit tool\n\n"
        "Observed: file_not_found errors (5 failures across 3 sessions, 3 days)\n")

    print(f"State 3: full state with {len(rules)} rules, {len(effectiveness)} effectiveness records")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", type=int, required=True, choices=[1, 2, 3])
    parser.add_argument("--dir", type=str, required=True)
    args = parser.parse_args()

    demo_dir = Path(args.dir)
    demo_dir.mkdir(parents=True, exist_ok=True)
    # Also init as a basic project
    (demo_dir / ".git").mkdir(exist_ok=True)

    {1: setup_state_1, 2: setup_state_2, 3: setup_state_3}[args.state](demo_dir)

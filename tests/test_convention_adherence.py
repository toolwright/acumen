"""Tests for convention adherence tracking in lib/measure.py."""

from lib.measure import measure_convention_adherence, EffectivenessRecord


def _obs(tool_name="Bash", command_family="test", command_signature="pytest",
         outcome="success", write_kind=None, file_basename=None,
         path_pattern=None, session_id="s1", timestamp="2026-03-20T10:00:00Z"):
    return {
        "tool_name": tool_name,
        "command_family": command_family,
        "command_signature": command_signature,
        "outcome": outcome,
        "write_kind": write_kind,
        "file_basename": file_basename,
        "path_pattern": path_pattern,
        "session_id": session_id,
        "timestamp": timestamp,
    }


def _rule(pattern_kind="test_command", action="Use pytest for running tests",
          rule_id="rule-1", applied_at="2026-03-15T00:00:00Z"):
    return {
        "id": rule_id,
        "type": "convention",
        "pattern_kind": pattern_kind,
        "action": action,
        "scope": "project",
        "status": "applied",
        "applied": applied_at,
        "target_tool": None,
        "trigger_class": None,
    }


# --- test_command adherence ---

def test_test_command_full_adherence():
    """All test runs use the convention command → 100% adherence."""
    rule = _rule(pattern_kind="test_command", action="Use pytest for running tests")
    obs = [_obs(command_signature="pytest", session_id=f"s{i}",
                timestamp=f"2026-03-{20+i:02d}T10:00:00Z")
           for i in range(25)]
    rec = measure_convention_adherence(rule, obs, after_days=7)
    assert rec.adherence_rate == 100.0
    assert rec.verdict == "effective"


def test_test_command_partial_adherence():
    """Mixed test commands → partial adherence."""
    rule = _rule(pattern_kind="test_command", action="Use pytest for running tests")
    obs = []
    for i in range(20):
        sig = "pytest" if i < 16 else "jest"
        obs.append(_obs(command_signature=sig, session_id=f"s{i%5}",
                        timestamp=f"2026-03-{20+(i%10):02d}T10:00:00Z"))
    rec = measure_convention_adherence(rule, obs, after_days=7)
    assert rec.adherence_rate == 80.0  # 16/20


def test_test_command_ignores_non_test():
    """Only command_family=test counts for test_command adherence."""
    rule = _rule(pattern_kind="test_command", action="Use pytest for running tests")
    obs = [
        _obs(command_family="test", command_signature="pytest"),
        _obs(command_family="test", command_signature="pytest"),
        _obs(command_family="shell", command_signature=None),  # not relevant
    ]
    rec = measure_convention_adherence(rule, obs, after_days=7)
    # Only 2 relevant obs, below min threshold → pending
    assert rec.verdict == "pending"


# --- file_naming adherence ---

def test_file_naming_adherence():
    """All new .py files use snake_case → 100% adherence."""
    rule = _rule(pattern_kind="file_naming", action="New Python files use snake_case naming")
    obs = []
    for i in range(25):
        obs.append(_obs(tool_name="Write", write_kind="create",
                        file_basename=f"module_{i}.py",
                        command_family=None, command_signature=None,
                        session_id=f"s{i%5}",
                        timestamp=f"2026-03-{20+(i%10):02d}T10:00:00Z"))
    rec = measure_convention_adherence(rule, obs, after_days=7)
    assert rec.adherence_rate == 100.0


def test_file_naming_partial():
    """Some camelCase files → less than 100%."""
    rule = _rule(pattern_kind="file_naming", action="New Python files use snake_case naming")
    obs = []
    for i in range(20):
        name = f"good_name_{i}.py" if i < 15 else f"badName{i}.py"
        obs.append(_obs(tool_name="Write", write_kind="create",
                        file_basename=name,
                        command_family=None, command_signature=None,
                        session_id=f"s{i%5}",
                        timestamp=f"2026-03-{20+(i%10):02d}T10:00:00Z"))
    rec = measure_convention_adherence(rule, obs, after_days=7)
    assert rec.adherence_rate == 75.0  # 15/20


def test_file_naming_ignores_edits():
    """Only write_kind=create counts for file_naming."""
    rule = _rule(pattern_kind="file_naming", action="New Python files use snake_case naming")
    obs = []
    for i in range(25):
        obs.append(_obs(tool_name="Write", write_kind="create",
                        file_basename=f"good_{i}.py",
                        command_family=None, command_signature=None,
                        session_id=f"s{i%5}",
                        timestamp=f"2026-03-{20+(i%10):02d}T10:00:00Z"))
    # Add edits with bad names — should not count
    for i in range(10):
        obs.append(_obs(tool_name="Write", write_kind="edit",
                        file_basename=f"badEdit{i}.py",
                        command_family=None, command_signature=None,
                        session_id=f"s{i%5}",
                        timestamp=f"2026-03-{20+(i%10):02d}T10:00:00Z"))
    rec = measure_convention_adherence(rule, obs, after_days=7)
    assert rec.adherence_rate == 100.0


# --- test_placement adherence ---

def test_test_placement_adherence():
    """All test files in correct pattern → 100%."""
    rule = _rule(pattern_kind="test_placement",
                 action="Test files go in tests_root directory pattern")
    obs = []
    for i in range(25):
        obs.append(_obs(tool_name="Write", write_kind="create",
                        file_basename=f"test_mod_{i}.py",
                        path_pattern="tests_root",
                        command_family=None, command_signature=None,
                        session_id=f"s{i%5}",
                        timestamp=f"2026-03-{20+(i%10):02d}T10:00:00Z"))
    rec = measure_convention_adherence(rule, obs, after_days=7)
    assert rec.adherence_rate == 100.0


def test_test_placement_partial():
    """Some test files in wrong location → partial adherence."""
    rule = _rule(pattern_kind="test_placement",
                 action="Test files go in tests_root directory pattern")
    obs = []
    for i in range(20):
        pp = "tests_root" if i < 16 else "colocated"
        obs.append(_obs(tool_name="Write", write_kind="create",
                        file_basename=f"test_mod_{i}.py",
                        path_pattern=pp,
                        command_family=None, command_signature=None,
                        session_id=f"s{i%5}",
                        timestamp=f"2026-03-{20+(i%10):02d}T10:00:00Z"))
    rec = measure_convention_adherence(rule, obs, after_days=7)
    assert rec.adherence_rate == 80.0


# --- Pending: insufficient data ---

def test_pending_insufficient_observations():
    """< 20 relevant operations → pending."""
    rule = _rule(pattern_kind="test_command")
    obs = [_obs(command_signature="pytest", session_id=f"s{i}")
           for i in range(15)]
    rec = measure_convention_adherence(rule, obs, after_days=7)
    assert rec.verdict == "pending"


def test_pending_insufficient_time():
    """< 7 days after → pending."""
    rule = _rule(pattern_kind="test_command")
    obs = [_obs(command_signature="pytest", session_id=f"s{i}",
                timestamp=f"2026-03-{20+i:02d}T10:00:00Z")
           for i in range(25)]
    rec = measure_convention_adherence(rule, obs, after_days=5)
    assert rec.verdict == "pending"


# --- Verdict logic ---

def test_effective_above_80():
    """Adherence ≥ 80% → effective."""
    rule = _rule(pattern_kind="test_command")
    obs = [_obs(command_signature="pytest") for _ in range(20)]
    rec = measure_convention_adherence(rule, obs, after_days=7)
    assert rec.verdict == "effective"


def test_neutral_between_50_and_80():
    """Adherence 50-80% → neutral."""
    rule = _rule(pattern_kind="test_command")
    obs = []
    for i in range(20):
        sig = "pytest" if i < 12 else "jest"  # 60%
        obs.append(_obs(command_signature=sig))
    rec = measure_convention_adherence(rule, obs, after_days=7)
    assert rec.verdict == "neutral"


def test_harmful_below_50():
    """Adherence < 50% → harmful (convention not being followed)."""
    rule = _rule(pattern_kind="test_command")
    obs = []
    for i in range(20):
        sig = "pytest" if i < 8 else "jest"  # 40%
        obs.append(_obs(command_signature=sig))
    rec = measure_convention_adherence(rule, obs, after_days=7)
    assert rec.verdict == "harmful"


# --- Record fields ---

def test_record_has_correct_rule_id():
    rule = _rule(rule_id="conv-42", applied_at="2026-03-10T00:00:00Z")
    obs = [_obs(command_signature="pytest") for _ in range(20)]
    rec = measure_convention_adherence(rule, obs, after_days=7)
    assert rec.rule_id == "conv-42"
    assert rec.applied_at == "2026-03-10T00:00:00Z"


def test_record_sessions_observed():
    rule = _rule(pattern_kind="test_command")
    obs = [_obs(command_signature="pytest", session_id=f"s{i%3}")
           for i in range(21)]
    rec = measure_convention_adherence(rule, obs, after_days=7)
    assert rec.sessions_observed == 3


def test_failure_rates_zero_for_conventions():
    """Convention records use adherence_rate, not target_pattern_before/after."""
    rule = _rule(pattern_kind="test_command")
    obs = [_obs(command_signature="pytest") for _ in range(20)]
    rec = measure_convention_adherence(rule, obs, after_days=7)
    assert rec.target_pattern_before == 0.0
    assert rec.target_pattern_after == 0.0
    assert rec.adherence_rate is not None

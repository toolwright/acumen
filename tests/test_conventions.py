"""Tests for convention extraction in lib/cluster.py."""

from lib.cluster import ConventionCandidate, extract_conventions


def _ok_bash(command_signature="pytest", session_id="s1", day="28"):
    """Successful Bash test call."""
    return {
        "tool_name": "Bash",
        "outcome": "success",
        "command_family": "test",
        "command_signature": command_signature,
        "session_id": session_id,
        "timestamp": f"2026-03-{day}T10:00:00Z",
    }


def _ok_write(file_basename="foo.py", path_pattern="src_dir",
              write_kind="create", session_id="s1", day="28"):
    """Successful Write call."""
    return {
        "tool_name": "Write",
        "outcome": "success",
        "write_kind": write_kind,
        "file_basename": file_basename,
        "path_pattern": path_pattern,
        "session_id": session_id,
        "timestamp": f"2026-03-{day}T10:00:00Z",
    }


# --- Empty / insufficient data ---

def test_empty_observations():
    assert extract_conventions([]) == []


def test_insufficient_observations():
    """Below min_obs → no convention proposed."""
    obs = [_ok_bash(session_id="s1", day="28")]
    assert extract_conventions(obs) == []


# --- test_command convention ---

def test_test_command_clear_winner():
    """≥80% use same command_signature across 3+ sessions, 2+ days → propose."""
    obs = []
    for sid, day in [("s1", "28"), ("s2", "29"), ("s3", "30")]:
        obs.append(_ok_bash(command_signature="pytest", session_id=sid, day=day))
        obs.append(_ok_bash(command_signature="pytest", session_id=sid, day=day))
    # 6 pytest calls, 0 others → 100%
    candidates = extract_conventions(obs)
    tc = [c for c in candidates if c.pattern_kind == "test_command"]
    assert len(tc) == 1
    assert tc[0].dominant_value == "pytest"
    assert tc[0].consistency_pct >= 80.0
    assert tc[0].observation_count == 6
    assert tc[0].session_count == 3
    assert tc[0].day_count == 3


def test_test_command_runner_up_too_close():
    """Runner-up ≥20% → ambiguous, propose NOTHING."""
    obs = []
    for sid, day in [("s1", "28"), ("s2", "29"), ("s3", "30")]:
        # 3 pytest + 2 jest per session = 60% vs 40%
        obs.append(_ok_bash(command_signature="pytest", session_id=sid, day=day))
        obs.append(_ok_bash(command_signature="pytest", session_id=sid, day=day))
        obs.append(_ok_bash(command_signature="pytest", session_id=sid, day=day))
        obs.append(_ok_bash(command_signature="jest", session_id=sid, day=day))
        obs.append(_ok_bash(command_signature="jest", session_id=sid, day=day))
    candidates = extract_conventions(obs)
    tc = [c for c in candidates if c.pattern_kind == "test_command"]
    assert len(tc) == 0


def test_test_command_gap_exactly_15_pct():
    """Gap between top two < 15% → propose NOTHING (ambiguity rule)."""
    # 57% vs 43% → gap 14% < 15 → ambiguous
    obs = []
    for sid, day in [("s1", "28"), ("s2", "29"), ("s3", "30")]:
        for _ in range(4):
            obs.append(_ok_bash(command_signature="pytest", session_id=sid, day=day))
        for _ in range(3):
            obs.append(_ok_bash(command_signature="jest", session_id=sid, day=day))
    candidates = extract_conventions(obs)
    tc = [c for c in candidates if c.pattern_kind == "test_command"]
    assert len(tc) == 0


def test_test_command_needs_3_sessions():
    """Only 2 sessions → no proposal even with high consistency."""
    obs = []
    for sid, day in [("s1", "28"), ("s2", "29")]:
        for _ in range(5):
            obs.append(_ok_bash(command_signature="pytest", session_id=sid, day=day))
    candidates = extract_conventions(obs)
    tc = [c for c in candidates if c.pattern_kind == "test_command"]
    assert len(tc) == 0


def test_test_command_needs_2_days():
    """3 sessions but all on 1 day → no proposal."""
    obs = []
    for sid in ["s1", "s2", "s3"]:
        for _ in range(3):
            obs.append(_ok_bash(command_signature="pytest", session_id=sid, day="30"))
    candidates = extract_conventions(obs)
    tc = [c for c in candidates if c.pattern_kind == "test_command"]
    assert len(tc) == 0


def test_test_command_below_80_pct():
    """Winner at 78% → below 80% threshold → no proposal."""
    obs = []
    for sid, day in [("s1", "28"), ("s2", "29"), ("s3", "30")]:
        # 78% pytest: 7 pytest + 2 jest = ~78%
        for _ in range(7):
            obs.append(_ok_bash(command_signature="pytest", session_id=sid, day=day))
        for _ in range(2):
            obs.append(_ok_bash(command_signature="jest", session_id=sid, day=day))
    # Total: 21 pytest / 27 = 77.8%
    candidates = extract_conventions(obs)
    tc = [c for c in candidates if c.pattern_kind == "test_command"]
    assert len(tc) == 0


def test_test_command_ignores_errors():
    """Error observations should not count for convention extraction."""
    obs = []
    for sid, day in [("s1", "28"), ("s2", "29"), ("s3", "30")]:
        obs.append(_ok_bash(command_signature="pytest", session_id=sid, day=day))
        obs.append(_ok_bash(command_signature="pytest", session_id=sid, day=day))
        obs.append({
            "tool_name": "Bash",
            "outcome": "error",
            "command_family": "test",
            "command_signature": "jest",
            "session_id": sid,
            "timestamp": f"2026-03-{day}T10:00:00Z",
        })
    candidates = extract_conventions(obs)
    tc = [c for c in candidates if c.pattern_kind == "test_command"]
    assert len(tc) == 1
    assert tc[0].dominant_value == "pytest"


def test_test_command_ignores_non_test_family():
    """Bash calls without command_family=test are ignored."""
    obs = []
    for sid, day in [("s1", "28"), ("s2", "29"), ("s3", "30")]:
        obs.append(_ok_bash(command_signature="pytest", session_id=sid, day=day))
        obs.append(_ok_bash(command_signature="pytest", session_id=sid, day=day))
        obs.append({
            "tool_name": "Bash",
            "outcome": "success",
            "command_family": "shell",
            "command_signature": None,
            "session_id": sid,
            "timestamp": f"2026-03-{day}T10:00:00Z",
        })
    candidates = extract_conventions(obs)
    tc = [c for c in candidates if c.pattern_kind == "test_command"]
    assert len(tc) == 1


# --- file_naming convention ---

def test_file_naming_snake_case_dominant():
    """≥85% snake_case new .py files → propose."""
    obs = []
    for sid, day in [("s1", "28"), ("s2", "29"), ("s3", "30")]:
        # snake_case names
        obs.append(_ok_write(file_basename="my_module.py", session_id=sid, day=day))
        obs.append(_ok_write(file_basename="test_foo.py", session_id=sid, day=day))
        obs.append(_ok_write(file_basename="data_utils.py", session_id=sid, day=day))
        obs.append(_ok_write(file_basename="bar_baz.py", session_id=sid, day=day))
    # 12 snake_case / 12 = 100%
    candidates = extract_conventions(obs)
    fn = [c for c in candidates if c.pattern_kind == "file_naming"]
    assert len(fn) == 1
    assert fn[0].dominant_value == "snake_case"
    assert fn[0].consistency_pct >= 85.0


def test_file_naming_needs_10_observations():
    """file_naming min_obs=10 per guardrails table."""
    obs = []
    for sid, day in [("s1", "28"), ("s2", "29"), ("s3", "30")]:
        obs.append(_ok_write(file_basename="my_module.py", session_id=sid, day=day))
        obs.append(_ok_write(file_basename="test_foo.py", session_id=sid, day=day))
        obs.append(_ok_write(file_basename="data_utils.py", session_id=sid, day=day))
    # 9 observations < 10
    candidates = extract_conventions(obs)
    fn = [c for c in candidates if c.pattern_kind == "file_naming"]
    assert len(fn) == 0


def test_file_naming_below_85_pct():
    """Dominant style below 85% → no proposal."""
    obs = []
    for sid, day in [("s1", "28"), ("s2", "29"), ("s3", "30")]:
        # 3 snake + 1 camel per session = 75%
        obs.append(_ok_write(file_basename="my_module.py", session_id=sid, day=day))
        obs.append(_ok_write(file_basename="test_foo.py", session_id=sid, day=day))
        obs.append(_ok_write(file_basename="data_utils.py", session_id=sid, day=day))
        obs.append(_ok_write(file_basename="myModule.py", session_id=sid, day=day))
    # 9 snake / 12 = 75% < 85
    candidates = extract_conventions(obs)
    fn = [c for c in candidates if c.pattern_kind == "file_naming"]
    assert len(fn) == 0


def test_file_naming_only_create():
    """Only write_kind=create counts, not edits."""
    obs = []
    for sid, day in [("s1", "28"), ("s2", "29"), ("s3", "30")]:
        obs.append(_ok_write(file_basename="my_module.py", write_kind="create",
                             session_id=sid, day=day))
        obs.append(_ok_write(file_basename="test_foo.py", write_kind="create",
                             session_id=sid, day=day))
        obs.append(_ok_write(file_basename="data_utils.py", write_kind="create",
                             session_id=sid, day=day))
        obs.append(_ok_write(file_basename="bar_baz.py", write_kind="create",
                             session_id=sid, day=day))
        # Edits with camelCase should not count
        obs.append(_ok_write(file_basename="camelCase.py", write_kind="edit",
                             session_id=sid, day=day))
    candidates = extract_conventions(obs)
    fn = [c for c in candidates if c.pattern_kind == "file_naming"]
    assert len(fn) == 1
    assert fn[0].dominant_value == "snake_case"


def test_file_naming_only_py_files():
    """Only .py files analyzed for naming style."""
    obs = []
    for sid, day in [("s1", "28"), ("s2", "29"), ("s3", "30")]:
        obs.append(_ok_write(file_basename="my_module.py", session_id=sid, day=day))
        obs.append(_ok_write(file_basename="test_foo.py", session_id=sid, day=day))
        obs.append(_ok_write(file_basename="data_utils.py", session_id=sid, day=day))
        obs.append(_ok_write(file_basename="utils.py", session_id=sid, day=day))
        # Non-py files should not matter
        obs.append(_ok_write(file_basename="MyComponent.tsx", session_id=sid, day=day))
        obs.append(_ok_write(file_basename="myConfig.json", session_id=sid, day=day))
    candidates = extract_conventions(obs)
    fn = [c for c in candidates if c.pattern_kind == "file_naming"]
    assert len(fn) == 1
    assert fn[0].dominant_value == "snake_case"


def test_file_naming_ambiguity_rule():
    """Gap between top two naming styles < 15% → propose NOTHING."""
    obs = []
    for sid, day in [("s1", "28"), ("s2", "29"), ("s3", "30")]:
        # Equal split: 2 snake + 2 camel per session
        obs.append(_ok_write(file_basename="my_module.py", session_id=sid, day=day))
        obs.append(_ok_write(file_basename="test_foo.py", session_id=sid, day=day))
        obs.append(_ok_write(file_basename="myModule.py", session_id=sid, day=day))
        obs.append(_ok_write(file_basename="testFoo.py", session_id=sid, day=day))
    candidates = extract_conventions(obs)
    fn = [c for c in candidates if c.pattern_kind == "file_naming"]
    assert len(fn) == 0


# --- test_placement convention ---

def test_test_placement_clear_dominant():
    """≥80% of test files in same path_pattern across 3+ sessions → propose."""
    obs = []
    for sid, day in [("s1", "28"), ("s2", "29"), ("s3", "30")]:
        obs.append(_ok_write(file_basename="test_store.py",
                             path_pattern="tests_root", session_id=sid, day=day))
        obs.append(_ok_write(file_basename="test_cluster.py",
                             path_pattern="tests_root", session_id=sid, day=day))
    # 6 test files in tests_root → 100%
    candidates = extract_conventions(obs)
    tp = [c for c in candidates if c.pattern_kind == "test_placement"]
    assert len(tp) == 1
    assert tp[0].dominant_value == "tests_root"
    assert tp[0].consistency_pct >= 80.0


def test_test_placement_needs_6_observations():
    """test_placement min_obs=6 per guardrails table."""
    obs = []
    for sid, day in [("s1", "28"), ("s2", "29"), ("s3", "30")]:
        obs.append(_ok_write(file_basename="test_store.py",
                             path_pattern="tests_root", session_id=sid, day=day))
    # 3 obs < 6
    candidates = extract_conventions(obs)
    tp = [c for c in candidates if c.pattern_kind == "test_placement"]
    assert len(tp) == 0


def test_test_placement_ambiguous():
    """Gap between top two < 15% → propose NOTHING."""
    obs = []
    for sid, day in [("s1", "28"), ("s2", "29"), ("s3", "30")]:
        obs.append(_ok_write(file_basename="test_store.py",
                             path_pattern="tests_root", session_id=sid, day=day))
        obs.append(_ok_write(file_basename="test_foo.py",
                             path_pattern="colocated", session_id=sid, day=day))
    # 50% vs 50% → gap 0 < 15 → ambiguous
    candidates = extract_conventions(obs)
    tp = [c for c in candidates if c.pattern_kind == "test_placement"]
    assert len(tp) == 0


def test_test_placement_matches_test_prefix_and_suffix():
    """Both test_ prefix and _test suffix count as test files."""
    obs = []
    for sid, day in [("s1", "28"), ("s2", "29"), ("s3", "30")]:
        obs.append(_ok_write(file_basename="test_store.py",
                             path_pattern="tests_root", session_id=sid, day=day))
        obs.append(_ok_write(file_basename="store_test.py",
                             path_pattern="tests_root", session_id=sid, day=day))
    candidates = extract_conventions(obs)
    tp = [c for c in candidates if c.pattern_kind == "test_placement"]
    assert len(tp) == 1
    assert tp[0].observation_count == 6


def test_test_placement_ignores_non_test_files():
    """Non-test Write calls don't factor into test placement."""
    obs = []
    for sid, day in [("s1", "28"), ("s2", "29"), ("s3", "30")]:
        obs.append(_ok_write(file_basename="test_store.py",
                             path_pattern="tests_root", session_id=sid, day=day))
        obs.append(_ok_write(file_basename="test_cluster.py",
                             path_pattern="tests_root", session_id=sid, day=day))
        # Non-test file in different location
        obs.append(_ok_write(file_basename="utils.py",
                             path_pattern="src_dir", session_id=sid, day=day))
    candidates = extract_conventions(obs)
    tp = [c for c in candidates if c.pattern_kind == "test_placement"]
    assert len(tp) == 1
    assert tp[0].observation_count == 6  # only test files counted


# --- Multiple conventions at once ---

def test_multiple_conventions_can_coexist():
    """Can get test_command + file_naming + test_placement all at once."""
    obs = []
    for sid, day in [("s1", "28"), ("s2", "29"), ("s3", "30")]:
        # test_command: 4 pytest calls
        for _ in range(4):
            obs.append(_ok_bash(command_signature="pytest", session_id=sid, day=day))
        # file_naming: 4 snake_case .py files created
        for name in ["foo_bar.py", "baz_qux.py", "data_util.py", "config_reader.py"]:
            obs.append(_ok_write(file_basename=name, session_id=sid, day=day))
        # test_placement: 3 test files in tests_root
        for name in ["test_foo.py", "test_bar.py", "test_baz.py"]:
            obs.append(_ok_write(file_basename=name, path_pattern="tests_root",
                                 session_id=sid, day=day))
    candidates = extract_conventions(obs)
    kinds = {c.pattern_kind for c in candidates}
    assert "test_command" in kinds
    assert "file_naming" in kinds
    assert "test_placement" in kinds


def test_no_none_command_signature():
    """Observations with command_signature=None are ignored for test_command."""
    obs = []
    for sid, day in [("s1", "28"), ("s2", "29"), ("s3", "30")]:
        obs.append(_ok_bash(command_signature="pytest", session_id=sid, day=day))
        obs.append(_ok_bash(command_signature="pytest", session_id=sid, day=day))
        obs.append({
            "tool_name": "Bash",
            "outcome": "success",
            "command_family": "test",
            "command_signature": None,
            "session_id": sid,
            "timestamp": f"2026-03-{day}T10:00:00Z",
        })
    candidates = extract_conventions(obs)
    tc = [c for c in candidates if c.pattern_kind == "test_command"]
    assert len(tc) == 1
    assert tc[0].observation_count == 6  # only non-None signatures


def test_candidate_dataclass_fields():
    """ConventionCandidate has all expected fields."""
    obs = []
    for sid, day in [("s1", "28"), ("s2", "29"), ("s3", "30")]:
        obs.append(_ok_bash(command_signature="pytest", session_id=sid, day=day))
        obs.append(_ok_bash(command_signature="pytest", session_id=sid, day=day))
    candidates = extract_conventions(obs)
    c = candidates[0]
    assert hasattr(c, "pattern_kind")
    assert hasattr(c, "dominant_value")
    assert hasattr(c, "consistency_pct")
    assert hasattr(c, "observation_count")
    assert hasattr(c, "session_count")
    assert hasattr(c, "day_count")

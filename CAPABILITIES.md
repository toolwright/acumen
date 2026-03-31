# Acumen Capability Registry

Canonical map of what Acumen can do today. No roadmap items. Every entry has file paths and entry points.

**Spec:** [spec-v2.1.md](spec-v2.1.md) — the implementation contract this registry tracks against.

---

## Observation Layer

### CAP-OBS-001: Tier 0.5 Tool Call Observation

**What:** Classifies every Claude Code tool call into categorical metadata and persists only derived fields. Raw commands, file contents, and error messages are read transiently to classify, then discarded.
**Files:** `hooks/observe.sh`, `lib/classify.py`
**Entry point:** Shell hook fired on PostToolUse / PostToolUseFailure → pipes to `python3 lib/classify.py`
**Fields persisted:** tool_name, outcome, error_type, command_family, command_signature, file_basename, path_pattern, write_kind, environment_tag, burst_count, error_class, session_id, timestamp
**Fields NOT persisted:** Raw commands, raw file paths, raw error messages, tool input/output, file contents, conversation text
**Storage:** `.acumen/observations/<session_id>.jsonl` (per-session, append-only)
**Performance:** ~52ms per observation
**Spec ref:** Section 4.1 (Tier 0.5)

### CAP-OBS-002: Tier 0.5 Field Classification

**What:** Derives categorical fields from raw hook data.
**Files:** `lib/classify.py`
**Functions:**
- `classify_command_family(tool_name, command)` → "python" | "node" | "git" | "test" | etc.
- `classify_command_signature(tool_name, command)` → "pytest" | "uv_pytest" | "npm_test" | etc.
- `classify_file_basename(tool_name, file_path)` → basename only
- `classify_path_pattern(tool_name, file_path)` → "tests_root" | "src_dir" | etc.
- `classify_write_kind(tool_name, file_path)` → "create" | "edit"
- `classify_environment_tag(project_root)` → "python" | "node" | "rust" | "go"
- `classify_error_class(error_type, error_message)` → "command_not_found" | "file_not_found" | etc.
**Tests:** `tests/test_classify.py` (56 tests)
**Spec ref:** Section 4.1 derivation rules

### CAP-OBS-003: Burst Count Tracking

**What:** Counts consecutive calls to the same tool within a session (< 60s gap). Detects retry patterns.
**Files:** `lib/classify.py` (__main__ block), `lib/store.py` (`read_last_observation`)
**Entry point:** Computed during observation by reading last event in session file
**Spec ref:** Section 4.1

### CAP-OBS-004: Auto-Reflection Trigger

**What:** Counts observations since last reflection. When threshold exceeded, flags for reflection at next session start.
**Files:** `hooks/session-end.sh`, `hooks/session-start.sh`
**Entry point:** SessionEnd hook (count + flag), SessionStart hook (consume flag + inject context)
**Threshold:** Default 10, configurable via `ACUMEN_REFLECT_THRESHOLD` env var
**Flag file:** `.acumen/should-reflect`

---

## Storage Layer

### CAP-STORE-001: Per-Session Observation Storage

**What:** Append-only JSONL files, one per session. Eliminates concurrent write conflicts.
**Files:** `lib/store.py` — `append_observation()`, `read_observations()`
**Storage:** `.acumen/observations/<session_id>.jsonl`
**Index:** `.acumen/observations/index.json` — maps session_ids to paths/timestamps, updated via atomic rename + fcntl.flock()
**Corruption recovery:** Skips bad JSONL lines, counts errors, returns `(observations, error_count)` tuple. Error count surfaced in `/acumen-status`.
**Tests:** `tests/test_store.py` (32 tests)
**Spec ref:** Section 6.1

### CAP-STORE-002: Observation Rotation

**What:** Archives session files older than 30 days to `.acumen/observations/archive/`.
**Files:** `lib/store.py` — `rotate_observations()`
**Entry point:** Called during maintenance operations
**Spec ref:** Section 6.1

### CAP-STORE-003: Rule Storage

**What:** JSON array of AcumenRule objects with atomic read/write.
**Files:** `lib/apply.py` — `read_rules()`, `save_rules()`
**Storage:** `.acumen/rules.json`
**Safety:** Atomic write via tempfile + rename. Graceful fallback on missing/corrupt files.
**Tests:** `tests/test_apply.py` (14 tests)
**Spec ref:** Section 6.2

---

## Learning Layer

### CAP-LEARN-001: Failure Clustering

**What:** Groups error observations by (tool_name, error_class), counts evidence across sessions and days, applies quality guardrails, drops clusters that don't pass.
**Files:** `lib/cluster.py` — `cluster_failures()`, `FailureCluster` dataclass
**Guardrails:** ≥5 observations, ≥3 sessions, ≥2 days
**Special case:** `command_not_found` + all `command_family="python"` → `pattern_kind="python_launcher"`
**Tests:** `tests/test_cluster.py` (11 tests)
**Spec ref:** Section 7.1 step 2, Section 5.2 guardrails table

### CAP-LEARN-002: Proposal Generation

**What:** Converts FailureClusters into structured AcumenRule proposals with evidence, confidence scoring, and quality guardrails.
**Files:** `lib/propose.py` — `generate_proposals()`, `AcumenRule` dataclass
**Confidence formula:** `min(obs/20, 1.0) * 0.5 + min(sessions/10, 1.0) * 0.3 + min(days/7, 1.0) * 0.2`
**Min confidence:** 0.4 (below = discarded)
**Max pending:** 5 proposals at a time
**Action text:** Dict-based template lookup for all 6 failure pattern_kinds + unknown fallback
**Tests:** `tests/test_propose.py` (18 tests)
**Spec ref:** Section 7.1 steps 4-6, Section 5.1

### CAP-LEARN-003: Contradiction Detection

**What:** Before adding a proposal, checks existing rules for conflicts. Same pattern_kind + same scope + different action + status in (proposed, approved, applied) → conflict blocked.
**Files:** `lib/propose.py` — `_has_contradiction()`
**Deterministic:** No LLM needed. Structured field comparison only.
**Tests:** 3 tests in `tests/test_propose.py`
**Spec ref:** Section 5.1 contradiction detection

---

## Improvement Layer

### CAP-IMP-001: Rule Application

**What:** Writes approved rules as `.claude/rules/acumen-<id>.md` files. Updates status to "applied" with timestamp.
**Files:** `lib/apply.py` — `apply_rule()`
**Rule format:** `# Acumen rule\n\n<action>\n\nObserved: <pattern> (<evidence>)`
**Safety:** Atomic write (tempfile + rename). Only writes to `acumen-*` namespaced files. Never modifies CLAUDE.md.
**Tests:** `tests/test_apply.py`
**Spec ref:** Section 5.3

### CAP-IMP-002: Rule Rejection

**What:** Marks a proposal as "rejected" with decided timestamp.
**Files:** `lib/apply.py` — `reject_rule()`
**Tests:** `tests/test_apply.py`

### CAP-IMP-003: Rule Revert

**What:** Deletes the `.claude/rules/acumen-<id>.md` file and marks status "reverted". Returns False if file already missing.
**Files:** `lib/apply.py` — `revert_rule()`
**Tests:** `tests/test_apply.py`
**Spec ref:** Section 5.3

### CAP-IMP-004: Proposal Review UI

**What:** Slash command showing pending proposals with evidence. User approves/rejects each. Applied rules are also revertible.
**Files:** `commands/review.md`
**Entry point:** `/acumen-review`
**Flow:** Read pending → display with evidence → approve/reject → summary
**Spec ref:** Section 5.3

---

## Measurement Layer

### CAP-MEAS-001: Failure Recurrence Tracking

**What:** After a rule is applied, measures whether the targeted failure class actually decreases. Computes error rate per 100 relevant events (scoped by command_family, fallback to tool_name). Requires minimum 50 events in each window and 7 days in after window before issuing verdict.
**Files:** `lib/measure.py` — `measure_effectiveness()`, `EffectivenessRecord` dataclass
**Verdicts:** "effective" (>50% reduction), "harmful" (>10% increase), "neutral" (otherwise), "pending" (insufficient data)
**Retention tracking:** `retained_at_2_weeks` set True when rule survives 14+ days
**Storage:** `.acumen/effectiveness.json` — atomic read/write
**Tests:** `tests/test_measure.py` (15 tests)
**Spec ref:** Section 8.1

---

## Display Layer

### CAP-DISP-001: Status Dashboard

**What:** Quick health check showing: session count, event count, observation tier, active rules with pattern_kinds, pending proposals, effectiveness verdicts, data quality warnings (corruption count).
**Files:** `commands/status.md`
**Entry point:** `/acumen-status`
**Data sources:** `observations/index.json`, `rules.json` (via `lib/apply.read_rules`), `effectiveness.json` (via `lib/measure.read_effectiveness`), observation corruption count from `lib/store.read_observations`

### CAP-DISP-002: Report

**What:** Detailed report: failure reduction with explicit denominators, convention adherence, improvement history.
**Files:** `commands/report.md`
**Entry point:** `/acumen-report`
**Status:** Planned for Phase 1B
**Spec ref:** Section 8.2

---

## Legacy Capabilities (v0.3, pending cleanup)

The following capabilities exist from the v0.3 codebase. They will be evaluated during Phase 1A Step 10 for integration into or replacement by the v2.1 pipeline.

### CAP-LEGACY-001: v0.3 Insight Pipeline
**Files:** `lib/scorer.py`, `lib/improver.py`, `lib/formatter.py`, `lib/evaluator.py`
**Status:** Functional but superseded by the v2.1 pipeline (classify → cluster → propose → apply). Will be cleaned up once the v2.1 pipeline is fully wired.

### CAP-LEGACY-002: Stop Gate
**Files:** `hooks/stop-gate.sh`
**Status:** Functional. May be retained as a complementary feature alongside the v2.1 pipeline.

### CAP-LEGACY-003: InstructionsLoaded / StopFailure Hooks
**Files:** `hooks/instructions-loaded.sh`, `hooks/stop-failure.sh`
**Status:** Functional. Provide attribution data. Evaluate for retention.

---

## Known Bugs

### ~~BUG-001: write_kind hardcoded in classify pipeline~~ FIXED
**Fixed in:** Phase 1A Step 10. `classify_write_kind(tool_name, file_path)` now called correctly.

### ~~BUG-002: Corruption skip counter not tracked~~ FIXED
**Fixed in:** Phase 1A Step 9. `read_observations()` now returns `(observations, error_count)`. Count surfaced in `/acumen-status`.

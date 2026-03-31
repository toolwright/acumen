# Acumen: Turn Your Generalist AI Into a Specialist

## Implementation Contract v2.1

**Date:** 2026-03-30
**Status:** Final draft — ready to build from
**Supersedes:** spec.md (v0.1), spec-v2.md (v2.0)

---

## 1. What Acumen Is

Acumen observes how you work and turns your generalist AI into a specialist in your project.

Every AI agent today is stuck at Day 1. Every session starts from zero. The model gets smarter once a quarter when the provider ships an update, but it never learns YOUR project, YOUR conventions, YOUR workflow.

Acumen changes that. Install it, work normally, and your agent goes through the same learning curve a new hire would — but in days, not months. After two weeks, your agent knows your repo's test runner, file naming conventions, and test placement patterns. It stops making the same mistakes. It starts feeling like it knows your codebase.

**The aha moment:** "I installed Acumen, worked normally for a week, and now my agent uses our test command, puts files in the right place, and follows our repo's patterns without me reminding it."

**What Acumen is NOT:**
- Not a fine-tuning system. Works with frozen API-only models through scaffold improvement.
- Not an observability platform. Braintrust observes. Acumen improves.
- Not a memory layer. Mem0 remembers. Acumen learns and applies.

**The gap nobody fills:** The market has observability, memory, and evaluation as separate products. Nobody closes the loop: observe → learn → propose → approve → apply → measure. That loop is what makes agents actually get better. That is what Acumen does.

---

## 2. Vision: Domain-Agnostic Engine, Coding-First Execution

The observe → learn → propose → approve → apply loop is domain-agnostic. Any system that generates actions with outcomes can benefit:

```
CODING AGENT:    Bash "python foo.py" → command_not_found → learn "use python3"
ROBOT ARM:       pick_up(angle=0°)    → grip_failure      → learn "approach at 15°"
RESEARCH AGENT:  search(query)        → zero_results       → learn "use domain terms"
WRITING AGENT:   draft(style=formal)  → user_rejection     → learn "user prefers casual"
```

The abstraction is identical. An ObservationEvent with a tool, an outcome, and contextual metadata. A proposed rule with evidence and a rollback path. An approval flow. An effectiveness measurement.

**Phase 1 builds for coding.** The abstractions are domain-agnostic so that robotics, research, and general-purpose adapters are natural extensions — not rewrites.

**Requirements from any host system:**
1. Observable actions (hooks/events for tool/action calls)
2. Outcomes (success/failure signals)
3. Metadata (what was attempted, at minimum categorically)

Claude Code has all three. Codex has all three. A ROS-based robot has all three. A browser-based agent has all three.

---

## 3. Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         ACUMEN ENGINE                                 │
│                                                                       │
│  OBSERVATION (Tier 0.5 default — privacy-safe operational metadata)   │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ tool_name         │ outcome        │ error_type                  │ │
│  │ command_family     │ file_basename  │ environment_tag             │ │
│  │ burst_count        │ error_class    │ session_id, timestamp       │ │
│  │                                                                  │ │
│  │ ALL LOCAL. Nothing leaves the machine. No raw commands.          │ │
│  │ No file contents. No conversation text. No code.                 │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                             │                                         │
│  THE LOOP                                                             │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │  OBSERVE ──> LEARN ──> PROPOSE ──> [APPROVE] ──> APPLY          │ │
│  │     │                                               │            │ │
│  │     └──────────── MEASURE EFFECTIVENESS <───────────┘            │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  PHASE 1 RULE TYPES                                                  │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ FAILURE RULES:     "Stop doing X because it fails"               │ │
│  │ CONVENTION RULES:  "This project always does Y"                  │ │
│  │   (3 categories: test_command, file_naming, test_placement)      │ │
│  └──────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 4. Observation Model

### 4.1 Tier 0.5 (DEFAULT)

The default observation tier. Captures enough to generate failure rules and operational convention rules while remaining privacy-safe.

```python
@dataclass
class ObservationEvent:
    # Core (always captured)
    tool_name: str                    # "Bash", "Edit", "Write", "Read", etc.
    session_id: str                   # UUID from agent host
    timestamp: str                    # ISO 8601
    outcome: str                      # "success" | "error"
    error_type: str | None            # "tool_failure" | "tool_error" | None

    # Tier 0.5 enrichments (derived, not raw)
    command_family: str | None        # "python" | "node" | "git" | "test" |
                                      # "shell" | "build" | "lint" | "format" |
                                      # "docker" | None
    command_signature: str | None     # For test/build commands: "pytest" |
                                      # "uv_pytest" | "npm_test" | "cargo_test" |
                                      # "jest" | "go_test" | "ruff_check" | None
                                      # Derived from raw command, raw discarded.
    file_basename: str | None         # "foo.py", "test_bar.py" (no directory)
    path_pattern: str | None          # "tests_root" | "tests_mirror" |
                                      # "colocated" | "integration_dir" |
                                      # "src_dir" | "lib_dir" | None
                                      # Derived from full path, full path discarded.
    write_kind: str | None            # "create" | "edit" | None
                                      # Distinguishes new files from edits.
    environment_tag: str | None       # "python" | "node" | "rust" | "go" | None
    burst_count: int                  # 1 = single call, 3+ = retry burst
    error_class: str | None           # normalized: "command_not_found" |
                                      # "file_not_found" | "permission_denied" |
                                      # "syntax_error" | "timeout" |
                                      # "test_failure" | None
```

**What Tier 0.5 captures:** Categories, not content. `command_family: "python"` not `command: "python3 -m pytest tests/ -v"`. `file_basename: "test_store.py"` not `file_path: "/Users/tom/secret-project/tests/test_store.py"`.

**What Tier 0.5 does NOT capture:**
- Raw commands or arguments
- File contents or diffs
- Full file paths (only basenames)
- Conversation text
- Tool input or response content
- Error message text (only classified error_class)

**Derivation rules for Tier 0.5 fields:**

```
command_family:
  Extract from tool_name + minimal parsing of the hook event.
  Claude Code hooks expose tool_name and basic metadata.
  Map: "Bash" calls starting with python/python3 → "python"
       "Bash" calls starting with npm/npx/node → "node"
       "Bash" calls starting with git → "git"
       "Bash" calls starting with pytest/jest/cargo test → "test"
       etc.
  The hook sees the command string to classify it,
  but stores ONLY the family tag, not the command.

command_signature:
  For test/build/lint commands, derive a more specific tag:
  Map: "python -m pytest ..." or "pytest ..." → "pytest"
       "uv run pytest ..." → "uv_pytest"
       "npm test" or "npx jest" → "npm_test" / "jest"
       "cargo test" → "cargo_test"
       "go test" → "go_test"
       "ruff check" → "ruff_check"
       "ruff format" → "ruff_format"
  The hook reads the raw command to classify, stores ONLY the signature.
  Only populated when command_family is "test", "lint", "format", or "build".

file_basename:
  For Write/Edit/Read tools, extract os.path.basename() from the path.
  Store only the basename. Discard the full path.

path_pattern:
  For Write/Edit tools, derive directory classification from full path:
  Map: "/.../<project>/tests/..." → "tests_root"
       "/.../<project>/tests/unit/..." → "tests_root"
       "/.../<project>/tests/<mirror_of_src>/..." → "tests_mirror"
       test file next to source file (same dir) → "colocated"
       "/.../<project>/integration/..." → "integration_dir"
       "/.../<project>/src/..." → "src_dir"
       "/.../<project>/lib/..." → "lib_dir"
  Detection: split path, identify project root from .git or
  pyproject.toml, classify relative directory. Store ONLY the pattern.

write_kind:
  For Write tool: if the file existed before the call → "edit"
  If the file did not exist → "create"
  For Edit tool: always "edit"
  Detection: the hook checks file existence before the write
  (or Claude Code's hook metadata may indicate this).
  If unknown: None.

environment_tag:
  Detected once per session from project files.
  Check for pyproject.toml/setup.py → "python"
  Check for package.json → "node"
  Check for Cargo.toml → "rust"
  Check for go.mod → "go"

burst_count:
  Count consecutive calls to the same tool_name within
  the same session with < 60s gap. Reset on tool change.

error_class:
  Normalize from error_type + minimal error message parsing.
  The hook reads the error message to classify it,
  but stores ONLY the class tag, not the message text.
```

**Privacy invariant:** The observation hook reads raw data (commands, paths, error messages) to DERIVE categorical fields, then DISCARDS the raw data. Only derived fields are persisted. This is analogous to how a server logs HTTP status codes without logging request bodies.

### 4.2 Tier 1 (OPT-IN)

Available when user runs `acumen config set observation-tier 1`.

Adds to Tier 0.5:
```python
    # Tier 1 additions (redacted, ephemeral)
    error_message: str | None         # Aggressively redacted, max 200 chars
    file_paths: list[str] | None      # Full paths (redacted if sensitive)
    command_summary: str | None        # First 100 chars, redacted
```

**Retention:** Tier 1 fields are EPHEMERAL. Deleted from observation files after reflection completes. Hard maximum retention: 24 hours.

**Redaction rules:**
- Base64-like strings (20+ chars matching `[A-Za-z0-9+/=]`) → `[REDACTED]`
- Common secret patterns (sk-, token=, password=, API_KEY, etc.) → `[REDACTED]`
- Email patterns → `[REDACTED]`
- Paths containing "secret", "credential", "token", ".env" → `[REDACTED]`

### 4.3 Tier Upgrade Prompting

After the first reflection on Tier 0.5, if proposal confidence is low (< 0.3 average), include in `/acumen-report`:

```
Acumen found 3 likely improvement areas, but confidence is limited.
Enable trace analysis for stronger fixes? (All analysis stays local.)

  acumen config set observation-tier 1
```

### 4.4 Security: Observation Text as Hostile Input

**CRITICAL RULE:** All observation-derived text is untrusted input. When passed to the reflection LLM:
- Observation fields are wrapped in structured data blocks, never interpolated into instruction text
- Tool names and error classes are validated against known enumerations
- Any field exceeding expected length is truncated
- No observation field is ever used to construct a shell command, file path, or code snippet

---

## 5. Rule Model

### 5.1 Structured Rule Format

Rules are structured tuples, not free-form prose. This makes contradiction detection deterministic.

```python
@dataclass
class AcumenRule:
    id: str                           # UUID
    type: str                         # "failure" | "convention"
    pattern_kind: str                 # Phase 1 enum (see below)
    target_tool: str | None           # "Bash" | "Edit" | "Write" | None
    trigger_class: str | None         # "command_not_found" | None
    pattern: str                      # What was observed
    action: str                       # What to do
    evidence_summary: str             # "47 failures across 12 sessions, 4 days"
    supporting_observations: int      # Count of observations backing this
    supporting_sessions: int          # Count of distinct sessions
    supporting_days: int              # Count of distinct days
    confidence: float                 # 0.0-1.0
    scope: str                        # "project" (only scope in Phase 1)
    status: str                       # "proposed" | "approved" | "applied" | "reverted"
    created: str                      # ISO 8601
    decided: str | None               # When approved/rejected
    applied: str | None               # When applied
    reverted: str | None              # When reverted
    human_edited: bool                # True if user modified the rule text
```

**Phase 1 pattern_kind enum (required on every rule):**

```python
# Failure pattern_kinds
"python_launcher"         # python vs python3
"command_not_found"       # generic command not found
"file_not_found"          # missing file before edit/read
"permission_denied"       # permission errors
"syntax_error"            # command syntax issues
"test_failure"            # test runner failures

# Convention pattern_kinds
"test_command"            # canonical test runner for this project
"file_naming"             # dominant file naming convention
"test_placement"          # where test files go
```

**Contradiction detection (deterministic):** Two rules contradict if:
- Same `scope` AND same `pattern_kind`
- Different `action` values
- Both have status in ("proposed", "approved", "applied")

Example: "Use pytest -v" and "Use uv run pytest -q" both have `pattern_kind=test_command` → flagged as conflict. No LLM needed.

**Proposal quality guardrails (PER pattern_kind):**

```
pattern_kind          | min_obs | min_sessions | min_days | consistency
----------------------|---------|-------------|----------|------------
python_launcher       | 5       | 3           | 2        | n/a (failure)
command_not_found     | 5       | 3           | 2        | n/a (failure)
file_not_found        | 5       | 3           | 2        | n/a (failure)
permission_denied     | 5       | 3           | 2        | n/a (failure)
syntax_error          | 5       | 3           | 2        | n/a (failure)
test_failure          | 5       | 3           | 2        | n/a (failure)
test_command          | 5       | 3           | 2        | ≥80% winner, <20% runner-up
file_naming           | 10      | 3           | 2        | ≥85% dominant style
test_placement        | 6       | 3           | 2        | clear dominant pattern
```

**Ambiguity rule:** If the evidence is mixed (competing candidates within same pattern_kind have <15% gap), Acumen proposes NOTHING. Silence is better than a noisy proposal.

**Maximum 5 pending proposals at a time** (avoid overwhelming user).

**Rule rendering:** When applied, the structured rule is rendered as a one-sentence `.claude/rules/acumen-<id>.md` file:

```markdown
# Acumen rule

<action>

Observed: <pattern> (<evidence_summary>)
```

### 5.2 Rule Types (Phase 1)

Phase 1 ships TWO rule types: failure rules and convention rules. Preference rules are deferred until proposal quality is proven and approval patterns are stable.

**FAILURE RULES** — "Stop doing X because it fails"

Source: Repeated failure patterns in observations.
Detection: Group observations by (tool_name, error_class). Propose if count ≥ 5 across 3+ sessions AND 2+ distinct days.
Example: `pattern_kind=python_launcher, target_tool=Bash, trigger_class=command_not_found, action="Use python3 instead of python"`

**CONVENTION RULES** — "This project always does Y"

Source: Consistent success patterns in observations.
Phase 1 convention rules are limited to exactly THREE deterministic categories:

1. **test_command**: Canonical test runner for this project.
   Detection: Among successful Bash calls where command_family="test", if ≥80% use the same command family pattern across 3+ sessions, propose.
   Example: `pattern_kind=test_command, action="Use pytest -v for tests in this project"`

2. **file_naming**: Dominant file naming convention.
   Detection: Among successful Write calls, extract file_basename patterns. If ≥80% of new .py files use snake_case (or ≥80% use camelCase, etc.) across 3+ sessions, propose.
   Example: `pattern_kind=file_naming, action="New Python files use snake_case naming"`

3. **test_placement**: Where test files go.
   Detection: Among successful Write calls where file_basename starts with "test_" or ends with "_test", extract directory patterns. If ≥80% are placed in a consistent directory pattern across 3+ sessions, propose.
   Example: `pattern_kind=test_placement, action="Tests go in tests/ mirroring source structure"`

No general tool-sequence mining in Phase 1. No code-structure conventions. Three categories, deterministic detection rules, clear thresholds.

**PREFERENCE RULES** — deferred to Phase 2+.
Approval patterns are a weak proxy for user preference this early. Preference learning requires a stable proposal pipeline and enough approval data to distinguish real preferences from noise.

### 5.3 Application Rules (v1 — STRICT)

```
AUTO (no approval needed):
  /acumen-status output
  /acumen-report output
  Passive session-start observations ("Acumen has 3 pending proposals")
  Tier upgrade suggestions

APPROVAL REQUIRED (everything behavioral):
  ALL failure rules
  ALL convention rules
  ANY mutation to .claude/rules/
  ANY mutation to .claude/memory/
```

**No auto-apply for behavioral changes in v1.** This is load-bearing. Do not weaken it.

---

## 6. Storage

### 6.1 Observation Store

Per-session JSONL files: `.acumen/observations/<session_id>.jsonl`

**Why per-session:** Eliminates concurrent write conflicts. Each session writes to its own file. No locking needed for observations.

**Index file:** `.acumen/observations/index.json` maps session_ids to file paths and timestamps. Updated via atomic write-then-rename. Locked with `fcntl.flock()`.

**Rotation:** Session files older than 30 days moved to `.acumen/observations/archive/`.

**Corruption recovery:** If a JSONL line fails `json.loads()`, skip it, increment error counter, continue. Error count reported in `/acumen-status`.

### 6.2 Rule Store

Active rules: `.acumen/rules.json` (array of AcumenRule, read/written atomically).
Applied rule files: `.claude/rules/acumen-<id>.md` (one file per applied rule).

### 6.3 Effectiveness Store

`.acumen/effectiveness.json` — per-rule effectiveness records:

```python
@dataclass
class EffectivenessRecord:
    rule_id: str
    applied_at: str                   # ISO 8601
    sessions_observed: int            # Sessions since application
    target_pattern_before: float      # Occurrence rate before (per 100 events)
    target_pattern_after: float       # Occurrence rate after (per 100 events)
    adherence_rate: float | None      # For convention rules: % of relevant ops following convention
    verdict: str                      # "effective" | "neutral" | "harmful" | "pending"
    retained_at_2_weeks: bool | None  # Still active after 14 days?
```

### 6.4 File I/O Safety

1. **Append-only for observation JSONL** — no in-place edits
2. **Atomic rename for state files** — write to `.tmp`, then `os.rename()`
3. **fcntl.flock() on index and state files** — prevents concurrent corruption
4. **Per-session segmentation** — eliminates observation write conflicts
5. **Corruption recovery** — skip bad lines, log, continue
6. **No silent data loss** — every skip counted and reported

---

## 7. Reflection Engine

The reflection engine transforms raw observations into rule proposals. It runs:
1. On demand via `/acumen-reflect`
2. Prompted at session start if should-reflect flag is set

### 7.1 Pipeline

```
RAW OBSERVATIONS
      │
      v
[1. EVENT NORMALIZATION]
      Validate fields against known enums, fill defaults, discard malformed.
      Truncate any field exceeding expected length.
      │
      v
[2. FAILURE CLUSTERING]
      Group by (tool_name, error_class).
      Apply per-pattern_kind guardrails (min obs, sessions, days).
      Identify clusters that pass guardrails.
      │
      v
[3. CONVENTION EXTRACTION] (Phase 1B only, 3 categories)
      test_command: Group successful Bash calls where command_family="test"
        by command_signature. Check ≥80% winner, <20% runner-up.
      file_naming: Group successful Write calls where write_kind="create"
        by basename style (snake_case, camelCase, etc.). Check ≥85% dominant.
      test_placement: Group successful Write calls where write_kind="create"
        and file_basename matches test pattern, by path_pattern.
        Check clear dominant pattern.
      AMBIGUITY RULE: If gap between top two candidates <15%, propose NOTHING.
      │
      v
[4. PROPOSAL SYNTHESIS]
      For each failure cluster → generate failure rule proposal
      For each convention pattern → generate convention rule proposal
      │
      v
[5. CONTRADICTION CHECK]
      Compare each proposal against existing rules:
        same scope + same pattern_kind + different action
        + both status in ("proposed", "approved", "applied")
        → flag as conflict, do not auto-resolve
      │
      v
[6. CONFIDENCE SCORING]
      confidence = f(observation_count, session_spread, day_spread,
                     pattern_consistency)
      Minimum threshold: 0.4 to propose (below = discard)
      │
      v
RANKED PROPOSALS → rules.json (max 5 pending)
```

### 7.2 What the LLM Does vs. What Code Does

**Code does (deterministic, no LLM):**
- Event normalization
- Failure clustering (group by, count, guardrails)
- Convention extraction (frequency analysis, ambiguity check)
- Contradiction check (structured field comparison on pattern_kind)
- Confidence scoring (formula)

**LLM does (via reflection subagent):**
- Generate natural language `action` text from structured patterns
- Synthesize human-readable `evidence_summary` from observation data
- Identify non-obvious failure patterns that pure grouping misses
  (e.g., correlated failures across different tools)

**Rule:** The LLM receives observation data as STRUCTURED QUOTED DATA, never as instructions. All observation fields are treated as untrusted input.

---

## 8. Measurement

### 8.1 Phase 1 Success Metrics (hard, ungameable, explicit denominators)

| Metric | Target | How Measured | Denominator |
|--------|--------|-------------|-------------|
| Proposal approval rate | ≥ 50% | approved / (approved + rejected) | All proposals that reached review |
| 2-week retention rate | ≥ 30% | rules still active 14 days after apply | All rules applied ≥ 14 days ago |
| Failure recurrence rate | ≥ 1 class halved | occurrences per 100 events of same command_family, before vs after | Only events matching same (tool_name, command_family). Min 50 events in each window. |
| Convention adherence rate | ≥ 1 convention tracked | relevant operations following convention / total relevant operations | Only events matching the convention's pattern_kind. Min 20 relevant operations. |

**Denominator rules (prevent gaming/misreading):**
- Failure recurrence: measured per 100 events of the SAME command_family. If Python work drops for a week, that doesn't count as improvement — the denominator shrinks proportionally.
- Convention adherence: measured over RELEVANT operations only (e.g., "file naming" is measured only over Write calls that create new files, not all Write calls).
- Minimum sample size: no verdict until both before and after windows have sufficient observations (50 events for failure, 20 operations for conventions).
- Time window: "before" = 14 days pre-application. "After" = days since application. Minimum 7 days in "after" window before declaring verdict.

**Why these metrics:**
- Approval rate alone is gameable (propose obvious low-value rules). Recurrence reduction is not.
- Retention proves proposals are actually useful, not just easy to approve.
- Convention adherence proves the agent is actually behaving differently, not just carrying rules.
- Explicit denominators prevent false positives from workload shifts.

### 8.2 /acumen-report Output

```
┌──────────────────────────────────────────────────────────────────┐
│                       ACUMEN REPORT                               │
│                       my-project (14 days)                        │
│                                                                   │
│  YOUR AGENT IS SPECIALIZING                                       │
│                                                                   │
│  Failures reduced:                                                │
│    "python command_not_found"                                     │
│      Before: 9.4 per 100 python calls                             │
│      After:  0.4 per 100 python calls    ↓ 96%                   │
│      Rule: "Use python3 instead of python"                        │
│                                                                   │
│    "Edit file_not_found"                                          │
│      Before: 4.6 per 100 Edit calls                               │
│      After:  1.6 per 100 Edit calls      ↓ 65%                   │
│      Rule: "Verify file exists before Edit tool"                  │
│                                                                   │
│  Conventions learned:                                             │
│    test_command: "pytest -v"                                      │
│      adherence: 23/23 test runs (100%)                            │
│    file_naming: "snake_case for .py files"                        │
│      adherence: 15/16 new files (94%)                             │
│    test_placement: "tests/ mirroring src/"                        │
│      adherence: 8/9 test files (89%)                              │
│                                                                   │
│  5 rules active │ 4 approved, 1 pending │ 0 reverted             │
│                                                                   │
│  Observation: Tier 0.5 (categorical)                              │
│  Sessions observed: 23 │ Events: 1,847                            │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

---

## 9. Phased Implementation

### Phase 1: Operational Specialization (Weeks 1-6)

**One job:** Prove that automatic observation can generate useful, evidence-backed proposals that users approve and keep, and that targeted failure classes decrease and conventions are internalized.

**Deliverables (build order):**

Phase 1A — Failure rules:
- [ ] Tier 0.5 observation hook (classify, don't capture)
- [ ] Per-session observation files with index
- [ ] File I/O safety (append-only, atomic rename, flock, corruption recovery)
- [ ] Failure clustering (group by tool_name + error_class, apply guardrails)
- [ ] Structured rule format with pattern_kind contradiction detection
- [ ] Proposal quality guardrails (min support, session spread, day spread)
- [ ] `/acumen-review` (approve/reject proposals)
- [ ] Rule application (write .claude/rules/acumen-*.md) + revert
- [ ] Effectiveness tracking: failure recurrence rate with explicit denominators
- [ ] `/acumen-status` (quick health)
- [ ] Dogfood failure rules until proposals are actually useful

Phase 1B — Convention rules (only after 1A is stable):
- [ ] Success pattern extraction for 3 categories: test_command, file_naming, test_placement
- [ ] Convention proposal generation with 80% consistency threshold
- [ ] Convention adherence tracking with explicit denominators
- [ ] `/acumen-report` (full report with failures + conventions)
- [ ] Tier upgrade prompting (suggest Tier 1 when confidence is low)
- [ ] Dogfood conventions on our own projects

**Phase 1 does NOT include:**
- Preference rules (deferred — approval patterns too noisy this early)
- Marketplace submission (earn it with data first)
- Auto-apply for behavioral changes
- General tool-sequence mining
- Skill synthesis
- Archive tree
- Meta-improvement
- Structural fingerprints (code-structure conventions)
- Global scope
- Any second adapter

**Phase 1 honest claim:**
> Acumen reduces your coding agent's repeated failures and teaches it your project's test runner, file naming, and test placement conventions — all with your approval, all local.

### Phase 2: Validated Improvement + Code Structure (Weeks 7-12)

- [ ] Before/after baseline comparison (verifiable signals)
- [ ] Regression detection + auto-revert
- [ ] Structural fingerprints for code-structure conventions:
  - Import block style
  - Exception handling pattern
  - Test skeleton structure
  - Framework-specific patterns
- [ ] Ephemeral content inspection (read at write time, extract fingerprint, discard raw)
- [ ] Data-informed graduation of safe categories to auto-apply
- [ ] Submit to Anthropic marketplace

### Phase 3: Flywheel + Expansion (Weeks 13-20)

- [ ] Skill synthesis from observed multi-step workflows
- [ ] Archive tree (preserve diverse improvements)
- [ ] Meta-improvement (track whether improvement quality itself improves)
- [ ] Global scope (cross-project learnings)
- [ ] Second adapter design (Codex or generic)

### Phase 4+: Beyond Coding (when platform support exists)

- [ ] Non-coding adapters (as Claude expands hook infrastructure)
- [ ] Robotics adapter (if/when robot dev tools expose action hooks)
- [ ] Enterprise features
- [ ] Skill network (anonymous community sharing)
- [ ] Monetization

---

## 10. Tech Stack

- **Architecture:** Pure Claude Code plugin (zero external dependencies)
- **Observation:** Shell script (bash) for hot path
- **Logic:** Python 3.11+ stdlib only (dataclasses, json, pathlib, uuid, fcntl)
- **Storage:** JSONL (observations), JSON (rules, effectiveness, config)
- **Agent integration:** Claude Code plugin system (skills, hooks, commands, agents)
- **Testing:** pytest (dev dependency only)
- **Linting:** ruff (dev dependency only)

**Zero dependency discipline.** Python stdlib ONLY. No pip packages. No npm. No jq (removed in v0.1.1). This is a competitive advantage: install is one command, nothing can break, nothing to update.

---

## 11. Safety & Privacy

### 11.1 Privacy Contract

**Tier 0.5 (default):** Captures tool names, outcome categories, error classifications, command families, and file basenames. No raw commands, no file contents, no conversation text, no code. Less information than a standard web server access log.

**Tier 1 (opt-in):** Adds redacted error messages, full file paths, and command summaries. Ephemeral — deleted after reflection, hard 24-hour cap.

**All tiers:** Nothing ever leaves the machine. Zero network calls. Zero telemetry.

**The claim:** Acumen defaults to local, categorical analysis. It reads raw commands and error text transiently to classify them, then discards the raw data — persisting only derived categories like "python" or "command_not_found", never raw commands or file contents. Optionally, with your permission, it can retain redacted execution traces — locally, ephemerally, deleted after analysis.

### 11.2 Safety Principles

1. **All behavioral mutations require approval in v1.** No exceptions.
2. **All improvements are reversible.** Delete the rule file, it's gone.
3. **Observation text is hostile input.** Never interpolated into instructions.
4. **Fail-open.** If Acumen crashes, the agent works normally.
5. **Transparent.** Every proposal cites evidence. Every rule shows its source.
6. **No reward hacking.** Multiple independent metrics, not one number.

### 11.3 Threat Model

| Threat | L | I | Mitigation |
|--------|---|---|------------|
| Prompt injection via observation fields | M | M | Structured quoted data, validated enumerations, truncation |
| LLM generates harmful rule | M | H | All rules require approval; structured format limits expressiveness |
| Observation leaks sensitive data | L | M | Tier 0.5: categories only, no raw data. Tier 1: redaction + ephemeral |
| Improvement degrades performance | M | M | Effectiveness tracking + user can revert any rule |
| Concurrent file corruption | L | M | Per-session files + flock + atomic rename |

---

## 12. File Structure (Phase 1)

```
acumen/                                # Plugin root
  plugin.json                          # Plugin manifest
  spec-v2.1.md                         # This spec (implementation contract)

  skills/
    reflect.md                         # Reflection skill (triggers pipeline)

  commands/
    status.md                          # /acumen-status
    reflect.md                         # /acumen-reflect
    report.md                          # /acumen-report
    review.md                          # /acumen-review

  hooks/
    observe.sh                         # PostToolUse/Failure → Tier 0.5 event

  agents/
    reflector.md                       # Reflection subagent

  lib/
    store.py                           # Observation store (per-session JSONL)
    classify.py                        # Tier 0.5 field derivation (command_family, etc.)
    cluster.py                         # Failure clustering + success pattern extraction
    propose.py                         # Proposal synthesis + contradiction check
    apply.py                           # Rule application (write .claude/rules/ files)
    measure.py                         # Effectiveness tracking
    format.py                          # CLI output formatting

  tests/
    test_store.py
    test_classify.py
    test_cluster.py
    test_propose.py
    test_apply.py
    test_measure.py
    fixtures/
      sample_observations.jsonl
```

---

## 13. Competitive Positioning

**Adjacent (observe or remember, don't improve):**
- Braintrust ($80M): Observability + eval. Stops at dashboards.
- Mem0 ($24M): Memory layer. Remembers, doesn't learn.
- Arize ($70M): ML observability. Monitors, doesn't evolve.

**Direct (attempt self-improvement):**
- claude-reflect: Reads conversation content (privacy concern). No structured learning.
- OpenSpace: Self-evolving skill engine. Strong but framework-specific.
- A-Evolve (Amazon): Solve-Observe-Evolve loop. Research, not a product.

**Acumen's wedge:** The only tool that (a) observes automatically from categorical metadata, (b) proposes structured, evidence-cited improvements for failure reduction and convention learning, (c) requires approval for all behavioral changes, (d) measures effectiveness with explicit denominators, and (e) does all of this locally with zero cloud dependency.

---

## 14. Open Questions

1. **command_signature mapping completeness.** Start with: pytest, uv_pytest, npm_test, jest, cargo_test, go_test, ruff_check, ruff_format. Expand based on real data.
2. **path_pattern detection accuracy.** Detecting "tests_mirror" requires knowing the source root. Heuristic: find src/ or lib/, check if test paths mirror. May need tuning.
3. **write_kind detection.** Can we reliably distinguish create vs edit in the Claude Code hook? Hook may not expose this. Fallback: check file existence in the hook script before the event.
4. **Convention detection thresholds.** 80%/85% — right bar? Tune from dogfooding.
5. **Reflection trigger frequency.** Start with session-end flag-and-defer. May need time-based if sessions are long.
6. **Effectiveness measurement window.** 5 sessions or 7 days, whichever first. Min 50 events for failure verdicts, 20 for conventions.

---

## 15. Implementation Workflow (from lean research)

This spec MUST be built following these rules from findings-lean-implementation.md:

1. **Research → Plan → Implement → Verify → Review.** Each phase uses fresh context.
2. **One function, one feature, one test at a time.** Commit after each logical unit.
3. **Deletion first.** Before adding code, check if removing or simplifying existing code solves the problem.
4. **Read before writing.** Match existing code style. Do not reformat code you didn't change.
5. **Fresh-context review.** After implementation, review in a new context for unnecessary abstractions.
6. **Pre-commit hooks for enforcement.** Use ruff as hard guardrail, not advisory.
7. **No unnecessary abstractions.** Three concrete uses before extracting a pattern.
8. **Context budget.** Target 40-60% context utilization. /clear between unrelated tasks.

**Build order for Phase 1A (failure rules):**
1. `lib/classify.py` — Tier 0.5 field derivation. Test: `test_classify.py`
2. `hooks/observe.sh` — Refactor for Tier 0.5 output. Test: manual + fixture
3. `lib/store.py` — Per-session files + index. Test: `test_store.py`
4. `lib/cluster.py` — Failure clustering only. Test: `test_cluster.py`
5. `lib/propose.py` — Proposal generation + guardrails + contradiction. Test: `test_propose.py`
6. `commands/review.md` — Approve/reject UI. Test: manual dogfood
7. `lib/apply.py` — Write .claude/rules/ files + revert. Test: `test_apply.py`
8. `lib/measure.py` — Failure recurrence tracking. Test: `test_measure.py`
9. `commands/status.md` — Quick health display. Test: manual dogfood
10. Dogfood until failure rule proposals are useful

**Build order for Phase 1B (convention rules, only after 1A is stable):**
11. Extend `lib/cluster.py` with success pattern extraction for 3 categories
12. Extend `lib/propose.py` with convention proposal generation
13. Extend `lib/measure.py` with convention adherence tracking
14. `commands/report.md` — Full report with failures + conventions
15. Dogfood conventions on our own projects

**Anti-bloat checkpoints:**
- After step 5: Is the codebase under 500 lines of Python? If not, simplify.
- After step 10: Fresh-context review of entire lib/ for unnecessary abstractions.
- After step 15: Writer/reviewer pattern — separate session reviews the full implementation.

**Human orchestrator guidance:**
- Review the PLAN before each build step begins
- Review each committed unit before proceeding to next step
- If correcting the same issue twice: /clear and restart with a better prompt
- The plan for each step should be describable in one sentence — if not, the step is too big

---

## 16. Research Grounding

| Decision | Source | Key Finding |
|----------|--------|-------------|
| Scaffold improvement, not model | DGM, Live-SWE-agent, AutoResearch, M2.7 | All achieve 30-250% improvement by changing scaffold, not model weights |
| Learn from successes AND failures | ExpeL (AAAI 2024 Oral) | Insights from both produce dramatically better agents than failures alone |
| Categorical observation (classify, don't capture) | DGM safety research | Self-improving systems encounter sensitive data; minimize capture |
| Approval-required application | DGM reward hacking | Systems WILL game evaluation metrics; human-in-the-loop is essential |
| Structured rule format | ARTEMIS | Joint optimization requires conflict awareness; structured = deterministic contradiction detection |
| Multiple metrics, not one | AZR | Verifiable signals from code execution beat LLM self-evaluation |
| Diverse preservation (archive) | DGM, DGM-Hyperagents | Stepping stones enable breakthroughs; don't prune aggressively |
| Lightweight reflection | Live-SWE-agent | One prompt ("would this help?") is enough; complex meta-learning unnecessary |
| Domain-agnostic abstractions | DGM-Hyperagents | Meta-improvements transfer across domains (coding → robotics → math) |
| Skill synthesis from workflows | SkillWeaver, Voyager, OpenSpace | Skill libraries are transferable between agents; 4.2x improvement |

# Acumen: Continuous Improvement Harness for Coding Agents

## Specification v2.0

**Date:** 2026-03-30
**Status:** Draft (supersedes spec.md v0.1)
**Author:** Acumen team

---

## 1. Vision

Acumen is a continuous improvement harness for coding agents with observable tool use, replayable tasks, and verifiable outcomes.

The tools that monitor your agent stop at dashboards. The tools that remember stop at memory. Acumen closes the loop: it turns observations into validated improvements that make your agent measurably better -- locally, safely, with your approval.

**The aha moment:** You install Acumen, work normally for two weeks, and `/acumen-report` shows your agent's repeated-failure rate dropped 34%. You didn't have to tell it anything. It observed, learned, proposed, and you approved.

**What Acumen is NOT:**
- Not a fine-tuning system. Works with frozen API-only models through scaffold improvement.
- Not an observability platform. Braintrust and Arize observe. Acumen improves.
- Not a memory layer. Mem0 remembers. Acumen learns and applies.
- Not a heavyweight framework. Zero external dependencies. One plugin install.

**The gap nobody fills:** Nobody has clearly won the continuous improvement loop that turns observation and evaluation into validated scaffold changes. That is what Acumen does.

---

## 2. Core Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         ACUMEN ENGINE                                 │
│                                                                       │
│  OBSERVATION (tiered, all local, all ephemeral)                       │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ Tier 0 (default): metadata -- tool_name, outcome, error_type    │ │
│  │ Tier 1 (opt-in):  traces  -- + error_msg, paths, redacted cmds │ │
│  │ Tier 2 (hidden):  bounded -- + summarized inputs/outputs       │ │
│  │                                                                  │ │
│  │ ALL LOCAL. Traces are EPHEMERAL (deleted after reflection).      │ │
│  │ NOTHING leaves the machine.                                      │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                             │                                         │
│  THE LOOP                                                             │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │                                                                  │ │
│  │  OBSERVE ──> LEARN ──> PROPOSE ──> VALIDATE ──> APPLY           │ │
│  │     │                                              │             │ │
│  │     └──────────── TRACK EFFECTIVENESS <────────────┘             │ │
│  │                          │                                       │ │
│  │                     ARCHIVE ALL                                  │ │
│  │              (diverse improvements preserved)                    │ │
│  │                                                                  │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  REQUIREMENTS FROM HOST AGENT:                                        │
│  ┌──────────────────────────────────────────────────────────────────┐ │
│  │ 1. Observable tool use (hooks/events for tool calls)             │ │
│  │ 2. Replayable tasks (can re-run a task to compare outcomes)      │ │
│  │ 3. Verifiable outcomes (tests, lint, exit codes)                 │ │
│  └──────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘
```

### 2.1 The Five Phases

**OBSERVE:** Capture what happens during agent sessions.
- Tiered observation: metadata (default) → execution traces (opt-in) → bounded inspection (hidden)
- All local, all ephemeral. Traces deleted after reflection.

**LEARN:** Extract actionable insights from observations.
- Failure analysis: what went wrong and why
- Pattern detection: recurring mistakes, common corrections
- Success attribution: what worked and should be repeated

**PROPOSE:** Generate specific, evidence-cited improvement proposals.
- Each proposal has a standardized shape (see Section 3.3)
- Proposals cite the observations that motivated them
- Proposals include expected upside and rollback path

**VALIDATE:** Test improvements before deployment.
- Before/after baseline comparison using verifiable signals
- Staged evaluation: quick sanity check → full validation
- Regression detection: does the improvement make things worse?

**APPLY:** Deploy improvements with user approval.
- v1: ALL behavior-changing mutations require user approval
- Auto-apply only for passive/non-operative outputs (status, warnings, annotations)
- Every application tracked with before/after state for rollback

### 2.2 Scopes

```
GLOBAL (~/.claude/acumen/global/)
  Universal learnings across all projects.
  Examples: "User prefers python3 over python", "Always run tests before committing"

PROJECT (.acumen/)
  Learnings specific to a codebase and its patterns.
  Examples: "This project uses Pydantic v2", "Tests go in tests/"

SESSION (ephemeral)
  Within-conversation observations, not persisted.
```

Scope promotion requires evidence: multiple occurrences + user validation.

---

## 3. Technical Design

### 3.1 Plugin Architecture (Claude Code First)

Acumen delivers as a Claude Code plugin. Phase 1 targets Claude Code exclusively.
The internal observation interface is agent-agnostic (accepts a standard event schema),
so future adapters for other agents can plug in without rewriting core logic.

```
acumen/
  plugin.json                    # Plugin manifest
  skills/
    reflect.md                   # Reflection skill
  commands/
    status.md                    # /acumen-status
    reflect.md                   # /acumen-reflect
    report.md                    # /acumen-report (new in v2)
    review.md                    # /acumen-review
  hooks/
    observe.sh                   # PostToolUse / PostToolUseFailure
    session-end.sh               # Flag reflection trigger
    session-start.sh             # Inject reflection prompt + tier upgrade
  agents/
    reflector.md                 # Reflection analysis subagent
  lib/
    store.py                     # Observation store (append-only JSONL)
    reflect.py                   # Reflection engine (pattern extraction)
    propose.py                   # Proposal generation
    validate.py                  # Before/after baseline comparison
    apply.py                     # Trust-tiered application
    archive.py                   # Improvement archive (diverse preservation)
    format.py                    # CLI display formatting
  tests/
    test_store.py
    test_reflect.py
    test_propose.py
    test_validate.py
    test_apply.py
    test_archive.py
    fixtures/
      sample_observations.jsonl
```

### 3.2 Data Model

**ObservationEvent** (the unified event schema, agent-agnostic):

```python
@dataclass
class ObservationEvent:
    tool_name: str                          # e.g. "Bash", "Edit", "Write"
    session_id: str                         # UUID, set by agent host
    timestamp: str                          # ISO 8601
    outcome: Literal["success", "error"]
    error_type: str | None = None           # e.g. "tool_failure", "tool_error"

    # Tier 1 fields (only populated if user opts into Tier 1)
    error_message: str | None = None        # Redacted error message
    file_paths: list[str] | None = None     # Paths touched (no contents)
    command_summary: str | None = None       # Redacted command summary

    # Tier 2 fields (hidden, experimental)
    input_summary: str | None = None        # Summarized/redacted input
    output_summary: str | None = None       # Summarized/redacted output
```

Storage: Append-only JSONL, segmented per session:
`.acumen/observations/<session_id>.jsonl`

Per-session segmentation eliminates concurrent write conflicts (each session
writes to its own file). An index file `.acumen/observations/index.json`
maps session_ids to file paths and timestamps for efficient lookup.

**Observation store invariants:**
- Append-only writes (no in-place modification)
- Atomic append via write-then-rename for state updates (index)
- `fcntl.flock()` for the index file only
- Corruption recovery: if a JSONL line fails to parse, skip it and log warning
- Rotation: archive session files older than 30 days to `.acumen/observations/archive/`

**ImprovementProposal** (the standardized proposal shape):

```python
@dataclass
class ImprovementProposal:
    id: str                                 # ULID or UUID
    category: str                           # "error_pattern" | "workflow" | "tool_usage" | "convention"
    evidence_summary: str                   # Human-readable: "47 retries across 12 sessions"
    supporting_observations: int            # Count of observations backing this
    mutation_target: str                     # What changes: "rule", "skill", "memory"
    mutation_content: str                    # The actual rule/skill/memory text
    rationale: str                          # Why this should help
    confidence: float                       # 0.0-1.0, computed from evidence strength
    risk_class: str                         # "passive" (auto-ok) | "behavioral" (needs approval)
    expected_upside: str                    # "Eliminate python/python3 confusion (~5 failures/week)"
    rollback_path: str                      # "Delete .claude/rules/acumen-<slug>.md"
    status: str                             # "proposed" | "approved" | "rejected" | "applied" | "reverted"
    created: str                            # ISO 8601
    decided: str | None = None              # When approved/rejected
    applied: str | None = None              # When applied
    reverted: str | None = None             # When reverted, if ever
```

Storage: `.acumen/proposals.json` (JSON array, small enough to read/write atomically).

**EffectivenessRecord** (tracks whether applied improvements help):

```python
@dataclass
class EffectivenessRecord:
    proposal_id: str
    applied_at: str                         # ISO 8601
    sessions_since: int                     # How many sessions since application
    error_rate_before: float | None         # For the target pattern, before application
    error_rate_after: float | None          # For the target pattern, after application
    verdict: str                            # "effective" | "neutral" | "harmful" | "pending"
    retained: bool                          # Still active after 2+ weeks?
```

Storage: `.acumen/effectiveness.json`

**ArchiveNode** (preserves all improvements, not just the best):

```python
@dataclass
class ArchiveNode:
    id: str                                 # Same as proposal_id
    parent_id: str | None                   # What observation cluster spawned this
    proposal: ImprovementProposal           # The full proposal
    effectiveness: EffectivenessRecord | None
    children: list[str]                     # IDs of improvements that built on this
```

Storage: `.acumen/archive.json`

### 3.3 Observation Tiers (detailed contract)

**Tier 0: Metadata-Only (DEFAULT)**

What is captured:
- `tool_name`: string (e.g. "Bash", "Edit")
- `outcome`: "success" | "error"
- `error_type`: string | null
- `session_id`: string
- `timestamp`: ISO 8601 string

What is NOT captured: everything else. No commands, no file contents, no error messages, no paths.

Retention: permanent (JSONL files, archived after 30 days).

Sanitization: `tool_name` stripped to alphanumeric + underscore (max 64 chars). `error_type` stripped to alphanumeric + underscore (max 64 chars).

**Tier 1: Execution Traces (OPT-IN)**

What is additionally captured:
- `error_message`: string, aggressively redacted:
  - Anything matching `[A-Za-z0-9+/=]{20,}` (base64-like) → `[REDACTED]`
  - Anything matching common secret patterns (sk-, token=, password=, API_KEY) → `[REDACTED]`
  - Anything matching email patterns → `[REDACTED]`
  - Truncated to 200 chars max
- `file_paths`: list of file paths touched (no contents). Paths containing "secret", "credential", "token", ".env" → `[REDACTED]`
- `command_summary`: first 100 chars of command, with the same redaction rules

Retention: EPHEMERAL. Tier 1 fields are deleted from observation files after reflection completes. Only Tier 0 fields persist.

Maximum retention window: 24 hours from capture, regardless of whether reflection runs.

Activation: User runs `acumen config set observation-tier 1` OR approves the upgrade prompt.

**Tier 2: Bounded Artifact Inspection (HIDDEN/EXPERIMENTAL)**

Not exposed to users in Phase 1. Exists as an internal flag only. Will be designed based on Phase 1 learnings about where Tier 1 is insufficient.

**Tier upgrade prompting:**

After the first reflection cycle on Tier 0, if the reflection engine generates proposals with confidence < 0.3 (low evidence quality), the system includes a message in `/acumen-report`:

```
Acumen found 3 likely improvement areas, but confidence is limited
in metadata-only mode. Enable local ephemeral trace analysis for
stronger fixes? All analysis stays on your machine.

  acumen config set observation-tier 1
```

### 3.4 Reflection Engine

The reflection engine runs:
1. On demand via `/acumen-reflect`
2. Prompted at session start if the should-reflect flag is set (flag-and-defer)

Input:
- Session observations (Tier 0 or Tier 0+1 depending on setting)
- Existing proposals (to avoid duplicates)
- Existing active rules (to avoid contradictions)

Process:
1. Group observations by tool_name, outcome, error_type
2. Identify patterns: recurring failures, retry sequences, error clusters
3. Cross-reference with existing rules (contradiction check)
4. Generate structured ImprovementProposals
5. Score by confidence (evidence count, pattern strength) and expected impact

Output: Ranked list of ImprovementProposals written to `.acumen/proposals.json`

**Contradiction detection:** Before finalizing any proposal, the reflection engine checks:
- Does an existing active rule address the same tool + error_type combination?
- Does the proposed rule text conflict with existing rule text? (substring overlap + semantic check by the LLM)
- If contradiction found: flag proposal as "needs_review" regardless of risk_class

### 3.5 Validation Layer (Phase 2)

Before applying an improvement, the validation layer:

1. Records baseline metrics (error rate for the target pattern over last N sessions)
2. Applies the improvement
3. Waits for M sessions (default: 5)
4. Records post-application metrics
5. Compares: if error rate increased > 10%, auto-revert

Validation uses verifiable signals ONLY:
- Tool exit codes (success/failure counts)
- Test pass/fail rates (if test suite detected)
- Lint/typecheck results (if configured)
- Observation pattern recurrence

NOT used for validation: LLM self-evaluation, user sentiment inference, or any subjective metric.

### 3.6 Application Layer

**v1 application rules (STRICT):**

```
AUTO-APPLY (no approval needed):
  - /acumen-status output generation
  - /acumen-report output generation
  - Passive warnings in session start context
  - Non-operative annotations in memory
  - Observation tier upgrade suggestions

APPROVAL REQUIRED:
  - ALL rules that affect agent behavior
  - ALL skill files
  - ALL configuration changes
  - ALL mutations to .claude/rules/ or .claude/memory/

v1 DOES NOT HAVE:
  - Silent behavior-changing mutations
  - Aggressive auto-apply tier
  - Any mutation applied without user seeing it first
```

Approval flow: `/acumen-review` shows pending proposals with full evidence trail. User approves or rejects each individually.

### 3.7 Archive (Phase 3)

The archive preserves ALL improvement proposals -- applied, rejected, and reverted -- as a tree. This enables:
- Diverse improvement strategies preserved (DGM principle)
- Failed approaches recorded to avoid re-proposing
- Stepping stones: a rejected proposal may inform a future better proposal
- Full audit trail of what Acumen has learned

### 3.8 File I/O Safety

All file operations follow these rules:

1. **Append-only for observations**: No in-place edits to JSONL files
2. **Atomic rename for state updates**: Write to `.tmp` file, then `os.rename()` to target
3. **File locking**: `fcntl.flock()` on index files and proposal files
4. **Per-session segmentation**: Each session writes to its own observation file (eliminates concurrent write conflicts)
5. **Corruption recovery**: If a JSONL line fails `json.loads()`, skip it, log warning, continue
6. **No silent data loss**: Every skip/error is counted and reported in `/acumen-status`

---

## 4. User Experience

### 4.1 Installation

```bash
# From local clone (development)
claude plugin add /path/to/acumen

# From marketplace (after internal proof)
claude plugin add acumen
```

No `acumen init` command. The `.acumen/` directory is created on first observation hook fire.

### 4.2 Commands

| Command | Purpose |
|---------|---------|
| `/acumen-status` | Quick health check: observations, proposals, active rules |
| `/acumen-reflect` | Trigger reflection now |
| `/acumen-review` | Review and approve/reject pending proposals |
| `/acumen-report` | Detailed report: trends, effectiveness, improvement history |

### 4.3 The Report (/acumen-report)

```
┌──────────────────────────────────────────────────────────┐
│                    ACUMEN REPORT                          │
│                    my-app (project scope)                  │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  OBSERVATION SUMMARY (last 14 days)                       │
│    Sessions observed: 47                                  │
│    Total events: 2,340                                    │
│    Observation tier: 0 (metadata-only)                    │
│                                                           │
│  IMPROVEMENT PROPOSALS                                    │
│    Proposed: 8                                            │
│    Approved: 5  (62.5% approval rate)                     │
│    Rejected: 2                                            │
│    Pending: 1                                             │
│                                                           │
│  APPLIED IMPROVEMENTS                                     │
│    Active rules: 5                                        │
│    Retained after 2+ weeks: 4 (80% retention)             │
│    Reverted: 0                                            │
│                                                           │
│  EFFECTIVENESS (for applied improvements)                 │
│    "Use python3 not python" → Bash failures ↓ 73%         │
│    "Check file exists before edit" → Edit failures ↓ 41%  │
│    "Run tests with -x flag" → No measurable change        │
│    "Prefer absolute paths" → Path errors ↓ 28%            │
│                                                           │
│  REPEATED FAILURE CLASSES                                  │
│    #1: Bash command_not_found (47 occurrences, ↓ 73%)     │
│    #2: Edit file_not_found (23 occurrences, ↓ 41%)        │
│    #3: Write permission_denied (12 occurrences, unchanged) │
│                                                           │
│  TIP: Enable local trace analysis for stronger fixes:     │
│    acumen config set observation-tier 1                    │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

## 5. Tech Stack

- **Architecture:** Pure Claude Code plugin (zero external dependencies)
- **Observation:** Shell script (bash) for hot path (<50ms per event)
- **Logic:** Python 3.11+ stdlib only (dataclasses, json, pathlib, uuid, fcntl)
- **Storage:** JSONL files (observations), JSON files (proposals, archive, config)
- **Agent integration:** Claude Code plugin system (skills, hooks, commands, agents)
- **Testing:** pytest (dev dependency only)
- **Linting:** ruff (dev dependency only)

### 5.1 Research Grounding

| Decision | Research Source |
|----------|---------------|
| Tiered observation | DGM safety research: self-improving systems encounter sensitive data |
| Local-only analysis | Mem0 positioning: privacy as competitive advantage |
| Approval-required application | DGM: systems WILL hack their own reward functions |
| Verifiable validation signals | AZR: code execution as ground truth beats LLM-as-judge |
| Archive tree (diverse preservation) | DGM, DGM-Hyperagents: stepping stones enable breakthroughs |
| Evidence-cited proposals | ExpeL: natural language insights from experience |
| Per-session observation files | Live-SWE-agent: minimal starting point, earn complexity |
| Contradiction detection | ARTEMIS: joint optimization requires conflict awareness |

---

## 6. Phased Implementation

### Phase 1: Prove the Loop (Weeks 1-6)

**One job:** Demonstrate that the observe → learn → propose → approve cycle produces improvements users actually accept and retain.

Deliverables:
- [ ] Tiered observation (Tier 0 default, Tier 1 opt-in)
- [ ] Per-session observation files with index
- [ ] File I/O safety (append-only, atomic rename, flock, corruption recovery)
- [ ] Reflection engine (failure analysis → ImprovementProposal generation)
- [ ] Contradiction detection (existing rules vs new proposals)
- [ ] Approval-required application for all behavioral mutations
- [ ] `/acumen-status` (quick health)
- [ ] `/acumen-report` (detailed trends and effectiveness)
- [ ] Tier upgrade prompting (when Tier 0 confidence is low)
- [ ] Dogfood on our own projects until proposal quality is stable

**Phase 1 does NOT include:**
- Marketplace submission (earn it first)
- Auto-apply for behavioral changes
- Validation layer (before/after comparison)
- Archive tree
- Skill synthesis
- Meta-improvement
- Any second adapter

**Phase 1 success metrics:**
1. ≥ 50% proposal approval rate (users accept more than they reject)
2. ≥ 30% of approved proposals still retained after 2 weeks (not just accepted, actually useful)
3. Statistically meaningful reduction in at least one concrete repeated failure class on our own repos (not vanity — real improvement)

### Phase 2: Earn Trust (Weeks 7-12)

**One job:** Prove improvements are safe, measurable, and reversible.

Deliverables:
- [ ] Before/after baseline comparison (using verifiable signals)
- [ ] Regression detection + auto-revert
- [ ] Effectiveness tracking (per-proposal metrics over time)
- [ ] Smart Tier 1 upgrade prompting (based on Phase 1 data)
- [ ] Data-informed graduation of high-acceptance categories to auto-apply
- [ ] Submit to Anthropic marketplace (only after Phase 1 metrics are solid)

**Phase 2 success metrics:**
1. Zero regressions from applied improvements
2. Measurable error rate reduction visible in `/acumen-report`
3. Marketplace submission accepted

### Phase 3: Build the Flywheel (Weeks 13-20)

Deliverables:
- [ ] Archive tree (preserve diverse improvements)
- [ ] Skill synthesis (SkillWeaver-inspired, from successful multi-step patterns)
- [ ] Meta-improvement (simple: track whether improvement quality itself improves)
- [ ] Second adapter design (if demand warrants)
- [ ] Global scope (cross-project learnings)

### Deferred (not in Phase 1-3)

- Skill Network / community sharing
- Enterprise features (team-wide learning, RBAC)
- Platform API
- Additional adapters (Codex, Cursor, Windsurf, etc.)
- Monetization layer
- Tier 2 observation

---

## 7. Safety & Privacy

### 7.1 Privacy Contract

**Default (Tier 0):** Acumen captures only tool_name, outcome, and error_type. This is less information than a standard server access log.

**Opt-in (Tier 1):** Additionally captures error messages and file paths with aggressive redaction. Tier 1 data is EPHEMERAL -- deleted after reflection, with a hard maximum retention of 24 hours.

**All tiers:** Nothing ever leaves the machine. Zero network calls. Zero telemetry. No cloud component.

**The claim:** Acumen defaults to local, minimal-retention analysis. It can improve agents using execution traces, outcome signals, and optionally bounded artifact inspection -- without shipping raw code or conversations off your machine.

### 7.2 Safety Principles

1. **v1: All behavioral mutations require approval.** No silent changes.
2. **All improvements are reversible.** Every change has a recorded rollback path.
3. **Verifiable validation only.** Improvements are tested against objective signals (test results, error rates), never LLM self-evaluation.
4. **Fail-open.** If Acumen crashes, the agent works normally.
5. **Transparent operation.** Every proposal cites its evidence.
6. **Anti-reward-hacking.** Multiple independent validation signals, not one metric.

### 7.3 Threat Model

| Threat | Likelihood | Impact | Mitigation |
|--------|-----------|--------|------------|
| Prompt injection via observation fields | Med | Med | Sanitize all fields (alphanumeric + underscore, capped length) |
| LLM generates harmful rule | Med | High | All rules require approval in v1; contradiction detection |
| Observation store leaks sensitive data | Low | Med | Tier 0: metadata only. Tier 1: aggressive redaction + ephemeral |
| Improvement degrades agent performance | Med | Med | Validation layer (Phase 2) + user can revert any rule |
| Concurrent file corruption | Low | Med | Per-session files + flock + atomic rename |

---

## 8. Competitive Positioning

**Adjacent competitors (observe or remember, but don't improve):**
- Braintrust ($80M): AI observability and eval. Stops at dashboards.
- Mem0 ($24M): Memory layer for AI. Remembers but doesn't learn.
- Arize ($70M): ML observability. Monitors but doesn't evolve.
- Langfuse: Tracing and eval. Open source. Stops at traces.

**Direct competitors (attempt self-improvement):**
- claude-reflect: Reads conversation content (privacy concern). No validation layer.
- OpenSpace: Self-evolving skill engine. Strong but framework-specific, not a plugin.
- Self-improving-agent skill: Prompt-only, no automated observation.

**Acumen's wedge:** The only tool that (a) observes automatically, (b) proposes evidence-cited improvements, (c) requires approval for all behavioral changes, (d) validates against verifiable signals, and (e) does all of this locally with zero cloud dependency.

---

## 9. Success Definition

Acumen succeeds if:

1. A developer installs it, works normally for 2 weeks, and their agent measurably makes fewer repeated mistakes.
2. Every improvement Acumen proposes can be traced to specific observations.
3. Users approve more proposals than they reject (>50%).
4. Approved proposals are retained, not reverted (>30% after 2 weeks).
5. At least one concrete failure class is significantly reduced on our own repos.

Acumen fails if:
- It produces noisy/useless proposals (approval rate <30%)
- It silently degrades agent behavior
- It adds observable latency to agent operations
- Users have to understand Acumen's internals to use it

---

## 10. Open Questions

1. **Tier 1 redaction completeness:** The redaction patterns for error messages and commands need adversarial testing. What patterns do we miss?
2. **Reflection frequency:** How often should reflection run? After every session? After N observations? Time-based?
3. **Contradiction detection quality:** Simple string overlap vs. LLM-based semantic comparison? LLM is better but adds latency and cost.
4. **Global scope promotion criteria:** What evidence threshold justifies promoting a project-level insight to global?
5. **Archive pruning:** When the archive gets large, how do we decide what to keep? By recency? By effectiveness?

# Acumen: Self-Improving Agent Harness

## Specification v0.1

**Date:** 2026-03-29
**Status:** Draft
**Author:** Acumen team

---

## 1. Vision

Acumen is a harness that makes AI coding agents self-improving, self-evolving, and self-expanding. It plugs into the agent the user already uses (starting with Claude Code) and makes that agent measurably better over time with minimal user configuration.

**The aha moment:** A user installs Acumen, works normally for a week, and sees their agent making fewer mistakes, writing better code, and developing new capabilities -- all automatically.

**What Acumen is NOT:**
- Not another Toolwright (which governs API tools). Acumen improves the AGENT itself.
- Not a fine-tuning system. It works with API-only models through in-context learning.
- Not a heavyweight framework. It's a lightweight harness that plugs into existing agents.

---

## 2. Core Architecture

```
+------------------------------------------------------------------+
|                        ACUMEN HARNESS                             |
|                                                                   |
|  +-----------+    +------------+    +-----------+    +----------+ |
|  |  OBSERVE  |--->|   LEARN    |--->|  IMPROVE  |--->|  EXPAND  | |
|  +-----------+    +------------+    +-----------+    +----------+ |
|       |                |                 |                |       |
|   Hooks/events    Reflection        CLAUDE.md         Skills     |
|   Session logs    Insights          Memory             Commands  |
|   Outcomes        Patterns          Hooks              Workflows |
|                                                                   |
+------------------------------------------------------------------+
        |                                                   |
  +-----v------+                                  +---------v------+
  | Agent Host |                                  | Persistence    |
  | (Claude    |                                  | (git, files,   |
  |  Code,     |                                  |  CLAUDE.md,    |
  |  Codex,    |                                  |  .claude/)     |
  |  etc.)     |                                  +----------------+
  +------------+
```

### 2.1 The Four Phases

**OBSERVE [DONE]:** Capture what happens during agent sessions.
- [DONE] Hook into tool calls (PostToolUse, PostToolUseFailure via shell hook)
- [DONE] Track outcomes (success, error, with error_type and error_message)
- [PLANNED] Record user feedback (corrections, "no not that", "yes perfect")
- [PLANNED] Measure code quality signals (test pass rate, lint errors, churn)

**LEARN [DONE]:** Extract actionable insights from observations.
- [DONE] Failure analysis: what went wrong and why (ExpeL-style)
- [PLANNED] Success attribution: what worked and should be repeated
- [DONE] Pattern detection: recurring mistakes, common corrections
- [PLANNED] Quality trends: is the agent getting better or worse over time

**IMPROVE [DONE]:** Apply learnings to make the agent better.
- [DONE] Write path-scoped rules (.claude/rules/acumen-*.md)
- [DONE] Create/update memory entries (.claude/memory/acumen/)
- [PLANNED] Generate hooks (deterministic enforcement of learned rules)
- [DONE] Context injection via SessionStart hook (flag-and-defer auto-reflection)

**EXPAND [PLANNED]:** Grow the agent's capabilities.
- [PLANNED] Synthesize new skills from successful multi-step patterns (SkillWeaver-style)
- [PLANNED] Create slash commands for recurring workflows
- [PLANNED] Build reusable templates from successful sessions

### 2.2 Three Scopes

```
+----------------------------------------------------------+
|                 GLOBAL SCOPE [PLANNED]                    |
|  Universal learnings that apply across all projects       |
|  Storage: ~/.claude/acumen/global/                        |
|  Examples:                                                |
|    - "Always run tests before committing"                 |
|    - "User prefers explicit over clever"                  |
|    - Cross-project coding patterns                        |
|    - Universal anti-pattern detection                     |
+----------------------------------------------------------+
        |
+----------------------------------------------------------+
|                 PROJECT SCOPE [DONE]                      |
|  Learnings specific to a project's codebase & patterns   |
|  Storage: .acumen/ in project root                        |
|  Examples:                                                |
|    - "This project uses Pydantic v2, not v1"              |
|    - "Tests go in tests/, mirror source structure"        |
|    - Project-specific error patterns                      |
|    - Path-scoped rules and memory entries                 |
+----------------------------------------------------------+
        |
+----------------------------------------------------------+
|                 SESSION SCOPE [PLANNED]                   |
|  Within-conversation adaptation and reflection            |
|  Storage: in-memory (ephemeral)                           |
|  Examples:                                                |
|    - "User corrected my approach 3 times, adapt"          |
|    - Current task context and progress                    |
|    - Real-time quality monitoring                         |
+----------------------------------------------------------+
```

**Scope interaction rules [PLANNED]:**
- Global rules are injected into all sessions as baseline context
- Project rules override global rules when they conflict
- Session learnings are candidates for promotion to project or global scope
- Promotion requires evidence (multiple occurrences, user validation)

---

## 3. Technical Design

### 3.1 Plugin Architecture (Claude Code First) [DONE]

Acumen delivers as a Claude Code plugin:

```
acumen/                           # Plugin root
  plugin.json                     # Plugin manifest [DONE]
  skills/
    reflect.md                    # Reflection skill [DONE]
  commands/
    status.md                     # /acumen-status [DONE]
    reflect.md                    # /acumen-reflect [DONE]
    insights.md                   # /acumen-insights [DONE]
    review.md                     # /acumen-review [DONE]
  hooks/
    observe.sh                    # PostToolUse observation [DONE]
    session-end.sh                # Flag-and-defer reflection trigger [DONE]
    session-start.sh              # Inject reflection prompt [DONE]
  agents/
    reflector.md                  # Reflection/analysis subagent [DONE]
  lib/
    store.py                      # JSONL read/write + scope resolution [DONE]
    scorer.py                     # Confidence/impact scoring + dedup [DONE]
    formatter.py                  # CLI display formatting [DONE]
    improver.py                   # Proposal generation + application [DONE]
```

> **Simplifications from original plan:** Observation is handled entirely by the
> shell hook (no separate observer agent needed). Improvement is handled by
> lib/improver.py + the /acumen-review command (no separate improver agent
> needed). The observe.md and improve.md skills were unnecessary indirection.
> **v0.1.1 simplifications:** All insights become rules (`.claude/rules/acumen-*.md`).
> Memory entries dropped -- `.claude/memory/` is not read by Claude Code from
> the project root. Shell hook rewritten in pure bash (no jq dependency).
> Insight validation added. Proposal auto-expiry added (30-day TTL).

### 3.2 Data Model

**Observation [DONE]** (simplified from original spec -- metadata only):
```
{
  tool_name: string,
  session_id: string,
  timestamp: string (ISO 8601),
  outcome: "success" | "error",
  error_type: null | "tool_failure" | "tool_error",
  error_message: string | null
}
```

> Stored as JSONL in `.acumen/observations/YYYY-MM-DD.jsonl`. No id field
> (append-only, no need for lookups). No args/result capture (security).

**Insight [DONE]** (simplified):
```
{
  description: string,           # Natural language, dedup key
  category: "error_pattern" | "retry_pattern" | "recovery_pattern" |
            "usage_spike" | "best_practice" | "correction",
  evidence_count: int,
  tools: list[string],
  confidence: float (0-1),       # Computed by scorer.py
  impact: float (0-1),           # Computed by scorer.py
  combined: float (0-1),         # Weighted: 0.4*confidence + 0.6*impact
  first_seen: string | null,
  last_seen: string | null
}
```

> Stored as JSON array in `.acumen/insights.json`.

**Proposal [DONE]** (replaces ImprovementLog for Phase 1-2):
```
{
  description: string,
  rule_text: string,
  target: "rule" | "memory",
  status: "proposed" | "approved" | "rejected",
  created: string (ISO 8601)
}
```

> Stored as JSON array in `.acumen/proposals.json`.

**ImprovementLog [PLANNED]** -- full effectiveness tracking:
```
ImprovementLog {
  id: string (ulid)
  insight_id: string
  applied_at: datetime
  type: "rule" | "memory" | "hook" | "skill"
  before_state: string | null
  after_state: string
  status: "active" | "reverted"
  revert_reason: string | null
  effectiveness: {
    measured_after_n_sessions: int
    error_rate_before: float | null
    error_rate_after: float | null
    verdict: "effective" | "neutral" | "harmful" | "pending"
  }
}
```

### 3.3 The Learning Loop [DONE]

```
              +---> Observe session
              |          |
              |          v
              |     Collect observations
              |          |
              |          v
    +---------+    Extract insights (reflect)
    |                    |
    |                    v
    |              Score & rank insights
    |                    |
    |                    v
    |          Propose improvements
    |                    |
    |                    v
    |         [User review if needed]
    |                    |
    |                    v
    |           Apply improvement
    |                    |
    |                    v
    |          Measure effectiveness
    |                    |
    +---------<--- Keep or revert
```

**Safety tiers for auto-application:**

| Tier | Auto-apply? | Examples |
|------|-------------|----------|
| SAFE | Yes | Memory entries, session-scoped adaptations |
| REVIEW | User approval needed | CLAUDE.md rule additions, hook creation |
| MANUAL | Never auto-applied | Skill creation, global rule changes |

### 3.4 Observation Mechanism [DONE]

Observation is a shell hook (`hooks/observe.sh`) that fires on PostToolUse and
PostToolUseFailure events. Single jq pass, <5ms.

**What we observe today:**
- [DONE] Tool call outcomes (success/error + error_type + error_message)
- [DONE] Session ID and timestamp

**Planned observation expansion:**
- [PLANNED] User corrections ("no", "not that", "stop", "undo")
- [PLANNED] Retry patterns (same tool called 3+ times)
- [PLANNED] Test results (pass/fail counts, which tests)
- [PLANNED] Lint/type errors introduced
- [PLANNED] Files modified (to track code churn later)

**What we do NOT observe (privacy) -- this is permanent:**
- File contents (only tool_name and metadata)
- Tool input values or tool response content
- API keys, tokens, secrets
- Full conversation history

### 3.5 Reflection Engine [DONE]

The reflection engine runs on demand via `/acumen-reflect`, or is prompted
automatically via the flag-and-defer mechanism (SessionEnd sets flag,
SessionStart injects context suggesting the user run `/acumen-reflect`):

```
Input: Session observations
Process:
  1. Group observations by type and outcome
  2. Identify patterns:
     - Repeated failures with same tool/args
     - User corrections that follow a pattern
     - Quality signals trending in a direction
  3. Generate natural language insights (ExpeL-style)
  4. Compare against existing insights (dedup)
  5. Score by confidence (evidence count) and impact (severity)
Output: Ranked list of proposed improvements
```

**Reflection is an LLM call** that receives:
- Structured observation data (not raw conversation)
- Existing insights (to avoid duplicates)
- Current CLAUDE.md rules (to avoid conflicts)

The LLM generates insights as structured data, not free text.

### 3.6 Improvement Application [DONE]

Acumen uses Claude Code's native persistence systems with strict namespacing.
**Acumen NEVER modifies CLAUDE.md** -- that's the user's document.

```
Tiered persistence (research-grounded):

  Tier 1: RULES (.claude/rules/acumen-*.md) [DONE]
    - ALL insights become rules (corrections, patterns, best practices)
    - Loaded by Claude Code at session start or when path globs match
    - User can delete any rule file to override
    - Note: .claude/memory/acumen/ was dropped -- Claude Code does not
      read from project-local .claude/memory/ (only ~/.claude/projects/)

  Tier 2: HOOKS (Phase 3, requires explicit user opt-in)
    - Deterministic enforcement for code-verifiable rules
    - Zero instruction budget cost
    - Acumen never writes to user's settings.json

  NEVER: Auto-append to CLAUDE.md.
```

**Namespacing rules:**
- Rule files: `.claude/rules/acumen-<name>.md` (prefixed, easy to identify/delete)
- Memory files: `.claude/memory/acumen/<name>.md` (subdirectory, isolated)
- Acumen writes ONLY to paths it owns. Never modifies user files.

### 3.7 Effectiveness Measurement [PLANNED]

After applying an improvement, Acumen tracks whether it helped:

```
Improvement applied at time T
Wait for N sessions (configurable, default: 5)
Measure:
  - Did the target error/pattern recur?
  - Did overall error rate change?
  - Did the user revert the change?
Verdict:
  - effective: error rate decreased by >10%
  - neutral: no significant change
  - harmful: error rate increased or user reverted
Action:
  - effective: increase confidence, consider promoting scope
  - neutral: keep but flag for review
  - harmful: auto-revert, record why
```

---

## 4. User Experience

### 4.1 Installation [DONE]

Acumen is a pure Claude Code plugin. No pip install, no venv, no config files.

```bash
# From a local clone (development)
claude --plugin-dir /path/to/acumen

# Or, once published to the plugin registry [PLANNED]:
claude plugin add acumen
```

The `.acumen/` directory is created automatically on first tool use (the
observation hook creates `.acumen/observations/` as needed). No init command
required.

### 4.2 Day-to-Day Usage [DONE]

**Passive mode (default):** User works normally. Acumen observes silently.

**Active commands:**
- `/acumen-status` -- Show how many insights collected, improvements applied, trends
- `/acumen-reflect` -- Trigger reflection now (useful after a particularly good/bad session)
- `/acumen-insights` -- View all current insights with evidence
- `/acumen-review` -- Review and approve/reject pending improvements

### 4.3 The Dashboard [DONE — basic; trend metrics PLANNED]

```
+--------------------------------------------------+
|                ACUMEN STATUS                      |
+--------------------------------------------------+
| Scope: project (my-app)                           |
| Sessions observed: 47                             |
| Active insights: 12                               |
| Improvements applied: 8 (7 effective, 1 neutral)  |
|                                                   |
| Trends (last 7 days):                             |
|   Test pass rate:    92% -> 97% (+5%)             |
|   Corrections/session: 4.2 -> 1.8 (-57%)         |
|   Avg task time:     12m -> 8m (-33%)             |
|                                                   |
| Top insights:                                     |
|   1. [APPLIED] Always run type check before commit|
|   2. [APPLIED] Use pytest -x for faster feedback  |
|   3. [PROPOSED] Create skill for DB migration flow|
|   4. [PROPOSED] Add hook to lint on file save     |
+--------------------------------------------------+
```

### 4.4 Configuration [PLANNED]

No configuration file exists today. All behavior is hardcoded with sensible
defaults (observation threshold of 10, project scope only, all proposals require
user approval via `/acumen-review`).

A future `config.yaml` may be added if users need to customize behavior:

```yaml
# PLANNED -- not yet implemented
reflection:
  trigger: "session_end"
  min_observations: 10

scopes:
  global: true
  project: true
  session: true
```

For now, the only tunable is the `ACUMEN_REFLECT_THRESHOLD` environment variable
(default: 10), which controls how many new observations trigger the auto-reflect
flag.

---

## 5. Tech Stack [DONE]

- **Architecture:** Pure Claude Code plugin (zero external dependencies)
- **Observation:** Shell script (bash/jq) for hot path
- **Logic:** Python 3.11+ stdlib only (dataclasses, json, pathlib, uuid)
- **Storage:** JSONL files (no database)
- **Agent integration:** Claude Code plugin system (skills, hooks, commands, agents)
- **Testing:** pytest (dev dependency only)
- **Linting:** ruff (dev dependency only)

### 5.1 Why These Choices

- **Pure plugin** -- install is `claude plugin add acumen`. No pip, no venv, no version issues.
- **Shell observer** -- near-instant observation. Python cold start (50-200ms) would blow the <100ms budget.
- **Python stdlib only** -- dataclasses replace Pydantic, json replaces yaml, uuid replaces ulid. Zero dependencies.
- **JSONL files** -- append-only, human-readable, git-friendly, naturally handles concurrent writes.
- **No LLM SDK** -- reflection uses Claude Code's built-in subagent system. No API key needed.

### 5.2 Dependencies

**Runtime:** None. Zero. Python stdlib + bash/jq.

**Development only:** pytest, ruff (for testing and linting during development).

### 5.3 Research Grounding

| Decision | Research Backing |
|----------|-----------------|
| Shell observer (zero latency) | AutoResearch: constrain ruthlessly. No overhead = more experiments. |
| Metadata-only capture | DGM safety: systems encounter sensitive data. Minimal capture is safest. |
| Skill-based reflection | ExpeL: natural language insights from experience, no fine-tuning needed. |
| Three scopes | SAGE: memory decay matters. Not all learnings have the same shelf life. |
| Zero deps | AutoResearch: radical simplicity. One file, one metric. |
| Safety tiers | DGM: self-improving systems HACK their own reward functions. Human-in-the-loop. |

---

## 6. File Structure [DONE]

```
acumen/                              # Plugin root (this IS the repo)
  plugin.json                        # Plugin manifest
  README.md                          # Public-facing documentation
  CLAUDE.md                          # Development guidelines
  spec.md                            # This specification
  findings.md                        # Research findings

  skills/
    reflect.md                       # Reflection skill (invokes subagent)

  commands/
    status.md                        # /acumen-status command
    reflect.md                       # /acumen-reflect command
    insights.md                      # /acumen-insights command
    review.md                        # /acumen-review command

  hooks/
    observe.sh                       # PostToolUse observation (shell/jq)
    session-end.sh                   # Flag-and-defer: set should-reflect flag
    session-start.sh                 # Flag-and-defer: inject reflection prompt

  agents/
    reflector.md                     # Reflection analysis subagent

  lib/                               # Python scripts (stdlib only)
    store.py                         # JSONL file read/write + scope resolution
    scorer.py                        # Confidence/impact scoring + dedup
    formatter.py                     # Status/insight formatting for CLI output
    improver.py                      # Proposal generation + application

  tests/                             # Test suite (dev only)
    test_store.py
    test_scorer.py
    test_formatter.py
    fixtures/
      sample_observations.jsonl
```

---

## 7. Goals & Success Metrics

### 7.1 User-Facing Goals

1. **Install in under 2 minutes** -- `claude --plugin-dir /path/to/acumen`
2. **Zero mandatory configuration** -- works with defaults
3. **Measurable improvement within 1 week** -- user sees trends in `/acumen-status`
4. **No workflow disruption** -- passive by default, active only when invoked
5. **Full transparency** -- every improvement traceable to evidence

### 7.2 Technical Goals

1. **< 100ms overhead per tool call** -- observation must not slow down the agent
2. **< 500 lines of CLAUDE.md-injected context** -- stay within instruction budget
3. **Deterministic observation** -- no LLM calls in the hot path (observe)
4. **LLM-assisted reflection** -- reflection can use the host agent's LLM
5. **Safe by default** -- only SAFE tier auto-applies, everything else needs approval

### 7.3 Success Metrics (for Acumen itself)

- User correction rate per session decreases over time
- Test pass rate increases over time
- Code churn (reverted within 2 weeks) decreases over time
- Time-to-task-completion decreases over time
- User-initiated reverts of Acumen improvements < 10%

---

## 8. Phased Implementation

### Phase 1: Observe + Learn (MVP) [DONE]
- [DONE] Observation hooks (tool calls via shell hook)
- [DONE] Basic reflection (pattern detection, insight extraction via subagent)
- [DONE] Status command showing stats and top insights
- [DONE] JSONL file storage (observations) + JSON (insights, proposals)
- [DONE] Project scope only

### Phase 2: Improve [DONE — partial]
- [DONE] Tiered persistence (rules + memory, replaces CLAUDE.md managed section)
- [DONE] Memory entry generation (via improver.py)
- [DONE] User review flow (`/acumen-review`)
- [DONE] Proposal generation from insights
- [PLANNED] Effectiveness measurement (track whether improvements help)
- [PLANNED] Hook generation (REVIEW tier)

### Phase 3: Expand + Scopes [PLANNED]
- [PLANNED] Skill synthesis from successful patterns
- [PLANNED] Global scope (cross-project learnings)
- [PLANNED] Session scope (real-time adaptation)
- [PLANNED] Scope promotion/demotion
- [PLANNED] Plugin registry publishing

### Phase 4: Multi-Agent Support [DEFERRED]
- [DEFERRED] Codex adapter
- [DEFERRED] Gemini adapter
- [DEFERRED] Generic adapter interface
- [DEFERRED] Agent-agnostic observation format

---

## 9. Safety & Privacy

### 9.1 Safety Principles

1. **Human-in-the-loop for non-trivial changes** -- only SAFE tier auto-applies
2. **All improvements are reversible** -- every change recorded with before/after state
3. **No reward hacking** -- improvements measured against user behavior, not self-reported metrics
4. **Transparent operation** -- every insight shows its evidence
5. **Fail-open** -- if Acumen fails, the agent works normally without it

### 9.2 Privacy

1. **No conversation content stored** -- only structured events
2. **No file contents logged** -- only paths and metadata
3. **No network calls** -- all processing local
4. **No telemetry** -- zero data leaves the user's machine
5. **Secrets stripped** -- any observation containing potential secrets is redacted

---

## 10. Open Questions

1. ~~**How does reflection use the LLM?**~~ **[RESOLVED]** Via the host agent's subagent system. The reflector agent is dispatched by the reflect skill/command.
2. ~~**How do we handle CLAUDE.md instruction budget?**~~ **[RESOLVED]** Acumen never modifies CLAUDE.md. Uses path-scoped rules (.claude/rules/) and memory (.claude/memory/acumen/) instead.
3. **Cross-project skill transfer?** If a skill works well in one project, should it auto-suggest in others? [OPEN -- depends on global scope, Phase 3]
4. ~~**Observation granularity?**~~ **[RESOLVED]** Metadata only: tool_name, outcome, error_type, error_message. No args/results (security decision).
5. **Offline mode?** Should reflection work without an LLM (pure pattern matching)? [OPEN]

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

**OBSERVE:** Capture what happens during agent sessions.
- Hook into tool calls (pre/post)
- Track outcomes (success, failure, correction)
- Record user feedback (corrections, "no not that", "yes perfect")
- Measure code quality signals (test pass rate, lint errors, churn)

**LEARN:** Extract actionable insights from observations.
- Failure analysis: what went wrong and why (ExpeL-style)
- Success attribution: what worked and should be repeated
- Pattern detection: recurring mistakes, common corrections
- Quality trends: is the agent getting better or worse over time

**IMPROVE:** Apply learnings to make the agent better.
- Update CLAUDE.md rules (compounding engineering)
- Create/update memory entries (cross-session persistence)
- Generate hooks (deterministic enforcement of learned rules)
- Adjust agent behavior via context injection

**EXPAND:** Grow the agent's capabilities.
- Synthesize new skills from successful multi-step patterns (SkillWeaver-style)
- Create slash commands for recurring workflows
- Build reusable templates from successful sessions

### 2.2 Three Scopes

```
+----------------------------------------------------------+
|                     GLOBAL SCOPE                          |
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
|                    PROJECT SCOPE                          |
|  Learnings specific to a project's codebase & patterns   |
|  Storage: .acumen/ in project root                        |
|  Examples:                                                |
|    - "This project uses Pydantic v2, not v1"              |
|    - "Tests go in tests/, mirror source structure"        |
|    - Project-specific error patterns                      |
|    - CLAUDE.md rule suggestions                           |
+----------------------------------------------------------+
        |
+----------------------------------------------------------+
|                    SESSION SCOPE                          |
|  Within-conversation adaptation and reflection            |
|  Storage: in-memory (ephemeral)                           |
|  Examples:                                                |
|    - "User corrected my approach 3 times, adapt"          |
|    - Current task context and progress                    |
|    - Real-time quality monitoring                         |
+----------------------------------------------------------+
```

**Scope interaction rules:**
- Global rules are injected into all sessions as baseline context
- Project rules override global rules when they conflict
- Session learnings are candidates for promotion to project or global scope
- Promotion requires evidence (multiple occurrences, user validation)

---

## 3. Technical Design

### 3.1 Plugin Architecture (Claude Code First)

Acumen delivers as a Claude Code plugin:

```
acumen/                           # Plugin root
  plugin.json                     # Plugin manifest
  skills/
    observe.md                    # Observation skill
    reflect.md                    # Reflection/learning skill
    improve.md                    # Improvement application skill
  commands/
    acumen-status.md              # Show improvement status
    acumen-reflect.md             # Trigger manual reflection
    acumen-insights.md            # View current insights
    acumen-review.md              # Review & approve pending improvements
  hooks/
    post-tool-use.sh              # Observe tool outcomes
    pre-commit.sh                 # Quality gate before commits
    session-end.sh                # End-of-session reflection trigger
  agents/
    observer.md                   # Background observation agent
    reflector.md                  # Reflection/analysis agent
    improver.md                   # Improvement application agent
```

### 3.2 Data Model

```
Observation {
  id: string (ulid)
  timestamp: datetime
  scope: "session" | "project" | "global"
  type: "tool_call" | "correction" | "success" | "failure" | "feedback"
  context: {
    tool: string          # Which tool was called
    args: dict            # What arguments
    result: string        # What happened (truncated)
    outcome: "success" | "failure" | "corrected"
    user_feedback: string | null
  }
  session_id: string
  project: string
}

Insight {
  id: string (ulid)
  created: datetime
  scope: "session" | "project" | "global"
  type: "anti_pattern" | "best_practice" | "correction" | "skill_candidate"
  evidence: list[Observation.id]      # What observations support this
  confidence: float (0-1)             # How confident are we
  description: string                 # Natural language description
  action: {
    type: "claude_md_rule" | "memory_entry" | "hook" | "skill" | "none"
    content: string                   # The specific rule/hook/skill to create
    status: "proposed" | "approved" | "applied" | "reverted"
  }
  metrics: {
    occurrences: int                  # How many times observed
    impact: float                     # Estimated impact (0-1)
    last_seen: datetime
  }
}

ImprovementLog {
  id: string (ulid)
  insight_id: string
  applied_at: datetime
  type: "claude_md_rule" | "memory_entry" | "hook" | "skill"
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

### 3.3 The Learning Loop

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

### 3.4 Observation Mechanism

Claude Code plugins support hooks that fire on tool use:

```yaml
# PostToolUse hook: observe outcomes
hooks:
  post_tool_use:
    - event: "tool_result"
      script: "acumen observe"
      # Captures: tool name, args, result, duration
      # Detects: failures, corrections, retries
```

**What we observe (non-exhaustive):**
- Tool call outcomes (success/failure/error type)
- User corrections ("no", "not that", "stop", "undo")
- Retry patterns (same tool called 3+ times)
- Test results (pass/fail counts, which tests)
- Lint/type errors introduced
- Files modified (to track code churn later)
- Time between task start and completion

**What we do NOT observe (privacy):**
- File contents (only paths and metadata)
- API keys, tokens, secrets
- Full conversation history (only structured events)

### 3.5 Reflection Engine

The reflection engine runs at session end (or on demand via `/acumen-reflect`):

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

### 3.6 Improvement Application

Each improvement type has a specific mechanism:

**CLAUDE.md rules:**
- Appended to a managed section at the bottom of CLAUDE.md
- Section is clearly marked: `<!-- acumen:managed:start -->` ... `<!-- acumen:managed:end -->`
- User can edit/remove any rule manually
- Acumen never modifies user-written rules above the managed section

**Memory entries:**
- Written to the Claude Code memory system (`.claude/memory/`)
- Follow the standard memory format with frontmatter
- Tagged with `source: acumen` for traceability

**Hooks:**
- Generated as shell scripts in `.claude/hooks/`
- Always proposed as REVIEW tier (user must approve)
- Include comments explaining what the hook does and why

**Skills:**
- Generated as `.md` files in `.claude/skills/`
- Always proposed as MANUAL tier
- Include the evidence that motivated the skill

### 3.7 Effectiveness Measurement

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

### 4.1 Installation

```bash
# One command install
pip install acumen

# Initialize in a project
cd my-project
acumen init
# Creates .acumen/ directory
# Adds managed section to CLAUDE.md
# Sets up hooks
```

Or as a Claude Code plugin:
```bash
claude plugin add acumen
```

### 4.2 Day-to-Day Usage

**Passive mode (default):** User works normally. Acumen observes silently.

**Active commands:**
- `/acumen-status` -- Show how many insights collected, improvements applied, trends
- `/acumen-reflect` -- Trigger reflection now (useful after a particularly good/bad session)
- `/acumen-insights` -- View all current insights with evidence
- `/acumen-review` -- Review and approve/reject pending improvements

### 4.3 The Dashboard

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

### 4.4 Configuration

Minimal configuration required. One file: `.acumen/config.yaml`

```yaml
# Acumen configuration (all optional, these are defaults)
auto_apply:
  safe: true          # Auto-apply SAFE tier improvements
  review: false       # Require approval for REVIEW tier
  manual: false       # Never auto-apply MANUAL tier

reflection:
  trigger: "session_end"    # When to reflect
  min_observations: 5       # Min observations before reflecting

observation:
  track_tool_calls: true
  track_corrections: true
  track_test_results: true
  track_lint_errors: true

scopes:
  global: true        # Enable global scope
  project: true       # Enable project scope
  session: true       # Enable session scope
```

---

## 5. Tech Stack

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

## 6. File Structure

```
acumen/                              # Plugin root (this IS the repo)
  plugin.json                        # Plugin manifest
  README.md                          # Public-facing documentation
  CLAUDE.md                          # Development guidelines
  CAPABILITIES.md                    # Capability registry
  spec.md                            # This specification
  findings.md                        # Research findings

  skills/
    reflect.md                       # Reflection skill (invokes subagent)

  commands/
    status.md                        # /acumen-status command
    reflect.md                       # /acumen-reflect command
    insights.md                      # /acumen-insights command

  hooks/
    observe.sh                       # PostToolUse observation (shell/jq)

  agents/
    reflector.md                     # Reflection analysis subagent

  lib/                               # Python scripts (stdlib only)
    store.py                         # JSONL file read/write + scope resolution
    scorer.py                        # Confidence/impact scoring + dedup
    formatter.py                     # Status/insight formatting for CLI output

  tests/                             # Test suite (dev only)
    conftest.py                      # Shared fixtures
    test_store.py
    test_scorer.py
    test_formatter.py
    test_observe_hook.py             # Integration test for shell hook
    test_integration.py              # Full pipeline test
    fixtures/
      sample_observations.jsonl
      sample_insights.json
```

---

## 7. Goals & Success Metrics

### 7.1 User-Facing Goals

1. **Install in under 2 minutes** -- `pip install acumen && acumen init`
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

### Phase 1: Observe + Learn (MVP)
- Observation hooks (tool calls, corrections, test results)
- Basic reflection (pattern detection, insight extraction)
- Status command showing trends
- JSON file storage
- Project scope only

### Phase 2: Improve
- CLAUDE.md managed section
- Memory entry generation
- Effectiveness measurement
- User review flow (`/acumen-review`)
- Hook generation (REVIEW tier)

### Phase 3: Expand + Scopes
- Skill synthesis from successful patterns
- Global scope (cross-project learnings)
- Session scope (real-time adaptation)
- Scope promotion/demotion
- Plugin packaging for easy distribution

### Phase 4: Multi-Agent Support
- Codex adapter
- Gemini adapter
- Generic adapter interface
- Agent-agnostic observation format

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

1. **How does reflection use the LLM?** Via the host agent's plugin system (skill invocation) or a separate lightweight model?
2. **How do we handle CLAUDE.md instruction budget?** Acumen's managed section must be concise -- what's the max line count?
3. **Cross-project skill transfer?** If a skill works well in one project, should it auto-suggest in others?
4. **Observation granularity?** How much detail per tool call -- just outcome, or include args/results?
5. **Offline mode?** Should reflection work without an LLM (pure pattern matching)?

# Acumen

A Claude Code plugin that makes your AI coding agent self-improving. Acumen silently observes your sessions, learns from patterns and mistakes, and applies corrective rules that make the agent better over time. It measures whether each rule actually helped. Zero external dependencies. Install, work normally, get better results.

## How It Works

```
OBSERVE ──> LEARN ──> IMPROVE ──> MEASURE
  │            │          │           │
  │            │          │           └─ Before/after error rate tracking
  │            │          │              Effective / neutral / harmful verdicts
  │            │          │
  │            │          └─ Path-scoped rules (.claude/rules/acumen-*.md)
  │            │             Global promotion for proven universal rules
  │            │
  │            ├─ Pattern detection (error, retry, recovery)
  │            ├─ Confidence/impact scoring with recency weighting
  │            └─ Dedup against existing rules
  │
  ├─ PostToolUse hook (pure bash, <20ms)
  └─ Metadata only (tool_name, outcome, error_type, error_message)
```

Every tool call is observed. When enough data accumulates, Acumen flags that reflection is due. At next session start, the agent reflects, extracts insights, scores them, generates improvement proposals, and auto-applies safe ones -- then notifies you. Run `/acumen-review` to see what was applied or revert anything.

## Installation

```bash
# Local clone (development)
claude --plugin-dir /path/to/acumen
```

No pip, no venv, no config files. The `.acumen/` directory is created automatically on first use.

## Usage

Acumen runs passively in the background. Four commands give you control:

### `/acumen-status`

Shows observation stats, error rates, and top insights.

```
ACUMEN STATUS
  Sessions observed: 12
  Total observations: 847
  Error rate: 8%
  Active insights: 5
  Top insights:
    - [0.72] Use python3 instead of python -- exit code 127
    - [0.58] Run tests before committing to catch regressions
```

### `/acumen-reflect`

Triggers the reflector subagent to analyze recent observations and extract insights. Run this after a few sessions, or let auto-reflection remind you.

### `/acumen-insights`

Lists all extracted insights ranked by confidence and impact score.

### `/acumen-review`

Shows all auto-applied improvements with effectiveness verdicts. Revert any you disagree with. Promote proven rules to global scope (applies across all your projects).

## Auto-Reflection

Acumen uses a flag-and-defer mechanism -- no LLM calls happen in the hot path:

1. **SessionEnd hook** counts new observations since last reflection
2. If the count exceeds the threshold (default: 10), it writes a `.acumen/should-reflect` flag
3. **SessionStart hook** checks for the flag. If present, it injects context telling the agent to run reflection, auto-apply proposals, and notify you
4. On normal session starts (no flag), Acumen shows a brief summary: "Acumen: N active rule(s) improving your agent"

Run `/acumen-review` afterward to see what changed or undo anything. Set `ACUMEN_REFLECT_THRESHOLD` to change the observation threshold.

## What It Observes

Acumen captures **metadata only** from every tool call:

| Field | Example |
|-------|---------|
| `tool_name` | `"Bash"`, `"Edit"`, `"Read"` |
| `outcome` | `"success"` or `"error"` |
| `error_type` | `"tool_failure"`, `"tool_error"`, or `null` |
| `error_message` | `"exit code 127"` (from failures only) |
| `session_id` | Session identifier |
| `timestamp` | ISO 8601 UTC |

**What Acumen never captures:**
- Tool input values (commands, file contents, code)
- Tool response content
- API keys, tokens, or secrets
- Conversation history

This is a security decision, not a limitation. Self-improving systems encounter sensitive data. Minimal capture is safest. See [findings.md](findings.md) for the research behind this.

## Effectiveness Measurement

Acumen tracks whether applied rules actually work:

- After a rule is applied, it monitors the target tool's error rate
- With enough data (5+ observations before and after), it produces a verdict:
  - **Effective**: error rate dropped >10%
  - **Neutral**: no significant change
  - **Harmful**: error rate increased (should be reverted)
- Effective rules can be promoted to global scope (`~/.claude/rules/`) via `/acumen-review`

## Architecture

```
acumen/
  plugin.json              # Plugin manifest (hooks, metadata)
  skills/
    reflect.md             # Reflection skill (invokes subagent)
  commands/
    status.md              # /acumen-status
    reflect.md             # /acumen-reflect
    insights.md            # /acumen-insights
    review.md              # /acumen-review
  hooks/
    observe.sh             # PostToolUse observation (pure bash, <20ms)
    session-end.sh         # Flag-and-defer: set should-reflect
    session-start.sh       # Flag-and-defer: inject reflection prompt
  agents/
    reflector.md           # Reflection analysis subagent
  lib/
    store.py               # JSONL read/write, scope resolution
    scorer.py              # Confidence/impact scoring, validation, dedup
    formatter.py           # CLI display formatting
    improver.py            # Proposal generation, application, effectiveness
```

**Zero external dependencies.** Python stdlib only (json, pathlib, dataclasses). Shell hooks use pure bash. No pip packages, no jq, no database, no network calls, no telemetry.

**Data storage:**
- `.acumen/observations/YYYY-MM-DD.jsonl` -- append-only observation logs
- `.acumen/insights.json` -- extracted insights with scores
- `.acumen/proposals.json` -- improvement proposals with status and effectiveness
- `.claude/rules/acumen-*.md` -- auto-applied corrective rules (what Claude Code reads)

## Research Grounding

Acumen's design is informed by recent research on self-improving AI agents:

- **ExpeL** (AAAI 2024) -- natural language insights from experience, no fine-tuning
- **Darwin Godel Machine** (Sakana AI) -- safety tiers, because self-improving systems hack their rewards
- **AutoResearch** (Karpathy) -- constrain ruthlessly, one metric, git-as-memory
- **SAGE** -- memory decay matters, not all learnings have the same shelf life
- **SkillWeaver** -- skill synthesis from successful patterns (Phase 3)

Full survey and citations in [findings.md](findings.md). Design specification in [spec.md](spec.md).

## Safety

- **Reviewable**: All auto-applied improvements visible via `/acumen-review`, instantly revertible
- **Measured**: Every rule tracked for effectiveness (effective/neutral/harmful)
- **Metadata only**: Never captures tool inputs, file contents, or secrets
- **Namespaced**: Only writes to `acumen-*` prefixed files in `.claude/rules/`
- **Never modifies CLAUDE.md**: That's your document
- **Fail-open**: If Acumen crashes, your agent works normally
- **Reversible**: Delete any `acumen-*` rule file to undo an improvement
- **No network**: Everything runs locally. Zero data leaves your machine

## License

MIT

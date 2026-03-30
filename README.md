# Acumen

A Claude Code plugin that makes your AI coding agent self-improving. Acumen silently observes your sessions, extracts patterns from failures and successes, and proposes concrete improvements -- rules and memory entries that make the agent better over time. Zero external dependencies. Install, work normally, get better results.

## How It Works

```
OBSERVE ──> LEARN ──> IMPROVE
  │            │          │
  │            │          ├─ Path-scoped rules (.claude/rules/)
  │            │          └─ Memory entries (.claude/memory/acumen/)
  │            │
  │            ├─ Pattern detection (error, retry, recovery)
  │            └─ Confidence/impact scoring + dedup
  │
  ├─ PostToolUse hook (shell, <5ms)
  └─ Metadata only (tool_name, outcome, error_type)
```

Every tool call is observed. When enough data accumulates, Acumen flags that reflection is due. You run `/acumen-reflect`, a subagent analyzes the observations, extracts insights, and generates improvement proposals. You review and approve them with `/acumen-review`. Approved rules are written to `.claude/rules/` and `.claude/memory/acumen/` where Claude Code picks them up automatically.

## Installation

```bash
# Local clone
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

Reviews pending improvement proposals. For each proposal, you approve or reject. Approved proposals become:
- **Rules** (`.claude/rules/acumen-*.md`) -- corrections like "use python3 not python"
- **Memory** (`.claude/memory/acumen/*.md`) -- general insights and preferences

## Auto-Reflection

Acumen uses a flag-and-defer mechanism -- no LLM calls happen automatically:

1. **SessionEnd hook** counts new observations since last reflection
2. If the count exceeds the threshold (default: 10), it writes a `.acumen/should-reflect` flag
3. **SessionStart hook** checks for the flag. If present, it injects a message suggesting you run `/acumen-reflect`
4. You decide when to reflect. The agent never runs reflection without you.

Set `ACUMEN_REFLECT_THRESHOLD` to change the observation threshold.

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
    observe.sh             # PostToolUse observation (<5ms, bash+jq)
    session-end.sh         # Flag-and-defer: set should-reflect
    session-start.sh       # Flag-and-defer: inject reflection prompt
  agents/
    reflector.md           # Reflection analysis subagent
  lib/
    store.py               # JSONL read/write, scope resolution
    scorer.py              # Confidence/impact scoring, dedup
    formatter.py           # CLI display formatting
    improver.py            # Proposal generation + application
```

**Zero external dependencies.** Python stdlib only (json, pathlib, dataclasses). Shell hooks use bash + jq. No pip packages, no database, no network calls, no telemetry.

**Data storage:**
- `.acumen/observations/YYYY-MM-DD.jsonl` -- append-only observation logs
- `.acumen/insights.json` -- extracted insights with scores
- `.acumen/proposals.json` -- improvement proposals pending review

## Research Grounding

Acumen's design is informed by recent research on self-improving AI agents:

- **ExpeL** (AAAI 2024) -- natural language insights from experience, no fine-tuning
- **Darwin Godel Machine** (Sakana AI) -- safety tiers, because self-improving systems hack their rewards
- **AutoResearch** (Karpathy) -- constrain ruthlessly, one metric, git-as-memory
- **SAGE** -- memory decay matters, not all learnings have the same shelf life

Full survey and citations in [findings.md](findings.md). Design specification in [spec.md](spec.md).

## Safety

- **Human-in-the-loop**: All improvement proposals require explicit approval via `/acumen-review`
- **Metadata only**: Never captures tool inputs, file contents, or secrets
- **Namespaced writes**: Only writes to `acumen-*` prefixed files in `.claude/rules/` and `.claude/memory/acumen/`
- **Never modifies CLAUDE.md**: That's your document
- **Fail-open**: If Acumen crashes, your agent works normally
- **Reversible**: Delete any `acumen-*` rule file to undo an improvement
- **No network**: Everything runs locally. Zero data leaves your machine

## License

MIT

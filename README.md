# Acumen

**Turn your generalist AI into a specialist in your project.**

Your AI coding agent starts every session from zero. It doesn't remember your test runner, your file conventions, or the mistakes it made yesterday. The model gets smarter once a quarter when the provider ships an update. Your agent never learns YOUR project.

Acumen changes that. Install it, work normally, and your agent goes through the same learning curve a new hire would — but in days, not months. It observes tool outcomes, clusters repeated failures, extracts your project's operational conventions, and proposes structured rules for your approval. Every improvement cites its evidence. Every change is reversible.

```
OBSERVE ──> LEARN ──> PROPOSE ──> [APPROVE] ──> APPLY
   │                                               │
   └──────────── MEASURE EFFECTIVENESS <───────────┘
```

## What It Looks Like

After two weeks with Acumen:

```
┌──────────────────────────────────────────────────────────────┐
│                       ACUMEN REPORT                           │
│                       my-project (14 days)                    │
│                                                               │
│  YOUR AGENT IS SPECIALIZING                                   │
│                                                               │
│  Failures reduced:                                            │
│    "python command_not_found"                                 │
│      Before: 9.4 per 100 python calls                         │
│      After:  0.4 per 100 python calls    ↓ 96%               │
│      Rule: "Use python3 instead of python"                    │
│                                                               │
│    "Edit file_not_found"                                      │
│      Before: 4.6 per 100 Edit calls                           │
│      After:  1.6 per 100 Edit calls      ↓ 65%               │
│      Rule: "Verify file exists before Edit tool"              │
│                                                               │
│  Conventions learned:                                         │
│    test_command: "pytest -v"          adherence: 100%         │
│    file_naming: "snake_case"          adherence: 94%          │
│    test_placement: "tests/ mirror"    adherence: 89%          │
│                                                               │
│  5 rules active │ 4 approved, 1 pending │ 0 reverted         │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

## Installation

```bash
# Local clone (development)
claude plugin add /path/to/acumen

# From marketplace (coming soon)
claude plugin add acumen
```

No pip, no venv, no config files. Zero external dependencies. The `.acumen/` directory is created automatically on first use.

## How It Works

**Observation (automatic, silent):** Every tool call fires a hook. The hook classifies the event into categorical metadata (command family, file basename, error class) and discards the raw data. Only derived categories are persisted — never raw commands, file contents, or conversation text.

**Learning (triggered after enough observations):** The reflection engine clusters repeated failures, detects operational conventions from success patterns, and generates structured proposals with cited evidence.

**Proposals (require your approval):** Every behavioral change needs your explicit approval via `/acumen-review`. Acumen never silently modifies how your agent behaves.

**Measurement (automatic):** After you approve a rule, Acumen tracks whether the targeted failure class actually decreases, with explicit denominators to prevent false positives.

## Commands

| Command | Purpose |
|---------|---------|
| `/acumen-status` | Quick health: observations, proposals, active rules |
| `/acumen-reflect` | Trigger reflection now |
| `/acumen-review` | Review and approve/reject pending proposals |
| `/acumen-report` | Detailed report: failure reduction, convention adherence |

## Privacy & Safety

**What Acumen captures (Tier 0.5 — default):**

| Field | Example | Purpose |
|-------|---------|---------|
| `tool_name` | `"Bash"`, `"Edit"` | What tool was used |
| `outcome` | `"success"`, `"error"` | Did it work |
| `command_family` | `"python"`, `"test"` | Category, not the command |
| `command_signature` | `"pytest"`, `"ruff_check"` | Test/lint runner, not args |
| `file_basename` | `"test_store.py"` | Filename only, no directory |
| `error_class` | `"command_not_found"` | Classified, not raw message |

**What Acumen never captures:** Raw commands, file contents, full file paths, conversation text, API keys, secrets, tool input/output content.

The hook reads raw data transiently to classify it, then discards the raw data — persisting only derived categories. Nothing ever leaves your machine.

**Safety guarantees:**
- All behavioral mutations require your approval (no auto-apply in v1)
- Every improvement is reversible (delete the rule file)
- Effectiveness tracked with explicit denominators (no vanity metrics)
- Fail-open: if Acumen crashes, your agent works normally
- Namespaced: only writes to `acumen-*` files in `.claude/rules/`
- Never modifies CLAUDE.md
- Zero network calls, zero telemetry

## Research Grounding

Every architectural decision in Acumen maps to published research on self-improving AI agents. This isn't theoretical — these are proven techniques with demonstrated results.

### Foundation: The Scaffold Is the Lever

The core thesis: **improving the scaffold around a frozen model achieves 30-250% performance improvement without changing model weights.** Every major system in 2025-2026 independently proved this:

| System | What It Improved | Result | Source |
|--------|-----------------|--------|--------|
| Darwin Godel Machine | Agent scaffold code | +30 points on SWE-bench | [Sakana AI, 2025](https://arxiv.org/abs/2505.22954) |
| Live-SWE-agent | Runtime tools | +22.6%, $0 offline cost | [arXiv:2511.13646](https://arxiv.org/abs/2511.13646) |
| AutoResearch | Training code (one file) | 11% speedup overnight | [Karpathy, 2026](https://github.com/karpathy/autoresearch) |
| MiniMax M2.7 | Scaffold + sampling params | 30% improvement | [MiniMax, 2026](https://www.minimax.io/news/minimax-m27-en) |
| ARTEMIS | Prompts + tools + params | 10.1% improvement | [arXiv:2512.09108](https://arxiv.org/abs/2512.09108) |
| OpenSpace | Skill library | 4.2x on professional tasks | [HKUDS, 2026](https://github.com/HKUDS/OpenSpace) |
| DGM-Hyperagents | The improvement process itself | Cross-domain transfer | [arXiv:2603.19461](https://arxiv.org/abs/2603.19461) |

Acumen improves your agent's scaffold: its rules, conventions, and operational knowledge. Same principle, applied to your specific project.

### Current Features — Research Backing

| What Acumen Does | Research Source | Key Finding |
|---|---|---|
| **Observe tool outcomes** | [ExpeL](https://arxiv.org/abs/2308.10144) (AAAI 2024 Oral) | Extracting natural language insights from experience works without fine-tuning. API-only models can self-improve through in-context learning. |
| **Learn from failures** | [MiniMax M2.7](https://www.minimax.io/news/minimax-m27-en), [DGM](https://arxiv.org/abs/2505.22954) | Failure trajectory analysis is the primary improvement signal. M2.7's biggest gains came from analyzing WHY things failed. |
| **Learn from successes** | [ExpeL](https://arxiv.org/abs/2308.10144) | Learning from both success AND failure produces dramatically better agents than failure alone. Success patterns encode conventions. |
| **Classify, don't capture** | [DGM safety research](https://arxiv.org/abs/2505.22954) | Self-improving systems encounter sensitive data. The DGM paper documented agents gaming evaluations and accessing unintended data. Minimal capture is a security requirement. |
| **Require approval for changes** | [DGM](https://arxiv.org/abs/2505.22954) | Self-improving agents WILL hack their reward functions. The DGM paper explicitly documented this: agents fabricated tool logs and tried to bypass safety checks. Human-in-the-loop is non-negotiable. |
| **Measure with verifiable signals** | [Absolute Zero Reasoner](https://arxiv.org/abs/2505.03335) (NeurIPS 2025 Spotlight) | Code execution as ground truth beats LLM self-evaluation. Verifiable rewards eliminate reward hacking. Acumen uses tool exit codes and error rates, not LLM judgment. |
| **Structured contradiction detection** | [ARTEMIS](https://arxiv.org/abs/2512.09108) | Joint optimization of multiple components requires conflict awareness. Optimizing prompts + tools + params together outperforms any single component. |
| **Lightweight reflection** | [Live-SWE-agent](https://arxiv.org/abs/2511.13646) | A single reflection prompt ("would a tool help?") is enough to drive real improvement. Complex meta-learning is unnecessary. 79.2% on SWE-bench with zero offline cost. |
| **Traceable experiment history** | [AutoResearch](https://github.com/karpathy/autoresearch) | Git-tracked experiment logs: every change is a commit, every improvement is traceable and reversible. Radical simplicity (one file, one metric) outperforms complex setups. |

### Planned Features — Research Backing

| Planned Feature | Phase | Research Source | What the Research Proved |
|---|---|---|---|
| **Before/after baseline comparison** | 2 | [AZR](https://arxiv.org/abs/2505.03335) | Verifiable environment signals (code execution equality) are the gold standard for evaluating improvements. Binary pass/fail eliminates subjective judgment. |
| **Code-structure convention learning** | 2 | [SkillWeaver](https://arxiv.org/abs/2504.07079) | Agents can extract transferable skills/patterns from observed behavior. SkillWeaver achieved 31.8% improvement on WebArena. Skills from strong agents transfer to weak agents (+54.3%). |
| **Diverse improvement archive** | 3 | [DGM](https://arxiv.org/abs/2505.22954), [DGM-Hyperagents](https://arxiv.org/abs/2603.19461) | Maintaining a diverse population of solutions (not just the "best" one) enables stepping-stone discoveries and avoids local optima. Greedy hillclimbing consistently underperforms archive-based search. |
| **Skill synthesis from workflows** | 3 | [SkillWeaver](https://arxiv.org/abs/2504.07079), [Voyager](https://arxiv.org/abs/2305.16291), [OpenSpace](https://github.com/HKUDS/OpenSpace) | Ever-growing skill libraries are the foundation of self-improving agents. Voyager's skill library pattern has become foundational — nearly every modern self-improving system uses it. |
| **Meta-improvement** | 3 | [DGM-Hyperagents](https://arxiv.org/abs/2603.19461) | The improvement process itself can be made editable. Hyperagents improved not just task performance but the mechanism that generates improvements. Meta-level gains transfer across domains and compound over time. |
| **Automatic difficulty calibration** | 3+ | [AZR](https://arxiv.org/abs/2505.03335) | The proposer-solver loop naturally generates tasks at the frontier of the solver's ability. Acumen can weight insights by how "at the frontier" they are — patterns the agent sometimes gets right and sometimes doesn't. |
| **Multi-agent support** | 4 | [Self-Evolving Agents Survey](https://arxiv.org/abs/2507.21046) | The WHAT-WHEN-HOW taxonomy applies to any agent: what evolves (rules, skills, tools), when (inter-session), how (reward-based from verifiable signals). The abstraction is domain-agnostic. |
| **Cross-domain transfer** | 4+ | [DGM-Hyperagents](https://arxiv.org/abs/2603.19461) | Meta-improvements transfer across domains (coding → paper review → robotics → math). An improvement engine trained on coding agents could improve agents in any domain. |
| **Memory consolidation** | 3+ | [Anthropic Auto-Dream](https://claudefa.st/blog/guide/mechanics/auto-dream), [Sleep-time Compute](https://arxiv.org/abs/2504.13171) | Background computation during idle time pre-organizes information, reducing test-time compute by ~5x. Memory hygiene (pruning stale/contradictory knowledge) is a prerequisite for effective self-improvement. |
| **Population-based exploration** | Future | [ERL-Re2](https://arxiv.org/abs/2210.17375), [DERL](https://arxiv.org/abs/2512.13399) | Evolutionary + reinforcement learning hybrid search maintains population diversity while exploiting gradient-based optimization. Population diversity is load-bearing. |
| **Elo tournament for ranking** | Future | [Google AI Co-Scientist](https://arxiv.org/abs/2502.18864) | Elo-based pairwise comparison scales hypothesis ranking without requiring absolute quality scores. Simulated debates between candidates surface quality differences. |

### The Gap Nobody Fills

The market has observability (Braintrust, Arize), memory (Mem0), and evaluation (Braintrust, Maxim) as separate products. **Nobody closes the loop:** observe → learn → propose → approve → apply → measure. The companies that observe don't improve. The coding agents that execute don't learn.

Acumen closes the loop.

### Further Reading

- [DGM Paper](https://arxiv.org/abs/2505.22954) — The foundational paper on self-improving coding agents
- [ExpeL Paper](https://arxiv.org/abs/2308.10144) — Learning from experience without fine-tuning
- [AZR Paper](https://arxiv.org/abs/2505.03335) — Zero-data self-improvement via verifiable rewards
- [Self-Evolving Agents Survey](https://arxiv.org/abs/2507.21046) — Comprehensive taxonomy of the field

## Architecture

```
acumen/
  plugin.json              # Plugin manifest
  skills/
    reflect.md             # Reflection skill
  commands/
    status.md              # /acumen-status
    reflect.md             # /acumen-reflect
    review.md              # /acumen-review
    report.md              # /acumen-report
  hooks/
    observe.sh             # Tier 0.5 observation (classify → discard raw)
    session-end.sh         # Flag-and-defer: set should-reflect
    session-start.sh       # Inject reflection prompt
  agents/
    reflector.md           # Reflection subagent
  lib/
    classify.py            # Tier 0.5 field derivation
    store.py               # Per-session JSONL, index, rotation
    cluster.py             # Failure clustering with guardrails
    propose.py             # Proposal generation + contradiction detection
    apply.py               # Rule application + revert
    measure.py             # Effectiveness tracking
    format.py              # CLI output formatting
```

**Zero external dependencies.** Python 3.11+ stdlib only. No pip packages, no database, no network calls, no telemetry.

## License

MIT

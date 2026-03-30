# Acumen v1.0 Design Spec

**Date:** 2026-03-30
**Status:** Approved for implementation
**Scope:** v0.3 (trust layer) through v1.0 (skill synthesis + evolution engine)

---

## 1. North Star

Every self-improving AI system that works -- AutoResearch, Darwin Gödel Machine, MiniMax M2.7, SICA, GEA -- does the same thing: propose a mutation, evaluate it against an immutable metric, keep or revert. Nobody has packaged this as a harness that plugs into the coding agent you already use.

**Acumen is that harness.**

What gets mutated escalates over time. That escalation IS the roadmap:

```
Layer 1: LEARN FROM MISTAKES   (self-improving)  -- v0.2 mostly shipped
Layer 2: EVOLVE STRATEGY        (self-evolving)   -- v1.0
Layer 3: ACQUIRE SKILLS         (self-expanding)  -- v1.x
Layer 4: MODIFY OWN SCAFFOLD    (power growth)    -- v2.0
```

Each layer builds on the trust foundation of the layer below it. You cannot evolve strategy without verified learning. You cannot self-modify safely without all lower layers working. Note: within v1.0, Skills (Layer 3) ships before Evolution (Layer 2) because skills give the evolution loop a richer mutation space from day one -- both use the same trust layer foundation.

The version story:
- **v0.3** -- Trust layer: "Your agent can't lie to you anymore."
- **v1.0** -- Skills + Evolution: "Your agent optimized its own instructions overnight."
- **v2.0** -- Scaffold self-modification: "The harness that improves itself."

---

## 2. What exists today (v0.2)

### Shipped capabilities

**Observation pipeline**
- PostToolUse + PostToolUseFailure hooks capture metadata from every tool call
- Pure bash, <20ms per observation, zero external dependencies
- Data captured: tool_name, session_id, timestamp, outcome, error_type, error_message
- Storage: `.acumen/observations/YYYY-MM-DD.jsonl` (append-only, 7-day read window)

**Learning pipeline**
- Reflector subagent analyzes observations for patterns (error, retry, recovery, usage spike)
- 3+ supporting observations required per insight
- Confidence/impact scoring with recency-weighted exponential decay (3-day half-life)
- Deduplication by description match
- Storage: `.acumen/insights.json`

**Improvement pipeline**
- Proposal generation from insights (all insights become rule candidates)
- Auto-apply with status tracking (proposed → auto-applied → effective/reverted)
- Effectiveness measurement: before/after error rate comparison
- `/acumen-review` with revert capability
- Global scope promotion to `~/.claude/rules/acumen-*.md`
- 30-day TTL expiry

**Commands:** `/acumen-status`, `/acumen-reflect`, `/acumen-insights`, `/acumen-review`

### Architecture constraints (non-negotiable)

- **Zero external dependencies.** Python stdlib only. Shell hooks use pure bash.
- **Plugin architecture.** Installed via `claude plugin add`. Everything declared in `plugin.json`.
- **Metadata only.** Never captures tool input, tool response, file contents, or conversation.
- **JSONL storage.** Append-only observation logs, JSON for structured state.
- **Fail-open everywhere.** Acumen crashing never breaks the agent.
- **Namespaced writes.** Only writes to `acumen-*` prefixed files. Never modifies `CLAUDE.md`.

---

## 3. Research grounding

### The universal ratchet pattern

```
PROPOSE mutation → EVALUATE against immutable metric → KEEP or REVERT → REPEAT
```

| System | What it mutates | Evaluation signal | Keep/revert |
|--------|----------------|-------------------|-------------|
| AutoResearch | train.py (one file) | val_bpb (scalar) | git reset HEAD~1 |
| DGM | Agent Python codebase | SWE-bench score | Archive tree |
| SICA | Own codebase | SWE-bench + cost + time | Best-from-archive |
| MiniMax M2.7 | Memory, skills, scaffold | Internal eval suite | Compare + revert |
| GEPA/DSPy | Prompts/instructions | Task pass rate | Pareto frontier |
| Voyager | Skill library | GPT-4 critic + state | Verified skills only |
| ERL | Heuristic pool | Task success rate | Selective retrieval |

### Five invariant patterns

1. **Propose, evaluate, keep/revert.** The mechanism varies; the structure is invariant.
2. **Constrained mutation space.** AutoResearch: one file. DGM: scaffold only. Unconstrained mutation leads to reward hacking.
3. **External verification.** Every system relying on self-assessment alone exhibits capability hallucination.
4. **Persistent memory.** Without it, agents repeat the same mistakes.
5. **Diversity maintenance.** DGM's archive, GEPA's Pareto frontier, GEA's group sharing all outperform greedy single-best.

### Key research findings that shape this design

- **SICA:** Biggest gain was a new tool (AST locator, +10%), not a prompt rewrite. Tools > prompts. Skills > rules.
- **ERL:** Failure heuristics outperform success heuristics on search tasks (+14.3%). Retrieval quality > library size.
- **SlopCodeBench:** Prompt-side interventions shift the starting intercept but NOT the degradation slope. Rules alone hit a ceiling.
- **Voyager:** Compositional skill building creates exponential capability growth.
- **AutoResearch:** The evaluation function (prepare.py) MUST be immutable. The agent cannot modify its own test.
- **ResearchEnvBench:** Agents exhibit capability hallucination. External verification is mandatory.
- **SAGE:** Memory decay with forgetting curves prevents context pollution.

---

## 4. The evaluation signal

### The critical constraint

The evaluation criterion must be immutable and external to Acumen. Acumen can mutate rules, skills, reflection prompts. It can **never** mutate the evaluation function. The test suite is written by the user. The lint config is owned by the user. This is the `prepare.py` / `train.py` boundary that makes AutoResearch work.

### Tiered evaluation (auto-detected at `acumen init`)

Acumen detects available signals and locks in the strongest evaluation function for the project.

| Tier | Signal | Detection | Confidence |
|------|--------|-----------|------------|
| 1 (strongest) | Test suite | pytest, jest, go test, cargo test, etc. | HIGH |
| 2 | Lint + typecheck | ruff, eslint, mypy, tsc, etc. | MEDIUM |
| 3 (weakest) | Error rate | Always available (from observation data) | LOW |

Tier selection is automatic and transparent. If the user later adds tests, Acumen upgrades the tier and notifies.

**Confidence labeling is mandatory.** When tests exist: "this rule set passes 15% more tests." When tests don't exist: "improvement confidence: LOW -- add tests for stronger signal."

### Stop gate signal vs. session-end signal

The Stop gate (real-time) and session-end evaluation (async) use different signal subsets:

**Stop gate (must complete in <1 second):**
- `git diff --name-only HEAD` -- detect claimed file changes
- `ruff check --select E <changed-files>` -- fast lint on changed files only (if ruff present)
- Test suite *only if* it completes in <2 seconds (detected via `time` at init)

**Session-end evaluation (no latency constraint):**
- Full test suite
- Full lint + typecheck
- Error rate trend

If a project's test command takes >2 seconds (the common case), the Stop gate skips test verification and says so explicitly: *"test claims will be verified at session end."* This is more honest and more useful than pretending to verify something it can't.

### Composite score (for display, not for ratchet decisions)

The ratchet loop uses a single primary metric (highest available tier). For `/acumen-status` reporting:

```
Tier 1: test_pass_rate (50%) + error_rate_trend (20%) + lint_clean (20%) + process_health (10%)
Tier 2: lint_clean (40%) + error_rate_trend (40%) + process_health (20%)
Tier 3: error_rate_trend (60%) + process_health (40%)
```

---

## 5. The Stop gate (Phase 0 + Phase 1)

### Why it's the first thing to build

The first magical behavior users feel is the agent not getting away with "done" when work isn't done. This creates the trust foundation for everything else. It must be built and validated before the attribution model, because attribution uses the same evaluation signal the Stop gate establishes.

### Mechanism

The Claude Code Stop hook receives `last_assistant_message` and `stop_hook_active` in stdin JSON.

```
1. If stop_hook_active == true: exit 0 (loop guard -- prevent infinite blocking)
2. If stop gate disabled: exit 0
3. Run fast-signal evaluation:
   a. Check git state (instant)
   b. If ruff present: lint changed files (usually <500ms)
   c. If test command is sub-2-second: run tests
4. If evaluation PASSES: exit 0
5. If evaluation FAILS and failures are NEW (not pre-existing):
   block stop: exit 2 + stderr feedback
6. If evaluation cannot run / times out / errors: exit 0 (fail-open)
```

### Phase 0: validate before building

Run the following experiment before writing production Stop gate code:
1. Build ~30-line bash Stop hook that just returns exit 2 + a stderr message
2. Test in real Claude Code session: does the agent receive the feedback? Does it continue working?
3. Test loop guard: if the agent says "done" again after feedback, does stop_hook_active prevent infinite blocking?
4. Measure test command latency: `time <test-cmd>`. If >2s, it goes in the "session-end only" bucket.

**GO/NO-GO:** If Stop gate doesn't reliably deliver feedback to the agent and allow continuation, redesign before Phase 1.

### Feedback format

```
Acumen: stop blocked. Detected new failures since session start:
  - tests/test_auth.py::test_login (AssertionError -- was passing)
  - tests/test_auth.py::test_signup (AttributeError -- was passing)
  (test verification deferred to session end -- test suite takes 23s)
Fix the failures or describe what's still broken.
```

---

## 6. Attribution model (Phase 1)

### Why it matters before learning

Without attribution, Acumen learns wrong lessons. `redis-server` not installed causes test failures -- that is not the agent's fault. Generating a corrective rule from environment noise makes the agent worse. Attribution must gate what feeds the learning pipeline.

### Classification

**Agent-attributable** (feeds rule learning):
- `agent_error` -- Agent made a verifiable mistake
- `agent_process` -- Agent skipped a required step

**Environment-attributable** (feeds blocker tracking, NOT rule learning):
- `env_missing` -- Required binary/package not installed
- `env_version` -- Version incompatibility
- `env_permission` -- Permission denied
- `env_sandbox` -- Sandbox restriction
- `env_external` -- External service unavailable

**System/uncertain** (tracked, not used for any learning):
- `api_error` -- Claude Code API failure
- `user_interrupt` -- User cancelled
- `preexisting` -- Failure existed before session started
- `flaky` -- Result differs between runs or timed out
- `inconclusive` -- Cannot determine cause

**Critical default:** When uncertain, classify as `inconclusive`, NOT `agent_error`. Missing a true pattern is better than learning a false one.

### Baseline capture

At `SessionStart`: git branch + status + HEAD commit + test pass/fail count (if fast). At reflection: subtract pre-existing failures. Only NEW failures can be `agent_error`.

---

## 7. Mutation scope (v1 boundary)

### What Acumen can mutate

- `.claude/rules/acumen-*.md` -- corrective rules from failures **(SHIPPED)**
- `.claude/skills/acumen-*/SKILL.md` -- reusable skills from successes **(TO BUILD)**

### What Acumen cannot mutate

- Hook scripts (execute on every tool call; bad hook = broken agent loop)
- Its own code (observation logic, reflection prompts, scoring)
- `CLAUDE.md` (user's document)
- The evaluation function (test suite, lint config)

### Safety tiers

| Tier | Target | Condition | Mechanism |
|------|--------|-----------|-----------|
| AUTO | Corrective rules | 3+ evidence + effectiveness passes | Applied on next session start |
| REVIEW | Skills | Extraction complete | User approves via `/acumen-review` |
| MANUAL | Hook generation, scaffold | Explicit invocation + isolation | v2 only |

---

## 8. Skill synthesis (Phase 3 / Layer 3)

### The Voyager pattern for coding agents

After a successful session, extract the solution as a reusable skill. A session qualifies as successful for skill extraction when: (a) the evaluation signal is in a passing state at session end (tests pass, or lint clean if no tests), AND (b) at least 5 observations were recorded (indicating meaningful work was done), AND (c) the session didn't start with the evaluation already failing (baseline was passing).

### Skill format

```markdown
# .claude/skills/acumen-test-fixing/SKILL.md
---
name: test-fixing
description: "Fix failing pytest tests by reading error output, locating failures, applying targeted fixes"
source_sessions: [session_abc123]
verified_score: 0.92
created_by: acumen
---

## When to use
When pytest reports test failures and the task is to fix them.

## Steps
1. Run pytest -v --tb=short to get failure summary
2. For each failing test, read test file and source file
3. Identify the assertion that fails, trace to root cause
4. Fix the source code (not the test) unless the test is wrong
5. Run pytest -v again to verify
6. If new failures appear, repeat from step 2

## Verification
- All previously failing tests now pass
- No new test failures introduced
```

### Skill lifecycle

```
[Successful task verified by evaluation signal]
    → Reflector subagent extracts skill candidate     Status: CANDIDATE
    → User reviews via /acumen-review                 Status: PROPOSED
    → User approves (or auto if HIGH conf + 2+ matches) Status: ACTIVE
    (a "match" = a subsequent session where the same task family was detected
     and the skill's trigger conditions were met)
    → Written to .claude/skills/acumen-{name}/
```

Only verified skills enter the library. An unverified skill that worsens the agent is worse than no skill.

### Sandbox handling

If `.claude/skills/` is not writable (sandbox mode), store in `.acumen/generated-skills/` and notify user with promotion instructions.

---

## 9. Evolution engine (Phase 4 / Layer 2)

### The Karpathy Loop for agent configuration

```
acumen evolve [--rounds N] [--budget $]
```

Loop:
1. Display estimated cost per round before starting (based on average session token usage)
2. Snapshot current rule set + active skills (git commit on internal branch in worktree)
3. Select parent from Pareto frontier (current config if first run)
4. Mutate one thing (LLM-generated): add rule, remove underperforming rule, modify rule wording, adjust skill trigger
5. Evaluate: run agent on task suite via `claude -p` in isolated git worktree
6. Score against primary evaluation signal
7. Keep or revert:
   - Improved → commit stays, added to Pareto frontier
   - Same/worse → `git reset HEAD~1`
   - Mixed (better on some tasks, worse on others) → kept as Pareto-optimal variant
8. Stop if spend cap hit (default $5, configurable with `--budget`)
9. Repeat for N rounds, then report

### Pareto frontier (v1: simple)

v1 maintains 2-3 named variants (e.g., "test-heavy", "lint-heavy", "balanced") using explicit variant tags. Automatic task-type detection and variant selection is v1.2. The key insight from GEPA is "don't converge to one strategy" -- even manual variant selection delivers most of the diversity benefit.

### Cost transparency

Before starting:
```
Acumen: estimated cost per round ~$0.12 (based on 850 avg tokens/session × 14 sessions)
Budget: $5.00 | Max rounds: 41
Starting evolution. Ctrl-C to stop early.
```

After completion:
```
Acumen: evolution complete (23 rounds, $2.76 spent)
  4 improvements kept (test pass rate: 71% → 82%)
  1 new Pareto variant: "test-heavy"
  19 mutations reverted
```

### Constraints

- Requires Tier 1 or Tier 2 evaluation signal. Refuses to run with Tier 3 only ("too unreliable for autonomous mutation -- add tests or a linter").
- All mutations run in git worktrees. User's working directory is never touched.
- The evaluation function is never in the mutation space.

---

## 10. File structure (after all phases)

### Files that change

```
hooks/
  observe.sh              -- existing (unchanged)
  session-end.sh          -- existing (add eval tier detection)
  session-start.sh        -- existing (add baseline capture, eval tier)
  stop-gate.sh            -- NEW (~40 lines)
  instructions-loaded.sh  -- NEW (~20 lines): confirms rules entered context
  stop-failure.sh         -- NEW (~20 lines): blocks API errors from feeding attribution

lib/
  store.py                -- existing (unchanged)
  scorer.py               -- existing (unchanged)
  formatter.py            -- existing (minor additions)
  improver.py             -- existing (extend with evaluator, attribution)
  evaluator.py            -- NEW (~140 lines): detect + run eval signal, tier selection
  skills.py               -- NEW (~200 lines): extract, store, promote, retrieve skills
  evolve.py               -- NEW (~400 lines): evolution loop + Pareto frontier + mutations

agents/
  reflector.md            -- existing (add attribution awareness)
  skill-extractor.md      -- NEW
  evolver.md              -- NEW

commands/
  status.md               -- existing (add eval tier display)
  reflect.md              -- existing (unchanged)
  insights.md             -- existing (unchanged)
  review.md               -- existing (add skills to review queue)
  skills.md               -- NEW
  evolve.md               -- NEW
  evolve-report.md        -- NEW
```

### Key consolidations (anti-bloat corrections)

- **No `baseline.py`** -- baseline capture logic lives in `session-start.sh` (the git state) and `evaluator.py` (the test pass count).
- **No `effectiveness.py`** -- effectiveness measurement stays in `improver.py`, extended to use `evaluator.py` instead of raw error rate.
- **No `mutator.py`** -- mutation strategies live in `evolve.py` (mutations are only called from the evolution loop).
- **No `pareto.py`** -- Pareto frontier management lives in `evolve.py` (it's part of the same system, not a reusable utility).
- **No `skill_templates.py`** -- task family templates live in `skills.py`.

### Approximate line counts

```
Existing code:   ~800 lines
stop-gate.sh:           ~40 lines
instructions-loaded.sh: ~20 lines
stop-failure.sh:        ~20 lines
evaluator.py:           ~140 lines
skills.py:              ~200 lines
evolve.py:              ~400 lines
Other additions:        ~100 lines
Total new:              ~920 lines
Total:                  ~1720 lines
```

---

## 11. Implementation phases

### Phase 0: Prove the Stop gate (1-2 days)

**Goal:** Validate mechanism before building on it.

- [ ] Write ~30-line bash Stop hook that returns `exit 2` + stderr message
- [ ] Test in real Claude Code session: agent receives feedback, continues working
- [ ] Test loop guard: `stop_hook_active == true` prevents infinite blocking
- [ ] Measure `time <test-cmd>`. If >2s, test suite goes in "session-end only" bucket
- [ ] Document: what claims can the Stop gate verify instantly?

**GO/NO-GO gate:** Stop gate delivers feedback, agent continues, loop guard works.

---

### Phase 1: Trust layer (1-2 weeks, ~300 new lines)

**What ships:** Stop gate blocks false "done" claims. Attribution separates agent mistakes from environment noise. Evaluation signal is auto-detected and locked in.

New files:
- `hooks/stop-gate.sh` (~40 lines)
- `hooks/instructions-loaded.sh` (~20 lines) -- records which acumen rules entered context; closes the "rule generated vs rule active" gap in attribution
- `hooks/stop-failure.sh` (~20 lines) -- marks sessions with API/tool failures as `api_error`; prevents those sessions from feeding the learning pipeline
- `lib/evaluator.py` (~140 lines)

Modified files:
- `hooks/session-start.sh` (baseline capture)
- `hooks/session-end.sh` (eval tier detection)
- `lib/improver.py` (use evaluator for effectiveness, add attribution filter)
- `agents/reflector.md` (attribution-aware reflection)
- `commands/status.md` (show eval tier + confidence)

Tasks:
- [ ] P1.1: `lib/evaluator.py` -- detect test/lint/typecheck commands, measure latency, return tier + signal
- [ ] P1.2: Add baseline capture to `session-start.sh` (git state + pre-existing test failures)
- [ ] P1.3: Add attribution classification to `agents/reflector.md`
- [ ] P1.4: `hooks/stop-gate.sh` -- fast-signal evaluation, block on new failures, fail-open
- [ ] P1.4b: `hooks/instructions-loaded.sh` -- append rule names that entered context to `.acumen/rule-activity.jsonl`
- [ ] P1.4c: `hooks/stop-failure.sh` -- on API/tool failure at stop, append session marker so reflection skips it
- [ ] P1.5: Extend `lib/improver.py` to use evaluator for effectiveness + filter non-agent-attributable failures
- [ ] P1.6: Update `/acumen-status` to display eval tier and confidence label
- [ ] P1.7: Test in 3+ real sessions across projects with and without test suites

**Quality gate:**
- Stop gate blocks false completion (verified in real session)
- Stop gate allows when evaluation passes
- Stop gate fails open on errors/timeouts
- Loop guard works
- Attribution classifies environment errors as non-agent
- Zero new external dependencies
- All existing tests still pass

---

### Phase 2: Verified effectiveness (1 week, ~100 new lines)

**What ships:** Effectiveness claims are backed by the evaluation signal, not just error rates. Rules show measurable improvement with confidence labels.

Modified files:
- `lib/improver.py` (replace error-rate effectiveness with eval-signal effectiveness)
- `commands/status.md` / `commands/review.md` (confidence labels in display)

New files:
- `commands/effectiveness.md`

Tasks:
- [ ] P2.1: Replace `measure_effectiveness()` error-rate logic with evaluation signal comparison
- [ ] P2.2: Add confidence labels to all improvement claims (HIGH/MEDIUM/LOW based on eval tier)
- [ ] P2.3: `/acumen-effectiveness` command with per-rule confidence display
- [ ] P2.4: Rule retirement after N sessions without demonstrable improvement

---

### Phase 3: Skill synthesis (2 weeks, ~200 new lines)

**What ships:** After successful tasks, Acumen extracts reusable SKILL.md files. Users review and approve via `/acumen-review`. Active skills are retrieved at session start and injected as context.

New files:
- `lib/skills.py` (~200 lines)
- `agents/skill-extractor.md`
- `commands/skills.md`

Modified files:
- `hooks/session-end.sh` (trigger skill extraction on successful sessions)
- `commands/review.md` (add skill candidates to review queue)
- `hooks/session-start.sh` (inject active skills as context)

Tasks:
- [ ] P3.1: `lib/skills.py` -- extract, store, promote, retrieve skill lifecycle
- [ ] P3.2: `agents/skill-extractor.md` -- subagent that extracts SKILL.md from successful session trace
- [ ] P3.3: Add skill extraction trigger to `session-end.sh`
- [ ] P3.4: Add skill candidates to `/acumen-review` queue
- [ ] P3.5: Skill promotion to `.claude/skills/acumen-{name}/SKILL.md` on approval
- [ ] P3.6: Session-start skill retrieval and context injection
- [ ] P3.7: `/acumen-skills` command (list, status, verify)
- [ ] P3.8: Sandbox detection + fallback to `.acumen/generated-skills/`

---

### Phase 4: Evolution engine (2-3 weeks, ~400 new lines)

**What ships:** `acumen evolve` runs the Karpathy Loop on the agent's rule set and skills. Overnight runs produce measurably better configurations. Pareto frontier prevents convergence.

**Requires:** Tier 1 or Tier 2 evaluation signal (refuses to run otherwise).

New files:
- `lib/evolve.py` (~400 lines: loop + Pareto + mutations)
- `agents/evolver.md`
- `commands/evolve.md`
- `commands/evolve-report.md`

Tasks:
- [ ] P4.1: Core evolution loop (snapshot, select parent, mutate, evaluate, keep/revert)
- [ ] P4.2: Pareto frontier (maintain 2-3 named variants, v1 uses explicit tags)
- [ ] P4.3: Mutation strategies (add rule, remove rule, modify rule, adjust skill trigger)
- [ ] P4.4: Git worktree isolation for all evaluation runs
- [ ] P4.5: Cost estimation + spend cap + `--budget` flag
- [ ] P4.6: Batch evaluation via `claude -p` in isolated worktree
- [ ] P4.7: `/acumen-evolve` and `/acumen-evolve-report` commands

**Quality gate:**
- 10+ rounds without errors
- At least one mutation improves evaluation score in a test run
- Revert works correctly (user's working directory untouched)
- Pareto frontier maintains 2+ variants after sufficient rounds
- Refuses to run on Tier 3 only
- Cost cap stops the loop correctly

---

### Phase 5: Polish + v1.0 (1 week)

- [ ] README rewrite with screenshots
- [ ] Demo GIFs for all key workflows
- [ ] Plugin registry submission
- [ ] CHANGELOG.md
- [ ] Dogfood in 3 different repos

---

## 12. Correctness invariants

Ordered by criticality. If any breaks, halt and fix.

1. **The evaluation function is immutable.** Acumen can never modify the user's test suite, lint config, or typecheck config.
2. **Stop gate fails open.** If it crashes, times out, or can't determine truth, `exit 0`. A broken stop gate that blocks indefinitely will make users uninstall.
3. **Attribution defaults to `inconclusive`.** Only classify as `agent_error` with positive evidence.
4. **Evolution never touches the working directory.** All evolution runs in worktrees or temporary clones.
5. **Skills require verification before entering the library.** An unverified skill that worsens the agent is worse than no skill.
6. **Diversity beats convergence.** The Pareto frontier must maintain multiple variants.

---

## 13. What the compound effect looks like

```
Session 1:    Agent fails. Acumen observes. User doesn't notice.
Session 5:    Stop gate catches false "done" with failing tests.
              User: "That saved me 15 minutes."
Session 10:   Two corrective rules active. Error rate down 30%.
              /acumen-effectiveness shows proof with confidence: HIGH.
Session 20:   First skill extracted. Agent uses it automatically on next matching task.
Session 50:   acumen evolve runs overnight. 23 variants tested. 4 improvements kept.
              Test pass rate: 71% → 82%.
Session 100:  12 corrective rules, 8 verified skills, 3 strategy variants.
              Measurably, provably, demonstrably better than session 1.
```

That is a tight loop with a real verifier, conservative attribution, verified skill acquisition, and evolutionary strategy optimization. It is exactly what the research says works. And it compounds.

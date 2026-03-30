# Acumen Capability Registry

Canonical map of what Acumen can do today. No roadmap items. Every entry has file paths and entry points.

---

## CAP-OBS-001: Tool Call Observation

**What:** Captures metadata from every Claude Code tool call (PostToolUse, PostToolUseFailure).
**Files:** `hooks/observe.sh`
**Entry point:** Shell hook fired by Claude Code plugin system
**Data captured:** tool_name, session_id, timestamp, outcome, error_type, error_message
**Data NOT captured:** tool_input, tool_response, file contents, conversation
**Storage:** `.acumen/observations/YYYY-MM-DD.jsonl` (append-only)
**Performance:** <20ms per observation (pure bash, zero external dependencies)

## CAP-OBS-002: Auto-Reflection Trigger

**What:** Counts observations since last reflection. When threshold exceeded, flags for reflection at next session start.
**Files:** `hooks/session-end.sh`, `hooks/session-start.sh`
**Entry point:** SessionEnd hook (count + flag), SessionStart hook (consume flag + inject context)
**Threshold:** Default 10, configurable via `ACUMEN_REFLECT_THRESHOLD` env var
**Flag file:** `.acumen/should-reflect`

## CAP-OBS-003: Session-Start Improvement Summary

**What:** On normal session starts (no reflection pending), shows count of active acumen rules.
**Files:** `hooks/session-start.sh`
**Entry point:** SessionStart hook, after flag check
**Output:** "Acumen: N active rule(s) improving your agent. Run /acumen-status for details."

---

## CAP-LEARN-001: Reflection & Insight Extraction

**What:** Analyzes observations for patterns (error, retry, recovery, usage spike). Generates structured insights with evidence counts.
**Files:** `agents/reflector.md`, `skills/reflect.md`, `commands/reflect.md`
**Entry point:** `/acumen-reflect` command dispatches reflector subagent
**Pattern threshold:** 3+ supporting observations required
**Output:** `.acumen/insights.json`

## CAP-LEARN-002: Confidence/Impact Scoring

**What:** Scores insights using recency-weighted confidence and error-ratio-based impact. Combined score (40% confidence + 60% impact).
**Files:** `lib/scorer.py` -- `score_insight()`, `rank_insights()`
**Entry point:** Called by reflector agent after insight extraction
**Recency model:** Exponential decay with 3-day half-life (SAGE-inspired)
**Bounds:** All scores 0.0-1.0

## CAP-LEARN-003: Insight Deduplication

**What:** Merges new insights with existing ones by description match. Sums evidence counts.
**Files:** `lib/scorer.py` -- `dedup_insights()`
**Entry point:** Called by reflector agent after scoring

## CAP-LEARN-004: Insight Validation

**What:** Validates LLM-generated insights have required fields (description, category, evidence_count, tools) with correct types. Drops invalid entries.
**Files:** `lib/scorer.py` -- `validate_insight()`, `filter_valid_insights()`
**Entry point:** Available for reflector agent pipeline (wiring in TODO-004)

---

## CAP-IMP-001: Proposal Generation

**What:** Converts insights into improvement proposals. All insights become rules. Deduplicates against existing applied rules by slug.
**Files:** `lib/improver.py` -- `generate_proposals()`, `list_applied_rule_slugs()`
**Entry point:** Called by reflector agent after insights written
**Dedup:** Slug-based matching against `.claude/rules/acumen-*.md`

## CAP-IMP-002: Auto-Apply Proposals

**What:** Auto-applies all proposed improvements as rule files in `.claude/rules/acumen-*.md`.
**Files:** `lib/improver.py` -- `auto_apply_proposals()`, `apply_proposal()`
**Entry point:** Called during session-start auto-reflection flow
**Safety:** Only applies proposals with status="proposed". Sets status="auto-applied" and records applied_at timestamp.

## CAP-IMP-003: Effectiveness Measurement

**What:** Compares tool error rates before and after rule application. Produces effective/neutral/harmful verdicts.
**Files:** `lib/improver.py` -- `measure_effectiveness()`
**Entry point:** Called by reflector agent after proposal generation
**Threshold:** 5+ observations on each side, >10% delta for effective/harmful
**Output:** Updates proposal's `effectiveness` field in proposals.json

## CAP-IMP-004: Proposal Review & Revert

**What:** User reviews applied improvements, reverts unwanted ones, promotes proven rules to global scope.
**Files:** `commands/review.md`, `lib/improver.py` -- `revert_proposal()`, `lib/formatter.py` -- `format_review()`
**Entry point:** `/acumen-review` command

## CAP-IMP-005: Global Scope Promotion

**What:** Copies proven effective rules to `~/.claude/rules/acumen-*.md` (applies across all projects).
**Files:** `lib/improver.py` -- `promote_to_global()`
**Entry point:** Via `/acumen-review` command when user approves promotion
**Safety:** REVIEW tier -- requires user confirmation

## CAP-IMP-006: Proposal Auto-Expiry

**What:** Removes rejected/proposed proposals older than 30 days. Applied proposals kept as historical record.
**Files:** `lib/improver.py` -- `expire_stale_proposals()`
**Entry point:** Called during session-start auto-reflection flow

## CAP-IMP-007: Effectiveness Measurement with Eval Confidence

**What:** Wraps effectiveness measurement with an eval tier confidence label (HIGH/MEDIUM/LOW) derived from `eval-config.json`.
**Files:** `lib/improver.py` -- `measure_effectiveness_with_confidence()`
**Entry point:** Called by reflector agent, and by `/acumen-effectiveness` command
**Output:** Adds `eval_confidence` field to updated proposals

## CAP-IMP-008: Rule Retirement

**What:** Automatically retires applied rules that are harmful (after 7 days) or neutral (after 30 days). Deletes `.claude/rules/acumen-*.md` file and sets status='retired'.
**Files:** `lib/improver.py` -- `retire_ineffective_proposals()`, `hooks/session-end.sh`
**Entry point:** SessionEnd hook each session (fail-open)
**Safety:** Effective rules and rules with no verdict (pending) are never retired.

---

## CAP-TRUST-001: Stop Gate

**What:** Blocks agent from stopping when new test failures are introduced this session. Defers for slow test suites (>2s). Fail-open on all errors.
**Files:** `hooks/stop-gate.sh`
**Entry point:** Stop hook (fires before agent terminates)
**Baseline:** Compares against `session-baseline.json` — only blocks on NEW failures, not pre-existing ones.
**Loop guard:** `stop_hook_active=True` input exits immediately to prevent infinite blocking.

## CAP-TRUST-002: InstructionsLoaded Hook

**What:** Records which acumen rules entered context each session. Closes "rule generated vs rule active" attribution gap.
**Files:** `hooks/instructions-loaded.sh`
**Entry point:** InstructionsLoaded hook
**Storage:** `.acumen/rule-activity.jsonl`

## CAP-TRUST-003: StopFailure Hook

**What:** Marks sessions that ended with API/tool failures so the reflection pipeline can exclude them.
**Files:** `hooks/stop-failure.sh`
**Entry point:** StopFailure hook
**Storage:** `.acumen/stop-failures.jsonl`

---

## CAP-EVAL-001: Evaluation Signal Detection and Running

**What:** Auto-detects available evaluation signals (test suite > lint > error rate), measures latency, classifies tier (1=HIGH, 2=MEDIUM, 3=LOW). Runs signals for stop gate and effectiveness measurement.
**Files:** `lib/evaluator.py` -- `build_eval_config()`, `detect_eval_commands()`, `run_eval_signal()`
**Entry point:** Called at session-start; loaded by stop gate and effectiveness commands
**Detection:** pyproject.toml / pytest.ini / tests/ dir (Python), package.json (JS), Cargo.toml (Rust), go.mod (Go)
**Storage:** `.acumen/eval-config.json` (rebuilt every 24h)
**Fast threshold:** Tests taking <2s run inline in stop gate; >2s deferred to session-end.

## CAP-EVAL-002: Session Baseline Capture

**What:** Runs evaluation signal at session start and stores pass/fail counts. Stop gate compares against this to distinguish new failures from pre-existing ones.
**Files:** `hooks/session-start.sh`, `lib/evaluator.py` -- `run_eval_signal()`
**Entry point:** SessionStart hook Job 3 (only when fast_for_stop_gate=True)
**Storage:** `.acumen/session-baseline.json`

---

## CAP-DISP-001: Status Dashboard

**What:** Shows session count, observation count, error rate, daily activity, top insights, and evaluation tier/confidence.
**Files:** `commands/status.md`, `lib/formatter.py` -- `format_status()`
**Entry point:** `/acumen-status` command

## CAP-DISP-002: Insight Listing

**What:** Shows all insights ranked by combined score with category and evidence count.
**Files:** `commands/insights.md`, `lib/formatter.py` -- `format_insights()`
**Entry point:** `/acumen-insights` command

## CAP-DISP-003: Rule Effectiveness Dashboard

**What:** Shows per-rule effectiveness verdicts (effective/neutral/harmful/pending) with eval confidence labels.
**Files:** `commands/effectiveness.md`
**Entry point:** `/acumen-effectiveness` command

---

## CAP-STORE-001: JSONL Observation Storage

**What:** Append-only daily JSONL files with 7-day sliding window for reads.
**Files:** `lib/store.py` -- `read_observations()`
**Storage:** `.acumen/observations/YYYY-MM-DD.jsonl`

## CAP-STORE-002: Insight Storage

**What:** JSON array with atomic write (tmp-rename pattern).
**Files:** `lib/store.py` -- `read_insights()`, `write_insight()`
**Storage:** `.acumen/insights.json`

## CAP-STORE-003: Proposal Storage

**What:** JSON array with atomic write. Tracks status lifecycle (proposed -> auto-applied -> effective/reverted).
**Files:** `lib/improver.py` -- `read_proposals()`, `write_proposal()`
**Storage:** `.acumen/proposals.json`

## CAP-STORE-004: Scope Resolution

**What:** Resolves 'project' scope to `.acumen/` and 'global' scope to `~/.claude/acumen/`.
**Files:** `lib/store.py` -- `resolve_scope_path()`

# Acumen: Deferred Features & Research-Grounded Roadmap

Items below are explicitly deferred but planned. Each includes the research that motivates it and enough context to implement without re-doing the research.

**Shipped:** Phase 1 (observe + learn) and Phase 2 (improve + auto-apply + review/revert) are complete.

---

## v0.2 Priorities (immediate next steps, ~85 lines total)

### TODO-001: Rule Dedup in Reflector
**What:** Before generating a proposal, scan `.claude/rules/acumen-*.md` for an existing rule covering the same insight. Skip if already applied.
**Why:** Dogfooding showed duplicate proposals: "use python3" was already applied as a rule but got proposed again on next reflection cycle. The reflector deduplicates against insights.json but not against applied rule files.
**How:** In reflector.md, before calling `generate_proposals()`, list existing rule files and pass their contents as context so the LLM can skip already-covered insights.
**Effort:** ~15 lines (reflector.md update + improver.py: list existing acumen-* rule slugs).
**Depends on:** Nothing.

### TODO-002: Effectiveness Measurement
**What:** Track whether applied rules actually reduced target errors. After N sessions (default: 5), check: did the target error recur? did overall error rate change? Verdict: effective / neutral / harmful (revert).
**Why:** MiniMax M2.7's key innovation: analyze failure trajectories, compare before/after. AutoResearch: keep or discard based on single metric. Without measurement, we're applying rules blind.
**Research:** MiniMax M2.7 (before/after failure trajectory comparison), AutoResearch (single metric validation), DGM (archive what works, discard what doesn't).
**How:** In store.py: `measure_effectiveness(scope_path, rule_slug, sessions=5)` -- counts observations of the target error_type before and after the rule's applied_at timestamp. In improver.py: `verdict(before_count, after_count)` -- returns "effective" / "neutral" / "harmful".
**Effort:** ~40 lines. Triggered by reflector after N sessions have passed since application.
**Depends on:** Nothing (observations already have timestamps).

### TODO-003: Global Scope Promotion
**What:** Rules proven effective in 3+ projects can be promoted to `~/.claude/rules/acumen-*.md` (global Claude Code rules, picked up in every project). User confirms before global write.
**Why:** SAGE (Ebbinghaus forgetting curve): some learnings are universal (e.g., "use python3 not python"), some are project-specific. ALMA: the memory design itself should evolve.
**Research:** SAGE (memory optimization), ALMA (meta-learn memory designs).
**How:** `promote_to_global(rule_path)` in improver.py copies the rule to `~/.claude/rules/`. Reflector marks a proposal with `scope: "global"` when effectiveness is proven and the same pattern has been observed in 3+ projects. Global promotions are REVIEW tier -- user confirms via `/acumen-review` before write.
**Effort:** ~25 lines in improver.py + updated reflector.md guidance.
**Depends on:** TODO-002 (effectiveness must be measured before promoting on evidence).
**Confirmed:** Yes (user confirmed 2026-03-30).

### TODO-004: Research -- User Correction Capture
**What:** Research how to detect user corrections ("no, use X instead", "that's wrong, do Y") via Claude Code hooks, transcript analysis, or Stop hook. Do NOT implement yet -- research only.
**Why:** ExpeL showed learning from success AND failure outperforms learning from failure alone. Currently Acumen only sees tool errors, not user-initiated corrections. This gap means we miss a class of high-signal learning events.
**Research:** ExpeL (AAAI 2024) -- "failure AND success" insight extraction, Reflexion (verbal self-reflection signals).
**Output:** Write findings to findings.md. Implement in a separate TODO once approach is clear.
**Effort:** Research only. No code.
**Depends on:** Nothing.

---

## Phase 3: EXPAND

### TODO-005: Hook Generation
**What:** Generate shell hooks from insights (e.g., "always run lint after editing Python files").
**Why:** Hooks are deterministic enforcement. Research and community consensus: hooks > instructions for mechanical rules.
**Research:** Anthropic best practices ("hooks are deterministic, instructions are advisory").
**Depends on:** Effectiveness measurement (hooks need same evidence bar as global promotion).
**Safety:** REVIEW tier -- hooks execute code, must be human-approved.

### TODO-006: Skill Synthesis
**What:** Automatically create Claude Code skills from successful multi-step patterns.
**Why:** SkillWeaver (April 2025) showed 31.8% improvement on WebArena. Skills transfer from strong agents to weak agents (up to 54.3% improvement). Skills as reusable APIs is the unit of agent capability expansion.
**Research:** SkillWeaver, Voyager (Minecraft agent skill library), AutoResearch (validated optimizations become permanent).
**Depends on:** TODO-002 effectiveness measurement (only synthesize skills from PROVEN patterns).
**Safety:** MANUAL tier -- skill creation always requires human review.

### TODO-007: Session Scope (Real-Time Adaptation)
**What:** Within-conversation adaptation. If the user corrects the agent 3 times in similar ways, adapt immediately.
**Why:** Reflexion/LATS research: verbal self-reflection as the improvement signal. Real-time correction detection enables within-session learning.
**Research:** Reflexion (verbal self-reflection), MiniMax M2.7 (loop detection safeguards).
**Depends on:** TODO-004 research (correction detection must work first).
**Design:** Session learnings are ephemeral but candidates for promotion to project scope.

---

## Phase 4: MULTI-AGENT SUPPORT

### TODO-008: Agent-Agnostic Observation Format
**What:** Standard observation format that works across Claude Code, Codex, Gemini, etc.
**Why:** Acumen's value increases when it works with any agent. Different agents have different hook mechanisms but observation data is universal.
**Depends on:** Phase 1-3 proven on Claude Code.
**Design:** Define a minimal observation schema. Each agent adapter translates native events to this schema.

### TODO-009: Codex Adapter
**What:** Hook into OpenAI Codex's agent system.
**Depends on:** TODO-008.

### TODO-010: Gemini CLI Adapter
**What:** Hook into Google's Gemini CLI agent system.
**Depends on:** TODO-008.

---

## Research-Inspired Future Ideas (Not Committed)

### IDEA-001: Elo Tournament for Insights
**Inspiration:** Google AI Co-Scientist uses Elo-based ranking for hypothesis quality.
**Application:** When absolute scoring is ambiguous, use pairwise comparison of insights via LLM to rank them.
**Status:** Interesting but overkill until scoring proves unreliable.

### IDEA-002: Population-Based Exploration
**Inspiration:** DGM maintains an archive tree of agent variants, enabling diversity.
**Application:** Instead of one set of rules, maintain variants and A/B test them.
**Status:** Fascinating but complex. Requires controlled experiments across sessions.

### IDEA-003: Automatic Research Direction Generation
**Inspiration:** AutoResearch's `program.md` is human-written. What if the agent generates its own research directions?
**Application:** After N reflection cycles, Acumen proposes "areas to investigate" for the next cycle.
**Status:** Phase 4+. Requires strong effectiveness measurement first.

### IDEA-004: Cross-User Skill Marketplace
**Inspiration:** SkillWeaver showed skills transfer from strong to weak agents.
**Application:** Users share proven, anonymized skills via an opt-in marketplace.
**Status:** Requires privacy framework, trust model, and distribution mechanism. Long-term.

### IDEA-005: Forgetting Curve for Insights
**Inspiration:** SAGE uses Ebbinghaus forgetting curve for memory optimization.
**Application:** Insights that haven't been relevant for N sessions get demoted/archived. Prevents insight bloat.
**Status:** Phase 3 when we have enough data to model decay.

# Acumen: Deferred Features & Research-Grounded Roadmap

Items below are explicitly deferred but planned. Each includes the research that motivates it and enough context to implement without re-doing the research.

**Shipped:**
- v0.1-v0.3 (observe + learn + improve + auto-apply + review/revert + effectiveness + global promotion) -- complete
- v2.1 spec: "Turn your generalist AI into a specialist" -- approved, building Phase 1A
- Phase 1A Steps 1-3: classify.py (Tier 0.5), observe.sh (refactored), store.py (per-session JSONL) -- complete

---

## KNOWN BUGS (fix before Phase 1B)

### ~~BUG-001: write_kind hardcoded~~ FIXED
**Fixed in:** Phase 1A Step 10. `classify_write_kind(tool_name, file_path)` now called correctly.

### ~~BUG-002: Corruption skip counter not tracked~~ FIXED
**Fixed in:** Phase 1A Step 9. `read_observations()` returns `(observations, error_count)`. Count surfaced in `/acumen-status`.

---

## Phase 1A Remaining Steps (in progress)

### TODO-001: Plugin Registry Submission
**What:** Submit Acumen to the Claude Code community plugin marketplace and set up self-hosted marketplace as fallback.
**Why:** Current install (`claude --plugin-dir`) is dev-only. Registry submission enables `claude plugin install acumen` -- the plug-and-play experience.
**How:** Enrich plugin.json with author/homepage/keywords fields. Submit via clau.de/plugin-directory-submission. Add marketplace.json for self-hosted distribution.
**Effort:** S (~30 min).
**Depends on:** Nothing.

### TODO-002: PreToolUse Denial Capture
**What:** Add PreToolUse hook to capture tool denial signals (user blocked an Edit/Write). This is the strongest correction signal available without reading content.
**Why:** ExpeL showed learning from success AND failure outperforms failure alone. Tool denials are high-signal: user actively stopped the agent. Currently we miss this class of learning events.
**Research:** ExpeL (AAAI 2024), Reflexion (verbal self-reflection signals). Feasibility confirmed in findings.md section 8.
**How:** Add PreToolUse to plugin.json hooks. In observe.sh, detect hook_event_name=PreToolUse and record {tool_name, outcome: "denied", error_type: "user_denied"}. ~15 lines.
**Effort:** S (~30 min).
**Depends on:** Nothing.

### TODO-003: Demo GIFs for README
**What:** Create TUI Studio demo GIFs showing the key workflows: observation accumulation, reflection triggering, insight extraction, auto-apply, /acumen-review flow.
**Why:** README needs visual proof of the product. Research shows 'show don't tell' is the biggest conversion driver for CLI tools.
**Effort:** M (~1 hour).
**Depends on:** Nothing.

### TODO-004: Reflector Insight Quality Improvement
**What:** Tighten reflector.md to use validate_insight() and filter_valid_insights() from scorer.py. Ensure all LLM output passes validation before entering the pipeline.
**Why:** LLM-generated insights can have missing fields, wrong types, or empty descriptions. validate_insight() now exists but isn't wired into the reflector flow yet.
**Effort:** S (~15 min).
**Depends on:** Nothing.

---

## Phase 3: EXPAND

### TODO-005: Skill Synthesis (SkillWeaver-inspired)
**What:** Automatically create Claude Code skills from successful multi-step patterns. When the reflector detects a recurring successful workflow (e.g., "agent always runs lint then tests then commits"), synthesize a skill that codifies that workflow.
**Why:** SkillWeaver (April 2025) showed 31.8% improvement on WebArena. Skills transfer from strong agents to weak agents (up to 54.3% improvement). This is the "self-expanding" part of the vision.
**Research:** SkillWeaver, Voyager (Minecraft agent skill library).
**Depends on:** Effectiveness measurement (only synthesize from PROVEN patterns).
**Safety:** MANUAL tier -- skill creation always requires human review.

### TODO-006: Hook Generation
**What:** Generate shell hooks from insights (e.g., "always run lint after editing Python files").
**Why:** Hooks are deterministic enforcement. Research and community consensus: hooks > instructions for mechanical rules. This upgrades Acumen from advisory to enforcement.
**Research:** Anthropic best practices ("hooks are deterministic, instructions are advisory").
**Depends on:** Effectiveness measurement (hooks need same evidence bar as global promotion).
**Safety:** REVIEW tier -- hooks execute code, must be human-approved.

### TODO-007: Session Scope (Real-Time Adaptation)
**What:** Within-conversation adaptation. If the agent makes 3 similar errors in one session, adapt immediately rather than waiting for reflection.
**Why:** Reflexion/LATS research: verbal self-reflection as the improvement signal. Real-time correction detection enables within-session learning.
**Research:** Reflexion (verbal self-reflection), MiniMax M2.7 (loop detection safeguards).
**Depends on:** TODO-002 (correction detection must work first).

### TODO-008: Global Scope with Demotion
**What:** Rules proven effective in 3+ projects auto-promoted to `~/.claude/rules/`. Rules that become ineffective get demoted back to project scope.
**Why:** SAGE (Ebbinghaus forgetting curve): some learnings are universal, some are project-specific. Currently global promotion exists but demotion doesn't.
**Research:** SAGE (memory optimization), ALMA (meta-learn memory designs).
**Depends on:** TODO-005 effectiveness proven across projects.

---

## Phase 4: MULTI-AGENT SUPPORT

### TODO-009: Agent-Agnostic Observation Format
**What:** Standard observation format that works across Claude Code, Codex, Gemini CLI, etc.
**Why:** Acumen's value increases when it works with any agent. Different agents have different hook mechanisms but observation data is universal.
**Depends on:** Phase 1-3 proven on Claude Code.

### TODO-010: Codex Adapter
**What:** Hook into OpenAI Codex's agent system.
**Depends on:** TODO-009.

### TODO-011: Gemini CLI Adapter
**What:** Hook into Google's Gemini CLI agent system.
**Depends on:** TODO-009.

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

### IDEA-003: Forgetting Curve for Insights
**Inspiration:** SAGE uses Ebbinghaus forgetting curve for memory optimization.
**Application:** Insights that haven't been relevant for N sessions get demoted/archived.
**Status:** Partially implemented via proposal auto-expiry (30-day TTL).

### IDEA-004: Cross-User Skill Marketplace
**Inspiration:** SkillWeaver showed skills transfer from strong to weak agents.
**Application:** Users share proven, anonymized skills via an opt-in marketplace.
**Status:** Requires privacy framework, trust model, and distribution mechanism. Long-term.

### IDEA-005: Stop Gate (Contradiction Detection)
**Inspiration:** External review suggestion. Deterministic Stop hook that prevents fake-done states.
**Application:** Before claiming work is done, verify tests pass and lint is clean.
**Status:** Different product direction (enforcement vs advisory). Consider for v2.

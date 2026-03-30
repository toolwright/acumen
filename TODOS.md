# Acumen: Deferred Features & Research-Grounded Roadmap

Items below are explicitly deferred from Phase 1 but planned for future phases. Each includes the research that motivates it and enough context to implement without re-doing the research.

---

## Phase 2: IMPROVE (Auto-Application)

### TODO-001: CLAUDE.md Managed Section
**What:** Auto-append learned rules to a `<!-- acumen:managed -->` section in CLAUDE.md.
**Why:** Compounding engineering (Anthropic's highest-leverage recommendation). Every correction captured means that error class never recurs. Teams report time-to-ship dropping from >1 week to 1-3 days after 3 months.
**Research:** Anthropic best practices, community consensus on compounding engineering.
**Depends on:** Phase 1 (insights must exist before we can apply them).
**Safety:** REVIEW tier -- user must approve each rule before it's added.

### TODO-002: Memory Entry Generation
**What:** Write insights to Claude Code's `.claude/memory/` system as structured memory entries.
**Why:** Cross-session persistence using the agent's native memory. Insights survive context clearing.
**Research:** ExpeL (AAAI 2024) -- natural language insights from experience work WITHOUT fine-tuning.
**Depends on:** Phase 1 insights, TODO-001 (CLAUDE.md rules are simpler, do first).
**Safety:** SAFE tier -- memory entries are low-risk, additive.

### TODO-003: Effectiveness Measurement
**What:** Track whether applied improvements actually helped. Before/after comparison on target metrics.
**Why:** MiniMax M2.7's key innovation: analyze failure trajectories, compare before/after. AutoResearch: keep or discard based on single metric. Without measurement, we're guessing.
**Research:** MiniMax M2.7 (compare before/after), AutoResearch (single metric validation), DGM (archive what works).
**Depends on:** TODO-001 or TODO-002 (must have applied improvements to measure).
**Design:** Wait N sessions (default 5), measure: did target error recur? did overall error rate change? Verdict: effective (>10% improvement) / neutral / harmful (revert).

### TODO-004: User Review Flow (/acumen-review)
**What:** Interactive command to approve/reject/modify proposed improvements before application.
**Why:** Human-in-the-loop for REVIEW tier changes. DGM research showed self-improving systems hack their own reward -- human oversight is non-negotiable for non-trivial changes.
**Research:** DGM safety findings (reward hacking), all safety-first approaches in the literature.
**Depends on:** TODO-001 (need improvements to review).

### TODO-005: Hook Generation
**What:** Generate shell hooks from insights (e.g., "always run lint after editing Python files").
**Why:** Hooks are deterministic enforcement. Research and community consensus: hooks > instructions for mechanical rules.
**Research:** Anthropic best practices ("hooks are deterministic, instructions are advisory").
**Depends on:** TODO-004 (hooks need user approval via review flow).
**Safety:** REVIEW tier -- hooks execute code, must be human-approved.

---

## Phase 3: EXPAND + SCOPES

### TODO-006: Skill Synthesis
**What:** Automatically create Claude Code skills from successful multi-step patterns.
**Why:** SkillWeaver (April 2025) showed 31.8% improvement on WebArena. Skills transfer from strong agents to weak agents (up to 54.3% improvement). Skills as reusable APIs is the unit of agent capability expansion.
**Research:** SkillWeaver, Voyager (Minecraft agent skill library), AutoResearch (validated optimizations become permanent).
**Depends on:** Phase 2 effectiveness measurement (only synthesize skills from PROVEN patterns).
**Safety:** MANUAL tier -- skill creation always requires human review.

### TODO-007: Global Scope
**What:** Cross-project learnings stored in `~/.claude/acumen/global/`. Universal patterns that apply everywhere.
**Why:** SAGE research (Ebbinghaus forgetting curve): different learnings have different shelf lives. Some corrections are universal ("always run tests"), some are project-specific.
**Research:** SAGE (memory optimization), ALMA (meta-learn the memory design itself).
**Depends on:** Phase 1 project scope working reliably.
**Design:** Promotion from project to global requires: observed in 3+ projects, user validation, effectiveness > neutral.

### TODO-008: Session Scope (Real-Time Adaptation)
**What:** Within-conversation adaptation. If the user corrects the agent 3 times in similar ways, adapt immediately.
**Why:** Reflexion/LATS research: verbal self-reflection as the improvement signal. Real-time correction detection enables within-session learning.
**Research:** Reflexion (verbal self-reflection), MiniMax M2.7 (loop detection safeguards).
**Depends on:** Phase 1 observation (correction detection must work).
**Design:** Session learnings are ephemeral but candidates for promotion to project scope.

### TODO-009: Scope Promotion/Demotion
**What:** Rules that govern how insights move between scopes. Project insight used in 3+ projects -> promote to global. Global insight that doesn't apply in a specific project -> demote/exclude.
**Why:** ALMA research: even the memory design can be optimized. Promotion/demotion is the mechanism.
**Research:** ALMA (meta-learn memory designs), SAGE (forgetting curve).
**Depends on:** TODO-007, TODO-008.

---

## Phase 4: MULTI-AGENT SUPPORT

### TODO-010: Agent-Agnostic Observation Format
**What:** Standard observation format that works across Claude Code, Codex, Gemini, etc.
**Why:** Acumen's value increases when it works with any agent. Different agents have different hook mechanisms but observation data is universal.
**Depends on:** Phase 1-3 proven on Claude Code.
**Design:** Define a minimal observation schema. Each agent adapter translates native events to this schema.

### TODO-011: Codex Adapter
**What:** Hook into OpenAI Codex's agent system.
**Depends on:** TODO-010.

### TODO-012: Gemini CLI Adapter
**What:** Hook into Google's Gemini CLI agent system.
**Depends on:** TODO-010.

---

## Research-Inspired Future Ideas (Not Committed)

These are interesting research directions we may explore. They're NOT planned but documented so we don't lose the ideas.

### IDEA-001: Elo Tournament for Insights
**Inspiration:** Google AI Co-Scientist uses Elo-based ranking for hypothesis quality.
**Application:** When absolute scoring is ambiguous, use pairwise comparison of insights via LLM to rank them.
**Status:** Interesting but overkill for Phase 1-2. Revisit if scoring proves unreliable.

### IDEA-002: Population-Based Exploration
**Inspiration:** DGM maintains an archive tree of agent variants, enabling diversity.
**Application:** Instead of one set of CLAUDE.md rules, maintain variants and A/B test them.
**Status:** Fascinating but complex. Requires controlled experiments across sessions.

### IDEA-003: Automatic Research Direction Generation
**Inspiration:** AutoResearch's `program.md` is human-written. What if the agent generates its own research directions?
**Application:** After N reflection cycles, Acumen proposes "areas to investigate" for the next cycle.
**Status:** Phase 4+. Requires strong effectiveness measurement first.

### IDEA-004: Cross-User Skill Marketplace
**Inspiration:** SkillWeaver showed skills transfer from strong to weak agents.
**Application:** Users share proven, anonymized skills via an opt-in marketplace.
**Status:** Requires privacy framework, trust model, and a distribution mechanism. Long-term.

### IDEA-005: Forgetting Curve for Insights
**Inspiration:** SAGE uses Ebbinghaus forgetting curve for memory optimization.
**Application:** Insights that haven't been relevant for N sessions get demoted/archived. Prevents insight bloat.
**Status:** Phase 3 when we have enough data to model decay.

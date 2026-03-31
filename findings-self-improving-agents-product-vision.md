# Product Vision Research: Self-Improving AI Agents (March 2026)

Research date: 2026-03-30

---

## Executive Summary

Self-improving AI agents are crossing from research curiosity to production necessity in Q1 2026. Three converging forces make this inevitable: (1) every major AI lab has now demonstrated self-improvement loops (Karpathy's Autoresearch, MiniMax M2.7, Meta Hyperagents), (2) the agent memory market hit $6.27B in 2025 and is growing 35% CAGR, and (3) none of the dominant coding agents (Cursor at $2B ARR, Claude Code at 41% dev adoption) have built-in self-improvement. The gap is real and the window is open.

This document answers six questions from a CEO/founder perspective.

---

## 1. What Does "Self-Improving Agent" Look Like in REAL Products?

### The gap between research and product is closing fast

**Research systems (working, but not products):**
- Karpathy's Autoresearch: 700 autonomous experiments in 2 days, 54K GitHub stars in 19 days. Pure research optimization loop. Not a product -- a proof that the loop works.
- MiniMax M2.7: 100+ autonomous self-improvement rounds, 30% performance gain. The model handled 30-50% of its own development workflow. Proprietary, not a product you can buy.
- Meta Hyperagents: Self-modifying agents that rewrite their own improvement procedures. Cross-domain transfer of improvement strategies. Research framework, not shipping.

**Products that are actually shipping (or close):**

| Product | What it does | Self-improvement mechanism | Status |
|---------|-------------|---------------------------|--------|
| **Mem0** | Universal memory layer for AI apps | Continuously updates memories from interactions; 26% accuracy gains over baseline; consolidates and forgets irrelevant data | $24M raised, 80K+ developers, AWS exclusive memory provider, 186M API calls/quarter |
| **Letta Code** | Memory-first coding agent | Persistent agents that learn across sessions; memory blocks tied to projects and users; /remember command for guided memory | #1 model-agnostic agent on Terminal-Bench |
| **OpenViking** (ByteDance) | Context database for agents | Built-in memory self-iteration loop; extracts operational tips and tool experience from sessions; L0/L1/L2 tiered context loading | 15K GitHub stars, open-sourced Jan 2026 |
| **Kaizen Agent** | Meta-agent that improves other agents | Auto-generates tests, runs them, analyzes failures, suggests/applies fixes to code AND prompts, stores failures in long-term memory | Open source, early |
| **NVIDIA OpenShell** | Safe runtime for self-evolving agents | Sandboxed execution environment for agents that modify their own behavior; out-of-process policy enforcement | Apache 2.0, announced GTC March 2026 |

**Key observation:** The products that are getting traction are NOT the ones doing the most sophisticated self-improvement. They are the ones solving the simplest, most painful version of the problem: "My agent forgets everything between sessions." Memory is the wedge. Self-improvement is the moat that comes after.

### What "self-improving" means in practice today

In production, self-improvement is NOT what the research papers describe (evolutionary search, population-based optimization, RL fine-tuning). It is:

1. **Session memory extraction** -- After each session, extract what worked, what failed, user preferences
2. **Skill accumulation** -- Turn repeated patterns into reusable instructions
3. **Convention enforcement** -- Learn project-specific rules and apply them consistently
4. **Error pattern recognition** -- Identify recurring failures and prevent them

This is unglamorous compared to DGM or Hyperagents, but it is what actually ships.

**Sources:**
- [Mem0 raises $24M (TechCrunch)](https://techcrunch.com/2025/10/28/mem0-raises-24m-from-yc-peak-xv-and-basis-set-to-build-the-memory-layer-for-ai-apps/)
- [Letta Code blog](https://www.letta.com/blog/letta-code)
- [OpenViking GitHub](https://github.com/volcengine/OpenViking)
- [Kaizen Agent DEV.to](https://dev.to/suzuki_yuto_786e3bc445acb/kaizen-agent-architecture-how-our-ai-agent-improves-other-agents-466j)
- [NVIDIA OpenShell blog](https://developer.nvidia.com/blog/run-autonomous-self-evolving-agents-more-safely-with-nvidia-openshell/)

---

## 2. The Abstraction: What Pattern Do ALL Successful Self-Improving Systems Follow?

Every self-improving system -- from Autoresearch to M2.7 to Hyperagents to Voyager -- follows the same four-phase loop. The variation is in what each phase operates on.

### The Universal Loop

```
OBSERVE  -->  EVALUATE  -->  SYNTHESIZE  -->  APPLY
  |              |               |              |
  v              v               v              v
collect        judge          distill         inject
signal       outcomes       into rules     at point
from         against        or skills       of need
execution    criteria
```

**Phase 1: OBSERVE** -- Collect execution signal. Autoresearch records val_bpb. M2.7 captures failure trajectories. Acumen captures tool metadata. The key constraint: observe WITHOUT interfering. The hot path must be pure data collection.

**Phase 2: EVALUATE** -- Judge outcomes against criteria. This is where systems diverge:
- Autoresearch: single scalar metric (val_bpb) -- pure, automatable, but limited
- M2.7: self-criticism module that generates adversarial feedback
- Hyperagents: the evaluation criteria themselves evolve
- For coding agents: proxy metrics (error rate, task completion, tool failures)

**Phase 3: SYNTHESIZE** -- Distill evaluations into reusable knowledge. This is the hardest phase and where most systems are weakest:
- Autoresearch: git commit (the code change IS the knowledge)
- M2.7: markdown memory files + self-feedback chain
- Trace2Skill: automated extraction of transferable skills from traces
- ERL: heuristic pool extracted from single-attempt trajectories
- Key insight from Trace2Skill: automated synthesis outperforms hand-written knowledge

**Phase 4: APPLY** -- Inject knowledge at the point of need. NOT "dump everything into context." Successful systems use relevance scoring (ERL), tiered loading (OpenViking L0/L1/L2), or progressive disclosure (SKILL.md).

### What makes this loop compound

The loop becomes powerful when Phase 4's outputs become Phase 1's inputs. The agent applies a learned rule, observes the result, evaluates whether the rule helped, and either reinforces or revises it. This is the compound interest of self-improvement.

**The three requirements for compound improvement:**
1. **Reversibility** -- Every change can be undone (git-backed, before/after state)
2. **Measurability** -- Some signal exists to evaluate whether the change helped
3. **Decay** -- Old knowledge that stops being useful fades (SAGE's Ebbinghaus curve)

**Sources:**
- [Autoresearch (GitHub)](https://github.com/karpathy/autoresearch)
- [DGM paper](https://arxiv.org/abs/2505.22954)
- [Trace2Skill paper](https://arxiv.org/abs/2603.25158)
- [ERL paper](https://arxiv.org/abs/2603.24639)
- [Karpathy on autoresearch (NextBigFuture)](https://www.nextbigfuture.com/2026/03/andrej-karpathy-on-code-agents-autoresearch-and-the-self-improvement-loopy-era-of-ai.html)

---

## 3. Is Anyone Framing This as "Project Intelligence" or "Institutional Knowledge for AI"?

**Yes, and this is where the biggest market signal is.**

### The Knowledge Activation paper (arxiv:2603.14805, March 2026)

This paper names the core problem precisely: the "Institutional Impedance Mismatch." AI agents have general model knowledge but lack organization-specific knowledge -- architectural decisions, deployment procedures, compliance policies, incident playbooks. Without this, agents enter guess-failure-correction cycles that waste context and impose an "institutional knowledge tax" on senior engineers.

The paper proposes "Atomic Knowledge Units" (AKUs) -- minimal, self-contained bundles of institutional knowledge with seven components: intent declaration, procedural knowledge, tool bindings, organizational metadata, governance constraints, continuation paths, and validators. These are specialized versions of the SKILL.md format designed for institutional knowledge delivery.

**Key quote from the paper:** The bottleneck to effective agentic software development is not model capability but knowledge architecture.

### CLAUDE.md as the institutional knowledge primitive

Anthropic's own 2026 Agentic Coding Trends report positions CLAUDE.md (or equivalent) as the single highest-leverage action for improving agent performance. This is institutional knowledge in its simplest form: a markdown file that tells the agent how this project works.

The SKILL.md open standard extends this -- skills are now installable across 20+ coding agents (Claude Code, Cursor, Codex CLI, Gemini CLI, GitHub Copilot, Antigravity IDE). As of March 2026, there are thousands of community-contributed skills forming an ecosystem.

### Mintlify's signal

When Mintlify tripled in size, their institutional knowledge was dying in Slack threads. They built a KB agent that converts conversations into version-controlled documentation automatically. This is the same problem -- institutional knowledge trapped in formats designed for human interpretation, inaccessible to agents.

### The framing that resonates

Nobody is using the exact phrase "project intelligence" as a product category yet. But the concept is being described from multiple angles:
- "Knowledge architecture" (Knowledge Activation paper)
- "Agent memory" (Mem0, Letta, OpenViking)
- "Context engineering" (The New Stack, Anthropic)
- "Institutional knowledge delivery" (Knowledge Activation paper)

**The opportunity:** Whoever names and owns this category wins. "Project intelligence" is better than any of the existing terms because it implies (a) it is specific to a project, (b) it is actionable (intelligence, not just knowledge), and (c) it improves over time (intelligence grows).

**Sources:**
- [Knowledge Activation paper](https://arxiv.org/html/2603.14805v1)
- [SKILLS.md as the new README (Sterlites)](https://sterlites.com/blog/the-new-readme-skills-md)
- [Mintlify skill.md standard](https://www.mintlify.com/blog/skill-md)
- [Anthropic Agentic Coding Trends 2026](https://resources.anthropic.com/2026-agentic-coding-trends-report)
- [Memory for AI Agents (The New Stack)](https://thenewstack.io/memory-for-ai-agents-a-new-paradigm-of-context-engineering/)

---

## 4. Closest Analogy in the Non-AI World

### The winning analogy: Toyota Production System (TPS) / Kaizen

The analogy is not DevOps. DevOps is about pipeline automation -- making existing processes faster. The right analogy is the Toyota Production System, specifically Kaizen (continuous improvement).

**Why TPS/Kaizen is the right frame:**

| TPS Concept | Self-Improving Agent Equivalent |
|-------------|-------------------------------|
| **Andon cord** -- Any worker can stop the production line when they spot a defect | **Fail-open observation** -- Detect tool failures, error patterns, unexpected outcomes |
| **Gemba** -- Go to where the work happens to understand problems | **Metadata-only observation** -- Watch the agent work without interfering |
| **Kaizen** -- Small, continuous improvements by the people who do the work | **Incremental rule/skill updates** -- Each reflection produces a small, testable improvement |
| **Poka-yoke** -- Mistake-proofing through physical constraints | **Convention enforcement** -- Rules that prevent known-bad patterns |
| **Jidoka** -- Automation with human oversight | **SAFE tier auto-apply + human approval for REVIEW/UNSAFE** |
| **Standardized work** -- Document the best known way to perform each task | **Skills** -- Executable, version-controlled best practices |
| **PDCA cycle** (Plan-Do-Check-Act) | **OBSERVE-LEARN-IMPROVE-EXPAND** -- direct mapping |

**Why this analogy matters for positioning:**

1. **Executives understand Kaizen.** Every Fortune 500 company has run Kaizen programs. Saying "Kaizen for AI agents" immediately communicates the value proposition without needing to explain AI internals.

2. **Kaizen is proven at scale.** Toyota went from a small company to the world's largest automaker through continuous improvement. The principle is domain-independent.

3. **Kaizen is about culture, not technology.** The agents are the "workers" who continuously improve. The harness is the "production system" that enables and structures improvement. The human is the "manager" who sets direction and approves significant changes.

4. **The compounding effect is intuitive.** People understand that small improvements compound. A 1% improvement per day is a 37x improvement over a year. This is the pitch for self-improving agents.

### The analogy that does NOT work: DevOps

DevOps is about the pipeline (CI/CD, monitoring, deployment). Self-improving agents are about the worker getting better at the work itself. DevOps makes deployment faster. Kaizen makes the product better. These are orthogonal.

**Other analogies considered:**

| Analogy | Why it partially works | Why it falls short |
|---------|----------------------|-------------------|
| **Factory quality (Six Sigma)** | Measurement-driven, defect reduction | Too focused on defect elimination; misses the creative/generative aspect |
| **Spaced repetition (Anki)** | Memory decay, prioritized recall | Individual learning, not system improvement |
| **Immune system** | Pattern recognition, adaptive response | Too reactive; misses proactive improvement |
| **Evolution** | Variation + selection | Too slow, too random for product positioning |

**Sources:**
- [Kaizen Institute on AI + Kaizen](https://kaizen.com/insights/intersection-ai-kaizen-continuous-improvement/)
- [Intercom: Kaizen for the AI era](https://www.intercom.com/blog/kaizen-for-the-ai-era-how-small-improvements-build-smarter-support/)
- [Kaizen Agent GitHub](https://github.com/Kaizen-agent/kaizen-agent)
- [AWS DevOps Agent lessons](https://aws.amazon.com/blogs/devops/from-ai-agent-prototype-to-product-lessons-from-building-aws-devops-agent/)

---

## 5. What Makes a Self-Improving Agent Product INEVITABLE?

### The "inevitability argument" has five pillars

**Pillar 1: Agents are stateless by default, and that is unacceptable at scale.**

LLMs start every session with zero memory. This means every session repeats the same mistakes, asks the same clarifying questions, violates the same conventions. At individual developer scale, this is annoying. At enterprise scale (72% of Global 2000 deploying agents), this is a cost center. The agent that remembers is not a nice-to-have -- it is the minimum bar for production deployment.

**Pillar 2: The "institutional knowledge tax" is the hidden cost of AI adoption.**

The Knowledge Activation paper identifies this precisely: without institutional knowledge, agents impose a tax on senior engineers who must repeatedly externalize tacit expertise to guide corrections. As AI adoption scales (84% of developers using AI tools), this tax grows linearly with headcount. Self-improvement eliminates this tax by learning the institutional knowledge once and applying it forever.

**Pillar 3: Model upgrades are general; project knowledge is specific.**

The counterargument to self-improvement is always "just wait for the next model." But GPT-5 does not know your codebase conventions. Claude 5 does not know your deployment pipeline quirks. Model upgrades improve general capability. Self-improvement captures specific knowledge. General + specific always beats general alone. This is why Cursor is worth $29B even though the underlying models keep improving -- the value is in the specificity.

**Pillar 4: The observe-evaluate-improve loop is already happening manually.**

Every team using AI coding agents is ALREADY doing self-improvement -- manually. They write CLAUDE.md files. They add rules to .cursorrules. They create custom prompts. They share tips in Slack. The market does not need to be educated that improvement is valuable. It needs automation of what they are already doing by hand.

**Pillar 5: Compound improvement creates switching costs.**

An agent that has accumulated 6 months of project-specific knowledge, hundreds of validated rules, and a library of proven skills is irreplaceable. This is the moat investors want to see. Mem0's pitch is exactly this: persistent memory creates high switching costs because stored intelligence is unique to each customer.

### The investor pitch in one sentence

"Every AI coding agent starts every session from zero. We are the compound interest layer -- the agent that gets 1% better every session, so by month six it is 6x more productive than a fresh agent, and your team's institutional knowledge is captured in a system that compounds forever."

### What the market does not know it needs yet

The market THINKS it needs "better models" (general improvement). What it actually needs is "better memory" (specific improvement). The shift from "my AI assistant is smart" to "my AI assistant knows my project" has not happened yet at the product level. This is the transition from AI as a tool to AI as a team member. Tools are interchangeable. Team members accumulate context and get better.

The product that makes this transition visible -- a dashboard showing your agent's improvement curve, specific skills it has learned, conventions it enforces, mistakes it no longer makes -- will be the one that makes the category obvious in retrospect.

**Sources:**
- [Knowledge Activation paper](https://arxiv.org/html/2603.14805v1)
- [Insight Partners 2026 predictions](https://www.insightpartners.com/ideas/2026-investor-predictions/)
- [Anthropic Agentic Coding Trends 2026](https://resources.anthropic.com/2026-agentic-coding-trends-report)
- [Mem0 fundraise / Kindred Ventures](https://kindredventures.com/announcement/mem0-building-the-memory-infrastructure-for-personalized-ai/)
- [Agentic AI market outlook 2025-2026](https://mev.com/blog/what-2025-2026-data-reveal-about-the-agentic-ai-market)

---

## 6. The "Atomic Unit" of Improvement for a Coding Agent

### It is NOT a rule, a skill, or a convention. It is a **validated insight**.

An insight is: an observation from execution + a judgment about what it means + a tested action that results from it.

Here is why the other candidates are wrong:

| Candidate | Why it is not the atomic unit |
|-----------|------------------------------|
| **Rule** | A rule is the OUTPUT of improvement, not the unit of improvement itself. Rules are what you write AFTER you have an insight. |
| **Skill** | A skill is a COMPOSITION of multiple improvements. Skills are what you build after you have accumulated enough related insights. |
| **Convention** | A convention is a SOCIAL AGREEMENT derived from insights. It is the shared understanding, not the improvement itself. |
| **Memory** | Memory is raw data. An unprocessed memory is not an improvement -- it is an input to the improvement process. |
| **Heuristic** | Close, but heuristics are not validated. A heuristic is a guess. An insight has been tested. |

### The anatomy of a validated insight

```
INSIGHT = {
  observation:   "Tool X failed with error Y in context Z"
  hypothesis:    "This fails because of condition W"
  action:        "When context Z, do A instead of B"
  evidence:      "Applied in N sessions, success rate P%"
  confidence:    0.0 - 1.0 (grows with evidence)
  scope:         session | project | global
}
```

**The lifecycle of an insight:**

1. **Born from observation** -- The agent encounters an outcome (success or failure)
2. **Shaped by evaluation** -- A reflector judges what the observation means
3. **Crystallized into action** -- The insight becomes a concrete recommendation
4. **Validated by evidence** -- The recommendation is applied and the outcome is tracked
5. **Promoted or retired** -- High-confidence insights become rules; low-confidence ones decay

**What makes this different from just "a rule":**

A rule is static. An insight has a lifecycle. It starts uncertain, gains confidence through evidence, and can be retired when it stops being useful. This lifecycle IS the self-improvement. The agent is not just accumulating rules -- it is running a continuous experiment on what works.

### How insights compose into higher-order structures

```
INSIGHTS  -->  cluster by topic  -->  CONVENTIONS
INSIGHTS  -->  chain into workflows  -->  SKILLS
INSIGHTS  -->  apply to CLAUDE.md  -->  RULES
INSIGHTS  -->  aggregate across projects  -->  BEST PRACTICES
```

The insight is atomic because it cannot be decomposed further while retaining its meaning. A rule without its evidence is just an assertion. A skill without its constituent insights is just a script. The insight -- observation + judgment + tested action -- is the irreducible unit.

### What Karpathy, M2.7, and the research confirms

- Autoresearch: The atomic unit is a code change + its measured outcome (val_bpb delta). This is an insight in code form.
- M2.7: The atomic unit is a memory markdown file + self-criticism + optimization direction. This is an insight with embedded evaluation.
- Trace2Skill: The atomic unit is a trajectory-specific lesson extracted from execution traces. This is an insight derived from observation.
- ERL: The atomic unit is a heuristic extracted from a single attempt trajectory. This is an insight at its most minimal.

They all converge on the same thing: a unit of knowledge that includes BOTH the observation and the judgment about what to do about it.

**Sources:**
- [Trace2Skill paper](https://arxiv.org/abs/2603.25158)
- [ERL paper](https://arxiv.org/abs/2603.24639)
- [M2.7 model page](https://www.minimax.io/models/text/m27)
- [A-MEM paper (Zettelkasten for agents)](https://arxiv.org/abs/2502.12110)

---

## 7. The Competitive Moment (March 2026)

### What just happened in the last 30 days

- **March 7:** Karpathy releases Autoresearch. 54K stars in 19 days. Proves self-improvement loops work.
- **March 15:** ByteDance open-sources OpenViking. 15K stars. Proves agent memory/context is a category.
- **March 16:** NVIDIA releases OpenShell at GTC. Provides safe runtime for self-evolving agents. Enterprise validation.
- **March 18:** MiniMax releases M2.7. Demonstrates a model that improved itself through 100+ autonomous rounds.
- **March 23:** Meta publishes Hyperagents. Shows improvement strategies transfer across domains.
- **March 26:** YC W26 Demo Day. Agent share drops to 19% while infrastructure share rises to 40%+. The market is shifting from "agents" to "agent infrastructure."

### The window

None of the dominant coding agents (Cursor, Claude Code, GitHub Copilot, Windsurf) have built self-improvement natively. They all rely on model upgrades for improvement. The first product to make coding agents demonstrably self-improving -- with a visible improvement curve, not just memory -- owns a new category.

The window is 6-12 months before the platforms build this themselves. Anthropic could add self-improvement to Claude Code. Cursor could add learning across sessions. But platform companies are slow to add non-core features, and self-improvement is a surprisingly hard product problem (what to remember, what to forget, how to validate, how to measure).

### What makes Acumen's position strong

1. **Already building in the right direction** -- OBSERVE -> LEARN -> IMPROVE -> EXPAND maps directly to the universal loop every research system uses
2. **Zero dependencies** -- No database, no API keys, no network calls. This is the right design for a plugin that needs to be invisible
3. **Metadata-only observation** -- The safety decision (never capture inputs/outputs) is validated by DGM research on sensitive data in self-improving systems
4. **Plugin model** -- Works with the dominant tool (Claude Code) without replacing it. The wedge is right
5. **The SKILL.md standard exists** -- Skills are now a cross-platform primitive. Acumen's EXPAND phase can produce skills that work everywhere

---

## 8. The One-Slide Product Vision

**Problem:** Every AI coding agent starts every session from zero. Teams spend hours re-teaching their agents the same conventions, patterns, and project knowledge. This "institutional knowledge tax" grows linearly with team size and agent usage.

**Solution:** Acumen is Kaizen for AI coding agents -- continuous improvement that happens automatically. Install in one command. The agent observes its own sessions, extracts insights, validates them, and applies them. Your agent gets measurably better every week.

**Why now:** The research is proven (Autoresearch, M2.7, Hyperagents). The infrastructure exists (SKILL.md standard, Claude Code plugin system). The market is ready (41% of devs on Claude Code, none with self-improvement). The enterprise need is acute (72% of Global 2000 deploying agents, all need them to improve).

**Why us:** Already building. Metadata-only observation (privacy by design). Zero dependencies (no infrastructure to manage). Plugin model (works with the dominant tool). The right architecture validated by 2025-2026 research.

**The moat:** Compound improvement creates irreplaceable value. After 6 months of learning, your agent's accumulated project intelligence is unique, validated, and growing. Switching costs increase with every session. Network effects (anonymized, aggregated insights across the user base) compound this further.

**The expansion:** Coding agent plugin (now) -> cross-agent improvement platform (12mo) -> enterprise agent optimization layer (24mo).

---

## 9. Key Risks Revisited

| Risk | Severity | Mitigation |
|------|----------|------------|
| Anthropic builds this natively | HIGH | Move fast, build data moat, become the acquisition target. Anthropic is focused on model capability, not plugin-level learning |
| "Models will just get better" | MEDIUM | General + specific always beats general alone. This argument has been wrong for every layer of the stack (still need CI/CD even though code improved) |
| Hard to measure improvement | MEDIUM | Solvable with good metrics. The product that makes improvement visible wins. Dashboard showing improvement curve is table stakes |
| Privacy/safety concerns | LOW | Metadata-only observation is the right design. Privacy-by-design is a competitive advantage, not a constraint |
| Market timing too early | LOW | YC W26 signal (infrastructure shift), enterprise adoption (72% Global 2000), and developer behavior (everyone writes CLAUDE.md manually) all confirm timing is right |
| Open source kills monetization | MEDIUM | Open core model. Free plugin, paid for team features (shared learning, analytics, enterprise compliance). Mem0 model works ($24M raised, open source) |

---

## Summary: The Six Answers

1. **What does self-improvement look like in real products?** Memory extraction from sessions, skill accumulation, convention enforcement, error pattern recognition. Unglamorous but shippable. Mem0, Letta Code, and OpenViking are the closest production examples.

2. **What is the abstraction?** OBSERVE -> EVALUATE -> SYNTHESIZE -> APPLY, with compound feedback. Every successful system follows this loop. The variation is in what each phase operates on.

3. **Is anyone framing this as project intelligence?** Not yet by that name, but the concept exists under "knowledge activation," "context engineering," and "agent memory." The category is unnamed and ownable.

4. **Closest non-AI analogy?** Toyota Production System / Kaizen. Small, continuous improvements by the agents that do the work, structured by a system that makes improvement measurable and reversible.

5. **What makes it inevitable?** Five forces: agents are stateless by default, institutional knowledge tax grows with scale, model upgrades are general not specific, teams are already doing manual improvement, and compound improvement creates switching costs.

6. **What is the atomic unit of improvement?** A validated insight -- observation + judgment + tested action + evidence. Not a rule (rules are outputs of insights). Not a skill (skills compose from insights). Not memory (memory is raw input). The insight lifecycle IS the self-improvement.

# Research: Self-Improving AI Coding Agents (March 2026)

## 1. Karpathy's Autoresearch

**What it is:** An open-source system (released March 7, 2026) that gives an AI coding agent a real LLM training setup and lets it experiment autonomously overnight. 21,000+ GitHub stars within days.

**Core loop:** The agent reads its own source code, forms a hypothesis for improvement, modifies the code, trains for exactly 5 minutes, evaluates a single scalar metric (val_bpb -- validation bits per byte), and either keeps (git commit) or discards (git reset) the change. Then repeats forever.

**Three-file architecture:**
- `prepare.py` -- Data prep + evaluation utilities. **Immutable.** Guarantees every experiment is measured against the same yardstick.
- `train.py` -- The single file the agent edits. Contains the full GPT model, optimizer (Muon + AdamW), and training loop. Everything is fair game.
- `program.md` -- Natural language instructions for the agent. The only file the human touches. Contains "LOOP FOREVER" at line 94.

**Key design primitives:**
1. **Editable asset** -- A single file the agent can modify, keeping the search space interpretable
2. **Scalar metric** -- A single number (val_bpb) that determines improvement, computable without human judgment
3. **Time-boxed cycle** -- Fixed 5-minute duration makes every experiment directly comparable (~12 experiments/hour, ~100 overnight)

**Results:** Over 2 days, the agent processed ~700 autonomous changes, found ~20 additive improvements that transferred to larger models. Dropped "Time to GPT-2" metric from 2.02 hours to 1.80 hours (11% efficiency gain). Discovered real things: QKnorm missing a scaler multiplier, value embedding regularization benefits, banded attention tuning, AdamW beta optimization, weight decay scheduling.

**Applicability to Acumen:**
- The hypothesis-experiment-evaluate-commit/revert loop is the gold standard pattern for self-improvement
- Single scalar metric as the arbiter is crucial -- without a clear metric, you can't automate improvement
- The three-file separation (immutable evaluator / editable target / human instructions) is a clean architecture
- Git as the versioning/rollback mechanism is elegant and zero-dependency
- "LOOP FOREVER" -- the agent never asks for permission, just keeps improving
- Key limitation: requires a computable metric. For coding agents, the "metric" is harder to define than val_bpb

**Sources:**
- [GitHub repo](https://github.com/karpathy/autoresearch)
- [program.md instructions](https://github.com/karpathy/autoresearch/blob/master/program.md)
- [VentureBeat coverage](https://venturebeat.com/technology/andrej-karpathys-new-open-source-autoresearch-lets-you-run-hundreds-of-ai)
- [The New Stack: 630-line script](https://thenewstack.io/karpathy-autonomous-experiment-loop/)
- [DataCamp guide](https://www.datacamp.com/tutorial/guide-to-autoresearch)

---

## 2. MiniMax M2.7

**What it is:** A proprietary model from MiniMax that deeply participates in its own evolution. Built on the OpenClaw agent harness framework. 204,800-token context window, ~60 TPS standard, ~100 TPS highspeed variant.

**Self-evolution mechanism:** M2.7 ran entirely autonomously through an iterative loop:
1. Analyze failure trajectories
2. Plan changes
3. Modify scaffold code
4. Run evaluations
5. Compare results
6. Decide to keep or revert changes

This ran for 100+ rounds without human intervention, achieving 30% performance improvement on internal evaluations.

**Agent harness architecture (three core modules):**
1. **Short-term memory** -- After each iteration, the agent generates a markdown file capturing what happened
2. **Self-feedback** -- Simultaneously performs self-criticism on the current round's results, identifying potential optimization directions
3. **Self-optimization** -- Next round uses the memory + self-feedback chain from ALL previous rounds to guide further changes

**Key stats:**
- 97% skill adherence rate while working with 40+ complex skills (each 2,000+ tokens)
- 3 trials of 24 hours each for iterative evolution
- Best run: 9 gold medals, 5 silver, 1 bronze (competition context)
- Interleaved hidden chain-of-thought for verification before outputting code

**Applicability to Acumen:**
- The three-module architecture (short-term memory / self-feedback / self-optimization) maps directly to Acumen's OBSERVE -> LEARN -> IMPROVE cycle
- Markdown files as the memory format -- exactly what Acumen already does
- Self-criticism after each round is a key mechanism: not just "what happened" but "what went wrong and what could be better"
- The accumulating chain of memory + feedback across rounds is how you build compound improvement
- 97% skill adherence with 40+ skills proves that a well-designed harness can handle complexity
- Key insight: the harness itself is the editable target, not just the model's weights

**Sources:**
- [MiniMax official blog post](https://www.minimax.io/news/minimax-m27-en)
- [MiniMax M2.7 model page](https://www.minimax.io/models/text/m27)
- [VentureBeat coverage](https://venturebeat.com/technology/new-minimax-m2-7-proprietary-ai-model-is-self-evolving-and-can-perform-30-50)
- [WaveSpeedAI analysis](https://wavespeed.ai/blog/posts/minimax-m2-7-self-evolving-agent-model-features-benchmarks-2026/)

---

## 3. Self-Improving AI Coding Agents (Landscape)

### 3a. Darwin Godel Machine (DGM) -- Sakana AI / UBC, May 2025

**What it is:** A self-improving system inspired by Darwinian evolution. Maintains a growing archive/population of agents. Agents are selected, self-modify to create new versions, and the archive grows as a tree of diverse, high-quality agents.

**Architecture:**
- Initialized with a single base coding agent (frozen foundation model + Bash tool + Edit tool)
- Each iteration: select an agent from archive, it self-modifies its own code to create a child agent
- Child agents that compile and retain code-editing ability are kept (even if temporarily worse -- diversity matters)
- Evaluated on downstream benchmarks (SWE-bench, Polyglot)
- 80 iterations, 2 parallel for SWE-bench, 4 for Polyglot

**Results:** SWE-bench: 20.0% -> 50.0%. Polyglot: 14.2% -> 30.7%.

**Key insight:** Open-ended exploration (keeping "interesting" mutations even if they score lower) outperforms greedy hill-climbing. This is because innovative traits may combine with other beneficial characteristics in later generations.

**Applicability to Acumen:**
- Population/archive approach is interesting but heavy for a plugin
- The key lesson is: don't just keep the best -- keep diverse approaches and let them cross-pollinate
- Self-modification of the agent's own tools/scaffold is the core mechanism
- Empirical validation over mathematical proof -- pragmatic, testable improvement

**Sources:**
- [arXiv paper](https://arxiv.org/abs/2505.22954)
- [Sakana AI blog](https://sakana.ai/dgm/)
- [GitHub](https://github.com/jennyzzt/dgm)

### 3b. SICA (Self-Improving Coding Agent) -- University of Bristol, April 2025

**What it is:** Eliminates the distinction between meta-agent and target agent. The same agent that performs tasks also evaluates past performance, identifies shortcomings, and updates its own implementation.

**Architecture:**
- Starts with minimal code required for initial self-improvement
- Iterates: benchmark current implementation -> generate improvements to own code
- Keeps an archive of previous agents + benchmark results
- Best-performing agent becomes the meta-agent for the next iteration
- Utility function: U = w_score * p_score + w_cost * (1 - min(1, p_cost/$10)) + w_time * (1 - min(1, p_time/300s))

**Key distinction from DGM:** SICA unifies meta-agent and task-agent. The agent that solves the problem is the same agent that improves the solver. Improvements come from changes in tool orchestration, file management strategies, and problem decomposition heuristics -- NOT weight updates.

**Results:** 17% to 53% improvement on SWE-bench Verified subset. File editing performance: 82% -> 94%.

**Applicability to Acumen:**
- The unified meta/task agent is the most relevant architecture for Acumen -- the coding agent IS the thing being improved
- Improvements via scaffold changes (tool orchestration, strategies, heuristics) rather than model retraining is exactly Acumen's approach
- The multi-dimensional utility function (performance + cost + time) is more practical than a single metric
- Archive of previous agents with their results provides the learning history

**Sources:**
- [arXiv paper](https://arxiv.org/abs/2504.15228)
- [GitHub](https://github.com/MaximeRobeyns/self_improving_coding_agent)

### 3c. Hyperagents -- Meta AI, March 2026

**What it is:** Extends DGM into DGM-Hyperagents (DGM-H) where the meta-level modification procedure is itself fully editable. The agent can rewrite the rules of how it generates better versions of itself.

**Key innovation:** Resolves the infinite regress problem. Prior systems had fixed human-designed improvement logic. Hyperagents merge task agent + meta agent into a single editable program, so the agent improves BOTH at the task AND at the process of self-improvement.

**Results:**
- Polyglot: 0.084 -> 0.267
- Paper review: 0.0 -> 0.710
- Robotics reward design: 0.060 -> 0.372
- Cross-domain transfer: hyperagents optimized on paper review transferred to math grading achieved imp@50 of 0.630, while human-customized DGM scored 0.0

**Emergent behaviors:** Without explicit instruction, hyperagents developed:
- Performance tracking classes to log metrics across generations
- Persistent memory with timestamped storage for synthesized insights
- Causal hypotheses about what makes improvements work

**Applicability to Acumen:**
- The most theoretically ambitious approach -- self-improvement of self-improvement
- Cross-domain transfer of improvement strategies is powerful: skills learned in one domain help in others
- Emergent tool development (the agent building its own tracking/memory tools) validates Acumen's approach of letting the agent build its own capabilities
- Practically, the full DGM-H loop is too heavy for a plugin, but the PRINCIPLE of making the improvement process itself improvable is applicable
- The emergent memory/tracking behavior suggests these capabilities should be built in from the start

**Sources:**
- [arXiv paper](https://arxiv.org/abs/2603.19461)
- [GitHub](https://github.com/facebookresearch/Hyperagents)
- [MarkTechPost analysis](https://www.marktechpost.com/2026/03/23/meta-ais-new-hyperagents-dont-just-solve-tasks-they-rewrite-the-rules-of-how-they-learn/)

### 3d. ADAS (Automated Design of Agentic Systems) -- ICLR 2025 Oral

**What it is:** Meta Agent Search -- a "meta" agent iteratively programs new agents in code, tests them, adds to an archive, and uses the archive to inform subsequent iterations.

**Three key components:**
1. Search space (programming languages -- can represent any agent)
2. Search algorithm (meta-agent explores the space)
3. Evaluation function (benchmarks candidate agents)

**Applicability to Acumen:**
- Code as the search space for agent design is the right abstraction
- The archive of discovered agents with performance history is a reusable pattern
- Agents invented by Meta Agent Search transfer across domains and models

**Sources:**
- [arXiv paper](https://arxiv.org/abs/2408.08435)
- [GitHub](https://github.com/ShengranHu/ADAS)
- [Project page](https://www.shengranhu.com/ADAS/)

---

## 4. Meta-Learning and Experience-Based Improvement

### 4a. Trace2Skill -- March 2026

**What it is:** Automated extraction of transferable agent skills from execution traces. Instead of humans writing skill files, Trace2Skill dispatches parallel sub-agents to analyze diverse execution traces, extract trajectory-specific lessons, and hierarchically consolidate them into a unified skill directory.

**How it works:**
1. Collect a diverse pool of agent execution traces (success and failure)
2. Dispatch parallel sub-agents to analyze traces
3. Extract trajectory-specific lessons
4. Hierarchically consolidate via inductive reasoning into conflict-free skill directory

**Key result:** Skills evolved by Qwen3.5-35B on its own trajectories improved a Qwen3.5-122B agent by up to 57.65 percentage points. Trace-based skills outperformed Anthropic's official enterprise baselines.

**Applicability to Acumen:**
- This is DIRECTLY what Acumen's LEARN phase should do -- extract transferable skills from session traces
- Parallel analysis of success/failure traces is more effective than sequential processing
- Skills transfer across model scales -- insights extracted by smaller models help larger ones
- Hierarchical consolidation prevents conflicting/redundant skills
- The finding that automated trace-based skills outperform hand-written skills validates Acumen's entire premise

**Sources:**
- [arXiv paper](https://arxiv.org/abs/2603.25158)

### 4b. Experiential Reflective Learning (ERL) -- March 2026

**What it is:** A memory framework for efficient self-improvement without fine-tuning. Builds a pool of reusable heuristics from past experience trajectories and their outcomes.

**How it works:**
1. Agent attempts tasks, generating trajectories
2. Heuristics are extracted from single-attempt trajectories (not requiring repeated execution)
3. For each new task, an LLM scores stored heuristics for relevance
4. Top-scoring heuristics are injected into agent context as task-specific guidance

**Key advantage:** Extracts heuristics from single-attempt trajectories -- no need for curated training sets or repeated execution.

**Result:** 56.1% success rate on Gaia2 (+7.8% over ReAct baseline, outperforms ExpeL and AutoGuide).

**Applicability to Acumen:**
- Single-attempt heuristic extraction is practical for real-world coding sessions (you can't rerun sessions)
- Relevance scoring before injection prevents context pollution
- The heuristic pool is exactly what Acumen's insight store should be
- No fine-tuning required -- pure in-context learning

**Sources:**
- [arXiv paper](https://arxiv.org/abs/2603.24639)

### 4c. ExpeL (Experiential Learning) -- AAAI 2024

**What it is:** An agent that autonomously gathers experiences and extracts knowledge using natural language from training tasks.

**Two-phase approach:**
1. **Training:** Agent interacts via trial and error, stores experiences. Then extracts insights by comparing failed vs. successful trajectories for the same task, and identifying patterns across successful trajectories of different tasks.
2. **Evaluation:** Agent attempts unseen tasks augmented with extracted insights and successful trajectories.

**Key mechanism:** Cross-task learning by accumulating task experience. The agent compares failures and successes to derive generalizable rules.

**Applicability to Acumen:**
- Comparing failed vs. successful approaches for the same type of task is a powerful insight extraction strategy
- Cross-task pattern identification builds generalizable knowledge
- The insight accumulation approach (performance improves as experience grows) validates long-term memory

**Sources:**
- [arXiv paper](https://arxiv.org/abs/2308.10144)
- [GitHub](https://github.com/LeapLabTHU/ExpeL)

### 4d. SAGE (Self-Evolving Agents with Reflective Memory) -- NeurIPS 2025

**What it is:** Three-agent framework (User, Assistant, Checker) integrating iterative feedback, reflective reasoning, and memory optimization based on the Ebbinghaus forgetting curve.

**Memory mechanism:** Uses the Ebbinghaus forgetting curve to dynamically prioritize high-value information and prune trivial data. Separates working memory, episodic memory, and semantic memory.

**Key technique:** Explicit self-critique over own trajectories, extracting "lessons learned" that are re-injected as guiding context.

**Results:** Up to 2.26X performance enhancement on AgentBench for GPT-4.

**Applicability to Acumen:**
- Memory decay/prioritization (Ebbinghaus curve) prevents memory bloat -- stale insights should decay
- Three-tier memory (working/episodic/semantic) maps to Acumen's session/project/global scopes
- Self-critique is different from self-reflection -- it's specifically adversarial ("what went wrong") rather than descriptive

**Sources:**
- [arXiv paper](https://arxiv.org/abs/2409.00872)

### 4e. A-MEM (Agentic Memory) -- NeurIPS 2025

**What it is:** Self-organizing memory system inspired by the Zettelkasten method. Creates interconnected knowledge networks through dynamic indexing and linking.

**Key components:**
- **Link Generation:** When a new memory is added, finds nearest neighbors in embedding space, uses LLM to decide which to link to
- **Memory Evolution:** Revisits neighbors of new notes and asks LLM whether their fields should be updated as context accumulates
- Generates structured notes with contextual descriptions, keywords, and tags

**Result:** Doubles performance on complex multi-hop reasoning tasks.

**Applicability to Acumen:**
- Self-organizing memory that evolves as new information arrives is more robust than static storage
- Link generation between related insights creates a knowledge graph
- Memory evolution (updating old insights when new related ones arrive) prevents staleness
- The Zettelkasten approach (atomic notes with links) is a proven knowledge management pattern

**Sources:**
- [arXiv paper](https://arxiv.org/abs/2502.12110)
- [GitHub](https://github.com/agiresearch/A-mem)

### 4f. EvolveR -- October 2025

**What it is:** Closed-loop experience lifecycle with offline self-distillation and online interaction.

**Two phases:**
1. **Offline Self-Distillation:** Freeze agent policy, distill raw trajectories into strategic principles
2. **Online Interaction:** Agent uses distilled principles to guide decision-making, generating new trajectories
3. **Policy Evolution:** New trajectories used to update agent via RL (closes the loop)

**Applicability to Acumen:**
- The offline distillation phase (turning raw traces into strategic principles) is what Acumen's reflection should do
- Separation of "distill" and "apply" phases is clean
- The closed loop (apply -> generate new data -> distill again) is the compound improvement cycle

**Sources:**
- [arXiv paper](https://arxiv.org/abs/2510.16079)

### 4g. Voyager -- 2023 (foundational)

**What it is:** LLM-powered embodied agent in Minecraft with a continuously growing skill library.

**Three components:**
1. **Automatic curriculum** -- Maximizes exploration by dynamically proposing tasks
2. **Skill library** -- Ever-growing collection of executable code for storing/retrieving complex behaviors
3. **Iterative prompting** -- Incorporates environment feedback, execution errors, and self-verification

**Key insight:** Skills are temporally extended, interpretable, and compositional. They compound the agent's abilities and prevent catastrophic forgetting.

**Applicability to Acumen:**
- The skill library pattern (executable code snippets that compose) is foundational for Acumen's skills system
- Automatic curriculum (the agent decides what to learn next) could inform Acumen's learning prioritization
- Self-verification before storing a skill ensures quality

**Sources:**
- [arXiv paper](https://arxiv.org/abs/2305.16291)
- [Project page](https://voyager.minedojo.org/)

### 4h. Reflexion -- NeurIPS 2023 (foundational)

**What it is:** Verbal reinforcement learning. Instead of gradient updates, the agent reflects on failures in natural language, stores reflections in episodic memory, and uses them to improve on subsequent attempts.

**Architecture:** Actor (generates actions) + Evaluator (scores output) + Self-Reflection model (generates verbal reinforcement cues).

**Key mechanism:** Converts binary/scalar feedback into verbal feedback (textual summary) added as context for the next episode. Acts as a "semantic gradient."

**Applicability to Acumen:**
- The "semantic gradient" concept is directly applicable -- natural language reflections as the improvement signal
- Episodic memory buffer of reflections is what Acumen's insight store is
- Lightweight, no fine-tuning needed
- 91% pass@1 on HumanEval proves the approach works for coding

**Sources:**
- [arXiv paper](https://arxiv.org/abs/2303.11366)
- [GitHub](https://github.com/noahshinn/reflexion)

### 4i. Contextual Experience Replay (CER) -- ACL 2025

**What it is:** Training-free framework for self-improvement within the context window. Accumulates and synthesizes past experiences into a dynamic memory buffer.

**Key finding:** LLM agents display an "experience-following property" -- high similarity between a task input and a retrieved memory often results in highly similar outputs. This creates both benefits (knowledge reuse) and risks (error propagation, misaligned replay).

**Applicability to Acumen:**
- Experience-following property means bad memories propagate bad behavior -- quality control on stored insights is critical
- Multi-level experience design (low-level concrete sequences + high-level procedural knowledge) provides the right abstraction layers

**Sources:**
- [arXiv paper](https://arxiv.org/abs/2506.06698)

### 4j. Meta-RL for Language Agents (LaMer, MAGE, ReMA) -- 2025-2026

**LaMer:** Cross-episode training framework encouraging exploration + long-term reward optimization. In-context policy adaptation via reflection without gradient updates.

**MAGE:** Multi-episode training where interaction history + reflections from previous episodes are integrated into the context window. Optimizes policy across interaction trajectories via RL.

**ReMA:** Decouples reasoning into high-level meta-thinking agent (strategic oversight) and low-level reasoning agent (detailed execution).

**Applicability to Acumen:**
- Cross-episode learning (using history from prior sessions to improve future ones) is Acumen's core value proposition
- The high-level/low-level split (strategic oversight vs. detailed execution) maps to Acumen's insight hierarchy
- Exploration vs. exploitation tradeoff is relevant: the agent should try new approaches, not just repeat what worked

**Sources:**
- [LaMer](https://arxiv.org/abs/2512.16848)
- [MAGE](https://arxiv.org/html/2603.03680)
- [ReMA](https://arxiv.org/abs/2503.09501)

---

## Synthesis: What This Means for Acumen

### Validated Patterns (Acumen should use these)

1. **Observe-Reflect-Improve loop** -- Every system uses some variant. Acumen's OBSERVE -> LEARN -> IMPROVE -> EXPAND is the right structure.

2. **Markdown as memory format** -- MiniMax M2.7, Trace2Skill, and the Agent Skills standard all use markdown. Acumen is already doing this right.

3. **Git as versioning/rollback** -- Karpathy's autoresearch uses git commit/reset as the improvement mechanism. Acumen's CLAUDE.md modifications should be tracked via git for reversibility.

4. **Heuristic extraction from single trajectories** -- ERL proves you don't need repeated execution. A single session's trace is enough to extract useful insights.

5. **Cross-task insight transfer** -- ExpeL, Trace2Skill, and Hyperagents all show that insights generalize across tasks and even across models.

6. **Self-criticism over self-description** -- SAGE and M2.7 both emphasize adversarial self-critique ("what went wrong") rather than neutral summarization.

7. **Memory decay/prioritization** -- SAGE's Ebbinghaus curve approach prevents memory bloat. Stale insights should lose priority over time.

8. **Skill composability** -- Voyager shows skills should be compositional and executable, not just descriptive text.

### Architecture Insights for Acumen

1. **Acumen's reflection phase should compare failed vs. successful approaches** for similar task types (ExpeL pattern), not just summarize what happened.

2. **Insights should be scored for relevance** before injection into context (ERL pattern). Don't dump everything -- pick the most relevant.

3. **The insight store should be self-organizing** -- new insights should link to related existing ones and potentially update them (A-MEM pattern).

4. **Skill extraction from traces should be automated** -- Trace2Skill shows this outperforms hand-written skills. Acumen's EXPAND phase should generate skills from accumulated insights automatically.

5. **Quality control on stored insights is critical** -- CER shows that bad memories propagate bad behavior. Insights need validation before they influence future sessions.

6. **The improvement process itself should be improvable** -- Hyperagents' key insight. Acumen's reflection prompts and scoring mechanisms should themselves be subject to improvement over time.

### What NOT to Copy

1. **Population-based approaches** (DGM, ADAS) are too heavy for a plugin. Acumen should use a single-agent improvement loop, not evolutionary search.

2. **RL-based policy updates** (EvolveR, MAGE) require fine-tuning infrastructure. Acumen is training-free by design.

3. **Multi-agent architectures** (SAGE's three agents, ReMA's two-level system) add complexity. The unified agent (SICA approach) is more appropriate for a plugin.

4. **Benchmark-driven evaluation** works for research but not for real-world coding. Acumen needs proxy metrics (error rates, tool failures, session outcomes) rather than standardized benchmarks.

---

## 5. Self-Improving Agents in Robotics, Embodied AI, and Physical Autonomy (March 2026)

### 5a. The "Physical AI" Wave -- Market Context

**2026 is being called "The Year Intelligence Gets Physical."** The convergence of foundation models with robotics has created a new category called "Physical AI" -- systems that perceive, reason about, and act in the physical world autonomously.

**Market numbers:**
- Global AI-in-drone market: $12.3B (2024) projected to $51.3B by 2033 (~17.9% CAGR)
- Industrial robot installed base: 5.5M units by 2026, surging past 1M units/year by 2030
- Humanoid robot shipments: ~5,000-7,000 in 2025, ~15,000 in 2026, market worth $210-270M in 2026, potentially $600M-$1B by 2032
- 58% of surveyed business leaders already use physical AI in operations; 80% plan to within 2 years (Deloitte survey, 3,200+ global leaders)

**Sources:**
- [Deloitte Tech Trends 2026: Physical AI](https://www.deloitte.com/us/en/insights/topics/technology-management/tech-trends/2026/physical-ai-humanoid-robots.html)
- [Deloitte AI for Robots and Drones](https://www.deloitte.com/us/en/insights/industry/technology/technology-media-and-telecom-predictions/2026/ai-for-robots-drones.html)
- [Edge AI Vision: 2026 Intelligence Gets Physical](https://www.edge-ai-vision.com/2026/03/2026-the-year-intelligence-gets-physical/)
- [Analog Devices: 2026 Intelligence Gets Physical](https://www.analog.com/en/newsroom/press-releases/2026/2-9-2026-the-year-intelligence-gets-physical.html)
- [PR Newswire: AI Drone Market](https://www.prnewswire.com/news-releases/billions-in-flight-ai-and-autonomous-drone-technologies-set-to-disrupt-global-markets-302724048.html)

---

### 5b. Self-Evolving Embodied AI -- The Defining Paper (arXiv:2602.04411, Feb 2026)

**What it is:** A comprehensive framework for embodied AI agents that autonomously learn, adapt, and evolve through continuous interaction with physical environments. Published February 2026.

**Five coupled self-evolution modules:**

1. **Memory Self-Updating** -- Agents selectively retain, revise, or discard experiences. Prioritizes rare but consequential interaction failures over routine successes. Mechanisms include memory editing, organization, and distillation.

2. **Task Self-Switching** -- Agents autonomously adjust objectives rather than following fixed goals. Can select from evolving candidate tasks or generate entirely new tasks online based on environmental changes and user intent.

3. **Environment Self-Prediction** -- Agents maintain and refine internal world models (both latent predictive representations and generative models) to anticipate future states before acting.

4. **Embodiment Self-Adaptation** -- Systems adapt to heterogeneous robot morphologies, sensing modalities, actuation capabilities, and physical constraints through reconfiguration, calibration, and recovery.

5. **Model Self-Evolution** -- The agent's own architectures, optimization strategies, and evaluation criteria evolve through restructuring, optimization, and self-evaluation. Not just the weights -- the entire model paradigm is subject to change.

**Key design principle:** These modules form a unified closed-loop. Changes in one component propagate through the loop and induce adaptive responses in others, creating co-evolution across fast timescales (in-episode adaptation) and slow timescales (cross-episode learning).

**Three critical open problems identified:**
- **Controllable Self-Evolution:** Preventing unintended behavioral drift while enabling genuine improvement. Need hierarchical control architectures and quantifiable stability metrics.
- **Trustworthy Self-Evolution:** Safety and transparency in real-world deployment. Requires monitoring, auditing, and rollback mechanisms for harmful adaptations.
- **Swarm Self-Evolution:** Extending individual agent adaptation to multi-agent collectives with distributed memory sharing and emergent behavior alignment.

**Sources:**
- [arXiv:2602.04411](https://arxiv.org/html/2602.04411)

---

### 5c. Hyperagents in Robotics (Meta AI, March 2026)

**What it is:** Meta's Hyperagents framework (arXiv:2603.19461) was tested explicitly on robotics reward design, among other domains.

**Robotics application:** The hyperagent was tasked with designing Python reward functions to train a quadruped robot in the Genesis simulator. Performance rose from an initial score of 0.060 to 0.372 through autonomous self-modification of both the task-solving code and the self-improvement process itself.

**Cross-domain transfer result:** Hyperagents optimized on paper review and robotics tasks achieved an improvement score of 0.630 when transferred to Olympiad-level math grading, while traditional human-customized methods scored 0.0. This demonstrates that self-improvement strategies learned in robotics can transfer to entirely different domains.

**Emergent engineering tools:** Without instruction, hyperagents autonomously developed performance tracking (logging metrics across generations), persistent memory (timestamped storage for insights), and compute-aware planning -- all of which are directly relevant to robot self-improvement.

**Sources:**
- [arXiv:2603.19461](https://arxiv.org/abs/2603.19461)
- [MarkTechPost analysis](https://www.marktechpost.com/2026/03/23/meta-ais-new-hyperagents-dont-just-solve-tasks-they-rewrite-the-rules-of-how-they-learn/)
- [MLQ analysis](https://mlq.ai/news/meta-releases-hyperagents-self-modifying-ai-framework-enabling-autonomous-improvement-mechanisms/)

---

### 5d. Google DeepMind SIMA 2 -- Self-Improving Embodied Agent (Dec 2025)

**What it is:** A generalist embodied agent built on Gemini that acts in 3D virtual worlds. Demonstrates self-improvement in novel environments without human demonstrations.

**Self-improvement mechanism:** SIMA 2 uses Gemini to autonomously generate tasks and provide rewards. It adds information to a bank of self-generated experience, which the agent uses for further training in subsequent generations. The agent improves on previously failed tasks entirely independently of human-generated demonstrations.

**Generalization:** Substantially closes the gap with human performance. SIMA 1 completed 31% of complex tasks (humans: 71%); SIMA 2 roughly doubles to ~65%. Generalizes to unseen photorealistic environments generated by Genie 3.

**Relevance to physical AI:** While SIMA 2 operates in virtual 3D worlds, the self-improvement loop (attempt -> fail -> self-generate training experience -> improve -> re-attempt) is the same pattern that physical robots need. The key insight is that the agent generates its own curriculum.

**Sources:**
- [DeepMind blog](https://deepmind.google/blog/sima-2-an-agent-that-plays-reasons-and-learns-with-you-in-virtual-3d-worlds/)
- [arXiv:2512.04797](https://arxiv.org/abs/2512.04797)
- [InfoQ coverage](https://www.infoq.com/news/2025/12/sima-2-gemini-agent/)

---

### 5e. NVIDIA's Physical AI Stack (2025-2026)

**What it is:** NVIDIA has built the most comprehensive infrastructure stack for robot learning and self-improvement, positioning itself as the platform layer for physical AI.

**Key components:**
- **Isaac GR00T N1.6** -- Foundation Vision-Language-Action (VLA) model for humanoid robots. Trained via imitation learning and RL in simulation. Enables zero-shot transfer and cross-embodiment performance with minimal finetuning.
- **Isaac Lab** -- Open-source modular framework for robot learning in simulation. The foundational training framework for GR00T.
- **Cosmos models** -- World models for synthetic data generation (Cosmos Transfer 2.5, Cosmos Predict 2.5) and robot policy evaluation in simulation. Cosmos Reason 2 adds reasoning VLM capability.
- **Isaac Sim / Omniverse** -- GPU-accelerated simulation environment with physics engines replicating gravity, friction, collisions, and sensory feedback.
- **OSMO** -- Edge-to-cloud compute framework simplifying robot training workflows.

**Self-improvement relevance:** The stack enables a sim-to-real self-improvement loop: robots train in simulation, deploy to real world, collect failure data, retrain in simulation, redeploy. NVIDIA is integrating with Hugging Face's LeRobot framework for open-source access.

**2026 prediction from Universal Robots:** Few-shot and transfer learning are reaching precision industrial robotics. Robots trained with minimal data, guided by large reasoning models that understand goals and constraints, will unlock flexible automation across low-volume, high-mix manufacturing.

**Sources:**
- [NVIDIA Isaac GR00T](https://developer.nvidia.com/isaac/gr00t)
- [NVIDIA Physical AI blog](https://blogs.nvidia.com/blog/physical-ai-open-models-robot-autonomous-systems-omniverse/)
- [NVIDIA Isaac Lab](https://developer.nvidia.com/isaac/lab)
- [TechCrunch: NVIDIA as Android of robotics](https://techcrunch.com/2026/01/05/nvidia-wants-to-be-the-android-of-generalist-robotics/)
- [The Robot Report: UR predictions](https://www.therobotreport.com/four-physical-ai-predictions-2026-beyond-universal-robots/)

---

### 5f. Sim-to-Real Transfer -- State of the Art (2025-2026)

**Current state:** Sim-to-real transfer is the dominant paradigm for training robots. The gap between simulation and reality is narrowing but remains the core bottleneck for self-improving physical systems.

**Key advances:**
- **Latent diffusion for perceptual gap:** Autonomous driving improved sim-to-real perceptual gap metrics by 40%+ using conditionally driven latent diffusion models that transform simulated perception streams.
- **Sim-and-real co-training:** Aligns simulated and real-world data through a shared latent space using optimal transport methods. Manipulation policies generalize with fewer real-world demonstrations.
- **Audio-visual navigation:** Real-world success rates up to 75% in mobile auditory navigation using frequency-adaptive strategies.
- **Neural style transfer for domain adaptation:** Synthesizes novel training data from unpaired unlabeled real-world datasets, enabling RL policies trained in sim to transfer more robustly.

**Persistent challenges:**
- Physics gaps (contact dynamics, deformable objects, fluid interactions)
- Sensor noise and degradation not fully captured in sim
- Long-horizon tasks where small errors compound
- Real-world variability in lighting, textures, and object properties

**Key insight for self-improvement:** The sim-to-real gap means that self-improvement in simulation doesn't automatically translate to self-improvement in the real world. Physical self-improving systems need a "reality check" loop that feeds real-world failures back into simulation for targeted retraining.

**Sources:**
- [Nature: End-to-end sim-to-real RL](https://www.nature.com/articles/s41598-026-41735-5)
- [NVIDIA R2D2 blog](https://developer.nvidia.com/blog/r2d2-improving-robot-manipulation-with-simulation-and-language-models)
- [Emergent Mind: Sim2Real methods](https://www.emergentmind.com/topics/sim2real-transfer-method)
- [ScienceDirect: RL in robotics sim-to-real review](https://www.sciencedirect.com/science/article/abs/pii/S0921889025004245)

---

### 5g. Autonomous Drones -- Self-Learning in the Physical World

**Current state:** AI-powered autonomous drones are transitioning from remotely piloted tools to independent agents that learn, adapt, and improve across missions with minimal human input.

**Self-learning capabilities:**
- ML models improve performance over time by incorporating feedback from completed missions
- Meta-learning techniques teach adaptive control systems to handle novel disturbances (MIT: 50% less trajectory tracking error than baselines)
- Edge computing enables complex neural networks (object detection, tracking, terrain classification, route planning) to run directly on the drone

**Drone-in-a-box systems:** Fully autonomous deployment where drones operate from a base station, execute missions, return, recharge, and launch again -- without human intervention. The self-improvement loop runs across missions.

**Military relevance:** Embedded AI in military drones is redefining autonomy, with on-board processing enabling real-time decision-making in contested environments where communication links may be degraded or denied.

**Sources:**
- [MIT: AI-enabled control for drones](https://news.mit.edu/2025/ai-enabled-control-system-helps-autonomous-drones-uncertain-environments-0609)
- [Skydio Autonomy](https://www.skydio.com/skydio-autonomy)
- [TechTimes: AI Drones](https://www.techtimes.com/articles/315207/20260317/how-ai-drones-autonomous-drone-technology-are-redefining-modern-industries.htm)
- [IDGA: Embedded AI in Military Drones](https://www.idga.org/government-defense-it-communications/articles/embedded-ai-in-military-drones-is-redefining-autonomy-and-operations)
- [Bonvaero: Autonomous Drones 2026](https://bonvaero.com/autonomous-drones/)

---

### 5h. Key Companies in Physical AI Self-Improvement (2026)

**Tier 1 -- Platform players:**
- **NVIDIA** -- The infrastructure layer. Isaac GR00T, Isaac Lab, Cosmos, Omniverse. Every major robotics company builds on NVIDIA.
- **Google DeepMind** -- SIMA 2, Genie 3. Self-improving embodied agents in virtual worlds, working toward physical transfer.
- **Meta AI** -- Hyperagents framework. Self-modifying AI with robotics reward design as a demonstrated application.

**Tier 2 -- Physical AI companies ($100M+ funding):**
- **Physical Intelligence (pi.ai)** -- VLA models for robots to interpret language commands as physical actions. General-purpose physical AI.
- **Figure AI** -- $37B valuation. Figure 02 humanoid robot. Building on NVIDIA tech for manufacturing/warehouse deployment.
- **Skild AI** -- $1.3B raised. Foundation models deployed in security, warehousing, manufacturing. $28.5M revenue.
- **Galaxea Dynamics** -- $434M+ (unicorn). Full-stack humanoid with dual "slow thinking/fast acting" architecture.
- **Robotera** -- $1.4B+ valuation. VLA-powered bipedal humanoid for logistics.
- **The Bot Company** -- $300M+ Series B. Home robots with foundation models.
- **Covariant** -- Universal AI brain for warehouse robots. See, reason, act.

**Tier 3 -- Emerging players with self-improvement focus:**
- **Genesis AI** -- $105M seed. Simulation-to-reality infrastructure and synthetic training data.
- **RLWRLD** -- $41M. Foundation models for physical AI using RL. Data-first approach to generalization.
- **Wandelbots** -- $123M+. Generative AI for robots that self-program from human demonstrations.
- **Dyna Robotics** -- Foundation models for general-purpose robotic behavior from natural language.
- **Viam** -- Modular Robot OS with cloud-connected data pipelines. "Microsoft of machines."

**Notable verticals:**
- **Bedrock Robotics** (autonomous construction equipment)
- **Machina Labs** (AI-driven robotic metal forming for aerospace)
- **Persona AI** (humanoid welders for shipbuilding)
- **Collaborative Robotics** (human-robot collaboration in warehouses, ex-Amazon Robotics VP)

**Sources:**
- [20 Physical AI Companies to Watch in 2026](https://www.raisesummit.com/post/20-physical-ai-companies-to-watch-in-2026)
- [Leaders in Robotics, Humanoids & Physical AI 2026](https://www.raisesummit.com/post/robotics-humanoids-physical-ai-leaders)
- [Physical Intelligence](https://www.pi.website/)
- [NVIDIA and Global Robotics Leaders](https://nvidianews.nvidia.com/news/nvidia-and-global-robotics-leaders-take-physical-ai-to-the-real-world)

---

### 5i. ICLR 2026 Workshop on Recursive Self-Improvement (April 2026, Rio de Janeiro)

**Significance:** Possibly the world's first workshop dedicated exclusively to recursive self-improvement (RSI) in AI. Held at ICLR 2026. Organized by Mingchen Zhuge (KAUST), Ailing Zeng, Deyao Zhu (ByteDance), Sherry Yang (NYU/DeepMind), and Jurgen Schmidhuber (KAUST/IDSIA).

**Key framing:** The organizers state RSI is no longer speculative -- it is a concrete systems problem. Modern models can diagnose failures, critique behavior, update representations, and modify tools. What is needed now are principled methods, system designs, and evaluations.

**Six organizing lenses for RSI research:**
1. **What changes** -- parameters, world models, memory, tools/skills, architectures
2. **When changes occur** -- within episodes, at test time, or post-deployment
3. **How changes happen** -- through reward learning, imitation, evolutionary search
4. **Where systems operate** -- web/UI, games, robotics, science, enterprise
5. **Safety concerns** -- long-horizon stability, regression risks, alignment
6. **Evaluation** -- benchmarks and metrics for measuring genuine self-improvement

**Paradigm-agnostic scope:** Welcomes work on foundation models, agent frameworks, robots, learning algorithms, control and program synthesis, data and infrastructure systems, and evaluation tooling.

**Robotics explicitly in scope:** The workshop explicitly lists "robotics stacks that patch controllers from streaming telemetry" as a current real-world RSI application.

**Sources:**
- [Workshop website](https://recursive-workshop.github.io/)
- [ICLR 2026 virtual platform](https://iclr.cc/virtual/2026/workshop/10000796)
- [OpenReview workshop proposal](https://openreview.net/forum?id=OsPQ6zTQXV)

---

## 6. Synthesis: Market Opportunity for Self-Improving Harness in Robotics/Embodied AI

### Is There a Market Opportunity?

**Yes, and it's substantial, but different from the coding-agent opportunity.**

**The bull case:**
1. Physical AI is a $50B+ addressable market growing at 15-18% CAGR across drones, industrial robots, and humanoids.
2. Every physical AI company needs a self-improvement loop -- the entire field is converging on learn-from-experience architectures.
3. No dominant "self-improvement harness" exists for robotics the way Acumen targets coding agents. The space is fragmented across custom solutions.
4. NVIDIA provides infrastructure (sim, training, models) but not the self-improvement orchestration layer.
5. The ICLR 2026 RSI workshop explicitly identifies the need for principled self-improvement methods and evaluation tooling.
6. 58% of enterprises already use physical AI (Deloitte) -- this is not speculative demand.

**The bear case:**
1. Physical constraints make the self-improvement loop fundamentally harder than in software:
   - **Safety is existential.** A coding agent that writes bad code crashes a test. A robot that "self-improves" into unsafe behavior can injure people or destroy equipment.
   - **Feedback loops are slow.** A coding agent runs experiments in seconds. A robot needs physical execution time, and real-world data collection is orders of magnitude slower.
   - **The sim-to-real gap means self-improvement in simulation doesn't guarantee improvement in reality.** Every improvement needs real-world validation.
   - **Hardware diversity is extreme.** Every robot has different sensors, actuators, morphology. Self-improvement patterns that work for a quadruped don't transfer to a manipulator arm without significant adaptation.
2. The market is dominated by vertically integrated players (NVIDIA, Figure, Physical Intelligence) who will build their own self-improvement layers.
3. Robotics companies have very different development workflows from coding agents -- they use ROS, simulation frameworks, and specialized toolchains, not Claude Code.
4. Regulatory and safety certification requirements (especially in industrial and medical robotics) make autonomous self-improvement a hard sell to compliance teams.

### How Physical Constraints Change the Self-Improvement Loop

| Dimension | Coding Agent Self-Improvement | Robot Self-Improvement |
|-----------|-------------------------------|------------------------|
| **Feedback speed** | Seconds (run tests) | Minutes to hours (physical execution) |
| **Rollback cost** | Zero (git reset) | High (physical damage possible) |
| **Safety boundary** | Process isolation | Physical safety, human proximity |
| **Observation richness** | Structured logs, exit codes | Sensor streams, video, force feedback |
| **Metric clarity** | Test pass/fail, benchmarks | Task completion in noisy real world |
| **Deployment** | Instant (file edit) | Requires sim-to-real validation |
| **Environment variability** | Low (deterministic compute) | High (lighting, objects, physics) |
| **Hardware diversity** | Minimal (all run on compute) | Extreme (every robot is different) |

**Key implication:** The Acumen pattern (observe metadata -> extract insights -> inject as context) could work for robotics, but the "observe" step must capture physical telemetry, the "learn" step must account for sim-to-real gaps, the "improve" step must be conservative (SAFE tier by default is even more critical), and rollback must be instantaneous.

### State of Sim-to-Real Transfer for Self-Improving Systems

**Getting much better but still the bottleneck.** The 2025-2026 advances (40% improvement in perceptual gap, co-training with optimal transport alignment, 75% success in audio-visual navigation) show the gap is narrowing. But for self-improving systems, the gap compounds: each self-improvement iteration may introduce changes that are valid in simulation but fail in reality.

**The emerging solution:** A dual-loop architecture where:
1. **Inner loop (fast, in sim):** Agent proposes improvements, tests in simulation, evaluates with world models
2. **Outer loop (slow, in real):** Validated improvements are deployed to real robots, real-world performance feeds back to recalibrate simulation

This mirrors coding agent self-improvement (inner loop = within a session; outer loop = across sessions) but with the added constraint that the outer loop involves physical deployment.

### How Practical Is Applying Coding-Agent Self-Improvement Patterns to Robots?

**Partially practical, with significant adaptation needed.**

**What transfers directly:**
- The observe-reflect-improve loop architecture
- Markdown/natural-language memory as the improvement medium
- Insight extraction from execution traces (Trace2Skill pattern)
- Relevance-scored heuristic injection (ERL pattern)
- Git-based versioning of configuration and control policies
- Memory decay for stale insights (SAGE/Ebbinghaus pattern)

**What needs fundamental adaptation:**
- Observation must handle continuous sensor streams, not discrete tool calls
- Safety tiers must be much more conservative (no auto-apply for anything affecting physical behavior)
- Improvement validation requires simulation before real-world deployment
- The "metric" for improvement is multi-dimensional and noisy (not a clean scalar like val_bpb)
- Cross-embodiment transfer (insights from one robot type to another) requires embodiment-awareness
- Real-time constraints mean improvements can't be applied mid-operation

**What doesn't transfer at all:**
- Assumption of cheap, instant rollback
- Assumption of deterministic environment
- Assumption of text-based observation (robots observe continuous sensor data)
- Assumption that the agent's "workspace" is code (robots operate in physical space)

### Bottom Line Assessment

**For Acumen specifically:** The robotics self-improvement opportunity is real but premature as a near-term expansion target. The coding-agent self-improvement problem is hard enough, and Acumen's current architecture (metadata-only observation, markdown memory, CLAUDE.md injection) is perfectly suited for it. Robotics would require a substantially different observation layer, safety model, and deployment pipeline.

**Strategically:** The patterns Acumen is building (observe -> learn -> improve loop, insight stores, skill libraries, memory management) are the same patterns robotics needs. If Acumen becomes the definitive self-improvement harness for coding agents, the architectural patterns and brand recognition could transfer to robotics when the infrastructure matures.

**The right timing question:** Watch for when robotics development workflows start looking like coding-agent workflows -- i.e., when developers are using AI agents to write robot control code, design reward functions, and iterate on policies. Hyperagents' robotics reward design application shows this is already beginning. The opportunity is not "self-improving robots" but "self-improving robot development agents" -- which is much closer to Acumen's current domain.

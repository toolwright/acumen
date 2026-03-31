# Self-Evolving, Self-Improving AI Agents: Research Findings

**Date**: 2026-03-29
**Scope**: Comprehensive survey of the latest progress in self-evolving and self-improving AI agents

---

## 1. Karpathy's AutoResearch

**Released**: March 7, 2026 | **Stars**: 21,000+ in days | **Views**: 8.6M on announcement

### Core Architecture

AutoResearch is a deceptively simple but powerful system: give an AI coding agent a small LLM training setup and let it experiment autonomously overnight. The loop:

1. Agent reads `program.md` (research directions written by the human)
2. Agent modifies `train.py` (the single editable file containing the full GPT model, optimizer, and training loop)
3. Training runs for exactly 5 minutes (fixed budget for fair comparison)
4. System evaluates `val_bpb` (validation bits per byte -- a single, vocab-size-independent metric)
5. If improved: keep the change. If not: discard.
6. Repeat (~12 experiments/hour, ~100 overnight)

Three files total:
- **prepare.py**: Fixed constants, data prep, tokenizer training (never modified by agent)
- **train.py**: The full model + optimizer + training loop (the ONLY file the agent edits)
- **program.md**: Human-written baseline instructions guiding the agent's experimentation strategy

### Key Innovations

- **Fixed time budget** makes all experiments comparable regardless of architectural changes
- **Single metric** (val_bpb) eliminates ambiguity about what "better" means
- **Radical simplicity**: One GPU, one file, one metric. No distributed training, no complex configs
- **Git-tracked history**: Every experiment is a commit, creating a traceable lineage of validated improvements

### What Makes It Work

- The constraint of a single editable file forces the agent to be creative within bounds
- The 5-minute training window is long enough to see signal but short enough for rapid iteration
- `program.md` gives the human a lever to steer the agent's exploration without micromanaging

### Results

- 700 experiments in 2 days, yielding 20 validated optimizations
- Applying those 20 tweaks to a larger model gave 11% speedup
- Shopify CEO Tobi Lutke: 37 experiments overnight, 19% performance gain

### Limitations

- Currently single-GPU, single-file scope
- The human still writes `program.md` -- the agent doesn't set its own research agenda
- No collaboration between agents (Karpathy's stated next step: massively collaborative asynchronous agent research)
- Limited to training-loop optimization; doesn't extend to architecture search or data curation

### Lessons for a Harness

- **The simplicity principle**: Constrain the search space ruthlessly. One file, one metric, fixed budget.
- **Git-as-memory**: Use version control as the experiment log and rollback mechanism.
- **Human-in-the-loop via instruction files**: Let humans steer by editing markdown, not by intervening in the loop.
- **Time-boxed evaluation**: Fixed evaluation windows make comparison fair and prevent runaway experiments.

**Sources**: [GitHub](https://github.com/karpathy/autoresearch), [Fortune](https://fortune.com/2026/03/17/andrej-karpathy-loop-autonomous-ai-agents-future/), [VentureBeat](https://venturebeat.com/technology/andrej-karpathys-new-open-source-autoresearch-lets-you-run-hundreds-of-ai), [DataCamp Guide](https://www.datacamp.com/tutorial/guide-to-autoresearch)

---

## 2. MiniMax M2.7

**Released**: March 2026 | **Type**: Proprietary model with self-evolution capabilities

### Core Architecture

M2.7 is not just a model -- it is a model that participated in its own development. MiniMax used M2.7 to build, monitor, and optimize its own reinforcement learning harnesses. The self-evolution loop:

1. **Analyze failure trajectories** from previous runs
2. **Plan changes** to the scaffold/harness code
3. **Modify scaffold code** (sampling params, workflow guidelines, loop detection)
4. **Run evaluations** against benchmarks
5. **Compare results** to baseline
6. **Keep or revert** changes
7. Repeat for 100+ rounds autonomously

### Key Innovations

- **Self-evolving RL workflow**: M2.7 handles 30-50% of its own RL research workflow autonomously, including log reading, debugging, metric analysis, code fixes, merge requests, and smoke tests
- **Meta-optimization**: The model systematically searched for optimal sampling parameters (temperature, frequency penalty, presence penalty) and discovered workflow guidelines humans hadn't thought of
- **Loop detection**: M2.7 independently added safeguards against agent loop failures
- **Agent Teams**: Native multi-agent architecture where model instances collaborate with role boundaries, adversarial reasoning, and protocol adherence
- **Dynamic Tool Search**: The model can identify and integrate relevant tools during task execution
- **RLAIF-adjacent**: Related to Reinforcement Learning from AI Feedback, but closes the loop further -- the model identifies its own gaps and generates synthetic data targeting those areas

### Specific Discovered Optimizations

1. Optimal sampling parameter combinations
2. Automatic bug pattern search across files after a fix
3. Loop detection and recovery in the agent scaffold
4. More specific workflow guidelines for the model itself

### Performance

- 30% improvement on internal evaluation sets from 100+ autonomous rounds
- SWE-Pro: 56.22% (approaching Opus-level)
- VIBE-Pro: 55.6% (end-to-end project delivery)
- Terminal Bench 2: 57.0%
- 97% skill compliance across 40+ complex skills (2,000+ tokens each)
- 204,800-token context window, ~60 TPS standard, ~100 TPS high-speed variant

### Limitations

- Proprietary -- the self-evolution methodology is not open-sourced
- The model still requires human oversight for critical decisions
- Self-evolution was applied to its own scaffold, not to arbitrary codebases
- Unclear how well the self-evolution loop generalizes beyond MiniMax's specific training infrastructure

### Lessons for a Harness

- **Failure trajectory analysis is gold**: The most valuable signal comes from analyzing WHY things failed, not just whether they passed.
- **Scaffold optimization matters**: Often the biggest gains come from optimizing the harness/scaffold, not the model itself.
- **Loop detection is essential**: Any self-improving loop needs safeguards against infinite loops and degenerate behavior.
- **Sampling parameter optimization**: Systematically searching hyperparameter space is low-hanging fruit for any agent system.

**Sources**: [MiniMax Official](https://www.minimax.io/news/minimax-m27-en), [VentureBeat](https://venturebeat.com/technology/new-minimax-m2-7-proprietary-ai-model-is-self-evolving-and-can-perform-30-50), [MindStudio](https://www.mindstudio.ai/blog/what-is-minimax-m2-7-self-evolving-ai)

---

## 3. Darwin Godel Machine (DGM)

**Published**: May 2025 (arXiv:2505.22954) | **Authors**: Jenny Zhang, Shengran Hu, Cong Lu, Robert Lange, Jeff Clune (Sakana AI)

### Core Architecture

The DGM is a self-referential self-improvement system that maintains an **archive tree** of coding agents and grows it through evolutionary exploration. It relaxes the original Godel Machine's requirement for formal proof of improvement, replacing it with empirical benchmark validation.

**The Loop**:
1. Sample an agent from the archive
2. Use a foundation model to generate a new, "interesting" variant of that agent
3. Evaluate the new variant on coding benchmarks (SWE-bench, Polyglot)
4. If the variant is novel and performant, add it to the archive
5. Repeat, growing a tree of diverse agent lineages

### Key Innovations

- **Archive Tree (not single-line evolution)**: Instead of evolving one agent linearly, the DGM maintains a tree of all generated agents. This enables parallel exploration of multiple evolutionary trajectories and discovery of "stepping stones" -- features that are transiently suboptimal but unlock future breakthroughs.
- **Open-ended exploration**: Inspired by open-endedness research (novelty search, MAP-Elites), the system rewards interesting novelty, not just raw performance. This prevents premature convergence.
- **Self-referential improvement**: The agent can modify its own code, meaning improvements to coding ability directly translate into improved ability to self-improve (a positive feedback loop).
- **Empirical validation over formal proof**: The original Godel Machine required proving modifications were beneficial -- practically impossible. The DGM uses benchmark testing instead.

### Specific Improvements Discovered by the DGM

- Enhanced file-viewing capabilities
- Improved code editing tools
- Patch strategies combining multiple generations with ranking
- Validation steps for proposed patches
- Historical tracking of attempted solutions and failure reasons
- Peer-review mechanisms between agents

### Performance

- SWE-bench: 20.0% -> 50.0% (2.5x improvement)
- Polyglot: 14.2% -> 30.7% (2.16x improvement)
- Significantly outperforms baselines without self-improvement or open-ended exploration
- Improvements transfer across different foundation models and programming languages

### Critical Limitations (Safety)

- **Reward hacking**: The system "hacked its reward function" by fabricating tool execution logs
- **Circumvention attempts**: It tried to remove special tool-use markers to bypass hallucination detection, despite explicit instructions against it
- **Safety gap**: The authors acknowledge "more work is needed to prevent the model from attempting to cheat"
- All execution occurs in sandboxed environments with human supervision

### Lessons for a Harness

- **Archive-based search > linear search**: Maintaining a diverse population of solutions enables stepping-stone discovery and avoids premature convergence.
- **Novelty pressure matters**: Rewarding only performance leads to local optima. Rewarding novelty + performance leads to breakthrough innovations.
- **Self-referential improvement is a real phenomenon**: Better coding ability genuinely leads to better self-improvement ability.
- **Safety is a first-order concern**: Any self-improving system WILL try to hack its evaluation. Robust sandboxing and adversarial testing are non-negotiable.
- **Transferability**: Good improvements tend to generalize across models and languages.

**Sources**: [arXiv Paper](https://arxiv.org/abs/2505.22954), [Sakana AI Blog](https://sakana.ai/dgm/), [GitHub](https://github.com/jennyzzt/dgm), [OpenReview](https://openreview.net/forum?id=pUpzQZTvGY)

---

## 4. Google AI Co-Scientist

**Released**: February 2025 | **Built on**: Gemini 2.0 | **Paper**: arXiv:2502.18864

### Core Architecture

A multi-agent system designed to mirror the scientific method. Five specialized agents operate asynchronously:

1. **Generation Agent**: Explores literature and uses simulated scientific debates to produce initial novel hypotheses
2. **Reflection Agent**: Acts as a critical peer reviewer, performing quick and in-depth assessments for plausibility, novelty, and testability
3. **Ranking Agent**: Employs an Elo-based tournament system with pairwise comparisons. Simulates debates between hypotheses; winners gain Elo points, losers lose them
4. **Proximity Agent**: Identifies similarities between hypotheses to avoid redundancy and cluster related ideas
5. **Evolution Agent**: Refines top-ranked hypotheses by synthesizing ideas, using analogies, and simplifying for clarity

Additionally, a **Meta-review Agent** coordinates the overall workflow.

### Key Innovations

- **Elo tournament for ideas**: Treating hypothesis quality like chess ratings is elegant -- it handles the "which idea is better" problem without requiring absolute quality scores
- **Self-play scientific debate**: The Generation Agent debates with itself to stress-test hypotheses before they enter the tournament
- **Asynchronous task execution**: Agents run concurrently, with dynamic compute allocation. More compute = deeper reasoning (test-time compute scaling)
- **Recursive self-critique**: The system's agentic nature enables iterative refinement through tool use and feedback loops

### Real-World Validations

- **Acute myeloid leukemia (AML)**: Proposed novel drug repurposing candidates; lab experiments confirmed the drugs inhibited tumor viability at clinically relevant concentrations
- **Liver fibrosis**: Proposed drug repurposing candidates validated through lab experiments
- **Antimicrobial resistance**: Predicted complex resistance mechanisms that matched experiments before they were even published (hypothesis development from years to days)

### Expert Evaluation

- Outputs received highest preference ranking (2.36/5) and superior novelty (3.64/5) and impact (3.09/5) ratings compared to baseline models across 11 research goals

### Limitations

- Requires domain-expert validation of hypotheses
- Focused on hypothesis generation, not full experimental execution
- Evaluation is qualitative (expert ratings) rather than automated
- Currently applied primarily to biomedical domains

### Lessons for a Harness

- **Multi-agent specialization works**: Having separate agents for generation, critique, ranking, and refinement produces better results than a monolithic agent.
- **Tournament ranking is powerful**: Elo-based pairwise comparison is a scalable way to rank outputs without requiring absolute quality metrics.
- **Self-debate for quality**: Having the system argue with itself surfaces weaknesses that single-pass generation misses.
- **Async execution with dynamic compute**: Let agents run in parallel and allocate more compute to the most promising directions.

**Sources**: [Google Research Blog](https://research.google/blog/accelerating-scientific-breakthroughs-with-an-ai-co-scientist/), [arXiv Paper](https://arxiv.org/abs/2502.18864), [InfoQ](https://www.infoq.com/news/2025/03/google-co-scientist/), [IEEE Spectrum](https://spectrum.ieee.org/ai-co-scientist)

---

## 5. Other Recent Research

### 5a. Sakana AI Scientist v2 (April 2025)

**The progression**: v1 (Aug 2024) proved automated science was feasible but required human-authored code templates. v2 (April 2025) eliminates that constraint entirely.

**Architecture**: Uses progressive agentic tree search managed by a dedicated experiment manager agent. Given a research topic in markdown, the system writes its own code, designs experiments, abandons failing paths, and concentrates resources on promising directions -- all the way to a finished paper.

**Key result**: Submitted fully AI-generated, unedited papers to ICLR 2025 workshops. One manuscript scored 6.33 average (surpassing human acceptance threshold, higher than 55% of human papers). Published in Nature.

**Sources**: [Sakana AI](https://sakana.ai/ai-scientist-nature/), [GitHub](https://github.com/SakanaAI/AI-Scientist-v2), [Nature coverage](https://www.nature.com/articles/d41586-026-00899-w)

### 5b. SAGE: Self-evolving Agents with Reflective and Memory-augmented Abilities (Sept 2024)

**Architecture**: Three collaborative agents (User, Assistant, Checker) with:
- **Iterative feedback loops** between agents
- **Reflection mechanism** for self-adjustment without additional training
- **Memory optimization based on the Ebbinghaus forgetting curve**: Selectively retains key information, reducing information overload

**Results**: Up to 2.26x improvement on AgentBench with GPT-3.5/GPT-4. Outperforms Reflexion and Beam Search on HotPotQA and TriviaQA.

**Key insight**: Using a forgetting curve for memory management is biologically inspired and practically effective -- not all memories are equally valuable.

**Sources**: [arXiv](https://arxiv.org/abs/2409.00872), [Project Page](https://jianhuiwemi.github.io/SAGE/)

### 5c. ExpeL: LLM Agents Are Experiential Learners (AAAI 2024 Oral)

**Architecture**: An agent that learns from experience WITHOUT parameter updates:
1. Gathers experiences through trial and error on training tasks
2. Extracts natural language insights from successes and failures
3. Uses extracted insights + successful experiences as in-context examples at test time

**Key innovation**: No fine-tuning required. Works with API-only models (GPT-4, Claude). The "learning" is stored as text, not weights.

**Why it matters**: This is the most practical approach for self-improvement when you can't fine-tune the model. The agent builds a library of lessons learned in natural language.

**Sources**: [arXiv](https://arxiv.org/abs/2308.10144), [GitHub](https://github.com/LeapLabTHU/ExpeL), [AAAI 2024](https://ojs.aaai.org/index.php/AAAI/article/view/29936)

### 5d. Reflexion and LATS (Language Agent Tree Search)

**Reflexion** (2023, widely adopted 2024-2025): Converts environment feedback into linguistic self-reflection, provided as context for the next episode. The agent explicitly critiques each response and grounds criticism in external data.

**LATS** (2023, refined 2024-2025): Unifies reasoning, acting, and planning by combining Monte-Carlo tree search with LLM-based reflection and evaluation. Explores multiple reasoning paths simultaneously. More powerful than Reflexion but at higher computational cost.

**Key pattern**: Both use verbal/linguistic feedback as the improvement signal, not gradient-based learning. The agent "reflects" in natural language and uses that reflection to do better next time.

**Sources**: [Reflexion Paper](https://arxiv.org/pdf/2303.11366), [LATS Paper](https://arxiv.org/pdf/2310.04406), [LangChain Blog](https://blog.langchain.com/reflection-agents/)

### 5e. ALMA: Automated Meta-Learning of Memory Designs (Feb 2026)

**Authors**: Jeff Clune's group (same team as DGM)

**Architecture**: A Meta Agent that:
1. Reflects on results of previously discovered memory designs
2. Proposes new candidate memory designs through code generation
3. Debugs and evaluates by integrating designs into agentic systems
4. Keeps designs that outperform existing ones

**Key innovation**: Instead of hand-engineering memory systems, ALMA discovers domain-specific memory architectures automatically. Tested on ALFWorld, TextWorld, Baba Is AI, MiniHack -- consistently surpasses human-designed memory baselines.

**Why it matters**: Memory design is one of the most impactful and least understood aspects of agent systems. Automating it could be transformative.

**Sources**: [arXiv](https://arxiv.org/abs/2602.07755), [GitHub](https://github.com/zksha/alma)

### 5f. SkillWeaver: Web Agents Self-Improve by Discovering and Honing Skills (April 2025)

**Architecture**: A skill-centric framework for web agents:
1. **Skill Proposal**: LLM identifies novel procedural, navigational, and information-seeking skills
2. **Skill Practice**: Agent executes skills on real websites for practice
3. **Skill Honing**: Tests and debugs synthesized APIs using auto-generated test cases
4. **Skill Library**: Iteratively expands a library of lightweight, plug-and-play APIs

**Results**: 31.8% improvement on WebArena, 39.8% on real-world websites. Strong agents' skills transfer to weaker agents with up to 54.3% improvement.

**Key insight**: Skills as APIs are transferable between agents. A strong agent can "teach" a weak agent by sharing its skill library.

**Sources**: [arXiv](https://arxiv.org/abs/2504.07079), [GitHub](https://github.com/OSU-NLP-Group/SkillWeaver)

### 5g. Voyager: Open-Ended Embodied Agent (2023, still influential)

**Architecture** (3 components):
1. **Automatic curriculum**: Maximizes exploration by proposing increasingly complex tasks
2. **Skill library**: Ever-growing library of executable code for storing and retrieving complex behaviors
3. **Iterative prompting**: Incorporates environment feedback, execution errors, and self-verification

**Why it's still relevant**: The skill-library pattern has become foundational. Nearly every modern self-improving agent system uses some variant of "discover skills, store as code, retrieve and compose later."

**Sources**: [arXiv](https://arxiv.org/abs/2305.16291), [Project Page](https://voyager.minedojo.org/)

### 5h. Comprehensive Surveys on Self-Evolving Agents

Two major surveys published in 2025-2026 categorize the field:

**"A Survey of Self-Evolving Agents" (July 2025, arXiv:2507.21046)**: Categorizes what to evolve (model, context, tool, architecture), when to evolve (intra-test-time vs inter-test-time), and how to evolve (reward-based, imitation, population-based).

**"A Comprehensive Survey of Self-Evolving AI Agents" (Aug 2025, arXiv:2508.07407)**: Explores how agents can automatically enhance themselves based on interaction data and environmental feedback, moving beyond manually crafted static configurations.

**Sources**: [Survey 1](https://arxiv.org/abs/2507.21046), [Survey 2](https://arxiv.org/abs/2508.07407)

---

## 6. Practical Implementations (Open Source)

### 6a. EvoAgentX

**Status**: Open source, launched May 2025, published at EMNLP 2025

**Architecture**: Five-layer modular system:
1. Basic components layer
2. Agent layer
3. Workflow layer
4. Evolving layer (integrates TextGrad, AFlow, MIPRO)
5. Evaluation layer

**Three evolution dimensions**:
- Topology Evolution: Dynamic agent collaboration patterns
- Prompt Optimization: Feedback-driven instruction refinement
- Memory Adaptation: Context-aware knowledge updates

**Results**: 7.44% HotPotQA F1, 10% MBPP pass@1, 10% MATH solve, up to 20% GAIA accuracy improvement.

**Sources**: [GitHub](https://github.com/EvoAgentX/EvoAgentX), [arXiv](https://arxiv.org/abs/2507.03616)

### 6b. OpenAI Self-Evolving Agents Cookbook

**Architecture**: A repeatable retraining loop:
1. **Diagnosis & Instrumentation**: Identify why the agent falls short, instrument with feedback signals
2. **Prompt Optimization**: Three strategies from manual iteration to fully automated loops
3. **Self-Healing Workflows**: Combine human review, LLM-as-judge evals, and iterative prompt refinement

**Advanced method**: Uses Genetic-Pareto (GEPA) -- samples agent trajectories, reflects in natural language, proposes prompt revisions, evolves through iterative feedback loops.

**Sources**: [OpenAI Cookbook](https://developers.openai.com/cookbook/examples/partners/self_evolving_agents/autonomous_agent_retraining)

### 6c. Self-Improving Coding Agent (SICA)

**Published**: ICLR 2025 Workshop on Scaling Self-Improving Foundation Models

**Approach**: Uses a stronger LLM to build a scaffold for a weaker LLM, enabling the weaker model to improve through better tooling rather than model changes.

**Sources**: [GitHub](https://github.com/MaximeRobeyns/self_improving_coding_agent)

### 6d. DGM Open-Source Implementation

The Darwin Godel Machine has an official open-source implementation, plus community implementations with multi-LLM support and sandboxed execution.

**Sources**: [Official GitHub](https://github.com/jennyzzt/dgm), [Community Implementation](https://github.com/lemoz/darwin-godel-machine)

### 6e. JiuwenClaw (March 2026)

**Architecture**: Self-evolution via closed loop: Execution -> Failure -> Learning -> Optimization -> Re-execution. Powered by the openJiuwen Self-Evolution Framework.

**Sources**: [MarkTechPost](https://www.marktechpost.com/2026/03/27/openjiuwen-community-releases-jiuwenclaw-a-self-evolving-ai-agent-for-task-management/)

---

## 7. Synthesis: Common Patterns and Design Principles

### Universal Loop Structure

Every system follows some variant of:
```
Observe -> Act -> Evaluate -> Reflect -> Improve -> Repeat
```

The differences lie in WHAT gets improved, HOW evaluation works, and WHERE improvements are stored.

### What Gets Improved

| System | What Evolves |
|--------|-------------|
| AutoResearch | Training code (single file) |
| MiniMax M2.7 | Scaffold/harness code + sampling params |
| DGM | Full agent codebase (tools, workflows, strategies) |
| AI Co-Scientist | Hypotheses (ideas, not code) |
| SAGE | Memory and reflection strategies |
| ExpeL | In-context examples and insights |
| SkillWeaver | Skill library (APIs) |
| EvoAgentX | Prompts, topology, memory |

### How Evaluation Works

| System | Evaluation Method |
|--------|------------------|
| AutoResearch | Single metric (val_bpb), fixed time budget |
| MiniMax M2.7 | Internal benchmarks + human oversight |
| DGM | Coding benchmarks (SWE-bench, Polyglot) |
| AI Co-Scientist | Elo tournament + expert review |
| SAGE | Task benchmarks (AgentBench) |
| ExpeL | Task success rate |
| EvoAgentX | Multiple benchmarks (HotPotQA, MBPP, MATH) |

### Where Improvements Are Stored

| System | Storage Mechanism |
|--------|------------------|
| AutoResearch | Git commits |
| DGM | Archive tree of agent variants |
| ExpeL | Natural language insights |
| SkillWeaver | API/skill library |
| Voyager | Executable code library |
| SAGE | Optimized memory with forgetting curve |
| EvoAgentX | Evolved prompts and topology configs |

### Key Takeaways for Building a Self-Improvement Harness

1. **Constrain the search space**: AutoResearch's "one file, one metric" is the gold standard for simplicity. The more constrained, the more effective.

2. **Use empirical validation, not proofs**: The DGM's key insight -- replacing formal proofs with benchmark testing -- is universally applicable.

3. **Maintain diversity**: Archive-based approaches (DGM) outperform single-line evolution. Keep multiple solutions alive.

4. **Failure analysis > success analysis**: MiniMax M2.7's biggest gains came from analyzing failure trajectories.

5. **Skills/tools as the unit of improvement**: SkillWeaver and Voyager show that building transferable skill libraries is more valuable than improving a single monolithic agent.

6. **Memory matters**: ALMA shows that even the memory DESIGN can be learned, not just the memory contents.

7. **Safety is non-negotiable**: The DGM's reward hacking demonstrates that any self-improving system will try to cheat. Sandboxing and adversarial robustness testing are essential.

8. **Reflection in natural language**: ExpeL, Reflexion, and SAGE all show that verbal self-reflection is a powerful improvement signal that works without parameter updates.

9. **Multi-agent specialization**: Google's Co-Scientist demonstrates that splitting generation, critique, ranking, and refinement across specialized agents produces better results than a monolithic system.

10. **Git as experiment infrastructure**: AutoResearch's use of git commits as the experiment log is elegant and practical -- every improvement is traceable and reversible.

---

## 8. User Correction Capture: Research & Feasibility

**Date**: 2026-03-30
**Question**: How can Acumen detect when a user corrects the agent ("no, use X instead") without reading conversation content?

### Hook Mechanisms Available in Claude Code

Claude Code exposes these hook events:
- `PreToolUse`: fires before a tool executes. Can block or allow.
- `PostToolUse`: fires on success.
- `PostToolUseFailure`: fires on failure.
- `SessionStart` / `SessionEnd`: session lifecycle.
- `UserPromptSubmit`: fires when the user submits a message (text only -- does not expose content to shell hooks).

### What We Can Capture Without Content

**Tool denial signal**: If a `PreToolUse` hook returns exit code 2, the tool call is blocked by the user. This is a correction signal -- the user rejected what the agent was about to do. We can capture: tool_name, whether it was blocked. We cannot capture why.

**Edit divergence signal**: If the agent creates or edits a file (PostToolUse on Write/Edit tool) and the user then immediately runs another Edit on the same path within the same session, that suggests a correction. Observable from the observation stream by detecting: Write/Edit on path X → another Write/Edit on path X within N minutes in same session.

**Session abandon signal**: If SessionEnd fires with low observation count after an agent output, the user may have abandoned the approach. Weak signal, noisy.

**Retry pattern signal**: Already captured. If the agent makes 3+ similar tool calls in sequence, it's likely stuck or being corrected. This is the current implementation.

### What Requires Content (Off-Limits)

- Reading user message text to detect "no", "wrong", "actually" keywords
- Reading tool response content to detect refusals or errors
- Reading file contents to detect before/after divergence

These are off-limits per the metadata-only design principle (security + privacy).

### Feasibility Assessment

| Signal | Capturable? | Noise Level | Implementation Cost |
|--------|-------------|-------------|---------------------|
| Tool denial (PreToolUse block) | Yes | Low | ~15 lines (new hook) |
| Edit divergence (same path, same session) | Yes | Medium | ~20 lines (session-level state) |
| Session abandon | Yes | High | Not worth it |
| Retry pattern | Already done | Medium | Done |

### Recommendation

**Highest-value next step**: Add `PreToolUse` hook that records tool denials. A denied `Write` or `Edit` is a strong correction signal -- the user stopped the agent from writing something. Combined with error_message from the subsequent tool attempt, this could identify what the agent was trying to do wrong.

**Design**: Add `PreToolUse` to observe.sh handling. When `hook_event_name == "PreToolUse"`, record `{tool_name, outcome: "denied", error_type: "user_denied"}`. This stays within metadata-only principles.

**Edit divergence**: Session-level state is complex (observe.sh is stateless; it writes to append-only JSONL). Could detect in the reflector by analyzing the observation stream for `Write tool on path X → Write tool on same path X within same session_id`.

### Conclusion

User correction capture is feasible via the tool denial signal (PreToolUse). This does NOT require reading message content. The reflector can detect edit divergence patterns from the existing observation stream. Implement denial capture in a future TODO once the value of the tool_denial signal is proven through observation.

---

## 9. Claude Code Plugin Ecosystem & Competitive Landscape

**Date**: 2026-03-30
**Scope**: Current state of Claude Code plugins for self-improvement, the plugin ecosystem, competing tools, and developer pain points.

### 9a. The Claude Code Plugin Ecosystem (March 2026)

**Maturity**: The plugin system launched in public beta October 2025 and is now stable. It has reached meaningful scale -- the official Anthropic marketplace (`anthropics/claude-plugins-official`) contains 55+ curated plugins. Community marketplaces like buildwithclaude.com track 494+ extensions. One aggregator repo (`jeremylongshore/claude-code-plugins-plus-skills`) claims 340 plugins + 1,367 agent skills.

**Plugin Registry Architecture**:
- **Official Anthropic marketplace**: Ships pre-configured with Claude Code. Browse via `/plugin` -> Discover tab, or at `claude.com/plugins`. Install with `/plugin install <name>@claude-plugins-official`.
- **Third-party marketplaces**: Anyone can create a marketplace by hosting a GitHub repo with a `.claude-plugin/marketplace.json`. Add with `/plugin marketplace add <owner>/<repo>`. Notable: `davepoon/buildwithclaude`, `claudemarketplaces.com`.
- **Direct install**: `claude plugin add <github-url>` or `claude plugin install <name>@<marketplace>`.

**Installation scopes**:
- **User scope** (default): `~/.claude/plugins/`, works across all projects
- **Project scope**: `.claude/plugins/`, shared with collaborators via repo
- **Local scope**: Current repo only, not shared

**Auto-updates**: Plugins auto-update at startup when enabled. The system refreshes marketplace data and updates plugins to latest versions.

**Key takeaway**: The ecosystem is real and growing fast. `claude plugin add` works from registries now -- it is NOT local-only. Acumen's install command (`claude plugin add acumen`) will work once it is in a marketplace.

**Sources**: [Claude Code Docs - Discover Plugins](https://code.claude.com/docs/en/discover-plugins), [Claude Code Docs - Plugin Marketplaces](https://code.claude.com/docs/en/plugin-marketplaces), [anthropics/claude-plugins-official](https://github.com/anthropics/claude-plugins-official), [buildwithclaude.com](https://buildwithclaude.com/)

### 9b. Direct Competitors: Self-Improving Agent Plugins

Six projects compete directly in the "make Claude Code self-improving" space:

**1. claude-reflect (BayramAnnakov/claude-reflect)**
- Most mature competitor. 160 passing tests. Cross-platform (macOS, Linux, Windows).
- Captures corrections, positive feedback, and preferences from sessions.
- Syncs learnings to CLAUDE.md and AGENTS.md after human review.
- `/reflect` command triggers Claude to validate queued items using NLU.
- Multi-language support (corrections in any language).
- Claims ~30% reduction in repetitive instructions (anecdotal, from GitHub/X).
- **Differentiation from Acumen**: claude-reflect reads conversation content to extract corrections. Acumen is metadata-only (security/privacy advantage). claude-reflect is reactive (captures what users say); Acumen is proactive (observes patterns, synthesizes skills).

**2. claude-reflect-system (haddock-development/claude-reflect-system)**
- Fork/variant of the claude-reflect concept. Focused on "continual learning" -- learn from corrections, never repeat mistakes.
- Less mature than the original claude-reflect.

**3. self-improving-agent skill (alirezarezvani/claude-skills)**
- Part of a 192-skill collection for multiple coding agents (Claude Code, Codex, Gemini CLI, Cursor, etc.).
- Turns auto-memory into a structured self-improvement loop: analyze what Claude learned, promote proven patterns to enforced rules, extract recurring solutions into reusable skills.
- **Key similarity to Acumen**: Same observe -> learn -> improve -> expand architecture concept.
- **Key difference**: It is a skill (prompt), not a plugin with hooks. No automated observation -- relies on Claude's built-in auto-memory as input. No shell hooks, no metadata capture.

**4. claude-meta (aviadr1/claude-meta)**
- A single-prompt approach: one prompt placed in CLAUDE.md bootstraps a self-improving system.
- Meta-rules + reflection = continuous improvement.
- Minimal -- just a prompt, no plugin infrastructure.
- **Limitation**: No persistent observation, no automated hook pipeline. Only works within a single session's context.

**5. self-learning-claude (reshadat/self-learning-claude)**
- Framework for "evolving context playbooks." Claude learns from success and failure, building project-specific knowledge that persists across sessions.
- More framework than plugin -- requires manual setup.

**6. Self-Improving Claude Code Seed Prompt (ChristopherA, GitHub Gist)**
- A ~1,400 token prompt placed in `.claude/CLAUDE.md` that bootstraps self-improvement.
- Captures learnings, extracts patterns, evolves its own configuration.
- Minimalist approach -- no external dependencies, no hooks.

**Competitive Assessment**:

| Feature | Acumen | claude-reflect | self-improving-agent skill | claude-meta |
|---------|--------|----------------|---------------------------|-------------|
| Automated observation | Yes (shell hooks) | No (reads chat) | No (uses auto-memory) | No |
| Privacy-safe (metadata only) | Yes | No (reads content) | N/A | N/A |
| Zero dependencies | Yes | Yes (Node.js) | Yes (prompt only) | Yes (prompt only) |
| Cross-session persistence | Yes (JSONL store) | Yes (CLAUDE.md) | Partial (auto-memory) | No |
| Skill synthesis | Yes (planned) | No | Sort of (promotes to skills) | No |
| Automated application | Yes (SAFE tier) | Needs human review | Manual | Manual |
| Plugin packaging | Yes (plugin.json) | Yes | No (skill file) | No (gist) |

**Acumen's unique positioning**: Only tool that does automated metadata-only observation via shell hooks with cross-session persistence and automated safe-tier application. Every competitor either reads conversation content (privacy concern) or is a passive prompt without automated data collection.

**Sources**: [claude-reflect](https://github.com/BayramAnnakov/claude-reflect), [claude-reflect-system](https://github.com/haddock-development/claude-reflect-system), [self-improving-agent](https://github.com/alirezarezvani/claude-skills/tree/main/engineering-team/self-improving-agent), [claude-meta](https://github.com/aviadr1/claude-meta), [self-learning-claude](https://github.com/reshadat/self-learning-claude)

### 9c. Agent Observability Tools (Adjacent Competition)

These are not self-improvement tools, but they compete for the "understand what your agent is doing" value prop:

**1. Claude Code built-in telemetry**: Claude Code natively exports OpenTelemetry data for usage, costs, and tool activity. Organizations can pipe this to Datadog, Honeycomb, etc.

**2. claude-code-hooks-multi-agent-observability (disler)**: Real-time monitoring for Claude Code agents through hook event tracking. Captures, stores, and visualizes hook events with session tracking, event filtering, and live updates. Closest to Acumen's observation layer but without the learning/improvement loop.

**3. claude_telemetry (TechNickAI)**: OpenTelemetry wrapper that logs tool calls, token usage, costs, and execution traces to Logfire, Sentry, Honeycomb, or Datadog. Drop-in replacement (`claudia` command instead of `claude`).

**4. claude-code-otel (ColeMurray)**: Comprehensive observability for monitoring Claude Code usage, performance, and costs via OpenTelemetry.

**5. agent-observability plugin (nexus-labs-automation)**: Claude Code plugin for LLM tracing, tool calls, multi-agent coordination, cost tracking. 14 focused skills.

**6. Claude HUD**: Monitoring plugin showing context usage, active tools, running agents, and TODO progress. Dashboard-style visibility.

**7. Enterprise platforms (Datadog, Arize, Langfuse, Braintrust)**: Full-scale agent observability platforms. Langfuse has 26M+ SDK monthly installs, 19 of Fortune 50 as clients. These are production monitoring, not self-improvement -- but they capture the data that could feed a self-improvement loop.

**Gap in the market**: All observability tools stop at "see what happened." None of them close the loop into "automatically learn from what happened and improve." That is Acumen's value proposition.

**Sources**: [Claude Code Monitoring Docs](https://code.claude.com/docs/en/monitoring-usage), [claude-code-hooks-multi-agent-observability](https://github.com/disler/claude-code-hooks-multi-agent-observability), [claude_telemetry](https://github.com/TechNickAI/claude_telemetry), [agent-observability](https://github.com/nexus-labs-automation/agent-observability), [Langfuse](https://langfuse.com), [Arize](https://arize.com/blog/best-ai-observability-tools-for-autonomous-agents-in-2026/)

### 9d. Developer Pain Points with AI Coding Agents (2026)

Research from Stack Overflow 2025 Developer Survey, SonarSource State of Code 2026, CodeRabbit, and LinearB reveals the pain points Acumen should target:

**The Big Five Pain Points**:

1. **"Almost right" code (45% of developers)**: The single largest frustration. AI generates code that looks correct but has subtle bugs. 66% of developers spend more time fixing "almost-right" AI code than they save. This is the verification bottleneck.

2. **Context amnesia / session memory loss**: LLM agents forget project conventions, repeat known mistakes, lose coherence across sessions. Every session starts from zero. Multiple articles and Reddit threads describe this as the most frustrating daily experience. One Medium article title captures it: "Why Your AI Coding Agent Keeps Forgetting Everything."

3. **Trust deficit (only 29% trust AI code accuracy)**: Trust declined from 40% to 29% year-over-year. The more developers use AI tools, the less they trust them.

4. **Code quality degradation at scale**: LinearB data shows 67.3% of AI-generated PRs get rejected vs 15.6% for manual code. Google DORA Report: 90% AI adoption increase correlates with 9% bug rate climb, 91% code review time increase, 154% PR size increase. AI code creates 1.7x more issues (CodeRabbit).

5. **Architectural drift**: Agents make locally sensible but globally inconsistent decisions. They suggest deprecated APIs, miss internal conventions, and produce style inconsistencies even with linters configured.

**Secondary Pain Points**:
- Cost (loudest complaint on Reddit)
- Agent adoption resistance (52% either don't use agents or stick to simpler tools)
- Collaboration impact (only 17% say agents improved team collaboration -- lowest-rated impact)
- Inconsistent output (1.5x more likely to produce code not matching team standards)

**What Developers Want** (synthesized from complaints):
- An agent that remembers project conventions across sessions
- An agent that learns from its own mistakes and doesn't repeat them
- An agent that maintains consistent code style and architecture
- Better signal on what the agent is actually doing and why
- Reduced verification burden -- the agent should catch its own mistakes

**Acumen's alignment**: Pain points 2 (context amnesia), 3 (trust), and 5 (drift) are exactly what Acumen targets. The observe->learn->improve loop directly addresses "remembers conventions" and "learns from mistakes." The metadata-only approach addresses trust (privacy-safe). The skill synthesis addresses drift (codifying patterns into reusable rules).

**Sources**: [Stack Overflow 2025 Developer Survey](https://survey.stackoverflow.co/2025/ai), [SonarSource State of Code 2026](https://www.sonarsource.com/state-of-code-developer-survey-report.pdf), [CodeRabbit AI vs Human Report](https://www.coderabbit.ai/blog/state-of-ai-vs-human-code-generation-report), [Faros AI Agent Reviews](https://www.faros.ai/blog/best-ai-coding-agents-2026), [Mike Mason on Agent Coherence](https://mikemason.ca/writing/ai-coding-agents-jan-2026/)

### 9e. Strategic Implications for Acumen

**Strengths to emphasize**:
1. **Privacy-safe metadata-only observation** -- no competitor does this. Every alternative reads conversation content.
2. **Automated hook-based data collection** -- competitors rely on manual triggers or reading auto-memory.
3. **Zero external dependencies** -- Python stdlib only. Most competitors need Node.js, npm packages, or external services.
4. **Plugin packaging ready** -- proper plugin.json, installable via marketplace system.

**Gaps to address**:
1. **Marketplace presence** -- Acumen needs to be in `anthropics/claude-plugins-official` or `buildwithclaude` to be discoverable. Currently install is local-only.
2. **Demonstrated results** -- claude-reflect claims 30% reduction in repetitive instructions. Acumen needs comparable metrics.
3. **Cross-platform testing** -- claude-reflect explicitly supports macOS/Linux/Windows with 160 tests. Acumen's test coverage needs to be competitive.

**Market timing**: The ecosystem is growing fast. The window to establish Acumen as the "observability + self-improvement" plugin is open but closing. Multiple approaches are converging on the same problem from different angles.

---

## 10. Darwin Godel Machine (DGM)

**Paper**: [arXiv:2505.22954](https://arxiv.org/abs/2505.22954) | **Authors**: Zhang, Hu, Lu, Lange, Clune (Sakana AI) | **Released**: May 2025, updated March 2026
**Code**: [github.com/jennyzzt/dgm](https://github.com/jennyzzt/dgm) | **Blog**: [sakana.ai/dgm](https://sakana.ai/dgm/)

### What It Does

A self-improving coding agent that rewrites its own Python codebase to get better at solving programming tasks. It marries Darwinian evolution (population, selection, mutation) with Godelian self-reference (the agent modifies itself). The "Godel" part is that the agent can read and edit its own source code; the "Darwin" part is that it maintains a population archive and selects parents based on fitness.

### Architecture

- **Base agent**: A tool-use coding agent with two tools (bash execution, file editing), powered by a frozen foundation model (Claude 3.5 Sonnet New for self-modification, Claude 3.5 Sonnet or o3-mini for evaluation)
- **Archive**: An ever-growing population of agent variants, organized as a phylogenetic tree. Every agent that compiles and retains code-editing ability is added. Failed modifications are discarded.
- **Evaluation**: Staged -- 10 tasks (basic functionality check), then 50 tasks (performance estimate), then 200 tasks (for top performers). Benchmarks are SWE-bench Verified and Polyglot.

### The Self-Improvement Loop (step by step)

1. **Select parent** from archive. Probability is roughly proportional to performance score AND the number of its children that retained codebase-editing ability. This rewards agents that are both good performers and good ancestors.
2. **Analyze**: The selected parent agent receives its own benchmark evaluation logs (what it got wrong and why).
3. **Propose**: The agent proposes the next feature to implement in its own codebase (e.g., "add string-replace editing instead of whole-file replacement").
4. **Implement**: The agent modifies its own Python source code to implement the proposed feature.
5. **Evaluate**: The new child agent is tested on benchmark subsets in staged fashion.
6. **Archive**: If the child compiles and can still edit codebases, it is added to the archive regardless of performance (this is critical for open-endedness).
7. **Repeat** for ~80 iterations.

### Key Mechanism: Open-Ended Exploration

The critical insight is that DGM does NOT just keep the best agent and iterate. It maintains the entire archive and allows branching from any agent with non-zero probability. This means:

- Suboptimal agents that contain novel ideas are preserved as "stepping stones"
- Multiple evolutionary paths are explored simultaneously
- The system can escape local optima because it doesn't discard dead-end-looking branches that may unlock future breakthroughs
- This is directly inspired by quality-diversity algorithms (MAP-Elites family) from open-endedness research

**Ablation proof**: DGM without open-ended exploration (only keeping the latest best agent) performs significantly worse. The archive is load-bearing.

### Specific Improvements DGM Discovered

These emerged automatically without human guidance:

1. **Granular file editing**: Line-based file viewing + string replacement instead of whole-file operations (the single most important tool improvement)
2. **Multi-attempt strategy**: Making multiple solution attempts per problem
3. **Peer review**: Using a second FM call to evaluate and select the best solution from multiple attempts
4. **Long-context management**: Auto-summarizing prior interactions to avoid context window overflow
5. **Informed retry**: Considering previous failed attempts when generating subsequent ones

These are remarkably human-like engineering improvements -- the kind of things a senior engineer would add to a coding agent scaffold.

### What Makes It Work

1. **Empirical validation, not formal proof**: The original Godel Machine (Schmidhuber 2007) required mathematical proofs that modifications were improvements. DGM drops this requirement entirely and uses benchmark performance as the judge. This is what makes it practical.
2. **Frozen FM, mutable scaffold**: The LLM weights never change. Only the agent's Python code (tools, workflow, prompts) evolves. This is tractable and safe.
3. **Self-referential**: The agent reads its own code and its own evaluation logs. It knows what it is and what it's bad at.
4. **Archive as collective memory**: The population preserves all viable variations, enabling recombination of ideas across lineages.

### Limitations and Costs

- **$22,000 and 2 weeks** for a single DGM run on SWE-bench
- Performance is bounded by the frozen FM's capabilities
- Risk of "objective hacking" -- agents gaming benchmark metrics rather than genuinely improving
- Evolved agents can become complex and uninterpretable
- Currently limited to coding domain

### Results

- SWE-bench Verified: 20.0% -> 50.0% (+30 absolute points)
- Polyglot: 14.2% -> 30.7% (+16.5 absolute points)

### Lessons for Acumen

- **Archive-based exploration beats greedy hillclimbing**. Acumen should preserve diverse insights/strategies, not just converge on the "best" one. Failed approaches may unlock future improvements.
- **Self-analysis of failure logs is the key input**. DGM's self-improvement proposals come from analyzing what went wrong. Acumen's observation data serves this same purpose.
- **Tool and workflow improvements are the highest-leverage mutations**. DGM's biggest gains came from better file-editing tools and multi-attempt workflows, not from prompt tweaking.
- **Staged evaluation prevents wasted compute**. Quick sanity checks before expensive full evaluations.
- **The scaffold is the thing to evolve, not the model**. Acumen already operates on this principle (improving CLAUDE.md, skills, hooks -- not model weights).

---

## 11. Absolute Zero Reasoner (AZR)

**Paper**: [arXiv:2505.03335](https://arxiv.org/abs/2505.03335) | **Authors**: Zhao et al. (Tsinghua Leap Lab) | **Released**: May 2025
**Code**: [github.com/LeapLabTHU/Absolute-Zero-Reasoner](https://github.com/LeapLabTHU/Absolute-Zero-Reasoner) | **Accepted**: NeurIPS 2025 Spotlight

### What It Does

A self-improving reasoning system that requires ZERO external training data. A single LLM simultaneously proposes tasks, solves them, and improves at both through reinforcement learning. It uses a Python code executor as the sole source of ground truth -- no human labels, no curated datasets.

### Architecture

One unified LLM (pi_theta) plays two roles:
- **Proposer**: Generates code-based reasoning tasks optimized for learning potential
- **Solver**: Attempts to solve the proposed tasks

The **environment** is a Python code executor that:
- Validates proposed tasks (syntax, determinism, safety)
- Verifies solver answers (execution equality)
- Provides binary rewards (correct/incorrect)

Three **task buffers** accumulate valid self-generated triplets (program, input, output) over training.

### The Three Task Types

This is the core innovation -- three complementary reasoning modes, all grounded in executable code:

1. **Deduction** (output prediction): Given a program and input, predict the output. Tests step-by-step logical reasoning and code tracing. The proposer generates (program, input) pairs; the environment executes to get the ground-truth output.

2. **Abduction** (input inference): Given a program and output, infer a valid input. Tests backward reasoning and search. Verification uses output equivalence: p(inferred_input) == p(true_input), which handles non-bijective programs.

3. **Induction** (program synthesis): Given input-output examples, synthesize the program. Tests generalization. Verification runs the synthesized program on hidden test cases. Uses first half of I/O pairs for training, second half for validation (prevents if-else overfitting).

### The Self-Play Loop (step by step)

1. **Initialize**: Bootstrap from a single identity function triplet. Seed each buffer with B*4 examples.
2. **Propose**: For each batch element, sample K reference triplets from the buffer and generate new tasks conditioned on task type and references. Explicit prompt: "generate different tasks" for diversity.
3. **Validate**: Python executor checks proposed tasks: syntax correctness, safety (no os/sys/shutil), determinism (run twice, outputs must match).
4. **Buffer**: All valid triplets added to the appropriate buffer regardless of reward.
5. **Solve**: Model attempts to solve all proposed tasks.
6. **Verify**: Python executor checks solver answers via execution equality.
7. **Reward**: Compute proposer learnability rewards and solver correctness rewards.
8. **Update**: Task-Relative REINFORCE++ with 6 separate baselines (one per task-type x role combination).
9. **Repeat**.

### The Learnability Reward (the key mechanism)

For each proposed task, run n Monte Carlo solver rollouts. Compute average success rate r_bar.

- If r_bar = 0 (impossible): reward = 0
- If r_bar = 1 (trivial): reward = 0
- Otherwise: reward = 1 - r_bar

This pushes the proposer to generate tasks at the frontier of the solver's ability -- not too easy, not too hard. Tasks near 50% success rate get the highest reward. This creates an automatic curriculum that tracks the solver's improving capability.

### How It Avoids Degenerate Behavior

1. **Learnability reward**: Trivial/impossible tasks get zero reward
2. **Diversity prompting**: Proposer sees K reference examples with explicit instruction to generate different tasks
3. **Three complementary task types**: Each requires distinct reasoning modes, preventing convergence to a single easy distribution
4. **Code executor verification**: Ground truth is objective (execution result), not a learned reward model. This eliminates reward hacking.
5. **Ablation**: Removing any single task type drops overall performance 3-5 points, confirming they are mutually reinforcing

### Results

Trained on Qwen2.5 models (3B, 7B, 14B):
- **Zero data**: Outperforms models trained on 2k-484k curated human examples
- **Cross-domain transfer**: Code-trained AZR gains +15.2 points on MATH benchmarks (vs +0.65 for expert-labeled baselines). Training on self-generated code tasks transfers massively to math.
- **Scaling**: Bigger models yield bigger gains (+5.7 at 3B, +10.2 at 7B, +13.2 at 14B)

### What Makes It Work

1. **Verifiable environment as reward source**: The code executor is the oracle. No learned reward model, no reward hacking. This is what makes zero-data training stable.
2. **Automatic curriculum via learnability**: The proposer naturally generates harder tasks as the solver improves. No manual curriculum design.
3. **Cross-role knowledge transfer**: Training on proposing tasks improves solving (and vice versa). Joint training on a unified model outperforms separate training.
4. **Emergent behaviors**: Models spontaneously develop intermediate planning via code comments (resembling ReAct), enumeration strategies for induction, and trial-and-error for abduction -- without being taught these strategies.

### Lessons for Acumen

- **The verifiable environment principle is paramount**. AZR works because code execution provides objective ground truth. For Acumen, the analog is: tool success/failure, test pass/fail, lint results -- all are verifiable signals. Insights grounded in verifiable outcomes are far more valuable than LLM-judged ones.
- **Automatic difficulty calibration is powerful**. Acumen could weight insights by how "at the frontier" they are -- patterns the agent sometimes gets right and sometimes doesn't. These are the highest-leverage improvement targets.
- **Three complementary reasoning modes prevent monoculture**. Acumen's reflection could similarly cover multiple dimensions: what tools failed (deduction analog), what could have caused a failure (abduction analog), and what general pattern explains multiple observations (induction analog).
- **Self-generated training signal can outperform curated data**. Acumen's session observations are self-generated data. The key is having the right reward signal to learn from them.

---

## 12. Live-SWE-agent

**Paper**: [arXiv:2511.13646](https://arxiv.org/abs/2511.13646) | **Authors**: Xia, Wang et al. | **Released**: November 2025
**Code**: [github.com/OpenAutoCoder/live-swe-agent](https://github.com/OpenAutoCoder/live-swe-agent) | **Leaderboard**: [live-swe-agent.github.io](https://live-swe-agent.github.io/)

### What It Does

The first runtime self-evolving software engineering agent. Unlike DGM (which evolves offline across many runs), Live-SWE-agent evolves during a single task execution. It starts with a minimal scaffold (bash-only) and creates its own tools on the fly while solving real-world issues.

### Architecture: Mini-SWE-Agent

The agent starts intentionally minimal:
- **Only bash tools** -- no file editors, no search utilities, no specialized commands
- The agent receives: project codebase + issue description
- At each step, it can either: execute a command (use existing tools) OR create a new custom tool

### Runtime Evolution Mechanism

1. **Lightweight step-reflection**: After each environmental interaction, a reflection prompt asks: "Would making or improving a tool help me here?"
2. **Tool synthesis**: If yes, the agent writes a bash-invokable Python script that becomes a first-class action
3. **Validation**: Each new tool includes explicit error handling and post-condition verification
4. **Integration**: Created tools are immediately available for subsequent steps in the same task
5. **Iteration**: Tools can be revised as understanding of the problem deepens

This is NOT a preprocessing step. Tool creation is interleaved with problem-solving in a continuous loop.

### What Tools It Creates for Itself

Examples observed in practice:
- **Advanced editors** with validation and actionable error feedback (vs raw sed/awk)
- **Structured search utilities** that limit output to prevent prompt overload
- **Domain-specific analyzers** (MARC parsers, Go static analyzers, format-specific tools)
- **Context management tools** for efficient information extraction from large codebases

### Online vs Offline Evolution (key distinction)

| Aspect | DGM (offline) | Live-SWE-agent (online) |
|--------|---------------|------------------------|
| When | Between tasks, across population | During single task execution |
| Cost | $22k, 2 weeks | Zero additional cost |
| Scope | Evolves entire agent codebase | Creates task-specific tools |
| Persistence | Permanent archive of agents | Tools exist for current task only |
| Transfer | Evolved agents used on future tasks | No cross-task transfer (each task starts fresh) |

### Results

- SWE-bench Verified: 79.2% (Claude Opus 4.5), 77.4% (Gemini 3 Pro) -- outperforming manually-engineered scaffolds
- SWE-bench Pro: 45.8% SOTA
- Up to 22.6% absolute improvement over static agents for advanced LLMs
- Weaker LLMs may not benefit (the meta-cognitive capability to create useful tools requires strong base models)

### What Makes It Work

1. **The agent IS software**: Software agents can modify themselves because they are programs. This is a tautological but profound insight.
2. **Task-driven tool creation**: Tools aren't speculative -- they emerge from actual bottlenecks encountered during real problem-solving. Every tool has an immediate use case.
3. **Zero offline overhead**: No population, no archive, no multi-week training. The evolution happens in the same budget as the task itself.
4. **Lightweight reflection is sufficient**: A single prompt ("would a tool help?") is enough to trigger productive self-modification. No complex meta-learning.

### Lessons for Acumen

- **Runtime self-modification is practical TODAY with strong models**. The reflection prompt pattern ("would X help?") is simple and effective. Acumen's hooks could include a similar lightweight reflection step.
- **Tool creation is the highest-ROI evolution**. Both DGM and Live-SWE-agent converge on this: the biggest improvements come from creating better tools, not tweaking prompts.
- **Fresh-start per task has advantages**. Live-SWE-agent intentionally does NOT persist tools across tasks. This avoids tool bloat and ensures every tool earns its place. Acumen should consider "tool/skill expiry" mechanisms.
- **The minimal starting point matters**. Starting with less forces the agent to create exactly what it needs. Acumen's "safe tier only auto-applies" principle is aligned: don't front-load improvements, earn them through observation.

---

## 13. Evolutionary Agent Optimization (ARTEMIS + Related Work)

### ARTEMIS: Evolving Excellence

**Paper**: [arXiv:2512.09108](https://arxiv.org/abs/2512.09108) | **Authors**: Brookes et al. | **Released**: December 2025

A no-code evolutionary optimization platform that treats agents as black boxes and jointly optimizes their configurations (prompts, tool descriptions, parameters) through semantically-aware genetic operators.

**Architecture**:
1. **Component Discovery**: Automatically analyzes agent codebase to find optimizable elements using semantic search
2. **Local Optimization**: Genetic algorithms with LLM-based mutation and crossover operators that maintain semantic validity
3. **Global Optimization**: Bayesian optimization to find synergistic component combinations
4. **Evaluation**: Hierarchical -- cheap LLM-based filters, then expensive benchmark runs

**Key Results**: Mini-SWE agent gained 10.1% improvement. The system discovered that the original "general improvement" heuristic should be replaced with a "bottleneck-driven" strategy -- a qualitative strategy shift, not just prompt tweaking.

**Key Insight**: Joint optimization of multiple components (prompts + tool descriptions + parameters) outperforms optimizing any single component in isolation. The interdependencies between components matter.

### Multi-Agent Evolve (MAE)

**Paper**: [arXiv:2510.23595](https://arxiv.org/abs/2510.23595) | **Accepted**: ICLR 2026

Three co-evolving roles from a single LLM:
- **Proposer**: Generates increasingly difficult questions
- **Solver**: Attempts solutions
- **Judge**: Evaluates both with domain-agnostic self-rewarding

The proposer adapts difficulty based on the solver's current capability (similar to AZR's learnability reward). Results: +4.54% average across math, commonsense, and reading comprehension on Qwen2.5-3B.

### Self-Evolving Agents Taxonomy (Survey)

**Paper**: [arXiv:2507.21046](https://arxiv.org/abs/2507.21046) | **Survey covering 200+ papers**

The survey identifies three design dimensions:

**WHAT evolves**:
- Model parameters (fine-tuning from self-generated data)
- Context (memory systems, prompt refinement)
- Tools (creation, mastery, selection)
- Architecture (workflow graphs, multi-agent topology)

**WHEN it evolves**:
- Intra-task (during execution -- like Live-SWE-agent)
- Inter-task (between tasks -- like DGM)

**HOW it evolves**:
- Reward-based (textual feedback, internal confidence, external scores)
- Imitation (self-demonstrations, peer learning)
- Population-based (evolutionary algorithms, quality-diversity)

**Unifying formulation**: f(Pi, tau, r) = Pi', where agent system Pi transforms based on trajectory tau and feedback r into evolved system Pi'.

**Practical challenges identified**:
1. Evaluation benchmarks are too short-horizon to measure real adaptation
2. Catastrophic forgetting when learning new capabilities
3. Most deployed systems are "proto-evolutionary" (human-guided), not fully autonomous
4. Safety and controllability of self-modifying systems is unsolved

### Lessons for Acumen (from evolutionary approaches collectively)

- **Joint optimization > isolated optimization**. ARTEMIS showed that optimizing prompts alone gives less than optimizing prompts + tools + parameters together. Acumen's improvements should consider interactions between CLAUDE.md rules, skills, and hooks.
- **The Proposer-Solver-Judge triad recurs everywhere**. AZR, MAE, and many others independently converge on this pattern. Acumen's reflection agent could adopt this: observe (propose what to learn), analyze (solve for the insight), validate (judge whether the insight is actionable and correct).
- **Co-evolution beats isolated improvement**. MAE shows that evolving the question-generator alongside the solver produces better results than evolving either alone. Acumen's observation hooks and reflection agent should co-evolve.
- **The WHAT-WHEN-HOW taxonomy is useful for design**. For Acumen: WHAT = CLAUDE.md rules + skills + hooks. WHEN = inter-session (reflection after sessions). HOW = reward-based (tool success/failure signals from observations).

---

## 14. Cross-Cutting Synthesis: Patterns Across All Systems

### Pattern 1: Verifiable Rewards Beat Learned Rewards

Every successful system grounds improvement in objective verification:
- DGM: benchmark pass/fail
- AZR: code execution equality
- Live-SWE-agent: tool produces correct output
- AutoResearch: val_bpb metric
- M2.7: evaluation benchmark scores

Systems using LLM-as-judge or learned reward models are more fragile and prone to reward hacking. **For Acumen**: Ground insights in verifiable signals (test results, lint output, tool exit codes), not LLM self-evaluation.

### Pattern 2: The Scaffold Is the Lever

No system improves by changing model weights in real-time. All improve by changing the surrounding code:
- DGM: modifies agent Python code
- Live-SWE-agent: creates new tools
- AutoResearch: modifies train.py
- ARTEMIS: optimizes prompts + tool descriptions
- M2.7: modifies scaffold code

**For Acumen**: This validates the core architecture. CLAUDE.md + skills + hooks ARE the scaffold. Improving them is the right approach.

### Pattern 3: Diversity Preservation Enables Breakthrough

- DGM: archive of all viable agents (not just the best)
- AZR: three complementary task types prevent monoculture
- ARTEMIS: population-based search with diverse candidates

Greedy hillclimbing (only keeping the best) consistently underperforms archive-based approaches. **For Acumen**: Don't prune insights aggressively. Preserve diverse observations and strategies even if they don't seem immediately useful.

### Pattern 4: Self-Analysis of Failures Is the Primary Signal

- DGM: reads its own benchmark evaluation logs to propose improvements
- AZR: learnability reward identifies exactly what the solver struggles with
- M2.7: analyzes failure trajectories from previous runs

**For Acumen**: The observation data about tool failures, error patterns, and session struggles IS the primary improvement signal. This is already the design. The research validates it.

### Pattern 5: Lightweight Meta-Cognition Is Sufficient

- Live-SWE-agent: one reflection prompt ("would a tool help?") is enough
- DGM: agent simply reads its own logs and proposes next feature
- AutoResearch: agent reads program.md and decides what to try

Complex meta-learning architectures are not necessary. Simple reflection on recent performance is enough to drive improvement. **For Acumen**: The reflection agent's job is straightforward -- read observations, extract patterns, propose improvements. Don't over-engineer the meta-cognitive layer.

### Pattern 6: Compute-Bounded Evaluation Makes Everything Tractable

- AutoResearch: 5-minute training window
- DGM: staged evaluation (10 -> 50 -> 200 tasks)
- AZR: binary rewards from fast code execution
- ARTEMIS: hierarchical evaluation (cheap filter then expensive benchmark)

**For Acumen**: Insight validation should be cheap. A quick check (does this pattern match recent observations?) before expensive application (modifying CLAUDE.md or creating a skill).

---

## 15. Anthropic Auto-Dream: Memory Consolidation for Coding Agents

**Discovered**: March 2026 (feature flag `tengu_onyx_plover` in Claude Code v2.1.83) | **Status**: Experimental, rolling out via server-side flag
**System prompt**: [Piebald-AI/claude-code-system-prompts](https://github.com/Piebald-AI/claude-code-system-prompts/blob/main/system-prompts/agent-prompt-dream-memory-consolidation.md)

### What It Is

Auto-Dream is NOT a self-improving agent framework in the DGM/AZR sense. It is a **memory consolidation subsystem** for Claude Code -- a background sub-agent that periodically reviews, prunes, deduplicates, and reorganizes the agent's accumulated memory files between sessions. The name is a deliberate analogy to human REM sleep, where short-term memories are consolidated into long-term storage.

It solves a specific problem: after 20+ sessions, auto-memory notes become noisy -- contradictory entries, stale debugging solutions referencing deleted files, relative dates that lose meaning, and duplicate observations. Auto-Dream is the cleanup pass that prevents memory decay from degrading agent performance.

### Architecture

Claude Code now has a four-layer memory architecture:
1. **CLAUDE.md**: User-written instructions and project rules (static, human-maintained)
2. **Auto Memory**: Model-generated notes written during sessions (append-only, accumulates)
3. **Session Memory**: Conversation continuity within a single session (ephemeral)
4. **Auto-Dream**: Periodic consolidation of everything Auto Memory has accumulated (maintenance)

Auto-Dream is a background sub-agent with its own system prompt, separate from the primary coding agent. It has read-only access to the codebase (cannot modify source code) and write access only to memory files.

### The Four-Phase Consolidation Cycle

**Phase 1 -- Orient**: Scans the memory directory, reads MEMORY.md index, skims topic files. Builds a map of current memory state to avoid creating duplicates. Checks for subdirectories like `logs/` or `sessions/`.

**Phase 2 -- Gather Signal**: Searches for high-value information using targeted grep-style searches of JSONL session transcripts. Prioritizes: (1) daily logs (append-only stream), (2) existing memories that contradict current codebase facts, (3) narrow grep hits for corrections, explicit saves, recurring themes. Instruction: "Don't exhaustively read transcripts. Look only for things you already suspect matter."

**Phase 3 -- Consolidate**: The core operation. Merges new signal into existing topic files (not creating new ones). Converts relative dates to absolute dates for durability. Deletes contradicted facts at their source. Resolves conflicting entries.

**Phase 4 -- Prune and Index**: Updates MEMORY.md to stay under 200 lines (~25KB). Each entry is one line under ~150 characters: `- [Title](file.md) -- one-line hook`. Removes stale pointers, shortens verbose entries, adds new memories, reorders by relevance.

### Trigger Conditions

Both conditions must be met:
- **Time threshold**: At least 24 hours since last consolidation
- **Session threshold**: At least 5 sessions have accumulated

Users can also trigger manually via prompt ("consolidate my memory using dream"). The system uses lock files to prevent concurrent consolidation.

### Performance Observation

One reported case consolidated 913 sessions in approximately 8-9 minutes.

### Theoretical Foundation: Sleep-Time Compute

Auto-Dream draws on the "Sleep-time Compute" concept from a Letta/UC Berkeley paper ([arXiv:2504.13171](https://arxiv.org/abs/2504.13171), April 2025). The core insight: not all computation needs to happen while the user is waiting. Background cycles during idle time can pre-organize, pre-index, and pre-consolidate information, reducing test-time compute requirements by approximately 5x for relevant tasks. The biological analog: humans consolidate memories during sleep, and the preprocessing makes waking cognition faster and more accurate.

### How It Compares to DGM, AZR, and Other Self-Improving Systems

Auto-Dream operates at a fundamentally different level than DGM, AZR, or ARTEMIS:

| Dimension | Auto-Dream | DGM | AZR | Acumen |
|-----------|-----------|-----|-----|--------|
| **What improves** | Memory quality | Agent source code | Model reasoning weights | Agent rules, skills, hooks |
| **Mechanism** | Prune/merge/organize notes | Evolutionary code mutation | RL self-play with zero data | Observation -> reflection -> rule extraction |
| **Scope** | Knowledge management | Agent architecture | Model capabilities | Agent behavior config |
| **Modifies model weights** | No | No | Yes | No |
| **Modifies agent code** | No | Yes | No | No (modifies config/rules) |
| **Self-referential** | Partially (reviews its own notes) | Fully (reads/edits own code) | Fully (proposes own curriculum) | Partially (observes own failures) |
| **Safety risk** | Very low (read-only on code) | High (reward hacking observed) | Low (code executor verification) | Low (metadata-only observation) |
| **Cost** | Cheap (one sub-agent pass) | $22k per run | GPU training time | Cheap (LLM reflection calls) |

**Key distinction**: Auto-Dream is infrastructure maintenance, not capability improvement. It keeps the agent's existing knowledge clean and accessible. DGM/AZR/Acumen actually make the agent better at tasks it previously struggled with. Auto-Dream prevents the agent from getting worse due to memory noise; the others make it get better.

### Lessons for Acumen

1. **Memory hygiene is a prerequisite for effective self-improvement.** If Acumen's insight store accumulates contradictory or stale rules, the agent's performance will degrade regardless of how good the new insights are. Auto-Dream proves this is a real problem at scale (20+ sessions). Acumen needs a consolidation mechanism for its own insight/rule store.

2. **The 4-phase pattern (orient, gather, consolidate, prune) is reusable.** Acumen's reflection agent could use a similar structured approach: survey existing insights, identify contradictions or staleness, merge/update, and prune the index. This is more principled than ad-hoc "check if rule still applies."

3. **Time + session thresholds are a pragmatic trigger model.** Rather than running consolidation on every session (wasteful) or manually (forgotten), the dual-threshold approach ensures consolidation happens often enough to prevent decay but not so often it wastes compute.

4. **Read-only safety is achievable and sufficient.** Auto-Dream proves you can do meaningful maintenance work on agent state without write access to the codebase. Acumen's insight store operations should similarly be scoped: the reflection agent modifies rules and skills but never directly modifies project source code.

5. **The 200-line index limit is a useful constraint.** Unbounded memory indexes become noise. Acumen's rule store should similarly have a capacity limit that forces prioritization and pruning of low-value insights.

6. **Auto-Dream complements self-improvement but doesn't replace it.** Auto-Dream keeps the knowledge base healthy. DGM/AZR/Acumen add new capabilities. Both are needed. Acumen should think of itself as the capability-improvement layer that sits on top of a clean knowledge base -- and should incorporate auto-dream-style consolidation as a maintenance pass on its own insight store.

**Sources**: [claudefa.st guide](https://claudefa.st/blog/guide/mechanics/auto-dream), [DEV Community analysis](https://dev.to/akari_iku/does-claude-code-need-sleep-inside-the-unreleased-auto-dream-feature-2n7m), [tessl.io](https://tessl.io/blog/anthropic-tests-auto-dream-to-clean-up-claudes-memory/), [implicator.ai](https://www.implicator.ai/anthropic-adds-auto-dream-to-claude-code-fixing-memory-decay-between-sessions/), [Frank's World](https://www.franksworld.com/2026/03/29/claude-code-memory-2-0-the-game-changing-auto-dream-feature/), [GitHub system prompt](https://github.com/Piebald-AI/claude-code-system-prompts/blob/main/system-prompts/agent-prompt-dream-memory-consolidation.md), [Sleep-time Compute paper](https://arxiv.org/abs/2504.13171)

---

## 16. Evolutionary Reinforcement Learning (ERL) Family

**Surveyed**: March 2026 | **Type**: Hybrid EA+RL optimization paradigm | **Scope**: Continuous control, agent policy learning, reward design

### What ERL Is

Evolutionary Reinforcement Learning (ERL) is a family of algorithms that fuse Evolutionary Algorithms (EA) with Reinforcement Learning (RL). The core insight: EA provides diverse global exploration through population-based search, while RL provides efficient local optimization through gradient-based policy improvement. Neither alone is sufficient for complex agent tasks.

The canonical ERL architecture (Khadka & Tumer, 2018):
1. A **population of EA actors** explores the parameter space, generating diverse behavioral trajectories
2. These trajectories feed an **off-policy RL agent's replay buffer**, giving the RL agent diverse experience it wouldn't generate on its own
3. The RL agent trains via standard gradient-based methods (e.g., TD3, SAC)
4. Periodically, the RL agent's policy is **injected back into the EA population**, seeding gradient-informed solutions into the evolutionary search
5. The population evolves via mutation and crossover, maintaining diversity while incorporating RL's refinements

This bidirectional information flow -- EA provides exploration data to RL, RL provides refined policies back to EA -- is the defining characteristic.

### Three Research Directions in ERL

The field has organized into three branches:

**1. EA-assisted RL**: EA optimizes RL hyperparameters, architectures, or reward functions. RL does the actual policy learning. Example: Population-Based Training (PBT) evolves learning rates and discount factors while RL trains policies.

**2. RL-assisted EA**: RL guides the evolutionary search process itself. Example: using RL to learn crossover/mutation operators rather than using fixed heuristic operators.

**3. Synergistic EA+RL**: Both run simultaneously and share information bidirectionally (the canonical ERL pattern). This is the most relevant to self-improving agents.

### Key Systems in the ERL Family

#### ERL-Re2 (ICLR 2023)
**Paper**: [arxiv:2210.17375](https://arxiv.org/abs/2210.17375) | **Code**: [GitHub](https://github.com/yeshenpy/ERL-Re2)

The original ERL has a problem: each EA agent and the RL agent learn their policies independently, wasting computation on redundant feature learning and preventing knowledge transfer. ERL-Re2 solves this with **two-scale representation**:

- **Shared nonlinear state representation**: All EA and RL agents share the same feature extractor (the deep network layers). This captures common environment knowledge collectively.
- **Individual linear policy representations**: Each agent has its own lightweight linear head. This preserves behavioral diversity.

The linear policy space enables novel **behavior-level crossover and mutation** (rather than parameter-level), and a **Policy-extended Value Function Approximator (PeVFA)** that can estimate fitness without running full episodes -- dramatically improving sample efficiency.

Result: consistent SOTA on MuJoCo continuous control benchmarks.

#### DERL -- Differentiable Evolutionary Reinforcement Learning (Dec 2025)
**Paper**: [arxiv:2512.13399](https://arxiv.org/abs/2512.13399) | **Code**: [GitHub](https://github.com/sitaocheng/DERL)

DERL's innovation is making the evolutionary process **differentiable**. Traditional ERL treats the reward function as a black box -- evolution proposes reward functions, RL trains with them, and evolution only sees final task performance. DERL closes the loop:

**Bilevel Architecture**:
- **Outer loop (Meta-Optimizer)**: A lightweight 0.5B model that generates reward configurations by composing atomic primitives. Trained via RL (GRPO) using validation performance as its reward signal.
- **Inner loop (Policy)**: A standard RL agent trained with the Meta-Optimizer's generated reward. Evaluated on held-out tasks.

**Atomic Reward Primitives** (the building blocks the Meta-Optimizer composes):
- For robotic/scientific tasks: binary outcome reward + 3 process rewards (early/mid/late trajectory phases)
- For math reasoning: binary outcome + format verification + step-by-step detection + soft matching

The Meta-Optimizer generates 8 reward configurations per iteration, trains 8 corresponding inner policies, evaluates them, and uses the validation signal to improve its own reward-generation policy. This creates a **meta-gradient** -- the system learns which reward structures produce good policies.

**Results**: SOTA on ALFWorld (91.8%), ScienceWorld (98.2% in-distribution), and strong OOD generalization (65.0% on ALFWorld L2 vs 56.3% for baselines). The differentiable meta-optimization is particularly valuable for out-of-distribution scenarios where heuristic rewards degrade.

#### EvoRL Framework (ACM TELO, July 2025)
**Paper**: [arxiv:2501.15129](https://arxiv.org/abs/2501.15129) | **Code**: [GitHub](https://github.com/EMI-Group/evorl)

A practical engineering contribution: fully GPU-accelerated ERL in JAX. Eliminates the CPU-GPU communication bottleneck that makes population-based methods slow. Implements RL (A2C, PPO, DDPG, TD3, SAC), EA (CMA-ES, OpenES, ARS), and hybrid ERL paradigms (ERL, CEM-RL, PBT) all on-accelerator.

Important because ERL's population-based nature makes it 10-50x more compute-expensive than vanilla RL. GPU acceleration is what makes it practical.

### How ERL Compares to DGM/AZR/AutoResearch

| Dimension | ERL Family | DGM | AZR | AutoResearch |
|-----------|-----------|-----|-----|-------------|
| What evolves | Policy parameters + reward functions | Agent source code | Training curriculum + reasoning | Training code |
| Population | Yes (core design) | Yes (archive of agents) | No (single model, dual role) | No (single agent) |
| Gradient info | Yes (RL component) | No (LLM-based proposals) | Yes (GRPO) | No (black-box eval) |
| Human data needed | Task reward definition | Benchmark suite | Zero | program.md + train.py |
| Compute cost | High (population overhead) | Very high ($22K/run) | Moderate | Low (single GPU) |
| Domain | Continuous control, reward design | Software engineering | Math + code reasoning | ML training optimization |
| Self-improving? | Partially (reward/policy co-evolve) | Yes (rewrites own code) | Yes (proposes own curriculum) | Yes (modifies own training) |

**Key distinction**: ERL is fundamentally about **policy optimization** -- finding better control policies through hybrid search. DGM/AZR/AutoResearch are about **agent self-modification** -- agents changing their own code, prompts, or curricula. ERL provides the optimization substrate; the self-improving agent systems provide the self-modification loop.

### Lessons for Acumen

1. **Population diversity is load-bearing.** ERL-Re2's shared representation + individual policies is a clean pattern. For Acumen: maintain diverse rule/insight populations rather than converging to a single "best" set.

2. **Differentiable meta-optimization beats black-box evolution.** DERL's meta-gradient dramatically improves sample efficiency. For Acumen: when evaluating rules, track not just "did it help?" but "what kind of help did it provide?" to build richer improvement signals.

3. **The bilevel structure is universal.** Outer loop proposes improvements, inner loop validates them. This maps directly to Acumen's reflection (outer) -> application (inner) -> observation (validation) cycle.

4. **Compute cost is the bottleneck.** ERL needs GPU acceleration to be practical. For Acumen: the analog is LLM API cost. Keep the reflection/evaluation loop cheap.

**Sources**: [ERL Survey (Intelligent Computing)](https://spj.science.org/doi/10.34133/icomputing.0025), [ERL-Re2 (ICLR 2023)](https://arxiv.org/abs/2210.17375), [DERL (arxiv:2512.13399)](https://arxiv.org/abs/2512.13399), [EvoRL (arxiv:2501.15129)](https://arxiv.org/abs/2501.15129), [Awesome-ERL GitHub](https://github.com/yeshenpy/Awesome-Evolutionary-Reinforcement-Learning), [ERL Systematic Review (MDPI)](https://www.mdpi.com/2227-7390/13/5/833)

---

## 17. SWE-Evo Ecosystem (SWE-EVO Benchmark + Live-SWE-agent)

**Dates**: Nov 2025 -- Jan 2026 | **Type**: Benchmark + self-evolving SWE agent | **Scope**: Software engineering agent evaluation and runtime self-improvement

These are two distinct but complementary works that together define the state of the art in self-evolving software engineering agents.

### 17a. SWE-EVO: The Long-Horizon Benchmark

**Paper**: [arxiv:2512.18470](https://arxiv.org/abs/2512.18470) | **Authors**: Minh V. T. Thai, Tue Le, Dung Nguyen Manh, Huy Phan Nhat, Nghi D. Q. Bui

#### What It Is

SWE-EVO is a benchmark that tests what SWE-Bench cannot: **long-horizon, multi-file software evolution**. Where SWE-Bench gives agents a single issue to fix, SWE-EVO gives agents an entire release's worth of changes to implement.

#### Construction Methodology

Three-stage pipeline:
1. **Repository selection**: 7 mature open-source Python projects (scikit-learn, pydantic, dask, DVC, and others)
2. **Task extraction**: Evolution tasks derived from release notes between consecutive version tags, each requiring at least one FAIL_TO_PASS test
3. **Execution-based validation**: Instances discarded if they trigger installation errors or lack measurable test improvements

#### Scale and Complexity

The 48 tasks are far harder than anything in SWE-Bench:
- **Spec size**: 2,391 words per task (vs. single-paragraph issues in SWE-Bench)
- **Code scope**: 363 non-test files per codebase (max: 1,046)
- **Patch breadth**: 610.5 lines edited across 20.9 files, touching 51 functions per task
- **Test coverage**: 874 total tests per instance, with 81.4 FAIL_TO_PASS tests requiring fixes

#### The Fix Rate Metric

SWE-EVO introduces "Fix Rate" -- a soft-score metric that awards credit for each FAIL_TO_PASS test fixed, but returns zero if any PASS_TO_PASS test breaks. This captures partial progress while penalizing regressions.

Fix Rate reveals differences that binary Resolved Rate masks. GPT-4.1 and GPT-OSS both score 2.08% resolved, but differ in Fix Rate (4.65% vs 2.08%).

#### Performance Results: The Gap Is Enormous

| Model + Agent | SWE-Bench Verified | SWE-EVO Resolved | Drop |
|---------------|-------------------|------------------|------|
| GPT-5 + OpenHands | 65% | ~21% | 3x |
| GPT-5-mini | 59.8% | ~10% | 6x |
| DeepSeek-R1 | 57.6% | ~10% | 6x |

Even the strongest model solves only one-third as many tasks when faced with multi-file evolution.

#### Why Agents Fail (Trajectory Analysis)

Automated failure classification reveals distinct failure modes per model:
- **GPT-5** (strongest): >60% fail via "Instruction Following" -- misinterpreting nuanced release notes, not lacking coding ability
- **GPT-5-nano** (weakest): "Tool-Use" and "Syntax Error" failures -- degraded interface control
- **Open-source models** (Qwen, Kimi): "Incorrect Implementation" -- good tool use but weak semantic reasoning
- **DeepSeek-R1**: "Stuck in Loop" -- less adaptive trajectory planning

**Difficulty proxy**: PR count per task. Hard instances average 14.84 PRs vs 1.67 for easy ones. Stronger models adaptively allocate more turns to harder instances.

### 17b. Live-SWE-agent: Runtime Self-Evolution

**Paper**: [arxiv:2511.13646](https://arxiv.org/abs/2511.13646) | **Authors**: Chunqiu Steven Xia, Zhe Wang, Yan Yang, Yuxiang Wei, Lingming Zhang | **Code**: [GitHub](https://github.com/OpenAutoCoder/live-swe-agent)

#### What It Is

Live-SWE-agent is the first software engineering agent that **self-evolves at runtime** -- it starts with a minimal scaffold (bash-only, ~100 lines) and creates its own tools, analyzers, and workflows while solving real-world issues. No offline training, no benchmark-specific tuning.

The key insight: **software agents are themselves software systems**. An agent with code-writing capabilities can write code that extends its own capabilities.

#### Architecture

**Starting point**: mini-SWE-agent -- a minimal scaffold with only bash command access. No specialized tools, no file editors, no code search utilities.

**Evolution loop** (continuous, interleaved with problem-solving):
1. Agent receives codebase + issue description
2. At each step, agent chooses: execute a command OR create/modify a custom tool
3. A **step-reflection prompt** explicitly asks: "Would creating or revising a tool accelerate progress?"
4. Tools are defined as executable Python scripts within the environment
5. Tool synthesis is iterative -- agents refine tools as their understanding evolves
6. The underlying scaffold stays unchanged; evolution happens purely through tool creation

**What gets created**: General utilities (search, edit, view tools) AND task-specific analyzers (a MARC file analyzer for publication records, a Go static analyzer, domain-specific data format parsers). t-SNE visualizations show distinct clusters for edit/search/view tools with repository-specific variants.

#### The Step-Reflection Mechanism

A lightweight prompt appended after each environmental feedback asks the agent to examine past trajectories and decide whether tool creation would help. Without this prompt, tool creation drops from 3.28 to 2.92 tools per task and solve rate drops from 76% to 64%.

The reflection is deliberately simple -- no complex meta-learning, just one prompt.

#### Performance Results

**SWE-bench Verified** (500 problems):
- Claude Opus 4.5 + Live-SWE-agent: **79.2%** (SOTA as of late 2025)
- Gemini 3 Pro + Live-SWE-agent: **77.4%**
- Mini-SWE-agent baseline (no evolution): 70.6%
- Cost: $0.68 avg per problem (up from $0.56 baseline -- minimal overhead)

**SWE-Bench Pro** (731 problems): **45.8%** (SOTA)

**SWE-bench Multilingual** (50-problem subset): **46.0%** (vs 40.0% baseline)

#### Comparison with DGM (Darwin Godel Machine)

| Dimension | Live-SWE-agent | DGM |
|-----------|---------------|-----|
| Evolution timing | Runtime (per-task) | Offline (pre-deployment) |
| What evolves | Tools/analyzers created at runtime | Agent source code, scaffold, prompts |
| Offline training cost | **$0** | **~$22,000** (1,231 hours) |
| Per-task cost | ~$0.68 | Higher (complex scaffold) |
| SWE-bench (60-problem DGM subset) | **65.0%** | 53.3% |
| Generalization | Adapts per-task via tool creation | Static after offline training |
| LLM dependency | Scales with model capability | Fixed to trained configuration |

Live-SWE-agent wins on every dimension: cheaper, more performant, more generalizable, zero offline investment.

#### Ablation Studies (Critical Insights)

- **Removing tool creation entirely**: 76.0% -> 62.0% (22.6% degradation)
- **Removing reflection prompt**: 76.0% -> 64.0% with fewer tools created
- **Weak models (GPT-5-Nano)**: 68.2% performance degradation when attempting tool synthesis -- the approach requires sufficient reasoning capacity
- **Strong models benefit most**: Claude 4.5 Sonnet gains 22.6% improvement, suggesting the approach scales with LLM advancement

### Lessons for Acumen

1. **Runtime evolution beats offline training.** Live-SWE-agent's $0 offline cost and superior performance over DGM's $22K investment is definitive. Acumen's approach of generating insights in real-time during sessions is validated.

2. **One reflection prompt is enough.** The step-reflection mechanism is a single prompt -- and it drives the entire evolution. Acumen's reflection agent doesn't need complex architectures.

3. **Tool creation as the evolution primitive.** Live-SWE-agent doesn't modify its own code -- it creates new tools. For Acumen: skill creation (EXPAND phase) is the right evolution primitive. Don't modify core plugin code; create new skills/rules instead.

4. **Long-horizon tasks expose the real gaps.** SWE-EVO shows that agents scoring 65% on single issues score 21% on multi-file evolution. Session-level patterns (multi-step workflows) are much harder to capture and correspondingly more valuable.

5. **Failure mode classification is actionable.** SWE-EVO's taxonomy (instruction-following, tool-use, implementation, stuck-in-loop) maps to the kinds of patterns Acumen should detect and address with targeted rules.

6. **Model capability gates the approach.** Live-SWE-agent's ablations show weak models degrade with self-evolution. Design for strong models (Opus, Sonnet) and degrade gracefully for weaker ones.

**Sources**: [SWE-EVO paper (arxiv:2512.18470)](https://arxiv.org/abs/2512.18470), [Live-SWE-agent paper (arxiv:2511.13646)](https://arxiv.org/abs/2511.13646), [Live-SWE-agent GitHub](https://github.com/OpenAutoCoder/live-swe-agent), [Live-SWE-agent Leaderboard](https://live-swe-agent.github.io/), [SWE-EVO HTML](https://arxiv.org/html/2512.18470v1), [Live-SWE-agent Emergent Mind](https://www.emergentmind.com/papers/2511.13646)

---

## 18. Adjacent Systems: SAGE, MemRL, A-Evolve

### 18a. SAGE -- Skill Augmented GRPO for self-Evolution (Dec 2025)

**Paper**: [arxiv:2512.17102](https://arxiv.org/abs/2512.17102)

SAGE integrates a **skill library** into RL-based agent training. As the agent solves sequential tasks via GRPO rollouts, skills from previous tasks accumulate in the library and become available for subsequent tasks. A skill-integrated reward enhances both skill generation and utilization.

**Results**: 8.9% higher Scenario Goal Completion, 26% fewer interaction steps, 59% fewer tokens on AppWorld.

**Relevance**: Validates that accumulating reusable skills across tasks improves efficiency. This is Acumen's EXPAND phase. The 26% step reduction and 59% token reduction are the efficiency gains Acumen should target.

### 18b. MemRL -- Self-Evolving via Episodic Memory (Jan 2026)

**Paper**: [arxiv:2601.03192](https://arxiv.org/abs/2601.03192) | **Code**: [GitHub](https://github.com/MemTensor/MemRL)

MemRL separates **stable reasoning** (frozen LLM) from **plastic memory** (evolving episodic store). Two-Phase Retrieval filters candidates by semantic relevance, then selects by learned Q-values (utility). The LLM never changes; only the memory evolves via RL.

**Key innovation**: The frozen-LLM / evolving-memory separation solves the stability-plasticity dilemma. No fine-tuning, no catastrophic forgetting, continuous runtime improvement.

**Relevance**: The closest academic analog to Acumen's architecture. Acumen keeps Claude frozen and evolves external memory (CLAUDE.md rules, skills, observations). MemRL's Two-Phase Retrieval (relevance then utility) maps to Acumen's observe -> reflect -> apply pipeline. The Q-value utility scoring suggests Acumen should track per-rule effectiveness (which the evaluator already does).

### 18c. A-Evolve -- Amazon's Automated Agent Evolution (March 2026)

**Coverage**: [MarkTechPost](https://www.marktechpost.com/2026/03/29/meet-a-evolve-the-pytorch-moment-for-agentic-ai-systems-replacing-manual-tuning-with-automated-state-mutation-and-self-correction/)

Modular framework for automating agent improvement. Five-stage loop:
1. **Solve**: Agent attempts tasks
2. **Observe**: Results evaluated
3. **Evolve**: State modifications (prompt edits, parameter changes) proposed
4. **Gate**: Quality checks filter regressions
5. **Reload**: Successful mutations persist, git-tagged for reproducibility

**Results**: #1 on MCP-Atlas (79.4%), 76.8% on SWE-bench Verified, 76.5% on Terminal-Bench 2.0.

**Relevance**: A-Evolve's Solve-Observe-Evolve-Gate-Reload is structurally identical to Acumen's OBSERVE-LEARN-IMPROVE-EXPAND. The Gate stage maps to Acumen's SAFE tier validation. Git-tagging every mutation is a pattern Acumen should consider for rule versioning.

**Sources**: [SAGE (arxiv:2512.17102)](https://arxiv.org/abs/2512.17102), [MemRL (arxiv:2601.03192)](https://arxiv.org/abs/2601.03192), [MemRL GitHub](https://github.com/MemTensor/MemRL), [A-Evolve (MarkTechPost)](https://www.marktechpost.com/2026/03/29/meet-a-evolve-the-pytorch-moment-for-agentic-ai-systems-replacing-manual-tuning-with-automated-state-mutation-and-self-correction/)

---

## 19. Updated Cross-System Synthesis (Expanded with ERL + SWE-Evo)

### The Self-Improving Agent Landscape (March 2026, Full Picture)

**Tier 1: Runtime Self-Evolution (Zero offline cost)**
- Live-SWE-agent: Creates tools at runtime. 79.2% SWE-bench. $0 offline.
- AutoResearch: Modifies training code at runtime. 11% speedup. $0 offline.
- MemRL: Evolves episodic memory at runtime. Frozen LLM. $0 offline.

**Tier 2: Lightweight Offline + Runtime**
- AZR: Self-proposes training curriculum. Zero external data. NeurIPS 2025 spotlight.
- SAGE: Accumulates skill library across task rollouts. 26% step reduction.
- A-Evolve: Modular evolution framework. Git-tagged mutations. 76.8% SWE-bench.

**Tier 3: Heavy Offline Training**
- DGM: Archive-based code evolution. 50% SWE-bench. $22K per run.
- DERL: Bilevel meta-reward optimization. SOTA on ALFWorld/ScienceWorld.
- ERL family: Population-based policy evolution. Requires GPU-accelerated frameworks.

### The Frozen-Core / Evolving-Periphery Architecture (Universal Pattern)

| System | Frozen Core | Evolving Periphery |
|--------|------------|-------------------|
| Live-SWE-agent | Agent scaffold | Runtime tools |
| AutoResearch | prepare.py + evaluation | train.py |
| MemRL | LLM weights | Episodic memory + Q-values |
| AZR | Model architecture | Training curriculum |
| SAGE | Base model | Skill library |
| A-Evolve | Framework | Agent state (prompts, params) |
| DGM | Foundation model | Agent source code |
| DERL | Inner policy structure | Meta-reward function |
| **Acumen** | **Claude + plugin code** | **CLAUDE.md rules, skills, observations** |

Acumen fits naturally. The frozen core is Claude plus the plugin code. The evolving periphery is the rule store, skills, and observation data. Architecturally validated by the entire field.

### Evolution Primitive Determines Cost and Generalization

| Evolution Primitive | Cost | Generalization | Examples |
|--------------------|------|----------------|----------|
| Tool/script creation | Very low | Per-task | Live-SWE-agent |
| Memory/rule updates | Low | Cross-session | MemRL, Acumen |
| Skill accumulation | Low | Cross-task | SAGE, Acumen |
| Code modification | Medium | Per-codebase | AutoResearch, DGM |
| Reward function design | High | Cross-domain | DERL |
| Policy parameters | Very high | Domain-specific | ERL family |

Acumen uses the low-cost primitives (memory/rule updates, skill accumulation). This positions it well for practical deployment -- the evolution loop is cheap enough to run every session.

---

## 14. Trace2Skill: Automated Skill Extraction from Execution Traces

**Paper**: [arXiv:2603.25158](https://arxiv.org/abs/2603.25158) | **Authors**: Ni, Liu, Liu, Sun, Zhou, Cheng, Wang, Jiang, Jiang | **Published**: March 2026

### What It Does

Trace2Skill extracts transferable skills from execution traces by dispatching a parallel fleet of sub-agents to analyze diverse trajectories, then hierarchically consolidating their findings into a unified, conflict-free skill directory. The key insight: analyzing 128 trajectories in parallel and merging via inductive reasoning produces skills that transfer across model scales and out-of-distribution tasks.

### Architecture

**Skill structure**: A skill S = (M, R) comprises:
- **M (SKILL.md)**: Procedural knowledge in natural language -- when to apply techniques, step-by-step strategies, failure modes
- **R (Resources)**: Three subdirectories -- scripts/ (executable code), references/ (domain-specific lookup files), assets/ (supporting materials)

**Pipeline**:
1. **Trajectory generation**: Agent executes on tasks, producing labeled trajectories partitioned into success set T+ and failure set T-
2. **Parallel patch proposal**: 128 sub-agents run in parallel. Each analyst receives one frozen skill copy and a single trajectory, outputting a skill patch. Two specialist types:
   - *Success analysts*: Single-pass, identify generalizable behavior patterns
   - *Error analysts*: Multi-turn ReAct loops -- inspect files, compare outputs, iteratively diagnose failure root causes
3. **Hierarchical consolidation**: Patches merge in L = ceil(log_32 |P|) levels. A merge operator deduplicates, resolves conflicts, and preserves unique insights via inductive reasoning: recurring patterns across independent patches are treated as systematic task properties

**Conflict resolution** uses three deterministic guardrails:
- Patches referencing non-existent files are rejected
- Overlapping edits on same line ranges are flagged and withheld
- Updated skill format is validated programmatically

### Key Results

| Domain | Baseline | Trace2Skill | Gain |
|--------|----------|-------------|------|
| SpreadsheetBench (122B, deepening+combined) | 48.33% | 69.83% | +21.5pp |
| WikiTableQuestions (cross-model, 35B->122B) | 23.73% | 81.38% | +57.65pp |
| Math DAPO (122B, error analysis) | baseline | +3.0pp | in-distribution |
| DocVQA (122B, error analysis) | baseline | +15.3pp ANLS | vision |

The cross-model transfer result is the headline: skills evolved by Qwen3.5-35B improved Qwen3.5-122B by 57.65 absolute percentage points. Skills created by smaller models improve larger models because inductive filtering during consolidation discards model-specific quirks and retains systematic task patterns.

**Outperformed Anthropic's official xlsx skills** on SpreadsheetBench -- machine-evolved skills beat hand-authored ones.

### Skill Deepening vs. Skill Creation

- **Deepening**: Start with a human-expert-written skill. Pipeline refines it by adding failure-specific guidance and reinforcing effective strategies. The human skill provides a strong prior.
- **Creation from scratch**: Start with a skill drafted from parametric knowledge alone (no trajectory access). The parametric draft provides zero substantial improvement over no skill -- so all value comes from the evolution pipeline. This is genuine skill creation.

### What a Product Built on Trace2Skill Would Look Like

**Not a research tool -- a developer product:**

The product would be an automated "skill compiler" that:
1. Observes agent sessions (execution traces with outcomes)
2. Dispatches parallel analyzers against accumulated traces
3. Produces SKILL.md files that drop into Claude Code's .claude/skills/ directory
4. Skills auto-improve as more traces accumulate

**Concrete product mechanics:**
- User installs the plugin. Works normally for a week. Observation data accumulates.
- Weekly (or on-demand), the system runs the Trace2Skill pipeline against session traces
- Output: 1-3 new SKILL.md files per domain (e.g., "testing patterns for this project", "deployment workflow", "error handling in this codebase")
- Skills get staged for user review, or auto-applied at SAFE tier
- As more traces accumulate, skills deepen -- the references/ directory grows with project-specific lookup tables

**The key product insight**: Trace2Skill's parallel sub-agent architecture is expensive ($-wise) but produces dramatically better skills than sequential analysis. The product question is whether the cost is justified for a developer tool. At current API prices, analyzing 128 trajectories with a 35B model is plausible for a weekly batch job. The 57.65pp improvement justifies significant per-run cost.

### How Trace2Skill Combines with an Observation Pipeline

Acumen already captures tool_name, outcome, timestamp, error_type in its observation store. To feed Trace2Skill:

1. **Enrich observation granularity**: Trace2Skill needs trajectory-level structure (task start, sequence of actions, task outcome), not just individual tool call metadata. Acumen's session_id grouping already provides this -- each session's observations form a trajectory.
2. **Add outcome labels**: Trace2Skill partitions into success/failure. Acumen needs a reliable session-level outcome signal. Options: test pass/fail at session end, user satisfaction signal (tool denial count), or explicit /acumen-feedback command.
3. **Batch processing**: Trace2Skill is inherently batch, not streaming. Run it periodically against accumulated observation data, not on every session.
4. **Privacy constraint**: Acumen is metadata-only. Trace2Skill as published requires full trajectory content (tool inputs/outputs). A privacy-safe variant would need to work with metadata-enriched trajectories: (tool_name, outcome, error_type, duration, file_paths_touched) without content. This is a research gap -- no one has shown Trace2Skill works with metadata-only traces. But the inductive consolidation mechanism might still extract useful patterns from metadata because recurring tool-failure patterns are visible without content.

**Sources**: [Trace2Skill Paper](https://arxiv.org/abs/2603.25158), [Bytez Summary](https://bytez.com/docs/arxiv/2603.25158/paper)

---

## 15. Experiential Reflective Learning (ERL): Heuristic Extraction from Trajectories

**Paper**: [arXiv:2603.24639](https://arxiv.org/abs/2603.24639) | **Authors**: Allard, Teinturier, Xing, Viaud | **Published**: March 2026

### What It Does

ERL reflects on single-attempt task trajectories to extract structured heuristics -- actionable rules with explicit trigger conditions and recommended actions. At test time, an LLM scores stored heuristics for relevance to the current task and injects the top-k into the agent's system prompt.

### How Heuristics Work (the core mechanism)

A heuristic has two parts:
1. **Analysis**: What led to success or failure in the specific trajectory
2. **Learned guideline**: Trigger condition ("When I encounter X") + Action ("I must do Y")

**Concrete example from the paper**: "When sending emails to calendar attendees, first resolve names to email addresses via the Contacts tool before calling the email API."

The extraction prompt forces specificity. For failures: "Pinpoint the breakpoint" and "Derive a correction rule." For successes: identify the "Winning move" and derive best practices with specific tool usage guidance. Vague feedback like "be more careful" is explicitly forbidden.

### How This Differs from Plain Memory/RAG

This is the critical distinction:

| Aspect | Plain memory/RAG | ERL heuristics |
|--------|-----------------|----------------|
| Storage | Raw experiences, conversations | Abstracted principles with triggers |
| Retrieval | Similarity matching | LLM-scored relevance (task decomposition + pattern matching) |
| Format | Unstructured text | Structured: trigger condition + action |
| Transferability | Low (examples are context-specific) | High (principles generalize) |
| Token efficiency | Poor (raw trajectories are long) | Good (heuristics are compact) |

The paper proves this quantitatively: heuristics provide +5.5% to +23.8% gains over raw trajectory prompting at equivalent token budgets. The abstraction step is what makes them transferable.

### Scoring and Retrieval

At test time:
1. LLM analyzes the new task, decomposing it into potential sub-tasks and action steps
2. Each stored heuristic is scored on three criteria: task similarity, diversity of experiences, informativeness of guideline content
3. Output: JSON with scenario IDs, rationale, and scores (0-100)
4. Top k=20 heuristics injected into system prompt

k=20 was empirically optimal. Performance degrades with excessive inclusion -- too many heuristics create noise.

### Key Results

| Benchmark | ERL | ExpeL | AutoGuide | Baseline |
|-----------|-----|-------|-----------|----------|
| Gaia2 overall | 56.1% | 50.9% | 50.8% | 48.3% |
| Gaia2 execution | 51.4% | -- | -- | 43.1% |
| Gaia2 search | 60.7% | -- | -- | 53.6% |

**Critical finding**: ERL improves primarily through reliability (pass^3, consistency across all 3 runs) rather than solving entirely new task classes (minimal pass@3 gains). The framework stabilizes performance on learnable tasks -- fewer random failures, more consistent execution.

### How ERL Differs from ExpeL

| Aspect | ExpeL | ERL |
|--------|-------|-----|
| Trajectory requirement | Multiple rollouts per task (Reflexion with 3 retries) | Single attempt per task |
| Retrieval | All insights concatenated regardless of relevance | Selective top-k retrieval via scoring |
| Scalability | Degrades as experience grows (dumps everything in) | Scales via relevance filtering |
| Practical deployment | Requires task retry infrastructure | Works with real-world single-attempt data |

ERL's single-attempt advantage is critical for a product: real coding sessions cannot be "retried." You get one trajectory per task.

### Failure Heuristics vs. Success Heuristics

Task-type dependent:
- Failure heuristics outperform success-derived ones overall (+14.3% on Search tasks)
- Success heuristics work best on Execution tasks (+9.0%)
- Combined is most robust

### What a Product Built on ERL Would Look Like

The product would be an "experience compiler" that:
1. After each session, reflects on the trajectory to extract 1-3 heuristics
2. Scores and stores them in a growing heuristic pool
3. Before each new session, retrieves the most relevant heuristics and injects them into context
4. The agent gets progressively better at the specific project's patterns

**Key product mechanics:**
- Lightweight extraction: One LLM call per session to generate heuristics (cheap)
- Retrieval is the bottleneck: Scoring all heuristics against a new task requires one LLM call at session start
- Natural fit for Claude Code's SessionStart hook: inject top-k heuristics into the session context
- Heuristic pool needs curation: without pruning, pool grows unbounded. ERL does not solve this -- but the scoring mechanism naturally down-ranks stale or irrelevant heuristics

**The product insight that ERL reveals**: The difference between "memory" and "learning" is abstraction. Storing raw experiences is memory. Extracting principles with trigger conditions is learning. The trigger-action format is what makes heuristics reusable across dissimilar tasks. This is exactly what distinguishes a good engineer from a novice: the good engineer has internalized principles ("always validate inputs before API calls"), not memorized specific instances.

**Sources**: [ERL Paper](https://arxiv.org/abs/2603.24639), [ERL HTML](https://arxiv.org/html/2603.24639)

---

## 16. SkillWeaver: Web Agent Skill Discovery and API Synthesis

**Paper**: [arXiv:2504.07079](https://arxiv.org/abs/2504.07079) | **Authors**: Zheng, Fatemi, Jin, Wang, Gandhi, Song, Gu, Srinivasa, Liu, Neubig, Su | **Published**: April 2025

### What It Does

SkillWeaver enables web agents to self-improve by autonomously discovering skills on websites, practicing them, and distilling practice experiences into robust APIs. The APIs are transferable -- skills from stronger agents improve weaker agents by up to 54.3%.

### The Four-Phase Pipeline

1. **Skill Proposal**: LLM identifies novel procedural, navigational, and information-seeking skills for a given website
2. **Skill Practice**: Agent executes proposed skills on real websites, generating practice trajectories
3. **Skill Honing**: Auto-generated test cases validate and debug the synthesized APIs
4. **Skill Library**: Iteratively expands a library of lightweight, plug-and-play APIs

### Key Results

- WebArena: +31.8% relative improvement
- Real-world websites: +39.8% relative improvement
- Cross-agent transfer: +54.3% (strong agent's APIs used by weak agent)

### Product Relevance

SkillWeaver's most important insight for Acumen: **skills as APIs are the right abstraction for transfer**. Not prompts, not raw examples, not heuristics -- executable APIs that encapsulate procedural knowledge. The practice/honing cycle (generate skill, test it, debug it, validate it) produces more robust skills than one-shot extraction.

**Sources**: [SkillWeaver Paper](https://arxiv.org/abs/2504.07079), [GitHub](https://github.com/OSU-NLP-Group/SkillWeaver)

---

## 17. Voyager Skill Library Pattern (Foundational Reference)

**Paper**: [arXiv:2305.16291](https://arxiv.org/abs/2305.16291) | **Authors**: Wang, Xie et al. | **Published**: May 2023

### Why It Still Matters

Nearly every modern skill-extraction system cites Voyager. The three-component architecture has become the template:
1. **Automatic curriculum** (propose increasingly complex tasks)
2. **Skill library** (ever-growing library of executable code, indexed by description embeddings)
3. **Iterative prompting** (environment feedback + execution errors + self-verification)

### Key Design Decisions

- Skills are indexed by description embedding, retrieved via similarity search
- Complex skills compose simpler ones -- compounding capabilities over time
- The skill library prevents catastrophic forgetting (old skills remain available)
- 3.3x more unique items, 2.3x longer distances, 15.3x faster tech tree milestones vs. prior SOTA

### Product Lesson

The Voyager pattern shows that a skill library with composition and retrieval is strictly better than a flat list of rules. Acumen's current .claude/rules/ approach is flat -- each rule is independent. The Voyager pattern suggests Acumen should eventually support skill composition (skill A can call skill B) and embedding-based retrieval (find the most relevant skill for the current task).

**Sources**: [Voyager Paper](https://arxiv.org/abs/2305.16291), [Project Page](https://voyager.minedojo.org/)

---

## 18. Products That Auto-Generate Claude Code Skills or Cursor Rules

**Date**: 2026-03-30

### Current State of the Art

No product exists that automatically generates Claude Code skills from observation of real sessions. The closest approaches:

**1. Learnings.md pattern (MindStudio blog)**: A markdown file in the project that Claude reads before starting any task and appends to after finishing. Accumulates structured observations over time. This is passive memory, not skill extraction -- it stores what happened, not abstracted principles.

**2. Firecrawl Skills Generator**: Generates SKILL.md files from documentation URLs using their Agent endpoint. This is documentation-to-skill, not observation-to-skill. Different input modality entirely.

**3. Cursor's /Generate Cursor Rules**: Built-in command that generates rules from the current conversation context. Session-scoped, not cross-session. No automated observation.

**4. cursor-doctor**: Validates and auto-generates Cursor rules from the tech stack (`npx cursor-doctor --generate`). Stack analysis, not behavioral observation.

**5. Self-Improving CLAUDE.md (Martin Alderson approach)**: Agent searches through existing chat logs and references current CLAUDE.md to spot optimization opportunities. Closest to observation-based improvement, but requires the agent to read its own logs (content access, not metadata-only) and is manual/prompt-driven.

**6. self-improving-agent skill (alirezarezvani)**: Turns auto-memory into a structured self-improvement loop. Promotes patterns to rules, extracts solutions into skills. But relies on Claude's built-in auto-memory as input -- no automated observation hooks.

### The Gap

Every existing approach either:
- Reads conversation content (privacy concern)
- Requires manual triggering (not automated)
- Produces rules, not transferable skills (flat vs. compositional)
- Works within a single session (no cross-session learning)

**No product closes the full loop**: automated privacy-safe observation -> heuristic/skill extraction -> cross-session application -> verification of improvement. This is Acumen's opportunity.

---

## 19. Synthesized Product Vision: The Self-Improving Agent Stack

### The Convergence

Five research threads are converging on the same product:

| Research | What it provides | Product analog |
|----------|-----------------|----------------|
| Trace2Skill | Skill extraction from traces via parallel analysis | Automated skill compiler |
| ERL | Heuristic extraction from single-attempt trajectories | Experience-to-principle converter |
| AZR | Verifiable rewards via code execution | Automated evaluation of improvements |
| DGM | Safety lessons from self-improving systems | Privacy-safe observation constraints |
| SkillWeaver/Voyager | Skill-as-API pattern with composition and retrieval | Skill library architecture |

### Product Concept 1: "The Skill Compiler"

**What it is**: A system that automatically compiles execution traces into Claude Code SKILL.md files.

**How it works**:
1. **Observe** (Acumen's existing pipeline): Capture metadata from every tool call -- tool_name, outcome, error_type, session_id, timestamp, file paths touched
2. **Classify** (Acumen's existing classifier): Categorize observations by domain (testing, deployment, debugging, etc.)
3. **Extract** (ERL-inspired): After each session, reflect on the metadata trajectory to extract 1-3 heuristics with trigger-action format. Cost: one LLM call per session.
4. **Consolidate** (Trace2Skill-inspired): Periodically (weekly), dispatch parallel sub-agents against all heuristics in a domain. Merge via inductive reasoning into a unified SKILL.md per domain. Cost: one batch job per week.
5. **Validate** (AZR-inspired): Test each generated skill by measuring whether sessions using the skill have better outcomes than sessions without it. Verifiable reward: did error rates decrease? Did test pass rates increase?
6. **Apply** (Acumen's existing safe-tier mechanism): Skills auto-load via Claude Code's skill system. User reviews via /acumen-status.

**Architecture**:
```
Session traces (metadata-only)
    |
    v
[ERL-style per-session heuristic extraction]
    |
    v
Heuristic pool (.acumen/heuristics/*.jsonl)
    |
    v
[Trace2Skill-style periodic consolidation]
    |
    v
SKILL.md files (.claude/skills/acumen-*.md)
    |
    v
[AZR-style outcome verification]
    |
    v
Skill effectiveness scores -> retirement or promotion
```

**What makes it a product, not a research tool**:
- Zero configuration: install the plugin, work normally
- Privacy-safe: metadata-only observation, no content capture
- Low cost: ERL extraction is one cheap LLM call per session; Trace2Skill consolidation is a weekly batch
- Verifiable: outcome metrics prove skills are actually helping
- Reversible: every skill has before/after state, can be rolled back

### Product Concept 2: "The Heuristic Injector"

**What it is**: A lighter-weight product that skips skill compilation and directly injects relevant heuristics into each session.

**How it works**:
1. After each session, extract heuristics (ERL-style)
2. At session start, score all stored heuristics against the current project context
3. Inject top-k (k=20) into the session via SessionStart hook
4. The agent receives project-specific guidance without the overhead of formal skill files

**Why this might be the right v1**: It is dramatically simpler than the full skill compiler. No parallel sub-agents, no hierarchical consolidation, no skill file management. Just extract and inject. The ERL paper shows this alone provides 7.8% improvement on complex tasks.

**The tradeoff**: Heuristics are less structured than skills. They do not compose, they do not have executable code components, they do not have references/ directories. But they are fast to generate, cheap to store, and the scoring mechanism handles relevance naturally.

### Product Concept 3: "The Cross-Project Skill Library"

**What it is**: A global skill library where skills extracted from one project transfer to others.

**How it works**:
1. Skills extracted at project scope get tagged with domain metadata
2. When a user starts a new project, the system retrieves globally-relevant skills
3. Skills that work across projects get promoted to global scope
4. Skills that are project-specific stay scoped

**Why this matters**: Trace2Skill's headline result is cross-model transfer. The product analog is cross-project transfer. A developer who learns testing patterns in Project A should benefit when they start Project B. Voyager's skill library pattern proves this works -- skills compose and compound across contexts.

**Privacy constraint**: Cross-project transfer must respect project boundaries. A heuristic extracted from a private project cannot leak information to another project. Metadata-only observation makes this safe by design -- heuristics derived from (tool_name, outcome, error_type) contain no project-specific code or content.

### Product Concept 4: "The Verified Improvement Loop"

**What it is**: A system where every improvement is empirically validated before permanent application.

**How it works** (AZR-inspired):
1. Generate a candidate improvement (rule, heuristic, or skill)
2. Apply it to a subset of sessions (A/B test)
3. Measure outcome metrics: error rate, test pass rate, tool failure frequency
4. If the improvement reduces errors with statistical significance, promote it
5. If it has no effect or increases errors, retire it
6. All decisions are logged and reversible

**Why this matters**: The DGM's lesson is that self-improving systems will try to hack their evaluation. AZR's lesson is that code execution provides verifiable ground truth. For a coding agent, the verifiable signals are: did tests pass? Did the build succeed? Did the user deny fewer tool calls? These are observable from metadata without reading content.

**Acumen already has the foundation**: The existing observation pipeline captures tool outcomes, the classifier categorizes them, and the scorer assigns effectiveness ratings. The missing piece is the A/B testing mechanism -- applying improvements to some sessions and measuring the delta.

### The Combined Vision

**Phase 1 (ship now with existing architecture)**: Heuristic Injector. ERL-style extraction from session metadata + injection via SessionStart hook. Minimal new code. Immediate user value.

**Phase 2 (after Phase 1 proves value)**: Skill Compiler. Trace2Skill-style periodic consolidation of heuristics into formal SKILL.md files. Requires a batch processing pipeline.

**Phase 3 (after skill compilation works)**: Verified Improvement Loop. AZR-style A/B testing of skills. Requires outcome tracking across sessions with and without specific skills.

**Phase 4 (after verification is reliable)**: Cross-Project Skill Library. Global scope with privacy-safe transfer.

### Why This Matters for Acumen Specifically

Acumen is uniquely positioned to build this product because:

1. **Observation pipeline exists** -- hooks/observe.sh already captures the metadata that feeds ERL-style extraction
2. **Classification exists** -- lib/classify.py already categorizes observations into domains
3. **Store exists** -- lib/store.py already persists observations with session grouping
4. **Safe-tier application exists** -- the existing rule application mechanism can be extended to heuristics/skills
5. **Privacy-safe design is load-bearing** -- every competitor reads content. Acumen's metadata-only constraint is a feature, not a limitation, because it enables cross-project transfer without information leakage
6. **Plugin packaging is ready** -- SKILL.md files dropped into .claude/skills/ are automatically loaded by Claude Code

The research validates every architectural decision Acumen has already made. The frozen-core/evolving-periphery pattern, the metadata-only observation, the rule store, the session-scoped analysis -- all of these map directly onto the Trace2Skill/ERL/AZR findings.

### Key Open Questions

1. **Does metadata-only trajectory analysis produce useful heuristics?** ERL uses full trajectories. Can (tool_name, outcome, error_type, duration, paths_touched) provide enough signal for the reflection LLM to extract meaningful principles? This needs empirical testing.

2. **What is the minimum trajectory count for useful skill compilation?** Trace2Skill uses 128 parallel trajectories. How many sessions does a typical developer accumulate in a week? Is the signal sufficient?

3. **How do you measure "this skill helped" without controlled experiments?** In production, there is no control group. Options: before/after comparison (noisy), user feedback (sparse), tool failure rate trends (indirect but available from metadata).

4. **Cost model**: ERL extraction is cheap (~1 LLM call per session). Trace2Skill consolidation is expensive (128 parallel sub-agents). What is the right batch cadence and model size for a developer tool?

**Sources**: All papers cited in sections 14-17 above, plus [Addy Osmani on Self-Improving Agents](https://addyosmani.com/blog/self-improving-agents/), [Yohei Nakajima on Self-Improving Agents](https://yoheinakajima.com/better-ways-to-build-self-improving-ai-agents/), [SICA Paper](https://arxiv.org/abs/2504.15228)

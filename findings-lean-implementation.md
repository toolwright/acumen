# Lean AI-Assisted Implementation: Research Findings

**Date**: 2026-03-29
**Scope**: Techniques, frameworks, and practices for implementing software with AI coding agents without producing bloated, overengineered, or sloppy code. Covers 2025-2026 research and practitioner knowledge.

---

## 1. Implementation Strategies That Prevent Bloat

### 1.1 Prompt Structure for Implementation

The consensus across practitioners (Addy Osmani, Nathan Onn, Simon Willison, Anthropic's official docs) is:

**Declarative over imperative.** Define success criteria and constraints, not step-by-step instructions. Spend 70% of effort on problem definition, 30% on execution. The TDAD paper independently confirmed this: "surfacing the right information (which tests are at risk) matters more than prescribing workflow."

**The "Surgical Coding" technique** (Nathan Onn): After Claude produces its initial overengineered plan, reject it and paste:
> "Think harder and thoroughly examine similar areas of the codebase to ensure your proposed approach fits seamlessly with the established patterns and architecture. Aim to make only minimal and necessary changes, avoiding any disruption to the existing design. Whenever possible, take advantage of components, utilities, or logic that have already been implemented."

This triggers extended thinking (31,999 tokens vs. 4,000 default) and forces actual codebase examination before proposing solutions.

**Variation prompts that work:**
- **Pattern Detective**: "Find 3 similar existing patterns, align new solution with most appropriate"
- **Deletion First**: "Check if removing/simplifying existing code solves the problem"
- **One-File Challenge**: "Attempt solution in single file modification only"
- **Framework Native**: "Prioritize framework built-ins before custom implementations"

**Demonstrated impact**: Email OTP feature went from 15 files / 1000+ lines / multiple abstract patterns down to 3 files / ~120 lines / zero patterns.

### 1.2 Optimal Chunk Size

**One function, one bug, one feature at a time.** LLMs do best with focused prompts. Each chunk should be small enough for the AI to handle within context. The practical guideline is 5-15 minute steps that mirror human work chunking.

**Batch sizing for file changes**: 5-20 files per batch. A good batch is a logical subset that compiles and tests independently.

**Commit cadence**: Commit after each task completion. Addy Osmani treats commits as "save points in a game," enabling rapid rollback if the LLM introduces unnecessary complexity.

### 1.3 Preventing Scope Creep

**Root cause**: Vague or missing constraints. Agents add caching infrastructure, logging refactors, or other features outside the task boundary.

**Solutions**:
- Spec-driven task decomposition with explicit file and interface boundaries per task
- "All work done for a task must strictly adhere to that task's defined scope; no changes outside this scope permitted"
- Write tests first to create objective boundaries preventing unconstrained implementation
- Use `Esc` to stop Claude mid-action the moment you notice it going off track

### 1.4 Step-by-Step vs. Monolithic

**Step-by-step wins decisively.** The Advanced Context Engineering guide (HumanLayer) establishes a three-phase workflow:
1. **Research**: Map the codebase, identify relevant files, understand information flow (fresh context)
2. **Plan**: Create precise step-by-step implementation instructions with explicit testing verification (fresh context)
3. **Implement**: Execute the plan phase-by-phase, recompacting status after each verified phase (fresh context)

Each phase uses a fresh context window, preventing cascading errors. The key insight: "A bad line of code is a bad line of code. But a bad line of a plan could lead to hundreds of bad lines of code."

**Human leverage points**: Humans should focus on validating research and plans, not individual code lines. One expert review of the research phase prevents thousands of bad lines downstream.

---

## 2. Claude Code Specific Best Practices (2025-2026)

### 2.1 Power User Consensus

**CLAUDE.md is essential infrastructure.** The community consensus in 2026 is that CLAUDE.md is as important as .gitignore. But it must be concise -- the sweet spot is 100-200 lines maximum. Bloated CLAUDE.md files cause Claude to ignore actual instructions.

**Rules for CLAUDE.md content:**
- Include: bash commands Claude can't guess, style rules that differ from defaults, testing instructions, architectural decisions, common gotchas
- Exclude: anything Claude can figure out by reading code, standard language conventions, detailed API docs, self-evident practices like "write clean code"
- Emphasis markers (IMPORTANT, YOU MUST) improve adherence
- For each line, ask: "Would removing this cause Claude to make mistakes?" If not, cut it

### 2.2 Plan Mode, Subagents, /clear

**Plan Mode** (Shift+Tab+Tab): Read-only exploration that halves token consumption. Use at the start of any complex multi-file task. The Explore Subagent (Haiku-powered) searches your codebase while saving context tokens.

**/clear**: Reset context between unrelated tasks. If you've corrected Claude more than twice on the same issue, the context is cluttered with failed approaches. A clean session with a better prompt almost always outperforms a long session with accumulated corrections.

**Subagents** for context control: Use subagents specifically for "finding/searching/summarizing that enables the parent agent to get straight to work without clouding its context window with Glob/Grep/Read calls." Up to 10 simultaneous subagents supported (2026).

**Context budget**: At 70% context, Claude starts losing precision. At 85%, hallucinations increase. At 90%+, responses become erratic. Target 40-60% context utilization through frequent intentional compaction.

**Context editing** (2026 feature): Automatically clears stale tool call outputs while preserving conversation flow, cutting token consumption by 84% in a 100-turn evaluation.

### 2.3 Preventing Unnecessary Abstractions

**Claude defaults to enterprise-grade patterns from training data** rather than examining your existing setup. It pattern-matches to production-ready architectures, creates unnecessary strategy patterns/factories/base classes, proposes entirely new systems when existing infrastructure exists, and builds extensibility for scenarios that may never occur.

**Effective countermeasures:**
- Add "use the simplest possible approach" to CLAUDE.md
- Organize codebase by problem domains, not technical layers
- Use the "surgical coding" prompt to force codebase examination
- Push back: "Couldn't you just...?" -- agents readily simplify when redirected
- Fresh-context code review: same model reviews its own code with a clean context window

### 2.4 Keeping File Counts Low

- **Consolidation approach**: Ask "What if this could be done in just one file?" then see how close you can get
- **Writer/Reviewer pattern**: Have one Claude session write code, another review it with fresh context
- **Hooks over CLAUDE.md for enforcement**: Unlike advisory CLAUDE.md instructions, hooks are deterministic and guarantee actions happen (e.g., "Write a hook that blocks writes to the migrations folder")

---

## 3. Spec-Driven Development (SDD)

### 3.1 GitHub's Spec-Kit

**Released 2025, 72,000+ GitHub stars.** Three steering commands: `/specify` (generate specification), `/plan` (produce technical plan), `/tasks` (derive actionable task list).

**Constitutional principles that prevent bloat:**
- **Library-First Principle**: Features must exist as reusable libraries before integration
- **Simplicity Gate**: Limited to 3 or fewer projects; additional complexity requires documented justification
- **Anti-Abstraction**: Use frameworks directly; no speculative wrapper layers
- **Test-First Imperative**: No implementation code before unit tests

**Forced clarification**: `[NEEDS CLARIFICATION]` markers prevent assumed requirements. Structured checklists create self-review gates before proceeding.

### 3.2 Martin Fowler's Analysis

**Mixed verdict.** Fowler's August 2025 experiments revealed:
- Agents frequently ignored instructions despite detailed specifications
- False sense of control -- elaborate workflows didn't prevent hallucinations
- Generated features not requested, changed assumptions mid-stream, claimed success when builds failed
- SDD tools created excessive documentation that took longer to review than direct implementation
- For simple changes, specification overhead outweighed benefits

Fowler invokes "Verschlimmbesserung" (worsening through attempted improvement) -- reviewing markdown over reviewing code creates cognitive overhead without clear benefits.

**Fundamental concern**: No clear mechanism exists within SDD to prevent specification bloat itself. SDD may inherit Model-Driven Development's failures (inflexibility + LLM non-determinism).

### 3.3 When SDD Works vs. Doesn't

**Works for**: Complex multi-file features where the scope is genuinely uncertain, team coordination where multiple agents work on related tasks, projects where the spec survives beyond initial implementation.

**Doesn't work for**: Simple changes where "you could describe the diff in one sentence," bug fixes, single-file modifications. Anthropic's own docs say: "If you could describe the diff in one sentence, skip the plan."

---

## 4. TDAD and Test-Aware Implementation

### 4.1 The TDAD Paper (March 2026, arxiv:2603.17973)

**Core finding**: Agents do not need to be told *how* to do TDD; they need to be told *which tests to check*.

**How it works:**
1. AST Parser extracts functions, classes, imports, and call targets from Python files
2. Graph Builder creates nodes for files/functions/classes and edges capturing structural relationships
3. Test Linker connects test functions to source code using naming conventions and proximity heuristics
4. Four parallel impact strategies (direct, transitive, coverage-based, import-based) with weighted confidence scores
5. Tests ranked by likelihood of impact, exported as a static `test_map.txt` file

**Results**: 70% regression reduction (test failures dropped from 562 to 155 across 100 instances). Test-level regression rate decreased from 6.08% to 1.82%.

**Critical finding -- the TDD Prompting Paradox**: Verbose procedural TDD instructions alone *increased* regressions to 9.94% with smaller models. Context quality (factual test mappings) matters more than prescriptive instructions.

**Integration**: Zero dependencies beyond NetworkX. `pip install tdad`, index your repo once, provide agents a 20-line skill definition and the static test map. Agents grep the map to identify affected tests before generating patches.

### 4.2 Simon Willison's Red/Green TDD Pattern

**Key insight**: Test-first development is "a fantastic fit for coding agents" because it prevents both non-functional code AND unnecessary features.

**Practical guidance**: Use the shorthand prompt "Use red/green TDD" -- every good model understands this as shorthand. The red phase (confirming tests fail before writing code) is critical to avoid building tests that already pass.

### 4.3 Measuring Regression Severity

The TDAD paper recommends tracking regression *severity*, not just whether regressions occurred. A patch breaking 322 tests differs fundamentally from one breaking 1 test. Teams should track:
- Resolution rate (patches passing fix tests)
- Test-level regression rate (failures among previously-passing tests)
- Generation rate (non-empty patch output)

---

## 5. Anti-Patterns During Implementation

### 5.1 How Projects Bloat from 10 to 100 Files

**Abstraction Bloat**: Agents scaffold 1,000 lines where 100 would suffice, creating elaborate class hierarchies where a function would do. They optimize for appearing comprehensive rather than maintainable.

**Assumption Propagation**: Models misunderstand early requirements and build entire features on faulty premises, embedding mistakes five commits deep before discovery.

**Dead Code Accumulation**: Agents fail to clean up after themselves, leaving old implementations, stray comments, and variant files (`component.tsx`, `component_backup.tsx`, `component_fixed.tsx`).

**Greenfield Thinking**: Proposing entirely new systems (like complete auth frameworks) when existing infrastructure exists.

**Future-Proofing Obsession**: Building extensibility for scenarios that may never occur.

### 5.2 The "Just One More Abstraction" Trap

AI agents generate defensively: adding unused imports, creating abstractions for things with only one implementation, building configuration systems for values that never change. The root cause is training data bias -- agents pattern-match to enterprise examples rather than examining your specific context.

**Measured impact** (Christopher Montes, 2026): AI-authored PRs contain 10.83 issues per PR compared to 6.45 for human-only PRs. Security vulnerabilities appear at 2.74x the rate. Performance I/O regressions are 8x more common.

### 5.3 When DRY Becomes Harmful

**Empirical finding** (arxiv:2511.04824): Agentic refactoring emphasizes low-level edits more than humans while performing fewer high-level structural changes (43.0% vs. 54.9% signatures refactoring). Agents often generate new code instead of reusing or refactoring existing code, leading to code bloat and technical debt.

**Agentic refactoring leads to statistically significant but practically negligible reductions** in overall design and implementation smell counts. High-level refactorings (extracting classes, restructuring inheritance) require domain knowledge and strategic intent that current agents lack.

**Bottom line**: Reserve architectural refactoring decisions for human engineers. Use AI agents primarily for low-level consistency tasks.

### 5.4 Specific Lintable Anti-Patterns (Montes, 2026)

Ten categories with detection rules:
1. **Duplication** -- regenerating existing code (Ruff TID251)
2. **Abstraction Bypass** -- using raw libraries instead of project abstractions (TID251 banned-api)
3. **Error Handling** -- bare except clauses, catch-all handlers (BLE001, TRY003, E722)
4. **Type Safety** -- excessive `any` types (Pyright strict, @typescript-eslint/no-explicit-any)
5. **Security** -- SQL interpolation, hardcoded secrets (S105-S107, Semgrep OWASP)
6. **Dead Code** -- unused imports, speculative features (F401, F841, ERA001, ARG001-005)
7. **Debugging Residue** -- variant files from iterative development
8. **Async Misuse** -- blocking calls in async functions (ASYNC100-102)
9. **Deprecated APIs** -- outdated patterns from training data (Ruff UP rules)
10. **Test Anti-Patterns** -- high coverage masking insufficient assertion depth (PT011, PT012, PT018)

**Prevention strategy**: Pre-commit hooks with pattern matching. Results after two months: 100% prevention rate with zero false positives and execution under 2 seconds.

---

## 6. Practical Implementation Workflows That Work

### 6.1 Anthropic's Official Recommended Workflow

Four phases:
1. **Explore** (Plan Mode): Read files and answer questions without making changes
2. **Plan** (Plan Mode): Create detailed implementation plan, press Ctrl+G to edit in text editor
3. **Implement** (Normal Mode): Code against the plan, writing tests and verifying
4. **Commit**: Descriptive message and PR

### 6.2 Addy Osmani's "Waterfall in 15 Minutes"

Create a comprehensive spec.md first containing requirements, architecture decisions, and data models. This is rapid structured planning that prevents architectural drift. Then implement iteratively -- one function, one bug, one feature at a time.

**Key risk he identifies**: "Comprehension Debt" -- when an agent generates code faster than you can read and understand it, you are borrowing against your future ability to maintain that system.

### 6.3 Advanced Context Engineering (HumanLayer)

**The three-file pattern**: progress.md, findings.md, task_plan.md. Deliberately pause work to "write everything we did so far to progress.md, ensure to note the end goal, the approach we're taking, the steps we've done so far, and the current failure we're working on."

**Context priority hierarchy:**
1. Incorrect information (worst)
2. Missing information
3. Excessive noise (least damaging)

**Sub-agents for context isolation**: Use subagents for finding/searching/summarizing. This isolates exploration work from implementation work, keeping the parent agent's context clean for actual coding.

### 6.4 The Writer/Reviewer Pattern

Use separate Claude sessions:
- Session A (Writer): Implements the feature
- Session B (Reviewer): Reviews with fresh context, looking for edge cases, race conditions, consistency with existing patterns
- Session A: Addresses review feedback

This works because Claude won't be biased toward code it just wrote when reviewing in a fresh context.

### 6.5 Simon Willison's Agentic Engineering Patterns

Core principles:
- **"Writing code is cheap now"**: Rethink resource allocation. The constraint is now human attention and review capacity, not code generation speed.
- **"Hoard things you know how to do"**: Preserve expertise in areas where human judgment matters. Codify working patterns into reusable prompts and skills.
- **"AI should help us produce better code"**: Position agents as quality enhancers, not just labor savers.

### 6.6 Code Review During Implementation

**GitClear's 2025 findings** (211M lines analyzed): Copy/pasted code rose from 8.3% to 12.3%. Refactoring dropped from 25% to under 10%. These are structural quality problems that only code review catches.

**Qodo's 2025 findings** (609 developers): 65% say AI misses context during refactoring. Among developers perceiving quality degradation, 44% blame missing context. Teams using AI for code review show 81% quality gains vs. 55% without.

**Cognitive complexity**: Increases 39% in agent-assisted repositories. Initial velocity gains disappear within months.

---

## 7. Recent Research Papers (2025-2026)

### 7.1 Code Complexity in AI-Generated Code

**Human vs. AI comparison** (arxiv:2508.21634): Human-written Python functions average 12.72 lines with cyclomatic complexity 3.97. AI-generated code is shorter and simpler (6.89/2.47 for ChatGPT, 5.16/2.00 for DSC, 4.47/1.84 for Qwen). However, this simplicity is per-function -- the total code volume is much higher because agents generate more functions.

### 7.2 Measuring Overengineering

**GitClear's AI Copilot Code Quality Research (2025)**: First time in history that cloned code exceeded moved code. The percentage of changed code associated with refactoring sank from 25% (2021) to under 10% (2024). This suggests agents create rather than consolidate.

**OX Security study**: "Comments Everywhere" anti-pattern found in 90-100% of AI-generated repositories. Over-specification found in 80-90%.

**ACM study on Copilot**: 29.5% of Python snippets and 24.2% of JavaScript snippets contained security weaknesses. Claude can generate 1.75x more logic errors than human-written code.

### 7.3 Agentic Refactoring Study (arxiv:2511.04824)

Agents perform more low-level edits than humans but fewer high-level structural changes. Agentic refactoring achieves only negligible reductions in design smell counts. The paper recommends reserving architectural decisions for humans.

### 7.4 TDAD: Graph-Based Impact Analysis (arxiv:2603.17973)

See Section 4.1. Key contribution: zero-dependency tool for graph-based test impact analysis. 70% regression reduction. The TDD Prompting Paradox finding is particularly significant -- showing that context quality trumps procedural instructions.

### 7.5 Code Review Agent Benchmark (arxiv:2603.23448)

Establishes benchmarks for AI code review quality. Key metrics: Comment Quality, Summary Quality, Accuracy, Noise, Speed. Finding: human review comments used as references can themselves be noisy or incomplete, complicating evaluation.

### 7.6 Spec-Driven Development Paper (arxiv:2602.00180)

Academic treatment of SDD concepts. Positions specifications as contracts rather than documentation, inverting the traditional relationship where code is primary.

---

## 8. Synthesis: What Actually Works

### The Core Pattern

1. **Research with subagents** (isolated context) -- understand the codebase before touching it
2. **Plan with human review** -- this is the highest-leverage human intervention point
3. **Implement in small chunks** -- one function, one test, one feature. Commit after each.
4. **Verify with tests** -- red/green TDD, using test impact analysis (TDAD) to know which tests matter
5. **Review with fresh context** -- writer/reviewer pattern catches what accumulated context misses
6. **Enforce with automation** -- pre-commit hooks, linters, type checkers as hard guardrails

### The Anti-Pattern

1. Give Claude a big vague task
2. Let it explore for 20 minutes filling context
3. Accept its overengineered plan
4. Let it generate 15 files of abstractions
5. Try to fix problems by correcting in the same cluttered session
6. Ship without fresh-context review

### Key Numbers to Remember

- **70%**: Context threshold where precision drops
- **70%**: Regression reduction with TDAD
- **39%**: Cognitive complexity increase in agent-assisted repos
- **10.83 vs 6.45**: Issues per PR (AI vs. human)
- **2.74x**: Security vulnerability rate in AI code
- **100-200 lines**: CLAUDE.md sweet spot
- **5-20 files**: Optimal batch size
- **84%**: Token reduction from context editing

---

## Sources

- [Addy Osmani - The 80% Problem in Agentic Coding](https://addyo.substack.com/p/the-80-problem-in-agentic-coding)
- [Addy Osmani - My LLM coding workflow going into 2026](https://medium.com/@addyosmani/my-llm-coding-workflow-going-into-2026-52fe1681325e)
- [Addy Osmani - The Factory Model](https://addyosmani.com/blog/factory-model/)
- [Nathan Onn - How To Stop Claude Code From Overengineering Everything](https://www.nathanonn.com/how-to-stop-claude-code-from-overengineering-everything/)
- [Simon Willison - Agentic Engineering Patterns](https://simonwillison.net/guides/agentic-engineering-patterns/)
- [Simon Willison - Red/Green TDD](https://simonwillison.net/guides/agentic-engineering-patterns/red-green-tdd/)
- [Anthropic - Best Practices for Claude Code](https://code.claude.com/docs/en/best-practices)
- [Anthropic - Eight trends defining how software gets built in 2026](https://claude.com/blog/eight-trends-defining-how-software-gets-built-in-2026)
- [GitHub - Spec-Driven Development with Spec-Kit](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/)
- [GitHub - spec-driven.md](https://github.com/github/spec-kit/blob/main/spec-driven.md)
- [Martin Fowler - Understanding SDD: Kiro, spec-kit, and Tessl](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)
- [TDAD Paper - arxiv:2603.17973](https://arxiv.org/abs/2603.17973)
- [TDAD Paper (Behavioral Specifications) - arxiv:2603.08806](https://arxiv.org/abs/2603.08806)
- [Christopher Montes - Lint Against the Machine: AI Coding Agent Anti-Patterns](https://medium.com/@montes.makes/lint-against-the-machine-a-field-guide-to-catching-ai-coding-agent-anti-patterns-3c4ef7baeb9e)
- [HumanLayer - Advanced Context Engineering for Coding Agents](https://github.com/humanlayer/advanced-context-engineering-for-coding-agents/blob/main/ace-fca.md)
- [GitClear - AI Copilot Code Quality 2025 Research](https://www.gitclear.com/ai_assistant_code_quality_2025_research)
- [Qodo - State of AI Code Quality 2025](https://www.qodo.ai/reports/state-of-ai-code-quality/)
- [Agentic Refactoring Study - arxiv:2511.04824](https://arxiv.org/abs/2511.04824)
- [Spec-Driven Development Paper - arxiv:2602.00180](https://arxiv.org/html/2602.00180v1)
- [Code Review Agent Benchmark - arxiv:2603.23448](https://arxiv.org/html/2603.23448)
- [Human-Written vs AI-Generated Code - arxiv:2508.21634](https://arxiv.org/pdf/2508.21634)

# Market Landscape: AI Agent Improvement, Self-Improving Agents, and Project Intelligence

**Date**: 2026-03-30
**Scope**: Comprehensive survey of shipping products and open-source projects that compete with or are adjacent to Acumen's value proposition.

---

## Executive Summary

The market for "making AI agents better over time" is fragmented across five distinct categories, none of which fully close the improvement loop that Acumen targets. The closest competitors are either (a) memory-only systems that store context but don't propose improvements, (b) skill engines that evolve reusable procedures but don't observe your specific agent sessions, or (c) IDE-integrated learning that's locked to a single vendor. No shipping product today combines session observation, pattern extraction, evidence-cited improvement proposals, validation against verifiable signals, and local-only execution in a single system.

---

## 1. Products That Improve AI Coding Agents Over Time

### Sakana AI -- Darwin Godel Machine (DGM)
- **What it is**: A self-improving coding agent that rewrites its own source code using evolutionary search. Maintains a lineage of agent variants, selects improvements that pass empirical validation on benchmarks.
- **Results**: SWE-bench 20.0% to 50.0%; Polyglot 14.2% to 30.7%. Improvements generalize across foundation models.
- **Gap**: This improves a *benchmark agent*, not *your* agent in *your* codebase. It's a research system, not a product. No session observation, no project-specific learning. Open source (github.com/jennyzzt/dgm).

### Meta -- Hyperagents (DGM-H)
- **What it is**: Extension of DGM that adds metacognitive self-modification -- agents can edit their own improvement procedures, not just task-solving code. Domain-agnostic (coding, robotics, math, paper review).
- **Released**: March 2026, open source (CC non-commercial).
- **Gap**: Research framework, not a product. Requires benchmark loops to improve. No project context, no session observation, no user-facing improvement proposals.

### OpenSpace (HKUDS)
- **What it is**: A self-evolving skill engine. Intercepts task executions via hooks, logs inputs/outputs to local SQLite, mines patterns, and evolves reusable SKILL.md files. Three evolution modes: FIX (repair broken skills), DERIVED (create variants), CAPTURED (extract new skills from successful runs).
- **Results**: 4.2x income improvement, 46% token reduction on 50 professional tasks.
- **Integration**: Works with any agent that reads SKILL.md (Claude Code, Codex, Cursor). Community sharing at open-space.cloud.
- **Gap**: Focuses on skill evolution (reusable procedures), not project-specific insights. No evidence-cited improvement proposals. No rule retirement or drift detection. Closest competitor to Acumen's EXPAND phase, but does not cover OBSERVE or LEARN.

### Termo.ai -- Self-Improving Agent Skill
- **What it is**: A skill (224k downloads, 2.1k stars) that captures learnings, errors, and corrections to markdown files. Learnings can be promoted to project memory or extracted as reusable skills.
- **Gap**: Passive logging to markdown. No automatic pattern extraction, no evidence-cited proposals, no validation loop. Manual curation required. It's a notepad, not a compiler.

### Codex CLI -- Skills + Auto-Deepening
- **What it is**: OpenAI's Codex CLI supports agent skills (SKILL.md format, same as Anthropic's spec). Claims an "auto-deepening" feature that periodically analyzes work history and improves skills automatically. Writes improvements back to ~/.codex/skills/ as git-tracked files.
- **Gap**: Auto-deepening details are sparse in public docs -- unclear how much is shipping vs. announced. Improvement is skill-level (reusable procedures), not project-rule-level. No observation of tool outcomes, no evidence-cited proposals, no validation against success/failure signals.

---

## 2. Agent Memory Products (Mem0, Zep, Letta)

### Mem0
- **What it is**: Dedicated memory layer that extracts "memories" from interactions, stores in a hybrid vector-graph architecture, retrieves for personalization. User-level, session-level, and agent-level scopes. Graph capabilities on $249/mo Pro tier.
- **Does it close the improvement loop?** No. Mem0 stores and retrieves context. It does not propose improvements, validate changes, or modify agent behavior. It's a memory *store*, not an improvement *engine*.

### Zep
- **What it is**: Episodic and temporal memory. Stores interactions as a temporal knowledge graph that tracks how facts change over time. Combines graph memory with vector search.
- **Does it close the improvement loop?** No. Same as Mem0 -- it's a retrieval system, not an improvement system. Better at temporal reasoning than Mem0, but still passive storage.

### Letta
- **What it is**: Agent runtime built around self-editing memory. Agents manage their own memory blocks using dedicated tools. REST API, development environment, stateful services.
- **Does it close the improvement loop?** Partially. Letta agents can edit their own memory, which is closer to self-improvement. But the agent decides what to remember in-context -- there's no offline reflection, no pattern extraction from multiple sessions, no evidence-cited improvement proposals. It's memory self-management, not behavioral self-improvement.

### Verdict on Memory Products
All three are infrastructure for *storing* agent context. None of them observe agent sessions, extract behavioral patterns, propose evidence-cited improvements, or validate those improvements. They solve the "agent forgets" problem, not the "agent doesn't learn" problem.

---

## 3. "Codebase Intelligence" / "Project Intelligence" Products

### Sourcegraph Cody
- **What it is**: Code intelligence platform with semantic search, cross-repository understanding, RAG-based context with up to 1M token windows. Uses SCIP code graph + embeddings.
- **Gap**: Understands your codebase statically. Does not observe agent sessions, learn from outcomes, or propose improvements. It's a search/comprehension tool.

### Augment Code
- **What it is**: Builds a real-time knowledge graph of your codebase, maps dependency paths across services. Scored +12.8 on 500 agent-generated PRs against Elasticsearch (competitors at -13.9 and -11.8).
- **Gap**: Impressive codebase comprehension, but it's about understanding code, not improving agent behavior. No session observation, no learning loop.

### GitHub Copilot (Repository Intelligence)
- **What it is**: GitHub's chief product officer called repository intelligence "the defining AI trend of the year." Copilot analyzes entire repository structure, commit history, file relationships, team patterns.
- **Gap**: Makes suggestions more context-aware, but does not observe agent sessions, extract patterns, or propose behavioral improvements. It's awareness, not learning.

### Verdict on Codebase Intelligence
"Repository intelligence" is about giving agents better context at suggestion time. None of these products observe what the agent *does* and learn from outcomes. They're read-only comprehension, not read-write improvement.

---

## 4. Claude Code Plugins in This Space

### Claude-Mem (thedotmack)
- **What it is**: 21.5k GitHub stars. Automatically captures everything Claude does during sessions, compresses with AI (agent-sdk), stores in local SQLite, injects relevant context into future sessions via progressive disclosure.
- **Architecture**: Lifecycle hooks for capture, AI compression/summarization, SQLite with vector retrieval, hybrid search.
- **Gap**: Claude-Mem is memory, not improvement. It remembers what you did; it doesn't analyze what went wrong, propose changes, or validate improvements. No pattern extraction from tool outcomes. No evidence-cited rules.

### Memsearch Plugin (Zilliz/Milvus)
- **What it is**: Persistent memory plugin on top of memsearch CLI. Indexes conversations, decisions, style preferences. Fully searchable across sessions.
- **Gap**: Same as Claude-Mem -- memory retrieval, not behavioral improvement.

### Claude Supermemory
- **What it is**: Long-term memory plugin for Claude Code, focused on cross-session context persistence.
- **Gap**: Memory layer only.

### Claude Autoresearch Skill
- **What it is**: Autonomous goal-directed iteration inspired by Karpathy. Modify, Verify, Keep/Discard, Repeat cycle.
- **Gap**: This is a workflow pattern (iterative experimentation), not a learning system. Each run is independent; there's no accumulation of insights across runs.

### Claude Code Auto Memory (built-in)
- **What it is**: Official Anthropic feature (v2.1.59+). Claude saves notes to MEMORY.md as it works -- build commands, debugging insights, architecture notes, code style. Auto Dream feature searches session transcripts for user corrections, recurring themes, important decisions. Deletes contradicted facts, merges overlapping entries.
- **Gap**: Closest to Acumen's territory. But: (a) stores plain text memories, not typed rules with evidence chains; (b) no structured observation of tool outcomes (success/failure/error patterns); (c) no confidence scoring or validation against verifiable signals; (d) no rule retirement for harmful rules; (e) no reflection subagent that proposes improvements; (f) improvements are notes, not actionable CLAUDE.md modifications. It remembers preferences, it doesn't *reason about* agent behavior.

### Julep Memory Store Plugin
- **What it is**: Development tracking and context management plugin. Captures session context, analyzes git commits, maintains team knowledge.
- **Gap**: Context management, not improvement proposals.

### Direct Competitors to Acumen
**None found.** No Claude Code plugin currently:
1. Observes tool-level session metadata (tool_name, outcome, error_type)
2. Runs offline reflection to extract behavioral patterns
3. Proposes evidence-cited improvements to CLAUDE.md
4. Validates improvements against success/failure signals
5. Retires harmful rules
6. Does all of this locally with zero cloud dependency

---

## 5. Agent Skill Libraries / Self-Improvement in Open Source

### SkillRL (aiming-lab)
- **What it is**: RL framework for LLM agents to learn reusable behavioral patterns. Distills successful trajectories into strategic patterns and failures into lessons. Hierarchical SkillBank with general and task-specific skills. Recursive skill evolution during RL training.
- **Gap**: Research framework, requires RL training. Not a runtime plugin, not project-specific.

### SAGE (Amazon Science)
- **What it is**: Skill Augmented GRPO for self-Evolution. RL framework incorporating skills into learning. 8.9% higher goal completion, 26% fewer steps, 59% fewer tokens.
- **Gap**: Research, requires fine-tuning. Not a plug-and-play system.

### OpenClaw / ClawHub
- **What it is**: Public skills registry with 13,729+ community-built skills. Open standard adopted by Anthropic and OpenAI.
- **Gap**: Skill distribution platform, not a skill evolution platform. Skills are static files written by humans, not automatically generated from session observations.

### AI-Research-SKILLs (Orchestra Research)
- **What it is**: 87 skills across 22 categories for AI research agents. Works with Claude Code, Codex, Gemini.
- **Gap**: Curated skill library, not self-improving. Static content.

### Anthropic Skills Spec (Open Standard)
- **What it is**: Anthropic released agent skills as an open standard in Dec 2025. OpenAI adopted same format. SKILL.md files with frontmatter, instructions, resources.
- **Relevance**: This is the format Acumen's EXPAND phase targets. The standard exists; the self-improvement layer on top of it does not.

---

## 6. IDE-Integrated Learning

### Windsurf -- Memories
- **What it is**: Learns architecture patterns and coding conventions after ~48 hours of use. Autogenerated memories stored locally in ~/.codeium/windsurf/memories/. Two types: user-defined rules and auto-generated memories. Does not consume credits. Cascade retrieves memories when relevant.
- **Gap**: Passive preference learning, not behavioral improvement. No observation of tool outcomes, no evidence-cited proposals, no validation. Locked to Windsurf IDE.

### Cursor -- Rules System
- **What it is**: Evolved from single .cursorrules file (2023) to multi-file .cursor/rules/*.mdc architecture (2025) to context-aware rules with MCP integration (2026). Project rules, user rules, team rules. Studies show acceptance rate goes from 30% to 80%+ with rules.
- **Gap**: Rules are manually authored by humans. No automatic extraction from sessions. No learning from outcomes. Cursor does not observe what worked and propose improvements. The "Memory Bank" pattern is a community workaround, not a product feature.

### Google Antigravity
- **What it is**: Agent-first IDE from Google (public preview, free). Agents can save useful context to a knowledge base. Learns from feedback and past work over time. SWE-bench 76.2%.
- **Gap**: New and details are sparse on learning mechanism. Likely similar to Windsurf Memories -- preference learning, not behavioral improvement. Locked to Antigravity IDE.

### Verdict on IDE Learning
All three major IDEs (Windsurf, Cursor, Antigravity) have some form of memory/learning. But in every case:
- Learning is *preference/convention* learning, not *behavioral pattern* learning
- No observation of tool-level success/failure
- No evidence-cited improvement proposals
- No validation against verifiable signals
- Locked to their respective IDE -- no portability

---

## The Gap: What Acumen Does That Nothing Else Does

| Capability | DGM | OpenSpace | Claude-Mem | Windsurf | Cursor Rules | Auto Memory | Acumen |
|---|---|---|---|---|---|---|---|
| Observes tool-level session metadata | No | Partial | Yes (full) | No | No | No | Yes |
| Extracts behavioral patterns offline | Yes (evolve) | Yes (skill mining) | No | Auto after 48h | No | Auto Dream | Yes |
| Evidence-cited improvement proposals | No | No | No | No | No | No | Yes |
| Validates against success/fail signals | Yes (bench) | Yes (task outcome) | No | No | No | No | Yes |
| Rule retirement for harmful rules | No | FIX mode | No | No | No | Deletes stale | Yes |
| Local-only, zero cloud dependency | Yes | SQLite local | Local SQLite | Local files | Local files | Local files | Yes |
| Project-specific (not generic) | No (benchmark) | No (generic) | Yes | Yes | Yes | Yes | Yes |
| Works across IDEs/agents | Partial | Yes (SKILL.md) | No (CC only) | No | No | No (CC only) | CC first, extensible |
| Zero external dependencies | No (Python) | No (Python+deps) | No (agent-sdk) | N/A (IDE) | N/A (IDE) | Built-in | Yes (stdlib) |

**The unique gap Acumen fills**: A closed-loop system that observes agent sessions at the tool-metadata level, runs reflection to extract evidence-cited behavioral patterns, proposes improvements to project rules, validates improvements against verifiable outcome signals, and retires harmful rules -- all locally, with zero cloud dependency, zero external dependencies, as a plug-and-play Claude Code plugin.

The closest products approach one or two columns of this table. None approach all of them.

---

## Competitive Risks

1. **Claude Code Auto Memory gets smarter**: Anthropic could extend Auto Dream to analyze tool outcomes and propose rule changes. This is the most direct competitive threat because it's built-in. Acumen's defense: it's already shipping this, and built-in features tend to stay general-purpose.

2. **OpenSpace adds evidence-citing**: OpenSpace has the skill evolution loop but lacks evidence-cited proposals. If they add project-specific observation + evidence, they become a real competitor. Acumen's defense: OpenSpace is a general skill engine, not a project-specific rule system.

3. **Codex auto-deepening matures**: If OpenAI ships real auto-deepening that observes outcomes and improves skills, that's competitive. But it would be Codex-only.

4. **IDE memory gets behavioral**: If Windsurf/Cursor/Antigravity move from preference learning to behavioral learning (observing what worked, not just what the user typed), that threatens the IDE-integrated use case. Acumen's defense: IDE lock-in, and Acumen is agent-native, not IDE-native.

---

## Sources

- [Sakana AI Darwin Godel Machine](https://sakana.ai/dgm/)
- [Meta Hyperagents](https://arxiv.org/abs/2603.19461)
- [OpenSpace](https://github.com/HKUDS/OpenSpace)
- [SkillRL](https://github.com/aiming-lab/SkillRL)
- [SAGE (Amazon)](https://github.com/amazon-science/SAGE)
- [Mem0 Graph Memory](https://mem0.ai/blog/graph-memory-solutions-ai-agents)
- [Letta vs Mem0 vs Zep comparison](https://forum.letta.com/t/agent-memory-letta-vs-mem0-vs-zep-vs-cognee/88)
- [Agent Memory Frameworks Compared](https://vectorize.io/articles/best-ai-agent-memory-systems)
- [Claude-Mem Plugin](https://github.com/thedotmack/claude-mem)
- [Memsearch Plugin](https://zilliztech.github.io/memsearch/claude-plugin/)
- [Claude Code Memory Docs](https://code.claude.com/docs/en/memory)
- [Claude Code Auto Dream](https://claudefa.st/blog/guide/mechanics/auto-dream)
- [Windsurf Memories](https://docs.windsurf.com/windsurf/cascade/memories)
- [Cursor Rules](https://docs.cursor.com/context/rules)
- [Google Antigravity](https://developers.googleblog.com/build-with-google-antigravity-our-new-agentic-development-platform/)
- [Codex CLI Skills](https://developers.openai.com/codex/skills)
- [Augment Code](https://www.augmentcode.com/tools/13-best-ai-coding-tools-for-complex-codebases)
- [Sourcegraph Cody](https://sourcegraph.com/blog/how-cody-understands-your-codebase)
- [OpenClaw Skills Registry](https://github.com/VoltAgent/awesome-openclaw-skills)
- [Termo Self-Improving Agent](https://termo.ai/skills/self-improvement)
- [Anthropic Skills Spec](https://github.com/anthropics/skills)
- [Repository Intelligence Trend](https://www.buildmvpfast.com/blog/repository-intelligence-ai-coding-codebase-understanding-2026)

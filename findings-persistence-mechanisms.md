# Persistence Mechanisms for AI Coding Agent Knowledge

**Date**: 2026-03-29
**Scope**: Deep research on how to persist learned rules/knowledge for Claude Code agents
**Context**: Acumen needs a persistence strategy that enables self-improvement without degrading instruction compliance

---

## Executive Summary

There is no single best persistence mechanism. The optimal strategy is a **tiered architecture** that distributes learned knowledge across multiple layers based on universality, enforcement criticality, and frequency of access. The key insight from both Anthropic's documentation and community experience: **instruction compliance degrades linearly as instruction count increases** (Jaroslawicz et al., 2025). Every low-value rule added dilutes the compliance probability of every high-value rule equally. This makes the choice of WHERE to persist a learned rule as important as WHAT the rule says.

---

## 1. CLAUDE.md as Persistence Mechanism

### How It Works
- Loaded in full at the start of every session as user-message-level context (not system prompt)
- Hierarchical: walks up directory tree from CWD, loading all CLAUDE.md files found
- Subdirectory CLAUDE.md files load on-demand when Claude reads files in those directories
- Survives `/compact` -- re-read from disk and re-injected fresh
- Supports `@path/to/import` syntax for pulling in external files (max 5 hops deep)

### The Instruction Budget Problem
- **Hard limit**: Frontier models reliably follow ~150-200 instructions before compliance drops
- **System prompt overhead**: Claude Code's own system prompt consumes ~50 instruction slots
- **Remaining budget**: ~100-150 slots for user rules
- **Degradation curve**: Linear decay -- doubling instructions halves compliance (Claude Sonnet specifically)
- **Uniform degradation**: Past the threshold, every low-value rule added dilutes compliance probability for ALL rules equally
- **Empirical evidence**: One practitioner wrote 200 lines of rules; Claude ignored half of them. Best models follow fewer than 30% of instructions perfectly in agent scenarios
- **Context cost**: ~20K tokens burned loading system prompt + tool definitions + CLAUDE.md before any conversation starts

### What Practitioners Say About Bloat
- "A bloated CLAUDE.md makes Claude ignore your actual instructions" -- directly from Anthropic guidance
- "If Claude keeps doing something you don't want despite having a rule against it, the file is probably too long"
- Community consensus: "A claude.md file will give you 90% of what you need" but only if kept lean
- Anthropic's internal teams: "ruthlessly remove everything unless it passes one rule" -- would removing this cause Claude to make mistakes?
- Target: under 200 lines per CLAUDE.md file; under 50 lines for root CLAUDE.md according to progressive disclosure advocates

### Anthropic's Position on Automated Modification
- **No recommendation for automated CLAUDE.md modification found**
- Anthropic recommends manual curation; `/init` generates a draft, not a finished artifact
- CLAUDE.md is treated as context, not enforced configuration
- The `/memory` command is the recommended path for Claude to write learnings (to MEMORY.md, not CLAUDE.md)
- When users say "remember this," Claude saves to auto memory, not CLAUDE.md, unless explicitly told otherwise

### Verdict for Acumen
**CLAUDE.md is the WRONG place to auto-append learned rules.** The instruction budget is finite and shared with manually written project rules. Auto-appending risks:
1. Exceeding the ~150-instruction threshold
2. Uniformly degrading compliance on ALL rules (including critical project-level ones)
3. Conflicting with manually curated rules
4. Growing unboundedly over time

---

## 2. Claude Code Memory System (.claude/memory/ -> actually ~/.claude/projects/<project>/memory/)

### How It Works
- Storage: `~/.claude/projects/<encoded-path>/memory/` (derived from git repo path)
- Machine-local, never touches git
- All worktrees and subdirectories within the same git repo share one memory directory
- Contains `MEMORY.md` (entrypoint/index) and optional topic files

### Loading Behavior
- **First 200 lines of MEMORY.md, or first 25KB** (whichever comes first) loaded at start of every session
- Content beyond that threshold is NOT loaded at session start
- Topic files (e.g., `debugging.md`, `patterns.md`) are NOT loaded at startup -- Claude reads them on demand
- MEMORY.md acts as an index pointing to topic files

### Auto Memory Feature
- On by default (since v2.1.59)
- Claude decides what's worth remembering based on utility for future conversations
- Saves: build commands, debugging insights, architecture notes, code style preferences, workflow habits
- Does NOT save every session -- only when it discovers something genuinely useful
- Can be toggled via `/memory` or `autoMemoryEnabled` in settings

### AutoDream Consolidation
- Runs automatically between sessions
- Three operations: pruning (removing redundant/stale), merging (consolidating related), refreshing (updating to reflect current state)
- Keeps memory files lean and organized

### Capacity/Budget
- **200 lines / 25KB** for MEMORY.md auto-loading (whichever limit hits first)
- Topic files: no hard limit, but loaded on-demand only
- Custom storage location possible via `autoMemoryDirectory` setting

### Can Plugins Write To It?
- Subagents can have their own persistent memory via the `memory` field (`user`, `project`, or `local` scope)
- Subagent memory directory gets Read/Write/Edit tools automatically enabled
- The memory directory is plain markdown files -- any process with filesystem access can write to them
- Third-party plugins (claude-mem, memsearch, memory-store-plugin) have been built to extend memory
- There is no formal "memory API" -- it's just files on disk

### Verdict for Acumen
**Memory is a strong candidate for learned rules**, but with caveats:
- **Pro**: Purpose-built for agent learnings; separate budget from CLAUDE.md instructions
- **Pro**: 200 lines / 25KB auto-loaded is generous for curated rules
- **Pro**: Topic file overflow pattern provides graceful scaling
- **Pro**: AutoDream handles consolidation automatically
- **Con**: Limited to 200 lines auto-loaded; rules beyond that require Claude to actively seek them
- **Con**: Machine-local (not sharable across team members unless you build a sync mechanism)
- **Con**: No formal plugin API -- must write files directly
- **Recommendation**: Use MEMORY.md for high-priority learned rules (limited set), topic files for detailed patterns

---

## 3. .claude/rules/ Directory

### How It Works
- Place `.md` files in `.claude/rules/` directory
- Discovered recursively (can organize into subdirectories like `frontend/`, `backend/`)
- Each file should cover one topic with descriptive filename

### Loading Behavior
- **Rules WITHOUT `paths` frontmatter**: loaded at launch, same priority as .claude/CLAUDE.md (always-on)
- **Rules WITH `paths` frontmatter**: loaded on-demand when Claude reads files matching the glob pattern
- User-level rules in `~/.claude/rules/` load before project rules (project rules have higher priority)

### Path Scoping (Conditional Loading)
- Uses YAML frontmatter with `paths` field
- Glob patterns: `**/*.ts`, `src/**/*`, `src/components/*.tsx`
- Brace expansion supported: `src/**/*.{ts,tsx}`
- **Important bug note**: The documented `paths:` format has had issues; quoted glob patterns work reliably

### Difference from CLAUDE.md
- **Modularity**: Multiple files vs. one monolith
- **Scoping**: Can be path-conditional; CLAUDE.md cannot
- **Organization**: Each file covers one topic
- **Same budget**: Always-on rules consume the same instruction budget as CLAUDE.md
- **Symlink support**: Can share rules across projects via symlinks

### Verdict for Acumen
**Rules are excellent for STATIC, pre-defined, path-scoped patterns** but have the same instruction budget problem as CLAUDE.md for always-on rules. For learned rules:
- **Pro**: Path scoping means learned rules can be targeted, reducing budget waste
- **Pro**: Modular files are easier to manage programmatically than appending to CLAUDE.md
- **Pro**: Can be version-controlled and shared with team
- **Con**: Always-on rules share the same instruction budget as CLAUDE.md
- **Con**: Not designed for dynamic/auto-generated content
- **Recommendation**: Use path-scoped rules for domain-specific learned patterns (e.g., "when working on API files, always validate inputs" only loads when Claude touches API files)

---

## 4. Settings.json Hooks (Deterministic Enforcement)

### How They Work
- Configure in `~/.claude/settings.json` (user) or `.claude/settings.json` (project)
- Fire at specific lifecycle points: PreToolUse, PostToolUse, Stop, SessionStart, etc.
- 25+ hook events available
- Three-level filtering: Event fires -> Matcher checks -> If condition checks -> Handler executes

### Hook Types
1. **Command hooks**: Run shell scripts; input via stdin JSON, output via stdout JSON
2. **HTTP hooks**: POST to URL endpoints
3. **Prompt hooks**: LLM evaluation (still probabilistic, not 100% reliable)
4. **Agent hooks**: Spawn agent for evaluation

### Exit Code Behavior
- **Exit 0**: Success, parses stdout JSON
- **Exit 2**: Blocking error -- blocks the tool call (PreToolUse), denies permission, rejects prompt
- **Other**: Non-blocking error, continues

### Hooks vs Instructions for Behavioral Enforcement
| Aspect | Hooks | Instructions (CLAUDE.md) |
|---|---|---|
| Execution | Deterministic, code-based | Probabilistic, Claude interprets |
| Blocking | Can block tool calls, permissions | Advisory only, cannot block |
| Real-time control | Can modify tool inputs, return decisions | No real-time control |
| Performance cost | Process/HTTP spawn per event | No runtime cost |
| Use case | Security, compliance, format checking | Guidelines, best practices |
| Reliability | 100% for command hooks | Linear decay with instruction count |

### Key Insight
"Rules in prompts are requests. Hooks in code are laws."

### What Can Be Enforced via Hooks
- Format checking (run prettier/black after every edit)
- Test requirements (block commits without passing tests)
- Command interception (block dangerous commands)
- File validation (check file contents after write)
- Naming conventions (validate file/function names)
- Import restrictions (block disallowed dependencies)

### What CANNOT Be Enforced via Hooks
- Architectural decisions (too subjective for code-based checking)
- Code quality patterns (requires understanding intent)
- Documentation standards (content quality, not just presence)
- Design pattern usage (too context-dependent)

### Verdict for Acumen
**Hooks are the RIGHT mechanism for objectively determinable rules** -- anything that can be expressed as a shell script check. For Acumen's self-improvement:
- **Pro**: 100% enforcement, no instruction budget consumed
- **Pro**: Cannot be ignored or forgotten by the model
- **Pro**: Deterministic -- same behavior every time
- **Con**: Only works for rules expressible as code checks
- **Con**: Process spawn overhead per event
- **Con**: Cannot enforce subjective/contextual patterns
- **Recommendation**: Convert any learned rule that is objectively verifiable into a hook. Use the `PostToolUse` matcher on `Write|Edit` to validate outputs, and `PreToolUse` on `Bash` to validate commands.

---

## 5. Other Persistence Mechanisms

### Skills (On-Demand Context Injection)
- Only skill descriptions loaded at startup (short text for matching)
- Full skill content loads ONLY when invoked or auto-matched
- Zero token cost when not active
- Can include supporting files, templates, scripts
- Can inject dynamic context via `!`command`` syntax (shell commands run before content reaches Claude)
- Path-scoped activation via `paths` frontmatter
- Can run in subagent context (`context: fork`)

**For learned rules**: Skills are ideal for DOMAIN-SPECIFIC learned patterns that don't need to be active in every session. Example: a "database-patterns" skill that loads only when Claude is working on DB code, containing all learned patterns about query optimization, migration safety, etc.

**Important finding**: Vercel's evals showed skills had 79% pass rate vs 100% for explicit docs -- skills work best for reference material, not critical enforcement.

### Custom Commands (Merged Into Skills)
- `.claude/commands/deploy.md` and `.claude/skills/deploy/SKILL.md` are equivalent
- Both create `/deploy` slash command
- Skills are the recommended path going forward

### Subagent Memory
- Subagents can maintain their own persistent memory via `memory: user|project|local`
- Memory stored at `~/.claude/agent-memory/` (user scope)
- First 200 lines / 25KB of MEMORY.md auto-loaded into subagent context
- Read/Write/Edit tools automatically enabled

### Third-Party Plugins
- **claude-mem**: Captures all tool usage, compresses into summaries, stores in SQLite, injects index into future sessions
- **memsearch**: Vector-based semantic memory search via MCP
- **mem0**: External memory service integration
- **Basic Memory**: Knowledge graph-based persistence
- **Supermemory**: Enhanced memory with auto-injection

### Progress Files / Task State
- `progress.txt`, `prd.json`, `findings.md` -- plain files on disk
- Agent appends results each iteration
- Next iteration reads to understand history
- No framework dependency; works with any agent

### Git History as Memory
- Commit messages provide context
- `git log` and `git diff` available to agents
- Auditable, version-controlled
- No additional infrastructure

---

## 6. Community Consensus and Best Practices

### What Works (Strong Agreement)
1. **Simplicity wins**: "I didn't want a database or an MCP server or embeddings -- markdown files work with git"
2. **Local-first**: Strong preference for local, version-controlled approaches over cloud services
3. **Progressive disclosure**: Root CLAUDE.md stays short; domain knowledge loads on demand
4. **Deterministic over advisory**: "I try to make as much of it as deterministic as possible"
5. **Tooling over documentation**: Don't document what linters enforce; let ESLint/Prettier/Black handle it

### What Doesn't Work (Strong Agreement)
1. **Bloated CLAUDE.md**: Universally recognized as counterproductive
2. **Over-engineered memory solutions**: "So many of these memory solutions are incredibly over-engineered"
3. **Write-only knowledge bases**: Claude saves to them but rarely retrieves from them
4. **Context compaction reliance**: Rules given only in conversation get "summarized into oblivion"
5. **Dedicated memory products**: "This is the #1 thing Claude Code developers are working on too, and it's clearly getting better" -- competing with native features

### Emerging Patterns for Self-Improving Agents
1. **Validate before learning**: Run tests/lint before recording learnings; bad information degrades future performance
2. **Curated knowledge, not logs**: Treat AGENTS.md/MEMORY.md as curated artifacts, not catch-all logs
3. **Pruning schedule**: Regularly review for stale entries; archive outdated items
4. **Task-based context filtering**: Only show learnings relevant to current task
5. **Stop conditions**: Set maximum iteration limits to prevent runaway learning loops
6. **Earned trust model**: Start with zero trust, let agent earn autonomous authority through demonstrated accuracy

---

## 7. Recommended Architecture for Acumen

Based on all research, the recommended tiered persistence architecture:

### Tier 1: Hooks (Deterministic Enforcement) -- for rules that CAN be expressed as code
- Convert learned patterns into shell-script validations
- PostToolUse hooks on Write/Edit for output validation
- PreToolUse hooks on Bash for command safety
- Zero instruction budget consumed
- 100% enforcement reliability
- **Examples**: "Always run formatter after edit", "Never delete migration files", "Always include type hints"

### Tier 2: Path-Scoped Rules (.claude/rules/) -- for domain-specific learned rules
- Write learned patterns as path-scoped rule files
- Only load when Claude works on matching files
- Minimizes instruction budget impact
- Version-controllable, shareable
- **Examples**: "When working on API handlers, always validate request bodies", "When writing tests for auth, mock the JWT provider"

### Tier 3: Auto Memory (MEMORY.md) -- for general learned insights
- Let Claude's native auto memory handle broad learnings
- 200 lines / 25KB auto-loaded budget
- Topic file overflow for detailed patterns
- AutoDream handles consolidation
- **Examples**: "This project uses pnpm not npm", "The CI requires Node 20", "Database migrations need DOWN scripts"

### Tier 4: Skills (On-Demand Context) -- for deep domain knowledge
- Package extensive learned knowledge as skills
- Zero token cost when not active
- Can include templates, examples, scripts
- Path-scoped activation possible
- **Examples**: "All learned patterns about database optimization", "Comprehensive testing playbook for this project"

### What NOT to do
- Do NOT auto-append to CLAUDE.md
- Do NOT create always-on rules for domain-specific patterns
- Do NOT rely on a single persistence mechanism
- Do NOT persist learnings without validation (tests must pass first)
- Do NOT compete with Claude Code's native memory system -- work with it

---

## Sources

- [How Claude remembers your project - Claude Code Docs](https://code.claude.com/docs/en/memory)
- [Best Practices for Claude Code - Claude Code Docs](https://code.claude.com/docs/en/best-practices)
- [Extend Claude with skills - Claude Code Docs](https://code.claude.com/docs/en/skills)
- [Hooks reference - Claude Code Docs](https://code.claude.com/docs/en/hooks)
- [Self-Improving Coding Agents - Addy Osmani](https://addyosmani.com/blog/self-improving-agents/)
- [I Wrote 200 Lines of Rules for Claude Code. It Ignored Them All. - DEV Community](https://dev.to/minatoplanb/i-wrote-200-lines-of-rules-for-claude-code-it-ignored-them-all-4639)
- [Stop Bloating Your CLAUDE.md: Progressive Disclosure - alexop.dev](https://alexop.dev/posts/stop-bloating-your-claude-md-progressive-disclosure-ai-coding-tools/)
- [Claude Code Rules: Stop Stuffing Everything into One CLAUDE.md - Medium](https://medium.com/@richardhightower/claude-code-rules-stop-stuffing-everything-into-one-claude-md-0b3732bca433)
- [Recursive Self-Improvement: Building a Self-Improving Agent - Medium](https://medium.com/@davidroliver/recursive-self-improvement-building-a-self-improving-agent-with-claude-code-d2d2ae941282)
- [Show HN: Stop Claude Code from forgetting everything - Hacker News](https://news.ycombinator.com/item?id=46426624)
- [Claude Code Memory Explained - substack](https://joseparreogarcia.substack.com/p/claude-code-memory-explained)
- [How Claude Code rules actually work - substack](https://joseparreogarcia.substack.com/p/how-claude-code-rules-actually-work)
- [5 Patterns That Make Claude Code Actually Follow Your Rules - DEV](https://dev.to/docat0209/5-patterns-that-make-claude-code-actually-follow-your-rules-44dh)
- [Claude Code for Everything: CLAUDE.md Deep Dive - substack](https://hannahstulberg.substack.com/p/claude-code-for-everything-the-best-personal-assistant-remembers-everything-about-you)
- [CLAUDE.md Best Practices - Medium](https://medium.com/@rentierdigital/claude-md-is-the-new-env-and-most-developers-treat-it-like-a-readme-1d17c989147e)
- [Claude-Mem Plugin - GitHub](https://github.com/thedotmack/claude-mem)
- [Claude Code Hooks Mastery - GitHub](https://github.com/disler/claude-code-hooks-mastery)
- [CLAUDE.md Complete Guide 2026 - shareuhack.com](https://www.shareuhack.com/en/posts/claude-code-claude-md-setup-guide-2026)
- [What Is Claude Code AutoDream? - MindStudio](https://www.mindstudio.ai/blog/what-is-claude-code-autodream-memory-consolidation-2)
- [Building Persistent Memory for Claude Code Agents - DEV Community](https://dev.to/benji_banwart/building-persistent-memory-for-claude-code-agents-3b5m)

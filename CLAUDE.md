# CLAUDE.md -- Acumen Development Guidelines

## What is Acumen?
A pure Claude Code plugin that makes AI coding agents self-improving. Zero external dependencies. Install is `claude plugin add acumen`. Observes sessions, extracts insights, applies improvements, synthesizes skills.

## Architecture (read spec.md for full details)
```
OBSERVE -> LEARN -> IMPROVE -> EXPAND
  shell hook  subagent    CLAUDE.md    skills
  (bash/jq)   reflection  memory       commands
  metadata    insights     hooks        workflows
  only        patterns
```

Three scopes: global (~/.claude/acumen/), project (.acumen/), session (ephemeral).

## Build & Test Commands
```bash
# Run tests (pytest is a dev-only dependency)
python -m pytest tests/ -v

# Run specific test
python -m pytest tests/test_store.py -v

# Lint Python scripts
ruff check lib/

# Format
ruff format lib/

# Test the observation hook
echo '{"tool_name":"Bash","tool_input":{"command":"ls"},"tool_response":{"exit_code":0},"session_id":"test"}' | bash hooks/observe.sh
```

## Code Style
- Python 3.11+ stdlib ONLY (dataclasses, json, pathlib, uuid) -- zero external dependencies
- Shell scripts for hot-path observation (bash + jq)
- Type hints on all public functions
- No docstrings on obvious methods. Docstrings only when behavior is non-obvious.

## Testing
- Tests live in `tests/`, mirror source structure
- Naming: `test_<module>.py`
- Test-aware development (NOT rigid TDD ceremony -- research shows procedural TDD instructions without targeted test context INCREASE regressions by 63%)
- For every behavior change: (1) identify which tests are affected, (2) ensure tests exist, (3) run them before committing
- No mocks for file I/O -- use tmp_path fixture
- Test the public interface, not internals
- Write tests ALONGSIDE implementation, not ceremonially before. The goal is test coverage, not process theater.

## Key Design Rules

<IMPORTANT>
### Anti-Bloat Rules (CRITICAL)
Follow KISS, YAGNI, DRY. These rules exist because AI coding agents produce bloated, overengineered code by default. Every line below is load-bearing.

**Structure:**
1. **Prefer functions over classes.** Only use a class if it holds mutable state across multiple method calls. No abstract base classes, factory patterns, or dependency injection.
2. **No utility modules, helper files, or "common" packages.** Put code where it's used. If two files need the same function, it goes in the one that uses it more.
3. **No custom exception hierarchies.** Use ValueError, RuntimeError, or built-in exceptions. `raise ValueError("bad scope")` not `raise AcumenScopeError("bad scope")`.
4. **Maximum one level of function nesting.** If you need a helper, make it a module-level function, not a nested def.
5. **File count discipline.** Before creating a new file, check if the code fits naturally in an existing one. A module with < 50 lines probably shouldn't be its own file.

**Scope:**
6. **No speculative features.** Build only what spec.md Phase 1 requires. Phase 2+ features do not exist until Phase 1 ships.
7. **No premature abstraction.** Three concrete implementations before extracting a pattern. If a function is only called from one place, inline it.
8. **Do not refactor code unless the task explicitly says "refactor."** A bug fix does not need surrounding code cleaned up.
9. **No "just in case" error handling.** Handle errors that can actually happen. Don't catch exceptions you can't do anything useful with.

**Style:**
10. **Read the file before editing it.** Match existing code style. Do not reformat or restructure code you didn't change.
11. **No auto-generated docstrings, comments, or type stubs.** Comments explain WHY, never WHAT. Only add comments where the logic isn't self-evident.
12. **No configuration for things that don't vary.** If all users will use the same value, hardcode it.
13. **Zero dependency discipline.** Python stdlib ONLY. No pip packages. Do not add ANY dependency without explicit approval.
14. **When unsure between two approaches, pick the one with fewer lines of code.**
</IMPORTANT>

### Architectural Rules
- **No LLM calls in the hot path.** Observation is pure data collection. Only reflection uses the LLM.
- **No database.** JSON files only. Human-readable, git-friendly, zero setup.
- **No network calls.** Everything runs locally. Zero telemetry.
- **Fail-open.** If Acumen crashes, the agent works normally. Never block the user.
- **Idempotent operations.** Running the same reflection twice produces the same insights.

### Safety Rules
- **Metadata-only observation.** Capture tool_name, outcome, timestamp, error_type. NEVER capture tool_input values or tool_response content. This is a security decision grounded in DGM research showing self-improving systems encounter sensitive data.
- **SAFE tier only auto-applies.** Everything else needs user approval.
- **All improvements reversible.** Before/after state recorded.
- **Fail-open always.** If any Acumen component fails, the agent continues normally.

## Project Structure
```
acumen/                  # Plugin root (this IS the repo)
  plugin.json            # Plugin manifest
  skills/                # Claude Code skills (reflection, etc.)
  commands/              # Slash commands (/acumen-status, etc.)
  hooks/                 # Shell hooks (observation)
  agents/                # Subagent definitions (reflector)
  lib/                   # Python stdlib scripts (store, scorer, formatter)
  tests/                 # Test suite (dev only)
```

## Documentation
<IMPORTANT>
- Keep README.md up to date as a public-facing document. It should include: what Acumen is, why it exists, installation (one command), usage, architecture overview, how it works, privacy/safety guarantees, and links to spec/findings.
- Structure README.md for open-source readability: badges, hero section, quick start, features, architecture diagram, FAQ.
- Update README.md whenever features, commands, or architecture change.
</IMPORTANT>

## Implementation Protocol (Research-Grounded)
<IMPORTANT>
These rules are derived from 2025-2026 research on preventing AI code bloat. Sources: TDAD paper (arxiv:2603.17973), Addy Osmani, Nathan Onn's "surgical coding", GitClear 2025, HumanLayer ACE, Anthropic best practices.

### Before writing ANY code:
1. **Examine existing code first.** Search for similar patterns already in the codebase. Ask: "Can I solve this by modifying existing code rather than creating new code?"
2. **Challenge the plan.** Ask: "What if this could be done in just one file? What's the simplest possible approach?" If you catch yourself planning an abstraction, stop and ask if there are three concrete uses for it yet.
3. **Know which tests matter.** Before changing code, identify which tests cover the affected area. Run them before AND after.

### While writing code:
4. **One function, one feature at a time.** Never implement multiple features in a single pass. Commit after each logical unit.
5. **Deletion first.** Before adding code, check if removing or simplifying existing code solves the problem.
6. **If you've corrected the same issue twice, /clear and restart.** A clean context with a better prompt outperforms a polluted context with accumulated corrections.

### After writing code:
7. **Fresh-context review.** After implementation, review your own output in a new context. Look for: unnecessary abstractions, dead code, enterprise patterns where simple code would do, files that could be merged.
</IMPORTANT>

## Common Mistakes to Avoid
- Don't import from `toolwright`, `ward`, or `cask`. Acumen is a standalone project.
- Don't use `asyncio` unless a specific feature requires it. Start synchronous.
- Don't create abstract base classes for "future extensibility." Build concrete implementations.
- Don't add logging everywhere. Log at boundaries only.
- Don't write "adapter" classes for future agent support. Build for Claude Code first, adapt later.
- Don't use Pydantic, Click, or any pip package. Python stdlib only.
- Don't capture tool_input values or file contents in observations. Metadata only.
- Don't generate wrapper classes, strategy patterns, or factory patterns. Use plain functions.
- Don't add unused imports, speculative features, or variant files.
- Don't refactor architecture -- reserve that for human judgment. AI is good at low-level consistency, bad at high-level structural decisions (arxiv:2511.04824).

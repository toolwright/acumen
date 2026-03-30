# Claude Code Plugin Automation: Hooks, Scheduled Tasks, and Background Processing

**Date**: 2026-03-29
**Scope**: Deep research on how to make Acumen automatically trigger reflection/review without user intervention
**Context**: Acumen currently requires `/acumen-reflect` and `/acumen-review` to be manually invoked. Goal: automatic reflection so the agent improves between sessions.

---

## 1. Complete List of Claude Code Hook Events (25 Events)

As of March 2026, Claude Code provides **25 hook events** across 8 categories. Four handler types exist: `command` (shell), `http` (POST to URL), `prompt` (single-turn LLM evaluation), and `agent` (subagent with tools).

### Session Lifecycle
| Event | Can Block? | Key Data | Notes |
|-------|-----------|----------|-------|
| **SessionStart** | No | `source` (startup/resume/clear/compact), `model`, `agent_type` | Can inject context via stdout, set env vars via `CLAUDE_ENV_FILE` |
| **SessionEnd** | No | `reason` (clear/resume/logout/prompt_input_exit/bypass_permissions_disabled/other) | Cleanup only. **1.5s default timeout** (configurable via `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS`). Cannot block termination. |

### User Interaction
| Event | Can Block? | Key Data |
|-------|-----------|----------|
| **UserPromptSubmit** | Yes | `prompt` text. Can block with `decision: "block"`, add context. Cannot modify prompt text. |

### Tool Execution
| Event | Can Block? | Key Data |
|-------|-----------|----------|
| **PreToolUse** | Yes | `tool_name`, `tool_input`, `tool_use_id`. Can allow/deny/ask, modify input via `updatedInput`. |
| **PermissionRequest** | Yes | `tool_name`, `tool_input`, `permission_suggestions`. Can allow/deny, update permissions. |
| **PostToolUse** | Yes (feedback) | `tool_name`, `tool_input`, `tool_response`, `tool_use_id`. Tool already ran. Can add context. |
| **PostToolUseFailure** | No | `tool_name`, `tool_input`, `tool_use_id`, `error`, `is_interrupt`. Logging only. |

### Agent Lifecycle
| Event | Can Block? | Key Data |
|-------|-----------|----------|
| **SubagentStart** | No | `agent_id`, `agent_type`. Can inject context. |
| **SubagentStop** | Yes | `agent_id`, `agent_type`, `agent_transcript_path`, `last_assistant_message`, `stop_hook_active`. Can block stopping. |
| **Stop** | Yes | `stop_hook_active`, `last_assistant_message`, `transcript_path`. Can block with `decision: "block"`. |
| **StopFailure** | No | `error`, `error_details`, `last_assistant_message`. Fires on API error instead of normal Stop. |

### Notifications & System
| Event | Can Block? | Key Data |
|-------|-----------|----------|
| **Notification** | No | `message`, `title`, `notification_type` (permission_prompt/idle_prompt/auth_success/elicitation_dialog). |
| **InstructionsLoaded** | No | `file_path`, `memory_type`, `load_reason`. Audit only. |
| **ConfigChange** | Yes | `source` (user_settings/project_settings/local_settings/policy_settings/skills). Can block non-policy changes. |
| **CwdChanged** | No | Can set env vars via `CLAUDE_ENV_FILE`. |
| **FileChanged** | No | Matchers: filename/basename to watch. Can set env vars. |

### Agent Team Tasks
| Event | Can Block? | Key Data |
|-------|-----------|----------|
| **TaskCreated** | Yes | `task_id`, `task_subject`, `task_description`, `teammate_name`, `team_name`. |
| **TaskCompleted** | Yes | Same fields as TaskCreated. Can enforce completion criteria. |
| **TeammateIdle** | Yes | `teammate_name`, `team_name`. Can block idle state. |

### Worktree Management
| Event | Can Block? | Key Data |
|-------|-----------|----------|
| **WorktreeCreate** | Yes | Can replace default git behavior, return worktree path. |
| **WorktreeRemove** | No | Logging/cleanup only. |

### Context Compaction
| Event | Can Block? | Key Data |
|-------|-----------|----------|
| **PreCompact** | No | Trigger type (manual/auto). Logging only. |
| **PostCompact** | No | Trigger type. Logging only. |

### MCP Elicitation
| Event | Can Block? | Key Data |
|-------|-----------|----------|
| **Elicitation** | Yes | MCP server elicitation request. Can accept/decline/cancel. |
| **ElicitationResult** | Yes | User's elicitation response. Can override field values. |

---

## 2. The "Stop" Hook -- Detailed Analysis

### What It Is
The Stop hook fires **every time Claude finishes a response** -- NOT only at session end. This is a critical distinction.

### Input Payload
```json
{
  "session_id": "uuid",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/path/to/project",
  "permission_mode": "ask",
  "hook_event_name": "Stop",
  "stop_hook_active": false,
  "last_assistant_message": "Here's what I did..."
}
```

### Blocking Behavior
- Return `{"decision": "block", "reason": "..."}` to prevent Claude from stopping (forces continuation)
- The `stop_hook_active` flag is `true` when Claude is already in forced-continuation mode from a prior block
- **MUST check `stop_hook_active`** to prevent infinite loops

### Limitations for Acumen
- **Fires after EVERY turn**, not just session end -- would trigger reflection too frequently
- **Cannot reliably determine if this is the final turn** -- user might continue the conversation
- Using Stop to block and run reflection would be disruptive mid-conversation
- Prompt-type Stop hooks have had bugs (JSON validation failures reported)

### What Other Plugins Do With Stop
- **claude-mem**: Fire-and-forget HTTP POST to a separate worker process that summarizes the session asynchronously
- **claude-memory**: Deterministic keyword triage, then blocks stop to spawn parallel subagents for memory drafting
- **dream-skill**: Lightweight check (~10ms), sets a flag file if 24hrs elapsed since last consolidation; actual consolidation runs at next SessionStart

---

## 3. The "SessionEnd" Hook -- Detailed Analysis

### What It Is
SessionEnd fires **once when the session actually terminates** (user exits, /clear, logout, etc.).

### Input Payload
```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/path/to/project",
  "hook_event_name": "SessionEnd",
  "reason": "prompt_input_exit"
}
```

### Critical Limitation: 1.5-Second Default Timeout
- Default timeout is **1.5 seconds** -- far too short for LLM reflection
- Configurable via `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS` environment variable
- Cannot block session termination regardless of timeout
- Command hooks only (no prompt/agent hook types supported)

### What It CAN Do
- Log session data
- Write flag files for next session
- Spawn a background process (nohup/detach) if done quickly
- Make a fire-and-forget HTTP POST to a worker

### What It CANNOT Do
- Run LLM-based reflection (too short, wrong hook type)
- Block or delay session termination
- Trigger a new Claude Code session directly

### The Open Feature Request
- GitHub issue #34954 requested a true "SessionEnd" hook with prompt/agent handler support and 30-120s timeout
- Closed as duplicate of issue #16886 ("PreSessionEnd Hook")
- Users want: fires once at actual end, supports prompt type, configurable timeout, captures complete context
- **This capability does not exist yet**

---

## 4. Scheduled Tasks -- Three Tiers

### Tier 1: Session-Scoped (`/loop` / CronCreate)
- **Mechanism**: Cron jobs within the current Claude Code session
- **Persistence**: Dies when session ends
- **Interval**: Minimum 1 minute, with jitter
- **Limit**: 50 tasks per session
- **Expiry**: Auto-expire after 3 days (7 days for some implementations)
- **Key constraint**: Only fires while Claude Code is running and idle
- **Not useful for Acumen**: Session-scoped means it can't run after session ends

### Tier 2: Desktop Scheduled Tasks
- **Mechanism**: Persistent tasks stored at `~/.claude/scheduled-tasks/<task-name>/SKILL.md`
- **Persistence**: Survives restarts, runs as long as the app is open
- **Minimum interval**: 1 minute
- **Access**: Full access to files, MCP servers, skills, connectors, plugins
- **Platform**: macOS and Windows only (not Linux)
- **Each run**: Fires a fresh session at the scheduled time
- **Created via**: `mcp__scheduled-tasks__create_scheduled_task` MCP tool or Desktop UI
- **VERY USEFUL for Acumen**: Could schedule periodic reflection that runs independently

### Tier 3: Cloud Scheduled Tasks
- **Mechanism**: Runs on Anthropic's cloud infrastructure
- **Persistence**: Yes, survives everything
- **Minimum interval**: 1 hour
- **Access**: Fresh clone (no local files), connectors configured per task
- **No local file access**: Not suitable for Acumen's observation files

---

## 5. Background Agents

Claude Code supports background agents (since v2.0.60):
- Kick off sub-tasks that run in independent git worktrees
- Each background agent works in an independent copy of code
- Results returned when finished
- **However**: These are session-scoped -- they run within a session, not between sessions

---

## 6. What Other Plugins Do (Patterns for Automatic Processing)

### Pattern A: "Flag and Defer" (dream-skill)
1. **Stop hook** runs a ~10ms bash check: has 24hrs elapsed since last consolidation?
2. If yes: writes a flag file (e.g., `.claude/should-dream`)
3. **SessionStart hook** checks for the flag file
4. If flag exists: injects context telling Claude to run `/dream` consolidation
5. Consolidation runs at the START of the next session, not the end of the current one

**Pros**: Zero overhead when not needed, no timeout issues, works reliably
**Cons**: Requires user to start a new session, adds latency to session start

### Pattern B: "Fire-and-Forget Worker" (claude-mem)
1. Runs a **separate Node.js worker process** on port 37777
2. **Stop hook** makes a fire-and-forget HTTP POST to the worker with the transcript
3. Worker processes asynchronously (AI summarization, vector sync) without blocking
4. **SessionEnd hook** signals session completion to the worker
5. Worker uses Claude SDK (Agent SDK) for AI processing

**Pros**: Non-blocking, immediate processing, rich AI analysis
**Cons**: Requires running a separate server process, complex architecture, external dependency

### Pattern C: "Block-and-Process" (claude-memory)
1. **Stop hook** runs deterministic keyword triage across 6 categories
2. If triggers found: blocks the Stop, outputs structured data
3. Spawns parallel LLM subagents per category to draft memories
4. Then allows the stop

**Pros**: Thorough analysis with LLM reasoning
**Cons**: Disruptive (blocks mid-conversation too), can create infinite loops, fires too often

### Pattern D: "Headless Background Session"
1. **SessionEnd hook** spawns `nohup claude -p "reflect on observations" &` as a background process
2. The headless Claude session runs reflection autonomously
3. Results written to files that the next session picks up

**Pros**: Full LLM capability, runs after session ends
**Cons**: Uses API credits, 1.5s timeout may not be enough to spawn reliably, untested pattern

### Pattern E: "Desktop Scheduled Task"
1. Create a Desktop scheduled task via `create_scheduled_task` MCP tool
2. Task runs on a cron schedule (e.g., every 30 minutes, or daily)
3. Each run is a fresh session with full file/MCP/plugin access
4. Task prompt instructs Claude to reflect on observations and generate proposals

**Pros**: Persistent, reliable, full capability, runs independently of user sessions
**Cons**: macOS/Windows only, requires Desktop app, minimum 1-minute interval

---

## 7. Recommended Approach for Acumen

Based on this research, the best strategies for Acumen automatic reflection (ranked by feasibility):

### Strategy 1: Flag-and-Defer (Recommended -- Simplest)
Add two hooks to Acumen's `plugin.json`:

1. **SessionEnd hook** (command): Quick bash script that writes a flag file (`.acumen/should-reflect`) if enough new observations exist since last reflection
2. **SessionStart hook** (command): Checks for flag file, if present, injects context via stdout telling Claude to run reflection

**Implementation**:
```json
{
  "SessionEnd": [{
    "hooks": [{
      "type": "command",
      "command": "${CLAUDE_PLUGIN_ROOT}/hooks/should-reflect.sh"
    }]
  }],
  "SessionStart": [{
    "hooks": [{
      "type": "command",
      "command": "${CLAUDE_PLUGIN_ROOT}/hooks/auto-reflect.sh"
    }]
  }]
}
```

The `should-reflect.sh` script (must complete in <1.5s):
- Count observations since last reflection timestamp
- If threshold met (e.g., 5+ new observations): write flag file
- Exit 0

The `auto-reflect.sh` script:
- Check for flag file
- If present: echo context telling Claude to reflect (stdout becomes additionalContext)
- Remove flag file

**Tradeoff**: Reflection happens at the START of the next session (slight delay for user), but is reliable and zero-complexity.

### Strategy 2: Desktop Scheduled Task (Recommended -- Most Autonomous)
Create a Desktop scheduled task that periodically runs reflection:

```
Prompt: "Check for new Acumen observations in the project. If there are unreflected observations, run /acumen-reflect and then /acumen-review to generate proposals. Write results to the standard Acumen output locations."
Schedule: Every 2 hours (or daily)
```

**Tradeoff**: Requires Desktop app, but runs completely independently of user sessions. The agent literally improves itself in the background.

### Strategy 3: Hybrid (Best of Both Worlds)
Combine Strategy 1 + Strategy 2:
- Flag-and-defer handles the common case (user starts new session, gets reflection)
- Desktop scheduled task handles the background case (reflection runs even if user doesn't start a new session for hours)
- Both are idempotent and check the same observation timestamps

### What NOT to Do
- **Don't use the Stop hook for reflection**: It fires after every turn, not at session end
- **Don't use blocking Stop hooks**: Disruptive mid-conversation, creates loop risks
- **Don't rely on SessionEnd for LLM work**: 1.5s timeout is insufficient
- **Don't use Cloud scheduled tasks**: No local file access, can't read observations

---

## 8. Key Technical Details for Implementation

### Hook Input/Output Common Fields
All hooks receive via stdin:
```json
{
  "session_id": "string",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/current/working/dir",
  "permission_mode": "ask|allow",
  "hook_event_name": "EventName"
}
```

### SessionStart Output (Context Injection)
Anything printed to stdout becomes `additionalContext` shown to Claude:
```bash
#!/bin/bash
echo "You have 7 new observations ready for reflection. Consider running /acumen-reflect."
```

### Plugin hooks.json Format
```json
{
  "description": "Acumen automation hooks",
  "hooks": {
    "SessionEnd": [...],
    "SessionStart": [...]
  }
}
```
Note: Plugin hooks go in `hooks/hooks.json`, NOT in `plugin.json` (though `plugin.json` also supports a hooks field directly).

### Desktop Scheduled Task Creation
Via MCP tool `create_scheduled_task`:
```json
{
  "taskId": "acumen-reflect",
  "prompt": "Check for new observations and run reflection...",
  "description": "Periodic Acumen reflection and proposal generation",
  "cronExpression": "0 */2 * * *"
}
```

### SessionEnd Timeout Configuration
```bash
export CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS=10000  # 10 seconds
```

---

## Sources

- [Claude Code Hooks Reference (Official)](https://code.claude.com/docs/en/hooks)
- [Claude Code Scheduled Tasks (Official)](https://code.claude.com/docs/en/scheduled-tasks)
- [Stop Hook Task Enforcement](https://claudefa.st/blog/tools/hooks/stop-hook-task-enforcement)
- [Session Lifecycle Hooks](https://claudefa.st/blog/tools/hooks/session-lifecycle-hooks)
- [Claude Code Headless Mode (Official)](https://code.claude.com/docs/en/headless)
- [Claude Code Plugin Development (Official)](https://github.com/anthropics/claude-code/blob/main/plugins/plugin-dev/skills/hook-development/SKILL.md)
- [SessionEnd Hook Feature Request #34954](https://github.com/anthropics/claude-code/issues/34954)
- [claude-mem Architecture: Stop and SessionEnd Hooks](https://deepwiki.com/thedotmack/claude-mem/3.1.4-stop-and-sessionend-hooks)
- [dream-skill: Memory Consolidation](https://github.com/grandamenium/dream-skill)
- [claude-mem Plugin](https://github.com/thedotmack/claude-mem)
- [claude-memory Plugin](https://github.com/idnotbe/claude-memory)
- [Claude Code Hooks Guide (All 12+ Events)](https://www.pixelmojo.io/blogs/claude-code-hooks-production-quality-ci-cd-patterns)
- [Claude Code Background Workers](https://winbuzzer.com/2026/03/09/anthropic-claude-code-cron-scheduling-background-worker-loop-xcxwbn/)
- [Claude Code Desktop Scheduled Tasks](https://claudefa.st/blog/guide/development/scheduled-tasks)

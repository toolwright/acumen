# Acumen Implementation Plan

**Date:** 2026-03-29
**Scope:** Phase 1 (Observe + Learn) -- MVP
**Architecture:** Pure Claude Code plugin, zero external dependencies

---

## Overview

Phase 1 delivers the core observation and learning loop. The user installs Acumen (`claude plugin add acumen`), works normally, and after a week can see `/acumen-status` showing insight trends. No auto-application of improvements yet (that's Phase 2).

```
Phase 1 data flow:

  PostToolUse event (stdin JSON)
      |
      v
  observe.sh (shell hook) -----> .acumen/observations/YYYY-MM-DD.jsonl
      |                                    |
      |  (metadata only:                   |
      |   tool_name, outcome,              |
      |   timestamp, error_type)           |
      |                                    |
      +-- /acumen-reflect -------> reflector subagent
      |                               |
      |                               |-- reads observations
      |                               |-- detects patterns
      |                               |-- extracts insights (LLM)
      |                               |-- scores & ranks
      |                               v
      |                          .acumen/insights/insights.json
      |
      +-- /acumen-status --------> lib/formatter.py
                                       |
                                       |-- reads observations (trends)
                                       |-- reads insights
                                       |-- formats CLI output
                                       v
                                  Displayed to user
```

---

## Step 0: Plugin Scaffolding

**Files:**
- `plugin.json` -- plugin manifest with name, description, version
- `hooks/observe.sh` -- empty placeholder (implemented in Step 2)
- `.gitignore`

**Tests:** None needed (manifest is declarative)

**Exit criteria:** `claude plugin add ./` installs without errors. Plugin appears in plugin list.

---

## Step 1: Observation Hook

The hot path. Must be near-instant. Pure shell.

**Files:**
- `hooks/observe.sh` -- PostToolUse shell hook

**Responsibilities:**
- Read JSON from stdin (Claude Code hook data contract)
- Extract metadata: tool_name, session_id, timestamp, outcome (inferred from tool_response)
- Detect error outcomes (Bash exit_code != 0, etc.)
- Append JSONL line to `.acumen/observations/YYYY-MM-DD.jsonl`
- Create `.acumen/observations/` if missing
- Check for jq availability; fall back to raw JSON append if missing

**Tests:** `tests/test_observe_hook.py`
- Hook produces valid JSONL from sample PostToolUse JSON
- Hook creates directory if missing
- Hook handles missing/malformed stdin gracefully (no crash, no output)
- Hook does NOT capture tool_input values (security test)
- Hook does NOT capture tool_response content (security test)
- Hook works without jq (fallback test)

**Exit criteria:** Every tool call produces one JSONL line with metadata only.

---

## Step 2: Storage Library

Python stdlib script for reading/writing observation and insight data.

**Files:**
- `lib/store.py` -- read/write functions for observations and insights

**Functions:**
- `read_observations(scope_path, days=7)` -- read JSONL files, return list of dicts
- `write_insight(scope_path, insight)` -- append insight to insights.json
- `read_insights(scope_path)` -- read insights.json, return list of dicts
- `resolve_scope_path(scope="project")` -- return correct directory path for scope

**Uses:** dataclasses for Observation/Insight data shapes, json for serialization, pathlib for file ops.

**Tests:** `tests/test_store.py`
- read_observations returns empty list when no files exist
- read_observations reads across multiple daily files
- read_observations skips corrupted JSONL lines (logs warning count)
- write_insight creates file if missing
- write_insight appends without overwriting
- Concurrent writes don't corrupt (write-tmp-rename pattern)
- resolve_scope_path returns correct paths for project scope
- Handles empty files, missing directories gracefully

**Exit criteria:** Reliable read/write of JSONL observation data and JSON insight data.

---

## Step 3: Scorer

Confidence and impact scoring. Pure math, no LLM.

**Files:**
- `lib/scorer.py` -- scoring and ranking functions

**Functions:**
- `score_insight(insight, observations)` -- compute confidence (0-1) and impact (0-1)
- `rank_insights(insights)` -- sort by combined score
- `dedup_insights(new_insights, existing_insights)` -- merge similar insights

**Scoring logic:**
- Confidence = f(evidence_count, recency_weight)
- Impact = f(error_severity, frequency, user_correction_count)
- Combined = confidence * 0.4 + impact * 0.6

**Tests:** `tests/test_scorer.py`
- Insight with 10 observations scores higher than 2
- Recent observations score higher than old ones
- Failure patterns score higher than informational observations
- Dedup merges insights with matching descriptions
- Handles zero observations, NaN, empty inputs

**Exit criteria:** Insights are scored and ranked deterministically.

---

## Step 4: Reflector Subagent

The brain. An agent definition that reads observations and extracts insights using the host LLM.

**Files:**
- `agents/reflector.md` -- subagent definition with system prompt
- `skills/reflect.md` -- skill that invokes the reflector subagent

**The reflector agent prompt includes:**
- Instructions to read observation files from `.acumen/observations/`
- Pattern detection guidelines (repeated failures, correction patterns, error trends)
- Output format specification (structured JSON insights)
- Existing insights (to avoid duplicates)
- Guidelines grounded in ExpeL research (natural language insights from experience)

**The reflect skill:**
- Invoked via `/acumen-reflect`
- Launches the reflector subagent
- Subagent reads observations, generates insights, writes to store
- Reports back with summary of findings

**Tests:** `tests/test_integration.py` (integration test with sample data)
- Feed sample observations, verify reflector prompt is well-formed
- Verify parsed insights have required fields
- Verify dedup works against existing insights

**Exit criteria:** Running `/acumen-reflect` produces ranked, deduplicated insights from observations.

---

## Step 5: Status & Insights Commands

User-facing slash commands.

**Files:**
- `commands/status.md` -- `/acumen-status` command
- `commands/insights.md` -- `/acumen-insights` command
- `commands/reflect.md` -- `/acumen-reflect` command
- `lib/formatter.py` -- formatting functions for CLI output

**Status command shows:**
- Sessions observed (count of unique session_ids)
- Total observations
- Active insights (count and top 5)
- Trends: observations per day, error rate over time
- Time since last reflection

**Insights command shows:**
- All insights, ranked by score
- Evidence count per insight
- Proposed action type (for Phase 2 preview)

**Reflect command:**
- Triggers the reflector subagent
- Shows progress and results

**Tests:** `tests/test_formatter.py`
- format_status with zero data shows "no data yet" message
- format_status with sample data shows correct trends
- format_insights with empty list shows "no insights"
- format_insights with sample insights shows ranked list

**Exit criteria:** All three commands work, output is clear and useful.

---

## Step 6: Integration Test & Polish

End-to-end test of the full pipeline.

**Files:**
- `tests/test_integration.py`
- `tests/fixtures/sample_observations.jsonl`

**Tests:**
- Feed 20 realistic observations through observe.sh
- Read them via store.py
- Score them via scorer.py
- Format status output via formatter.py
- Verify the full pipeline produces coherent output

**Exit criteria:** The complete observe -> store -> reflect -> score -> display loop works.

---

## Dependency Graph

```
Step 0 (scaffold)
  |
  v
Step 1 (observe.sh) ----+
  |                      |
  v                      v
Step 2 (store.py)    Step 3 (scorer.py)
  |                      |
  +----------+-----------+
             |
             v
Step 4 (reflector subagent)
             |
             v
Step 5 (commands + formatter)
             |
             v
Step 6 (integration test)
```

---

## What is NOT in Phase 1

- Auto-applying improvements to CLAUDE.md (Phase 2)
- Hook generation (Phase 2)
- Memory entry generation (Phase 2)
- Effectiveness measurement (Phase 2)
- User review flow `/acumen-review` (Phase 2)
- Skill synthesis (Phase 3)
- Global scope (Phase 3)
- Session scope -- real-time adaptation (Phase 3)
- Multi-agent support (Phase 4)
- Dashboard TUI (maybe never)
- Tool repair/kill (Toolwright's domain)
- MCP tools (unnecessary token overhead)

---

## Risk Assessment

| Risk | Mitigation |
|------|-----------|
| observe.sh adds latency | Shell script + jq append is <5ms |
| jq not installed | Fallback to raw shell JSON construction |
| LLM reflection returns garbage | Structured output format + graceful fallback |
| JSONL files grow large | Rotate daily, cap reads to last 7 days |
| User doesn't see value quickly | Status shows observation counts from session 1 |
| Privacy concerns | Metadata only, no file contents, no telemetry |
| Plugin system changes | Pin to current Claude Code plugin API |

---

## File Count Summary

| Category | Count | Files |
|----------|-------|-------|
| Plugin manifest | 1 | plugin.json |
| Hooks | 1 | observe.sh |
| Skills | 1 | reflect.md |
| Commands | 3 | status.md, insights.md, reflect.md |
| Agents | 1 | reflector.md |
| Python libs | 3 | store.py, scorer.py, formatter.py |
| Tests | 5 | test_store.py, test_scorer.py, test_formatter.py, test_observe_hook.py, test_integration.py |
| Config | 1 | conftest.py |
| **Total** | **16** | |

Down from ~40 in the original plan. Business logic: 3 Python files + 1 shell script.

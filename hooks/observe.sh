#!/usr/bin/env bash
# Acumen observation hook -- captures tool-use metadata only.
# Handles both PostToolUse (success) and PostToolUseFailure (error) events.
# Must be near-instant (<5ms).
# SECURITY: Never captures tool_input values or tool_response content.

# Fail-open: if jq isn't available, skip silently
command -v jq >/dev/null 2>&1 || exit 0

timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Single jq pass: extract metadata only, skip if tool_name missing.
# PostToolUse has tool_response; PostToolUseFailure has .error string instead.
obs=$(jq -c --arg ts "$timestamp" '
  select((.tool_name // "") != "") |
  {
    tool_name: .tool_name,
    session_id: (.session_id // "unknown"),
    timestamp: $ts,
    outcome: (
      if .hook_event_name == "PostToolUseFailure" then "error"
      elif .error != null then "error"
      else "success"
      end
    ),
    error_type: (
      if .hook_event_name == "PostToolUseFailure" then "tool_failure"
      elif .error != null then "tool_error"
      else null
      end
    ),
    error_message: (
      if .hook_event_name == "PostToolUseFailure" then (.error // null)
      elif .error != null then .error
      else null
      end
    )
  }
' 2>/dev/null) || exit 0

[ -z "$obs" ] && exit 0

mkdir -p ".acumen/observations"
echo "$obs" >> ".acumen/observations/$(date -u +%Y-%m-%d).jsonl"

#!/usr/bin/env bash
# Acumen observation hook -- captures tool-use metadata only.
# Handles both PostToolUse (success) and PostToolUseFailure (error) events.
# Must be near-instant (<5ms). Pure bash, zero external dependencies.
# SECURITY: Never captures tool_input values or tool_response content.

# Read all stdin
input=$(cat)
[ -z "$input" ] && exit 0

# Extract a JSON string value by key. Returns empty string if not found or null.
# Works for top-level flat keys in single-line JSON from Claude Code hooks.
_jval() {
  local key="\"$1\"" rest
  case "$input" in
    *"$key"*) ;;
    *) return ;;
  esac
  rest="${input#*$key}"
  rest="${rest#*:}"
  # Skip whitespace
  rest="${rest# }"
  # Check for null
  case "$rest" in
    null*) return ;;
  esac
  # Must start with quote
  case "$rest" in
    \"*) ;;
    *) return ;;
  esac
  rest="${rest#\"}"
  # Extract up to closing quote (handles simple strings, not escaped quotes)
  printf '%s' "${rest%%\"*}"
}

tool_name=$(_jval tool_name)
[ -z "$tool_name" ] && exit 0

session_id=$(_jval session_id)
: "${session_id:=unknown}"

hook_event=$(_jval hook_event_name)
error_msg=$(_jval error)

timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Determine outcome and error_type
if [ "$hook_event" = "PostToolUseFailure" ] || [ -n "$error_msg" ]; then
  outcome=error
  if [ "$hook_event" = "PostToolUseFailure" ]; then
    error_type=tool_failure
  else
    error_type=tool_error
  fi
  # Escape quotes in error message for JSON safety
  error_msg="${error_msg//\\/\\\\}"
  error_msg="${error_msg//\"/\\\"}"
  obs="{\"tool_name\":\"${tool_name}\",\"session_id\":\"${session_id}\",\"timestamp\":\"${timestamp}\",\"outcome\":\"${outcome}\",\"error_type\":\"${error_type}\",\"error_message\":\"${error_msg}\"}"
else
  obs="{\"tool_name\":\"${tool_name}\",\"session_id\":\"${session_id}\",\"timestamp\":\"${timestamp}\",\"outcome\":\"success\",\"error_type\":null,\"error_message\":null}"
fi

mkdir -p ".acumen/observations"
echo "$obs" >> ".acumen/observations/$(date -u +%Y-%m-%d).jsonl"

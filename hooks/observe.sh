#!/usr/bin/env bash
# Acumen observation hook — Tier 0.5 classification + per-session storage.
# Fires on PostToolUse and PostToolUseFailure.
# Delegates to Python for classification and storage (<100ms total).
# SECURITY: Python reads raw fields to derive categories, then discards them.
# Only categorical Tier 0.5 fields are persisted. Never raw commands/paths/errors.

input=$(cat)
[ -z "$input" ] && exit 0

# Quick check: bail if no tool_name in the input
case "$input" in
  *'"tool_name"'*) ;;
  *) exit 0 ;;
esac

# Delegate to classify.py which derives Tier 0.5 fields and writes per-session JSONL
echo "$input" | python3 "$(dirname "$0")/../lib/classify.py" 2>/dev/null

exit 0

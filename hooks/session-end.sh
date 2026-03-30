#!/usr/bin/env bash
# Acumen SessionEnd hook -- sets a flag if enough new observations exist.
# Must complete in <1.5s (SessionEnd timeout). Fail-open.

obs_dir=".acumen/observations"
insights=".acumen/insights.json"
flag=".acumen/should-reflect"
threshold=${ACUMEN_REFLECT_THRESHOLD:-10}

[ -d "$obs_dir" ] || exit 0

# Count observations newer than last reflection (insights.json mtime)
if [ -f "$insights" ]; then
  count=$(find "$obs_dir" -name '*.jsonl' -newer "$insights" -exec cat {} + 2>/dev/null | wc -l)
else
  count=$(cat "$obs_dir"/*.jsonl 2>/dev/null | wc -l)
fi

count=$(echo "$count" | tr -d ' ')
[ "$count" -ge "$threshold" ] 2>/dev/null && touch "$flag"
exit 0

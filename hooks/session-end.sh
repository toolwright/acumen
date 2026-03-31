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

# Retire harmful rules via v2.1 effectiveness data (fail-open)
plugin_root="${CLAUDE_PLUGIN_ROOT:-}"
if [ -n "$plugin_root" ] && [ -f "$plugin_root/lib/measure.py" ]; then
  python3 -c "
import sys; sys.path.insert(0, '$plugin_root/lib')
try:
    from pathlib import Path
    from store import resolve_scope_path
    from measure import read_effectiveness
    from apply import read_rules, save_rules, revert_rule
    scope = resolve_scope_path('project')
    records = read_effectiveness(scope)
    harmful = [r for r in records if r.verdict == 'harmful']
    if harmful:
        for h in harmful:
            revert_rule(scope, h.rule_id, Path('.'))
except Exception:
    pass
" 2>/dev/null || true
fi

exit 0

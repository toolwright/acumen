#!/usr/bin/env bash
# Acumen Stop hook -- checks evaluation signals before allowing the agent to stop.
# Single Python invocation for all logic. Fail-open on any error.
# Blocks only on NEW failures introduced this session (compares against baseline).

set -uo pipefail

input=$(cat 2>/dev/null || echo "{}")
plugin_root="${CLAUDE_PLUGIN_ROOT:-}"
[ -n "$plugin_root" ] || exit 0

result=$(python3 -c "
import sys, json, os
sys.path.insert(0, os.environ.get('CLAUDE_PLUGIN_ROOT', '') + '/lib')
data = {}
try:
    data = json.loads(sys.argv[1])
except Exception:
    pass

if data.get('stop_hook_active', False):
    print('ALLOW')
    sys.exit(0)

try:
    from evaluator import load_eval_config, run_eval_signal
    from pathlib import Path
    project_root = Path('.')
    config = load_eval_config(project_root)
    if not config or not config.fast_for_stop_gate:
        print('ALLOW')
        sys.exit(0)

    baseline_fail = 0
    bp = project_root / '.acumen' / 'session-baseline.json'
    if bp.exists():
        try:
            baseline_fail = json.loads(bp.read_text()).get('fail_count', 0)
        except Exception:
            pass

    sig = run_eval_signal(config, project_root)
    new_fail = sig.fail_count - baseline_fail
    if new_fail <= 0:
        print('ALLOW')
    else:
        print('BLOCK')
        print(new_fail)
        for d in sig.details[:5]:
            print(f'  - {d}')
except Exception:
    print('ALLOW')
" "$input" 2>/dev/null || echo "ALLOW")

first_line=$(printf '%s' "$result" | head -1)
if [ "$first_line" = "BLOCK" ]; then
  count=$(printf '%s' "$result" | sed -n '2p')
  details=$(printf '%s' "$result" | tail -n +3)
  printf "Acumen: stop blocked. %s new failure(s) since session start:\n%s\nFix the failures or describe what is still broken.\n" \
    "$count" "$details" >&2
  exit 2
fi

exit 0

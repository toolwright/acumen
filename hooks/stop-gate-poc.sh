#!/usr/bin/env bash
# hooks/stop-gate-poc.sh -- PoC only, validates Stop hook mechanism before production code
input=$(cat)
stop_hook_active=$(python3 -c "
import json, sys
try:
    d = json.loads(sys.argv[1])
    print('true' if d.get('stop_hook_active', False) else 'false')
except Exception:
    print('true')
" "$input" 2>/dev/null || echo "true")

if [ "$stop_hook_active" = "true" ]; then
  exit 0
fi

echo "Acumen stop-gate-poc: hook fires correctly. Say 'continue' to proceed." >&2
exit 2

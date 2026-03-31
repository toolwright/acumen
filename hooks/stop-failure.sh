#!/usr/bin/env bash
# Acumen StopFailure hook.
# Appends record to .acumen/stop-failures.jsonl so reflection pipeline can exclude API-error sessions.

input=$(cat 2>/dev/null || echo "{}")
mkdir -p ".acumen" 2>/dev/null || true

python3 -c "
import json, sys
from datetime import datetime, timezone
from pathlib import Path
try:
    d = json.loads(sys.argv[1])
    record = {
        'session_id': d.get('session_id', ''),
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'error': d.get('error', ''),
        'error_details': d.get('error_details', ''),
    }
    with open(Path('.acumen') / 'stop-failures.jsonl', 'a') as f:
        f.write(json.dumps(record) + '\n')
except Exception:
    pass
" "$input" 2>/dev/null || true

exit 0

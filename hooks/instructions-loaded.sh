#!/usr/bin/env bash
# Acumen InstructionsLoaded hook.
# Appends record to .acumen/rule-activity.jsonl showing which acumen rules entered context.

input=$(cat 2>/dev/null || echo "{}")
mkdir -p ".acumen" 2>/dev/null || true

python3 -c "
import json, sys
from datetime import datetime, timezone
from pathlib import Path
try:
    d = json.loads(sys.argv[1])
    files = d.get('files', [])
    session_id = d.get('session_id', '')
    acumen_rules = [
        Path(f).stem.removeprefix('acumen-')
        for f in files
        if '/acumen-' in f or Path(f).stem.startswith('acumen-')
    ]
    if not acumen_rules:
        sys.exit(0)
    record = {
        'session_id': session_id,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'rules_loaded': acumen_rules,
    }
    with open(Path('.acumen') / 'rule-activity.jsonl', 'a') as f:
        f.write(json.dumps(record) + '\n')
except Exception:
    pass
" "$input" 2>/dev/null || true

exit 0

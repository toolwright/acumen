---
name: acumen-status
description: Quick health overview — observations, rules, proposals, effectiveness, data quality.
---

# Acumen Status

Show a quick health overview of Acumen's current state.

## What to do

Run the following to display status:

```bash
python3 -c "
import sys, json
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/lib')
from pathlib import Path
from store import resolve_scope_path, read_observations
from apply import read_rules
from measure import read_effectiveness

scope = resolve_scope_path('project')

# 1. Observations
observations, corruption_count = read_observations(scope)
index_path = scope / 'observations' / 'index.json'
session_count = 0
if index_path.exists():
    try:
        session_count = len(json.loads(index_path.read_text()))
    except (json.JSONDecodeError, OSError):
        pass

# 2. Rules
rules = read_rules(scope)
active = [r for r in rules if r.get('status') == 'applied']
pending = [r for r in rules if r.get('status') == 'pending']
kinds = sorted({r.get('pattern_kind', 'unknown') for r in active}) if active else []

# 3. Effectiveness
verdicts = read_effectiveness(scope)

# Display
print('ACUMEN STATUS')
print()
print(f'  Observations: {len(observations)} events across {session_count} sessions (Tier 0.5)')
if corruption_count:
    print(f'  Data quality: {corruption_count} corrupted line(s) skipped')
print(f'  Active rules: {len(active)}' + (f' ({', '.join(kinds)})' if kinds else ''))
print(f'  Pending proposals: {len(pending)}')

if verdicts:
    icons = {'effective': '+', 'neutral': '~', 'harmful': '-', 'pending': '?'}
    print(f'  Effectiveness ({len(verdicts)} measured):')
    for v in verdicts:
        icon = icons.get(v.verdict, '?')
        print(f'    [{icon}] {v.rule_id}: {v.verdict} ({v.target_pattern_before:.1f} -> {v.target_pattern_after:.1f} per 100)')
else:
    print('  Effectiveness: no measurements yet')
"
```

Display the output to the user exactly as printed.

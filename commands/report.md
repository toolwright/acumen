---
name: acumen-report
description: Full report with failure reductions and convention adherence.
---

# Acumen Report

Show the full Acumen report: failures reduced, conventions learned, rule stats.

## What to do

Run the following to display the report:

```bash
python3 -c "
import sys, json
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/lib')
from pathlib import Path
from datetime import datetime, timezone
from store import resolve_scope_path, read_observations
from apply import read_rules
from measure import read_effectiveness, measure_convention_adherence

scope = resolve_scope_path('project')

# 1. Observations
observations, corruption_count = read_observations(scope, days=30)
index_path = scope / 'observations' / 'index.json'
session_count = 0
if index_path.exists():
    try:
        session_count = len(json.loads(index_path.read_text()))
    except (json.JSONDecodeError, OSError):
        pass

if not observations:
    print('ACUMEN REPORT')
    print()
    print('  No observation data yet. Work normally and check back after a few sessions.')
    sys.exit(0)

# 2. Rules
rules = read_rules(scope)
applied = [r for r in rules if r.get('status') == 'applied']
pending = [r for r in rules if r.get('status') == 'proposed']
rejected = [r for r in rules if r.get('status') == 'rejected']
reverted = [r for r in rules if r.get('status') == 'reverted']

failure_rules = [r for r in applied if r.get('type') == 'failure']
convention_rules = [r for r in applied if r.get('type') == 'convention']

# 3. Effectiveness for failure rules
verdicts = read_effectiveness(scope)
failure_verdicts = {v.rule_id: v for v in verdicts}

# 4. Convention adherence (compute live from observations)
conv_adherence = {}
for r in convention_rules:
    applied_at = r.get('applied', '')
    if not applied_at:
        continue
    after_obs = [o for o in observations if o.get('timestamp', '') >= applied_at]
    try:
        applied_dt = datetime.fromisoformat(applied_at.replace('Z', '+00:00'))
        days = (datetime.now(timezone.utc) - applied_dt).days
    except (ValueError, TypeError):
        days = 0
    conv_adherence[r['id']] = measure_convention_adherence(r, after_obs, days)

# 5. Project name from cwd
project = Path.cwd().name

# 6. Time span
timestamps = sorted(o.get('timestamp', '') for o in observations if o.get('timestamp'))
if timestamps:
    try:
        first = datetime.fromisoformat(timestamps[0].replace('Z', '+00:00'))
        span = (datetime.now(timezone.utc) - first).days
    except (ValueError, TypeError):
        span = 0
else:
    span = 0

# Display
print('ACUMEN REPORT')
print(f'  {project} ({span} days)')
print()

has_improvements = any(v.verdict == 'effective' for v in failure_verdicts.values()) or conv_adherence
if has_improvements:
    print('  YOUR AGENT IS SPECIALIZING')
else:
    print('  YOUR AGENT IS LEARNING')
print()

# Failure reductions
effective_failures = [(r, failure_verdicts[r['id']])
                      for r in failure_rules if r['id'] in failure_verdicts
                      and failure_verdicts[r['id']].verdict == 'effective']
if effective_failures:
    print('  Failures reduced:')
    for rule, v in effective_failures:
        label = f\"{rule.get('target_tool', '?')} {rule.get('trigger_class', '?')}\"
        reduction = 0
        if v.target_pattern_before > 0:
            reduction = (1 - v.target_pattern_after / v.target_pattern_before) * 100
        tool = rule.get('target_tool', '?')
        fam = ''
        if rule.get('pattern_kind') == 'python_launcher':
            fam = 'python'
        else:
            fam = tool
        print(f'    \"{label}\"')
        print(f'      Before: {v.target_pattern_before:.1f} per 100 {fam} calls')
        after_str = f'      After:  {v.target_pattern_after:.1f} per 100 {fam} calls'
        if reduction > 0:
            after_str += f'    down {reduction:.0f}%'
        print(after_str)
        print(f'      Rule: \"{rule.get(\"action\", \"\")}\"')
    print()

# Conventions learned
if conv_adherence:
    print('  Conventions learned:')
    for rule in convention_rules:
        rec = conv_adherence.get(rule['id'])
        if not rec:
            continue
        kind = rule.get('pattern_kind', '?')
        action = rule.get('action', '')
        rate = rec.adherence_rate if rec.adherence_rate is not None else 0.0
        print(f'    {kind}: \"{action}\"')
        print(f'      adherence: {rate:.0f}%')
    print()

# Rule summary
print(f'  {len(applied)} rules active | {len(pending)} pending | {len(reverted)} reverted')
print()
print(f'  Observation: Tier 0.5 (categorical)')
print(f'  Sessions observed: {session_count} | Events: {len(observations):,}')
if corruption_count:
    print(f'  Data quality: {corruption_count} corrupted line(s) skipped')
"
```

Display the output to the user exactly as printed.

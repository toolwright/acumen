---
name: acumen-effectiveness
description: Show effectiveness verdicts for applied Acumen rules, with eval confidence labels.
---

Run the following to display effectiveness of applied rules:

```python
python3 -c "
import sys; sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/lib')
from pathlib import Path
from store import resolve_scope_path, read_observations
from improver import read_proposals, measure_effectiveness_with_confidence

scope = resolve_scope_path('project')
proposals = read_proposals(scope)
observations = read_observations(scope, days=30)
changed = measure_effectiveness_with_confidence(proposals, observations, Path('.'))

applied = [p for p in proposals if p.get('status') in ('auto-applied', 'approved')]
if not applied:
    print('No applied rules yet. Run /acumen-reflect to generate proposals.')
    import sys; sys.exit(0)

print(f'Rule effectiveness ({len(applied)} rules):')
icons = {'effective': '[+]', 'neutral': '[~]', 'harmful': '[-]', 'pending': '[?]'}
for p in applied:
    verdict = p.get('effectiveness', 'pending')
    confidence = p.get('eval_confidence', 'LOW')
    icon = icons.get(verdict, '[?]')
    print(f'  {icon} [{confidence}] {p[\"description\"]}')

if any(p.get('effectiveness') not in ('effective', 'neutral', 'harmful') for p in applied):
    print()
    print('  [?] = pending (need 5+ observations before and after)')
"
```

---
name: acumen-review
description: View auto-applied Acumen improvements and revert any you disagree with.
---

# Acumen Review

View what Acumen has auto-applied and let the user revert anything they disagree with.

## What to do

1. List all auto-applied rules and memory entries:

```bash
python3 -c "
import sys, json
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/lib')
from store import resolve_scope_path
from improver import read_proposals

scope = resolve_scope_path('project')
proposals = read_proposals(scope)
applied = [p for p in proposals if p.get('status') in ('approved', 'auto-applied')]
if not applied:
    print('No applied improvements. Run /acumen-reflect first.')
else:
    print(f'{len(applied)} applied improvement(s):\n')
    for i, p in enumerate(applied, 1):
        target = 'Rule (.claude/rules/)' if p['target'] == 'rule' else 'Memory (.claude/memory/acumen/)'
        print(f'{i}. [{p[\"target\"].upper()}] {p[\"description\"]}')
        print(f'   Target: {target}')
        print(f'   Status: {p[\"status\"]}')
        print()
print(json.dumps(proposals))
"
```

2. Show the applied improvements to the user in a clear, numbered format.

3. Ask the user: **Would you like to revert any of these?** (they can pick by number, or say "none")

4. For each improvement the user wants to revert, delete the corresponding file:

```bash
python3 -c "
import sys, json, re
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/lib')
from improver import _slugify
from pathlib import Path

proposal = json.loads(sys.argv[1])
slug = _slugify(proposal['description'])

if proposal['target'] == 'rule':
    path = Path('.claude/rules') / f'acumen-{slug}.md'
else:
    path = Path('.claude/memory/acumen') / f'{slug}.md'

if path.exists():
    path.unlink()
    print(f'Reverted: {path}')
else:
    print(f'File already removed: {path}')
" '$PROPOSAL_JSON'
```

5. Update the proposal status to `"reverted"` in proposals.json:

```bash
python3 -c "
import sys, json
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/lib')
from store import resolve_scope_path
from pathlib import Path

scope = resolve_scope_path('project')
proposals = json.loads(sys.argv[1])
(scope / 'proposals.json').write_text(json.dumps(proposals, indent=2))
print('Proposals updated.')
" '$UPDATED_PROPOSALS_JSON'
```

6. Report what was reverted and what remains active.

## When there are no applied improvements

If no applied improvements exist, tell the user:

> No applied improvements yet. Run `/acumen-reflect` to analyze recent sessions -- improvements will be auto-applied automatically.

---
name: acumen-review
description: View auto-applied Acumen improvements, revert any you disagree with, or promote proven rules to global scope.
---

# Acumen Review

View what Acumen has auto-applied, revert anything you disagree with, and promote proven environment-level rules to global scope (applies across all your projects).

## What to do

1. List all auto-applied rules, memory entries, and global promotion candidates:

```bash
python3 -c "
import sys, json
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/lib')
from store import resolve_scope_path
from improver import read_proposals

scope = resolve_scope_path('project')
proposals = read_proposals(scope)
applied = [p for p in proposals if p.get('status') in ('approved', 'auto-applied')]
global_candidates = [p for p in applied if p.get('scope') == 'global_candidate' and p.get('scope') != 'global']

if not applied:
    print('No applied improvements. Run /acumen-reflect first.')
else:
    print(f'{len(applied)} applied improvement(s):\n')
    for i, p in enumerate(applied, 1):
        target = 'Rule (.claude/rules/)' if p['target'] == 'rule' else 'Memory (.claude/memory/acumen/)'
        effectiveness = f' [{p[\"effectiveness\"].upper()}]' if p.get('effectiveness') else ''
        print(f'{i}. [{p[\"target\"].upper()}]{effectiveness} {p[\"description\"]}')
        print(f'   Target: {target}')
        print()

    if global_candidates:
        print('GLOBAL PROMOTION CANDIDATES (would apply across all your projects):')
        for p in global_candidates:
            proven = ' -- proven effective' if p.get('effectiveness') == 'effective' else ''
            print(f'  * {p[\"description\"]}{proven}')
        print()

print(json.dumps(proposals))
"
```

2. Show the applied improvements to the user in a clear, numbered format. If there are global promotion candidates, explain: these are environment-level rules that would apply across all your projects if promoted.

3. Ask the user: **Would you like to (a) revert any of these, (b) promote any global candidates to apply across all projects, or (c) neither?**

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

## Promoting a rule to global scope

For each rule the user wants to promote globally, run:

```bash
python3 -c "
import sys, json
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/lib')
from store import resolve_scope_path
from improver import promote_to_global
from pathlib import Path

proposal = json.loads(sys.argv[1])
path = promote_to_global(proposal)
print(f'Promoted to global: {path}')
print('This rule will now apply in all your projects.')
" '$PROPOSAL_JSON'
```

Then update proposals.json with the modified proposal (scope='global', promoted_at set):

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

## When there are no applied improvements

If no applied improvements exist, tell the user:

> No applied improvements yet. Run `/acumen-reflect` to analyze recent sessions -- improvements will be auto-applied automatically.

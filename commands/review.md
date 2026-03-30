---
name: acumen-review
description: View auto-applied Acumen improvements, revert any you disagree with, or promote proven rules to global scope.
---

# Acumen Review

View what Acumen has auto-applied, revert anything you disagree with, and promote proven environment-level rules to global scope (applies across all your projects).

## What to do

1. List all applied improvements:

```bash
python3 -c "
import sys, json
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/lib')
from store import resolve_scope_path
from improver import read_proposals
from formatter import format_review

scope = resolve_scope_path('project')
proposals = read_proposals(scope)
print(format_review(proposals))
"
```

2. Show the output to the user. Ask: **Would you like to (a) revert any of these, (b) promote any global candidates to apply across all projects, or (c) neither?**

3. For each improvement the user wants to revert:

```bash
python3 -c "
import sys, json
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/lib')
from pathlib import Path
from store import resolve_scope_path
from improver import read_proposals, revert_proposal

scope = resolve_scope_path('project')
proposals = read_proposals(scope)

# Revert the Nth proposal (1-indexed, from the applied list)
n = int(sys.argv[1])
applied = [p for p in proposals if p.get('status') in ('approved', 'auto-applied')]
msg = revert_proposal(Path('.'), applied[n - 1])
print(msg)

# Write updated proposals back
import tempfile
fd, tmp = tempfile.mkstemp(dir=scope, suffix='.tmp')
with open(fd, 'w') as f:
    json.dump(proposals, f, indent=2)
Path(tmp).replace(scope / 'proposals.json')
" '$NUMBER'
```

4. Report what was reverted.

## Promoting a rule to global scope

For each rule the user wants to promote globally:

```bash
python3 -c "
import sys, json, tempfile
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/lib')
from pathlib import Path
from store import resolve_scope_path
from improver import read_proposals, promote_to_global

scope = resolve_scope_path('project')
proposals = read_proposals(scope)

# Promote the global candidate by description match
desc = sys.argv[1]
for p in proposals:
    if p['description'] == desc and p.get('scope') == 'global_candidate':
        path = promote_to_global(p)
        print(f'Promoted to global: {path}')
        print('This rule will now apply in all your projects.')
        break

# Write updated proposals back
fd, tmp = tempfile.mkstemp(dir=scope, suffix='.tmp')
with open(fd, 'w') as f:
    json.dump(proposals, f, indent=2)
Path(tmp).replace(scope / 'proposals.json')
" '$DESCRIPTION'
```

## When there are no applied improvements

If no applied improvements exist, tell the user:

> No applied improvements yet. Run `/acumen-reflect` to analyze recent sessions -- improvements will be auto-applied automatically.

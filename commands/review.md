---
name: acumen-review
description: Review pending Acumen improvement proposals -- approve or reject each one.
---

# Acumen Review

Review and approve/reject pending improvement proposals generated from insights.

## What to do

1. Load proposals:

```bash
python3 -c "
import sys, json
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/lib')
from store import resolve_scope_path
from improver import read_proposals

scope = resolve_scope_path('project')
proposals = read_proposals(scope)
if not proposals:
    print('No pending proposals. Run /acumen-reflect first to generate insights, then run this command again.')
else:
    pending = [p for p in proposals if p.get('status') == 'proposed']
    if not pending:
        print('All proposals have been reviewed. No pending items.')
    else:
        print(f'{len(pending)} pending proposal(s):\n')
        for i, p in enumerate(pending, 1):
            target = 'Rule (.claude/rules/)' if p['target'] == 'rule' else 'Memory (.claude/memory/acumen/)'
            print(f'{i}. [{p[\"target\"].upper()}] {p[\"description\"]}')
            print(f'   Target: {target}')
            print(f'   Proposed text:')
            for line in p.get('rule_text', '').splitlines():
                print(f'     {line}')
            print()
print(json.dumps(proposals))
"
```

2. Show the pending proposals to the user in a clear format.

3. For each pending proposal, ask the user: **Approve or Reject?**

4. For approved proposals, apply them:

```bash
python3 -c "
import sys, json
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/lib')
from store import resolve_scope_path
from improver import apply_proposal

project_root = '.'
proposal = json.loads(sys.argv[1])
proposal['status'] = 'approved'
path = apply_proposal(project_root, proposal)
print(f'Applied: {path}')
" '$PROPOSAL_JSON'
```

5. After processing all proposals, update their statuses in proposals.json:

```bash
python3 -c "
import sys, json
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/lib')
from store import resolve_scope_path
from improver import read_proposals, write_proposal
from pathlib import Path

scope = resolve_scope_path('project')
# Rewrite proposals.json with updated statuses
proposals_path = scope / 'proposals.json'
proposals = json.loads(sys.argv[1])
proposals_path.write_text(json.dumps(proposals, indent=2))
print('Proposals updated.')
" '$UPDATED_PROPOSALS_JSON'
```

6. Report to the user how many were approved, rejected, and what files were created.

## When there are no proposals

If no proposals exist, tell the user:

> No pending proposals. Run `/acumen-reflect` to analyze recent sessions, then `/acumen-review` to review the generated improvement proposals.

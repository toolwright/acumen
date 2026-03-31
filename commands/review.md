---
name: acumen-review
description: Review pending Acumen proposals — approve to apply as rules, reject to dismiss, or revert applied rules.
---

# Acumen Review

Review pending proposals, approve or reject them, and manage applied rules.

## What to do

### 1. Load pending proposals

```bash
python3 -c "
import sys, json
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/lib')
from store import resolve_scope_path
from apply import read_rules

scope = resolve_scope_path('project')
rules = read_rules(scope)
pending = [r for r in rules if r['status'] == 'proposed']
applied = [r for r in rules if r['status'] == 'applied']

if not pending and not applied:
    print('NO_DATA')
elif not pending:
    print('NO_PENDING')
    print(f'{len(applied)} rules currently applied.')
else:
    print(f'PENDING:{len(pending)}')
    for i, r in enumerate(pending, 1):
        conf = f\"{r['confidence']:.0%}\"
        print(f\"  {i}. [{r['pattern_kind']}] {r['action']}\")
        print(f\"     Evidence: {r['evidence_summary']} (confidence: {conf})\")
        print()
    if applied:
        print(f'{len(applied)} rules currently applied.')
"
```

### 2. Handle results

**If output is `NO_DATA`:**
> No proposals or applied rules yet. Run `/acumen-reflect` to analyze recent sessions and generate proposals.

**If output is `NO_PENDING`:**
Show the applied rule count, then ask: **Would you like to revert any applied rules?**

**If output starts with `PENDING`:**
Show the proposals to the user exactly as printed. For each pending proposal, ask the user: **Approve or reject?**

### 3. Apply approved proposals

For each proposal the user approves:

```bash
python3 -c "
import sys, json
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/lib')
from pathlib import Path
from store import resolve_scope_path
from apply import read_rules, apply_rule

scope = resolve_scope_path('project')
rules = read_rules(scope)
pending = [r for r in rules if r['status'] == 'proposed']

rule = pending[int(sys.argv[1]) - 1]
path = apply_rule(scope, rule, Path('.'))
print(f'Applied: {path}')
" '$NUMBER'
```

### 4. Reject declined proposals

For each proposal the user rejects:

```bash
python3 -c "
import sys, json
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/lib')
from store import resolve_scope_path
from apply import read_rules, reject_rule

scope = resolve_scope_path('project')
rules = read_rules(scope)
pending = [r for r in rules if r['status'] == 'proposed']

rule_id = pending[int(sys.argv[1]) - 1]['id']
reject_rule(scope, rule_id)
print(f'Rejected proposal {sys.argv[1]}.')
" '$NUMBER'
```

### 5. Revert applied rules

If the user wants to revert an applied rule:

```bash
python3 -c "
import sys
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/lib')
from pathlib import Path
from store import resolve_scope_path
from apply import read_rules, revert_rule

scope = resolve_scope_path('project')
rules = read_rules(scope)
applied = [r for r in rules if r['status'] == 'applied']

rule = applied[int(sys.argv[1]) - 1]
ok = revert_rule(scope, rule['id'], Path('.'))
if ok:
    print(f\"Reverted: {rule['action']}\")
else:
    print('Rule file not found — may have been manually removed.')
" '$NUMBER'
```

### 6. Show summary

After processing all decisions, show:

> **N approved, M rejected, K remaining**

## When there are no proposals

If `.acumen/rules.json` doesn't exist or has no proposals, tell the user:

> No proposals yet. Run `/acumen-reflect` to analyze recent sessions and generate proposals.

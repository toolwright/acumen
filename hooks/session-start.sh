#!/usr/bin/env bash
# Acumen SessionStart hook -- if should-reflect flag exists, inject context
# telling the agent to run /acumen-reflect. Fail-open.

flag=".acumen/should-reflect"

[ -f "$flag" ] || exit 0

rm -f "$flag"

# stdout becomes additionalContext shown to the agent
cat <<'EOF'
Acumen has collected enough new observations since your last reflection.
Please do the following:
1. Run /acumen-reflect to extract insights and generate improvement proposals.
2. Auto-apply all proposals by running:
   ```python3
   python3 -c "
   import sys, json; sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/lib')
   from store import resolve_scope_path
   from improver import read_proposals, auto_apply_proposals
   from pathlib import Path
   scope = resolve_scope_path('project')
   proposals = read_proposals(scope)
   applied = auto_apply_proposals(Path('.'), proposals)
   # Update proposals.json with new statuses
   (scope / 'proposals.json').write_text(json.dumps(proposals, indent=2))
   for a in applied:
       t = 'Rule' if a['target'] == 'rule' else 'Memory'
       print(f'  [{t}] {a[\"description\"]}')
   if not applied: print('  No new proposals to apply.')
   "
   ```
3. Notify the user what was applied. Example:
   "Acumen auto-applied N improvements (M rules, K memory entries). Run /acumen-review to see details or revert any."
EOF
exit 0

#!/usr/bin/env bash
# Acumen SessionStart hook -- two jobs:
# 1. If should-reflect flag exists, tell agent to run /acumen-reflect
# 2. If recent improvements exist, show brief summary to user
# Fail-open. Pure bash.

acumen_dir=".acumen"
flag="$acumen_dir/should-reflect"

# --- Job 1: Trigger reflection if flagged ---
if [ -f "$flag" ]; then
  rm -f "$flag"
  cat <<'REFLECT_EOF'
Acumen has collected enough new observations since your last reflection.
Please do the following:
1. Run /acumen-reflect to extract insights and generate improvement proposals.
2. Auto-apply all proposals by running:
   ```python3
   python3 -c "
   import sys, json; sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/lib')
   from store import resolve_scope_path
   from improver import read_proposals, auto_apply_proposals, expire_stale_proposals
   from pathlib import Path
   scope = resolve_scope_path('project')
   proposals = read_proposals(scope)
   expire_stale_proposals(proposals)
   applied = auto_apply_proposals(Path('.'), proposals)
   (scope / 'proposals.json').write_text(json.dumps(proposals, indent=2))
   for a in applied:
       print(f'  [RULE] {a[\"description\"]}')
   if not applied: print('  No new proposals to apply.')
   "
   ```
3. Notify the user what was applied. Example:
   "Acumen auto-applied N rules. Run /acumen-review to see details or revert any."
REFLECT_EOF
  exit 0
fi

# --- Job 2: Show improvement summary if recent rules exist ---
# Only if not in reflection mode (avoid double output)
rules_dir=".claude/rules"
if [ -d "$rules_dir" ]; then
  count=$(ls -1 "$rules_dir"/acumen-*.md 2>/dev/null | wc -l | tr -d ' ')
  if [ "$count" -gt 0 ]; then
    echo "Acumen: $count active rule(s) improving your agent. Run /acumen-status for details."
  fi
fi

exit 0

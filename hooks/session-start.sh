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
Run /acumen-reflect now, then run /acumen-review to approve or reject proposals.
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

# --- Job 3: Detect evaluation signal + capture session baseline ---
# One Python call: build/load eval config, then run baseline if tests are fast.
# Rebuilds config once per 24h. Fail-open.
plugin_root="${CLAUDE_PLUGIN_ROOT:-}"
if [ -n "$plugin_root" ] && [ -f "$plugin_root/lib/evaluator.py" ]; then
  python3 -c "
import sys, json, time, tempfile
sys.path.insert(0, '$plugin_root/lib')
try:
    from evaluator import build_eval_config, save_eval_config, load_eval_config, run_eval_signal
    from pathlib import Path
    project_root = Path('.')
    config_path = project_root / '.acumen' / 'eval-config.json'
    should_rebuild = not config_path.exists()
    if not should_rebuild:
        should_rebuild = time.time() - config_path.stat().st_mtime > 86400
    if should_rebuild:
        config = build_eval_config(project_root)
        save_eval_config(config, project_root)
    else:
        config = load_eval_config(project_root)
    if config and config.fast_for_stop_gate:
        result = run_eval_signal(config, project_root)
        acumen_dir = project_root / '.acumen'
        acumen_dir.mkdir(parents=True, exist_ok=True)
        baseline = json.dumps({'pass_count': result.pass_count, 'fail_count': result.fail_count})
        fd, tmp = tempfile.mkstemp(dir=str(acumen_dir), suffix='.tmp')
        with open(fd, 'w') as f: f.write(baseline)
        Path(tmp).replace(acumen_dir / 'session-baseline.json')
except Exception:
    pass
" 2>/dev/null || true
fi

exit 0

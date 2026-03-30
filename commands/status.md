---
name: acumen-status
description: Show Acumen observation stats, error trends, and top insights.
---

# Acumen Status

Show current observation and insight stats.

## What to do

Run the formatter to display status:

```bash
python3 -c "
import sys
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/lib')
from pathlib import Path
from store import resolve_scope_path, read_observations, read_insights
from formatter import format_status

scope = resolve_scope_path('project')
observations = read_observations(scope)
insights = read_insights(scope)

last_reflection = None
insights_path = scope / 'insights.json'
if insights_path.exists():
    from datetime import datetime
    mtime = insights_path.stat().st_mtime
    last_reflection = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')

print(format_status(observations, insights, last_reflection, project_root=Path('.')))
"
```

Display the output to the user exactly as printed.

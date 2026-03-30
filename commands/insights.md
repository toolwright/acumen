---
name: acumen-insights
description: View all Acumen insights ranked by confidence and impact score.
---

# Acumen Insights

Show all extracted insights, ranked by score.

## What to do

Run the formatter to display insights:

```bash
python3 -c "
import sys
sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/lib')
from store import resolve_scope_path, read_insights
from scorer import rank_insights
from formatter import format_insights

scope = resolve_scope_path('project')
insights = rank_insights(read_insights(scope))
print(format_insights(insights))
"
```

Display the output to the user exactly as printed.

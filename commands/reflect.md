---
name: acumen-reflect
description: Trigger a reflection over recent sessions to extract insights and generate rule proposals.
---

# Acumen Reflect

Trigger the reflector to analyze recent observations, generate rule proposals, and measure effectiveness.

## What to do

1. Launch the `acumen-reflector` agent with this task:

> Run the deterministic pipeline first (cluster failures, generate proposals, measure effectiveness), then read all observation files from `.acumen/observations/` (last 7 days of JSONL data). Also read `.acumen/insights.json` if it exists (these are prior insights to avoid duplicates). Analyze the observations for non-obvious patterns: correlated failures, retry loops, recovery patterns, and sequence patterns. For each pattern with 3+ supporting observations, produce an insight in the required JSON format. Then run the scoring and storage pipeline as described in your instructions to write ranked, deduplicated insights to `.acumen/insights.json`. Print a summary when done.

2. After the reflector finishes, show the user:
   - Pipeline results: clusters found, proposals generated, effectiveness verdicts
   - How many observations were analyzed
   - How many new insights were found
   - Top insights by score (if any)

## When there's no data

If `.acumen/observations/` doesn't exist or is empty, tell the user:

> No observation data found yet. Acumen collects data as you work. Check back after a few sessions.

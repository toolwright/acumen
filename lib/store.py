"""Read/write observation and insight data. Stdlib only (json, pathlib)."""

import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path


def resolve_scope_path(scope: str = "project") -> Path:
    """Return the base directory for the given scope."""
    if scope == "project":
        return Path(".acumen")
    if scope == "global":
        return Path.home() / ".claude" / "acumen"
    raise ValueError(f"Unknown scope: {scope!r}. Use 'project' or 'global'.")


def read_observations(scope_path: Path, days: int = 7) -> list[dict]:
    """Read JSONL observation files from scope_path/observations/, last N days."""
    obs_dir = scope_path / "observations"
    if not obs_dir.is_dir():
        return []

    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    results = []
    for f in sorted(obs_dir.glob("*.jsonl")):
        # Filename is YYYY-MM-DD.jsonl; skip files older than cutoff
        date_str = f.stem
        if date_str < cutoff:
            continue
        for line in f.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                results.append(json.loads(line))
            except json.JSONDecodeError:
                print(f"warning: skipping corrupted line in {f.name}", file=sys.stderr)
    return results


def read_insights(scope_path: Path) -> list[dict]:
    """Read insights.json, return list of dicts. Empty list if missing/corrupted."""
    path = scope_path / "insights.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, ValueError):
        return []


def write_insight(scope_path: Path, insight: dict) -> None:
    """Append an insight to insights.json. Uses write-tmp-rename for atomicity."""
    scope_path.mkdir(parents=True, exist_ok=True)
    path = scope_path / "insights.json"

    existing = read_insights(scope_path)
    existing.append(insight)

    # Atomic write: write to temp file in same dir, then rename
    fd, tmp = tempfile.mkstemp(dir=scope_path, suffix=".tmp")
    try:
        with open(fd, "w") as f:
            json.dump(existing, f, indent=2)
        Path(tmp).replace(path)
    except Exception:
        Path(tmp).unlink(missing_ok=True)
        raise

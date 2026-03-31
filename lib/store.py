"""Read/write observation and insight data. Stdlib only (json, pathlib, fcntl)."""

from __future__ import annotations

import fcntl
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


def _is_date_filename(stem: str) -> bool:
    return len(stem) == 10 and stem[4:5] == "-" and stem[7:8] == "-"


def read_observations(scope_path: Path, days: int = 7) -> tuple[list[dict], int]:
    """Read JSONL observation files from scope_path/observations/, last N days.

    Handles both date-based (YYYY-MM-DD.jsonl) and session-based (<session_id>.jsonl) files.
    Date files are filtered by filename; session files are filtered by record timestamp.
    Returns (observations, error_count) where error_count is corrupted lines skipped.
    """
    obs_dir = scope_path / "observations"
    if not obs_dir.is_dir():
        return [], 0

    cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    cutoff_ts = cutoff_date + "T00:00:00"
    results = []
    error_count = 0

    for f in sorted(obs_dir.glob("*.jsonl")):
        is_date = _is_date_filename(f.stem)
        if is_date and f.stem < cutoff_date:
            continue

        for line in f.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                error_count += 1
                print(f"warning: skipping corrupted line in {f.name}", file=sys.stderr)
                continue
            # For session files, filter by record timestamp
            if not is_date:
                ts = record.get("timestamp", "")
                if ts and ts < cutoff_ts:
                    continue
            results.append(record)
    return results, error_count


def append_observation(scope_path: Path, session_id: str, obs: dict) -> None:
    """Append an observation to the per-session JSONL file."""
    obs_dir = scope_path / "observations"
    obs_dir.mkdir(parents=True, exist_ok=True)
    with open(obs_dir / f"{session_id}.jsonl", "a") as f:
        f.write(json.dumps(obs, separators=(",", ":")) + "\n")


def read_last_observation(scope_path: Path, session_id: str) -> dict | None:
    """Read the last valid observation from a session file (for burst tracking)."""
    filepath = scope_path / "observations" / f"{session_id}.jsonl"
    if not filepath.exists():
        return None
    for line in reversed(filepath.read_text().splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    return None


def update_index(scope_path: Path, session_id: str, timestamp: str) -> None:
    """Update the observation index with session metadata. Atomic + locked."""
    obs_dir = scope_path / "observations"
    obs_dir.mkdir(parents=True, exist_ok=True)
    index_path = obs_dir / "index.json"
    lock_path = obs_dir / ".index.lock"

    with open(lock_path, "w") as lock_f:
        fcntl.flock(lock_f, fcntl.LOCK_EX)
        try:
            index = {}
            if index_path.exists():
                try:
                    index = json.loads(index_path.read_text())
                except (json.JSONDecodeError, OSError):
                    index = {}

            entry = index.get(session_id, {})
            entry["path"] = f"{session_id}.jsonl"
            entry.setdefault("first_seen", timestamp)
            entry["last_seen"] = timestamp
            index[session_id] = entry

            tmp = index_path.with_suffix(".tmp")
            tmp.write_text(json.dumps(index, indent=2))
            tmp.rename(index_path)
        finally:
            fcntl.flock(lock_f, fcntl.LOCK_UN)


def rotate_observations(scope_path: Path, max_age_days: int = 30) -> int:
    """Archive session files older than max_age_days. Returns count of archived."""
    obs_dir = scope_path / "observations"
    index_path = obs_dir / "index.json"
    if not index_path.exists():
        return 0

    try:
        index = json.loads(index_path.read_text())
    except (json.JSONDecodeError, OSError):
        return 0

    cutoff = (datetime.now(timezone.utc) - timedelta(days=max_age_days)).isoformat()
    archive_dir = obs_dir / "archive"
    archived = 0
    to_remove = []

    for session_id, entry in index.items():
        if entry.get("last_seen", "") < cutoff:
            src = obs_dir / entry["path"]
            if src.exists():
                archive_dir.mkdir(parents=True, exist_ok=True)
                src.rename(archive_dir / src.name)
                archived += 1
            to_remove.append(session_id)

    if to_remove:
        for sid in to_remove:
            del index[sid]
        tmp = index_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(index, indent=2))
        tmp.rename(index_path)

    return archived


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

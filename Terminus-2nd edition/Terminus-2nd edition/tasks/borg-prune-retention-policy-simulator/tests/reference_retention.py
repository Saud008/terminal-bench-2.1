#!/usr/bin/env python3
"""Independent Borg list retention oracle for verifier (not used by /app toolchain)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


UTC = timezone.utc


@dataclass(frozen=True)
class Archive:
    name: str
    ts: datetime
    bytes: int
    segments: int
    line: int


def parse_ts(value: str) -> datetime:
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


def parse_list_text(text: str) -> list[Archive]:
    """Parse tab-separated borg list fixtures; duplicate names: last line wins."""
    by_name: dict[str, Archive] = {}
    line_no = 0
    for raw in text.splitlines():
        line_no += 1
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 4:
            raise ValueError(f"bad list line {line_no}: {raw!r}")
        name, ts_s, size_s, seg_s = parts[0], parts[1], parts[2], parts[3]
        arch = Archive(
            name=name,
            ts=parse_ts(ts_s),
            bytes=int(size_s),
            segments=int(seg_s),
            line=line_no,
        )
        by_name[name] = arch
    return sorted(by_name.values(), key=lambda a: (a.ts, a.line))


def parse_list_file(path: Path) -> list[Archive]:
    return parse_list_text(path.read_text(encoding="utf-8"))


def normalize_ts(archive_ts: datetime, reference_now: datetime, skew_sec: int) -> tuple[datetime, bool]:
    limit = reference_now + timedelta(seconds=skew_sec)
    if archive_ts > limit:
        return reference_now, True
    return archive_ts, False


def is_held(name: str, holds: dict[str, Any]) -> bool:
    if name in holds.get("exact", []):
        return True
    for prefix in holds.get("prefix", []):
        if name.startswith(prefix):
            return True
    return False


def week_start_date(d: date, week_start: str) -> date:
    if week_start == "monday":
        return d - timedelta(days=d.weekday())
    # sunday-start week
    return d - timedelta(days=(d.weekday() + 1) % 7)


def bucket_keys(reference_now: datetime, keep: int, granularity: str, week_start: str) -> list:
    keys: list = []
    cursor = reference_now.date()
    if granularity == "daily":
        for i in range(keep):
            keys.append(cursor - timedelta(days=i))
    elif granularity == "weekly":
        seen: set[date] = set()
        probe = cursor
        while len(seen) < keep:
            wk = week_start_date(probe, week_start)
            if wk not in seen:
                seen.add(wk)
                keys.append(wk)
            probe -= timedelta(days=7)
    elif granularity == "monthly":
        y, m = cursor.year, cursor.month
        for _ in range(keep):
            keys.append((y, m))
            m -= 1
            if m == 0:
                m = 12
                y -= 1
    elif granularity == "yearly":
        y = cursor.year
        for _ in range(keep):
            keys.append(y)
            y -= 1
    else:
        raise ValueError(granularity)
    return keys


def archive_day_key(ts: datetime) -> date:
    return ts.date()


def archive_week_key(ts: datetime, week_start: str) -> date:
    return week_start_date(ts.date(), week_start)


def archive_month_key(ts: datetime) -> tuple[int, int]:
    return (ts.year, ts.month)


def archive_year_key(ts: datetime) -> int:
    return ts.year


def pick_newest(candidates: list[Archive], normalized: dict[str, datetime]) -> Archive | None:
    if not candidates:
        return None
    return max(candidates, key=lambda a: (normalized[a.name], a.line))


def evaluate_retention(
    archives: list[Archive],
    policy: dict[str, Any],
    holds: dict[str, Any],
    reference_now: datetime,
) -> dict[str, Any]:
    if reference_now.tzinfo is None:
        reference_now = reference_now.replace(tzinfo=UTC)
    else:
        reference_now = reference_now.astimezone(UTC)

    skew = int(policy.get("clock_skew_sec", 0))
    week_start = policy.get("week_start", "monday")

    normalized: dict[str, datetime] = {}
    clock_skew_adjusted: list[str] = []
    for arch in archives:
        nts, adjusted = normalize_ts(arch.ts, reference_now, skew)
        normalized[arch.name] = nts
        if adjusted:
            clock_skew_adjusted.append(arch.name)

    kept: set[str] = set()
    legal_hold_kept: list[str] = []
    for arch in archives:
        if is_held(arch.name, holds):
            kept.add(arch.name)
            legal_hold_kept.append(arch.name)

    bucket_hits: dict[str, list[str]] = {"daily": [], "weekly": [], "monthly": [], "yearly": []}

    for day in bucket_keys(reference_now, int(policy["keep_daily"]), "daily", week_start):
        cands = [a for a in archives if archive_day_key(normalized[a.name]) == day]
        best = pick_newest(cands, normalized)
        if best:
            kept.add(best.name)
            bucket_hits["daily"].append(best.name)

    for wk in bucket_keys(reference_now, int(policy["keep_weekly"]), "weekly", week_start):
        cands = [a for a in archives if archive_week_key(normalized[a.name], week_start) == wk]
        best = pick_newest(cands, normalized)
        if best:
            kept.add(best.name)
            bucket_hits["weekly"].append(best.name)

    for month in bucket_keys(reference_now, int(policy["keep_monthly"]), "monthly", week_start):
        cands = [a for a in archives if archive_month_key(normalized[a.name]) == month]
        best = pick_newest(cands, normalized)
        if best:
            kept.add(best.name)
            bucket_hits["monthly"].append(best.name)

    for year in bucket_keys(reference_now, int(policy["keep_yearly"]), "yearly", week_start):
        cands = [a for a in archives if archive_year_key(normalized[a.name]) == year]
        best = pick_newest(cands, normalized)
        if best:
            kept.add(best.name)
            bucket_hits["yearly"].append(best.name)

    all_names = {a.name for a in archives}
    pruned = sorted(all_names - kept)
    kept_sorted = sorted(kept)

    pruned_archives = [a for a in archives if a.name in pruned]
    compaction_bytes = sum(a.bytes for a in pruned_archives)
    compaction_segments = sum(a.segments for a in pruned_archives)

    return {
        "kept_archives": kept_sorted,
        "pruned_archives": pruned,
        "legal_hold_count": len(set(legal_hold_kept)),
        "clock_skew_adjustment_count": len(clock_skew_adjusted),
        "compaction_bytes_reclaimable": compaction_bytes,
        "compaction_segments_reclaimable": compaction_segments,
        "evaluation": {
            "kept": kept_sorted,
            "pruned": pruned,
            "bucket_hits": bucket_hits,
            "clock_skew_adjusted": sorted(clock_skew_adjusted),
            "legal_hold_kept": sorted(set(legal_hold_kept)),
        },
    }


def stage_path_for(list_file: Path) -> Path:
    return list_file.parent / "borg.stage.json"


def compact_export(doc: dict[str, Any]) -> str:
    return json.dumps(doc, sort_keys=True, separators=(",", ":")) + "\n"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def make_random_list(
    work_dir: Path,
    *,
    suffix: str,
    reference_now: datetime,
    count: int = 12,
) -> Path:
    import random
    import secrets

    rng = random.Random(secrets.randbits(64))
    work_dir.mkdir(parents=True, exist_ok=True)
    path = work_dir / f"repo_{suffix}.list"
    lines: list[str] = []
    for i in range(count):
        days_back = rng.randint(0, 400)
        hour = rng.randint(0, 23)
        ts = reference_now - timedelta(days=days_back, hours=hour)
        ts_s = ts.strftime("%Y-%m-%dT%H:%M:%SZ")
        size = rng.randint(1_000_000, 50_000_000)
        segs = rng.randint(1, 20)
        lines.append(f"arc-{suffix}-{i}\t{ts_s}\t{size}\t{segs}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path

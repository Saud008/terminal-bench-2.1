"""Cron ledger schedule math for cronctl verifier (independent of /app sources)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


@dataclass
class CronJob:
    id: str
    cron: str
    location: str
    tags: dict[str, str]
    singleton: bool


@dataclass
class CronScenario:
    window_start: str
    window_end_ms: int
    jobs: list[CronJob]
    events: list[dict]


def read_seed_scenario(path: Path, seed: str) -> CronScenario:
    raw = json.loads(path.read_text(encoding="utf-8"))
    jobs = []
    for row in raw["jobs"]:
        jid = f"{seed}:{row['id']}"
        jobs.append(
            CronJob(
                id=jid,
                cron=row["cron"],
                location=row.get("location") or "UTC",
                tags=row.get("tags") or {},
                singleton=bool(row.get("singleton")),
            )
        )
    events = []
    for ev in raw.get("events") or []:
        e = dict(ev)
        if e.get("job_id"):
            e["job_id"] = f"{seed}:{e['job_id']}"
        events.append(e)
    return CronScenario(
        window_start=raw["window_start"],
        window_end_ms=int(raw["window_end_ms"]),
        jobs=jobs,
        events=events,
    )


def _parse_cron(expr: str) -> tuple[str, str, str, str, str]:
    parts = expr.split()
    if len(parts) != 5:
        raise ValueError(expr)
    return tuple(parts)  # type: ignore[return-value]


def _field_matches(value: int, field: str, *, is_dow: bool = False) -> bool:
    if field == "*":
        return True
    if field.startswith("*/"):
        step = int(field[2:])
        return value % step == 0
    if is_dow and field.isdigit():
        return value == int(field)
    if field.isdigit():
        return value == int(field)
    return False


def _cron_next(after: datetime, expr: str, loc: ZoneInfo) -> datetime | None:
    minute, hour, dom, month, dow = _parse_cron(expr)
    cursor = after.astimezone(loc).replace(second=0, microsecond=0)
    if cursor <= after.astimezone(loc):
        cursor += timedelta(minutes=1)
    for _ in range(525600):
        if not _field_matches(cursor.month, month):
            cursor += timedelta(minutes=1)
            continue
        if not _field_matches(cursor.day, dom):
            cursor += timedelta(minutes=1)
            continue
        if not _field_matches(cursor.weekday(), dow, is_dow=True):
            cursor += timedelta(minutes=1)
            continue
        if not _field_matches(cursor.hour, hour):
            cursor += timedelta(minutes=1)
            continue
        if not _field_matches(cursor.minute, minute):
            cursor += timedelta(minutes=1)
            continue
        return cursor.astimezone(timezone.utc)
    return None


def _zone_for(job: CronJob, default: str = "UTC") -> ZoneInfo:
    return ZoneInfo(job.location or default)


def _fire_sort_key(fire: tuple[str, int]) -> tuple[int, str]:
    jid, at_ms = fire
    return (at_ms, jid)


def fnv_digest_for_fires(fires: list[tuple[str, int]]) -> str:
    ordered = sorted(fires, key=_fire_sort_key)
    payload = "".join(f"{jid}:{at}\n" for jid, at in ordered)
    h = 1469598103934665603
    for b in payload.encode("utf-8"):
        h ^= b
        h = (h * 1099511628211) & 0xFFFFFFFFFFFFFFFF
    return f"{h:016x}"


def expand_cron_fires(
    sc: CronScenario, default_loc: str = "UTC"
) -> list[tuple[str, int]]:
    start = datetime.fromisoformat(sc.window_start.replace("Z", "+00:00"))
    end = start + timedelta(milliseconds=sc.window_end_ms)
    fires: list[tuple[str, int]] = []
    for job in sc.jobs:
        loc = _zone_for(job, default_loc)
        cursor = start - timedelta(microseconds=1)
        while True:
            nxt = _cron_next(cursor, job.cron, loc)
            if nxt is None or nxt >= end:
                break
            fires.append((job.id, int(nxt.timestamp() * 1000)))
            cursor = nxt
    fires.sort(key=_fire_sort_key)
    return fires


def _singleton_group(job: CronJob) -> str | None:
    g = job.tags.get("singleton_group")
    return g if g else None


def rollup_execution_rows(sc: CronScenario, default_loc: str = "UTC") -> dict:
    planned = expand_cron_fires(sc, default_loc)
    by_ms: dict[int, list[str]] = {}
    for jid, at_ms in planned:
        by_ms.setdefault(at_ms, []).append(jid)

    executions: list[dict] = []
    dedup = 0
    group_seen_at: dict[tuple[int, str], bool] = {}

    for at_ms in sorted(by_ms):
        for jid in sorted(by_ms[at_ms]):
            job = next(j for j in sc.jobs if j.id == jid)
            grp = _singleton_group(job)
            if job.singleton or grp:
                key = (at_ms, grp or jid)
                if group_seen_at.get(key):
                    executions.append(
                        {
                            "job_id": jid,
                            "fired_at_ms": at_ms,
                            "status": "deduped",
                            "deduped": True,
                        }
                    )
                    dedup += 1
                    continue
                group_seen_at[key] = True
            executions.append(
                {
                    "job_id": jid,
                    "fired_at_ms": at_ms,
                    "status": "fired",
                    "deduped": False,
                    "lock_held": True,
                }
            )

    start = datetime.fromisoformat(sc.window_start.replace("Z", "+00:00"))
    start_ms = int(start.timestamp() * 1000)
    for ev in sc.events:
        at_ms = start_ms + int(ev["at_ms"])
        jid = ev["job_id"]
        if ev.get("action") == "reschedule":
            executions.append(
                {
                    "job_id": jid,
                    "fired_at_ms": at_ms,
                    "status": "aborted",
                    "deduped": False,
                }
            )
        if ev.get("action") == "panic":
            executions.append(
                {
                    "job_id": jid,
                    "fired_at_ms": at_ms,
                    "status": "panic",
                    "deduped": False,
                    "lock_held": False,
                }
            )

    fires = sum(1 for e in executions if not e.get("deduped"))
    return {"fire_count": fires, "dedup_count": dedup, "executions": executions}


def count_gap_window_fires(sc: CronScenario, default_loc: str = "UTC") -> int:
    return len(expand_cron_fires(sc, default_loc))

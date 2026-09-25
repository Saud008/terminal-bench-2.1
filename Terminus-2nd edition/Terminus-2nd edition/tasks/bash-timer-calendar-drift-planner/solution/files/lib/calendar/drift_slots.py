#!/usr/bin/env python3
"""Correct calendar drift slots for oracle."""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from lib.units.fragment_merge import merge_timer_bundle


def parse_duration_sec(spec: str) -> int:
    spec = spec.strip()
    if spec.endswith("min"):
        return int(spec[:-3].strip()) * 60
    if spec.endswith("h"):
        return int(spec[:-1].strip()) * 3600
    if spec.endswith("s"):
        return int(spec[:-1].strip())
    return int(spec)


def in_weekday_range(d: date, start: int, end: int) -> bool:
    w = d.weekday()
    if start <= end:
        return start <= w <= end
    return w >= start or w <= end


def parse_on_calendar(expr: str) -> dict[str, Any]:
    expr = " ".join(expr.split())
    parts = expr.split()
    if len(parts) == 3:
        weekday_token, _ymd, time_spec = parts
        day_spec = weekday_token
    elif len(parts) == 2:
        day_spec, time_spec = parts
    else:
        raise ValueError(f"unsupported OnCalendar: {expr}")
    hh, mm, ss = (int(x) for x in time_spec.split(":"))
    weekday_range = None
    dom = None
    m = re.fullmatch(r"(\w+)\.\.(\w+)", day_spec)
    if m:
        names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        start = names.index(m.group(1)[:3].title())
        end = names.index(m.group(2)[:3].title())
        weekday_range = (start, end)
        day_spec = "*-*-*"
    if day_spec.startswith("*-*-") and day_spec != "*-*-*":
        dom = int(day_spec.split("-")[-1])
    return {"weekday_range": weekday_range, "dom": dom, "hour": hh, "minute": mm, "second": ss}


def local_slot_to_utc(d: date, hour: int, minute: int, second: int, tz_name: str) -> datetime:
    tz = ZoneInfo(tz_name)
    local = datetime(d.year, d.month, d.day, hour, minute, second, tzinfo=tz)
    return local.astimezone(timezone.utc)


def expand_calendar_slots(timer: dict[str, str], start: datetime, end: datetime, host_tz: str) -> list[datetime]:
    expr = timer.get("OnCalendar", "")
    if not expr:
        return []
    spec = parse_on_calendar(expr)
    tz_name = timer.get("Timezone", host_tz)
    cur = start.date()
    end_date = end.date()
    slots: list[datetime] = []
    while cur <= end_date:
        ok = True
        if spec["weekday_range"] is not None:
            ok = in_weekday_range(cur, spec["weekday_range"][0], spec["weekday_range"][1])
        if spec["dom"] is not None and cur.day != spec["dom"]:
            ok = False
        if ok:
            inst = local_slot_to_utc(cur, spec["hour"], spec["minute"], spec["second"], tz_name)
            if start < inst <= end:
                slots.append(inst)
        cur += timedelta(days=1)
    return sorted(slots)


def timer_mode(timer: dict[str, str]) -> str:
    cal = bool(timer.get("OnCalendar"))
    mono = bool(timer.get("OnBootSec") or timer.get("OnUnitActiveSec"))
    if cal and mono:
        return "mixed"
    if mono:
        return "monotonic"
    return "calendar"


def monotonic_next_fire(timer: dict[str, str], activation: dict[str, Any], context: dict[str, Any], reference: datetime):
    boot_now = int(context.get("boot_monotonic_usec", 0))
    last_mono = int(activation.get("unit_active_monotonic_usec", 0))
    candidates: list[int] = []
    if timer.get("OnBootSec"):
        candidates.append(int(context.get("boot_monotonic_usec", 0)) + parse_duration_sec(timer["OnBootSec"]) * 1_000_000)
    if timer.get("OnUnitActiveSec"):
        candidates.append(last_mono + parse_duration_sec(timer["OnUnitActiveSec"]) * 1_000_000)
    if not candidates:
        return None
    target = min(candidates)
    delta_usec = target - boot_now
    return reference + timedelta(microseconds=delta_usec)


def build_forecast(bundle: Path, timer_name: str, context: dict[str, Any], reference: datetime) -> dict[str, Any]:
    timer = merge_timer_bundle(bundle, timer_name)
    activation_path = bundle / "activation.json"
    activation = json.loads(activation_path.read_text(encoding="utf-8")) if activation_path.is_file() else {}
    last_trigger = datetime.fromisoformat(
        activation.get("last_trigger_utc", "1970-01-01T00:00:00Z").replace("Z", "+00:00")
    ).astimezone(timezone.utc)
    host_tz = context.get("host_timezone", "UTC")
    accuracy = int(timer.get("AccuracySec", "0") or 0)
    rand_delay = int(timer.get("RandomizedDelaySec", "0") or 0)
    persistent = str(timer.get("Persistent", "false")).lower() == "true"
    mode = timer_mode(timer)

    calendar_slots = expand_calendar_slots(timer, last_trigger, reference, host_tz)
    missed = [s for s in calendar_slots if s > last_trigger and s <= reference]

    mono_next = monotonic_next_fire(timer, activation, context, reference)
    future = expand_calendar_slots(timer, reference, reference + timedelta(days=400), host_tz)
    cal_next = future[0] if future else None

    if mode == "monotonic":
        nominal_next = mono_next
    elif mode == "calendar":
        nominal_next = cal_next
    else:
        candidates = [x for x in (cal_next, mono_next) if x is not None]
        nominal_next = min(candidates) if candidates else None

    earliest = nominal_next
    latest = nominal_next + timedelta(seconds=rand_delay) if nominal_next else None
    catchup = list(missed) if persistent else []

    dropins = []
    drop_dir = bundle / f"{timer_name}.timer.d"
    if drop_dir.is_dir():
        dropins = sorted(p.name for p in drop_dir.glob("*.conf"))

    return {
        "timer_name": timer_name,
        "timer_mode": mode,
        "timezone_normalized": timer.get("Timezone", host_tz),
        "next_fire_utc_earliest": earliest.strftime("%Y-%m-%dT%H:%M:%SZ") if earliest else None,
        "next_fire_utc_latest": latest.strftime("%Y-%m-%dT%H:%M:%SZ") if latest else None,
        "missed_run_count": len(missed),
        "missed_run_utc": [s.strftime("%Y-%m-%dT%H:%M:%SZ") for s in missed],
        "catchup_run_count": len(catchup),
        "catchup_run_utc": [s.strftime("%Y-%m-%dT%H:%M:%SZ") for s in catchup],
        "randomized_delay_sec": rand_delay,
        "accuracy_sec": accuracy,
        "drop_in_overrides_applied": dropins,
        "persistent_enabled": persistent,
    }

"""Independent RRULE expansion reference per /app/docs/ical-expansion-contract.md."""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

WEEKDAY = {"SU": 6, "MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5}


@dataclass
class Transition:
    at: datetime
    offset_sec: int


@dataclass
class TimeZone:
    tzid: str
    transitions: list[Transition] = field(default_factory=list)


@dataclass
class RRule:
    freq: str = ""
    interval: int = 1
    byday: list[str] = field(default_factory=list)
    bysetpos: int = 0
    count: int = 0
    until: datetime | None = None
    until_utc: bool = False


@dataclass
class Event:
    uid: str
    dtstart: datetime
    floating: bool
    tzid: str
    rrule: RRule
    exdates: list[datetime] = field(default_factory=list)
    rdates: list[datetime] = field(default_factory=list)


def parse_ics_date(raw: str) -> datetime:
    raw = raw.strip()
    if raw.endswith("Z"):
        return datetime.strptime(raw, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc)
    return datetime.strptime(raw, "%Y%m%dT%H%M%S")


def unfold(text: str) -> list[str]:
    lines: list[str] = []
    cur = ""
    for line in text.splitlines():
        if line.startswith(" ") or line.startswith("\t"):
            cur += line[1:]
        else:
            if cur:
                lines.append(cur)
            cur = line
    if cur:
        lines.append(cur)
    return lines


def load_calendar(path: Path) -> tuple[list[Event], dict[str, TimeZone]]:
    text = path.read_text(encoding="utf-8")
    zones: dict[str, TimeZone] = {}
    events: list[Event] = []
    in_tz = in_event = False
    tz = TimeZone("")
    tz_std = tz_dst = 0
    tz_to_dst: datetime | None = None
    tz_to_std: datetime | None = None
    ev: Event | None = None
    for line in unfold(text):
        if line == "BEGIN:VTIMEZONE":
            in_tz = True
            tz = TimeZone("")
            tz_std = tz_dst = 0
            tz_to_dst = tz_to_std = None
        elif line == "END:VTIMEZONE":
            if tz.tzid and tz_to_dst and tz_to_std:
                tz.transitions = [
                    Transition(datetime(1970, 1, 1, tzinfo=timezone.utc), tz_std),
                    Transition(tz_to_dst, tz_dst),
                    Transition(tz_to_std, tz_std),
                ]
                zones[tz.tzid] = tz
            in_tz = False
        elif in_tz and line.startswith("TZID:"):
            tz.tzid = line[5:]
        elif in_tz and line.startswith("X-OFFSET-STANDARD:"):
            tz_std = int(line.split(":", 1)[1])
        elif in_tz and line.startswith("X-OFFSET-DAYLIGHT:"):
            tz_dst = int(line.split(":", 1)[1])
        elif in_tz and line.startswith("X-TRANSITION-TO-DST:"):
            tz_to_dst = parse_ics_date(line.split(":", 1)[1])
        elif in_tz and line.startswith("X-TRANSITION-TO-STD:"):
            tz_to_std = parse_ics_date(line.split(":", 1)[1])
        elif line == "BEGIN:VEVENT":
            in_event = True
            ev = Event("", datetime(1970, 1, 1), True, "", RRule())
        elif line == "END:VEVENT" and ev is not None:
            events.append(ev)
            in_event = False
            ev = None
        elif in_event and ev is not None:
            if line.startswith("UID:"):
                ev.uid = line[4:]
            elif line.startswith("DTSTART"):
                val = line.split(":", 1)[1]
                if ";TZID=" in line:
                    ev.tzid = line.split(";TZID=")[1].split(":")[0]
                    ev.floating = False
                elif val.endswith("Z"):
                    ev.floating = False
                else:
                    ev.floating = True
                ev.dtstart = parse_ics_date(val)
            elif line.startswith("RRULE:"):
                ev.rrule = parse_rrule(line[6:])
            elif line.startswith("EXDATE"):
                for part in line.split(":", 1)[1].split(","):
                    ev.exdates.append(parse_ics_date(part.strip()))
            elif line.startswith("RDATE"):
                for part in line.split(":", 1)[1].split(","):
                    ev.rdates.append(parse_ics_date(part.strip()))
    return events, zones


def parse_rrule(raw: str) -> RRule:
    r = RRule()
    for part in raw.split(";"):
        if "=" not in part:
            continue
        key, val = part.split("=", 1)
        if key == "FREQ":
            r.freq = val
        elif key == "INTERVAL":
            r.interval = int(val)
        elif key == "BYDAY":
            r.byday = val.split(",")
        elif key == "BYSETPOS":
            r.bysetpos = int(val)
        elif key == "COUNT":
            r.count = int(val)
        elif key == "UNTIL":
            r.until = parse_ics_date(val)
            r.until_utc = val.endswith("Z")
    return r


def offset_at(t: datetime, tz: TimeZone) -> int:
    if not tz.transitions:
        return 0
    tr = sorted(tz.transitions, key=lambda x: x.at)
    off = tr[0].offset_sec
    for item in tr:
        if item.at <= t.replace(tzinfo=timezone.utc) if t.tzinfo is None else item.at <= t:
            off = item.offset_sec
    cmp = t.replace(tzinfo=timezone.utc) if t.tzinfo is None else t
    off = tr[0].offset_sec
    for item in tr:
        if item.at <= cmp:
            off = item.offset_sec
    return off


def in_dst_gap(t: datetime, tz: TimeZone) -> bool:
    if len(tz.transitions) < 2:
        return False
    tr = sorted(tz.transitions, key=lambda x: x.at)
    local = t.replace(tzinfo=None)
    for prev, cur in zip(tr, tr[1:]):
        if cur.offset_sec - prev.offset_sec != 3600:
            continue
        local_transition = (cur.at + timedelta(seconds=prev.offset_sec)).replace(tzinfo=None)
        gap_start = local_transition.replace(minute=0, second=0, microsecond=0)
        gap_end = gap_start + timedelta(hours=1)
        if local >= gap_start and local < gap_end:
            return True
    return False


def to_utc(t: datetime, tz: TimeZone, floating: bool) -> datetime | None:
    if floating:
        return t.replace(tzinfo=timezone.utc)
    if in_dst_gap(t, tz):
        return None
    off = offset_at(t, tz)
    local = t.replace(tzinfo=None)
    return (local - timedelta(seconds=off)).replace(tzinfo=timezone.utc)


def pick_bysetpos(days: list[datetime], pos: int) -> list[datetime]:
    if pos == 0 or not days:
        return []
    if pos < 0:
        idx = len(days) + pos
        if 0 <= idx < len(days):
            return [days[idx]]
        return []
    if 1 <= pos <= len(days):
        return [days[pos - 1]]
    return []


def within_until(candidate: datetime, rule: RRule) -> bool:
    if rule.until is None:
        return True
    until = rule.until
    if rule.until_utc:
        return candidate.replace(tzinfo=timezone.utc) <= until.replace(tzinfo=timezone.utc)
    return candidate <= until


def merge_occurrences(series: list[datetime], exdates: list[datetime], rdates: list[datetime]) -> list[datetime]:
    out = sorted(set(series + rdates))
    ex_set = {x.replace(tzinfo=None) for x in exdates}
    return [t for t in out if t.replace(tzinfo=None) not in ex_set]


def limit_count(items: list[datetime], count: int) -> list[datetime]:
    if count <= 0:
        return items
    return items[:count]


def match_byday(t: datetime, byday: list[str]) -> bool:
    if not byday:
        return True
    wd = t.weekday()
    return any(WEEKDAY[code] == wd for code in byday)


def expand_weekly(ev: Event) -> list[datetime]:
    out: list[datetime] = []
    cur = ev.dtstart
    max_n = 128 if ev.rrule.count <= 0 else ev.rrule.count * 2
    while len(out) < max_n:
        for d in range(7):
            day = cur + timedelta(days=d)
            if match_byday(day, ev.rrule.byday):
                out.append(day)
        cur = cur + timedelta(days=7 * ev.rrule.interval)
        if ev.rrule.until is not None:
            if ev.rrule.until_utc:
                if cur.replace(tzinfo=timezone.utc) > ev.rrule.until:
                    break
            elif cur > ev.rrule.until:
                break
    return out


def month_days(ev: Event, month: datetime) -> list[datetime]:
    first = month.replace(day=1, hour=ev.dtstart.hour, minute=ev.dtstart.minute, second=ev.dtstart.second)
    cur = first
    days: list[datetime] = []
    while cur.month == first.month:
        if match_byday(cur, ev.rrule.byday):
            days.append(cur)
        cur += timedelta(days=1)
    return days


def expand_monthly(ev: Event) -> list[datetime]:
    out: list[datetime] = []
    cur = ev.dtstart.replace(day=1)
    for _ in range(36):
        picked = pick_bysetpos(month_days(ev, cur), ev.rrule.bysetpos)
        out.extend(picked)
        if cur.month == 12:
            cur = cur.replace(year=cur.year + 1, month=1)
        else:
            cur = cur.replace(month=cur.month + ev.rrule.interval)
        if ev.rrule.until is not None:
            if ev.rrule.until_utc:
                if cur.replace(tzinfo=timezone.utc) > ev.rrule.until:
                    break
            elif cur > ev.rrule.until:
                break
    return out


def expand_event(ev: Event, zones: dict[str, TimeZone], window_start: datetime, window_end: datetime) -> list[tuple[str, datetime]]:
    tz = zones.get(ev.tzid, TimeZone(""))
    if ev.rrule.freq == "WEEKLY":
        series = expand_weekly(ev)
    elif ev.rrule.freq == "MONTHLY":
        series = expand_monthly(ev)
    else:
        series = [ev.dtstart]
    merged = limit_count(merge_occurrences(series, ev.exdates, ev.rdates), ev.rrule.count)
    out: list[tuple[str, datetime]] = []
    for local in merged:
        if not within_until(local, ev.rrule):
            continue
        utc = to_utc(local, tz, ev.floating)
        if utc is None:
            continue
        if utc < window_start or utc > window_end:
            continue
        out.append((ev.uid, utc))
    out.sort(key=lambda row: (row[1], row[0]))
    return out


def parse_window(raw: str) -> tuple[datetime, datetime]:
    start_s, end_s = raw.split("/", 1)
    start = datetime.fromisoformat(start_s.replace("Z", "+00:00"))
    end = datetime.fromisoformat(end_s.replace("Z", "+00:00"))
    return start.astimezone(timezone.utc), end.astimezone(timezone.utc)


def reference_expand(ics_path: Path, window: str) -> list[tuple[str, str]]:
    events, zones = load_calendar(ics_path)
    w0, w1 = parse_window(window)
    rows: list[tuple[str, datetime]] = []
    for ev in events:
        rows.extend(expand_event(ev, zones, w0, w1))
    rows.sort(key=lambda r: (r[1], r[0]))
    return [(uid, ts.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")) for uid, ts in rows]


def read_db(path: Path) -> list[tuple[str, str]]:
    conn = sqlite3.connect(path)
    cur = conn.execute("SELECT uid, start_utc FROM occurrences ORDER BY start_utc ASC, uid ASC")
    rows = [(r[0], r[1]) for r in cur.fetchall()]
    conn.close()
    return rows


def procedural_ics(seed: str) -> str:
    h = hashlib.sha256(seed.encode()).digest()
    count = 4 + (h[0] % 3)
    byday = ["MO", "WE", "FR"][h[1] % 3]
    exdate = ""
    rdate = ""
    if h[2] % 2 == 0:
        exdate = "EXDATE;TZID=America/New_York:20240117T120000\n"
        rdate = "RDATE;TZID=America/New_York:20240108T120000\n"
    return f"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VTIMEZONE
TZID:America/New_York
X-OFFSET-STANDARD:-18000
X-OFFSET-DAYLIGHT:-14400
X-TRANSITION-TO-DST:20240310T070000Z
X-TRANSITION-TO-STD:20241103T060000Z
END:VTIMEZONE
BEGIN:VEVENT
UID:proc-{seed}@generated
DTSTART;TZID=America/New_York:20240104T120000
RRULE:FREQ=WEEKLY;BYDAY={byday};COUNT={count}
{exdate}{rdate}END:VEVENT
END:VCALENDAR
"""


def procedural_monthly_setpos(seed: str) -> str:
    h = hashlib.sha256(seed.encode()).digest()
    setpos = 1 if h[0] % 2 == 0 else -1
    count = 2 + (h[1] % 2)
    day = ["MO", "TU", "WE", "TH", "FR"][h[2] % 5]
    start_day = 15 + (h[3] % 14)
    return f"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VTIMEZONE
TZID:America/New_York
X-OFFSET-STANDARD:-18000
X-OFFSET-DAYLIGHT:-14400
X-TRANSITION-TO-DST:20240310T070000Z
X-TRANSITION-TO-STD:20241103T060000Z
END:VTIMEZONE
BEGIN:VEVENT
UID:proc-monthly-{seed}@generated
DTSTART;TZID=America/New_York:202401{start_day:02d}T090000
RRULE:FREQ=MONTHLY;BYDAY={day};BYSETPOS={setpos};COUNT={count}
END:VEVENT
END:VCALENDAR
"""


def procedural_combo(seed: str) -> str:
    h = hashlib.sha256(seed.encode()).digest()
    count = 4 + (h[0] % 2)
    byday = ["MO", "WE", "FR"][h[1] % 3]
    exdate = "EXDATE;TZID=America/New_York:20240117T120000\n"
    rdate = "RDATE;TZID=America/New_York:20240108T120000\n"
    if h[2] % 3 == 0:
        exdate = ""
    if h[3] % 2 == 0:
        rdate = ""
    return f"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VTIMEZONE
TZID:America/New_York
X-OFFSET-STANDARD:-18000
X-OFFSET-DAYLIGHT:-14400
X-TRANSITION-TO-DST:20240310T070000Z
X-TRANSITION-TO-STD:20241103T060000Z
END:VTIMEZONE
BEGIN:VEVENT
UID:proc-combo-{seed}@generated
DTSTART;TZID=America/New_York:20240104T120000
RRULE:FREQ=WEEKLY;BYDAY={byday};COUNT={count}
{exdate}{rdate}END:VEVENT
END:VCALENDAR
"""


def procedural_biweekly(seed: str) -> str:
    h = hashlib.sha256(seed.encode()).digest()
    count = 3 + (h[0] % 3)
    byday = ["TU", "TH", "SA"][h[1] % 3]
    hour = 8 + (h[2] % 10)
    return f"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VTIMEZONE
TZID:America/New_York
X-OFFSET-STANDARD:-18000
X-OFFSET-DAYLIGHT:-14400
X-TRANSITION-TO-DST:20240310T070000Z
X-TRANSITION-TO-STD:20241103T060000Z
END:VTIMEZONE
BEGIN:VEVENT
UID:proc-biweekly-{seed}@generated
DTSTART;TZID=America/New_York:20240102T{hour:02d}0000
RRULE:FREQ=WEEKLY;INTERVAL=2;BYDAY={byday};COUNT={count}
END:VEVENT
END:VCALENDAR
"""

"""Independent Python reference for nmeapipeline merge reports."""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path
from typing import Any


def nmea_checksum(body_after_dollar: str) -> str:
    v = 0
    for ch in body_after_dollar:
        v ^= ord(ch)
    return f"{v:02X}"


def with_checksum(prefix: str) -> str:
    assert prefix.startswith("$")
    return f"{prefix}*{nmea_checksum(prefix[1:])}"


def verify_checksum(line: str) -> bool:
    if not line.startswith("$") or "*" not in line:
        return False
    body, _, claimed = line[1:].partition("*")
    if len(claimed) < 2:
        return False
    return nmea_checksum(body).upper() == claimed[:2].upper()


def split_fields(body: str) -> list[str]:
    out: list[str] = []
    cur: list[str] = []
    in_quotes = False
    i = 0
    chars = list(body)
    while i < len(chars):
        c = chars[i]
        if in_quotes:
            if c == '"':
                if i + 1 < len(chars) and chars[i + 1] == '"':
                    cur.append('"')
                    i += 2
                    continue
                in_quotes = False
                cur.append('"')
                i += 1
                continue
            cur.append(c)
            i += 1
            continue
        if c == '"':
            in_quotes = True
            cur.append('"')
            i += 1
            continue
        if c == ",":
            out.append("".join(cur))
            cur = []
            i += 1
            continue
        cur.append(c)
        i += 1
    out.append("".join(cur))
    return out


def canonical_talker(talker: str) -> str:
    if talker in ("GP", "GN"):
        return "GN"
    return talker


def days_in_month(year: int, month: int) -> int:
    if month in (1, 3, 5, 7, 8, 10, 12):
        return 31
    if month in (4, 6, 9, 11):
        return 30
    leap = year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
    return 29 if leap else 28


def attach_utc(rmc_date: str | None, rmc_time: str | None, time_field: str) -> str | None:
    if not rmc_date or len(rmc_date) != 6 or len(time_field) < 6:
        return None
    day = int(rmc_date[0:2])
    month = int(rmc_date[2:4])
    year = 2000 + int(rmc_date[4:6])
    hh, mm, ss = int(time_field[0:2]), int(time_field[2:4]), int(time_field[4:6])
    if rmc_time and len(rmc_time) >= 2:
        rh = int(rmc_time[0:2])
        if hh < rh:
            day += 1
            dim = days_in_month(year, month)
            if day > dim:
                day = 1
                month += 1
                if month > 12:
                    month = 1
                    year += 1
    return f"{year:04d}-{month:02d}-{day:02d}T{hh:02d}:{mm:02d}:{ss:02d}Z"


def parse_line(line: str) -> dict[str, Any] | str:
    line = line.strip()
    if not verify_checksum(line):
        return "checksum"
    star = line.rfind("*")
    body = line[1:star]
    parts = split_fields(body)
    if not parts or len(parts[0]) < 5:
        return "addr"
    addr = parts[0]
    talker, sentence = addr[:2], addr[2:]
    fields = parts[1:]
    is_multipart = (
        sentence in ("GSV", "GSA")
        and len(fields) >= 2
        and fields[0].isdigit()
        and int(fields[0]) > 1
    )
    return {
        "raw": line,
        "talker": talker,
        "sentence": sentence,
        "fields": fields,
        "is_multipart": is_multipart,
    }


def merge_payload(fragments: list[dict]) -> tuple[int, int, list[str]]:
    sorted_f = sorted(
        fragments,
        key=lambda s: int(s["fields"][1])
        if len(s["fields"]) > 1 and s["fields"][1].isdigit()
        else 0,
    )
    total = int(sorted_f[0]["fields"][0]) if sorted_f and sorted_f[0]["fields"] else 1
    payload: list[str] = []
    for s in sorted_f:
        if len(s["fields"]) > 3:
            payload.extend(s["fields"][3:])
    nums = {s["fields"][1] for s in sorted_f if len(s["fields"]) > 1}
    return total, len(nums), payload


def reconcile(fragments: list[dict]) -> list[dict]:
    by_num: dict[str, dict] = {}
    for s in fragments:
        num = s["fields"][1] if len(s["fields"]) > 1 else "0"
        by_num[num] = s
    out = list(by_num.values())
    out.sort(
        key=lambda s: int(s["fields"][1])
        if len(s["fields"]) > 1 and s["fields"][1].isdigit()
        else 0
    )
    return out


def digest_snapshot(groups: list[dict], rejected: list[dict]) -> str:
    g = sorted(groups, key=lambda x: x["merge_key"])
    r = sorted(rejected, key=lambda x: x["line"])
    payload = json.dumps({"groups": g, "rejected": r}, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def reference_merge(
    input_path: Path,
    session: dict | None = None,
    use_session: bool = False,
) -> tuple[dict, dict]:
    session = deepcopy(
        session or {"version": 1, "rmc_date": None, "rmc_time": None, "pending": []}
    )
    pending: dict[str, list[dict]] = {
        p["merge_key"]: deepcopy(p["fragments"]) for p in session.get("pending", [])
    }
    rmc_date = session.get("rmc_date")
    rmc_time = session.get("rmc_time")

    rejected: list[dict] = []
    buckets: dict[str, list[dict]] = {}
    order: list[str] = []
    singles: dict[str, dict] = {}

    for raw_line in input_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parsed = parse_line(line)
        if isinstance(parsed, str):
            rejected.append({"line": line, "reason": parsed})
            continue
        if (
            parsed["sentence"] == "RMC"
            and len(parsed["fields"]) >= 9
            and parsed["fields"][1] == "A"
        ):
            new_date = parsed["fields"][8]
            new_time = parsed["fields"][0]
            if use_session and rmc_date and new_date != rmc_date:
                pending.clear()
            rmc_date, rmc_time = new_date, new_time
        if parsed["is_multipart"]:
            talker = canonical_talker(parsed["talker"])
            total = int(parsed["fields"][0])
            key = f"{talker}:{parsed['sentence']}:{total}"
            if key not in buckets:
                order.append(key)
                buckets[key] = pending.pop(key, [])
            buckets[key].append(parsed)
        else:
            talker = canonical_talker(parsed["talker"])
            key = f"{talker}:{parsed['sentence']}:1"
            if key not in order:
                order.append(key)
            utc = (
                attach_utc(rmc_date, rmc_time, parsed["fields"][0])
                if parsed["fields"]
                else None
            )
            singles[key] = {
                "merge_key": key,
                "talker": talker,
                "sentence": parsed["sentence"],
                "multipart_total": 1,
                "fragments_merged": 1,
                "payload_fields": list(parsed["fields"]),
                "utc_iso": utc,
            }

    groups: list[dict] = []
    for key in order:
        if key in buckets:
            frags = reconcile(buckets[key])
            has_one = any(
                len(f["fields"]) > 1 and f["fields"][1] == "1" for f in frags
            )
            if not has_one:
                continue
            total, merged, payload = merge_payload(frags)
            if use_session and merged < total:
                pending[key] = frags
                continue
            groups.append(
                {
                    "merge_key": key,
                    "talker": key.split(":")[0],
                    "sentence": key.split(":")[1],
                    "multipart_total": total,
                    "fragments_merged": merged,
                    "payload_fields": payload,
                    "utc_iso": None,
                }
            )
        elif key in singles:
            groups.append(singles[key])

    digest = digest_snapshot(groups, rejected)
    report = {"groups": groups, "rejected": rejected, "snapshot_digest": digest}
    new_session = {
        "version": 1,
        "rmc_date": rmc_date,
        "rmc_time": rmc_time,
        "pending": [
            {
                "merge_key": k,
                "talker": k.split(":")[0],
                "sentence": k.split(":")[1],
                "multipart_total": int(k.split(":")[2]),
                "fragments": v,
            }
            for k, v in pending.items()
            if any(len(f["fields"]) > 1 and f["fields"][1] == "1" for f in v)
        ],
    }
    return report, new_session


def reference_report(input_path: Path) -> dict:
    report, _ = reference_merge(input_path, use_session=False)
    return report


def load_session_file(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

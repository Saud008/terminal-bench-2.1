"""Reference oracle for s3lc S3 lifecycle cost simulator."""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_day(ts: str) -> date:
    return datetime.strptime(ts[:10], "%Y-%m-%d").date()


def days_between(start: date, end: date) -> int:
    return (end - start).days


def days_in_month(ymd: str) -> int:
    d = parse_day(ymd)
    if d.month == 12:
        nxt = date(d.year + 1, 1, 1)
    else:
        nxt = date(d.year, d.month + 1, 1)
    return (nxt - date(d.year, d.month, 1)).days


def load_inventory(path: Path) -> list[dict[str, Any]]:
    rows: dict[tuple[str, str], dict[str, Any]] = {}
    order: list[tuple[str, str]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        row = json.loads(line)
        key = (row["key"], row["version_id"])
        if key not in rows:
            order.append(key)
        rows[key] = row
    return [rows[k] for k in order]


def tag_prefixes_match(tags: dict[str, str], prefixes: dict[str, str]) -> bool:
    if not prefixes:
        return True
    for key, prefix in prefixes.items():
        val = tags.get(key, "")
        if not val.startswith(prefix):
            return False
    return True


def pick_rule(tags: dict[str, str], rules_doc: dict[str, Any]) -> dict[str, Any] | None:
    winner: dict[str, Any] | None = None
    win_pri = -1
    win_spec = -1
    for rule in rules_doc.get("rules", []):
        if not tag_prefixes_match(tags, rule.get("tag_prefixes", {})):
            continue
        pri = int(rule["priority"])
        spec = len(rule.get("tag_prefixes", {}))
        if pri > win_pri or (pri == win_pri and spec > win_spec):
            winner = rule
            win_pri = pri
            win_spec = spec
        elif pri == win_pri and spec == win_spec and winner is not None:
            if rule["id"] < winner["id"]:
                winner = rule
    return winner


def mark_current(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key: dict[str, list[dict[str, Any]]] = {}
    for o in objects:
        by_key.setdefault(o["key"], []).append(o)
    out: list[dict[str, Any]] = []
    for key, vers in by_key.items():
        cur = max(vers, key=lambda v: (v["last_modified"], vers.index(v)))
        for v in vers:
            nc = None if v is cur else cur["last_modified"]
            row = dict(v)
            row["current_version"] = v is cur
            row["noncurrent_since"] = nc
            out.append(row)
    return out


def dedupe_mpu(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for o in objects:
        mid = o.get("multipart_id")
        if mid and o.get("multipart_complete"):
            if mid in seen:
                continue
            seen.add(mid)
        out.append(o)
    return out


def key_suppressed(
    objects: list[dict[str, Any]], key: str, holds: dict[str, Any], window_end: str
) -> bool:
    end_day = parse_day(window_end)
    for o in objects:
        if o["key"] != key:
            continue
        if o.get("legal_hold"):
            return True
        until = o.get("retention_until")
        if until and parse_day(until) > end_day:
            return True
    for pfx in holds.get("legal_hold_prefixes", []):
        if key.startswith(pfx):
            return True
    return False


def apply_transitions(age: int, rule: dict[str, Any], storage_class: str) -> str:
    cls = storage_class
    for tr in sorted(rule.get("transitions", []), key=lambda t: t["days"]):
        if age >= int(tr["days"]):
            cls = tr["storage_class"]
    return cls


def simulate(
    objects: list[dict[str, Any]],
    rules_doc: dict[str, Any],
    holds: dict[str, Any],
    window_start: str,
    window_end: str,
) -> dict[str, Any]:
    marked = dedupe_mpu(mark_current(objects))
    end_day = parse_day(window_end)
    suppressed: set[str] = set()
    transitions: list[dict[str, str]] = []
    expired: list[dict[str, str]] = []
    billable: list[dict[str, Any]] = []
    cur_delete: dict[str, bool] = {}
    for o in marked:
        if o["current_version"]:
            cur_delete[o["key"]] = bool(o["is_delete_marker"])
    for o in marked:
        key = o["key"]
        if key_suppressed(marked, key, holds, window_end):
            suppressed.add(key)
            row = dict(o)
            billable.append(row)
            continue
        rule = pick_rule(o.get("tags", {}), rules_doc)
        if not rule:
            billable.append(dict(o))
            continue
        if o["current_version"] and o["is_delete_marker"]:
            billable.append(dict(o))
            continue
        if cur_delete.get(key) and o["current_version"]:
            billable.append(dict(o))
            continue
        if not o.get("multipart_complete") and o.get("multipart_id"):
            billable.append(dict(o))
            continue
        age = days_between(parse_day(o["last_modified"]), end_day)
        cls = apply_transitions(age, rule, o["storage_class"])
        if not o["current_version"]:
            nc = o.get("noncurrent_since")
            nc_age = days_between(parse_day(nc), end_day) if nc else age
            if nc_age >= int(rule.get("noncurrent_expiration", {}).get("days", 10**9)):
                expired.append({"key": key, "version_id": o["version_id"]})
                continue
        else:
            if age >= int(rule.get("expiration", {}).get("days", 10**9)):
                expired.append({"key": key, "version_id": o["version_id"]})
                continue
        row = dict(o)
        row["storage_class"] = cls
        transitions.append({"key": key, "version_id": o["version_id"], "storage_class": cls})
        billable.append(row)
    orphan = 0
    for key, is_dm in cur_delete.items():
        if not is_dm:
            continue
        orphan += sum(
            1
            for o in marked
            if o["key"] == key and not o["current_version"] and not o["is_delete_marker"]
        )
    tran_sorted = sorted(transitions, key=lambda t: (t["key"], t["version_id"]))
    exp_sorted = sorted(expired, key=lambda t: (t["key"], t["version_id"]))
    dig = sha256_hex(
        f"{window_start}|{window_end}|{json.dumps(tran_sorted, separators=(',', ':'))}|{json.dumps(exp_sorted, separators=(',', ':'))}"
    )
    return {
        "objects": marked,
        "simulation": {
            "window_start": window_start,
            "window_end": window_end,
            "suppressed_keys": sorted(suppressed),
            "transitions_applied": tran_sorted,
            "expired_versions": exp_sorted,
            "delete_marker_orphan_count": orphan,
            "simulation_digest": dig,
        },
    }


def cost_report(
    staging: dict[str, Any], rates: dict[str, float], window_start: str, window_end: str
) -> dict[str, Any]:
    dim = days_in_month(window_start)
    bill_days = days_between(parse_day(window_start), parse_day(window_end)) + 1
    prorate = bill_days / dim
    expired = {
        (e["key"], e["version_id"])
        for e in staging.get("simulation", {}).get("expired_versions", [])
    }
    by_class: dict[str, float] = {}
    mpu_bytes = 0
    for o in staging.get("objects", []):
        if (o["key"], o["version_id"]) in expired:
            continue
        if not o.get("multipart_complete") and o.get("multipart_id"):
            mpu_bytes += int(o["size_bytes"])
            continue
        cls = o["storage_class"]
        by_class[cls] = by_class.get(cls, 0.0) + int(o["size_bytes"])
    by_out: dict[str, dict[str, str]] = {}
    total = 0.0
    for cls in sorted(by_class):
        gb = by_class[cls] / (1024**3) * prorate
        usd = gb * float(rates.get(cls, 0.0))
        total += usd
        by_out[cls] = {"gb_months": f"{gb:.2f}", "usd": f"{usd:.2f}"}
    mpu_usd = (mpu_bytes / (1024**3)) * float(rates.get("STANDARD", 0.0)) * prorate
    total += mpu_usd
    sup = len(staging.get("simulation", {}).get("suppressed_keys", []))
    orphan = int(staging.get("simulation", {}).get("delete_marker_orphan_count", 0))
    dig = sha256_hex(
        f"{window_start}|{window_end}|{json.dumps(by_out, separators=(',', ':'))}|{mpu_usd:.10f}"
    )
    return {
        "bucket": staging["bucket"],
        "window_start": window_start,
        "window_end": window_end,
        "total_usd": f"{total:.2f}",
        "by_storage_class": by_out,
        "multipart_pending_usd": f"{mpu_usd:.2f}",
        "suppressed_by_legal_hold_count": sup,
        "delete_marker_orphan_versions": orphan,
        "report_digest": dig,
    }


def reference_pipeline(
    inventory: Path,
    bucket: str,
    rules: Path,
    holds: Path,
    rates: Path,
    window_start: str,
    window_end: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    objs = load_inventory(inventory)
    rules_doc = json.loads(rules.read_text(encoding="utf-8"))
    holds_doc = json.loads(holds.read_text(encoding="utf-8"))
    rates_doc = json.loads(rates.read_text(encoding="utf-8"))
    joined = "\n".join(json.dumps(o, separators=(",", ":")) for o in objs)
    fp = sha256_hex(joined)
    sim = simulate(objs, rules_doc, holds_doc, window_start, window_end)
    staging = {
        "schema_version": 1,
        "bucket": bucket,
        "inventory_fingerprint": fp,
        "objects": sim["objects"],
        "simulation": sim["simulation"],
    }
    report = cost_report(staging, rates_doc, window_start, window_end)
    return staging, report

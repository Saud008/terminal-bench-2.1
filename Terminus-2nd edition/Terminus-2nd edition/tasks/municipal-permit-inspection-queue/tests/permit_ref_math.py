"""Independent mpiqctl municipal queue reference simulator."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


def load_bundle(root: Path, scenario: str) -> dict:
    return json.loads((root / "scenarios" / scenario / "bundle.json").read_text(encoding="utf-8"))


def hold_bias() -> int:
    raw = os.environ.get("TB3_HOLD_BIAS", "")
    if raw:
        try:
            return int(raw)
        except ValueError:
            pass
    return 0


def recency_weight(days_ago: int) -> int:
    return max(1, 10 - min(days_ago, 9))


def cert_ok(inspector_level: int, required: int) -> bool:
    return inspector_level >= required


def day_blocked(day: int, start_day: int, end_day: int) -> bool:
    return start_day <= day < end_day


def district_hold_rank(bundle: dict, district: str) -> int:
    best = 0
    for h in bundle.get("zoning_holds", []):
        if h["district_id"] != district or not h.get("active"):
            continue
        rank = int(h["hold_rank"]) + hold_bias()
        if rank > best:
            best = rank
    return best


def permit_blocked(bundle: dict, district: str) -> bool:
    return district_hold_rank(bundle, district) > 0


def day_eligible(bundle: dict, district: str, day: int) -> bool:
    for bw in bundle.get("blackout_windows", []):
        if bw["district_id"] != district:
            continue
        if day_blocked(day, int(bw["start_day"]), int(bw["end_day"])):
            return False
    return True


def route_lane(bundle: dict, permit_type: str) -> tuple[str, int]:
    for r in bundle["permit_routes"]:
        if r["permit_type"] == permit_type:
            return r["inspection_lane"], int(r["min_cert_level"])
    if permit_type.startswith("electrical"):
        return "lane-electrical", 2
    return "lane-general", 1


def violation_sum(bundle: dict, permit_id: str) -> int:
    total = 0
    for v in bundle.get("violations", []):
        if v["permit_id"] != permit_id:
            continue
        total += int(v["severity"]) * recency_weight(int(v["days_ago"]))
    return total


def composite_score(base_priority: int, viol_sum: int) -> int:
    return base_priority * 100 + viol_sum


def reference_scores(fixture_root: Path, scenario: str) -> list[dict]:
    bundle = load_bundle(fixture_root, scenario)
    rows: list[dict] = []
    for p in bundle["permits"]:
        if p.get("deferred"):
            continue
        if not day_eligible(bundle, p["district_id"], int(p["requested_day"])):
            continue
        if permit_blocked(bundle, p["district_id"]):
            continue
        viol = violation_sum(bundle, p["permit_id"])
        rows.append(
            {
                "permit_id": p["permit_id"],
                "composite_score": composite_score(int(p["base_priority"]), viol),
                "violation_weight": viol,
            }
        )
    rows.sort(key=lambda r: (-r["composite_score"], r["permit_id"]))
    return rows


def reference_entries(fixture_root: Path, scenario: str) -> list[dict]:
    bundle = load_bundle(fixture_root, scenario)
    scores = {r["permit_id"]: r for r in reference_scores(fixture_root, scenario)}
    permits = [p for p in bundle["permits"] if not p.get("deferred") and p["permit_id"] in scores]
    permits.sort(key=lambda p: (-scores[p["permit_id"]]["composite_score"], p["permit_id"]))
    inspectors = sorted(bundle["inspectors"], key=lambda i: i["inspector_id"])
    load: dict[str, int] = {}
    out: list[dict] = []
    for p in permits:
        lane, min_cert = route_lane(bundle, p["permit_type"])
        scheduled = int(p["requested_day"])
        candidates = []
        for ins in inspectors:
            if not cert_ok(int(ins["cert_level"]), min_cert):
                continue
            if load.get(ins["inspector_id"], 0) >= int(ins["daily_cap"]):
                continue
            if p["district_id"] not in ins["districts"] and "*" not in ins["districts"]:
                continue
            if scheduled < int(ins["available_day"]):
                continue
            candidates.append(ins)
        candidates.sort(key=lambda i: (load.get(i["inspector_id"], 0), i["inspector_id"]))
        if not candidates:
            continue
        pick = candidates[0]
        out.append(
            {
                "permit_id": p["permit_id"],
                "inspector_id": pick["inspector_id"],
                "scheduled_day": scheduled,
                "inspection_lane": lane,
                "status": "queued",
            }
        )
        load[pick["inspector_id"]] = load.get(pick["inspector_id"], 0) + 1
    out.sort(key=lambda r: r["permit_id"])
    return out


def reference_queue(fixture_root: Path, scenario: str) -> dict:
    bundle = load_bundle(fixture_root, scenario)
    entries = reference_entries(fixture_root, scenario)
    hold_summary: dict[str, int] = {}
    for p in bundle["permits"]:
        if permit_blocked(bundle, p["district_id"]):
            hold_summary[p["district_id"]] = hold_summary.get(p["district_id"], 0) + 1
    digest = hashlib.sha256(
        json.dumps(entries, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()
    return {
        "scenario": scenario,
        "planning_epoch_day": int(bundle["planning_epoch_day"]),
        "queue_entries": entries,
        "hold_summary": hold_summary,
        "queue_digest": digest,
    }

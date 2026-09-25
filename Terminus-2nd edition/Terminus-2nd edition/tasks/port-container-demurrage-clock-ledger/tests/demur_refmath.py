"""Independent reference math for port-container-demurrage-clock-ledger."""

from __future__ import annotations

import hashlib
import json
from datetime import date, timedelta
from pathlib import Path

HOLD_RANKS = {
    "CUSTOMS": 300,
    "TERMINAL_OPS": 200,
    "CARRIER_DISPUTE": 100,
}


def _parse_day(ts: str) -> date:
    return date.fromisoformat(ts[:10])


def _day_range_inclusive_exclusive(start: date, end_exclusive: date) -> list[date]:
    days: list[date] = []
    cur = start
    while cur < end_exclusive:
        days.append(cur)
        cur += timedelta(days=1)
    return days


def _is_closure(day: date, closures: list[dict]) -> bool:
    token = day.isoformat()
    return any(c["date"] == token for c in closures)


def _on_hold(day: date, holds: list[dict], container_id: str) -> bool:
    for h in holds:
        if h["container_id"] != container_id:
            continue
        start = date.fromisoformat(h["start"])
        end = date.fromisoformat(h["end"])
        if start <= day < end:
            return True
    return False


def _active_hold_label(day: date, holds: list[dict], container_id: str) -> str:
    active: list[dict] = []
    for h in holds:
        if h["container_id"] != container_id:
            continue
        start = date.fromisoformat(h["start"])
        end = date.fromisoformat(h["end"])
        if start <= day < end:
            active.append(h)
    if not active:
        return ""
    best = max(active, key=lambda row: HOLD_RANKS.get(row["code"], 0))
    return best["code"]


def _remap_id(seed: str, original: str) -> str:
    digest = hashlib.sha256(f"{seed}:{original}".encode()).hexdigest()
    return f"CNT-{digest[:8]}"


def _apply_demur_seed(scenario: dict, seed: str | None) -> dict:
    if not seed:
        return scenario
    sc = json.loads(json.dumps(scenario))
    id_map = {c["container_id"]: _remap_id(seed, c["container_id"]) for c in sc["containers"]}
    for c in sc["containers"]:
        c["container_id"] = id_map[c["container_id"]]
    for e in sc["gate_events"]:
        e["container_id"] = id_map[e["container_id"]]
    for c in sc["contracts"]:
        c["container_id"] = id_map[c["container_id"]]
    for h in sc.get("holds", []):
        h["container_id"] = id_map[h["container_id"]]
    return sc


def load_scenario(fixture_root: Path, name: str, seed: str | None = None) -> dict:
    path = fixture_root / "scenarios" / f"{name}.json"
    sc = json.loads(path.read_text(encoding="utf-8"))
    events = sorted(sc["gate_events"], key=lambda e: e["ts"])
    sc["gate_events"] = events
    return _apply_demur_seed(sc, seed)


def _pair_gate(events: list[dict], billing_through: str) -> tuple[date, date]:
    gate_in: date | None = None
    gate_out: date | None = None
    for e in events:
        if e["event"] == "gate_in":
            gate_in = _parse_day(e["ts"])
        elif e["event"] == "gate_out":
            gate_out = _parse_day(e["ts"])
    assert gate_in is not None
    end = gate_out if gate_out is not None else _parse_day(billing_through + "T00:00:00Z")
    return gate_in, end


def compute_container(scenario: dict, container: dict) -> dict:
    cid = container["carrier_id"]
    container_id = container["container_id"]
    events = [e for e in scenario["gate_events"] if e["container_id"] == container_id]
    gate_in, end_exclusive = _pair_gate(events, scenario["billing_through"])
    contract = next(c for c in scenario["contracts"] if c["container_id"] == container_id)
    holds = scenario.get("holds", [])
    closures = scenario.get("closures", [])
    tariff = next(t for t in scenario["tariffs"] if t["carrier_id"] == cid)

    eligible_days: list[date] = []
    peak_hold = ""
    peak_rank = -1
    for day in _day_range_inclusive_exclusive(gate_in, end_exclusive):
        if _is_closure(day, closures):
            continue
        label = _active_hold_label(day, holds, container_id)
        if label:
            rank = HOLD_RANKS.get(label, 0)
            if rank > peak_rank:
                peak_rank = rank
                peak_hold = label
        if _on_hold(day, holds, container_id):
            continue
        eligible_days.append(day)

    free_used = min(contract["free_days"], len(eligible_days))
    dem_days = len(eligible_days) - free_used
    tier1 = tier2 = tier3 = 0
    total = 0
    for idx in range(1, dem_days + 1):
        if idx <= 3:
            tier1 += 1
            total += tariff["tier1_rate_cents"]
        elif idx <= 7:
            tier2 += 1
            total += tariff["tier2_rate_cents"]
        else:
            tier3 += 1
            total += tariff["tier3_rate_cents"]

    active_hold = peak_hold

    return {
        "container_id": container_id,
        "eligible_days": len(eligible_days),
        "free_days_used": free_used,
        "demurrage_days": dem_days,
        "tier1_days": tier1,
        "tier2_days": tier2,
        "tier3_days": tier3,
        "total_cents": total,
        "active_hold": active_hold,
        "currency": contract["currency"],
    }


def reference_invoices(fixture_root: Path, scenario_name: str, seed: str | None = None) -> dict:
    sc = load_scenario(fixture_root, scenario_name, seed=seed)
    lines = [compute_container(sc, c) for c in sc["containers"]]
    lines.sort(key=lambda row: row["container_id"])
    export_lines = []
    grand = 0
    for row in lines:
        grand += row["total_cents"]
        item = {
            "container_id": row["container_id"],
            "total_cents": row["total_cents"],
            "currency": row["currency"],
            "tier1_days": row["tier1_days"],
            "tier2_days": row["tier2_days"],
            "tier3_days": row["tier3_days"],
        }
        if row["active_hold"]:
            item["active_hold"] = row["active_hold"]
        export_lines.append(item)
    digest_payload = json.dumps(
        {"grand_total_cents": grand, "lines": export_lines},
        sort_keys=True,
        separators=(",", ":"),
    )
    digest = hashlib.sha256(digest_payload.encode()).hexdigest()[:16]
    return {
        "grand_total_cents": grand,
        "lines": export_lines,
        "invoice_digest": digest,
        "rows": lines,
    }


def reference_ledger_digest(scenario_name: str, rows: list[dict], clock_pass: int) -> str:
    payload_rows = [
        {
            "container_id": r["container_id"],
            "total_cents": r["total_cents"],
            "tier1_days": r["tier1_days"],
            "tier2_days": r["tier2_days"],
            "tier3_days": r["tier3_days"],
        }
        for r in sorted(rows, key=lambda x: x["container_id"])
    ]
    payload = json.dumps(
        {"scenario": scenario_name, "clock_pass": clock_pass, "rows": payload_rows},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode()).hexdigest()[:16]

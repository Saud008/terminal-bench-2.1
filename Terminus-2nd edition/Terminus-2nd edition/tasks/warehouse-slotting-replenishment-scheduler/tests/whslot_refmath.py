"""Independent reference math for whslot verifier."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def load_bundle(root: Path, scenario: str) -> dict:
    return json.loads((root / "scenarios" / scenario / "bundle.json").read_text(encoding="utf-8"))


def lane_bias(zone: str) -> int:
    z = (zone or "").strip().upper()
    return {"A": 30, "B": 20, "C": 10}.get(z, 0)


def velocity_score(sku: dict, zone: str) -> int:
    return sku["picks_per_day"] * 1000 + (100 - sku["on_hand_pct"]) * 10 + lane_bias(zone)


def expected_sku_rank_board(root: Path, scenario: str) -> list[dict]:
    bundle = load_bundle(root, scenario)
    zone_by_slot = {s["slot_id"]: s["zone"] for s in bundle["slots"]}
    rows = [
        {
            "sku_id": s["sku_id"],
            "velocity_score": velocity_score(s, zone_by_slot[s["pick_face_slot"]]),
        }
        for s in bundle["skus"]
    ]
    rows.sort(key=lambda r: (-r["velocity_score"], r["sku_id"]))
    for i, row in enumerate(rows):
        row["rank_ord"] = i + 1
    return rows


def effective_capacity(slot: dict, pol: dict) -> int:
    return slot["capacity_units"] - pol["headroom_margin"]


def allow_partial(units: int, pallet: int, min_keep: int) -> bool:
    if units >= pallet:
        return True
    rem = pallet - units
    if rem == 0:
        return True
    return rem >= min_keep


def units_needed(sku: dict, pol: dict, eff_cap: int) -> int:
    if sku["on_hand_pct"] >= pol["reorder_pct"]:
        return 0
    deficit = eff_cap - sku["current_units"]
    if deficit <= 0:
        return 0
    if deficit > sku["pallet_units"]:
        return sku["pallet_units"]
    return deficit


def reference_planned_tasks(root: Path, scenario: str) -> list[dict]:
    bundle = load_bundle(root, scenario)
    pol = bundle["policies"]
    slot_map = {s["slot_id"]: s for s in bundle["slots"]}
    start = 600
    out = []
    for sku in sorted(bundle["skus"], key=lambda s: s["sku_id"]):
        slot = slot_map[sku["pick_face_slot"]]
        eff = effective_capacity(slot, pol)
        units = units_needed(sku, pol, eff)
        if units == 0:
            continue
        if not allow_partial(units, sku["pallet_units"], pol["min_keep_units"]):
            continue
        tk = f"{bundle['wave_id']}|{sku['sku_id']}|{sku['pick_face_slot']}"
        end = start + 30
        out.append(
            {
                "task_key": tk,
                "sku_id": sku["sku_id"],
                "slot_id": sku["pick_face_slot"],
                "units": units,
                "start_minute": start,
                "end_minute": end,
            }
        )
        start += 35
    return out


def worker_fits(w: dict, start: int, end: int) -> bool:
    if start < w["shift_start"]:
        return False
    return end <= w["shift_end"]


def expected_wave_assignments(root: Path, scenario: str) -> list[dict]:
    bundle = load_bundle(root, scenario)
    tasks = reference_planned_tasks(root, scenario)
    out = []
    for t in tasks:
        worker_id = ""
        for worker in bundle["workers"]:
            if worker_fits(worker, t["start_minute"], t["end_minute"]):
                worker_id = worker["worker_id"]
                break
        out.append({**t, "worker_id": worker_id})
    out.sort(key=lambda r: r["task_key"])
    return out


def canonical(v):
    if isinstance(v, dict):
        return {k: canonical(v[k]) for k in sorted(v)}
    if isinstance(v, list):
        return [canonical(x) for x in v]
    return v


def expected_atlas_body(root: Path, scenario: str) -> dict:
    bundle = load_bundle(root, scenario)
    assignments = expected_wave_assignments(root, scenario)
    body = {"wave_id": bundle["wave_id"], "assignments": assignments}
    raw = json.dumps(canonical(body), separators=(",", ":"), sort_keys=True).encode()
    digest = hashlib.sha256(raw).hexdigest()
    return {"wave_id": bundle["wave_id"], "assignments": assignments, "atlas_fingerprint": digest}

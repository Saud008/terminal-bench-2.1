"""Independent carbon shift planner constraint solver."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def deadline_ok(start: int, duration: int, deadline: int) -> bool:
    return start + duration - 1 <= deadline


def region_allowed(region: str, allowed: list[str]) -> bool:
    return region in allowed


def carbon_mass(curve: list[float], compute: int, start: int, duration: int) -> float:
    total = sum(curve[s] for s in range(start, start + duration))
    return total * compute


def quota_ledger_rows(
    regions: dict[str, Any],
    window_count: int,
    usage: dict[tuple[str, int], int],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for region, spec in sorted(regions.items()):
        carry = 0
        for w in range(window_count):
            base = int(spec["quota_per_window"])
            max_carry = int(spec["max_carryover"])
            available = base + carry
            used = usage.get((region, w), 0)
            leftover = max(0, available - used)
            carry_out = min(max_carry, leftover)
            rows.append(
                {
                    "region": region,
                    "window_index": w,
                    "base_quota": base,
                    "carry_in": carry,
                    "used": used,
                    "carry_out": carry_out,
                }
            )
            carry = carry_out
    return rows


def can_place(
    usage: dict[tuple[str, int], int],
    regions: dict[str, Any],
    window_count: int,
    region: str,
    start: int,
    duration: int,
    compute: int,
) -> bool:
    temp = dict(usage)
    for s in range(start, start + duration):
        temp[(region, s)] = temp.get((region, s), 0) + compute
    ledger = quota_ledger_rows(regions, window_count, temp)
    for s in range(start, start + duration):
        row = next(r for r in ledger if r["region"] == region and r["window_index"] == s)
        if row["used"] > row["base_quota"] + row["carry_in"]:
            return False
    return True


def schedule(meta: dict[str, Any], run_id: str) -> dict[str, Any]:
    regions = meta["regions"]
    intensity = meta["intensity"]
    window_count = int(meta["window_count"])
    jobs = sorted(meta["jobs"], key=lambda j: (j["deadline_slot"], j["job_id"]))
    usage: dict[tuple[str, int], int] = {}
    assignments: list[dict[str, Any]] = []
    infeas: list[dict[str, Any]] = []

    for job in jobs:
        best: tuple[str, int, float] | None = None
        residency_fail = True
        deadline_fail = True
        for region, curve in intensity.items():
            if not region_allowed(region, job["allowed_regions"]):
                continue
            residency_fail = False
            for start in range(window_count):
                if not deadline_ok(start, int(job["duration_slots"]), int(job["deadline_slot"])):
                    continue
                deadline_fail = False
                if not can_place(
                    usage,
                    regions,
                    window_count,
                    region,
                    start,
                    int(job["duration_slots"]),
                    int(job["compute_units"]),
                ):
                    continue
                mass = carbon_mass(curve, int(job["compute_units"]), start, int(job["duration_slots"]))
                if best is None or mass < best[2] or (mass == best[2] and (region, start) < (best[0], best[1])):
                    best = (region, start, mass)
        if best is None:
            if residency_fail:
                reason = "RESIDENCY"
            elif deadline_fail:
                reason = "DEADLINE"
            else:
                reason = "QUOTA"
            infeas.append({"job_id": job["job_id"], "reason": reason})
            continue
        region, start, mass = best
        for s in range(start, start + int(job["duration_slots"])):
            usage[(region, s)] = usage.get((region, s), 0) + int(job["compute_units"])
        assignments.append(
            {
                "job_id": job["job_id"],
                "region": region,
                "start_slot": start,
                "carbon_mass_g": mass,
            }
        )
    assignments.sort(key=lambda a: a["job_id"])
    infeas.sort(key=lambda r: r["job_id"])
    ql = quota_ledger_rows(regions, window_count, usage)
    from plan_digest import plan_digest as digest_fn
    plan_digest = digest_fn(assignments, infeas)
    total = sum(a["carbon_mass_g"] for a in assignments)
    return {
        "run_id": run_id,
        "assignments": assignments,
        "quota_ledger": ql,
        "blocked_jobs": infeas,
        "summary": {
            "feasible_count": len(assignments),
            "infeasible_count": len(infeas),
            "total_carbon_mass_g": total,
        },
        "plan_digest": plan_digest,
    }


def reference_atlas(scenario_dir: Path, run_id: str) -> dict[str, Any]:
    meta = json.loads((scenario_dir / "scenario.json").read_text(encoding="utf-8"))
    return schedule(meta, run_id)

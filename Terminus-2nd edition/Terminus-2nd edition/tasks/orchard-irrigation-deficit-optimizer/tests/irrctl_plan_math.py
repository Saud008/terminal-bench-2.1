"""Independent orchard irrigation deficit planner."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


def _sha256_hex(payload: bytes) -> str:
    return subprocess.check_output(["sha256sum"], input=payload).decode().split()[0]


def calibrated_vwc(raw: float, offset: float) -> float:
    return raw - offset


def weighted_blend(probes: list[dict[str, Any]]) -> float:
    num = 0.0
    den = 0.0
    for p in probes:
        v = calibrated_vwc(float(p["raw_vwc"]), float(p["offset"]))
        w = float(p["weight"])
        num += v * w
        den += w
    return num / den if den > 0 else 0.0


def kc_for_stage(stages: list[float], crop_stage: int) -> float:
    idx = min(crop_stage, len(stages) - 1)
    return float(stages[idx])


def vwc_to_mm(vwc: float, target_vwc: float, root_depth_cm: float) -> float:
    return (target_vwc - vwc) * root_depth_cm * 100.0


def liters_from_mm(mm: float, area_ha: float) -> float:
    return mm * area_ha * 10.0


def et_demand_mm(kc: float, et_forecast: float) -> float:
    return kc * et_forecast


def deficit_mm(moisture_gap_mm: float, et_demand: float) -> float:
    return max(0.0, moisture_gap_mm + et_demand)


def round4(v: float) -> float:
    return round(v + 0.0, 4)


def assert_assignments_close(got: list[dict[str, Any]], want: list[dict[str, Any]]) -> None:
    assert len(got) == len(want)
    for g, w in zip(got, want):
        assert g["field_id"] == w["field_id"]
        assert g["window_index"] == w["window_index"]
        assert abs(g["liters_applied"] - w["liters_applied"]) < 1e-2
        assert abs(g["deficit_after_mm"] - w["deficit_after_mm"]) < 1e-2


def assert_trace_close(got: list[dict[str, Any]], want: list[dict[str, Any]]) -> None:
    assert len(got) == len(want)
    for g, w in zip(got, want):
        assert g["field_id"] == w["field_id"]
        assert g["window_index"] == w["window_index"]
        assert abs(g["deficit_before_mm"] - w["deficit_before_mm"]) < 1e-2
        assert abs(g["deficit_after_mm"] - w["deficit_after_mm"]) < 1e-2


def assert_quota_close(got: list[dict[str, Any]], want: list[dict[str, Any]]) -> None:
    assert len(got) == len(want)
    for g, w in zip(got, want):
        assert g["window_index"] == w["window_index"]
        for key in ("base_m3", "carry_in_m3", "used_m3", "carry_out_m3"):
            assert abs(float(g[key]) - float(w[key])) < 1e-4


def quota_ledger_rows(windows: list[dict[str, Any]], usage: dict[int, float]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    carry = 0.0
    for w in sorted(windows, key=lambda x: int(x["window_index"])):
        idx = int(w["window_index"])
        base = float(w["max_m3"])
        max_carry = float(w["max_carry_m3"])
        available = base + carry
        used = usage.get(idx, 0.0)
        leftover = max(0.0, available - used)
        carry_out = min(max_carry, leftover)
        rows.append(
            {
                "window_index": idx,
                "base_m3": base,
                "carry_in_m3": carry,
                "used_m3": used,
                "carry_out_m3": carry_out,
            }
        )
        carry = carry_out
    return rows


def schedule(meta: dict[str, Any], run_id: str) -> dict[str, Any]:
    fields = meta["fields"]
    window_count = int(meta["window_count"])
    target = float(meta["target_vwc"])
    kc_stages = [float(x) for x in meta["kc_stages"]]
    et_forecast = [float(x) for x in meta["et_forecast_mm"]]
    pump = meta["pump"]
    cap = float(pump["max_liters_per_hour"]) * float(pump["hours_per_slot"])

    staged: list[dict[str, Any]] = []
    for field_id, spec in sorted(fields.items()):
        vwc = weighted_blend(spec["probes"])
        kc = kc_for_stage(kc_stages, int(spec["crop_stage"]))
        deficits = []
        for w in range(window_count):
            gap = vwc_to_mm(vwc, target, float(spec["root_depth_cm"]))
            et_d = et_demand_mm(kc, et_forecast[w])
            deficits.append(deficit_mm(gap, et_d))
        staged.append({"field_id": field_id, "spec": spec, "deficits": deficits})

    assignments: list[dict[str, Any]] = []
    trace_rows: list[dict[str, Any]] = []
    usage: dict[int, float] = {}

    for w_idx in range(window_count):
        remaining = cap
        order = sorted(staged, key=lambda s: s["deficits"][w_idx], reverse=True)
        for row in order:
            fid = row["field_id"]
            spec = row["spec"]
            before = round4(row["deficits"][w_idx])
            if before <= 0 or remaining <= 0:
                trace_rows.append(
                    {
                        "field_id": fid,
                        "window_index": w_idx,
                        "deficit_before_mm": before,
                        "deficit_after_mm": before,
                    }
                )
                continue
            need = liters_from_mm(before, float(spec["area_ha"]))
            applied = round4(min(need, remaining))
            remaining -= applied
            area = float(spec["area_ha"])
            applied_mm = applied / (area * 10.0) if area > 0 else 0.0
            after = round4(max(0.0, before - applied_mm))
            assignments.append(
                {
                    "field_id": fid,
                    "window_index": w_idx,
                    "liters_applied": applied,
                    "deficit_after_mm": after,
                }
            )
            usage[w_idx] = usage.get(w_idx, 0.0) + applied / 1000.0
            trace_rows.append(
                {
                    "field_id": fid,
                    "window_index": w_idx,
                    "deficit_before_mm": before,
                    "deficit_after_mm": after,
                }
            )

    assignments.sort(key=lambda a: (a["field_id"], a["window_index"]))
    trace_rows.sort(key=lambda r: (r["field_id"], r["window_index"]))
    ql = quota_ledger_rows(meta["quota_windows"], usage)
    digest_body = {"assignments": assignments, "deficit_trace": trace_rows}
    plan_digest = _sha256_hex(json.dumps(digest_body, sort_keys=True).encode())
    total_liters = round4(sum(a["liters_applied"] for a in assignments))
    return {
        "run_id": run_id,
        "assignments": assignments,
        "quota_ledger": ql,
        "deficit_trace": trace_rows,
        "summary": {"assignment_count": len(assignments), "total_liters": total_liters},
        "plan_digest": plan_digest,
    }


def independent_plan(orchard_dir: Path, run_id: str) -> dict[str, Any]:
    meta = json.loads((orchard_dir / "orchard.json").read_text(encoding="utf-8"))
    return schedule(meta, run_id)

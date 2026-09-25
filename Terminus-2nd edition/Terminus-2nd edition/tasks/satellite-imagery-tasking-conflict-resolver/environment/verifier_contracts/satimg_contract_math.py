"""Satctl tasking verifier — subprocess driver and independent reference resolver."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

APP = Path("/app")
BIN = APP / "bin" / "imgctl"
SCENARIOS = APP / "fixtures" / "scenarios"
HIDDEN_ROOT = "/opt/verifier-fixtures/satimg"
HIDDEN_DIGEST_TRAP = "/opt/verifier-fixtures/satimg/digest-preempt-trap"
HIDDEN_PADDING_TRAP = "/opt/verifier-fixtures/satimg/padding-overlap-trap"
SUBPROC_SAMPLE = "/app/output/subproc-check.json"
MATRIX = "/app/var/conflict-matrix-{token}.csv"


def scenario_root() -> Path:
    override = os.environ.get("SAT_FIXTURE_ROOT")
    return Path(override) if override else SCENARIOS


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def cargo_rebuild() -> None:
    _run(["bash", str(APP / "scripts" / "rebuild-release.sh")])


def scrub_var() -> None:
    _run(["bash", str(APP / "scripts" / "purge-workspace.sh")])


def run_resolve(scenario: str, token: str, dest: Path | None = None) -> Path:
    dest = dest or APP / "output" / f"{token}.json"
    scrub_var()
    cargo_rebuild()
    _run([str(BIN), "resolve", "--scenario", scenario, "--token", token, "--dest", str(dest)])
    return dest


def read_matrix_meta(token: str) -> dict:
    path = APP / "var" / f"conflict-matrix-{token}.meta.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_scenario(name: str) -> dict[str, Any]:
    return json.loads((scenario_root() / name / "scenario.json").read_text(encoding="utf-8"))


def _round4(v: float) -> float:
    return round(v + 0.0, 4)


def cloud_blend(forecast: dict[str, Any]) -> float:
    risk = float(forecast["risk_score"])
    gap = 1.0 - float(forecast.get("coverage_factor", 1.0))
    return _round4(0.6 * risk + 0.4 * gap)


def setup_duration(modes: dict[str, Any], mode: str, warm: bool) -> int:
    spec = modes[mode]
    return int(spec["warm_setup_sec"] if warm else spec["cold_setup_sec"])


def windows_overlap_with_setup(
    a_start: int, a_end: int, a_setup: int, b_start: int, b_end: int, b_setup: int
) -> bool:
    a_pad = a_end + a_setup
    b_pad = b_end + b_setup
    return a_start < b_pad and b_start < a_pad


def plan_digest_payload(manifest: dict[str, Any]) -> str:
    payload = {
        "scenario_id": manifest["scenario_id"],
        "assignment_count": manifest["assignment_count"],
        "assignments": manifest["assignments"],
        "preemption_trace": manifest["preemption_trace"],
        "mean_cloud_risk": manifest["mean_cloud_risk"],
    }
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)


def reference_resolve(meta: dict[str, Any]) -> dict[str, Any]:
    contracts = {c["contract_id"]: c for c in meta["priority_contracts"]}
    requests = sorted(
        meta["imaging_requests"],
        key=lambda r: (contracts[r["contract_id"]]["preempt_rank"], r["request_id"]),
    )
    occupied: list[dict[str, Any]] = []
    assignments: list[dict[str, Any]] = []
    preemptions: list[dict[str, Any]] = []
    pass_cursor: dict[str, int] = {}
    last_mode: dict[str, str] = {}

    for req in requests:
        rank = contracts[req["contract_id"]]["preempt_rank"]
        passes = [p for p in meta["pass_windows"] if req["cell_id"] in p["cells"]]
        best: tuple[dict[str, Any], float] | None = None

        for pas in passes:
            cell_idx = next(
                (
                    idx
                    for idx, slot in enumerate(occupied)
                    if slot["pass_id"] == pas["pass_id"] and slot["cell_id"] == req["cell_id"]
                ),
                None,
            )
            if cell_idx is not None:
                slot = occupied[cell_idx]
                if rank > slot["rank"]:
                    preemptions.append(
                        {
                            "displaced_request_id": slot["request_id"],
                            "winner_request_id": req["request_id"],
                            "pass_id": pas["pass_id"],
                        }
                    )
                    displaced = occupied.pop(cell_idx)
                    assignments = [a for a in assignments if a["request_id"] != displaced["request_id"]]
                    pass_cursor.pop(pas["pass_id"], None)
                    last_mode.pop(pas["pass_id"], None)
                else:
                    continue

            warm = last_mode.get(pas["pass_id"]) == req["mode"]
            setup = setup_duration(meta["sensor_modes"], req["mode"], warm)
            cursor = pass_cursor.get(pas["pass_id"], int(pas["start_sec"]))
            eff_start = cursor + setup
            eff_end = eff_start + int(req["imaging_duration_sec"])
            if eff_end > int(pas["end_sec"]):
                continue

            forecast = next(
                (
                    f
                    for f in meta["cloud_forecasts"]
                    if f["pass_id"] == pas["pass_id"] and f["cell_id"] == req["cell_id"]
                ),
                {"risk_score": 1.0, "coverage_factor": 0.0},
            )
            composite = cloud_blend(forecast)

            clash_idx = None
            for idx, slot in enumerate(occupied):
                if windows_overlap_with_setup(
                    eff_start,
                    eff_end,
                    setup,
                    slot["start"],
                    slot["end"],
                    slot["setup_pad"],
                ):
                    clash_idx = idx
                    break

            if clash_idx is not None:
                slot = occupied[clash_idx]
                if rank > slot["rank"]:
                    preemptions.append(
                        {
                            "displaced_request_id": slot["request_id"],
                            "winner_request_id": req["request_id"],
                            "pass_id": pas["pass_id"],
                        }
                    )
                    displaced = occupied.pop(clash_idx)
                    assignments = [a for a in assignments if a["request_id"] != displaced["request_id"]]
                    pass_cursor.pop(pas["pass_id"], None)
                    last_mode.pop(pas["pass_id"], None)
                else:
                    continue

            candidate = {
                "request_id": req["request_id"],
                "pass_id": pas["pass_id"],
                "orbit_id": pas["orbit_id"],
                "cell_id": req["cell_id"],
                "mode": req["mode"],
                "setup_sec": setup,
                "effective_start_sec": eff_start,
                "effective_end_sec": eff_end,
                "cloud_composite": composite,
                "preempt_rank": rank,
            }
            if best is None or composite < best[1]:
                best = (candidate, composite)

        if best is not None:
            plan = best[0]
            assignments.append(plan)
            occupied.append(
                {
                    "start": plan["effective_start_sec"],
                    "end": plan["effective_end_sec"],
                    "setup_pad": plan["setup_sec"],
                    "request_id": plan["request_id"],
                    "rank": plan["preempt_rank"],
                    "pass_id": plan["pass_id"],
                    "cell_id": plan["cell_id"],
                }
            )
            pass_cursor[plan["pass_id"]] = plan["effective_end_sec"] + plan["setup_sec"]
            last_mode[plan["pass_id"]] = plan["mode"]

    assignments.sort(key=lambda a: (a["effective_start_sec"], a["request_id"]))
    mean = _round4(sum(a["cloud_composite"] for a in assignments) / len(assignments)) if assignments else 0.0
    manifest = {
        "scenario_id": meta["scenario_id"],
        "constellation_id": meta["constellation_id"],
        "assignment_count": len(assignments),
        "preemption_count": len(preemptions),
        "assignments": assignments,
        "preemption_trace": preemptions,
        "mean_cloud_risk": mean,
    }
    manifest["plan_digest"] = "sha256:" + hashlib.sha256(plan_digest_payload(manifest).encode()).hexdigest()
    return manifest


def reference_from_scenario(name: str, token: str) -> dict[str, Any]:
    ref = reference_resolve(load_scenario(name))
    ref["run_token"] = token
    return ref


def assert_manifest_matches(actual: dict[str, Any], expected: dict[str, Any]) -> None:
    assert actual["scenario_id"] == expected["scenario_id"]
    assert actual["constellation_id"] == expected["constellation_id"]
    assert actual["assignment_count"] == expected["assignment_count"]
    assert actual["preemption_count"] == expected["preemption_count"]
    assert actual["mean_cloud_risk"] == expected["mean_cloud_risk"]
    assert actual["plan_digest"] == expected["plan_digest"]
    assert actual["assignments"] == expected["assignments"]
    assert actual["preemption_trace"] == expected["preemption_trace"]

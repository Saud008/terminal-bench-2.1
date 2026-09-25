"""Independent textile shade drift contract math for pytest."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any


def read_tsv_rows(path: Path) -> list[dict[str, str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    header = lines[0].split("\t")
    seen: dict[str, dict[str, str]] = {}
    for line in lines[1:]:
        if not line.strip():
            continue
        row = dict(zip(header, line.split("\t")))
        seen[row["reading_id"]] = row
    return [seen[k] for k in sorted(seen, key=lambda x: (seen[x]["batch_id"], x))]


def read_rework(path: Path) -> list[dict[str, Any]]:
    lines = path.read_text(encoding="utf-8").splitlines()[1:]
    out = []
    for line in lines:
        if not line.strip():
            continue
        b, s, e, reason, sup = line.split("\t")
        out.append(
            {
                "batch_id": b,
                "rework_start_epoch": int(s),
                "rework_end_epoch": int(e),
                "reason_code": reason,
                "supersedes_reading_before_epoch": int(sup),
            }
        )
    return out


def cie76(l1: float, a1: float, b1: float, l2: float, a2: float, b2: float) -> float:
    return round(math.sqrt((l1 - l2) ** 2 + (a1 - a2) ** 2 + (b1 - b2) ** 2), 6)


def pick_recipe(recipes: list[dict[str, Any]], name: str, as_of: int, override: str | None) -> dict[str, Any]:
    if override:
        for r in recipes:
            if r["version"] == override:
                return r
    candidates = [r for r in recipes if r["recipe_name"] == name and r["effective_from_epoch"] <= as_of]
    if not candidates:
        raise ValueError(f"no recipe for {name} at {as_of}")
    return max(candidates, key=lambda r: r["effective_from_epoch"])


def resolve_target_lab(batches: list[dict[str, Any]], batch_id: str) -> dict[str, float] | None:
    by_id = {b["batch_id"]: b for b in batches}
    cur = batch_id
    while cur:
        b = by_id[cur]
        tl = b.get("target_lab")
        if tl is not None:
            return tl
        cur = b.get("parent_batch_id")
    return None


def in_rework(measured: int, start: int, end: int) -> bool:
    return start <= measured <= end


def drift_class(delta: float, warn: float, fail: float) -> str:
    if delta <= warn:
        return "within"
    if delta <= fail:
        return "watch"
    return "reject"


def correlate_scenario(scenario_dir: Path, policy: dict[str, Any]) -> list[dict[str, Any]]:
    recipes = json.loads((scenario_dir / "recipes.json").read_text(encoding="utf-8"))["recipes"]
    batches = json.loads((scenario_dir / "batches.json").read_text(encoding="utf-8"))["batches"]
    rework = read_rework(scenario_dir / "rework.tsv")
    warn = float(policy["warn_delta_e"])
    fail = float(policy["fail_delta_e"])
    by_batch = {b["batch_id"]: b for b in batches}
    rows_out: list[dict[str, Any]] = []
    for row in read_tsv_rows(scenario_dir / "readings.tsv"):
        batch = by_batch[row["batch_id"]]
        measured = int(row["measured_at_epoch"])
        as_of = int(batch["created_at_epoch"])
        rework_applied = False
        for rw in rework:
            if rw["batch_id"] != row["batch_id"]:
                continue
            if in_rework(measured, rw["rework_start_epoch"], rw["rework_end_epoch"]):
                as_of = rw["supersedes_reading_before_epoch"] - 1
                rework_applied = True
        override = batch.get("recipe_version_override")
        recipe = pick_recipe(recipes, batch["recipe_name"], as_of, override)
        tL, ta, tb = recipe["target_L"], recipe["target_a"], recipe["target_b"]
        inherited = resolve_target_lab(batches, row["batch_id"])
        if inherited is not None:
            tL, ta, tb = inherited["L"], inherited["a"], inherited["b"]
        L, a, b = float(row["L"]), float(row["a"]), float(row["b"])
        de = cie76(L, a, b, float(tL), float(ta), float(tb))
        rows_out.append(
            {
                "batch_id": row["batch_id"],
                "reading_id": row["reading_id"],
                "delta_e": de,
                "drift_class": drift_class(de, warn, fail),
                "recipe_version": recipe["version"],
                "rework_applied": rework_applied,
            }
        )
    rows_out.sort(key=lambda r: (r["batch_id"], r["reading_id"]))
    return rows_out


def reference_report(scenario_dir: Path, run_id: str, policy_path: Path) -> dict[str, Any]:
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    drift_rows = correlate_scenario(scenario_dir, policy)
    audit = hashlib.sha256(json.dumps(drift_rows, separators=(",", ":")).encode()).hexdigest()
    return {
        "run_id": run_id,
        "drift_rows": drift_rows,
        "totals": {"row_count": len(drift_rows)},
        "audit_digest": audit,
    }


def build_ephemeral_scenario(
    tmp: Path,
    *,
    batch_id: str,
    reading_id: str,
    L: float,
    a: float,
    b: float,
    target: tuple[float, float, float],
) -> Path:
    scenario = tmp / "ephemeral"
    scenario.mkdir(parents=True, exist_ok=True)
    (scenario / "scenario.json").write_text(json.dumps({"name": "ephemeral"}), encoding="utf-8")
    tL, ta, tb = target
    (scenario / "readings.tsv").write_text(
        "batch_id\treading_id\tL\ta\tb\tmeasured_at_epoch\tspectrometer_id\n"
        f"{batch_id}\t{reading_id}\t{L}\t{a}\t{b}\t1900000000\tSPEC-RND\n",
        encoding="utf-8",
    )
    (scenario / "recipes.json").write_text(
        json.dumps(
            {
                "recipes": [
                    {
                        "recipe_name": "ephemeral-dye",
                        "version": "v1",
                        "effective_from_epoch": 1890000000,
                        "target_L": tL,
                        "target_a": ta,
                        "target_b": tb,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (scenario / "batches.json").write_text(
        json.dumps(
            {
                "batches": [
                    {
                        "batch_id": batch_id,
                        "parent_batch_id": None,
                        "recipe_name": "ephemeral-dye",
                        "created_at_epoch": 1895000000,
                        "recipe_version_override": None,
                        "target_lab": None,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    (scenario / "rework.tsv").write_text(
        "batch_id\trework_start_epoch\trework_end_epoch\treason_code\tsupersedes_reading_before_epoch\n",
        encoding="utf-8",
    )
    return scenario

"""Fixture catalog builder for iceexpctl scenarios — anti-hardcoding via seeded RNG."""
from __future__ import annotations

import hashlib
import json
import os
import random
from pathlib import Path

BUNDLED = (
    "clean-lineage",
    "branch-protect",
    "tag-pin",
    "delete-retain",
    "manifest-nested",
    "meta-order",
    "orphan-trap",
    "stable-republish",
)

HIDDEN = (
    "tag-branch-trap",
    "delete-boundary-trap",
)


def _rng(scenario: str) -> random.Random:
    seed = int(hashlib.sha256(scenario.encode()).hexdigest()[:16], 16)
    return random.Random(seed)


def _base_table(rng: random.Random, scenario: str) -> dict:
    snaps = []
    ts = rng.randint(1_700_000_000_000, 1_700_010_000_000)
    parent = 0
    for sid in range(1, 6):
        snaps.append(
            {
                "snapshot_id": sid,
                "parent_snapshot_id": parent,
                "event_ms": ts + sid * 3_600_000,
                "manifest_list": f"meta_{sid}.json",
            }
        )
        parent = sid
    return {
        "table_name": f"lake_{scenario}",
        "location": f"s3://lake/{scenario}",
        "current_snapshot_id": 5,
        "delete_retention_hours": 168,
        "snapshots": snaps,
        "refs": [{"name": "main", "ref_type": "branch", "snapshot_id": 5}],
    }


def _manifests(rng: random.Random, table: dict) -> dict[str, list]:
    out: dict[str, list] = {}
    for snap in table["snapshots"]:
        sid = snap["snapshot_id"]
        rows = [
            {
                "status": "added",
                "data_file": f"data/part-{sid}-a.parquet",
            }
        ]
        if sid == 5:
            rows.append(
                {
                    "status": "existing",
                    "data_file": f"data/part-{sid - 1}-a.parquet",
                }
            )
        out[f"meta_{sid}.json"] = rows
    if rng.random() > 0.5:
        out.setdefault("meta_3.json", []).append(
            {"status": "deleted", "data_file": "data/ghost-deleted.parquet"}
        )
    return out


def overlay(scenario: str, table: dict, manifests: dict) -> tuple[dict, dict]:
    if scenario == "branch-protect":
        table["refs"] = [{"name": "main", "ref_type": "branch", "snapshot_id": 3}]
    elif scenario == "tag-pin":
        table["refs"].append({"name": "v1", "ref_type": "tag", "snapshot_id": 2})
    elif scenario == "delete-retain":
        table["delete_retention_hours"] = 24
    elif scenario == "manifest-nested":
        manifests["meta_5.json"].append(
            {
                "status": "added",
                "nested_manifest": "meta_3.json",
            }
        )
    elif scenario == "meta-order":
        manifests["meta_10.json"] = [{"status": "added", "data_file": "data/meta-order.parquet"}]
        table["snapshots"].append(
            {
                "snapshot_id": 10,
                "parent_snapshot_id": 5,
                "event_ms": table["snapshots"][-1]["event_ms"] + 1000,
                "manifest_list": "meta_10.json",
            }
        )
        table["current_snapshot_id"] = 10
    elif scenario == "orphan-trap":
        manifests["meta_1.json"].append(
            {"status": "deleted", "data_file": "data/orphan-trap.parquet"}
        )
    elif scenario == "stable-republish":
        pass
    elif scenario == "tag-branch-trap":
        table["refs"] = [
            {"name": "main", "ref_type": "branch", "snapshot_id": 4},
            {"name": "release", "ref_type": "tag", "snapshot_id": 2},
        ]
    elif scenario == "delete-boundary-trap":
        table["delete_retention_hours"] = 72
        cur = next(s for s in table["snapshots"] if s["snapshot_id"] == table["current_snapshot_id"])
        floor = cur["event_ms"] - 72 * 3600 * 1000
        for s in table["snapshots"]:
            if s["snapshot_id"] == 2:
                s["event_ms"] = floor
            if s["snapshot_id"] == 3:
                s["event_ms"] = floor + 1
    return table, manifests


def write_scenario(root: Path, scenario: str) -> None:
    rng = _rng(scenario)
    table = _base_table(rng, scenario)
    manifests = _manifests(rng, table)
    table, manifests = overlay(scenario, table, manifests)
    scen_dir = root / "tables" / scenario
    man_dir = scen_dir / "manifests"
    man_dir.mkdir(parents=True, exist_ok=True)
    (scen_dir / "table.json").write_text(json.dumps(table, indent=2) + "\n", encoding="utf-8")
    for name, rows in sorted(manifests.items()):
        (man_dir / name).write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    root = Path("/app/fixtures")
    hidden = os.environ.get("ICEEXP_HIDDEN_ROOT")
    if hidden:
        root = Path(hidden)
    scenarios = HIDDEN if hidden else BUNDLED
    for scenario in scenarios:
        write_scenario(root, scenario)
    for scen_dir in sorted((root / "tables").iterdir()):
        if scen_dir.is_dir() and not (scen_dir / "table.json").exists():
            write_scenario(root, scen_dir.name)
    catalog = {
        "root": str(root),
        "scenarios": sorted(p.name for p in (root / "tables").iterdir() if p.is_dir()),
    }
    out = root / "data_catalog.json"
    out.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()


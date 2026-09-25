#!/usr/bin/env python3
"""Fixture catalog builder for snapretctl scenarios — anti-hardcoding via seeded RNG."""
from __future__ import annotations

import hashlib
import json
import os
import random
from pathlib import Path


BUNDLED = (
    "clean-retention",
    "pvc-join-chain",
    "class-override",
    "dangling-snap",
    "policy-precedence",
    "quota-cap",
    "retain-pin",
    "stable-republish",
)

HIDDEN = (
    "policy-boundary-trap",
    "quota-hidden-trap",
)


def _rng(scenario: str) -> random.Random:
    seed = int(hashlib.sha256(scenario.encode()).hexdigest()[:16], 16)
    return random.Random(seed)


def _base_cluster(rng: random.Random, scenario: str) -> dict:
    ns = f"ns-{scenario[:6]}"
    pvc_a = f"pvc-{rng.randint(100, 999)}"
    pvc_b = f"pvc-{rng.randint(1000, 1999)}"
    sc_fast = "sc-fast"
    sc_slow = "sc-slow"
    base_ts = rng.randint(1_700_000_000_000, 1_700_010_000_000)
    snaps = [
        {
            "uid": f"snap-{scenario}-a",
            "namespace": ns,
            "name": "snap-a",
            "source_pvc": pvc_a,
            "restore_size_bytes": rng.randint(1_000_000, 5_000_000),
            "deletion_policy": "Delete",
            "creation_clock_ms": base_ts,
        },
        {
            "uid": f"snap-{scenario}-b",
            "namespace": ns,
            "name": "snap-b",
            "source_pvc": pvc_b,
            "restore_size_bytes": rng.randint(1_000_000, 5_000_000),
            "deletion_policy": "Delete",
            "creation_clock_ms": base_ts + 86_400_000,
        },
    ]
    return {
        "audit_clock_ms": base_ts + 90 * 86_400_000,
        "default_retention_days": 30,
        "pvcs": [
            {
                "namespace": ns,
                "name": pvc_a,
                "storage_class_name": sc_fast,
                "requested_bytes": 10_000_000,
            },
            {
                "namespace": ns,
                "name": pvc_b,
                "storage_class_name": sc_slow,
                "requested_bytes": 20_000_000,
            },
        ],
        "snapshots": snaps,
        "storage_classes": [
            {"name": sc_fast, "retention_days": 7},
            {"name": sc_slow, "retention_days": 60},
        ],
        "backup_policies": [
            {
                "name": "default-backup",
                "priority": 10,
                "retention_days": 14,
                "namespace_selector": "",
            }
        ],
        "quotas": [
            {
                "namespace": ns,
                "max_snapshot_bytes": 50_000_000,
                "used_snapshot_bytes": 0,
            }
        ],
    }


def overlay(scenario: str, cluster: dict) -> dict:
    ns = cluster["pvcs"][0]["namespace"]
    if scenario == "pvc-join-chain":
        cluster["snapshots"].append(
            {
                "uid": f"snap-{scenario}-chain",
                "namespace": ns,
                "name": "snap-chain",
                "source_pvc": cluster["pvcs"][0]["name"],
                "restore_size_bytes": 2_000_000,
                "deletion_policy": "Delete",
                "creation_clock_ms": cluster["audit_clock_ms"] - 40 * 86_400_000,
            }
        )
    elif scenario == "class-override":
        cluster["snapshots"][0]["creation_clock_ms"] = (
            cluster["audit_clock_ms"] - 10 * 86_400_000
        )
    elif scenario == "dangling-snap":
        cluster["snapshots"].append(
            {
                "uid": f"snap-{scenario}-orphan",
                "namespace": ns,
                "name": "snap-orphan",
                "source_pvc": "missing-pvc",
                "restore_size_bytes": 1_000_000,
                "deletion_policy": "Delete",
                "creation_clock_ms": cluster["audit_clock_ms"] - 5 * 86_400_000,
            }
        )
    elif scenario == "policy-precedence":
        cluster["backup_policies"].append(
            {
                "name": "ns-backup",
                "priority": 50,
                "retention_days": 21,
                "namespace_selector": ns,
            }
        )
        cluster["snapshots"][0]["creation_clock_ms"] = (
            cluster["audit_clock_ms"] - 15 * 86_400_000
        )
    elif scenario == "quota-cap":
        cluster["quotas"][0]["max_snapshot_bytes"] = 5_000_000
        for snap in cluster["snapshots"]:
            snap["restore_size_bytes"] = 3_000_000
    elif scenario == "retain-pin":
        cluster["snapshots"][0]["deletion_policy"] = "Retain"
        cluster["snapshots"][0]["creation_clock_ms"] = (
            cluster["audit_clock_ms"] - 200 * 86_400_000
        )
    elif scenario == "stable-republish":
        pass
    elif scenario == "policy-boundary-trap":
        cluster["backup_policies"] = [
            {"name": "low", "priority": 5, "retention_days": 45, "namespace_selector": ""},
            {"name": "high", "priority": 100, "retention_days": 10, "namespace_selector": ns},
        ]
        cluster["storage_classes"][0]["retention_days"] = 90
        cluster["snapshots"][0]["creation_clock_ms"] = (
            cluster["audit_clock_ms"] - 12 * 86_400_000
        )
    elif scenario == "quota-hidden-trap":
        other_ns = f"other-{scenario[:4]}"
        cluster["pvcs"].append(
            {
                "namespace": other_ns,
                "name": "pvc-cross",
                "storage_class_name": "sc-fast",
                "requested_bytes": 5_000_000,
            }
        )
        cluster["snapshots"].append(
            {
                "uid": f"snap-{scenario}-cross",
                "namespace": other_ns,
                "name": "snap-cross",
                "source_pvc": "pvc-cross",
                "restore_size_bytes": 8_000_000,
                "deletion_policy": "Delete",
                "creation_clock_ms": cluster["audit_clock_ms"] - 3 * 86_400_000,
            }
        )
        cluster["quotas"].append(
            {
                "namespace": other_ns,
                "max_snapshot_bytes": 6_000_000,
                "used_snapshot_bytes": 0,
            }
        )
    return cluster


def write_scenario(root: Path, scenario: str) -> None:
    rng = _rng(scenario)
    cluster = _base_cluster(rng, scenario)
    cluster = overlay(scenario, cluster)
    scen_dir = root / "clusters" / scenario
    scen_dir.mkdir(parents=True, exist_ok=True)
    (scen_dir / "cluster.json").write_text(json.dumps(cluster, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    """Refresh bundled /app/fixtures clusters only. Hidden verifier fixtures are pre-shipped."""
    root = Path(os.environ.get("SNAPRET_FIXTURE_ROOT", "/app/fixtures"))
    for scenario in BUNDLED:
        write_scenario(root, scenario)
    clusters = root / "clusters"
    if clusters.is_dir():
        for scen_dir in sorted(clusters.iterdir()):
            if scen_dir.is_dir() and not (scen_dir / "cluster.json").exists():
                write_scenario(root, scen_dir.name)
    catalog = {
        "root": str(root),
        "scenarios": sorted(
            p.name for p in (root / "clusters").iterdir() if p.is_dir()
        )
        if (root / "clusters").is_dir()
        else [],
    }
    out = root / "data_catalog.json"
    out.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

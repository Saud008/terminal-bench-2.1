from __future__ import annotations

from typing import Any

from snapret import claim_bind


def dangling_snapshots(cluster: dict[str, Any]) -> list[dict[str, str]]:
    jm = claim_bind.join_map(cluster)
    rows: list[dict[str, str]] = []
    for snap in cluster.get("snapshots", []):
        if snap["source_pvc"] in jm:
            continue
        rows.append(
            {
                "uid": snap["uid"],
                "namespace": snap["namespace"],
                "source_pvc": snap["source_pvc"],
                "kind": "dangling",
            }
        )
    rows.sort(key=lambda row: (row["uid"], row["namespace"]))
    return rows

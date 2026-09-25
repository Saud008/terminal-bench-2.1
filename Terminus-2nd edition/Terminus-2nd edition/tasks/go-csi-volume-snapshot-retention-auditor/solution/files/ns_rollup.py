from __future__ import annotations

from typing import Any


def projected_bytes(cluster: dict[str, Any], namespace: str) -> int:
    total = 0
    for snap in cluster.get("snapshots", []):
        if snap["namespace"] == namespace:
            total += int(snap.get("restore_size_bytes", 0))
    return total


def quota_violations(cluster: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for quota in cluster.get("quotas", []):
        projected = projected_bytes(cluster, quota["namespace"])
        limit = int(quota.get("max_snapshot_bytes", 0))
        if projected > limit:
            out.append(
                {
                    "namespace": quota["namespace"],
                    "projected_bytes": projected,
                    "max_snapshot_bytes": limit,
                }
            )
    out.sort(key=lambda row: row["namespace"])
    return out

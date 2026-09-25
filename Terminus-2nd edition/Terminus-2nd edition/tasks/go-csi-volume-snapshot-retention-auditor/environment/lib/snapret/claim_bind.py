from __future__ import annotations

from typing import Any


def join_map(cluster: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for pvc in cluster.get("pvcs", []):
        out[pvc["name"]] = pvc
    return out


def snapshot_pvc(
    cluster: dict[str, Any], snap: dict[str, Any]
) -> tuple[dict[str, Any], bool]:
    jm = join_map(cluster)
    pvc = jm.get(snap["source_pvc"])
    if pvc is None:
        return {}, False
    return pvc, True

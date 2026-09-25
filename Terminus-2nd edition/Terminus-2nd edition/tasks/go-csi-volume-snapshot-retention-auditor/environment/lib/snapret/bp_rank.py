from __future__ import annotations

import os
from typing import Any

from snapret import claim_bind, sc_days

DEFAULT_CLUSTER_RETENTION_DAYS = 30


def cluster_default_days(cluster: dict[str, Any]) -> int:
    raw = os.environ.get("TB3_CLUSTER_DEFAULT_RETENTION_DAYS", "")
    if raw:
        try:
            value = int(raw)
            if value > 0:
                return value
        except ValueError:
            pass
    default = int(cluster.get("default_retention_days", 0))
    if default > 0:
        return default
    return DEFAULT_CLUSTER_RETENTION_DAYS


def retention_days_for_snapshot(cluster: dict[str, Any], snap: dict[str, Any]) -> int:
    if snap.get("deletion_policy") == "Retain":
        return -1
    pvc, ok = claim_bind.snapshot_pvc(cluster, snap)
    class_days = sc_days.class_retention_days(cluster, "")
    if ok:
        class_days = sc_days.class_retention_days(cluster, pvc.get("storage_class_name", ""))
    if class_days > 0:
        return class_days
    best = -1
    best_pri = -1
    for bp in cluster.get("backup_policies", []):
        selector = bp.get("namespace_selector", "")
        if selector and selector != snap["namespace"]:
            continue
        pri = int(bp.get("priority", 0))
        if pri > best_pri:
            best_pri = pri
            best = int(bp.get("retention_days", 0))
    if best > 0:
        return best
    return cluster_default_days(cluster)


def is_protected(snap: dict[str, Any], retention_days: int) -> bool:
    return snap.get("deletion_policy") == "Retain" or retention_days < 0

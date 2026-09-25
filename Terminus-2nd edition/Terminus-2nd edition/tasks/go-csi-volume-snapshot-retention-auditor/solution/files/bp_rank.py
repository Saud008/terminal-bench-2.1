from __future__ import annotations

import os
from typing import Any

from snapret import claim_bind, sc_days

DEFAULT_CLUSTER_RETENTION_DAYS = 30


def selector_matches_namespace(selector: str, namespace: str) -> bool:
    if not selector:
        return True
    return selector == namespace


def highest_priority_policy(
    policies: list[dict[str, Any]], namespace: str
) -> tuple[int, bool]:
    best_pri = -1
    days = -1
    found = False
    for bp in policies:
        if not selector_matches_namespace(bp.get("namespace_selector", ""), namespace):
            continue
        pri = int(bp.get("priority", 0))
        if pri > best_pri:
            best_pri = pri
            days = int(bp.get("retention_days", 0))
            found = days > 0
    return days, found


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
    days, ok = highest_priority_policy(cluster.get("backup_policies", []), snap["namespace"])
    if ok:
        return days
    pvc, bound = claim_bind.snapshot_pvc(cluster, snap)
    if bound:
        cd = sc_days.class_retention_days(cluster, pvc.get("storage_class_name", ""))
        if cd > 0:
            return cd
    return cluster_default_days(cluster)


def is_protected(snap: dict[str, Any], retention_days: int) -> bool:
    return snap.get("deletion_policy") == "Retain" or retention_days < 0

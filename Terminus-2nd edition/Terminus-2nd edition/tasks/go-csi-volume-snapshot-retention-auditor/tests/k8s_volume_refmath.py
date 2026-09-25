"""Independent Kubernetes VolumeSnapshot retention reference for snapretctl."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


def cluster_default_days(cluster: dict[str, Any]) -> int:
    raw = os.environ.get("TB3_CLUSTER_DEFAULT_RETENTION_DAYS", "")
    if raw:
        return int(raw)
    return int(cluster.get("default_retention_days", 30))


def load_cluster(fixture_root: Path, scenario: str) -> dict[str, Any]:
    path = fixture_root / "clusters" / scenario / "cluster.json"
    return json.loads(path.read_text(encoding="utf-8"))


def pvc_key(namespace: str, name: str) -> str:
    return f"{namespace}/{name}"


def join_map(cluster: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for pvc in cluster.get("pvcs", []):
        out[pvc_key(pvc["namespace"], pvc["name"])] = pvc
    return out


def snapshot_pvc(cluster: dict[str, Any], snap: dict[str, Any]) -> dict[str, Any] | None:
    return join_map(cluster).get(pvc_key(snap["namespace"], snap["source_pvc"]))


def class_retention_days(cluster: dict[str, Any], class_name: str) -> int:
    for sc in cluster.get("storage_classes", []):
        if sc["name"] == class_name and int(sc.get("retention_days", 0)) > 0:
            return int(sc["retention_days"])
    return 0


def retention_days(cluster: dict[str, Any], snap: dict[str, Any]) -> int:
    if snap.get("deletion_policy") == "Retain":
        return -1
    best_pri = -1
    best_days = -1
    for bp in cluster.get("backup_policies", []):
        sel = bp.get("namespace_selector", "")
        if sel and sel != snap["namespace"]:
            continue
        pri = int(bp.get("priority", 0))
        if pri > best_pri:
            best_pri = pri
            best_days = int(bp.get("retention_days", 0))
    if best_days > 0:
        return best_days
    pvc = snapshot_pvc(cluster, snap)
    if pvc:
        cd = class_retention_days(cluster, pvc.get("storage_class_name", ""))
        if cd > 0:
            return cd
    return cluster_default_days(cluster)


def projected_bytes(cluster: dict[str, Any], namespace: str) -> int:
    return sum(
        int(snap.get("restore_size_bytes", 0))
        for snap in cluster.get("snapshots", [])
        if snap["namespace"] == namespace
    )


def dangling_rows(cluster: dict[str, Any]) -> list[dict[str, str]]:
    jm = join_map(cluster)
    rows: list[dict[str, str]] = []
    for snap in cluster.get("snapshots", []):
        key = pvc_key(snap["namespace"], snap["source_pvc"])
        if key not in jm:
            rows.append(
                {
                    "uid": snap["uid"],
                    "namespace": snap["namespace"],
                    "source_pvc": snap["source_pvc"],
                    "kind": "dangling",
                }
            )
    rows.sort(key=lambda r: (r["uid"], r["namespace"]))
    return rows


def _sorted_cluster_for_digest(cluster: dict[str, Any]) -> dict[str, Any]:
    sorted_snaps = sorted(cluster["snapshots"], key=lambda s: s["uid"])
    sorted_pvcs = sorted(cluster["pvcs"], key=lambda p: (p["namespace"], p["name"]))
    return {
        "audit_clock_ms": cluster["audit_clock_ms"],
        "default_retention_days": cluster["default_retention_days"],
        "pvcs": sorted_pvcs,
        "snapshots": sorted_snaps,
        "storage_classes": cluster.get("storage_classes", []),
        "backup_policies": cluster.get("backup_policies", []),
        "quotas": cluster.get("quotas", []),
    }


def reference_fleet_graph(scenario: str, fixture_root: Path) -> dict[str, Any]:
    cluster = load_cluster(fixture_root, scenario)
    payload = {"cluster": _sorted_cluster_for_digest(cluster)}
    digest = hashlib.sha256(
        json.dumps(payload, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "engine": "snapretctl",
        "scenario": scenario,
        "cluster": cluster,
        "fleet_graph_digest": digest,
    }


def reference_retention_report(scenario: str, fixture_root: Path) -> dict[str, Any]:
    cluster = load_cluster(fixture_root, scenario)
    now_ms = int(cluster.get("audit_clock_ms", 0))
    deletable: list[str] = []
    protected = 0
    for snap in cluster.get("snapshots", []):
        days = retention_days(cluster, snap)
        if days < 0:
            protected += 1
            continue
        age_days = (now_ms - int(snap.get("creation_clock_ms", 0))) // (86400 * 1000)
        if age_days >= days:
            deletable.append(snap["uid"])
    deletable.sort()
    quota_violations: list[dict[str, Any]] = []
    for quota in cluster.get("quotas", []):
        ns = quota["namespace"]
        projected = projected_bytes(cluster, ns)
        limit = int(quota.get("max_snapshot_bytes", 0))
        if projected > limit:
            quota_violations.append(
                {
                    "namespace": ns,
                    "projected_bytes": projected,
                    "max_snapshot_bytes": limit,
                }
            )
    quota_violations.sort(key=lambda r: r["namespace"])
    report = {
        "scenario": scenario,
        "protected_count": protected,
        "deletable_snapshot_uids": deletable,
        "quota_violations": quota_violations,
    }
    payload = {
        "deletable_snapshot_uids": deletable,
        "protected_count": protected,
        "quota_violations": quota_violations,
        "scenario": "",
    }
    report["report_digest"] = hashlib.sha256(
        json.dumps(payload, separators=(",", ":")).encode()
    ).hexdigest()
    return report

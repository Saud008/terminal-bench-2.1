from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

DEFAULT_STAGE_PATH = "/app/state/k8s-fleet-graph.json"


def write_fleet_graph(path: str, snap: dict[str, Any]) -> None:
    if not path:
        path = DEFAULT_STAGE_PATH
    stage_path = Path(path)
    stage_path.parent.mkdir(parents=True, exist_ok=True)
    digest = _compute_digest(snap["cluster"])
    snap = dict(snap)
    snap["fleet_graph_digest"] = digest
    data = json.dumps(snap, indent=2) + "\n"
    stage_path.write_text(data, encoding="utf-8")


def read_fleet_graph(path: str = "") -> dict[str, Any]:
    if not path:
        path = DEFAULT_STAGE_PATH
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _compute_digest(cluster: dict[str, Any]) -> str:
    sorted_snaps = sorted(cluster.get("snapshots", []), key=lambda snap: snap["uid"])
    sorted_pvcs = sorted(
        cluster.get("pvcs", []),
        key=lambda pvc: (pvc["namespace"], pvc["name"]),
    )
    cluster_copy = dict(cluster)
    cluster_copy["snapshots"] = sorted_snaps
    cluster_copy["pvcs"] = sorted_pvcs
    payload = {"cluster": cluster_copy}
    data = json.dumps(payload, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()

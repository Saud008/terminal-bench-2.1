"""Independent reference math for iceexpctl table expiry curator."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any


def delete_retention_hours(table: dict[str, Any]) -> int:
    raw = os.environ.get("TB3_DELETE_RETENTION_HOURS", "")
    if raw:
        return int(raw)
    return int(table.get("delete_retention_hours", 168))


def load_table(fixture_root: Path, scenario: str) -> tuple[dict[str, Any], dict[str, list]]:
    base = fixture_root / "tables" / scenario
    table = json.loads((base / "table.json").read_text(encoding="utf-8"))
    manifests: dict[str, list] = {}
    man_dir = base / "manifests"
    names = sorted(
        [p.name for p in man_dir.iterdir() if p.name.startswith("meta_") and p.name.endswith(".json")],
        key=lambda n: int(n.replace("meta_", "").replace(".json", "")),
    )
    for name in names:
        manifests[name] = json.loads((man_dir / name).read_text(encoding="utf-8"))
    return table, manifests


def ancestry_chain(table: dict[str, Any], snapshot_id: int) -> list[int]:
    by_id = {int(s["snapshot_id"]): int(s["parent_snapshot_id"]) for s in table["snapshots"]}
    out: list[int] = []
    cur = snapshot_id
    seen: set[int] = set()
    while cur and cur not in seen:
        seen.add(cur)
        out.append(cur)
        cur = by_id.get(cur, 0)
    out.sort()
    return out


def protected_ids(table: dict[str, Any]) -> set[int]:
    prot: set[int] = set()
    for ref in table.get("refs", []):
        for sid in ancestry_chain(table, int(ref["snapshot_id"])):
            prot.add(sid)
    return prot


def reachable_files(manifests: dict[str, list], root_manifest: str) -> set[str]:
    live: set[str] = set()

    def walk(path: str) -> None:
        for entry in manifests.get(path, []):
            status = entry.get("status", "")
            if status == "deleted":
                continue
            nested = entry.get("nested_manifest")
            if nested:
                walk(nested)
            data_file = entry.get("data_file")
            if data_file:
                live.add(data_file)

    walk(root_manifest)
    return live


def _normalized_cursor_seal(table: dict[str, Any], manifests: dict[str, list]) -> str:
    sorted_snaps = sorted(table["snapshots"], key=lambda s: int(s["snapshot_id"]))
    payload_table = dict(table)
    payload_table["snapshots"] = sorted_snaps
    parts = ['{"manifests":{']
    manifest_keys = list(manifests.keys())
    for idx, name in enumerate(manifest_keys):
        if idx:
            parts.append(",")
        parts.append(json.dumps(name, separators=(",", ":")))
        parts.append(":")
        parts.append(json.dumps(manifests[name], separators=(",", ":")))
    parts.append(',"table":')
    parts.append(json.dumps(payload_table, separators=(",", ":")))
    parts.append("}")
    return hashlib.sha256("".join(parts).encode()).hexdigest()


def reference_cursor_snapshot(scenario: str, fixture_root: Path) -> dict[str, Any]:
    table, manifests = load_table(fixture_root, scenario)
    digest = _normalized_cursor_seal(table, manifests)
    return {
        "engine": "iceexpctl",
        "scenario": scenario,
        "table": table,
        "manifests": manifests,
        "cursor_seal": digest,
    }


def reference_expiry_plan(scenario: str, fixture_root: Path) -> dict[str, Any]:
    table, _manifests = load_table(fixture_root, scenario)
    protected = protected_ids(table)
    current_id = int(table["current_snapshot_id"])
    current = next(s for s in table["snapshots"] if int(s["snapshot_id"]) == current_id)
    retention = delete_retention_hours(table)
    floor = int(current["event_ms"]) - retention * 3600 * 1000
    expired: list[int] = []
    for snap in table["snapshots"]:
        sid = int(snap["snapshot_id"])
        if sid in protected:
            continue
        if int(snap["event_ms"]) >= floor:
            expired.append(sid)
    expired.sort()
    plan = {
        "scenario": scenario,
        "protected_count": len(protected),
        "expired_snapshot_ids": expired,
    }
    payload = {
        "expired_snapshot_ids": expired,
        "protected_count": len(protected),
        "scenario": scenario,
    }
    plan["plan_digest"] = hashlib.sha256(
        json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    ).hexdigest()
    return plan


def reference_orphans(scenario: str, fixture_root: Path) -> list[dict[str, str]]:
    table, manifests = load_table(fixture_root, scenario)
    current_id = int(table["current_snapshot_id"])
    current = next(s for s in table["snapshots"] if int(s["snapshot_id"]) == current_id)
    live = reachable_files(manifests, current["manifest_list"])
    referenced: set[str] = set()
    for rows in manifests.values():
        for entry in rows:
            if entry.get("status") == "deleted":
                continue
            data_file = entry.get("data_file")
            if data_file:
                referenced.add(data_file)
    rows = [{"path": p, "kind": "data"} for p in sorted(referenced - live)]
    return rows


ref_cursor_snapshot = reference_cursor_snapshot
ref_expiry_plan_output = reference_expiry_plan
ref_orphan_ledger_rows = reference_orphans
protected_snapshot_ids = protected_ids

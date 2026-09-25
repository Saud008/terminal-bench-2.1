"""Independent reference for temporal-signal-replay export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def parse_tuple(version: str) -> tuple[int, int, int]:
    parts = (version + ".0.0.0").split(".")[:3]
    return tuple(int(p) for p in parts)


def semver_gte(a: str, b: str) -> bool:
    ta, tb = parse_tuple(a), parse_tuple(b)
    return ta >= tb


def resolve_version(scenario: dict[str, Any]) -> str:
    pinned = scenario.get("pinned_version") or ""
    if pinned:
        return pinned
    versions = scenario.get("versions_registered") or []
    return versions[0] if versions else "0.0.0"


def reference_export(scenario_path: Path) -> dict[str, Any]:
    sc = json.loads(scenario_path.read_text(encoding="utf-8"))
    routed = resolve_version(sc)
    seen: set[str] = set()
    dedup_skipped = 0
    events: list[dict[str, Any]] = []
    for sig in sc.get("signals", []):
        if not semver_gte(routed, sig["target_version"]):
            continue
        sid = sig["signal_id"]
        if sid in seen:
            dedup_skipped += 1
            continue
        seen.add(sid)
        events.append(
            {
                "signal_id": sid,
                "name": sig["name"],
                "version": sig["target_version"],
                "offset_ms": sig["server_time_ms"],
            }
        )
    beats = [b["heartbeat_server_ms"] for b in sc.get("activities", [])]
    return {
        "workflow_id": sc["workflow_id"],
        "effective_version": routed,
        "history_events": events,
        "duplicate_skipped": dedup_skipped,
        "heartbeat_clock_source": "server",
        "heartbeat_offsets_ms": beats,
    }


def reference_snapshot(scenario_path: Path) -> dict[str, Any]:
    sc = json.loads(scenario_path.read_text(encoding="utf-8"))
    routed = resolve_version(sc)
    seen: set[str] = set()
    dedup_skipped = 0
    acked: list[str] = []
    for sig in sc.get("signals", []):
        if not semver_gte(routed, sig["target_version"]):
            continue
        sid = sig["signal_id"]
        if sid in seen:
            dedup_skipped += 1
            continue
        seen.add(sid)
        acked.append(sid)
    beats = [b["heartbeat_server_ms"] for b in sc.get("activities", [])]
    return {
        "workflow_id": sc["workflow_id"],
        "routed_version": routed,
        "acked_signals": acked,
        # Final persisted snapshot: false means no handler wrote staging during replay.
        "staging_written": False,
        "dedup_seen": list(acked),
        "dedup_skipped": dedup_skipped,
        "heartbeat_offset_ms": beats,
    }


def procedural_scenario(seed: str) -> dict[str, Any]:
    """Build scenario JSON from seed for anti-cheat procedural checks."""
    import hashlib

    digest = hashlib.sha256(f"temporal-signal-{seed}".encode("utf-8")).digest()
    pinned = f"2.{digest[0] % 4}.{digest[1] % 15}"
    blocked = f"3.{digest[2] % 3}.{digest[3] % 10}"
    return {
        "workflow_id": f"proc-{digest[4] % 200}",
        "pinned_version": pinned,
        "migration_version": f"2.{digest[5] % 2}.0",
        "server_time_base_ms": 1_700_000_010_000 + digest[6],
        "versions_registered": [pinned, blocked, f"2.{digest[7] % 9}.0"],
        "signals": [
            {
                "signal_id": "z-late",
                "name": "late",
                "target_version": pinned,
                "server_time_ms": 80 + digest[8] % 20,
            },
            {
                "signal_id": "dup",
                "name": "once",
                "target_version": pinned,
                "server_time_ms": 10,
            },
            {
                "signal_id": "dup",
                "name": "twice",
                "target_version": pinned,
                "server_time_ms": 20,
            },
            {
                "signal_id": "a-early",
                "name": "early",
                "target_version": pinned,
                "server_time_ms": 5,
            },
            {
                "signal_id": "blocked",
                "name": "future",
                "target_version": blocked,
                "server_time_ms": 40,
            },
        ],
        "activities": [
            {
                "activity_id": "hb",
                "heartbeat_server_ms": 300 + digest[9] % 100,
                "worker_time_ms": 40 + digest[10] % 30,
            }
        ],
    }


def reference_export_from_dict(sc: dict[str, Any]) -> dict[str, Any]:
    """Reference export from an in-memory scenario dict."""
    import tempfile

    work = Path(tempfile.gettempdir()) / "ref-scenario.json"
    work.write_text(json.dumps(sc, indent=2) + "\n", encoding="utf-8")
    return reference_export(work)

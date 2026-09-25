"""Closed-form oracle for bag-atlas misroute root-cause atlas emission."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path


def read_hub_topology(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_scan_stream(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        v = json.loads(line)
        rows.append(
            {
                "bag_tag": v["bag_tag"],
                "scan_seq": int(v["scan_seq"]),
                "belt_id": v["belt_id"],
                "station_code": v["station_code"],
                "scan_minute": int(v["scan_minute"]),
                "relay_pass": int(v.get("relay_pass", 0)),
            }
        )
    return rows


def dedupe_scans(rows: list[dict]) -> list[dict]:
    best: dict[tuple[str, int], dict] = {}
    for row in rows:
        key = (row["bag_tag"], row["scan_seq"])
        if key not in best or row["relay_pass"] > best[key]["relay_pass"]:
            best[key] = row
    out = list(best.values())
    out.sort(key=lambda r: (r["scan_minute"], r["scan_seq"]))
    return out


def pick_belt(hub: dict, row: dict) -> dict | None:
    candidates = [
        b
        for b in hub["belts"]
        if b["belt_id"] == row["belt_id"] and b["station_code"] == row["station_code"]
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda b: int(b["priority"]))


def connection_feasible(hub: dict, inbound: str, outbound: str, mct_override: int | None = None) -> bool:
    flights = {f["flight_id"]: f for f in hub["flights"]}
    if inbound not in flights or outbound not in flights:
        return False
    rule = next(
        (c for c in hub["connections"] if c["inbound_flight"] == inbound and c["outbound_flight"] == outbound),
        None,
    )
    min_mct = mct_override if mct_override is not None else (int(rule["min_connect_minutes"]) if rule else 0)
    gap = int(flights[outbound]["dep_minute"]) - int(flights[inbound]["arr_minute"])
    return gap >= min_mct


def scan_suppressed(hub: dict, station: str, minute: int, station_override: str | None = None) -> bool:
    if station_override and station_override != station:
        return False
    for o in hub["outages"]:
        if o["station_code"] != station:
            continue
        if minute >= int(o["start_minute"]) and minute < int(o["end_minute"]):
            return True
    return False


def classify_row(row: dict) -> str:
    if row["outage_suppressed"]:
        return "OUTAGE_SUPPRESSED"
    if not row["connection_ok"]:
        return "CONNECTION_INFEASIBLE"
    if not row["target_flight_id"]:
        return "BELT_UNMAPPED"
    return "ROUTED_OK"


def build_route_rows(
    hub: dict,
    scans: list[dict],
    *,
    mct_override: int | None = None,
    station_override: str | None = None,
) -> list[dict]:
    rows: list[dict] = []
    for scan in scans:
        belt = pick_belt(hub, scan)
        target = belt["target_flight_id"] if belt else ""
        suppressed = scan_suppressed(hub, scan["station_code"], scan["scan_minute"], station_override)
        connection_ok = True
        for conn in hub["connections"]:
            if conn["outbound_flight"] == target:
                connection_ok = connection_feasible(
                    hub, conn["inbound_flight"], conn["outbound_flight"], mct_override
                )
                break
        row = {
            "bag_tag": scan["bag_tag"],
            "scan_seq": scan["scan_seq"],
            "belt_id": scan["belt_id"],
            "station_code": scan["station_code"],
            "scan_minute": scan["scan_minute"],
            "target_flight_id": target,
            "connection_ok": connection_ok,
            "outage_suppressed": suppressed,
            "misroute_cause": "",
        }
        row["misroute_cause"] = classify_row(row)
        rows.append(row)
    return rows


def audit_digest(rows: list[dict]) -> str:
    h = hashlib.sha256()
    for row in sorted(rows, key=lambda r: (r["bag_tag"], r["scan_seq"])):
        h.update(
            f"{row['bag_tag']}|{row['scan_seq']}|{row['misroute_cause']}|{row['target_flight_id']}|{row['scan_minute']}".encode()
        )
    return h.hexdigest()


def build_atlas(hub_id: str, topology_revision: int, rows: list[dict]) -> dict:
    hist: dict[str, int] = defaultdict(int)
    misroute_count = 0
    suppressed_count = 0
    for row in rows:
        hist[row["misroute_cause"]] += 1
        if row["outage_suppressed"]:
            suppressed_count += 1
        if row["misroute_cause"] not in ("ROUTED_OK", "OUTAGE_SUPPRESSED"):
            misroute_count += 1
    return {
        "hub_id": hub_id,
        "topology_revision": topology_revision,
        "route_row_count": len(rows),
        "misroute_count": misroute_count,
        "suppressed_count": suppressed_count,
        "cause_histogram": dict(sorted(hist.items())),
        "audit_digest": audit_digest(rows),
    }


def reference_dedupe_scans(rows: list[dict]) -> list[dict]:
    return dedupe_scans(rows)


def reference_build_atlas(hub_id: str, topology_revision: int, rows: list[dict]) -> dict:
    return build_atlas(hub_id, topology_revision, rows)


def reference_route_rows_from_paths(
    topo_path: Path,
    stream_path: Path,
    *,
    mct_override: int | None = None,
    station_override: str | None = None,
) -> list[dict]:
    hub = read_hub_topology(topo_path)
    scans = dedupe_scans(parse_scan_stream(stream_path))
    return build_route_rows(
        hub,
        scans,
        mct_override=mct_override,
        station_override=station_override,
    )


def recompute_atlas_from_paths(
    topo_path: Path,
    stream_path: Path,
    *,
    mct_override: int | None = None,
    station_override: str | None = None,
    topology_revision: int = 1,
) -> tuple[dict, list[dict]]:
    hub = read_hub_topology(topo_path)
    scans = dedupe_scans(parse_scan_stream(stream_path))
    rows = build_route_rows(
        hub,
        scans,
        mct_override=mct_override,
        station_override=station_override,
    )
    atlas = build_atlas(hub["hub_id"], topology_revision, rows)
    return atlas, rows


oracle_full_pipeline = recompute_atlas_from_paths

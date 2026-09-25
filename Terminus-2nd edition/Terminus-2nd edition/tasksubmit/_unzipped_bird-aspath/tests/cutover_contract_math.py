"""Independent contract math for bgpcut (not imported by /app)."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any


def is_well_known(community: str) -> bool:
    try:
        asn_s, _ = community.split(":", 1)
        asn = int(asn_s)
    except (ValueError, TypeError):
        return False
    return asn in (0, 65535)


def apply_salt(inventory: dict[str, Any], salt: str) -> dict[str, Any]:
    inv = copy.deepcopy(inventory)
    for peer in inv["peers"]:
        peer["peer_id"] = peer["peer_id"] + salt
    for route in inv["rib"]:
        route["peer_id"] = route["peer_id"] + salt
    return inv


def wave_order(peers: list[dict[str, Any]]) -> list[str]:
    ordered = sorted(peers, key=lambda p: (p["wave_rank"], p["asn"], p["peer_id"]))
    return [p["peer_id"] for p in ordered]


def inherit_filters(inventory: dict[str, Any], peer: dict[str, Any]) -> list[dict[str, Any]]:
    groups = {g["group_id"]: g for g in inventory["peer_groups"]}
    group = groups[peer["group_id"]]
    merged: dict[str, dict[str, Any]] = {f["filter_id"]: copy.deepcopy(f) for f in group["filters"]}
    for f in peer.get("filters") or []:
        merged[f["filter_id"]] = copy.deepcopy(f)
    filters = list(merged.values())
    filters.sort(key=lambda f: (-f["priority"], f["filter_id"]))
    return filters


def aspath_match(filt: dict[str, Any], as_path: list[int]) -> bool:
    mode = filt["match_mode"]
    if mode == "origin":
        return bool(as_path) and as_path[-1] == filt["asn"]
    if mode == "transit":
        if len(as_path) < 2:
            return False
        return filt["asn"] in as_path[:-1]
    if mode == "exact":
        return as_path == list(filt.get("as_path") or [])
    return False


def rewrite_communities(comms: list[str], rewrite: dict[str, str]) -> list[str]:
    out = list(comms)
    for key in sorted(rewrite.keys()):
        target = rewrite[key]
        out = [c if is_well_known(c) or c != key else target for c in out]
    return out


def clamp_med(med: int, ceiling: int | None) -> int:
    if ceiling is None:
        return med
    return min(med, ceiling)


def audit_digest(rows: list[dict[str, Any]]) -> str:
    lines = [
        f"{r['peer_id']}|{r['prefix']}|{r['action']}|{','.join(str(x) for x in r['as_path'])}"
        for r in rows
    ]
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def expected_cutover(inventory: dict[str, Any], run_id: str) -> dict[str, Any]:
    inv = copy.deepcopy(inventory)
    peer_order = wave_order(inv["peers"])
    peers_by_id = {p["peer_id"]: p for p in inv["peers"]}
    critical = set(inv.get("critical_prefixes") or [])
    checkpoint = copy.deepcopy(inv["rib"])
    working = copy.deepcopy(inv["rib"])
    rows: list[dict[str, Any]] = []
    wave_aborted = False

    for peer_id in peer_order:
        peer = peers_by_id[peer_id]
        filters = inherit_filters(inv, peer)
        routes = [r for r in working if r["peer_id"] == peer_id]
        for route in routes:
            action = "deny"
            matched: str | None = None
            for filt in filters:
                if aspath_match(filt, route["as_path"]):
                    action = filt["action"]
                    matched = filt["filter_id"]
                    break
            aborted = False
            communities = list(route["communities"])
            med = route["med"]
            if action == "accept":
                communities = rewrite_communities(communities, peer.get("community_rewrite") or {})
                med = clamp_med(med, peer.get("med_ceiling"))
                for wr in working:
                    if wr["peer_id"] == peer_id and wr["prefix"] == route["prefix"]:
                        wr["communities"] = list(communities)
                        wr["med"] = med
            elif peer.get("abort_on_critical_deny") and route["prefix"] in critical:
                wave_aborted = True
                aborted = True
                working = copy.deepcopy(checkpoint)
            rows.append(
                {
                    "peer_id": peer_id,
                    "prefix": route["prefix"],
                    "action": action,
                    "as_path": list(route["as_path"]),
                    "communities": communities,
                    "med": med,
                    "matched_filter": matched,
                    "aborted": aborted,
                }
            )
            if wave_aborted:
                break
        if wave_aborted:
            break

    return {
        "schema_version": 1,
        "run_id": run_id,
        "wave_aborted": wave_aborted,
        "peer_order": peer_order,
        "rows": rows,
        "rib_after": working,
    }


def reference_cutover(inventory: dict[str, Any], run_id: str) -> dict[str, Any]:
    """Independent atlas used by the verifier (alias of expected_cutover)."""
    return expected_cutover(inventory, run_id)


def expected_report(ledger: dict[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "run_id": ledger["run_id"],
        "wave_aborted": ledger["wave_aborted"],
        "peer_order": list(ledger["peer_order"]),
        "rows": copy.deepcopy(ledger["rows"]),
        "audit_digest": audit_digest(ledger["rows"]),
    }


def load_fixture(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

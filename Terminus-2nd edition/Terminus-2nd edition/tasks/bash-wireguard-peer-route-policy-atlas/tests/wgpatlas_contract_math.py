"""Independent WireGuard atlas contract math for pytest."""

from __future__ import annotations

import hashlib
import ipaddress
import json
from pathlib import Path
from typing import Any


def parse_wg_conf(path: Path) -> dict[str, Any]:
    iface: dict[str, str] = {}
    peers: list[dict[str, Any]] = []
    cur: dict[str, Any] = {}
    section: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            if section == "Peer" and cur:
                peers.append(cur)
                cur = {}
            section = line[1:-1]
            continue
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        k, v = k.strip(), v.strip()
        if section == "Interface":
            iface[k] = v
        elif section == "Peer":
            if k == "AllowedIPs":
                cur[k] = [p.strip() for p in v.split(",") if p.strip()]
            else:
                cur[k] = v
    if section == "Peer" and cur:
        peers.append(cur)
    return {"interface": iface, "peers": peers}


def cidrs_overlap(a: str, b: str) -> bool:
    na = ipaddress.ip_network(a, strict=False)
    nb = ipaddress.ip_network(b, strict=False)
    return na.overlaps(nb)


def pick_endpoint(peer_id: str, policy: dict[str, Any]) -> str:
    rows = [r for r in policy.get("endpoint_precedence", []) if r.get("peer") == peer_id]
    if not rows:
        return ""
    rows.sort(key=lambda r: int(r.get("metric", 0)))
    return str(rows[0].get("endpoint", ""))


def is_disabled(peer_id: str, policy: dict[str, Any]) -> bool:
    return peer_id in policy.get("disabled_peers", [])


def detect_route_conflicts(routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_table: dict[int, str] = {}
    conflicts: list[dict[str, Any]] = []
    for block in routes:
        tid = int(block["table_id"])
        iface = block["interface"]
        if tid in by_table and by_table[tid] != iface:
            conflicts.append(
                {
                    "table_id": tid,
                    "interface_a": by_table[tid],
                    "interface_b": iface,
                    "reason": "cross_interface_table_id",
                }
            )
        elif tid not in by_table:
            by_table[tid] = iface
    conflicts.sort(key=lambda c: (c["table_id"], c["interface_a"], c["interface_b"]))
    return conflicts


def build_peers(site_dir: Path, policy: dict[str, Any]) -> list[dict[str, Any]]:
    manifest = json.loads((site_dir / "manifest.json").read_text(encoding="utf-8"))
    peers: list[dict[str, Any]] = []
    for iface in manifest["interfaces"]:
        parsed = parse_wg_conf(site_dir / "wg" / f"{iface}.conf")
        for peer in parsed["peers"]:
            name = peer.get("Name", peer["PublicKey"])
            if is_disabled(name, policy):
                continue
            allowed = peer.get("AllowedIPs", [])
            endpoint = pick_endpoint(name, policy) or peer.get("Endpoint", "")
            peers.append(
                {
                    "public_key": peer["PublicKey"],
                    "peer_id": name,
                    "interface": iface,
                    "allowed_ips": allowed,
                    "endpoint": endpoint,
                    "disabled": False,
                }
            )
    return peers


def build_overlaps(peers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    overlaps: list[dict[str, Any]] = []
    for i, p1 in enumerate(peers):
        for p2 in peers[i + 1 :]:
            for c1 in p1["allowed_ips"]:
                for c2 in p2["allowed_ips"]:
                    if cidrs_overlap(c1, c2):
                        overlaps.append(
                            {
                                "peer_a": p1["peer_id"],
                                "peer_b": p2["peer_id"],
                                "cidr_a": c1,
                                "cidr_b": c2,
                                "reason": "allowed_ip_overlap",
                            }
                        )
    overlaps.sort(key=lambda o: (o["peer_a"], o["peer_b"], o["cidr_a"], o["cidr_b"]))
    return overlaps


def workspace_fingerprint(run_id: str, peers: list[dict[str, Any]], overlaps: list[dict[str, Any]], disabled: list[str]) -> str:
    body = {
        "run_id": run_id,
        "peers": [{"public_key": p["public_key"], "allowed_ips": p["allowed_ips"], "disabled": p.get("disabled", False)} for p in peers],
        "overlaps": overlaps,
        "disabled_skipped": sorted(disabled),
    }
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def load_routes(site_dir: Path, manifest: dict[str, Any]) -> list[dict[str, Any]]:
    routes: list[dict[str, Any]] = []
    for iface in manifest["interfaces"]:
        path = site_dir / "routes" / f"{iface}-routes.json"
        if path.exists():
            routes.append(json.loads(path.read_text(encoding="utf-8")))
    return routes


def reference_atlas(site_dir: Path, run_id: str) -> dict[str, Any]:
    policy = json.loads((site_dir / "site-policy.json").read_text(encoding="utf-8"))
    manifest = json.loads((site_dir / "manifest.json").read_text(encoding="utf-8"))
    peers = build_peers(site_dir, policy)
    overlaps = build_overlaps(peers)
    routes = load_routes(site_dir, manifest)
    route_conflicts = detect_route_conflicts(routes)
    peers_export = sorted(peers, key=lambda p: p["public_key"])
    audit_payload = [peers_export, overlaps, route_conflicts]
    audit = hashlib.sha256(json.dumps(audit_payload, sort_keys=True).encode()).hexdigest()
    return {
        "run_id": run_id,
        "peers": peers_export,
        "overlaps": overlaps,
        "route_conflicts": route_conflicts,
        "summary": {
            "active_peer_count": len(peers_export),
            "overlap_count": len(overlaps),
            "conflict_count": len(route_conflicts),
        },
        "audit_digest": audit,
    }

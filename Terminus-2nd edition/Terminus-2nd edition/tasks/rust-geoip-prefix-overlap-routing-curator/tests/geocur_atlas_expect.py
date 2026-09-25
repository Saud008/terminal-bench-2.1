"""Independent geocur overlap atlas math for pytest (verifier-only under /tests)."""

from __future__ import annotations

import hashlib
import ipaddress
import json
from pathlib import Path
from typing import Any

RESERVED = [
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("224.0.0.0/4"),
]


def normalize_cidr(raw: str) -> str:
    return str(ipaddress.ip_network(raw.strip(), strict=False))


def contains(outer: str, inner: str) -> bool:
    o = ipaddress.ip_network(outer, strict=False)
    i = ipaddress.ip_network(inner, strict=False)
    return i.subnet_of(o) and o != i


def is_reserved(cidr: str) -> bool:
    net = ipaddress.ip_network(cidr, strict=False)
    if not isinstance(net, ipaddress.IPv4Network):
        return False
    return any(net.subnet_of(r) for r in RESERVED)


def prefix_len(cidr: str) -> int:
    return int(cidr.split("/")[1])


def scoped_merge_id(seed: str, bundle: str, seq: int) -> str:
    body = f"{seed}:{bundle}:{seq}".encode()
    return "merge-" + hashlib.sha256(body).hexdigest()[:12]


def load_bundle(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def materialize(bundle: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for feed in bundle["feeds"]:
        for rec in feed["records"]:
            rows.append(
                {
                    "cidr": normalize_cidr(rec["cidr"]),
                    "country": rec["country"],
                    "asn": rec["asn"],
                    "feed_id": feed["feed_id"],
                    "lineage_id": rec["lineage_id"],
                }
            )
    return rows


def apply_salt(ids: list[str], salt: str) -> list[str]:
    if not salt:
        return sorted(ids)
    return sorted(i + salt for i in ids)


def build_rows(
    records: list[dict[str, Any]], salt: str = ""
) -> tuple[list[dict[str, Any]], int]:
    filtered = [r for r in records if not is_reserved(r["cidr"])]
    reserved_dropped = len(records) - len(filtered)
    by_cidr: dict[str, list[dict[str, Any]]] = {}
    for rec in filtered:
        by_cidr.setdefault(rec["cidr"], []).append(rec)

    winners: dict[str, dict[str, Any]] = {}
    for cidr, group in by_cidr.items():
        winners[cidr] = min(group, key=lambda r: r["feed_id"])

    rows: list[dict[str, Any]] = []
    for cidr in sorted(by_cidr.keys()):
        group = by_cidr[cidr]
        lineage_ids = sorted({g["lineage_id"] for g in group})
        lineage_ids = apply_salt(lineage_ids, salt)
        win = winners[cidr]
        container = None
        for other in sorted(winners.keys()):
            if other != cidr and contains(other, cidr):
                if container is None or prefix_len(other) > prefix_len(container):
                    container = other
        rows.append(
            {
                "cidr": cidr,
                "country": win["country"],
                "asn": win["asn"],
                "winning_feed": win["feed_id"],
                "contained_by": container,
                "asn_lineage": lineage_ids,
                "reserved_filtered": False,
            }
        )
    rows.sort(key=lambda r: (r["country"], r["asn"], r["cidr"]))
    return rows, reserved_dropped


def count_overlap_pairs(rows: list[dict[str, Any]]) -> int:
    n = 0
    for i, a in enumerate(rows):
        for b in rows[i + 1 :]:
            if (a["country"] != b["country"] or a["asn"] != b["asn"]) and (
                contains(a["cidr"], b["cidr"]) or contains(b["cidr"], a["cidr"])
            ):
                n += 1
    return n


def audit_digest(summary: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    chains = sorted(r["asn_lineage"] for r in rows)
    body = json.dumps(
        {
            "overlap_pairs": summary["overlap_pairs"],
            "reserved_dropped": summary["reserved_dropped"],
            "total_prefixes": summary["total_prefixes"],
            "asn_conflicts": summary["asn_conflicts"],
            "asn_lineage_chains": chains,
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(body.encode()).hexdigest()


def expect_overlap_report(
    seed: str,
    bundle: str,
    bundle_path: Path,
    load_generation: int,
    salt: str = "",
) -> dict[str, Any]:
    bf = load_bundle(bundle_path)
    records = materialize(bf)
    rows, reserved_dropped = build_rows(records, salt)
    summary = {
        "total_prefixes": len(rows),
        "overlap_pairs": count_overlap_pairs(rows),
        "asn_conflicts": sum(1 for r in rows if len(r["asn_lineage"]) > 1),
        "reserved_dropped": reserved_dropped,
    }
    rep: dict[str, Any] = {
        "seed": seed,
        "bundle": bundle,
        "reconcile_id": scoped_merge_id(seed, bundle, load_generation),
        "overlap_rows": rows,
        "summary": summary,
        "audit_digest": "",
    }
    rep["audit_digest"] = audit_digest(summary, rows)
    return rep

"""Independent reference for vexatlas SBOM/VEX impact reachability atlas."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUS_RANK = {
    "not_affected": 5,
    "fixed": 4,
    "under_investigation": 3,
    "affected": 2,
    "unknown": 1,
}


def normalize_purl(raw: str, name: str, version: str) -> str:
    trimmed_name = name.strip()
    trimmed_version = version.strip()
    if "@" in raw:
        base = raw.strip()
    else:
        base = f"pkg:cargo/{trimmed_name}@{trimmed_version}"
    if "/" in base:
        slash = base.index("/")
        prefix = base[:slash]
        rest = base[slash:]
        lowered = ":".join(part.lower() for part in prefix.split(":"))
        return f"{lowered}{rest}"
    return base.lower()


def collapse_packages(packages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, str]] = {}
    for pkg in packages:
        norm = normalize_purl(pkg["purl"], pkg["name"], pkg["version"])
        entry = merged.setdefault(
            norm,
            {
                "canonical_raw": pkg["purl"],
                "name": pkg["name"].strip(),
                "version": pkg["version"].strip(),
            },
        )
        if pkg["purl"] < entry["canonical_raw"]:
            entry["canonical_raw"] = pkg["purl"]
            entry["name"] = pkg["name"].strip()
            entry["version"] = pkg["version"].strip()
    rows = []
    for norm in sorted(merged):
        e = merged[norm]
        rows.append(
            {
                "norm_purl": norm,
                "canonical_raw": e["canonical_raw"],
                "name": e["name"],
                "version": e["version"],
            }
        )
    return rows


def staging_digest_from_stage(stage: dict[str, Any]) -> str:
    packages = [
        {
            "norm_purl": p["norm_purl"],
            "canonical_raw": p["canonical_raw"],
            "name": p["name"],
            "version": p["version"],
        }
        for p in stage["packages"]
    ]
    edges = [
        {"from": e["from"], "to": e["to"], "edge_kind": e["edge_kind"]} for e in stage["edges"]
    ]
    vex_rows = []
    for v in stage["vex"]:
        row = {
            "statement_id": v["statement_id"],
            "product_purl": v["product_purl"],
            "vuln_id": v["vuln_id"],
            "status": v["status"],
            "updated_at": v["updated_at"],
        }
        if v.get("expires_at") is not None:
            row["expires_at"] = v["expires_at"]
        vex_rows.append(row)
    body = {
        "bundle_id": stage["bundle_id"],
        "packages": packages,
        "edges": edges,
        "vex": vex_rows,
    }
    raw = json.dumps(body, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def parse_utc(ts: str) -> datetime:
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts).astimezone(timezone.utc)


def is_active(stmt: dict[str, Any], now: datetime | None = None) -> bool:
    exp = stmt.get("expires_at")
    if not exp:
        return True
    now = now or datetime.now(timezone.utc)
    return now < parse_utc(exp)


def pick_effective(statements: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not statements:
        return None
    return max(
        statements,
        key=lambda s: (STATUS_RANK.get(s["status"], 0), s["updated_at"]),
    )


def bfs_reachable(root: str, edges: list[dict[str, Any]]) -> set[str]:
    adj: dict[str, list[str]] = {}
    for e in edges:
        if e.get("edge_kind") == "runtime":
            adj.setdefault(e["from"], []).append(e["to"])
    seen = {root}
    queue = [root]
    while queue:
        cur = queue.pop(0)
        for nxt in adj.get(cur, []):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    return seen


def apply_salt(purl: str) -> str:
    salt = os.environ.get("TB3_BUNDLE_SALT", "")
    if salt:
        return f"{purl}{salt}"
    return purl


def reference_stage_from_bundle(bundle: dict[str, Any]) -> dict[str, Any]:
    packages = collapse_packages(bundle["packages"])
    purl_index = {p["purl"]: (p["name"], p["version"]) for p in bundle["packages"]}
    edges = []
    for e in bundle["edges"]:
        fn, fv = purl_index.get(e["from"], ("", ""))
        tn, tv = purl_index.get(e["to"], ("", ""))
        edges.append(
            {
                "from": normalize_purl(e["from"], fn, fv),
                "to": normalize_purl(e["to"], tn, tv),
                "edge_kind": e["edge_kind"],
            }
        )
    edges.sort(key=lambda x: (x["from"], x["to"]))
    vex = []
    for v in bundle["vex"]:
        pn, pv = purl_index.get(v["product_purl"], ("", ""))
        row = {
            "statement_id": v["statement_id"],
            "product_purl": normalize_purl(v["product_purl"], pn, pv),
            "vuln_id": v["vuln_id"],
            "status": v["status"],
            "updated_at": v["updated_at"],
        }
        if v.get("expires_at") is not None:
            row["expires_at"] = v["expires_at"]
        vex.append(row)
    vex.sort(key=lambda x: x["statement_id"])
    stage = {
        "bundle_id": bundle["bundle_id"],
        "fingerprint": bundle["fingerprint"],
        "ingest_seq": 1,
        "staging_digest": "",
        "packages": packages,
        "edges": edges,
        "vex": vex,
        "binaries": bundle["binaries"],
        "vulnerabilities": bundle["vulnerabilities"],
    }
    stage["staging_digest"] = staging_digest_from_stage(stage)
    return stage


def waiver_for(winner: dict[str, Any] | None) -> dict[str, Any] | None:
    if not winner:
        return None
    if winner["status"] not in ("not_affected", "fixed"):
        return None
    return {
        "statement_id": winner["statement_id"],
        "expires_at": winner.get("expires_at"),
    }


def export_digest_for(impacts: list[dict[str, Any]]) -> str:
    parts = []
    for row in impacts:
        waiver = row.get("waiver")
        if waiver is None:
            waiver_json = "null"
        else:
            exp = waiver.get("expires_at")
            exp_json = "null" if exp is None else json.dumps(exp)
            waiver_json = (
                f'{{"statement_id":{json.dumps(waiver["statement_id"])},"expires_at":{exp_json}}}'
            )
        parts.append(
            "{"
            f'"binary":{json.dumps(row["binary"])},'
            f'"package_purl":{json.dumps(row["package_purl"])},'
            f'"vuln_id":{json.dumps(row["vuln_id"])},'
            f'"effective_status":{json.dumps(row["effective_status"])},'
            f'"reachable":true,'
            f'"waiver":{waiver_json}'
            "}"
        )
    body = "[" + ",".join(parts) + "]"
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def reference_export(stage: dict[str, Any], now: datetime | None = None) -> dict[str, Any]:
    impacts: list[dict[str, Any]] = []
    for binary in stage["binaries"]:
        root = apply_salt(binary["root_purl"])
        reachable = bfs_reachable(root, stage["edges"])
        for vuln in stage["vulnerabilities"]:
            for pkg in stage["packages"]:
                pkg_purl = apply_salt(pkg["norm_purl"])
                if pkg_purl not in reachable:
                    continue
                stmts = [
                    v
                    for v in stage["vex"]
                    if v["product_purl"] == pkg_purl and v["vuln_id"] == vuln["vuln_id"]
                ]
                active = [s for s in stmts if is_active(s, now)]
                winner = pick_effective(active)
                status = winner["status"] if winner else "unknown"
                impacts.append(
                    {
                        "binary": binary["name"],
                        "package_purl": pkg_purl,
                        "vuln_id": vuln["vuln_id"],
                        "effective_status": status,
                        "reachable": True,
                        "waiver": waiver_for(winner),
                    }
                )
    impacts.sort(key=lambda r: (r["binary"], r["package_purl"], r["vuln_id"]))
    return {
        "bundle_id": stage["bundle_id"],
        "export_digest": export_digest_for(impacts),
        "impacts": impacts,
    }


def load_bundle(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

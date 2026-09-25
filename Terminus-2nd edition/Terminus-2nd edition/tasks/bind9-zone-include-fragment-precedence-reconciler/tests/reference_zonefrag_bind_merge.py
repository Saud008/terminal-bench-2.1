"""Independent BIND-style zone include merge reference for zonefrag verifier."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MAX_INCLUDE_DEPTH = 16


@dataclass
class Record:
    owner: str
    rclass: str
    rtype: str
    ttl: int
    rdata: str
    line: int
    origin: str
    source_file: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "owner": self.owner,
            "class": self.rclass,
            "type": self.rtype,
            "ttl": self.ttl,
            "rdata": self.rdata,
            "line": self.line,
            "origin": self.origin,
        }


def expand_zone_units(tree: Path, master_rel: str, origin: str) -> tuple[list[str], list[dict[str, Any]]]:
    processing_order: list[str] = []
    units: list[dict[str, Any]] = []
    visited: set[str] = set()

    def walk(abs_path: Path, rel: str, cur_origin: str, depth: int) -> None:
        if depth > MAX_INCLUDE_DEPTH:
            raise ValueError("include depth exceeded")
        key = str(abs_path.resolve())
        if key in visited:
            return
        visited.add(key)
        cur_origin_local = cur_origin
        default_ttl: int | None = None
        file_recs: list[Record] = []
        for line_no, raw in enumerate(abs_path.read_text(encoding="utf-8").splitlines(), start=1):
            line = raw.strip()
            if not line or line.startswith(";"):
                continue
            if line.startswith("$ORIGIN"):
                parts = line.split(None, 1)
                if len(parts) == 2:
                    cur_origin_local = parts[1].strip()
                continue
            if line.startswith("$TTL"):
                parts = line.split(None, 1)
                if len(parts) == 2:
                    default_ttl = int(parts[1].strip())
                continue
            if line.startswith("$INCLUDE"):
                parts = line.split(None, 1)
                if len(parts) != 2:
                    continue
                if file_recs:
                    processing_order.append(rel)
                    units.append({"file": rel, "records": [r.to_dict() for r in file_recs]})
                    file_recs = []
                inc_abs = (abs_path.parent / parts[1].strip()).resolve()
                inc_rel = (
                    inc_abs.relative_to(tree).as_posix()
                    if inc_abs.is_relative_to(tree)
                    else parts[1].strip()
                )
                if inc_abs.is_file():
                    walk(inc_abs, inc_rel, cur_origin_local, depth + 1)
                continue
            tokens = line.split()
            if len(tokens) < 4:
                continue
            owner = tokens[0]
            idx = 1
            ttl = default_ttl if default_ttl is not None else 3600
            if tokens[idx].isdigit():
                ttl = int(tokens[idx])
                idx += 1
            if idx >= len(tokens) or tokens[idx] != "IN":
                continue
            idx += 1
            rtype = tokens[idx]
            idx += 1
            rdata = " ".join(tokens[idx:])
            file_recs.append(
                Record(owner, "IN", rtype, ttl, rdata, line_no, cur_origin_local, rel)
            )
        if file_recs:
            processing_order.append(rel)
            units.append({"file": rel, "records": [r.to_dict() for r in file_recs]})

    walk(tree / master_rel, master_rel, origin, 0)
    return processing_order, units


def merge_records(units: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    merged: dict[tuple[str, str, str], dict[str, Any]] = {}
    sources: dict[str, dict[str, Any]] = {}
    for unit in units:
        for rec in unit.get("records", []):
            key = (rec["owner"], rec["class"], rec["type"])
            merged[key] = rec
            sources[f"{rec['owner']}/{rec['class']}/{rec['type']}"] = {
                "file": unit["file"],
                "line": rec["line"],
            }
    return list(merged.values()), sources


def normalize_apex(origin: str) -> str:
    return origin.rstrip(".")


def detect_wildcard_conflicts(records: list[dict[str, Any]], origin: str) -> list[dict[str, Any]]:
    apex = normalize_apex(origin)
    wildcards = [r for r in records if r["owner"].startswith("*")]
    conflicts: list[dict[str, Any]] = []
    for w in wildcards:
        for r in records:
            if r["owner"] in ("@", apex) and r["type"] in ("A", "AAAA"):
                conflicts.append({"wildcard": w["owner"], "apex": r["owner"], "type": r["type"]})
    return conflicts


def soa_serial_from_rdata(rdata: str) -> int | None:
    parts = rdata.split()
    if len(parts) >= 3 and parts[2].isdigit():
        return int(parts[2])
    return None


def set_soa_serial_in_rdata(rdata: str, serial: int) -> str:
    parts = rdata.split()
    if len(parts) >= 3:
        parts[2] = str(serial)
        return " ".join(parts)
    return rdata


def master_soa_serial(units: list[dict[str, Any]], master_rel: str) -> int | None:
    for unit in units:
        if unit["file"] != master_rel:
            continue
        for rec in unit.get("records", []):
            if rec["type"] == "SOA":
                found = soa_serial_from_rdata(rec["rdata"])
                if found is not None:
                    return found
    return None


def bump_soa_serial(units: list[dict[str, Any]], master_rel: str, reload: bool) -> tuple[int, str]:
    serial = master_soa_serial(units, master_rel)
    if serial is None:
        serial = 0
    if reload:
        serial += 1
    return serial, master_rel


def validate_nsec_chain(units: list[dict[str, Any]]) -> tuple[bool, list[dict[str, Any]]]:
    nsec_records: list[dict[str, Any]] = []
    for unit in units:
        for rec in unit.get("records", []):
            if rec["type"] == "NSEC":
                nsec_records.append({**rec, "file": unit["file"]})
    breaks: list[dict[str, Any]] = []
    for i in range(len(nsec_records) - 1):
        cur = nsec_records[i]
        nxt = nsec_records[i + 1]
        parts = cur["rdata"].split()
        expected = parts[0] if parts else ""
        if expected != nxt["owner"]:
            breaks.append(
                {
                    "file": cur.get("file"),
                    "owner": cur["owner"],
                    "expected": nxt["owner"],
                    "got": expected,
                }
            )
    return len(breaks) == 0, breaks


def include_fingerprint(tree: Path, master_rel: str) -> str:
    parts = [master_rel]
    for zone in sorted(tree.rglob("*.zone")):
        rel = zone.relative_to(tree).as_posix()
        if rel == master_rel:
            continue
        parts.append(f"{rel}:{hashlib.sha256(zone.read_bytes()).hexdigest()[:16]}")
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def canonical_snapshot_digest(meta: dict[str, Any]) -> str:
    payload = {
        "origin": meta.get("origin"),
        "processing_order": meta.get("processing_order"),
        "records": meta.get("records"),
        "soa_serial": meta.get("soa_serial"),
        "include_fingerprint": meta.get("include_fingerprint"),
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def build_snapshot(
    tree: Path,
    seed: str,
    reload: bool = False,
    cache: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    manifest = json.loads((tree / "manifest.json").read_text(encoding="utf-8"))
    origin = manifest.get("origin", "example.com.")
    master = manifest["master"]
    fp = include_fingerprint(tree, master)
    cache_key = hashlib.sha256(f"{tree}:{seed}:{fp}:{int(reload)}".encode()).hexdigest()
    if cache is not None and cache_key in cache:
        cached = cache[cache_key]
        if cached.get("include_fingerprint") == fp:
            return cached

    processing_order, units = expand_zone_units(tree, master, origin)
    records, sources = merge_records(units)
    wild = detect_wildcard_conflicts(records, origin)
    serial, soa_source = bump_soa_serial(units, master, reload)
    nsec_valid, nsec_breaks = validate_nsec_chain(units)

    if reload:
        for rec in records:
            if rec["type"] == "SOA":
                rec["rdata"] = set_soa_serial_in_rdata(rec["rdata"], serial)

    doc: dict[str, Any] = {
        "snapshot_version": 1,
        "tree_path": str(tree),
        "tree": tree.name,
        "seed": seed,
        "origin": origin,
        "processing_order": processing_order,
        "records": records,
        "sources": sources,
        "wildcard_conflicts": wild,
        "soa_serial": serial,
        "soa_source": soa_source,
        "nsec_valid": nsec_valid,
        "nsec_breaks": nsec_breaks,
        "include_fingerprint": fp,
        "stats": {
            "records": len(records),
            "units": len(units),
            "wildcard_conflicts": len(wild),
        },
    }
    doc["zone_hash"] = canonical_snapshot_digest(doc)
    if cache is not None:
        cache[cache_key] = doc
    return doc


def publish_export(snapshot: dict[str, Any]) -> dict[str, Any]:
    digest = canonical_snapshot_digest(snapshot)
    return {
        "compile_version": 1,
        "tree": snapshot["tree"],
        "seed": snapshot["seed"],
        "origin": snapshot["origin"],
        "processing_order": snapshot["processing_order"],
        "records": snapshot["records"],
        "soa_serial": snapshot["soa_serial"],
        "wildcard_conflicts": snapshot["wildcard_conflicts"],
        "nsec_valid": snapshot["nsec_valid"],
        "include_fingerprint": snapshot["include_fingerprint"],
        "zone_hash": snapshot.get("zone_hash"),
        "compile_digest": digest,
        "stats": snapshot["stats"],
    }


def reference_compile(tree: Path, seed: str, reload: bool = False) -> dict[str, Any]:
    snap = build_snapshot(tree, seed, reload=reload)
    return publish_export(snap)


def merge_staging(snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "staging_version": 1,
        "snapshot_digest": canonical_snapshot_digest(snapshot),
        "processing_order": snapshot.get("processing_order", []),
        "record_count": len(snapshot.get("records", [])),
    }


def verify_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    issues: list[str] = []
    if snapshot.get("wildcard_conflicts"):
        issues.append("wildcard")
    if not snapshot.get("nsec_valid", True):
        issues.append("nsec")
    return {"ok": len(issues) == 0, "issues": issues}

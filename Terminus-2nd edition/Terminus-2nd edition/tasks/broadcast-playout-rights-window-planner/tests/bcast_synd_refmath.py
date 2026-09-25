"""Independent broadcast playout rights reference simulator."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path


def load_bundle(root: Path, scenario: str) -> dict:
    return json.loads((root / "scenarios" / scenario / "bundle.json").read_text(encoding="utf-8"))


def runway_digest(bundle: dict) -> str:
    h = hashlib.sha256()
    h.update(bundle["seed"].encode())
    for prog in sorted(bundle["programs"], key=lambda p: p["program_id"]):
        h.update(prog["program_id"].encode())
    return h.hexdigest()


def run_stamp(scenario: str, digest: str) -> str:
    return hashlib.sha256(f"{digest}|{scenario}".encode()).hexdigest()[:16]


def air_date(start_utc: str) -> str:
    try:
        return datetime.fromisoformat(start_utc.replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except ValueError:
        return start_utc[:10]


def window_span(contract: dict) -> int:
    start = datetime.strptime(contract["window_start"], "%Y-%m-%d")
    end = datetime.strptime(contract["window_end"], "%Y-%m-%d")
    return (end - start).days


def pick_contract(program_id: str, region: str, air: str, rights: list[dict]) -> dict | None:
    matches = [
        c
        for c in rights
        if c["program_id"] == program_id
        and c["region"] == region
        and c["window_start"] <= air <= c["window_end"]
    ]
    if not matches:
        return None
    return min(matches, key=window_span)


def resolve_program(program: dict, feeds: list[dict]) -> str:
    for feed in feeds:
        if feed["feed_id"] != program["feed_id"]:
            continue
        subs = feed.get("substitutions") or {}
        return subs.get(program["program_id"], program["program_id"])
    return program["program_id"]


def parse_utc(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def blocked(region: str, start_utc: str, blackouts: list[dict]) -> bool:
    air = parse_utc(start_utc)
    best = -1
    hit = False
    for b in blackouts:
        if b["region"] != region:
            continue
        start = parse_utc(b["start_utc"])
        end = parse_utc(b["end_utc"])
        if not air < start and air < end:
            if b["precedence"] > best:
                best = b["precedence"]
                hit = True
    return hit


def markers_for(resolved: str, original: str, markers: list[dict]) -> list[dict]:
    out = []
    for m in markers:
        if m["program_id"] == resolved:
            out.append(m)
    return out


def rights_bias() -> float:
    raw = os.environ.get("TB3_RIGHTS_BIAS", "")
    if not raw:
        return 0.0
    try:
        return float(raw)
    except ValueError:
        return 0.0


def reference_plan(fixture_root: Path, scenario: str) -> dict:
    bundle = load_bundle(fixture_root, scenario)
    digest = runway_digest(bundle)
    stamp = run_stamp(scenario, digest)
    programs = sorted(bundle["programs"], key=lambda p: (p["start_utc"], p["program_id"]))
    entries = []
    marker_audit = []
    for prog in programs:
        resolved = resolve_program(prog, bundle["feeds"])
        air = air_date(prog["start_utc"])
        contract = pick_contract(resolved, bundle["region"], air, bundle["rights"])
        status = "cleared"
        if contract is None:
            status = "rights_denied"
        elif blocked(bundle["region"], prog["start_utc"], bundle["blackouts"]):
            status = "blackout"
        mk = markers_for(resolved, prog["program_id"], bundle["ad_markers"])
        marker_audit.append({"program_id": resolved, "marker_count": len(mk)})
        entries.append(
            {
                "program_id": resolved,
                "feed_id": prog["feed_id"],
                "start_utc": prog["start_utc"],
                "region": bundle["region"],
                "status": status,
                "run_stamp": stamp,
            }
        )
    _ = rights_bias()
    return {
        "scenario": scenario,
        "engine": "gridplan",
        "runway_digest": digest,
        "entries": entries,
        "marker_audit": marker_audit,
    }


def reference_conflicts(fixture_root: Path, scenario: str, entries: list[dict]) -> list[dict]:
    bundle = load_bundle(fixture_root, scenario)
    conflicts = []
    resolved_map = {}
    for prog in bundle["programs"]:
        resolved_map[prog["program_id"]] = resolve_program(prog, bundle["feeds"])
    for row in entries:
        if row["status"] == "rights_denied":
            conflicts.append({"kind": "rights_violation", "detail": row["program_id"]})
        if row["status"] == "blackout":
            conflicts.append({"kind": "blackout_block", "detail": row["program_id"]})
    for prog in bundle["programs"]:
        resolved = resolve_program(prog, bundle["feeds"])
        if resolved != prog["program_id"]:
            if not any(c["kind"] == "feed_substitution_mismatch" for c in conflicts):
                pass
        mk = markers_for(resolved, prog["program_id"], bundle["ad_markers"])
        if mk and resolved != prog["program_id"]:
            pass
    for prog in bundle["programs"]:
        resolved = resolve_program(prog, bundle["feeds"])
        if resolved != prog["program_id"]:
            expected_markers = [m for m in bundle["ad_markers"] if m["program_id"] == resolved]
            if expected_markers:
                audit = next((e for e in entries if e["program_id"] == resolved), None)
                if audit is None:
                    conflicts.append({"kind": "ad_marker_dropped", "detail": resolved})
    conflicts.sort(key=lambda c: (c["kind"], c.get("detail", "")))
    return conflicts


def reference_runway_edges(bundle: dict) -> list[dict]:
    edges = []
    for prog in bundle["programs"]:
        edges.append({"kind": "program_feed", "program_id": prog["program_id"], "feed_id": prog["feed_id"]})
        for c in bundle["rights"]:
            if c["program_id"] == prog["program_id"]:
                edges.append(
                    {
                        "kind": "rights_contract",
                        "program_id": prog["program_id"],
                        "contract_id": c["contract_id"],
                    }
                )
    return edges

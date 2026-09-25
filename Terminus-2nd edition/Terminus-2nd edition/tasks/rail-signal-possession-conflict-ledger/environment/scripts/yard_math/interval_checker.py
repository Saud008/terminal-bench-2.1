"""Independent rail possession conflict reference math."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def load_scenario(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_zone_map(sf: dict[str, Any]) -> dict[str, list[str]]:
    blocks = sorted(b["block_id"] for b in sf["blocks"])
    neighbors: dict[str, set[str]] = {b: set() for b in blocks}
    for a, b in sf["adjacency"]:
        neighbors[a].add(b)
        neighbors[b].add(a)

    def reach(start: str) -> list[str]:
        seen = {start}
        stack = [start]
        while stack:
            node = stack.pop()
            for nb in neighbors.get(node, ()):
                if nb not in seen:
                    seen.add(nb)
                    stack.append(nb)
        return sorted(seen)

    return {b: reach(b) for b in blocks}


def intervals_overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return a_start < b_end and b_start < a_end


def clip_window(a_start: int, a_end: int, b_start: int, b_end: int) -> tuple[int, int] | None:
    if not intervals_overlap(a_start, a_end, b_start, b_end):
        return None
    return max(a_start, b_start), min(a_end, b_end)


def protected_overlap(closure: dict[str, list[str]], blocks_a: list[str], blocks_b: list[str]) -> bool:
    zone_a: set[str] = set()
    for b in blocks_a:
        zone_a.update(closure.get(b, [b]))
    zone_b: set[str] = set()
    for b in blocks_b:
        zone_b.update(closure.get(b, [b]))
    return bool(zone_a & zone_b)


def claim_suppressed(
    closure: dict[str, list[str]],
    ov: dict[str, Any],
    blocks: list[str],
    start: int,
    end: int,
    priority: int,
) -> bool:
    if priority == 0 or ov.get("priority") != 0:
        return False
    if not intervals_overlap(start, end, ov["start_min"], ov["end_min"]):
        return False
    ov_zone: set[str] = set()
    for b in ov["blocks"]:
        ov_zone.update(closure.get(b, [b]))
    claim_zone: set[str] = set()
    for b in blocks:
        claim_zone.update(closure.get(b, [b]))
    return bool(ov_zone & claim_zone)


def filter_active(
    closure: dict[str, list[str]],
    sf: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    possessions = list(sf["possessions"])
    reservations = list(sf["reservations"])
    suppressed = 0
    for ov in sf.get("overrides", []):
        if ov.get("priority") != 0:
            continue
        keep_p: list[dict[str, Any]] = []
        for p in possessions:
            if claim_suppressed(closure, ov, p["blocks"], p["start_min"], p["end_min"], p["priority"]):
                suppressed += 1
            else:
                keep_p.append(p)
        possessions = keep_p
        keep_r: list[dict[str, Any]] = []
        for r in reservations:
            if claim_suppressed(closure, ov, r["blocks"], r["start_min"], r["end_min"], r["priority"]):
                suppressed += 1
            else:
                keep_r.append(r)
        reservations = keep_r
    return possessions, reservations, suppressed


def signal_conflicts(
    closure: dict[str, list[str]],
    sf: dict[str, Any],
    reservations: list[dict[str, Any]],
    salt: str = "",
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for sig in sf.get("signals", []):
        if sig.get("aspect") != "restrict":
            continue
        sig_zone = set(closure.get(sig["block_id"], [sig["block_id"]]))
        for res in reservations:
            res_zone: set[str] = set()
            for b in res["blocks"]:
                res_zone.update(closure.get(b, [b]))
            if not intervals_overlap(sig["start_min"], sig["end_min"], res["start_min"], res["end_min"]):
                continue
            if not (sig_zone & res_zone):
                continue
            window = clip_window(sig["start_min"], sig["end_min"], res["start_min"], res["end_min"])
            if window is None:
                continue
            parts = apply_salt_participants([sig["signal_id"], res["train_id"]], salt)
            rows.append(
                {
                    "group_key": "|".join(parts),
                    "participants": parts,
                    "window_start": window[0],
                    "window_end": window[1],
                    "blocks": block_km_order(sf, sorted({sig["block_id"], *res["blocks"]})),
                    "reasons": ["signal_restrict"],
                }
            )
    return rows


def block_km_order(sf: dict[str, Any], block_ids: list[str]) -> list[str]:
    km = {b["block_id"]: b["kilometer"] for b in sf["blocks"]}
    return sorted(block_ids, key=lambda b: (km.get(b, 0.0), b))


def possession_id(seed: str, scenario: str, load_seq: int) -> str:
    body = f"{seed}:{scenario}:{load_seq}".encode()
    return "poss-" + hashlib.sha256(body).hexdigest()[:12]


def audit_digest(summary: dict[str, Any], groups: list[dict[str, Any]]) -> str:
    keys = sorted(g["group_key"] for g in groups)
    body = json.dumps(
        {
            "possession_pairs": summary["possession_pairs"],
            "total_conflicts": summary["total_conflicts"],
            "signal_blocked": summary["signal_blocked"],
            "override_suppressed": summary["override_suppressed"],
            "part_sort": keys,
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(body.encode()).hexdigest()


def apply_salt_participants(ids: list[str], salt: str) -> list[str]:
    if not salt:
        return sorted(ids)
    return sorted(i + salt for i in ids)


def reference_ledger(
    seed: str,
    scenario: str,
    scenario_path: Path,
    load_seq: int,
    salt: str = "",
) -> dict[str, Any]:
    sf = load_scenario(scenario_path)
    closure = build_zone_map(sf)
    possessions, reservations, override_suppressed = filter_active(closure, sf)

    groups: list[dict[str, Any]] = []
    possession_pairs = 0

    for i, a in enumerate(possessions):
        for b in possessions[i + 1 :]:
            if not intervals_overlap(a["start_min"], a["end_min"], b["start_min"], b["end_min"]):
                continue
            if not protected_overlap(closure, a["blocks"], b["blocks"]):
                continue
            possession_pairs += 1
            window = clip_window(a["start_min"], a["end_min"], b["start_min"], b["end_min"])
            assert window is not None
            parts = apply_salt_participants([a["claim_id"], b["claim_id"]], salt)
            groups.append(
                {
                    "group_key": "|".join(parts),
                    "participants": parts,
                    "window_start": window[0],
                    "window_end": window[1],
                    "blocks": block_km_order(sf, sorted(set(a["blocks"]) | set(b["blocks"]))),
                    "reasons": ["possession_overlap"],
                }
            )

    for p in possessions:
        for r in reservations:
            if not intervals_overlap(p["start_min"], p["end_min"], r["start_min"], r["end_min"]):
                continue
            if not protected_overlap(closure, p["blocks"], r["blocks"]):
                continue
            window = clip_window(p["start_min"], p["end_min"], r["start_min"], r["end_min"])
            assert window is not None
            parts = apply_salt_participants([p["claim_id"], r["train_id"]], salt)
            groups.append(
                {
                    "group_key": "|".join(parts),
                    "participants": parts,
                    "window_start": window[0],
                    "window_end": window[1],
                    "blocks": block_km_order(sf, sorted(set(p["blocks"]) | set(r["blocks"]))),
                    "reasons": ["possession_train"],
                }
            )

    sig_rows = signal_conflicts(closure, sf, reservations, salt)
    groups.extend(sig_rows)
    groups.sort(key=lambda g: g["group_key"])

    summary = {
        "total_conflicts": len(groups),
        "signal_blocked": len(sig_rows),
        "override_suppressed": override_suppressed,
        "possession_pairs": possession_pairs,
    }
    rep: dict[str, Any] = {
        "seed": seed,
        "scenario": scenario,
        "possession_id": possession_id(seed, scenario, load_seq),
        "conflict_groups": groups,
        "summary": summary,
        "audit_digest": "",
    }
    rep["audit_digest"] = audit_digest(summary, groups)
    return rep

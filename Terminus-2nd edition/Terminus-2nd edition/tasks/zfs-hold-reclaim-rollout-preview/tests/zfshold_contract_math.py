"""Independent ZFS reclaim rollout contract math."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


PRIORITY = ["blocked_hold", "blocked_clone", "blocked_bookmark", "blocked_pool_floor"]


def apply_hold_salt(inv: dict[str, Any], salt: str) -> dict[str, Any]:
    out = json.loads(json.dumps(inv))
    if salt:
        for ds in out.get("datasets", []):
            holds = ds.get("holds") or []
            ds["holds"] = [h + salt for h in holds]
    return out


def reference_evaluate(inv: dict[str, Any]) -> dict[str, Any]:
    floor_ok = float(inv["free_pct"]) > float(inv["floor_pct"])
    hold_blocked: dict[str, str] = {}
    clone_blocked: dict[str, str] = {}
    book_blocked: dict[str, str] = {}

    for ds in inv.get("datasets", []):
        if ds.get("kind") == "snapshot" and (ds.get("holds") or []):
            hold_blocked[ds["name"]] = "blocked_hold"
        origin = ds.get("clone_of")
        if origin:
            clone_blocked[str(origin)] = "blocked_clone"

    for bk in inv.get("bookmarks", []):
        target = bk.get("target")
        if target:
            book_blocked[str(target)] = "blocked_bookmark"

    blocked: dict[str, str] = {}
    eligible_raw: list[dict[str, Any]] = []
    for ds in inv.get("datasets", []):
        if ds.get("kind") != "snapshot":
            continue
        name = ds["name"]
        reasons: list[str] = []
        if name in hold_blocked:
            reasons.append("blocked_hold")
        if name in clone_blocked:
            reasons.append("blocked_clone")
        if name in book_blocked:
            reasons.append("blocked_bookmark")
        if not floor_ok:
            reasons.append("blocked_pool_floor")
        if reasons:
            reasons.sort(key=lambda r: PRIORITY.index(r))
            blocked[name] = reasons[0]
        else:
            eligible_raw.append(
                {
                    "name": name,
                    "depth": int(ds["depth"]),
                    "creation_txg": int(ds["creation_txg"]),
                }
            )

    eligible_raw.sort(key=lambda r: (-r["depth"], r["creation_txg"], r["name"]))
    eligible = []
    for i, row in enumerate(eligible_raw, 1):
        eligible.append({**row, "reclaim_rank": i})

    return {
        "eligible": eligible,
        "blocked": [{"name": n, "block_reason": r} for n, r in sorted(blocked.items())],
        "eligible_count": len(eligible),
        "blocked_count": len(blocked),
    }


# Back-compat alias used by older helpers.
evaluate = reference_evaluate


def reference_audit_digest(eligible: list[dict[str, Any]]) -> str:
    names = [r["name"] for r in sorted(eligible, key=lambda r: int(r["reclaim_rank"]))]
    payload = "".join(n + "\n" for n in names)
    return hashlib.sha256(payload.encode()).hexdigest()


audit_digest = reference_audit_digest


def load_scenario(path: Path, salt: str = "") -> dict[str, Any]:
    inv = json.loads(path.read_text(encoding="utf-8"))
    return apply_hold_salt(inv, salt)

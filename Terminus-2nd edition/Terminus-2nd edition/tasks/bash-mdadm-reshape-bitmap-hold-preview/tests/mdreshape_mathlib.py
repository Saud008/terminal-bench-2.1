"""Independent mdadm reshape eligibility contract math."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


PRIORITY = [
    "blocked_bitmap",
    "blocked_spare_hold",
    "blocked_degraded",
    "blocked_illegal_path",
    "blocked_window",
]

MIN_ACTIVE_DISKS = {"raid1": 1, "raid5": 3, "raid6": 4, "raid10": 2}

ALLOWED_LEVEL_PATHS = {
    ("raid1", "raid5"),
    ("raid5", "raid6"),
    ("raid5", "raid1"),
    ("raid10", "raid10"),
}


def salted_name(host_salt: str, name: str) -> str:
    digest = hashlib.sha256((host_salt + ":" + name).encode("utf-8")).hexdigest()
    return digest[:16]


def apply_host_salt(inv: dict[str, Any]) -> dict[str, Any]:
    out = json.loads(json.dumps(inv))
    host_salt = out.get("host_salt") or ""
    for arr in out.get("arrays", []):
        arr["salted_name"] = salted_name(host_salt, arr["name"])
    return out


def reference_evaluate(inv: dict[str, Any]) -> dict[str, Any]:
    spare_holds = set(inv.get("spare_holds") or [])
    window_hours = float(inv["window_hours"])

    blocked: dict[str, str] = {}
    eligible_raw: list[dict[str, Any]] = []

    for arr in inv.get("arrays", []):
        name = arr["name"]
        reasons: list[str] = []

        bitmap = arr.get("bitmap")
        clear_planned = bool(arr.get("bitmap_clear_planned"))
        if bitmap in ("internal", "external") and not clear_planned:
            reasons.append("blocked_bitmap")

        spares = arr.get("spares") or []
        if any(s in spare_holds for s in spares):
            reasons.append("blocked_spare_hold")

        level = arr.get("level")
        minimum = MIN_ACTIVE_DISKS.get(level)
        if minimum is not None and int(arr.get("active_disks", 0)) < minimum:
            reasons.append("blocked_degraded")

        pair = (arr.get("level"), arr.get("target_level"))
        if pair not in ALLOWED_LEVEL_PATHS:
            reasons.append("blocked_illegal_path")

        if float(arr.get("estimated_hours", 0)) > window_hours:
            reasons.append("blocked_window")

        if reasons:
            reasons.sort(key=lambda r: PRIORITY.index(r))
            blocked[name] = reasons[0]
        else:
            eligible_raw.append(
                {
                    "name": name,
                    "salted_name": arr.get("salted_name", ""),
                    "criticality": int(arr["criticality"]),
                    "level": arr["level"],
                    "target_level": arr["target_level"],
                }
            )

    eligible_raw.sort(key=lambda r: (int(r["criticality"]), r["name"]))

    return {
        "eligible": eligible_raw,
        "blocked": [{"name": n, "block_reason": r} for n, r in sorted(blocked.items())],
        "eligible_count": len(eligible_raw),
        "blocked_count": len(blocked),
    }


evaluate = reference_evaluate


def reference_audit_digest(
    run_id: str,
    scenario: str,
    eligible: list[dict[str, Any]],
    blocked: list[dict[str, Any]],
) -> str:
    eligible_names = ",".join(r["name"] for r in eligible)
    blocked_pairs = ",".join(f'{r["name"]}:{r["block_reason"]}' for r in blocked)
    payload = "|".join(
        [
            "mdreshape",
            "v1",
            run_id,
            scenario,
            str(len(eligible)),
            str(len(blocked)),
            eligible_names,
            blocked_pairs,
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


audit_digest = reference_audit_digest


def load_scenario(path: Path) -> dict[str, Any]:
    inv = json.loads(path.read_text(encoding="utf-8"))
    return apply_host_salt(inv)

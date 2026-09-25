"""Independent bond-trust reconnect eligibility math — kept out of /app production imports."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

REASON_PRECEDENCE = [
    "ineligible_pairing_required",
    "ineligible_resume_armed",
    "ineligible_power_sequence",
    "ineligible_reconnect_storm",
]

DEFAULT_DEBOUNCE_MS = 500
DEFAULT_MAX_RECONNECTS = 3


def compute_salted_id(host_salt: str, adapter_id: str, mac: str) -> str:
    digest = hashlib.sha256(f"{host_salt}:{adapter_id}:{mac}".encode("utf-8")).hexdigest()
    return digest[:16]


def with_salted_ids(inv: dict[str, Any]) -> dict[str, Any]:
    out = json.loads(json.dumps(inv))
    host_salt = out.get("host_salt") or ""
    for adapter in out.get("adapters", []):
        adapter_id = adapter["adapter_id"]
        for dev in adapter.get("devices", []):
            dev["salted_id"] = compute_salted_id(host_salt, adapter_id, dev["mac"])
    return out


def unique_gatt_service_count(gatt_uuids: list[str]) -> int:
    return len({u.lower() for u in (gatt_uuids or [])})


def debounced_reconnect_attempts(probes_ms: list[int], debounce_ms: int = DEFAULT_DEBOUNCE_MS) -> int:
    probes = probes_ms or []
    if not probes:
        return 0
    ordered = sorted(probes)
    count = 1
    last = ordered[0]
    for p in ordered[1:]:
        if p - last >= debounce_ms:
            count += 1
            last = p
    return count


def evaluate_fleet(
    inv: dict[str, Any],
    *,
    debounce_ms: int = DEFAULT_DEBOUNCE_MS,
    max_reconnects_per_window: int = DEFAULT_MAX_RECONNECTS,
) -> dict[str, Any]:
    ineligible: dict[str, dict[str, Any]] = {}
    eligible_raw: list[dict[str, Any]] = []

    for adapter in inv.get("adapters", []):
        adapter_id = adapter["adapter_id"]
        power_plan = adapter.get("power_plan")
        for dev in adapter.get("devices", []):
            mac = dev["mac"]
            key = f"{adapter_id}|{mac}"
            reasons: list[str] = []

            trusted = bool(dev.get("trusted"))
            addr_type = dev.get("addr_type")
            bonded_addr_type = dev.get("bonded_addr_type")
            pairing_confirmed = bool(dev.get("pairing_confirmed"))
            if trusted and addr_type != bonded_addr_type and not pairing_confirmed:
                reasons.append("ineligible_pairing_required")

            token = dev.get("resume_token") or ""
            cleared = bool(dev.get("resume_cleared"))
            if token and not cleared:
                reasons.append("ineligible_resume_armed")

            if power_plan == "off_first" and not bool(dev.get("disconnect_before_power")):
                reasons.append("ineligible_power_sequence")
            elif power_plan not in ("cycle", "off_first"):
                reasons.append("ineligible_power_sequence")

            attempts = debounced_reconnect_attempts(dev.get("battery_probes_ms") or [], debounce_ms)
            if attempts > max_reconnects_per_window:
                reasons.append("ineligible_reconnect_storm")

            if reasons:
                reasons.sort(key=lambda r: REASON_PRECEDENCE.index(r))
                ineligible[key] = {
                    "adapter_id": adapter_id,
                    "mac": mac,
                    "reason": reasons[0],
                }
            else:
                eligible_raw.append(
                    {
                        "adapter_id": adapter_id,
                        "mac": mac,
                        "salted_id": dev.get("salted_id", ""),
                        "criticality": int(dev["criticality"]),
                        "gatt_service_count": unique_gatt_service_count(dev.get("gatt_uuids") or []),
                        "reconnect_attempts": attempts,
                    }
                )

    eligible_raw.sort(key=lambda r: (int(r["criticality"]), r["mac"]))
    for idx, row in enumerate(eligible_raw, start=1):
        row["rank"] = idx

    ineligible_rows = sorted(ineligible.values(), key=lambda r: (r["adapter_id"], r["mac"]))

    return {
        "eligible": eligible_raw,
        "ineligible": ineligible_rows,
        "eligible_count": len(eligible_raw),
        "ineligible_count": len(ineligible_rows),
    }


def compute_audit_digest(
    eligible: list[dict[str, Any]],
    ineligible: list[dict[str, Any]],
) -> str:
    lines: list[str] = []
    for row in eligible:
        lines.append(f'{row["adapter_id"]}|{row["mac"]}|true||{row["rank"]}')
    for row in ineligible:
        lines.append(f'{row["adapter_id"]}|{row["mac"]}|false|{row["reason"]}|')
    lines.sort()
    payload = "\n".join(lines)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_fleet_scenario(path: Path) -> dict[str, Any]:
    inv = json.loads(path.read_text(encoding="utf-8"))
    return with_salted_ids(inv)


def reference_audit_digest(eligible: list[dict[str, Any]], ineligible: list[dict[str, Any]]) -> str:
    """Probe-visible reference_ alias for deterministic atlas digest math."""
    return compute_audit_digest(eligible, ineligible)

"""Independent reference FSM and seal oracle for bondattest absorb/seal."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class DeviceRecord:
    addr_type: str = "public"
    trusted: bool = False
    resume_token: str = ""
    bonded: bool = False
    pairing_confirmed: bool = False


@dataclass
class AttestState:
    debounce_ms: int = 500
    adapter_power: str = "on"
    devices: dict[str, DeviceRecord] = field(default_factory=dict)
    gatt_seen: set[tuple[str, str]] = field(default_factory=set)
    gatt_resolve_count: int = 0
    pairing_confirms: int = 0
    reconnect_attempts: int = 0
    resume_tokens_cleared: int = 0
    disconnect_reasons: list[dict[str, Any]] = field(default_factory=list)
    ledger_rows: list[dict[str, Any]] = field(default_factory=list)
    last_reconnect_ts: dict[str, int] = field(default_factory=dict)


def load_debounce_ms(config: Path) -> int:
    doc = json.loads(config.read_text(encoding="utf-8"))
    return int(doc["debounce_ms"])


def load_trace_rows(trace: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw in trace.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line:
            rows.append(json.loads(line))
    rows.sort(key=lambda r: (int(r["seq"]), int(r.get("ts", 0))))
    return rows


def _device(st: AttestState, mac: str) -> DeviceRecord:
    if mac not in st.devices:
        st.devices[mac] = DeviceRecord()
    return st.devices[mac]


def _emit(st: AttestState, row: dict[str, Any]) -> None:
    st.ledger_rows.append(row)


def apply_seed_bond(st: AttestState, ev: dict[str, Any]) -> None:
    mac = ev["mac"]
    dev = _device(st, mac)
    dev.addr_type = ev.get("addr_type", "public")
    dev.trusted = bool(ev.get("trusted", False))
    dev.resume_token = str(ev.get("resume_token", ""))
    dev.bonded = True
    dev.pairing_confirmed = False
    _emit(
        st,
        {
            "event": "seed_bond",
            "mac": mac,
            "addr_type": dev.addr_type,
            "resume_token": dev.resume_token,
        },
    )


def apply_pairing_confirm(st: AttestState, ev: dict[str, Any]) -> None:
    mac = ev["mac"]
    dev = _device(st, mac)
    dev.pairing_confirmed = True
    st.pairing_confirms += 1
    _emit(st, {"event": "pairing_confirm", "mac": mac})


def _connect_allowed(st: AttestState, mac: str, addr_type: str) -> bool:
    dev = _device(st, mac)
    if not dev.trusted:
        return True
    if addr_type == dev.addr_type:
        return True
    return dev.pairing_confirmed


def apply_connect(st: AttestState, ev: dict[str, Any]) -> None:
    mac = ev["mac"]
    addr_type = ev.get("addr_type", "public")
    if not _connect_allowed(st, mac, addr_type):
        _emit(st, {"event": "connect_rejected", "mac": mac, "reason": "pairing_required"})
        return
    _emit(st, {"event": "connect", "mac": mac, "addr_type": addr_type})


def apply_disconnect(st: AttestState, ev: dict[str, Any]) -> None:
    mac = ev["mac"]
    reason = ev.get("reason", "unknown")
    st.disconnect_reasons.append({"mac": mac, "reason": reason, "adapter_power": st.adapter_power})
    _emit(
        st,
        {
            "event": "disconnect",
            "mac": mac,
            "reason": reason,
            "adapter_power": st.adapter_power,
        },
    )
    dev = _device(st, mac)
    dev.pairing_confirmed = False


def apply_bond_remove(st: AttestState, ev: dict[str, Any]) -> None:
    mac = ev["mac"]
    dev = _device(st, mac)
    if dev.resume_token:
        st.resume_tokens_cleared += 1
    dev.resume_token = ""
    dev.bonded = False
    dev.trusted = False
    dev.pairing_confirmed = False
    _emit(st, {"event": "bond_remove", "mac": mac})


def apply_adapter_power(st: AttestState, ev: dict[str, Any]) -> None:
    st.adapter_power = ev.get("state", "on")
    _emit(st, {"event": "adapter_power", "state": st.adapter_power})


def apply_gatt_discover(st: AttestState, ev: dict[str, Any]) -> None:
    mac = ev["mac"]
    uuid = ev["uuid"].lower()
    key = (mac, uuid)
    if key in st.gatt_seen:
        return
    st.gatt_seen.add(key)
    st.gatt_resolve_count += 1
    _emit(st, {"event": "gatt_discover", "mac": mac, "uuid": uuid})


def apply_battery_level(st: AttestState, ev: dict[str, Any]) -> None:
    mac = ev["mac"]
    ts = int(ev.get("ts", 0))
    last = st.last_reconnect_ts.get(mac, -10_000)
    if ts - last < st.debounce_ms:
        _emit(st, {"event": "reconnect_suppressed", "mac": mac, "ts": ts})
        return
    st.last_reconnect_ts[mac] = ts
    st.reconnect_attempts += 1
    _emit(st, {"event": "reconnect_attempt", "mac": mac, "ts": ts})


OPS = {
    "seed_bond": apply_seed_bond,
    "pairing_confirm": apply_pairing_confirm,
    "connect": apply_connect,
    "disconnect": apply_disconnect,
    "bond_remove": apply_bond_remove,
    "adapter_power": apply_adapter_power,
    "gatt_discover": apply_gatt_discover,
    "battery_level": apply_battery_level,
}


def _midstate_payload(seed: str, trace_name: str, st: AttestState) -> str:
    return "\n".join(
        [
            f"seed={seed}",
            f"trace={trace_name}",
            f"adapter_power={st.adapter_power}",
            f"pairing_confirms={st.pairing_confirms}",
            f"resume_tokens_cleared={st.resume_tokens_cleared}",
            f"gatt_resolve_count={st.gatt_resolve_count}",
            f"reconnect_attempts={st.reconnect_attempts}",
            "disconnect_reasons=" + json.dumps(st.disconnect_reasons, separators=(",", ":")),
        ]
    )


def absorb(trace: Path, config: Path, seed: str) -> dict[str, Any]:
    st = AttestState(debounce_ms=load_debounce_ms(config))
    for ev in load_trace_rows(trace):
        op = ev["op"]
        handler = OPS.get(op)
        if handler is None:
            raise ValueError(f"unknown op: {op}")
        handler(st, ev)

    midstate_digest = sha256_hex(_midstate_payload(seed, trace.name, st))
    return {
        "schema_version": 1,
        "seed": seed,
        "trace": trace.name,
        "adapter_power": st.adapter_power,
        "pairing_confirms": st.pairing_confirms,
        "resume_tokens_cleared": st.resume_tokens_cleared,
        "gatt_resolve_count": st.gatt_resolve_count,
        "reconnect_attempts": st.reconnect_attempts,
        "disconnect_reasons": st.disconnect_reasons,
        "ledger_rows": st.ledger_rows,
        "midstate_digest": midstate_digest,
    }


def ledger_fingerprint(ledger_rows: list[dict[str, Any]]) -> str:
    blob = json.dumps(ledger_rows, sort_keys=True, separators=(",", ":"))
    return sha256_hex(blob)


def seal(midstate: dict[str, Any]) -> dict[str, Any]:
    lf = ledger_fingerprint(midstate["ledger_rows"])
    bundle_seal = sha256_hex(f"{midstate['midstate_digest']}|{lf}|{midstate['seed']}")
    return {
        "schema_version": 1,
        "seed": midstate["seed"],
        "trace": midstate["trace"],
        "counts": {
            "pairing_confirms": midstate["pairing_confirms"],
            "resume_tokens_cleared": midstate["resume_tokens_cleared"],
            "gatt_resolve_count": midstate["gatt_resolve_count"],
            "reconnect_attempts": midstate["reconnect_attempts"],
        },
        "disconnect_reasons": midstate["disconnect_reasons"],
        "ledger_fingerprint": lf,
        "bundle_seal": bundle_seal,
    }


def run_pipeline(trace: Path, config: Path, seed: str) -> tuple[dict[str, Any], dict[str, Any]]:
    midstate = absorb(trace, config, seed)
    bundle = seal(midstate)
    return midstate, bundle

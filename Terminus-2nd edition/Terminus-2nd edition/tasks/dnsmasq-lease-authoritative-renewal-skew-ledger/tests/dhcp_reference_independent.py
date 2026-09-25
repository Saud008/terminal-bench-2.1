"""Independent DHCP replay reference for dnsmasqledger verifier."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def identity_key(mac: str, duid: str, iaid: int) -> str:
    return f"{mac.lower().strip()}|{duid.lower().strip()}|{iaid}"


def load_events(path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        events.append(json.loads(line))
    return sorted(events, key=lambda e: (e["seq"], e.get("tie", 0)))


def invalidate_dns(dns: dict[str, str], hostname: str, ip: str) -> None:
    if not hostname:
        return
    if dns.get(hostname) == ip:
        del dns[hostname]


def bind_dns(dns: dict[str, str], hostname: str, ip: str) -> None:
    if hostname and ip:
        dns[hostname] = ip


def expire_due(state: dict[str, Any]) -> None:
    now = state["now_sec"]
    leases = state["leases"]
    for key in list(leases.keys()):
        lease = leases[key]
        if now >= lease["expires_sec"]:
            invalidate_dns(state["dns_forward"], lease["hostname"], lease["ip"])
            del leases[key]
    tentative = state["tentative"]
    for key in list(tentative.keys()):
        t = tentative[key]
        if t.get("expires_sec", 0) > 0 and now >= t["expires_sec"]:
            del tentative[key]


def apply_event(state: dict[str, Any], ev: dict[str, Any], ack_seen: dict[int, bool]) -> bool:
    op = ev["op"]
    if op == "tick":
        state["now_sec"] += int(ev.get("elapsed_sec", 0))
        expire_due(state)
        return True
    if op == "dhcp_discover":
        key = identity_key(ev["mac"], ev["duid"], ev["iaid"])
        state["tentative"][key] = {
            "identity_key": key,
            "mac": ev["mac"],
            "duid": ev["duid"],
            "iaid": ev["iaid"],
            "hostname": ev.get("hostname", ""),
        }
        return True
    if op == "dhcp_offer":
        key = identity_key(ev["mac"], ev["duid"], ev["iaid"])
        t = state["tentative"].get(key)
        if not t:
            return False
        t["ip"] = ev["ip"]
        t["lease_sec"] = ev["lease_sec"]
        t["expires_sec"] = state["now_sec"] + ev["lease_sec"]
        return True
    if op == "dhcp_request":
        return True
    if op == "dhcp_ack":
        key = identity_key(ev["mac"], ev["duid"], ev["iaid"])
        if not ev.get("ip"):
            return False
        prev = state["leases"].get(key)
        old_ip = prev["ip"] if prev else ""
        old_host = prev["hostname"] if prev else ""
        lease_sec = ev.get("lease_sec") or (prev or {}).get("lease_sec") or 3600
        hostname = ev.get("hostname") or (prev or {}).get("hostname", "")
        if not hostname:
            t = state["tentative"].get(key)
            hostname = (t or {}).get("hostname", "")
        state["leases"][key] = {
            "identity_key": key,
            "mac": ev["mac"],
            "duid": ev["duid"],
            "iaid": ev["iaid"],
            "hostname": hostname,
            "ip": ev["ip"],
            "lease_sec": lease_sec,
            "expires_sec": state["now_sec"] + lease_sec,
            "authoritative": True,
        }
        state["tentative"].pop(key, None)
        if prev and old_ip != ev["ip"] and old_host:
            invalidate_dns(state["dns_forward"], old_host, old_ip)
        bind_dns(state["dns_forward"], hostname, ev["ip"])
        ack_seen[ev["seq"]] = True
        return True
    if op == "dhcp_renew":
        key = identity_key(ev["mac"], ev["duid"], ev["iaid"])
        lease = state["leases"].get(key)
        if not lease or not lease["authoritative"]:
            return False
        lease_sec = ev.get("lease_sec") or lease["lease_sec"]
        lease["expires_sec"] = lease["expires_sec"] + lease_sec
        lease["lease_sec"] = lease_sec
        return True
    if op == "dhcp_decline":
        key = identity_key(ev["mac"], ev["duid"], ev["iaid"])
        lease = state["leases"].get(key)
        if lease and lease.get("hostname"):
            invalidate_dns(state["dns_forward"], lease["hostname"], lease["ip"])
            state["leases"].pop(key, None)
        state["tentative"].pop(key, None)
        return True
    if op == "dhcp_release":
        key = identity_key(ev["mac"], ev["duid"], ev["iaid"])
        lease = state["leases"].get(key)
        if not lease:
            return False
        if lease.get("hostname"):
            invalidate_dns(state["dns_forward"], lease["hostname"], lease["ip"])
        state["leases"].pop(key, None)
        state["tentative"].pop(key, None)
        return True
    if op == "replay_checkpoint":
        state["checkpoint_seq"] = ev.get("through_seq", ev["seq"])
        return True
    return True


def replay_log(path: Path) -> dict[str, Any]:
    state: dict[str, Any] = {
        "now_sec": 0,
        "leases": {},
        "tentative": {},
        "dns_forward": {},
        "journal": [],
        "checkpoint_seq": 0,
    }
    ack_seen: dict[int, bool] = {}
    applied = 0
    for ev in load_events(path):
        expire_due(state)
        ok = apply_event(state, ev, ack_seen)
        state["journal"].append(
            {"seq": ev["seq"], "op": ev["op"], "ok": ok, "at_sec": state["now_sec"]}
        )
        applied += 1
    expire_due(state)
    active = []
    for lease in state["leases"].values():
        if lease["authoritative"] and state["now_sec"] < lease["expires_sec"]:
            active.append(
                {
                    "identity_key": lease["identity_key"],
                    "mac": lease["mac"],
                    "duid": lease["duid"],
                    "iaid": lease["iaid"],
                    "hostname": lease["hostname"],
                    "ip": lease["ip"],
                    "expires_sec": lease["expires_sec"],
                    "authoritative": True,
                }
            )
    active.sort(key=lambda r: (r["identity_key"], r["hostname"]))
    tail = state["journal"][-8:]
    return {
        "now_sec": state["now_sec"],
        "active_leases": active,
        "dns_forward": dict(state["dns_forward"]),
        "journal_tail": tail,
        "checkpoint_seq": state["checkpoint_seq"],
        "events_applied": applied,
        "tentative_count": len(state["tentative"]),
    }


def mutate_mac(seed: str, base: str) -> str:
    parts = base.split(":")
    n = sum(ord(c) for c in seed) % 200
    parts[-1] = f"{(int(parts[-1], 16) + n) % 256:02x}"
    return ":".join(parts)

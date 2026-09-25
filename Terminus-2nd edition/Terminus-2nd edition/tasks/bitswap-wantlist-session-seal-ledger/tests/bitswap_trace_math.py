"""Independent bitswap session reference replay for pytest."""

from __future__ import annotations

CID_REGISTRY = {
    "bafyAA0000000000000000000000000000000000000000000000000000000000000001": "a1000000000000000000000000000000000000000000000000000000000000000001",
    "bafyAA0000000000000000000000000000000000000000000000000000000000000002": "a1000000000000000000000000000000000000000000000000000000000000000002",
    "bafyAA0000000000000000000000000000000000000000000000000000000000000003": "a1000000000000000000000000000000000000000000000000000000000000000003",
    "bafyAA0000000000000000000000000000000000000000000000000000000000000004": "a1000000000000000000000000000000000000000000000000000000000000000004",
    "QmAlias000000000000000000000000000000000000000000000000000000000001": "a1000000000000000000000000000000000000000000000000000000000000000001",
    "QmAlias000000000000000000000000000000000000000000000000000000000002": "a1000000000000000000000000000000000000000000000000000000000000000002",
    "QmAlias000000000000000000000000000000000000000000000000000000000003": "a1000000000000000000000000000000000000000000000000000000000000000003",
    "QmAlias000000000000000000000000000000000000000000000000000000000004": "a1000000000000000000000000000000000000000000000000000000000000000004",
}

IDLE_LIMIT = 5000


def canonical(display: str) -> str:
    key = CID_REGISTRY.get(display)
    if not key:
        raise KeyError(display)
    return key


def load_trace_events(path) -> list[dict]:
    import json
    from pathlib import Path

    events: list[dict] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        events.append(json.loads(line))
    return sorted(events, key=lambda e: e["seq"])


def reference_bitswap_session(events: list[dict], name: str) -> dict:
    """Independent reference session state matching contract docs."""
    state = {
        "name": name,
        "wants": {},
        "in_flight": {},
        "partial": {},
        "ledger": {},
        "canceled": set(),
        "delivered": [],
        "last_activity": 0,
    }

    def touch() -> None:
        state["last_activity"] = 0

    def merge_wants(wants: list[dict]) -> None:
        for w in wants:
            cid = w["cid"]
            canon_key = canonical(cid)
            if canon_key in state["canceled"]:
                continue
            ent = state["wants"].get(canon_key)
            pri = int(w.get("priority", 0))
            if ent:
                ent["priority"] = max(ent["priority"], pri)
            else:
                state["wants"][canon_key] = {"display": cid, "priority": pri}

    for ev in events:
        op = ev["op"]
        if op == "want":
            cid = ev["cid"]
            canon_key = canonical(cid)
            if canon_key in state["canceled"]:
                continue
            pri = int(ev.get("priority", 0))
            ent = state["wants"].get(canon_key)
            if ent:
                ent["priority"] = max(ent["priority"], pri)
            else:
                state["wants"][canon_key] = {"display": cid, "priority": pri}
            touch()
        elif op == "merge_wants":
            merge_wants(ev.get("wants", []))
            touch()
        elif op == "cancel":
            cid = ev["cid"]
            canon_key = canonical(cid)
            state["canceled"].add(canon_key)
            if canon_key not in state["in_flight"]:
                state["wants"].pop(canon_key, None)
            touch()
        elif op == "block_start":
            canon_key = canonical(ev["cid"])
            state["in_flight"][canon_key] = ev.get("peer", "")
            touch()
        elif op == "block_part":
            canon_key = canonical(ev["cid"])
            state["partial"][canon_key] = int(ev.get("bytes", 0))
            touch()
        elif op == "block_done":
            cid = ev["cid"]
            canon_key = canonical(cid)
            peer = ev.get("peer", "")
            bytes_val = int(ev.get("bytes", 0))
            state["in_flight"].pop(canon_key, None)
            state["partial"].pop(canon_key, None)
            ledger_peer = state["ledger"].setdefault(peer, {})
            if ledger_peer.get(cid, 0) == 0:
                ledger_peer[cid] = bytes_val
            ent = state["wants"].pop(canon_key, None)
            pri = ent["priority"] if ent else 0
            display = ent["display"] if ent else cid
            state["delivered"].append(
                {"cid": display, "peer": peer, "bytes": bytes_val, "priority": pri}
            )
            state["canceled"].discard(canon_key)
            touch()
        elif op == "tick":
            state["last_activity"] += int(ev.get("idle_ms", 0))
            if state["last_activity"] >= IDLE_LIMIT:
                state["wants"] = {}
                state["partial"] = {}
                state["in_flight"] = {}
        else:
            raise AssertionError(f"unknown op {op}")

    wants_remaining = sorted(
        (
            {"cid": v["display"], "priority": v["priority"]}
            for v in state["wants"].values()
        ),
        key=lambda row: (-row["priority"], row["cid"]),
    )
    delivered = sorted(
        state["delivered"],
        key=lambda row: (row["cid"], row["peer"]),
    )
    ledger_totals: list[dict] = []
    for peer in sorted(state["ledger"]):
        for cid in sorted(state["ledger"][peer]):
            ledger_totals.append(
                {"peer": peer, "cid": cid, "credit": state["ledger"][peer][cid]}
            )

    return {
        "session_id": name,
        "wants_remaining": wants_remaining,
        "delivered": delivered,
        "ledger_totals": ledger_totals,
        "partial_blocks": len(state["partial"]),
        "in_flight_count": len(state["in_flight"]),
    }


def reference_bitswap_metrics(events: list[dict], name: str) -> dict:
    snap = reference_bitswap_session(events, name)
    active = snap["wants_remaining"]
    if not active:
        return {
            "report_version": 1,
            "session_id": name,
            "queue_head_cid": "",
            "queue_head_priority": 0,
            "cancel_merged": True,
        }
    head = min(active, key=lambda row: (-row["priority"], row["cid"]))
    return {
        "report_version": 1,
        "session_id": name,
        "queue_head_cid": head["cid"],
        "queue_head_priority": head["priority"],
        "cancel_merged": True,
    }

from __future__ import annotations

import sqlite3

from . import ledger, query


def load_party_state(db: sqlite3.Connection, party_id: str) -> dict | None:
    meta = query.party_meta_for(db, party_id)
    if not meta:
        return None
    return {
        **meta,
        "connected_ids": query.connected_member_ids(db, party_id),
        "pending_invites": query.pending_invite_refs(db, party_id),
    }


def write_audit_snapshot(db: sqlite3.Connection, party_id: str, mono_ms: int) -> None:
    state = load_party_state(db, party_id)
    if state is None:
        return
    value = ledger.load()
    if ledger.append_if_changed(value, state, mono_ms):
        ledger.save(value)


def mark_sweep_epoch() -> int:
    value = ledger.load()
    value["sweep_epoch"] += 1
    ledger.save(value)
    return value["sweep_epoch"]


def refresh_snapshots_after_sweep(db: sqlite3.Connection, mono_ms: int) -> int:
    value = ledger.load()
    changed = False
    live = query.party_ids_ordered(db)
    live_set = set(live)
    for party_id in live:
        state = load_party_state(db, party_id)
        if state and ledger.append_if_changed(value, state, mono_ms):
            changed = True
    retired = 0
    for party_id in ledger.party_ids_with_history(value):
        if party_id in live_set:
            continue
        old = ledger.latest_for(value, party_id)
        if not old or old["status"] == "retired":
            continue
        state = {
            "party_id": party_id,
            "leader_id": old["leader_id"],
            "status": "retired",
            "max_members": old["max_members"],
            "connected_ids": [],
            "pending_invites": [],
        }
        if ledger.append_if_changed(value, state, mono_ms):
            changed = True
            retired += 1
    if changed:
        ledger.save(value)
    return retired

from __future__ import annotations

import json
import sqlite3

from . import ledger, query

TOKENS = (
    "audit ledger unavailable",
    "audit ledger chain broken",
    "audit ledger party unstaged",
    "audit ledger party retired",
    "audit ledger party missing",
    "audit ledger drift",
)


class ExportRefusal(Exception):
    pass


def build_audit_report(db: sqlite3.Connection, party_id: str, mono_ms: int) -> dict:
    if not ledger.PATH.exists():
        raise ExportRefusal(TOKENS[0])
    try:
        value = ledger.load()
    except (OSError, ValueError, TypeError, json.JSONDecodeError):
        raise ExportRefusal(TOKENS[0]) from None
    if value.get("snapshot_version") != ledger.VERSION:
        raise ExportRefusal(TOKENS[0])
    if not ledger.verify(value):
        raise ExportRefusal(TOKENS[1])
    entry = ledger.latest_for(value, party_id)
    if not entry:
        raise ExportRefusal(TOKENS[2])
    if entry["status"] == "retired":
        raise ExportRefusal(TOKENS[3])
    meta = query.party_meta_for(db, party_id)
    if not meta:
        raise ExportRefusal(TOKENS[4])
    if any(meta[k] != entry[k] for k in ("status", "leader_id", "max_members")):
        raise ExportRefusal(TOKENS[5])
    connected = query.connected_member_ids(db, party_id)
    joined = set(connected)
    eligible = {
        row["invitee_id"]
        for row in entry["pending_invites"]
        if row["expires_mono_ms"] > mono_ms and row["invitee_id"] not in joined
    }
    stale = sum(
        1 for row in entry["pending_invites"] if row["expires_mono_ms"] <= mono_ms
    )
    reserved = len(eligible)
    return {
        "party_id": entry["party_id"],
        "leader_id": entry["leader_id"],
        "status": entry["status"],
        "max_members": entry["max_members"],
        "connected_members": len(connected),
        "pending_invites": query.count_pending_invites(db, party_id),
        "effective_occupancy": len(connected) + reserved,
        "expired_pending_invites": query.count_expired_pending_invites(
            db, party_id, mono_ms
        ),
        "orphan_party": entry["status"] == "active"
        and not query.leader_connected(db, party_id),
        "audit_seq": value["audit_seq"],
        "staged_party_seq": entry["party_seq"],
        "sweep_epoch": value["sweep_epoch"],
        "chain_head": value["chain_head"],
        "reserved_slots": reserved,
        "stale_staged_invites": stale,
    }

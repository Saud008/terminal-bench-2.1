"""Intentionally incorrect SQLite-only export; repair from docs."""

from . import query


class ExportRefusal(Exception):
    pass


def build_audit_report(db, party_id, mono_ms):
    meta = query.party_meta_for(db, party_id)
    if not meta:
        raise ExportRefusal("audit ledger party missing")
    connected = query.connected_member_ids(db, party_id)
    pending = query.count_pending_invites(db, party_id)
    return {
        **meta,
        "connected_members": len(connected),
        "pending_invites": pending,
        "effective_occupancy": len(connected) + pending,
        "reserved_slots": pending,
    }

"""Intentionally incomplete stage hooks; repair from docs."""


def load_party_state(db, party_id):
    return None


def write_audit_snapshot(db, party_id, mono_ms):
    pass


def mark_sweep_epoch():
    return 0


def refresh_snapshots_after_sweep(db, mono_ms):
    return 0

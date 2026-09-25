"""Intentionally incomplete sweep policy; repair from docs."""


def sweep(db, mono_ms):
    expired = db.execute(
        "UPDATE invites SET status='expired' WHERE status='pending' AND expires_mono_ms<=?",
        (mono_ms,),
    ).rowcount
    removed = db.execute("DELETE FROM parties WHERE status='disbanded'", ()).rowcount
    db.commit()
    return {
        "expired_invites": expired,
        "removed_parties": removed,
        "retired_parties": 0,
        "sweep_epoch": 0,
    }

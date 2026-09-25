from __future__ import annotations

import sqlite3

from . import stage


def sweep(db: sqlite3.Connection, mono_ms: int) -> dict:
    expired = db.execute(
        "UPDATE invites SET status='expired' WHERE status='pending' AND expires_mono_ms<=?",
        (mono_ms,),
    ).rowcount
    removed = db.execute("""DELETE FROM parties WHERE status='disbanded' AND party_id NOT IN
                         (SELECT DISTINCT party_id FROM members WHERE status='connected')""").rowcount
    db.commit()
    epoch = stage.mark_sweep_epoch()
    retired = stage.refresh_snapshots_after_sweep(db, mono_ms)
    return {
        "expired_invites": expired,
        "removed_parties": removed,
        "retired_parties": retired,
        "sweep_epoch": epoch,
    }

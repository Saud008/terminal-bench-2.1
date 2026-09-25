from __future__ import annotations

import sqlite3


def party_meta_for(db: sqlite3.Connection, party_id: str) -> dict | None:
    row = db.execute(
        "SELECT party_id, leader_id, status, max_members FROM parties WHERE party_id=?",
        (party_id,),
    ).fetchone()
    return dict(row) if row else None


def party_ids_ordered(db: sqlite3.Connection) -> list[str]:
    return [r[0] for r in db.execute("SELECT party_id FROM parties ORDER BY party_id")]


def connected_member_ids(db: sqlite3.Connection, party_id: str) -> list[str]:
    return [
        r[0]
        for r in db.execute(
            "SELECT player_id FROM members WHERE party_id=? AND status='connected' ORDER BY player_id",
            (party_id,),
        )
    ]


def pending_invite_refs(db: sqlite3.Connection, party_id: str) -> list[dict]:
    return [
        dict(r)
        for r in db.execute(
            "SELECT invite_id, invitee_id, expires_mono_ms FROM invites WHERE party_id=? AND status='pending' ORDER BY expires_mono_ms, invite_id",
            (party_id,),
        )
    ]


def count_pending_invites(db: sqlite3.Connection, party_id: str) -> int:
    return db.execute(
        "SELECT COUNT(1) FROM invites WHERE party_id=? AND status='pending'",
        (party_id,),
    ).fetchone()[0]


def count_expired_pending_invites(
    db: sqlite3.Connection, party_id: str, mono_ms: int
) -> int:
    return db.execute(
        "SELECT COUNT(1) FROM invites WHERE party_id=? AND status='pending' AND expires_mono_ms<=?",
        (party_id, mono_ms),
    ).fetchone()[0]


def leader_connected(db: sqlite3.Connection, party_id: str) -> bool:
    return (
        db.execute(
            "SELECT COUNT(1) FROM parties p JOIN members m ON p.party_id=m.party_id WHERE p.party_id=? AND m.player_id=p.leader_id AND m.status='connected'",
            (party_id,),
        ).fetchone()[0]
        == 1
    )

"""Protected lifecycle baseline for host-local party operations."""

from __future__ import annotations

import json
import secrets
import sqlite3

from . import config, query, stage


def _id(prefix: str) -> str:
    return prefix + secrets.token_hex(8)


class Conflict(Exception):
    pass


def create(
    db: sqlite3.Connection, leader: str, maximum: int | None, mono_ms: int
) -> dict:
    if not leader:
        raise Conflict("leader_id required")
    cap = config.clamp_max_members(maximum, config.load()["max_members"])
    party_id = _id("pty_")
    db.execute(
        "INSERT INTO parties VALUES (?, ?, 'active', ?, ?)",
        (party_id, leader, cap, mono_ms),
    )
    db.execute(
        "INSERT INTO members VALUES (?, ?, 'leader', 'connected', ?)",
        (party_id, leader, mono_ms),
    )
    db.commit()
    return {
        "party_id": party_id,
        "leader_id": leader,
        "status": "active",
        "max_members": cap,
        "created_mono_ms": mono_ms,
    }


def invite(
    db: sqlite3.Connection,
    party_id: str,
    invitee: str,
    ttl_ms: int | None,
    mono_ms: int,
) -> dict:
    if not invitee:
        raise Conflict("invitee_id required")
    meta = query.party_meta_for(db, party_id)
    if not meta:
        raise Conflict("party not found")
    if meta["status"] != "active":
        raise Conflict("party disbanded")
    if not query.leader_connected(db, party_id):
        raise Conflict("leader disconnected")
    ttl = ttl_ms if ttl_ms and ttl_ms > 0 else config.load()["default_invite_ttl_ms"]
    connected = len(query.connected_member_ids(db, party_id))
    pending = db.execute(
        "SELECT COUNT(1) FROM invites WHERE party_id=? AND status='pending' AND expires_mono_ms>?",
        (party_id, mono_ms),
    ).fetchone()[0]
    if connected + pending >= meta["max_members"]:
        raise Conflict("party full")
    invite_id = _id("inv_")
    expires = mono_ms + ttl
    db.execute(
        "INSERT INTO invites VALUES (?, ?, ?, 'pending', ?, ?)",
        (invite_id, party_id, invitee, expires, mono_ms),
    )
    db.commit()
    stage.write_audit_snapshot(db, party_id, mono_ms)
    return {
        "invite_id": invite_id,
        "party_id": party_id,
        "invitee_id": invitee,
        "status": "pending",
        "expires_mono_ms": expires,
        "created_mono_ms": mono_ms,
    }


def accept(
    db: sqlite3.Connection, invite_id: str, invitee: str, key: str, mono_ms: int
) -> dict:
    if not key:
        raise Conflict("idempotency key required")
    cached = db.execute(
        "SELECT body_json FROM idempotency WHERE idempotency_key=?", (key,)
    ).fetchone()
    if cached:
        return json.loads(cached[0])
    row = db.execute("SELECT * FROM invites WHERE invite_id=?", (invite_id,)).fetchone()
    if not row:
        raise Conflict("invite not found")
    if row["invitee_id"] != invitee:
        raise Conflict("invitee mismatch")
    meta = query.party_meta_for(db, row["party_id"])
    if not meta or meta["status"] != "active":
        raise Conflict("party disbanded")
    if not query.leader_connected(db, row["party_id"]):
        raise Conflict("leader disconnected")
    if row["status"] != "pending":
        raise Conflict("invite not pending")
    if mono_ms >= row["expires_mono_ms"]:
        raise Conflict("invite expired")
    pending = db.execute(
        "SELECT COUNT(1) FROM invites WHERE party_id=? AND status='pending' AND expires_mono_ms>? AND invite_id<>?",
        (row["party_id"], mono_ms, invite_id),
    ).fetchone()[0]
    if (
        len(query.connected_member_ids(db, row["party_id"])) + pending
        >= meta["max_members"]
    ):
        raise Conflict("party full")
    db.execute("UPDATE invites SET status='accepted' WHERE invite_id=?", (invite_id,))
    db.execute(
        "INSERT INTO members VALUES (?, ?, 'member', 'connected', ?)",
        (row["party_id"], invitee, mono_ms),
    )
    result = {"party_id": row["party_id"], "invitee_id": invitee, "status": "joined"}
    db.execute(
        "INSERT INTO idempotency VALUES (?, 200, ?, ?)",
        (key, json.dumps(result), mono_ms),
    )
    db.commit()
    stage.write_audit_snapshot(db, row["party_id"], mono_ms)
    return result


def disconnect(
    db: sqlite3.Connection, party_id: str, player: str, mono_ms: int
) -> dict:
    meta = query.party_meta_for(db, party_id)
    if not meta:
        raise Conflict("party not found")
    status = meta["status"]
    if player == meta["leader_id"]:
        status = "disbanded"
        db.execute(
            "UPDATE parties SET status='disbanded' WHERE party_id=?", (party_id,)
        )
        db.execute(
            "UPDATE members SET status='disconnected' WHERE party_id=?", (party_id,)
        )
        db.execute(
            "UPDATE invites SET status='revoked' WHERE party_id=? AND status='pending'",
            (party_id,),
        )
    else:
        db.execute(
            "UPDATE members SET status='disconnected' WHERE party_id=? AND player_id=?",
            (party_id, player),
        )
    db.commit()
    stage.write_audit_snapshot(db, party_id, mono_ms)
    return {"party_id": party_id, "status": status}

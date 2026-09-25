"""Intentionally incorrect database projections; repair from docs."""


def party_meta_for(db, party_id):
    row = db.execute(
        "SELECT party_id,leader_id,status,max_members FROM parties WHERE party_id=?",
        (party_id,),
    ).fetchone()
    return dict(row) if row else None


def party_ids_ordered(db):
    return [r[0] for r in db.execute("SELECT party_id FROM parties")]


def connected_member_ids(db, party_id):
    return [
        r[0]
        for r in db.execute(
            "SELECT player_id FROM members WHERE party_id=?", (party_id,)
        )
    ]


def pending_invite_refs(db, party_id):
    return [
        dict(r)
        for r in db.execute(
            "SELECT invite_id,invitee_id,expires_mono_ms FROM invites WHERE party_id=?",
            (party_id,),
        )
    ]


def count_pending_invites(db, party_id):
    return db.execute(
        "SELECT COUNT(1) FROM invites WHERE party_id=?", (party_id,)
    ).fetchone()[0]


def count_expired_pending_invites(db, party_id, mono_ms):
    return 0


def leader_connected(db, party_id):
    return True

"""Canonical pas/2 staging encodings."""

from __future__ import annotations

import hashlib

GENESIS = "0" * 64
LINE_PREFIX = "pas/2"


def members_field(ids: list[str]) -> str:
    return ",".join(ids)


def invites_field(refs: list[dict]) -> str:
    return ",".join(
        f"{r['invite_id']}:{r['invitee_id']}:{r['expires_mono_ms']}" for r in refs
    )


def state_key(state: dict) -> str:
    return "|".join(
        (
            state["status"],
            state["leader_id"],
            str(state["max_members"]),
            members_field(state["connected_ids"]),
            invites_field(state["pending_invites"]),
        )
    )


def entry_line(
    seq: int, party_seq: int, staged_mono_ms: int, sweep_epoch: int, state: dict
) -> str:
    return "|".join(
        (
            LINE_PREFIX,
            str(seq),
            state["party_id"],
            str(party_seq),
            str(staged_mono_ms),
            str(sweep_epoch),
            state_key(state),
        )
    )


def digest(prev_digest: str, line: str) -> str:
    return hashlib.sha256(f"{prev_digest}|{line}".encode()).hexdigest()

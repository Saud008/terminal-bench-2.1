"""Independent reference math for the party audit staging ledger."""

from __future__ import annotations

import hashlib
from typing import Any

GENESIS = "0" * 64
LINE_PREFIX = "pas/2"
RETAINED = 8


def members_field(ids: list[str]) -> str:
    return ",".join(ids)


def invites_field(pending: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for row in pending:
        parts.append(
            f"{row['invite_id']}:{row['invitee_id']}:{int(row['expires_mono_ms'])}"
        )
    return ",".join(parts)


def state_key(
    status: str,
    leader_id: str,
    max_members: int,
    connected_ids: list[str],
    pending: list[dict[str, Any]],
) -> str:
    return "|".join(
        [
            status,
            leader_id,
            str(max_members),
            members_field(connected_ids),
            invites_field(pending),
        ]
    )


def entry_line(
    seq: int,
    party_id: str,
    party_seq: int,
    staged_mono_ms: int,
    sweep_epoch: int,
    status: str,
    leader_id: str,
    max_members: int,
    connected_ids: list[str],
    pending: list[dict[str, Any]],
) -> str:
    return "|".join(
        [
            LINE_PREFIX,
            str(seq),
            party_id,
            str(party_seq),
            str(staged_mono_ms),
            str(sweep_epoch),
            state_key(status, leader_id, max_members, connected_ids, pending),
        ]
    )


def digest(prev: str, line: str) -> str:
    return hashlib.sha256(f"{prev}|{line}".encode()).hexdigest()


def reserved_slots(
    pending: list[dict[str, Any]],
    connected_ids: list[str],
    export_mono_ms: int,
) -> tuple[int, int]:
    """Return (reserved_slots, stale_staged_invites)."""
    joined = set(connected_ids)
    reserved_for: set[str] = set()
    stale = 0
    for row in pending:
        expires = int(row["expires_mono_ms"])
        if expires <= export_mono_ms:
            stale += 1
            continue
        invitee = str(row["invitee_id"])
        if invitee in joined:
            continue
        reserved_for.add(invitee)
    return len(reserved_for), stale


def effective_occupancy(
    connected: int,
    pending: list[dict[str, Any]],
    connected_ids: list[str],
    export_mono_ms: int,
) -> int:
    reserved, _ = reserved_slots(pending, connected_ids, export_mono_ms)
    return connected + reserved


def verify_ledger(ledger: dict[str, Any]) -> None:
    assert ledger["snapshot_version"] == 2
    entries = ledger.get("entries") or []
    if not entries:
        assert ledger["chain_base"] == GENESIS
        assert ledger["chain_head"] == GENESIS
        return
    prev = ledger["chain_base"]
    last_party_seq: dict[str, int] = {}
    party_seqs = ledger.get("party_seqs") or {}
    for i, entry in enumerate(entries):
        assert entry["prev_digest"] == prev
        line = entry_line(
            entry["seq"],
            entry["party_id"],
            entry["party_seq"],
            entry["staged_mono_ms"],
            entry["sweep_epoch"],
            entry["status"],
            entry["leader_id"],
            entry["max_members"],
            entry.get("connected_ids") or [],
            entry.get("pending_invites") or [],
        )
        assert entry["entry_digest"] == digest(entry["prev_digest"], line)
        if i > 0:
            assert entry["seq"] == entries[i - 1]["seq"] + 1
        party_id = entry["party_id"]
        assert entry["party_seq"] <= int(party_seqs.get(party_id, 0))
        if party_id in last_party_seq:
            assert entry["party_seq"] > last_party_seq[party_id]
        last_party_seq[party_id] = entry["party_seq"]
        prev = entry["entry_digest"]
    assert ledger["chain_head"] == prev
    assert ledger["audit_seq"] == entries[-1]["seq"]
    assert len(entries) <= RETAINED


def latest_for(ledger: dict[str, Any], party_id: str) -> dict[str, Any] | None:
    for entry in reversed(ledger.get("entries") or []):
        if entry["party_id"] == party_id:
            return entry
    return None

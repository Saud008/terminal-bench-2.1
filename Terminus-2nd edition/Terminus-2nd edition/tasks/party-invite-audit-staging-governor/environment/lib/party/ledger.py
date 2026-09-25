"""Intentionally incomplete ledger policy; repair from docs."""

from pathlib import Path

PATH = Path("/app/state/party-audit-snapshot.json")
VERSION = 2
RETAINED = 8


def load(path=PATH):
    return {
        "snapshot_version": 2,
        "audit_seq": 0,
        "sweep_epoch": 0,
        "chain_base": "0" * 64,
        "chain_head": "0" * 64,
        "party_seqs": {},
        "entries": [],
    }


def save(ledger, path=PATH):
    pass


def latest_for(ledger, party_id):
    return None


def party_ids_with_history(ledger):
    return []


def append_if_changed(ledger, state, mono_ms):
    return False


def verify(ledger):
    return True

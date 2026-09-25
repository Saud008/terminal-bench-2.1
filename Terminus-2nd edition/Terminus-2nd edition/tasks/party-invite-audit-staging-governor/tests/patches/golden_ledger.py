from __future__ import annotations

import json
from pathlib import Path

from .canon import GENESIS, digest, entry_line, state_key

PATH = Path("/app/state/party-audit-snapshot.json")
RETAINED = 8
VERSION = 2


def new() -> dict:
    return {
        "snapshot_version": VERSION,
        "audit_seq": 0,
        "sweep_epoch": 0,
        "chain_base": GENESIS,
        "chain_head": GENESIS,
        "party_seqs": {},
        "entries": [],
    }


def load(path: Path = PATH) -> dict:
    if not path.exists():
        return new()
    ledger = json.loads(path.read_text(encoding="utf-8"))
    ledger.setdefault("party_seqs", {})
    ledger.setdefault("entries", [])
    return ledger


def save(ledger: dict, path: Path = PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    for entry in ledger["entries"]:
        entry.setdefault("connected_ids", [])
        entry.setdefault("pending_invites", [])
    path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")


def latest_for(ledger: dict, party_id: str) -> dict | None:
    return next(
        (e for e in reversed(ledger["entries"]) if e["party_id"] == party_id), None
    )


def party_ids_with_history(ledger: dict) -> list[str]:
    return sorted(ledger["party_seqs"])


def append_if_changed(ledger: dict, state: dict, mono_ms: int) -> bool:
    prior = latest_for(ledger, state["party_id"])
    if prior and state_key(prior) == state_key(state):
        return False
    seq = ledger["audit_seq"] + 1
    party_seq = ledger["party_seqs"].get(state["party_id"], 0) + 1
    entry = {
        **state,
        "seq": seq,
        "party_seq": party_seq,
        "staged_mono_ms": mono_ms,
        "sweep_epoch": ledger["sweep_epoch"],
        "prev_digest": ledger["chain_head"],
    }
    entry["entry_digest"] = digest(
        entry["prev_digest"],
        entry_line(seq, party_seq, mono_ms, ledger["sweep_epoch"], state),
    )
    ledger["entries"].append(entry)
    ledger["audit_seq"] = seq
    ledger["chain_head"] = entry["entry_digest"]
    ledger["party_seqs"][state["party_id"]] = party_seq
    if len(ledger["entries"]) > RETAINED:
        drop = len(ledger["entries"]) - RETAINED
        ledger["chain_base"] = ledger["entries"][drop - 1]["entry_digest"]
        ledger["entries"] = ledger["entries"][drop:]
    return True


def verify(ledger: dict) -> bool:
    if ledger.get("snapshot_version") != VERSION:
        return False
    entries = ledger["entries"]
    if not entries:
        return ledger["chain_base"] == GENESIS and ledger["chain_head"] == GENESIS
    prev = ledger["chain_base"]
    last = {}
    for index, entry in enumerate(entries):
        if entry["prev_digest"] != prev:
            return False
        state = {
            k: entry[k]
            for k in (
                "party_id",
                "leader_id",
                "status",
                "max_members",
                "connected_ids",
                "pending_invites",
            )
        }
        want = digest(
            prev,
            entry_line(
                entry["seq"],
                entry["party_seq"],
                entry["staged_mono_ms"],
                entry["sweep_epoch"],
                state,
            ),
        )
        if want != entry["entry_digest"] or (
            index and entry["seq"] != entries[index - 1]["seq"] + 1
        ):
            return False
        if entry["party_seq"] > ledger["party_seqs"].get(entry["party_id"], 0) or entry[
            "party_seq"
        ] <= last.get(entry["party_id"], 0):
            return False
        last[entry["party_id"]] = entry["party_seq"]
        prev = entry["entry_digest"]
    return ledger["chain_head"] == prev and ledger["audit_seq"] == entries[-1]["seq"]

"""Independent witness math for CT log Merkle consistency auditor."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def leaf_hash(leaf_input: str) -> bytes:
    return hashlib.sha256(b"\x00" + leaf_input.encode()).digest()


def node_hash(left: bytes, right: bytes) -> bytes:
    return hashlib.sha256(b"\x01" + left + right).digest()


def hx(blob: bytes) -> str:
    return blob.hex()


def verify_inclusion_math(leaf_input: str, root_hex: str, path: list[dict[str, str]]) -> bool:
    acc = leaf_hash(leaf_input)
    want = bytes.fromhex(root_hex)
    for step in path:
        sib = bytes.fromhex(step["hash"])
        if step["side"] == "right":
            acc = node_hash(acc, sib)
        else:
            acc = node_hash(sib, acc)
    return acc == want


def verify_consistency_ref(
    from_root_hex: str, to_root_hex: str, path: list[dict[str, str]]
) -> bool:
    acc = bytes.fromhex(from_root_hex)
    want = bytes.fromhex(to_root_hex)
    for step in path:
        sib = bytes.fromhex(step["hash"])
        if step["side"] == "right":
            acc = node_hash(acc, sib)
        else:
            acc = node_hash(sib, acc)
    return acc == want


def quorum_met_ref(log_id: str, tree_size: int, root_hash: str, checkpoints: list[dict]) -> bool:
    agree = 0
    for cp in checkpoints:
        if cp["log_id"] != log_id:
            continue
        if cp["tree_size"] == tree_size and cp["sha256_root_hash"].lower() == root_hash.lower():
            agree += 1
    return agree >= 2


def timestamps_monotonic_ref(older_ts: int, newer_ts: int, older_size: int, newer_size: int) -> bool:
    if newer_size <= older_size:
        return True
    return newer_ts > older_ts


def witness_set_hash_ref(log_id: str, tree_size: int, root_hash: str, checkpoints: list[dict]) -> str:
    ids = sorted(
        cp["witness_id"]
        for cp in checkpoints
        if cp["log_id"] == log_id
        and cp["tree_size"] == tree_size
        and cp["sha256_root_hash"].lower() == root_hash.lower()
    )
    joined = "|".join(ids)
    h: int = 0
    for b in joined.encode():
        h = (h * 131 + b) & 0xFFFFFFFFFFFFFFFF
    return f"{h:x}"


def load_bundles_from_index(index_path: Path) -> list[dict]:
    root = index_path.parent
    meta = json.loads(index_path.read_text(encoding="utf-8"))
    rows = []
    for entry in meta["entries"]:
        p = root / entry["bundle_file"]
        rows.append(json.loads(p.read_text(encoding="utf-8")))
    rows.sort(key=lambda r: r["log_id"])
    return rows


def independent_staging_rows(index_path: Path, witnesses_path: Path) -> list[dict]:
    checkpoints = json.loads(witnesses_path.read_text(encoding="utf-8"))["checkpoints"]
    rows = []
    for bundle in load_bundles_from_index(index_path):
        newer_root = bundle["newer_sth"]["sha256_root_hash"].lower()
        older_root = bundle["older_sth"]["sha256_root_hash"].lower()
        inclusion_ok = verify_inclusion_math(
            bundle["inclusion"]["leaf_input"],
            newer_root,
            bundle["inclusion"]["audit_path"],
        )
        consistency_ok = verify_consistency_ref(
            older_root,
            newer_root,
            bundle["consistency"]["audit_path"],
        )
        witness_quorum_ok = quorum_met_ref(
            bundle["log_id"],
            bundle["newer_sth"]["tree_size"],
            newer_root,
            checkpoints,
        )
        timestamp_monotonic_ok = timestamps_monotonic_ref(
            bundle["older_sth"]["timestamp"],
            bundle["newer_sth"]["timestamp"],
            bundle["older_sth"]["tree_size"],
            bundle["newer_sth"]["tree_size"],
        )
        wsh = witness_set_hash_ref(
            bundle["log_id"],
            bundle["newer_sth"]["tree_size"],
            newer_root,
            checkpoints,
        )
        rows.append(
            {
                "log_id": bundle["log_id"],
                "older_tree_size": bundle["older_sth"]["tree_size"],
                "newer_tree_size": bundle["newer_sth"]["tree_size"],
                "inclusion_ok": inclusion_ok,
                "consistency_ok": consistency_ok,
                "witness_quorum_ok": witness_quorum_ok,
                "timestamp_monotonic_ok": timestamp_monotonic_ok,
                "witness_set_hash": wsh,
            }
        )
    rows.sort(key=lambda r: r["log_id"])
    return rows


def seal_digest_ref(audits: list[dict]) -> str:
    parts = sorted(
        f"{a['log_id']}:{a['newer_tree_size']}:{str(a['inclusion_ok']).lower()}:{str(a['consistency_ok']).lower()}:{str(a['witness_quorum_ok']).lower()}"
        for a in audits
    )
    payload = ";".join(parts)
    return hashlib.sha256(payload.encode()).hexdigest()[:32]


def independent_sealed_bundle(index_path: Path, witnesses_path: Path) -> dict:
    staged = independent_staging_rows(index_path, witnesses_path)
    audits = [
        {
            "log_id": r["log_id"],
            "older_tree_size": r["older_tree_size"],
            "newer_tree_size": r["newer_tree_size"],
            "inclusion_ok": r["inclusion_ok"],
            "consistency_ok": r["consistency_ok"],
            "witness_quorum_ok": r["witness_quorum_ok"],
            "timestamp_monotonic_ok": r["timestamp_monotonic_ok"],
            "witness_set_hash": r["witness_set_hash"],
        }
        for r in staged
    ]
    witness_set_hash = audits[0]["witness_set_hash"] if audits else ""
    return {
        "version": 1,
        "audits": audits,
        "witness_set_hash": witness_set_hash,
        "bundle_digest": seal_digest_ref(audits),
    }

"""PyNaCl golden math for twctl witness bundles — independent of /app sources."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey


def tw1_message(
    release_id: str,
    artifact_digest: str,
    epoch: int,
    prior_witness_id: str | None,
) -> bytes:
    prior = prior_witness_id if prior_witness_id else "none"
    body = (
        f"TW1\n"
        f"artifact_digest={artifact_digest}\n"
        f"epoch={epoch}\n"
        f"prior_witness_id={prior}\n"
        f"release_id={release_id}\n"
    )
    return body.encode("utf-8")


def sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def key_revoked_at_epoch(keyid: str, revocations: list[dict], epoch: int) -> bool:
    return any(row["keyid"] == keyid and epoch >= int(row["revoked_epoch"]) for row in revocations)


def verify_ed25519_row(witness: dict, keys: dict[str, dict]) -> bool:
    key = keys.get(witness["signer_keyid"])
    if not key:
        return False
    msg = tw1_message(
        witness["release_id"],
        witness["artifact_digest"],
        int(witness["epoch"]),
        witness.get("prior_witness_id"),
    )
    try:
        VerifyKey(bytes.fromhex(key["public"])).verify(msg, bytes.fromhex(witness["signature"]))
        return True
    except BadSignatureError:
        return False


def provenance_chain_valid(all_witnesses: list[dict], witness: dict) -> bool:
    index = {w["witness_id"]: w for w in all_witnesses}
    prior = witness.get("prior_witness_id")
    if prior in (None, "none"):
        return True
    parent = index.get(prior)
    return bool(parent and int(parent["epoch"]) < int(witness["epoch"]))


def merge_witness_rows(existing: list[dict], incoming: list[dict]) -> tuple[list[dict], int]:
    out = list(existing)
    seen = {w["witness_id"] for w in out}
    skipped = 0
    for w in incoming:
        if w["witness_id"] in seen:
            skipped += 1
            continue
        out.append(w)
        seen.add(w["witness_id"])
    out.sort(key=lambda x: x["witness_id"])
    return out, skipped


def bundle_materialized(bundle_dir: Path) -> dict[str, Any]:
    policy = json.loads((bundle_dir / "policy.json").read_text(encoding="utf-8"))
    keys = json.loads((bundle_dir / "keys.json").read_text(encoding="utf-8"))
    revocations = []
    rev_path = bundle_dir / "revocations.jsonl"
    if rev_path.exists():
        for line in rev_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                revocations.append(json.loads(line))
    art = bundle_dir / policy["artifact_file"]
    digest = sha256_file(art)
    witnesses = []
    for path in sorted((bundle_dir / "witnesses").glob("*.json")):
        row = json.loads(path.read_text(encoding="utf-8"))
        row["artifact_digest"] = digest
        witnesses.append(row)
    witnesses.sort(key=lambda x: x["witness_id"])
    return {
        "policy": policy,
        "artifact_digest": digest,
        "keys": keys,
        "revocations": revocations,
        "witnesses": witnesses,
    }


def golden_stage_after_load(bundle_dir: Path, existing: dict | None = None) -> dict[str, Any]:
    bundle = bundle_materialized(bundle_dir)
    ingest_seq = 1 if existing is None else int(existing["ingest_seq"]) + 1
    prior = existing["witnesses"] if existing else []
    witnesses, replay_deduped = merge_witness_rows(prior, bundle["witnesses"])
    return {
        "ingest_seq": ingest_seq,
        "bundle_dir": str(bundle_dir),
        "policy": bundle["policy"],
        "artifact_digest": bundle["artifact_digest"],
        "keys": bundle["keys"],
        "revocations": bundle["revocations"],
        "witnesses": witnesses,
        "replay_deduped": replay_deduped,
    }


def golden_quorum_at_epoch(staging: dict[str, Any], epoch: int) -> dict[str, Any]:
    keys = staging["keys"]
    revocations = staging["revocations"]
    witnesses = staging["witnesses"]
    outcomes = []
    signers_seen: set[str] = set()
    valid = 0
    for w in witnesses:
        signature_ok = verify_ed25519_row(w, keys)
        provenance_ok = provenance_chain_valid(witnesses, w)
        revoked_signer = key_revoked_at_epoch(w["signer_keyid"], revocations, epoch)
        counts = signature_ok and provenance_ok and not revoked_signer
        outcomes.append(
            {
                "witness_id": w["witness_id"],
                "signature_ok": signature_ok,
                "provenance_ok": provenance_ok,
                "revoked_signer": revoked_signer,
                "counts_toward_quorum": counts,
            }
        )
        if counts and w["signer_keyid"] not in signers_seen:
            signers_seen.add(w["signer_keyid"])
            valid += 1
    threshold = int(staging["policy"]["quorum"]["threshold"])
    provenance_ok = all(provenance_chain_valid(witnesses, w) for w in witnesses)
    quorum_met = valid >= threshold and provenance_ok
    return {
        "epoch": epoch,
        "quorum_met": quorum_met,
        "valid_witness_count": valid,
        "threshold": threshold,
        "provenance_ok": provenance_ok,
        "replay_deduped": int(staging.get("replay_deduped", 0)),
        "witnesses": outcomes,
    }


def golden_ledger_digest(artifact_digest: str, rows: list[dict]) -> str:
    witness_blob = [
        {
            "witness_id": r["witness_id"],
            "signer_keyid": r["signer_keyid"],
            "epoch": r["epoch"],
            "prior_witness_id": r["prior_witness_id"],
            "counts_toward_quorum": r["counts_toward_quorum"],
        }
        for r in sorted(rows, key=lambda x: x["witness_id"])
    ]
    payload = {"artifact_digest": artifact_digest, "witnesses": witness_blob}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def golden_release_ledger(staging: dict[str, Any], verdict: dict[str, Any]) -> dict[str, Any]:
    rows = []
    for o in verdict["witnesses"]:
        w = next(x for x in staging["witnesses"] if x["witness_id"] == o["witness_id"])
        rows.append(
            {
                "witness_id": o["witness_id"],
                "signer_keyid": w["signer_keyid"],
                "epoch": w["epoch"],
                "prior_witness_id": w.get("prior_witness_id") or "none",
                "counts_toward_quorum": o["counts_toward_quorum"],
            }
        )
    rows.sort(key=lambda x: x["witness_id"])
    return {
        "release_id": staging["policy"]["release_id"],
        "artifact_digest": staging["artifact_digest"],
        "epoch": verdict["epoch"],
        "quorum_met": verdict["quorum_met"],
        "valid_witness_count": verdict["valid_witness_count"],
        "threshold": verdict["threshold"],
        "ingest_seq": staging["ingest_seq"],
        "witnesses": rows,
        "ledger_digest": golden_ledger_digest(staging["artifact_digest"], rows),
    }


def read_json_stage(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def biased_epoch(requested: int) -> int:
    bias = os.environ.get("TB3_EPOCH_BIAS")
    return requested + int(bias) if bias is not None else requested


# Independent-reference aliases (first-submit F-prime record)
reference_verify = golden_quorum_at_epoch
reference_ledger = golden_release_ledger
reference_staging = golden_stage_after_load
load_staging = read_json_stage

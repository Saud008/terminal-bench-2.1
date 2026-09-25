"""Contract tests for authData and chain helpers."""
from __future__ import annotations

import json
from pathlib import Path

from attest_verifier_math import chain_valid, parse_auth_data

FIX = Path("/app/registry/transcript-bundles")


def test_auth_data_uv_bit_contract() -> None:
    """Verify reference authData parser reads UV from flag bit 0x04 per cbor-attestation-layout.md."""
    bundle = json.loads((FIX / "uv-required-trap.json").read_text(encoding="utf-8"))
    tr = bundle["transcripts"][0]
    uv, sign_count, aaguid = parse_auth_data(tr["auth_data_hex"])
    assert uv is False
    assert sign_count == 1
    assert len(aaguid) == 36


def test_chain_valid_leaf_to_root() -> None:
    """Verify valid leaf-to-root fingerprint linkage passes chain validation."""
    bundle = json.loads((FIX / "enterprise-trust.json").read_text(encoding="utf-8"))
    assert chain_valid(bundle["transcripts"][0]["cert_chain"]) is True


def test_chain_invalid_detected() -> None:
    """Verify broken issuer to subject linkage fails chain validation."""
    bundle = json.loads((FIX / "broken-chain.json").read_text(encoding="utf-8"))
    assert chain_valid(bundle["transcripts"][0]["cert_chain"]) is False


def test_decisions_sorted_by_trust_rank_then_credential_id() -> None:
    """Verify decisions sort by trust rank then credential_id per trust-decision-fields.md."""
    from attest_cli_helpers import run_pipeline, wipe

    wipe()
    out = run_pipeline("batch-alpha", "enterprise-trust", "enterprise-strict")
    got = json.loads(out.read_text(encoding="utf-8"))
    ranks = [{"rejected": 0, "untrusted": 1, "trusted": 2}[d["trust_level"]] for d in got["decisions"]]
    pairs = list(zip(ranks, [d["credential_id"] for d in got["decisions"]], strict=True))
    assert pairs == sorted(pairs)

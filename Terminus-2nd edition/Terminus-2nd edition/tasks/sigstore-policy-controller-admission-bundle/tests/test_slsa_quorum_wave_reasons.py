"""Quorum wave reasons, witness bind, and alternate-seed seal consistency."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import slsacip_harness as harness

WAVES = {
    "north": "/app/fixtures/pull-waves/wave-north.jsonl",
    "east": "/app/fixtures/pull-waves/wave-east.jsonl",
    "south": "/app/fixtures/pull-waves/wave-south.jsonl",
}

EXPECTED_REASONS = {
    "alpha-ok": ("admit_verified", ["env-acme-a1", "env-acme-a2"]),
    "alpha-pin": ("digest_deny", []),
    "alpha-revoke": ("revocation_hit", []),
    "alpha-fed": ("admit_verified", ["env-fed-d1", "env-fed-d2"]),
    "alpha-quorum": ("quorum_fail", []),
    "alpha-builder": ("builder_deny", []),
    "alpha-pred": ("predicate_reject", []),
    "beta-revoke-edge": ("trust_unbind", []),
    "beta-untrusted-only": ("trust_unbind", []),
    "beta-gamma-pin": ("digest_deny", []),
}


def _results_by_id(report):
    return {r["request_id"]: r for r in report["results"]}


def test_pull_waves_match_reference_exactly():
    """Each pull-wave ledger must equal independent verifier math."""
    for name, pulls_path in WAVES.items():
        harness.reset_state()
        report = harness.run_attest(pulls_path)
        reference = harness.reference_report(pulls_path)
        assert report == reference, f"wave-{name} diverges from reference"


def test_policy_gate_reasons_match_quorum_contract():
    """Per-request deny/allow reasons must match quorum-n-of-m terminal precedence."""
    combined = {}
    for pulls_path in WAVES.values():
        harness.reset_state()
        report = harness.run_attest(pulls_path)
        combined.update(_results_by_id(report))

    for request_id, (reason, ids) in EXPECTED_REASONS.items():
        assert request_id in combined, f"missing result for {request_id}"
        result = combined[request_id]
        assert result["reason"] == reason, (
            f"{request_id}: expected reason {reason!r}, got {result['reason']!r}"
        )
        assert result["envelope_ids"] == ids, (
            f"{request_id}: expected envelope_ids {ids}, got {result['envelope_ids']}"
        )


def test_trust_witness_path_binds_to_ledger_fingerprints():
    """Staged /app/state/slsacip/trust-witness.json fingerprints must match the ledger."""
    harness.reset_state()
    report = harness.run_attest(WAVES["north"])
    assert harness.WITNESS_PATH.exists()
    snap = harness.read_witness_snapshot()
    assert snap["seed"] == report["seed"]
    assert snap["quorum_k"] == report["quorum_k"]
    assert snap["policy_packs"] == report["policy_packs"]
    assert snap["trust_fingerprint"] == report["trust_fingerprint"]
    assert snap["deny_fingerprint"] == report["deny_fingerprint"]
    assert snap["revoke_fingerprint"] == report["revoke_fingerprint"]
    assert snap["predicate_fingerprint"] == report["predicate_fingerprint"]
    assert snap["builder_fingerprint"] == report["builder_fingerprint"]


def test_audit_digest_seal_matches_reference():
    """Ledger audit_digest must reseal identically to independent reference math."""
    harness.reset_state()
    report = harness.run_attest(WAVES["north"])
    reference = harness.reference_report(WAVES["north"])
    assert report["audit_digest"] == reference["audit_digest"]


def test_alternate_seed_changes_witness_packs_with_reference():
    """A different seed must reshuffle cip-tiers and still match reference seals."""
    with open(harness.CONFIG_PATH, "r", encoding="utf-8") as f:
        base_cfg = json.load(f)

    alt_cfg = dict(base_cfg)
    alt_cfg["seed"] = "slsacip-cluster-seed-alternate-v9"
    assert alt_cfg["seed"] != base_cfg["seed"]

    with tempfile.TemporaryDirectory() as td:
        alt_path = Path(td) / "slsacip-alt.json"
        alt_path.write_text(json.dumps(alt_cfg), encoding="utf-8")

        harness.reset_state()
        report = harness.run_attest(WAVES["north"], config=str(alt_path))
        reference = harness.reference_report(WAVES["north"], config_path=str(alt_path))

        assert report == reference
        assert report["seed"] == alt_cfg["seed"]
        harness.reset_state()
        base_report = harness.run_attest(WAVES["north"])
        assert report["policy_packs"] != base_report["policy_packs"]

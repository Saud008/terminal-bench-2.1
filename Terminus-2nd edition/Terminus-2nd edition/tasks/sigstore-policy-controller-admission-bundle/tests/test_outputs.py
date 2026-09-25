"""G-026: wave-north sealed ledger vs independent reference."""

from __future__ import annotations

from pathlib import Path

import slsacip_harness as harness

WAVE_NORTH = "/app/fixtures/pull-waves/wave-north.jsonl"
LEDGER_PATH = "/app/output/slsa-admission-ledger.json"
WITNESS_PATH = "/app/state/slsacip/trust-witness.json"


def test_attestation_seal_binds_wave_north_ledger_to_reference():
    """Sealed ledger at /app/output/slsa-admission-ledger.json must match reference attest math."""
    harness.reset_state()
    report = harness.run_attest(WAVE_NORTH, output=LEDGER_PATH)
    reference = harness.reference_report(WAVE_NORTH)
    assert Path(LEDGER_PATH).is_file()
    assert report == reference
    assert len(report["results"]) == 7


def test_witness_snapshot_digest_matches_report_fingerprints():
    """Witness at /app/state/slsacip/trust-witness.json must bind trust/deny/revoke seals to the ledger."""
    harness.reset_state()
    report = harness.run_attest(WAVE_NORTH, output=LEDGER_PATH)
    assert Path(WITNESS_PATH).is_file()
    snap = harness.read_witness_snapshot()
    assert snap["policy_packs"] == report["policy_packs"]
    assert snap["trust_fingerprint"] == report["trust_fingerprint"]
    assert snap["deny_fingerprint"] == report["deny_fingerprint"]
    assert snap["revoke_fingerprint"] == report["revoke_fingerprint"]
    assert report["audit_digest"] == harness.reference_report(WAVE_NORTH)["audit_digest"]

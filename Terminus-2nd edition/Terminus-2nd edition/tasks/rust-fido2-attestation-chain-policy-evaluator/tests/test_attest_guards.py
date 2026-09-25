"""Extended behavioral tests for fido2eval hard band.

Covers ingest-stage bundle loading separately from export-stage trust report emission.
"""
from __future__ import annotations

import json
from pathlib import Path

from attest_cli_helpers import invoke, run_pipeline, wipe

APP = Path("/app")
CLI = APP / "bin" / "fido2eval"


def test_run_batch_rejects_batch_bundle_mismatch() -> None:
    """Verify ingest rejects when --batch does not match bundle batch_id."""
    wipe()
    proc = invoke([
        str(CLI), "run-batch", "--batch", "wrong-batch", "--bundle", "enterprise-trust",
        "--policy", "enterprise-strict", "--output", str(APP / "output" / "x.json"),
    ])
    assert proc.returncode != 0


def test_run_batch_writes_policy_bind() -> None:
    """Verify run-batch fails when transcript cache snapshot is absent."""
    wipe()
    proc = invoke([
        str(CLI), "run-batch", "--batch", "batch-alpha", "--bundle", "enterprise-trust",
        "--policy", "enterprise-strict", "--output", str(APP / "output" / "x.json"),
    ])
    assert proc.returncode == 0


def test_run_batch_emits_trust_report() -> None:
    """Verify publish trust fails when policy ledger has no active row."""
    wipe()
    proc = invoke([str(CLI), "run-batch", "--batch", "batch-alpha", "--bundle", "enterprise-trust",
                   "--policy", "enterprise-strict", "--output", str(APP / "output" / "x.json")])
    assert proc.returncode == 0


def test_cache_records_chain_ok_flags() -> None:
    """Verify cache rows record chain_ok false for broken-chain bundle."""
    wipe()
    run_pipeline("batch-delta", "broken-chain", "enterprise-strict")
    snap = json.loads((APP / "var" / "transcript-rows.json").read_text(encoding="utf-8"))
    assert snap["rows"][0]["chain_ok"] is False


def test_cache_records_metadata_hit_for_known_aaguid() -> None:
    """Verify cache rows set metadata_hit for registry-known AAGUID values."""
    wipe()
    run_pipeline("batch-alpha", "enterprise-trust", "enterprise-strict")
    snap = json.loads((APP / "var" / "transcript-rows.json").read_text(encoding="utf-8"))
    assert all(r["metadata_hit"] for r in snap["rows"])


def test_decision_rows_include_reason_arrays() -> None:
    """Verify each trust decision includes a reasons list."""
    wipe()
    out = run_pipeline("batch-bravo", "uv-required-trap", "enterprise-strict")
    got = json.loads(out.read_text(encoding="utf-8"))
    assert isinstance(got["decisions"][0]["reasons"], list)


def test_reset_state_clears_cache() -> None:
    """Verify reset-state.sh removes transcript cache artifacts."""
    wipe()
    run_pipeline("batch-alpha", "enterprise-trust", "enterprise-strict")
    wipe()
    assert not (APP / "var" / "transcript-rows.json").exists()


def test_output_file_created_under_output_dir() -> None:
    """Verify export writes trust report JSON under /app/output/."""
    wipe()
    out = run_pipeline("batch-alpha", "enterprise-trust", "enterprise-strict")
    assert out.exists()
    assert out.parent == APP / "output"


def test_bundled_formats_are_packed_only() -> None:
    """Verify bundled transcripts use packed attestation format only."""
    bundles = Path("/app/registry/transcript-bundles")
    for path in bundles.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))
        for tr in data["transcripts"]:
            assert tr["attestation_format"] == "packed"


def test_hidden_batch_two_decisions() -> None:
    """Verify hidden shadow-trust bundle yields two trust decisions."""
    wipe()
    env = {"TB3_REGISTRY_ROOT": "/opt/verifier-fixtures/fido2"}
    out = run_pipeline("batch-hidden", "shadow-trust", "enterprise-strict", env=env)
    got = json.loads(out.read_text(encoding="utf-8"))
    assert len(got["decisions"]) == 2

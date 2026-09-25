"""Primary verifier tests for fido2eval."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

from attest_cli_helpers import run_pipeline, wipe
from attest_verifier_math import reference_trust_report

APP = Path("/app")
FIX = APP / "registry"


def test_fido2eval_binary_installed_for_subprocess_cli() -> None:
    """Verify fido2eval binary exists for subprocess CLI invocation."""
    subprocess.run(["test", "-x", str(APP / "bin" / "fido2eval")], check=True)


def test_enterprise_trust_publish_matches_contract() -> None:
    """Verify published trust decisions match independent verifier math for enterprise-trust."""
    wipe()
    out = run_pipeline("batch-alpha", "enterprise-trust", "enterprise-strict")
    got = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_trust_report(
        "batch-alpha",
        FIX / "transcript-bundles" / "enterprise-trust.json",
        FIX / "policies" / "enterprise-strict.json",
        FIX / "authenticators" / "aaguid-registry.json",
    )
    assert got["summary"] == ref["summary"]
    assert got["decisions"] == ref["decisions"]
    assert got["audit_digest"] == ref["audit_digest"]


def test_uv_required_trap_rejects_missing_uv() -> None:
    """Verify required user verification policy rejects transcripts with UV flag unset."""
    wipe()
    out = run_pipeline("batch-bravo", "uv-required-trap", "enterprise-strict")
    got = json.loads(out.read_text(encoding="utf-8"))
    assert got["summary"]["rejected"] == 1
    assert got["decisions"][0]["reasons"] == ["uv_policy"]


def test_duplicate_credential_batch_blocks_second_row() -> None:
    """Verify batch-wide duplicate credential identifiers increment dedupe_blocked per credential-dedupe-contract.md."""
    wipe()
    out = run_pipeline("batch-charlie", "duplicate-credential-batch", "enterprise-strict")
    got = json.loads(out.read_text(encoding="utf-8"))
    assert got["summary"]["dedupe_blocked"] == 1
    assert got["summary"]["rejected"] >= 1


def test_broken_chain_rejected() -> None:
    """Verify invalid certificate chain linkage yields chain_invalid rejection."""
    wipe()
    out = run_pipeline("batch-delta", "broken-chain", "enterprise-strict")
    got = json.loads(out.read_text(encoding="utf-8"))
    assert got["summary"]["rejected"] == 1
    assert "chain_invalid" in got["decisions"][0]["reasons"]


def test_cache_run_seq_increments_on_rerun() -> None:
    """Verify run_seq monotonicity in /app/var/transcript-rows.json across re-run."""
    wipe()
    run_pipeline("batch-alpha", "enterprise-trust", "enterprise-strict")
    snap1 = json.loads((APP / "var" / "transcript-rows.json").read_text(encoding="utf-8"))
    run_pipeline("batch-alpha", "enterprise-trust", "enterprise-strict")
    snap2 = json.loads((APP / "var" / "transcript-rows.json").read_text(encoding="utf-8"))
    assert snap2["run_seq"] > snap1["run_seq"]


def test_policy_bind_seq_matches_run_seq() -> None:
    """Verify /app/var/policy-bind.json bind_seq equals transcript cache run_seq."""
    wipe()
    run_pipeline("batch-alpha", "enterprise-trust", "enterprise-strict")
    snap = json.loads((APP / "var" / "transcript-rows.json").read_text(encoding="utf-8"))
    ledger = json.loads((APP / "var" / "policy-bind.json").read_text(encoding="utf-8"))
    assert snap["run_seq"] >= 1
    assert ledger["active"]["bind_seq"] == snap["run_seq"]


def test_enterprise_trust_two_trusted_decisions() -> None:
    """Verify enterprise-trust bundle yields two trusted decisions under enterprise-strict policy."""
    wipe()
    out = run_pipeline("batch-alpha", "enterprise-trust", "enterprise-strict")
    got = json.loads(out.read_text(encoding="utf-8"))
    assert got["summary"]["trusted"] == 2


def test_report_includes_policy_name() -> None:
    """Verify trust report records the active policy name from policy ledger."""
    wipe()
    out = run_pipeline("batch-alpha", "enterprise-trust", "enterprise-strict")
    got = json.loads(out.read_text(encoding="utf-8"))
    assert got["policy_name"] == "enterprise-strict"


def test_cache_rows_preserve_sign_count_from_auth_data() -> None:
    """Verify cache rows store sign_count parsed from authData not transcript fields."""
    wipe()
    run_pipeline("batch-alpha", "enterprise-trust", "enterprise-strict")
    snap = json.loads((APP / "var" / "transcript-rows.json").read_text(encoding="utf-8"))
    counts = sorted(r["sign_count"] for r in snap["rows"])
    assert counts == [1, 2]


def test_audit_digest_present_and_hex() -> None:
    """Verify trust report includes 64-char audit_digest per trust-decision-fields.md."""
    wipe()
    out = run_pipeline("batch-alpha", "enterprise-trust", "enterprise-strict")
    got = json.loads(out.read_text(encoding="utf-8"))
    assert len(got["audit_digest"]) == 64


def test_duplicate_credential_first_row_trusted_second_rejected() -> None:
    """Verify only the second duplicate credential row is rejected while first stays trusted."""
    wipe()
    out = run_pipeline("batch-charlie", "duplicate-credential-batch", "enterprise-strict")
    got = json.loads(out.read_text(encoding="utf-8"))
    levels = [d["trust_level"] for d in got["decisions"]]
    assert levels.count("trusted") == 1
    assert levels.count("rejected") == 1


def test_transcript_cache_path_written() -> None:
    """Verify run-batch writes /app/var/transcript-rows.json as named in instruction."""
    wipe()
    run_pipeline("batch-alpha", "enterprise-trust", "enterprise-strict")
    assert (APP / "var" / "transcript-rows.json").is_file()


def test_policy_bind_path_written() -> None:
    """Verify run-batch writes /app/var/policy-bind.json as named in instruction."""
    wipe()
    run_pipeline("batch-alpha", "enterprise-trust", "enterprise-strict")
    assert (APP / "var" / "policy-bind.json").is_file()

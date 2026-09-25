"""oidcgov — transcript staging, cache hydration, governance export pipeline."""

from __future__ import annotations

import json

import pytest

from oidc_verdict_refmath import reference_governance_report, reference_transcript_digest
from governor_cli_harness import (
    BUNDLED_SCENARIOS,
    OIDCGOV_BIN,
    OIDCGOV_CACHE,
    OIDCGOV_FIXTURES,
    OIDCGOV_REPORT,
    OIDCGOV_REV,
    OIDCGOV_STAGE,
    oidcgov_cli,
    oidcgov_reset_workspace,
    read_json,
    run_oidcgov_pipeline,
)


def test_oidc_smoke_load_transcript_writes_staging_path() -> None:
    """Verify load-transcript writes /app/state/transcript-vault.json per transcript-vault-contract.md."""
    oidcgov_reset_workspace()
    proc = oidcgov_cli(
        [OIDCGOV_BIN, "load-transcript", "--scenario", "kid-casefold-lookup", "--fixture-dir", str(OIDCGOV_FIXTURES)]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert OIDCGOV_STAGE.is_file()


@pytest.mark.parametrize("scenario_id", BUNDLED_SCENARIOS)
def test_oidc_ob01_transcript_digest_matches_refmath(scenario_id: str) -> None:
    """Verify transcript_digest matches independent reference math for each bundled scenario."""
    oidcgov_reset_workspace()
    proc = oidcgov_cli(
        [OIDCGOV_BIN, "load-transcript", "--scenario", scenario_id, "--fixture-dir", str(OIDCGOV_FIXTURES)]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    body = json.loads(OIDCGOV_STAGE.read_text(encoding="utf-8"))
    ref_digest = reference_transcript_digest(scenario_id, OIDCGOV_FIXTURES)
    assert body["transcript_digest"] == ref_digest


def test_oidc_ob02_kid_casefold_accepts_active_key() -> None:
    """Verify case-insensitive kid lookup accepts active_key verdict per kid-lookup-contract.md."""
    oidcgov_reset_workspace()
    run_oidcgov_pipeline("kid-casefold-lookup")
    report = read_json(OIDCGOV_REPORT)
    dec = {d["token_id"]: d for d in report["decisions"]}
    assert dec["t1"]["verdict"] == "accept"
    assert dec["t1"]["reason_code"] == "active_key"


def test_oidc_ob03_issuer_audience_rejects_partial_aud_match() -> None:
    """Verify audience binding rejects tokens when any aud value is missing from policy per issuer-audience-contract.md."""
    oidcgov_reset_workspace()
    run_oidcgov_pipeline("issuer-audience-bind")
    report = read_json(OIDCGOV_REPORT)
    dec = {d["token_id"]: d for d in report["decisions"]}
    assert dec["good"]["verdict"] == "accept"
    assert dec["bad-aud"]["verdict"] == "reject"
    assert dec["bad-aud"]["reason_code"] == "audience_mismatch"


def test_oidc_ob04_cache_max_age_rejects_stale_signature_epoch() -> None:
    """Verify cache max-age in seconds rejects stale signatures per cache-max-age-contract.md."""
    oidcgov_reset_workspace()
    run_oidcgov_pipeline("cache-max-age-expiry")
    report = read_json(OIDCGOV_REPORT)
    dec = {d["token_id"]: d for d in report["decisions"]}
    assert dec["fresh"]["verdict"] == "accept"
    assert dec["stale"]["verdict"] == "reject"
    assert dec["stale"]["reason_code"] == "cache_stale"


def test_oidc_ob05_grace_accepts_retired_kid_in_window() -> None:
    """Verify stale-key grace window accepts retired kids within inclusive bounds per grace-window-contract.md."""
    oidcgov_reset_workspace()
    run_oidcgov_pipeline("stale-key-grace-window")
    report = read_json(OIDCGOV_REPORT)
    dec = {d["token_id"]: d for d in report["decisions"]}
    assert dec["in-grace"]["verdict"] == "accept"
    assert dec["in-grace"]["reason_code"] == "grace_key"
    assert dec["past-grace"]["verdict"] == "reject"


def test_oidc_ob06_revoked_key_rejects_even_if_active_before() -> None:
    """Verify revoked keys reject with key_revoked regardless of prior active status per revoked-key-contract.md."""
    oidcgov_reset_workspace()
    run_oidcgov_pipeline("revoked-key-reject")
    report = read_json(OIDCGOV_REPORT)
    dec = {d["token_id"]: d for d in report["decisions"]}
    assert dec["revoked"]["verdict"] == "reject"
    assert dec["revoked"]["reason_code"] == "key_revoked"


def test_oidc_ob07_rollover_timeline_applies_final_active_kid() -> None:
    """Verify ascending timeline replay exposes post-rollover active kid per transcript-vault-contract.md."""
    oidcgov_reset_workspace()
    run_oidcgov_pipeline("rollover-timeline-order")
    report = read_json(OIDCGOV_REPORT)
    dec = {d["token_id"]: d for d in report["decisions"]}
    assert dec["uses-b"]["verdict"] == "accept"


def test_oidc_ob08_hydrate_cache_increments_revision() -> None:
    """Verify hydrate-cache increments hydrate_revision in /app/state/hydrate-revision.json."""
    oidcgov_reset_workspace()
    oidcgov_cli([OIDCGOV_BIN, "load-transcript", "--scenario", "stable-decision-batch", "--fixture-dir", str(OIDCGOV_FIXTURES)])
    oidcgov_cli([OIDCGOV_BIN, "hydrate-cache", "--scenario", "stable-decision-batch"])
    rev = read_json(OIDCGOV_REV)
    assert rev["hydrate_revision"] >= 1


def test_oidc_ob08b_hydrate_writes_jwks_cache_snapshot() -> None:
    """Verify hydrate-cache writes /app/state/jwks-cache-snapshot.json with active keys."""
    oidcgov_reset_workspace()
    oidcgov_cli([OIDCGOV_BIN, "load-transcript", "--scenario", "kid-casefold-lookup", "--fixture-dir", str(OIDCGOV_FIXTURES)])
    oidcgov_cli([OIDCGOV_BIN, "hydrate-cache", "--scenario", "kid-casefold-lookup"])
    assert OIDCGOV_CACHE.is_file()
    snap = read_json(OIDCGOV_CACHE)
    assert snap["active_keys"]


def test_oidc_ob08d_decide_batch_writes_verification_decisions_json() -> None:
    """Verify decide-batch writes /app/state/verification-decisions.json for the scenario."""
    oidcgov_reset_workspace()
    oidcgov_cli([OIDCGOV_BIN, "load-transcript", "--scenario", "stable-decision-batch", "--fixture-dir", str(OIDCGOV_FIXTURES)])
    oidcgov_cli([OIDCGOV_BIN, "hydrate-cache", "--scenario", "stable-decision-batch"])
    oidcgov_cli([OIDCGOV_BIN, "decide-batch", "--scenario", "stable-decision-batch"])
    from governor_cli_harness import OIDCGOV_DEC

    assert OIDCGOV_DEC.is_file()


def test_oidc_ob08c_emit_writes_verification_governance_report() -> None:
    """Verify emit-report writes /app/output/verification-governance-report.json after hydration."""
    oidcgov_reset_workspace()
    run_oidcgov_pipeline("stable-decision-batch")
    assert OIDCGOV_REPORT.is_file()
    body = read_json(OIDCGOV_REPORT)
    assert body["scenario"] == "stable-decision-batch"
    assert body["decisions"]


@pytest.mark.parametrize("scenario_id", ("stable-decision-batch", "repeat-governance-report", "issuer-audience-bind"))
def test_oidc_ob09_governance_report_matches_refmath(scenario_id: str) -> None:
    """Verify verification-governance-report.json decisions and report_digest match reference math."""
    oidcgov_reset_workspace()
    run_oidcgov_pipeline(scenario_id)
    body = read_json(OIDCGOV_REPORT)
    ref = reference_governance_report(scenario_id, OIDCGOV_FIXTURES)
    assert body["decisions"] == ref["decisions"]
    assert body["report_digest"] == ref["report_digest"]


def test_oidc_ob10_ingest_only_transcript_blocks_export() -> None:
    """Verify ingest-only load-transcript without hydrate blocks emit-report export per governance-report-contract.md."""
    oidcgov_reset_workspace()
    oidcgov_cli([OIDCGOV_BIN, "load-transcript", "--scenario", "stable-decision-batch", "--fixture-dir", str(OIDCGOV_FIXTURES)])
    proc = oidcgov_cli([OIDCGOV_BIN, "emit-report", "--scenario", "stable-decision-batch"])
    assert proc.returncode != 0


def test_oidc_ob11_repeat_report_bytes_on_second_emit() -> None:
    """Verify second emit-report produces byte-identical report per repeat-export-contract.md."""
    oidcgov_reset_workspace()
    run_oidcgov_pipeline("repeat-governance-report")
    first = OIDCGOV_REPORT.read_bytes()
    proc = oidcgov_cli([OIDCGOV_BIN, "emit-report", "--scenario", "repeat-governance-report"])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert OIDCGOV_REPORT.read_bytes() == first


def test_oidc_ob12_decisions_sorted_by_token_id_ascending() -> None:
    """Verify governance report decisions sort by token_id ascending per governance-report-contract.md."""
    oidcgov_reset_workspace()
    run_oidcgov_pipeline("stable-decision-batch")
    report = read_json(OIDCGOV_REPORT)
    ids = [d["token_id"] for d in report["decisions"]]
    assert ids == sorted(ids)


def test_oidc_ob13_subprocess_cli_invokes_oidcgov_binary() -> None:
    """Verify pytest drives /app/bin/oidcgov via subprocess per cli-surface.md."""
    oidcgov_reset_workspace()
    proc = oidcgov_cli([OIDCGOV_BIN, "load-transcript", "--scenario", "kid-casefold-lookup", "--fixture-dir", str(OIDCGOV_FIXTURES)])
    assert OIDCGOV_BIN in proc.args[0]
    assert proc.returncode == 0

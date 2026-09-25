"""Behavioral verifier for sshap OpenSSH principals attestor."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from sshap_verifier_oracle import (
    emit_principals_attestation,
    build_trust_ledger,
    decide_probe,
    reference_pipeline,
    resolve_match_scope,
)

APP = Path("/app")
CLI = Path("/usr/local/bin/sshap")
LEDGER = APP / "state" / "trust_ledger.json"
ATTESTATION = APP / "output" / "principals_attestation_bundle.json"
PRINCIPALS = APP / "fixtures" / "principals"
CAS = APP / "fixtures" / "cas"
KRL = APP / "fixtures" / "krl" / "revoked.krl"
MATCH = APP / "fixtures" / "match"
PROBES = APP / "fixtures" / "probes" / "sessions.json"
HIDDEN = Path("/opt/verifier-fixtures/ssh_hidden")


def _run(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=False, capture_output=True, text=True, cwd=str(APP), **kw)


def reset_state() -> None:
    proc = _run(["bash", str(APP / "scripts" / "reset-state.sh")])
    assert proc.returncode == 0, proc.stderr


def rebuild() -> None:
    proc = _run(["bash", str(APP / "scripts" / "rebuild-sshap.sh")])
    assert proc.returncode == 0, proc.stderr


def match_dir() -> Path:
    tb3 = os.environ.get("TB3_MATCH_DIR")
    return Path(tb3) if tb3 else MATCH


def probes_file() -> Path:
    tb3 = os.environ.get("TB3_PROBES_FILE")
    return Path(tb3) if tb3 else PROBES


def run_ingest(ledger: Path = LEDGER) -> subprocess.CompletedProcess:
    return _run(
        [
            str(CLI),
            "ingest",
            "--principals-dir",
            str(PRINCIPALS),
            "--ca-dir",
            str(CAS),
            "--krl",
            str(KRL),
            "--ledger",
            str(ledger),
        ]
    )


def run_attest(
    ledger: Path = LEDGER,
    out: Path = ATTESTATION,
    match: Path | None = None,
    probes: Path | None = None,
) -> subprocess.CompletedProcess:
    return _run(
        [
            str(CLI),
            "attest",
            "--ledger",
            str(ledger),
            "--match-dir",
            str(match or match_dir()),
            "--probes",
            str(probes or probes_file()),
            "--out",
            str(out),
        ]
    )


def run_pipeline() -> None:
    reset_state()
    rebuild()
    ing = run_ingest()
    assert ing.returncode == 0, ing.stderr
    exp = run_attest()
    assert exp.returncode == 0, exp.stderr


@pytest.fixture(autouse=True)
def _clean_env():
    reset_state()
    rebuild()
    os.environ.pop("TB3_MATCH_DIR", None)
    os.environ.pop("TB3_PROBES_FILE", None)
    yield
    os.environ.pop("TB3_MATCH_DIR", None)
    os.environ.pop("TB3_PROBES_FILE", None)


def test_cli_exists():
    """Instruction requires /app/scripts/sshap installed as /usr/local/bin/sshap for subprocess verification."""
    assert CLI.is_file()


def test_ingest_writes_trust_ledger_json():
    """Ingest must materialize /app/state/trust_ledger.json with principals and cas arrays."""
    proc = run_ingest()
    assert proc.returncode == 0, proc.stderr
    assert LEDGER.is_file()
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    assert len(data["principals"]) >= 6


def test_ledger_fingerprint_matches_reference():
    """Trust ledger ledger_fingerprint must follow trust_ledger_workflow digest rules."""
    run_ingest()
    got = json.loads(LEDGER.read_text(encoding="utf-8"))
    ref = build_trust_ledger(PRINCIPALS, CAS, KRL)
    assert got["ledger_fingerprint"] == ref["ledger_fingerprint"]


def test_attest_writes_principals_attestation_bundle():
    """Attest must write /app/output/principals_attestation_bundle.json with schema_version and session_bindings."""
    run_ingest()
    proc = run_attest()
    assert proc.returncode == 0, proc.stderr
    assert ATTESTATION.is_file()


def test_full_pipeline_bundle_seal_reference():
    """End-to-end ingest and attest bundle_seal must match the independent reference oracle."""
    run_ingest()
    run_attest()
    got = json.loads(ATTESTATION.read_text(encoding="utf-8"))
    _, ref_attestation = reference_pipeline(PRINCIPALS, CAS, KRL, MATCH, PROBES)
    assert got["bundle_seal"] == ref_attestation["bundle_seal"]


def test_bindings_sorted_by_probe_id():
    """Session bindings must be sorted by probe_id as defined in trust_ledger_workflow.md."""
    run_pipeline()
    ids = [d["probe_id"] for d in json.loads(ATTESTATION.read_text())["session_bindings"]]
    assert ids == sorted(ids)


def test_ops_allow_verdict():
    """Signed ops principal with matching infra-ca-01 ca_id must receive allow verdict."""
    run_pipeline()
    dec = {d["probe_id"]: d for d in json.loads(ATTESTATION.read_text())["session_bindings"]}
    assert dec["p_ops_allow"]["verdict"] == "allow"


def test_guest_deny_exclamation_principal():
    """Deploy scope deny line for guest principal must deny via principal_match reason."""
    run_pipeline()
    dec = {d["probe_id"]: d for d in json.loads(ATTESTATION.read_text())["session_bindings"]}
    assert dec["p_guest_deny"]["verdict"] == "deny"
    assert dec["p_guest_deny"]["reason"] == "principal_match"


def test_revoked_before_allow():
    """Revoked fingerprints in KRL must deny with reason revoked before principal matching."""
    run_pipeline()
    dec = {d["probe_id"]: d for d in json.loads(ATTESTATION.read_text())["session_bindings"]}
    assert dec["p_revoked"]["verdict"] == "deny"
    assert dec["p_revoked"]["reason"] == "revoked"


def test_ca_scope_denies_contractor_on_infra_ca():
    """infra-ca-01 ca_id must reject contractor principal per cert_authority_scope.md."""
    run_pipeline()
    dec = {d["probe_id"]: d for d in json.loads(ATTESTATION.read_text())["session_bindings"]}
    assert dec["p_ca_scope_deny"]["reason"] == "ca_scope"


def test_wildcard_namespace_allow():
    """Namespace wildcard *@corp.example.com must allow alice@corp.example.com."""
    run_pipeline()
    dec = {d["probe_id"]: d for d in json.loads(ATTESTATION.read_text())["session_bindings"]}
    assert dec["p_wildcard_allow"]["verdict"] == "allow"


def test_global_fallback_contractor():
    """Unscoped sessions must fall back to global principals file for contractor allow."""
    run_pipeline()
    dec = {d["probe_id"]: d for d in json.loads(ATTESTATION.read_text())["session_bindings"]}
    assert dec["p_global_fallback"]["verdict"] == "allow"
    assert dec["p_global_fallback"]["scope_id"] == "global"


def test_staging_match_scope_release():
    """Match block for staging hosts must select staging scope and allow release principal."""
    run_pipeline()
    dec = {d["probe_id"]: d for d in json.loads(ATTESTATION.read_text())["session_bindings"]}
    assert dec["p_staging_release"]["scope_id"] == "staging"
    assert dec["p_staging_release"]["verdict"] == "allow"


def test_wildcard_bad_token_denied():
    """Embedded asterisk principals such as bad*token must yield wildcard_denied."""
    run_pipeline()
    dec = {d["probe_id"]: d for d in json.loads(ATTESTATION.read_text())["session_bindings"]}
    assert dec["p_wildcard_bad"]["reason"] == "wildcard_denied"


def test_scoped_probe_ignores_global_contractor():
    """Non-global Match scope must exclude global.principals contractor allow per precedence doc."""
    run_pipeline()
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    probe = {
        "probe_id": "local_scoped",
        "user": "ops",
        "host": "bastion.corp.example.com",
        "principal": "contractor",
        "key_fingerprint": "abc",
        "signed_by_ca": False,
        "ca_id": "",
    }
    ref = decide_probe(ledger, MATCH, probe)
    assert ref["verdict"] == "deny"
    assert ref["scope_id"] == "deploy"


def test_match_scope_reference_bastion():
    """Bastion ops user/host pair must resolve deploy scope from Match blocks."""
    scope = resolve_match_scope(MATCH, "ops", "bastion.corp.example.com")
    assert scope == "deploy"


def test_krl_fingerprints_lowercase_in_ledger():
    """KRL ingestion must normalize revoked fingerprints to lowercase hex."""
    run_ingest()
    revoked = json.loads(LEDGER.read_text())["revoked"]
    assert all(fp == fp.lower() for fp in revoked)
    assert "deadbeef00112233445566778899aabbccddeeff" in revoked


def test_bindings_match_reference_rows():
    """Each session binding verdict and reason must match the sshap_verifier_oracle contract."""
    run_pipeline()
    got = json.loads(ATTESTATION.read_text(encoding="utf-8"))["session_bindings"]
    _, ref = reference_pipeline(PRINCIPALS, CAS, KRL, MATCH, PROBES)
    ref_map = {d["probe_id"]: d for d in ref["session_bindings"]}
    for row in got:
        assert row["verdict"] == ref_map[row["probe_id"]]["verdict"]
        assert row["reason"] == ref_map[row["probe_id"]]["reason"]


def test_attest_idempotent_bytes():
    """Repeated attest with unchanged ledger must produce identical principals_attestation_bundle.json bytes."""
    run_pipeline()
    first = ATTESTATION.read_bytes()
    run_attest()
    second = ATTESTATION.read_bytes()
    assert first == second


def test_decoy_not_in_attestation():
    """Decoy sort_principals_v0 helper must not appear in exported attestation bundle JSON."""
    run_pipeline()
    raw = ATTESTATION.read_text(encoding="utf-8")
    assert "sort_principals_v0" not in raw


def test_hidden_tb3_probes_file_override_when_present():
    """TB3_PROBES_FILE trap: alternate probe manifest must change bundle_seal vs bundled sessions."""
    if not (HIDDEN / "probes.json").is_file():
        pytest.skip("hidden probes absent")
    run_ingest()
    bundled_out = APP / "output" / "bundled_attestation.json"
    proc_b = run_attest(out=bundled_out)
    assert proc_b.returncode == 0, proc_b.stderr
    os.environ["TB3_PROBES_FILE"] = str(HIDDEN / "probes.json")
    alt = APP / "output" / "tb3_probes_attestation.json"
    proc = run_attest(probes=HIDDEN / "probes.json", out=alt)
    assert proc.returncode == 0, proc.stderr
    bundled = json.loads(bundled_out.read_text(encoding="utf-8"))
    got = json.loads(alt.read_text(encoding="utf-8"))
    assert got["bundle_seal"] != bundled["bundle_seal"]


def test_hidden_scoped_global_trap_when_present():
    """TB3 hidden probes must match reference bundle_seal when verifier fixtures are mounted."""
    if not HIDDEN.is_dir():
        pytest.skip("hidden fixtures absent")
    hidden_probes = HIDDEN / "probes.json"
    hidden_match = HIDDEN / "match"
    if not hidden_probes.is_file():
        pytest.skip("hidden probes absent")
    run_ingest()
    os.environ["TB3_MATCH_DIR"] = str(hidden_match)
    os.environ["TB3_PROBES_FILE"] = str(hidden_probes)
    alt = APP / "output" / "hidden_attestation.json"
    proc = run_attest(probes=hidden_probes, match=hidden_match, out=alt)
    assert proc.returncode == 0, proc.stderr
    got = json.loads(alt.read_text(encoding="utf-8"))
    ref_ledger = build_trust_ledger(PRINCIPALS, CAS, KRL)
    ref = emit_principals_attestation(ref_ledger, hidden_match, json.loads(hidden_probes.read_text()))
    assert got["bundle_seal"] == ref["bundle_seal"]


def test_hidden_staging_contractor_deny_when_present():
    """Hidden staging scope must deny contractor via scoped deny line independent of bundled probes."""
    if not (HIDDEN / "probes.json").is_file():
        pytest.skip("hidden probes absent")
    ref_ledger = build_trust_ledger(PRINCIPALS, CAS, KRL)
    probes_doc = json.loads((HIDDEN / "probes.json").read_text(encoding="utf-8"))
    dec = decide_probe(
        ref_ledger,
        HIDDEN / "match",
        next(p for p in probes_doc["probes"] if p["probe_id"] == "h_staging_contractor_deny"),
    )
    assert dec["verdict"] == "deny"


def test_subprocess_independent_alt_ledger():
    """Separate ledger path ingest/attest must succeed with full binding set via subprocess CLI."""
    alt_ledger = APP / "state" / "alt.json"
    alt_out = APP / "output" / "alt_attestation.json"
    run_ingest(alt_ledger)
    proc = run_attest(ledger=alt_ledger, out=alt_out)
    assert proc.returncode == 0, proc.stderr
    data = json.loads(alt_out.read_text(encoding="utf-8"))
    assert len(data["session_bindings"]) >= 8

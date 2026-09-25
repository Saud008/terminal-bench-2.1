"""LDAP effective-access matrix verifier contract for ldaprm."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Any

import pytest
from ldaprm_verifier_oracle import (
    build_matrix,
    build_staging,
    decide_probe,
    reference_pipeline,
)

APP = Path("/app")
CLI = Path("/usr/local/bin/ldaprm")
STAGING = APP / "state/acl_staging.json"
MATRIX = APP / "output/effective_rights_matrix.json"
LDIF = APP / "fixtures/directory/tree.ldif"
GROUPS = APP / "fixtures/groups/membership.tsv"
ACL_DIR = APP / "fixtures/acls"
DEFAULTS = APP / "fixtures/defaults/rights.json"
SUBJECTS = APP / "fixtures/subjects/probes.json"
HIDDEN = Path("/opt/verifier-fixtures/ldaprm_hidden")


def _exec(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(argv, check=False, capture_output=True, text=True, cwd=str(APP))


@pytest.fixture()
def ae_session() -> dict[str, Any]:
    os.environ.pop("TB3_ACL_DIR", None)
    os.environ.pop("TB3_SUBJECTS_FILE", None)
    assert _exec(["bash", str(APP / "scripts/reset-state.sh")]).returncode == 0
    assert _exec(["bash", str(APP / "scripts/rebuild-ldaprm.sh")]).returncode == 0
    yield {"staging": STAGING, "matrix": MATRIX}
    os.environ.pop("TB3_ACL_DIR", None)
    os.environ.pop("TB3_SUBJECTS_FILE", None)


def _ingest(staging: Path = STAGING) -> subprocess.CompletedProcess[str]:
    return _exec(
        [
            str(CLI),
            "ingest",
            "--ldif",
            str(LDIF),
            "--groups",
            str(GROUPS),
            "--acls",
            str(ACL_DIR),
            "--defaults",
            str(DEFAULTS),
            "--staging",
            str(staging),
        ]
    )


def _export(
    staging: Path = STAGING,
    out: Path = MATRIX,
    subjects: Path | None = None,
) -> subprocess.CompletedProcess[str]:
    subj = subjects
    if subj is None:
        tb3 = os.environ.get("TB3_SUBJECTS_FILE")
        subj = Path(tb3) if tb3 else SUBJECTS
    return _exec(
        [
            str(CLI),
            "export",
            "--staging",
            str(staging),
            "--subjects",
            str(subj),
            "--out",
            str(out),
        ]
    )


def _full_run(staging: Path = STAGING, out: Path = MATRIX) -> dict[str, Any]:
    ing = _ingest(staging)
    assert ing.returncode == 0, ing.stderr
    exp = _export(staging, out)
    assert exp.returncode == 0, exp.stderr
    return json.loads(out.read_text(encoding="utf-8"))


def _row_map(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["probe_id"]: row for row in doc["decisions"]}


def test_t524ab4_ae7f2_cli_entrypoint_installed(ae_session):
    """Verify ldaprm cli entrypoint installed."""
    assert Path("/usr/local/bin/ldaprm").is_file()


def test_t524ab4_ae7f2_ingest_writes_staging_snapshot(ae_session):
    """Verify ldaprm ingest writes staging snapshot."""
    assert _ingest().returncode == 0
    snap = json.loads(STAGING.read_text(encoding="utf-8"))
    assert snap["schema_version"] == 1
    assert len(snap["entries"]) >= 8
    assert len(snap["aces"]) >= 5


def test_t524ab4_ae7f2_staging_fingerprint_tracks_oracle(ae_session):
    """Verify ldaprm staging fingerprint tracks oracle."""
    _ingest()
    live = json.loads(STAGING.read_text(encoding="utf-8"))
    expect = build_staging(LDIF, GROUPS, ACL_DIR, DEFAULTS)
    assert live["staging_fingerprint"] == expect["staging_fingerprint"]


def test_t524ab4_ae7f2_nested_group_closure_contains_alice(ae_session):
    """Verify ldaprm nested group closure contains alice."""
    _ingest()
    closure = json.loads(STAGING.read_text(encoding="utf-8"))["group_closure"]
    grp = "cn=readers,ou=groups,dc=example,dc=com"
    assert "cn=alice,ou=people,dc=example,dc=com" in closure.get(grp, [])


def test_t524ab4_ae7f2_export_materializes_matrix_file(ae_session):
    """Verify ldaprm export materializes matrix file."""
    _ingest()
    assert _export().returncode == 0
    assert MATRIX.is_file()


def test_t524ab4_ae7f2_report_digest_matches_oracle_pipeline(ae_session):
    """Verify ldaprm report digest matches oracle pipeline."""
    doc = _full_run()
    _, expect = reference_pipeline(LDIF, GROUPS, ACL_DIR, DEFAULTS, SUBJECTS)
    assert doc["report_digest"] == expect["report_digest"]


def test_t524ab4_ae7f2_decision_rows_sorted_by_probe_id(ae_session):
    """Verify ldaprm decision rows sorted by probe id."""
    doc = _full_run()
    ids = [row["probe_id"] for row in doc["decisions"]]
    assert ids == sorted(ids)


def test_t524ab4_ae7f2_matrix_schema_version_one(ae_session):
    """Verify ldaprm matrix schema version one."""
    assert _full_run()["schema_version"] == 1


def test_t524ab4_ae7f2_staging_fingerprint_echoed_in_matrix(ae_session):
    """Verify ldaprm staging fingerprint echoed in matrix."""
    _ingest()
    snap = json.loads(STAGING.read_text(encoding="utf-8"))
    doc = _full_run()
    assert doc["staging_fingerprint"] == snap["staging_fingerprint"]


def test_t524ab4_ae7f2_decision_rows_include_audit_digest(ae_session):
    """Verify ldaprm decision rows include audit digest."""
    doc = _full_run()
    for row in doc["decisions"]:
        assert row["audit_digest"]
        assert len(row["audit_digest"]) == 64


@pytest.mark.parametrize(
    "probe_id,field,want",
    [
        ("p_alice_mail_write", "verdict", "allow"),
        ("p_alice_mail_deny_readers", "verdict", "deny"),
        ("p_carol_password_deny", "reason", "ace_deny"),
        ("p_nested_reader_bob", "verdict", "allow"),
        ("p_subtree_self_alice_read", "verdict", "allow"),
        ("p_admin_read_group", "verdict", "allow"),
        ("p_carol_no_admin_group", "verdict", "deny"),
        ("p_anonymous_person_deny", "verdict", "deny"),
    ],
)
def test_t524ab4_ae7f2_probe_expectations(ae_session, probe_id, field, want):
    """Verify ldaprm probe expectations."""
    rows = _row_map(_full_run())
    assert rows[probe_id][field] == want


def test_t524ab4_ae7f2_all_rows_align_with_oracle(ae_session):
    """Verify ldaprm all rows align with oracle."""
    doc = _full_run()
    _, expect = reference_pipeline(LDIF, GROUPS, ACL_DIR, DEFAULTS, SUBJECTS)
    expect_rows = _row_map(expect)
    for row in doc["decisions"]:
        assert row["verdict"] == expect_rows[row["probe_id"]]["verdict"]
        assert row["reason"] == expect_rows[row["probe_id"]]["reason"]


def test_t524ab4_ae7f2_repeat_export_is_byte_stable(ae_session):
    """Verify ldaprm repeat export is byte stable."""
    _full_run()
    first = MATRIX.read_bytes()
    assert _export().returncode == 0
    assert first == MATRIX.read_bytes()


def test_t524ab4_ae7f2_decoy_module_not_serialized(ae_session):
    """Verify ldaprm decoy module not serialized."""
    _full_run()
    assert "merge_acl_lines" not in MATRIX.read_text(encoding="utf-8")


def test_t524ab4_ae7f2_tb3_subjects_alters_report_digest(ae_session):
    """Verify ldaprm tb3 subjects alters report digest."""
    hidden = HIDDEN / "subjects/probes.json"
    if not hidden.is_file():
        pytest.skip("hidden probes absent")
    _ingest()
    bundled = APP / "output/bundled_matrix.json"
    alt = APP / "output/tb3_matrix.json"
    assert _export(out=bundled).returncode == 0
    assert _export(subjects=hidden, out=alt).returncode == 0
    assert json.loads(bundled.read_text())["report_digest"] != json.loads(alt.read_text())["report_digest"]


def test_t524ab4_ae7f2_hidden_inherit_probe_denies_mail_read(ae_session):
    """Verify ldaprm hidden inherit probe denies mail read."""
    hidden = HIDDEN / "subjects/probes.json"
    if not hidden.is_file():
        pytest.skip("hidden probes absent")
    snap = build_staging(LDIF, GROUPS, ACL_DIR, DEFAULTS)
    probe = next(p for p in json.loads(hidden.read_text())["probes"] if p["probe_id"] == "h_inherit_block_mail")
    verdict = decide_probe(
        probe,
        snap["entries"],
        snap["aces"],
        {k: set(v) for k, v in snap["group_closure"].items()},
        {k: set(v) for k, v in snap["group_graph"].items()},
        snap["defaults"],
    )
    assert verdict["verdict"] == "deny"


def test_t524ab4_ae7f2_tb3_acl_dir_swap_changes_matrix(ae_session):
    """Verify ldaprm tb3 acl dir swap changes matrix."""
    hidden_acl = HIDDEN / "acls"
    hidden_subj = HIDDEN / "subjects/probes.json"
    if not hidden_acl.is_dir():
        pytest.skip("hidden fixtures absent")
    os.environ["TB3_ACL_DIR"] = str(hidden_acl)
    _ingest()
    out = APP / "output/tb3_acl_matrix.json"
    assert _export(subjects=hidden_subj, out=out).returncode == 0
    got = json.loads(out.read_text(encoding="utf-8"))
    snap = json.loads(STAGING.read_text(encoding="utf-8"))
    expect = build_matrix(snap, json.loads(hidden_subj.read_text()), acl_dir_override=hidden_acl)
    assert got["report_digest"] == expect["report_digest"]
    row = _row_map(got)["h_inherit_block_mail"]
    assert row["verdict"] == "deny"
    assert row["reason"] == "ace_deny"


def test_t524ab4_ae7f2_custom_staging_and_output_paths(ae_session):
    """Verify ldaprm custom staging and output paths."""
    alt_staging = APP / "state/alt_staging.json"
    alt_out = APP / "output/alt_matrix.json"
    assert _ingest(alt_staging).returncode == 0
    assert _export(alt_staging, alt_out).returncode == 0
    assert len(json.loads(alt_out.read_text())["decisions"]) >= 10

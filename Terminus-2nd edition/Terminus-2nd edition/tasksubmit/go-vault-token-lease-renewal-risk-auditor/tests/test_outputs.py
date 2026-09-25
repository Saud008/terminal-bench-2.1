"""vaultaud audit/rollup behavioral contracts."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from lease_auditor_math import (
    bundled_config_sha256,
    bundled_transcript_sha256,
    lineage_edges,
    load_config,
    reference_atlas,
    reference_risk,
    reference_stage,
)
from vaultaud_cli import (
    ATLAS,
    BIN,
    LEDGER,
    active_transcript_dir,
    clear_outputs,
    compile_vaultaud,
    run_audit_rollup,
)
from vaultaud_json import read_atlas_doc, read_staging_rows

HIDDEN_ROOT = Path("/opt/verifier-fixtures/vaultaud_renewal_hidden")
HIDDEN_CHAIN = HIDDEN_ROOT / "renewal_logs"
HIDDEN_CYCLE = HIDDEN_ROOT / "renewal_cycles"


def _by_token(rows: list[dict]) -> dict[str, dict]:
    return {r["token_id"]: r for r in rows}


def _latest(rows: list[dict], token: str) -> dict:
    return max((r for r in rows if r["token_id"] == token), key=lambda r: r["renewal_seq"])


def test_t702cfb_vaultaud_rebuild_installs_binary():
    """rebuild-vaultaud.sh must produce the vaultaud binary at /app/bin/vaultaud."""
    compile_vaultaud()
    assert BIN.is_file()


def test_t702cfb_collect_emits_state_jsonl_ledger():
    """audit must write the staging ledger path /app/state/lease_audit_buffer.jsonl."""
    compile_vaultaud()
    run_audit_rollup()
    assert LEDGER.is_file()
    assert str(LEDGER) == "/app/state/lease_audit_buffer.jsonl"
    assert len(read_staging_rows()) >= 8


def test_t702cfb_publish_writes_token_risk_rollup():
    """rollup must write /app/output/token_risk_rollup.json with tokens, edges, roots, totals."""
    compile_vaultaud()
    run_audit_rollup()
    assert ATLAS.is_file()
    doc = read_atlas_doc()
    assert "tokens" in doc and "lineage_edges" in doc and "lineage_roots" in doc and "totals" in doc


def test_t702cfb_publish_rejects_missing_staging_ledger():
    """rollup must fail when the staging ledger is absent."""
    compile_vaultaud()
    clear_outputs()
    result = subprocess.run(
        [str(BIN), "rollup", "--staging", str(LEDGER), "--atlas", str(ATLAS)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert result.stderr.strip() != "" or result.stdout.strip() != ""


def test_t702cfb_collect_on_empty_transcript_dir(tmp_path):
    """audit on an empty transcript directory must write an empty staging file."""
    compile_vaultaud()
    empty = tmp_path / "empty"
    empty.mkdir()
    clear_outputs()
    result = subprocess.run(
        [
            str(BIN), "audit",
            "--transcript-dir", str(empty),
            "--config-dir", str(Path("/app/fixtures/config")),
            "--staging", str(LEDGER),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert read_staging_rows() == []


def test_t702cfb_bundled_config_sha256_integrity():
    """bundled /app/fixtures/config must match a stable sha256 digest."""
    digest = bundled_config_sha256()
    assert len(digest) == 64
    load_config()


def test_t702cfb_bundled_transcript_sha256_integrity():
    """bundled renewal transcripts must match a stable sha256 digest."""
    digest = bundled_transcript_sha256()
    assert len(digest) == 64


def test_t702cfb_staging_row_count_matches_reference_stage():
    """audit output row count must match independent reference_stage math."""
    compile_vaultaud()
    run_audit_rollup()
    assert len(read_staging_rows()) == len(reference_stage(active_transcript_dir()))


def test_staging_sorted_by_depth_then_seq_then_token():
    """staging_pipeline.md orders by depth key, renewal_seq, token_id, event_id."""
    compile_vaultaud()
    run_audit_rollup()
    rows = read_staging_rows()
    keys = [
        ((1 << 30 if r["lineage_depth"] < 0 else r["lineage_depth"]), r["renewal_seq"], r["token_id"], r["event_id"])
        for r in rows
    ]
    assert keys == sorted(keys)


def test_ops_policy_revision_boundary_on_child():
    """policy_revisions.md must pick the ops-standard revision active at CHILD issued_at."""
    compile_vaultaud()
    run_audit_rollup()
    child = _latest(read_staging_rows(), "hvs.CHILD")
    assert child["policy_cap_sec"] == 7200


def test_root_static_cap_is_role_tightest():
    """ttl_cap_precedence.md must fold ROOT to the tightest static layer."""
    compile_vaultaud()
    run_audit_rollup()
    root = _by_token(read_staging_rows())["hvs.ROOT"]
    assert root["static_cap_sec"] == 7200
    assert root["granted_ttl_sec"] == 7200


def test_approle_mount_caps_ci_renewal():
    """approle mount max lease must cap the latest hvs.CI renewal static and granted TTL."""
    compile_vaultaud()
    run_audit_rollup()
    ci = _latest(read_staging_rows(), "hvs.CI")
    assert ci["static_cap_sec"] == 900
    assert ci["granted_ttl_sec"] == 900


def test_child_second_renewal_clamped_by_parent_expiry():
    """delegation_clamp.md must clamp CHILD seq2 against ROOT's granted expiry."""
    compile_vaultaud()
    run_audit_rollup()
    child2 = _latest(read_staging_rows(), "hvs.CHILD")
    assert child2["renewal_seq"] == 2
    assert child2["granted_ttl_sec"] == 3600
    assert child2["admission"] == "granted"


def test_svc_budget_caps_requested_lease():
    """lifetime_budget.md must cap SVC granted TTL to the kubernetes/svc-agent lifetime."""
    compile_vaultaud()
    run_audit_rollup()
    svc = _by_token(read_staging_rows())["hvs.SVC"]
    assert svc["lifetime_ceiling_sec"] == 5400
    assert svc["budget_remaining_sec"] == 5400
    assert svc["granted_ttl_sec"] == 5400


def test_deny_second_renewal_exhausts_budget():
    """a second DENY renewal after the lifetime window must be denied with zero granted TTL."""
    compile_vaultaud()
    run_audit_rollup()
    deny2 = _latest(read_staging_rows(), "hvs.DENY")
    assert deny2["renewal_seq"] == 2
    assert deny2["budget_remaining_sec"] == 0
    assert deny2["granted_ttl_sec"] == 0
    assert deny2["admission"] == "denied"


def test_dchild_inherits_denied_parent_expiry():
    """a child of a denied parent must itself be denied via zero delegation headroom."""
    compile_vaultaud()
    run_audit_rollup()
    dchild = _by_token(read_staging_rows())["hvs.DCHILD"]
    assert dchild["delegated_parent"] == "hvs.DENY"
    assert dchild["granted_ttl_sec"] == 0
    assert dchild["admission"] == "denied"
    assert dchild["effective_renewable"] is False


def test_userpass_mount_marks_root_non_renewable():
    """renewable_inheritance.md must mark userpass mount tokens non renewable at ROOT."""
    compile_vaultaud()
    run_audit_rollup()
    assert _by_token(read_staging_rows())["hvs.ROOT"]["effective_renewable"] is False


def test_batch_role_marks_batch_non_renewable():
    """batch role renewable false must mark hvs.BATCH non renewable."""
    compile_vaultaud()
    run_audit_rollup()
    assert _by_token(read_staging_rows())["hvs.BATCH"]["effective_renewable"] is False


def test_orphan_token_flags_missing_parent():
    """lineage_graph.md must flag a missing parent_id with the orphan: lineage_root prefix."""
    compile_vaultaud()
    run_audit_rollup()
    orph = _by_token(read_staging_rows())["hvs.ORPH"]
    assert orph["is_orphan"] is True
    assert orph["lineage_root"] == "orphan:hvs.ORPH"
    assert orph["delegated_parent"] == ""


def test_severed_orphan_flag_drops_parent_edge():
    """an orphan issuance with a live parent_id must sever the edge and keep its own root."""
    compile_vaultaud()
    run_audit_rollup()
    sev = _by_token(read_staging_rows())["hvs.SEV"]
    assert sev["is_orphan"] is True
    assert sev["lineage_root"] == "hvs.SEV"
    assert sev["delegated_parent"] == ""
    assert sev["lineage_depth"] == 0
    edges = {(e["parent_token"], e["child_token"]) for e in read_atlas_doc()["lineage_edges"]}
    assert ("hvs.ROOT", "hvs.SEV") not in edges


def test_child_resolves_lineage_root_to_parent():
    """lineage walk must resolve hvs.CHILD lineage_root to parent hvs.ROOT with depth 1."""
    compile_vaultaud()
    run_audit_rollup()
    child = _latest(read_staging_rows(), "hvs.CHILD")
    assert child["lineage_root"] == "hvs.ROOT"
    assert child["lineage_depth"] == 1
    assert child["delegated_parent"] == "hvs.ROOT"


def test_full_staging_matches_reference_stage():
    """full ingest staging rows must match independent TTL, budget, delegation, and lineage math."""
    compile_vaultaud()
    run_audit_rollup()
    assert read_staging_rows() == reference_stage(active_transcript_dir())


def test_full_atlas_matches_reference_atlas():
    """full rollup document must match independent risk, roots, edges, and totals math."""
    compile_vaultaud()
    run_audit_rollup()
    cfg = load_config()
    staged = reference_stage(active_transcript_dir())
    assert read_atlas_doc() == reference_atlas(staged, cfg["anchor"])


def test_atlas_lineage_roots_severity_not_alphabetical():
    """lineage_roots.worst_bucket must use severity order, not alphabetical order."""
    compile_vaultaud()
    run_audit_rollup()
    cfg = load_config()
    staged = reference_stage(active_transcript_dir())
    expected = {r["lineage_root"]: r for r in reference_atlas(staged, cfg["anchor"])["lineage_roots"]}
    for row in read_atlas_doc()["lineage_roots"]:
        assert row["worst_bucket"] == expected[row["lineage_root"]]["worst_bucket"]
        assert row["token_count"] == expected[row["lineage_root"]]["token_count"]
        assert row["blast_radius"] == expected[row["lineage_root"]]["blast_radius"]


def test_denied_row_risk_score_includes_bonus():
    """token_risk_rollup.md must add the denied adjustment to DENY seq2 risk_score."""
    compile_vaultaud()
    run_audit_rollup()
    cfg = load_config()
    deny2 = _latest(reference_stage(active_transcript_dir()), "hvs.DENY")
    risk = reference_risk(deny2, cfg["anchor"])
    tokens = {(t["token_id"], t["renewal_seq"]): t for t in read_atlas_doc()["tokens"]}
    assert tokens[("hvs.DENY", 2)]["risk_score"] == risk["risk_score"]
    assert tokens[("hvs.DENY", 2)]["admission"] == "denied"


def test_cross_run_audit_rollup_byte_identical():
    """re-running audit then rollup over the same transcripts must be byte identical."""
    compile_vaultaud()
    run_audit_rollup()
    first_ledger = LEDGER.read_bytes()
    first_atlas = ATLAS.read_bytes()
    run_audit_rollup()
    assert LEDGER.read_bytes() == first_ledger
    assert ATLAS.read_bytes() == first_atlas


def test_tb3_hidden_chain_override_and_depth_order(monkeypatch):
    """hidden chain fixture requires override_parent and depth-ordered delegation."""
    if not HIDDEN_CHAIN.is_dir():
        pytest.skip("hidden fixtures not mounted")
    compile_vaultaud()
    monkeypatch.setenv("TB3_TRANSCRIPT_DIR", str(HIDDEN_CHAIN))
    run_audit_rollup(HIDDEN_CHAIN)
    staged = _by_token(read_staging_rows())
    assert staged["hvs.HROOT"]["policy_cap_sec"] == 7200
    assert staged["hvs.HROOT"]["granted_ttl_sec"] == 7200
    assert staged["hvs.HKID"]["granted_ttl_sec"] == 6600
    assert staged["hvs.HGC"]["policy_cap_sec"] == 12000
    assert staged["hvs.HGC"]["granted_ttl_sec"] == 5400
    assert staged["hvs.HLOCK"]["effective_renewable"] is False
    assert staged["hvs.HLOCK"]["policy_cap_sec"] == 1800
    assert read_staging_rows() == reference_stage(HIDDEN_CHAIN)


def test_tb3_hidden_cycle_clamp_and_score(monkeypatch):
    """hidden cycle fixture requires cycle classification and the risk_score clamp."""
    if not HIDDEN_CYCLE.is_dir():
        pytest.skip("hidden fixtures not mounted")
    compile_vaultaud()
    monkeypatch.setenv("TB3_TRANSCRIPT_DIR", str(HIDDEN_CYCLE))
    run_audit_rollup(HIDDEN_CYCLE)
    staged = read_staging_rows()
    by = _by_token(staged)
    assert by["hvs.CA"]["lineage_root"] == "cycle:hvs.CA"
    assert by["hvs.CA"]["lineage_depth"] == -1
    assert by["hvs.CB"]["lineage_root"] == "cycle:hvs.CA"
    assert by["hvs.CSEV"]["lineage_root"] == "hvs.CSEV"
    assert by["hvs.CSEV"]["is_orphan"] is True
    assert by["hvs.CMISS"]["lineage_root"] == "orphan:hvs.CMISS"
    clamp2 = _latest(staged, "hvs.CCLAMP")
    assert clamp2["admission"] == "denied"
    cfg = load_config()
    assert read_atlas_doc() == reference_atlas(reference_stage(HIDDEN_CYCLE), cfg["anchor"])
    tokens = {(t["token_id"], t["renewal_seq"]): t for t in read_atlas_doc()["tokens"]}
    assert tokens[("hvs.CCLAMP", 2)]["risk_score"] == 200
    assert lineage_edges(staged) == read_atlas_doc()["lineage_edges"]

"""Behavioral tests for rosterctl membership ops."""

from __future__ import annotations

import json
from pathlib import Path

from roster_refmath import reference_export, replay_reference
from roster_shell_ops import (
    BUNDLED,
    CLUSTER,
    INGEST_SCENARIOS,
    OFF_CATALOG,
    PATHS,
    drive_full_attestation_run,
    exec_roster,
    read_jsonl,
    wipe_workspace,
)

MATRIX = json.loads(Path(__file__).with_name("roster_scenario_matrix.json").read_text(encoding="utf-8"))


def test_c4e91b7d2f_matrix_bundled_scenarios_present() -> None:
    """Matrix lists every bundled ingest scenario slug."""
    for slug in MATRIX["bundled"]:
        assert slug in INGEST_SCENARIOS


def test_c4e91b7d2f_leader_handoff_committed_ledger() -> None:
    """Leader handoff scenario export matches independent replay reference."""
    wipe_workspace()
    drive_full_attestation_run("leader-handoff")
    ledger = read_jsonl(PATHS["ledger"])
    ref, _ = reference_export(CLUSTER, "leader-handoff", BUNDLED)
    assert ledger == ref


def test_c4e91b7d2f_term_order_trap_leader_term() -> None:
    """Term/index ordering picks higher-term leader after replay."""
    wipe_workspace()
    drive_full_attestation_run("term-order-trap")
    staging = json.loads(PATHS["staging"].read_text(encoding="utf-8"))
    ref = replay_reference(CLUSTER, BUNDLED / "term-order-trap")
    assert staging["leader_id"] == ref["leader_id"]
    assert staging["current_term"] == ref["current_term"]


def test_c4e91b7d2f_uncommitted_tail_excludes_pending_queue() -> None:
    """Uncommitted tail queue must not appear in export rows."""
    wipe_workspace()
    drive_full_attestation_run("uncommitted-tail")
    ledger = read_jsonl(PATHS["ledger"])
    ref, _ = reference_export(CLUSTER, "uncommitted-tail", BUNDLED)
    assert ledger == ref
    assert len(ledger) == 1


def test_c4e91b7d2f_snapshot_truncation_merge_path() -> None:
    """Snapshot truncation scenario uses merge-snapshot plus export."""
    wipe_workspace()
    drive_full_attestation_run("snapshot-truncation")
    staging = json.loads(PATHS["staging"].read_text(encoding="utf-8"))
    ref = replay_reference(CLUSTER, BUNDLED / "snapshot-truncation")
    assert staging["truncated_before"] == ref["truncated_before"]
    ledger = read_jsonl(PATHS["ledger"])
    ref_rows, _ = reference_export(CLUSTER, "snapshot-truncation", BUNDLED)
    assert ledger == ref_rows


def test_c4e91b7d2f_replica_add_same_term_membership() -> None:
    """Same-term config change adds voter to export replica set."""
    wipe_workspace()
    drive_full_attestation_run("replica-add-same-term")
    staging = json.loads(PATHS["staging"].read_text(encoding="utf-8"))
    ref = replay_reference(CLUSTER, BUNDLED / "replica-add-same-term")
    assert staging["membership"] == ref["membership"]
    expected_voter_count = 3
    assert len(staging["membership"]) == expected_voter_count


def test_c4e91b7d2f_cross_run_idempotent_bytes() -> None:
    """Repeated full pipeline yields identical ledger bytes."""
    wipe_workspace()
    drive_full_attestation_run("cross-run-idempotent")
    first = PATHS["ledger"].read_bytes()
    wipe_workspace()
    drive_full_attestation_run("cross-run-idempotent")
    assert PATHS["ledger"].read_bytes() == first


def test_c4e91b7d2f_quorum_seal_positive() -> None:
    """Export writes membership seal with positive raft_seal."""
    wipe_workspace()
    drive_full_attestation_run("leader-handoff")
    seal = json.loads(PATHS["seal"].read_text(encoding="utf-8"))
    assert seal["raft_seal"]
    assert seal["export_row_count"] >= 1


def test_c4e91b7d2f_membership_audit_report() -> None:
    """Audit-membership verb writes replica membership report."""
    wipe_workspace()
    drive_full_attestation_run("leader-handoff")
    assert PATHS["audit"].is_file()
    report = json.loads(PATHS["audit"].read_text(encoding="utf-8"))
    assert report["finding_count"] >= 1


def test_c4e91b7d2f_staging_replay_digest() -> None:
    """Staging replay_digest matches reference replay hash."""
    wipe_workspace()
    drive_full_attestation_run("term-order-trap")
    staging = json.loads(PATHS["staging"].read_text(encoding="utf-8"))
    ref = replay_reference(CLUSTER, BUNDLED / "term-order-trap")
    assert staging["replay_digest"] == ref["replay_digest"]


def test_c4e91b7d2f_ledger_sorted_by_queue_id() -> None:
    """Export ledger rows sorted by queue_id ascending."""
    wipe_workspace()
    drive_full_attestation_run("leader-handoff")
    ledger = read_jsonl(PATHS["ledger"])
    ids = [r["queue_id"] for r in ledger]
    assert ids == sorted(ids)


def test_c4e91b7d2f_replay_log_writes_staging() -> None:
    """replay-log alone creates membership staging artifact."""
    wipe_workspace()
    proc = exec_roster(["replay-log", "--cluster", CLUSTER, "--scenario", "leader-handoff"])
    assert proc.returncode == 0
    assert PATHS["staging"].is_file()


def test_c4e91b7d2f_commit_index_fenced() -> None:
    """Staging commit_index matches reference for uncommitted-tail."""
    wipe_workspace()
    drive_full_attestation_run("uncommitted-tail")
    staging = json.loads(PATHS["staging"].read_text(encoding="utf-8"))
    ref = replay_reference(CLUSTER, BUNDLED / "uncommitted-tail")
    assert staging["commit_index"] == ref["commit_index"]


def test_c4e91b7d2f_hidden_truncation_poison_off_catalog() -> None:
    """Hidden truncation poison fixture matches reference export."""
    wipe_workspace()
    drive_full_attestation_run("hidden-truncation-poison", OFF_CATALOG)
    ledger = read_jsonl(PATHS["ledger"])
    ref, _ = reference_export(CLUSTER, "hidden-truncation-poison", OFF_CATALOG)
    assert ledger == ref


def test_c4e91b7d2f_hidden_uncommitted_leader_off_catalog() -> None:
    """Hidden uncommitted leader trap excludes tail queue state."""
    wipe_workspace()
    drive_full_attestation_run("hidden-uncommitted-leader", OFF_CATALOG)
    ledger = read_jsonl(PATHS["ledger"])
    ref, _ = reference_export(CLUSTER, "hidden-uncommitted-leader", OFF_CATALOG)
    assert ledger == ref


def test_c4e91b7d2f_matrix_membership_audit_phase() -> None:
    """Matrix membership_audit phase validates replica-add scenario."""
    wipe_workspace()
    drive_full_attestation_run("replica-add-same-term")
    _, seal = reference_export(CLUSTER, "replica-add-same-term", BUNDLED)
    got = json.loads(PATHS["seal"].read_text(encoding="utf-8"))
    assert got["export_row_count"] == seal["export_row_count"]


def test_c4e91b7d2f_matrix_hidden_poison_catalog() -> None:
    """Hidden poison slug listed in scenario matrix."""
    assert "hidden-truncation-poison" in MATRIX["hidden"]


def test_c4e91b7d2f_seal_matches_reference() -> None:
    """Quorum ledger seal matches reference seal for leader-handoff."""
    wipe_workspace()
    drive_full_attestation_run("leader-handoff")
    got = json.loads(PATHS["seal"].read_text(encoding="utf-8"))
    _, ref = reference_export(CLUSTER, "leader-handoff", BUNDLED)
    assert got == ref


def test_c4e91b7d2f_export_row_replica_sorted() -> None:
    """Export replica lists are sorted ascending."""
    wipe_workspace()
    drive_full_attestation_run("replica-add-same-term")
    for row in read_jsonl(PATHS["ledger"]):
        assert row["replicas"] == sorted(row["replicas"])

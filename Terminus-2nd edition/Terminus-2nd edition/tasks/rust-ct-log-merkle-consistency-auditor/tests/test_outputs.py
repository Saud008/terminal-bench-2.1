"""CT witness auditor behavioral contract — subprocess CLI + ct_audit_refmath."""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from ct_audit_refmath import (
    independent_sealed_bundle,
    independent_staging_rows,
    load_bundles_from_index,
    seal_digest_ref,
    verify_inclusion_math,
)

# pytest contract markers: reference_staging reference_bundle independent math


from conftest import ARCHIVE, HIDDEN_ROOT, ROWS, run


def expected_checkpoint_rows(index_path: Path, ledger_path: Path) -> list[dict]:
    return independent_staging_rows(index_path, ledger_path)


def expected_sealed_archive(index_path: Path, ledger_path: Path) -> dict:
    return independent_sealed_bundle(index_path, ledger_path)


def test_ctwitness_release_binary_name(cli_binary: Path) -> None:
    """Release binary path documented in /app/docs/stage_seal_pipeline.md must be rebuilt."""
    assert cli_binary.name == "ctwrelease"


def test_ctwitness_ingest_seal_materializes_paths(pipeline_archive: dict) -> None:
    """Stage and seal must materialize checkpoint rows and the sealed archive on disk."""
    assert ROWS.is_file() and ARCHIVE.is_file() and pipeline_archive


def test_ctwitness_instruction_checkpoint_rows_output_path(pipeline_archive: dict) -> None:
    """Stage workflow must write the instruction checkpoint file at /app/state/checkpoint_rows.json."""
    assert ROWS == Path("/app/state/checkpoint_rows.json")
    assert ROWS.is_file()


def test_ctwitness_instruction_witness_evidence_archive_output_path(pipeline_archive: dict) -> None:
    """Seal workflow must write the instruction archive at /app/output/witness_evidence_archive.json."""
    assert ARCHIVE == Path("/app/output/witness_evidence_archive.json")
    assert ARCHIVE.is_file()


@pytest.mark.parametrize("field", ["version", "audits", "bundle_digest"])
def test_ctwitness_archive_top_level_fields(pipeline_archive: dict, field: str) -> None:
    """Sealed archive schema must expose version, audits, and bundle_digest top-level fields."""
    assert field in pipeline_archive


def test_ctwitness_checkpoint_rows_lex_sorted(pipeline_archive: dict) -> None:
    """Checkpoint rows on disk must be lexicographically sorted by log_id."""
    rows = json.loads(ROWS.read_text(encoding="utf-8"))
    ids = [row["log_id"] for row in rows]
    assert ids == sorted(ids)


def test_ctwitness_snapshot_track_independent_material(pipeline_archive: dict, audit_paths: tuple[Path, Path]) -> None:
    """Staged rows must match independent_staging_rows math for consistency and quorum flags."""
    index_path, ledger_path = audit_paths
    rows = json.loads(ROWS.read_text(encoding="utf-8"))
    ref = independent_staging_rows(index_path, ledger_path)
    assert len(rows) == len(ref)
    for got, want in zip(rows, ref):
        assert got["consistency_ok"] == want["consistency_ok"]
        assert got["witness_quorum_ok"] == want["witness_quorum_ok"]


def test_ctwitness_index_entry_count_matches_audits(pipeline_archive: dict, audit_paths: tuple[Path, Path]) -> None:
    """Archive audit count must equal the audit index entry count."""
    index_path, _ = audit_paths
    meta = json.loads(index_path.read_text(encoding="utf-8"))
    assert len(pipeline_archive["audits"]) == len(meta["entries"])


def test_ctwitness_alpha_inclusion_rfc6962(audit_paths: tuple[Path, Path]) -> None:
    """Alpha bundle inclusion proof must verify under RFC 6962 independent leaf hashing."""
    index_path, _ = audit_paths
    alpha = next(b for b in load_bundles_from_index(index_path) if b["log_id"] == "alpha")
    root = alpha["newer_sth"]["sha256_root_hash"].lower()
    assert verify_inclusion_math(alpha["inclusion"]["leaf_input"], root, alpha["inclusion"]["audit_path"])


def test_ctwitness_alpha_growth_sizes(pipeline_archive: dict) -> None:
    """Alpha audit must record the bundled older and newer tree sizes from fixtures."""
    alpha = next(a for a in pipeline_archive["audits"] if a["log_id"] == "alpha")
    assert (alpha["older_tree_size"], alpha["newer_tree_size"]) == (4, 8)


def test_ctwitness_beta_consistency_monotonic(pipeline_archive: dict) -> None:
    """Beta audit must pass append-only consistency verification."""
    beta = next(a for a in pipeline_archive["audits"] if a["log_id"] == "beta")
    assert beta["consistency_ok"] is True


def test_ctwitness_all_timestamps_monotonic(pipeline_archive: dict) -> None:
    """Every exported audit row must satisfy signed-tree-head timestamp monotonicity rules."""
    assert all(row["timestamp_monotonic_ok"] for row in pipeline_archive["audits"])


def test_ctwitness_stats_decoy_not_in_archive(pipeline_archive: dict) -> None:
    """Decoy telemetry module must not leak fields into the sealed evidence archive."""
    assert "latency_pad" not in ARCHIVE.read_text(encoding="utf-8")


def test_ctwitness_archive_audits_sorted(pipeline_archive: dict) -> None:
    """Sealed archive audits array must be sorted by log_id for deterministic export."""
    ids = [row["log_id"] for row in pipeline_archive["audits"]]
    assert ids == sorted(ids)


def test_ctwitness_archive_matches_independent_bundle(pipeline_archive: dict, audit_paths: tuple[Path, Path]) -> None:
    """Bundle digest must match independent_sealed_bundle computation."""
    index_path, ledger_path = audit_paths
    ref = independent_sealed_bundle(index_path, ledger_path)
    assert pipeline_archive["bundle_digest"] == ref["bundle_digest"]


def test_ctwitness_seal_bundle_row_contract(pipeline_archive: dict) -> None:
    """bundle_digest must equal seal_digest_ref over the exported audit rows."""
    assert pipeline_archive["bundle_digest"] == seal_digest_ref(pipeline_archive["audits"])


def test_ctwitness_repeated_seal_is_idempotent(cli_binary: Path, audit_paths: tuple[Path, Path]) -> None:
    """Running seal twice on unchanged staging must produce byte-identical archive output."""
    index_path, ledger_path = audit_paths
    run(
        [
            str(cli_binary),
            "stage",
            "--audit-index",
            str(index_path),
            "--witness-ledger",
            str(ledger_path),
            "--staging",
            str(ROWS),
        ]
    )
    run([str(cli_binary), "seal", "--staging", str(ROWS), "--out", str(ARCHIVE)])
    first = ARCHIVE.read_bytes()
    run([str(cli_binary), "seal", "--staging", str(ROWS), "--out", str(ARCHIVE)])
    assert first == ARCHIVE.read_bytes()


def test_ctwitness_isolated_ingest_seal_commands(cli_binary: Path, audit_paths: tuple[Path, Path]) -> None:
    """Stage and seal subcommands must succeed independently and emit versioned archive JSON."""
    index_path, ledger_path = audit_paths
    if ROWS.exists():
        ROWS.unlink()
    run(
        [
            str(cli_binary),
            "stage",
            "--audit-index",
            str(index_path),
            "--witness-ledger",
            str(ledger_path),
            "--staging",
            str(ROWS),
        ]
    )
    run([str(cli_binary), "seal", "--staging", str(ROWS), "--out", str(ARCHIVE)])
    payload = json.loads(ARCHIVE.read_text(encoding="utf-8"))
    assert payload["version"] == 1 and len(payload["audits"]) >= 2


def test_ctwitness_tb3_gamma_inclusion_hidden_index(cli_binary: Path) -> None:
    """Hidden gamma bundle under TB3 fixtures must pass inclusion and digest independent checks."""
    hidden_index = HIDDEN_ROOT / "audit_index.json"
    hidden_ledger = HIDDEN_ROOT / "witness_ledger_gamma.json"
    if not hidden_index.is_file():
        pytest.skip("hidden index missing")
    os.environ["TB3_AUDIT_INDEX"] = str(hidden_index)
    os.environ["TB3_WITNESS_LEDGER"] = str(hidden_ledger)
    try:
        ROWS.parent.mkdir(parents=True, exist_ok=True)
        ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
        for path in (ROWS, ARCHIVE):
            if path.exists():
                path.unlink()
        run(
            [
                str(cli_binary),
                "stage",
                "--audit-index",
                str(hidden_index),
                "--witness-ledger",
                str(hidden_ledger),
                "--staging",
                str(ROWS),
            ]
        )
        run([str(cli_binary), "seal", "--staging", str(ROWS), "--out", str(ARCHIVE)])
        data = json.loads(ARCHIVE.read_text(encoding="utf-8"))
        ref = independent_sealed_bundle(hidden_index, hidden_ledger)
        gamma = next(a for a in data["audits"] if a["log_id"] == "gamma")
        assert gamma["inclusion_ok"] and data["bundle_digest"] == ref["bundle_digest"]
    finally:
        os.environ.pop("TB3_AUDIT_INDEX", None)
        os.environ.pop("TB3_WITNESS_LEDGER", None)


def test_ctwitness_tb3_gamma_witness_quorum(cli_binary: Path) -> None:
    """Hidden gamma ledger must require witness quorum agreement independent of bundled fixtures."""
    hidden_index = HIDDEN_ROOT / "audit_index.json"
    hidden_ledger = HIDDEN_ROOT / "witness_ledger_gamma.json"
    if not hidden_ledger.is_file():
        pytest.skip("hidden ledger missing")
    os.environ["TB3_AUDIT_INDEX"] = str(hidden_index)
    os.environ["TB3_WITNESS_LEDGER"] = str(hidden_ledger)
    try:
        for path in (ROWS, ARCHIVE):
            if path.exists():
                path.unlink()
        run(
            [
                str(cli_binary),
                "stage",
                "--audit-index",
                str(hidden_index),
                "--witness-ledger",
                str(hidden_ledger),
                "--staging",
                str(ROWS),
            ]
        )
        run([str(cli_binary), "seal", "--staging", str(ROWS), "--out", str(ARCHIVE)])
        gamma = next(
            a
            for a in json.loads(ARCHIVE.read_text(encoding="utf-8"))["audits"]
            if a["log_id"] == "gamma"
        )
        assert gamma["witness_quorum_ok"] is True
    finally:
        os.environ.pop("TB3_AUDIT_INDEX", None)
        os.environ.pop("TB3_WITNESS_LEDGER", None)

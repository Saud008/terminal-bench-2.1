"""Matrix-driven compacted-topic curator contract tests."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from compact_segment_refmath import (
    load_records,
    reference_compact,
    reference_findings,
    reference_staging,
)
from kcompact_shell_ops import (
    BIN,
    BUNDLED_FIXTURES,
    OFF_CATALOG_FIXTURES,
    PATHS,
    TOPIC_SLUG,
    drive_full_curator_run,
    exec_kcompact,
    ingest_only,
    parse_jsonl_file,
    wipe_workspace,
)

MATRIX = json.loads((Path(__file__).parent / "compact_scenario_matrix.json").read_text(encoding="utf-8"))


def _matrix_cases(phase: str) -> list[dict]:
    return [row for row in MATRIX["bundled"] if row["phase"] == phase]


@pytest.mark.parametrize("row", _matrix_cases("staging_digest"), ids=lambda r: r["scenario"])
def test_kcompact_matrix_staging_digest(row: dict) -> None:
    """Frozen staging digest matches verifier refmath per frozen-segment-staging.md."""
    wipe_workspace()
    ingest_only(row["scenario"])
    body = json.loads(PATHS["staging"].read_text(encoding="utf-8"))
    ref = reference_staging(TOPIC_SLUG, row["scenario"], BUNDLED_FIXTURES)
    assert body["staging_digest"] == ref["staging_digest"]


@pytest.mark.parametrize("row", _matrix_cases("full_export"), ids=lambda r: r["scenario"])
def test_kcompact_matrix_full_export_golden(row: dict) -> None:
    """Snapshot and lineage JSONL match independent compact refmath for scenario."""
    wipe_workspace()
    drive_full_curator_run(row["scenario"])
    recs = load_records(BUNDLED_FIXTURES, row["scenario"])
    snap, lin = reference_compact(recs)
    assert parse_jsonl_file(PATHS["snapshot"]) == snap
    assert parse_jsonl_file(PATHS["lineage"]) == lin


def test_kcompact_matrix_load_flag_guard() -> None:
    """pull-segments rejects missing required flags per cli-surface.md."""
    wipe_workspace()
    proc = exec_kcompact([BIN, "pull-segments"])
    assert proc.returncode != 0
    assert isinstance(proc, subprocess.CompletedProcess)


def test_kcompact_matrix_seal_increments() -> None:
    """audit-log bumps curator_seal in compact-curator-seal.json."""
    wipe_workspace()
    drive_full_curator_run("clean-compact")
    seal = json.loads(PATHS["seal"].read_text(encoding="utf-8"))
    assert seal["curator_seal"] >= 1


def test_kcompact_matrix_emit_blocked_without_seal() -> None:
    """publish-keys fails when curator_seal is zero per publish-keys-contract.md."""
    wipe_workspace()
    ingest_only("clean-compact")
    proc = exec_kcompact([BIN, "publish-keys", "--topic", TOPIC_SLUG, "--scenario", "clean-compact"])
    assert proc.returncode != 0


@pytest.mark.parametrize("row", _matrix_cases("audit_only"), ids=lambda r: r["scenario"])
def test_kcompact_matrix_audit_rows(row: dict) -> None:
    """Segment audit findings match reference reconcile math for scenario."""
    wipe_workspace()
    ingest_only(row["scenario"])
    exec_kcompact([BIN, "audit-log", "--topic", TOPIC_SLUG, "--scenario", row["scenario"]])
    findings = json.loads(PATHS["audit"].read_text(encoding="utf-8"))
    recs = load_records(BUNDLED_FIXTURES, row["scenario"])
    assert findings["findings"] == reference_findings(recs)


def test_kcompact_matrix_seg_order_early_before_late() -> None:
    """Numeric segment ordering places seg_002 records before seg_010 records."""
    wipe_workspace()
    ingest_only("seg-order")
    body = json.loads(PATHS["staging"].read_text(encoding="utf-8"))
    keys = [r["canonical_key"] for r in body["records"]]
    assert keys.index("order:early") < keys.index("order:late")


def test_kcompact_matrix_repeat_emit_bytes_stable() -> None:
    """Repeat publish-keys emits byte-identical snapshot and lineage files."""
    wipe_workspace()
    drive_full_curator_run("idempotent-export")
    snap_bytes = PATHS["snapshot"].read_bytes()
    lin_bytes = PATHS["lineage"].read_bytes()
    proc = exec_kcompact([BIN, "publish-keys", "--topic", TOPIC_SLUG, "--scenario", "idempotent-export"])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert PATHS["snapshot"].read_bytes() == snap_bytes
    assert PATHS["lineage"].read_bytes() == lin_bytes


@pytest.mark.parametrize("row", _matrix_cases("field_probe"), ids=lambda r: f"{r['scenario']}-{r['key']}")
def test_kcompact_matrix_snapshot_field_probe(row: dict) -> None:
    """Snapshot row field matches publish-keys-contract for matrix probe row."""
    wipe_workspace()
    drive_full_curator_run(row["scenario"])
    hit = next(r for r in parse_jsonl_file(PATHS["snapshot"]) if r["canonical_key"] == row["key"])
    assert hit[row["field"]] == row["expect"]


@pytest.mark.parametrize("row", _matrix_cases("lineage_contains"), ids=lambda r: r["scenario"])
def test_kcompact_matrix_lineage_contains_key(row: dict) -> None:
    """Tombstone lineage JSONL includes expected canonical key for scenario."""
    wipe_workspace()
    drive_full_curator_run(row["scenario"])
    assert any(r["canonical_key"] == row["key"] for r in parse_jsonl_file(PATHS["lineage"]))


def test_kcompact_off_catalog_retention_bias_tb3() -> None:
    """TB3 retention window override affects audit findings and snapshot export."""
    wipe_workspace()
    env = {"TB3_FIXTURE_DIR": str(OFF_CATALOG_FIXTURES), "TB3_TOMB_RETENTION_MS": "50000"}
    ingest_only("retention-bias", fixture_root=OFF_CATALOG_FIXTURES, extra_env=env)
    exec_kcompact([BIN, "audit-log", "--topic", TOPIC_SLUG, "--scenario", "retention-bias"], env=env)
    findings = json.loads(PATHS["audit"].read_text(encoding="utf-8"))
    recs = load_records(OFF_CATALOG_FIXTURES, "retention-bias")
    assert findings["findings"] == reference_findings(recs, window=50000)
    exec_kcompact([BIN, "publish-keys", "--topic", TOPIC_SLUG, "--scenario", "retention-bias"], env=env)
    snap, _ = reference_compact(recs, window=50000)
    assert parse_jsonl_file(PATHS["snapshot"]) == snap


def test_kcompact_off_catalog_canonical_nfc_tb3() -> None:
    """Off-catalog NFC key trap collapses to refmath canonical_key in snapshot."""
    wipe_workspace()
    env = {"TB3_FIXTURE_DIR": str(OFF_CATALOG_FIXTURES)}
    ingest_only("canonical-trap", fixture_root=OFF_CATALOG_FIXTURES, extra_env=env)
    exec_kcompact([BIN, "audit-log", "--topic", TOPIC_SLUG, "--scenario", "canonical-trap"], env=env)
    exec_kcompact([BIN, "publish-keys", "--topic", TOPIC_SLUG, "--scenario", "canonical-trap"], env=env)
    recs = load_records(OFF_CATALOG_FIXTURES, "canonical-trap")
    snap, _ = reference_compact(recs)
    assert parse_jsonl_file(PATHS["snapshot"]) == snap


def test_kcompact_matrix_snapshot_keys_sorted() -> None:
    """topic-key-snapshot.jsonl rows sort by canonical_key per byte-stable-publish-contract."""
    wipe_workspace()
    drive_full_curator_run("idempotent-export")
    keys = [r["canonical_key"] for r in parse_jsonl_file(PATHS["snapshot"])]
    assert keys == sorted(keys)


def test_kcompact_matrix_bundled_catalog_non_empty() -> None:
    """Scenario matrix declares at least seven bundled compact-log scenarios."""
    assert len({r["scenario"] for r in MATRIX["bundled"]}) >= 7


def test_kcompact_matrix_staging_path_absolute() -> None:
    """Staging artifact path is the absolute frozen snapshot location from instruction."""
    assert str(PATHS["staging"]) == "/app/state/frozen-segment-snapshot.json"


def test_kcompact_matrix_seal_path_absolute() -> None:
    """Curator seal path is the absolute compact-curator-seal.json from instruction."""
    assert str(PATHS["seal"]) == "/app/state/compact-curator-seal.json"


def test_kcompact_matrix_audit_path_absolute() -> None:
    """Audit report path is the absolute segment-audit-report.json from instruction."""
    assert str(PATHS["audit"]) == "/app/work/segment-audit-report.json"


def test_kcompact_matrix_snapshot_path_absolute() -> None:
    """Snapshot export path is the absolute topic-key-snapshot.jsonl from instruction."""
    assert str(PATHS["snapshot"]) == "/app/output/topic-key-snapshot.jsonl"


def test_kcompact_matrix_lineage_path_absolute() -> None:
    """Lineage export path is the absolute tombstone-lineage.jsonl from instruction."""
    assert str(PATHS["lineage"]) == "/app/output/tombstone-lineage.jsonl"

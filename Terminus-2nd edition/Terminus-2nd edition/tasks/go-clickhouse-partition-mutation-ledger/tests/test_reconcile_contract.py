"""Reconcile-partitions staging contract tests for chmutled."""
from __future__ import annotations

import json

from chledger_shell_ops import (
    BIN,
    PATHS,
    exec_chledger,
    fixture_dirs,
    rebuild_binary,
    run_full_pipeline,
    wipe_workspace,
)
from readiness_refmath import reference_reconcile_rows


def test_8a3f2e1b_chledger_binary_present() -> None:
    """rebuild-chledger.sh must emit /app/bin/chmutled."""
    rebuild_binary()
    assert BIN.is_file()


def test_8a3f2e1b_reconcile_writes_chledger_staging() -> None:
    """reconcile-partitions must materialize /app/state/chledger-staging.jsonl."""
    run_full_pipeline()
    assert PATHS["staging"].is_file()
    lines = [ln for ln in PATHS["staging"].read_text(encoding="utf-8").splitlines() if ln.strip()]
    assert len(lines) >= 4


def test_8a3f2e1b_staging_row_order_contract() -> None:
    """staging_pipeline.md sorts by partition_id then mutation_version."""
    run_full_pipeline()
    rows = [json.loads(ln) for ln in PATHS["staging"].read_text(encoding="utf-8").splitlines() if ln.strip()]
    keys = [(r["partition_id"], r["mutation_version"]) for r in rows]
    assert keys == sorted(keys)


def test_8a3f2e1b_version_ladder_ten_beats_nine() -> None:
    """mutation_version_ordering.md must retain version 10 after 9 with numeric peak 10."""
    run_full_pipeline()
    pid = "events|month=2024-01|region=eu"
    rows = [json.loads(ln) for ln in PATHS["staging"].read_text(encoding="utf-8").splitlines() if ln.strip()]
    ladder = [r for r in rows if r["partition_id"] == pid]
    versions = [r["mutation_version"] for r in ladder]
    assert versions == sorted(versions)
    assert max(versions) == 10
    ref = reference_reconcile_rows(*fixture_dirs())
    ref_peak = max(r["mutation_version"] for r in ref if r["partition_id"] == pid)
    assert ref_peak == 10


def test_8a3f2e1b_lag_suppression_strict_gt() -> None:
    """replica_lag_suppression.md suppresses only when lag strictly exceeds threshold."""
    run_full_pipeline()
    rows = [json.loads(ln) for ln in PATHS["staging"].read_text(encoding="utf-8").splitlines() if ln.strip()]
    alpha = [r for r in rows if r["partition_id"] == "events|month=2024-01|region=eu"]
    assert max(r["replica_lag_max"] for r in alpha) == 130
    assert all(r["readiness_state"] == "suppressed" for r in alpha)


def test_8a3f2e1b_metrics_threshold_edge_ready() -> None:
    """lag equal to max_lag_sec must remain ready on metrics shard."""
    run_full_pipeline()
    pid = "metrics|day=2024-06-10|shard=s2"
    row = next(
        json.loads(ln)
        for ln in PATHS["staging"].read_text(encoding="utf-8").splitlines()
        if ln.strip() and json.loads(ln)["partition_id"] == pid
    )
    assert row["replica_lag_max"] == 120
    assert row["readiness_state"] == "ready"


def test_8a3f2e1b_detached_partition_excluded() -> None:
    """detached_part_handling.md marks detached rows on us events partition."""
    run_full_pipeline()
    pid = "events|month=2024-02|region=us"
    row = next(
        json.loads(ln)
        for ln in PATHS["staging"].read_text(encoding="utf-8").splitlines()
        if ln.strip() and json.loads(ln)["partition_id"] == pid
    )
    assert row["readiness_state"] == "detached"


def test_8a3f2e1b_reconcile_matches_refmath() -> None:
    """full reconcile output must match readiness_refmath independent rows."""
    run_full_pipeline()
    meta, mut, rep = fixture_dirs()
    got = [json.loads(ln) for ln in PATHS["staging"].read_text(encoding="utf-8").splitlines() if ln.strip()]
    ref = reference_reconcile_rows(meta, mut, rep)
    assert len(got) == len(ref)
    for g, e in zip(got, ref):
        assert g == e


def test_8a3f2e1b_reconcile_empty_inputs(tmp_path) -> None:
    """empty fixture directories produce empty staging without error."""
    rebuild_binary()
    empty = tmp_path / "blank"
    for name in ("metadata", "mutations", "replicas"):
        (empty / name).mkdir(parents=True)
    wipe_workspace()
    proc = exec_chledger([
        "reconcile-partitions",
        "--metadata-dir", str(empty / "metadata"),
        "--mutations-dir", str(empty / "mutations"),
        "--replica-dir", str(empty / "replicas"),
        "--config-dir", str(PATHS["config"]),
        "--staging", str(PATHS["staging"]),
    ])
    assert proc.returncode == 0
    assert PATHS["staging"].read_text(encoding="utf-8").strip() == ""

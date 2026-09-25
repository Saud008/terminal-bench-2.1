"""Primary emit-readiness and hidden-trap verifier contracts for chmutled."""
from __future__ import annotations

import json
import sqlite3
import subprocess
from pathlib import Path

import pytest
from chledger_shell_ops import (
    BIN,
    HIDDEN_ROOT,
    PATHS,
    exec_chledger,
    fixture_dirs,
    rebuild_binary,
    run_full_pipeline,
    wipe_workspace,
)
from readiness_refmath import (
    config_bundle_digest,
    load_policy_bundle,
    reference_reconcile_rows,
)


def test_t8d9473_8a3f2e1b_export_reads_staging_not_ingest_only() -> None:
    """After reconcile ingest completes, export emit must read staging without re-ingest."""
    run_full_pipeline()
    staging_mtime = PATHS["staging"].stat().st_mtime
    proc = exec_chledger([
        "emit-readiness",
        "--staging", str(PATHS["staging"]),
        "--sqlite", str(PATHS["sqlite"]),
        "--atlas", str(PATHS["atlas"]),
    ])
    assert proc.returncode == 0
    atlas = json.loads(PATHS["atlas"].read_text(encoding="utf-8"))
    assert atlas["totals"]["mutation_count"] >= 4
    assert PATHS["staging"].stat().st_mtime >= staging_mtime


def test_t8d9473_8a3f2e1b_emit_writes_atlas_and_sqlite() -> None:
    """emit-readiness must write atlas JSON and chledger-rows.sqlite."""
    run_full_pipeline()
    assert PATHS["atlas"].is_file()
    assert PATHS["sqlite"].is_file()
    body = json.loads(PATHS["atlas"].read_text(encoding="utf-8"))
    assert "mutations" in body and "totals" in body


def test_t8d9473_8a3f2e1b_atlas_anchor_passthrough() -> None:
    """mutation_readiness_export.md copies anchor_utc from config anchor.txt."""
    run_full_pipeline()
    atlas = json.loads(PATHS["atlas"].read_text(encoding="utf-8"))
    assert atlas["anchor_utc"] == load_policy_bundle()["anchor"]


def test_t8d9473_8a3f2e1b_atlas_mutation_sort_keys() -> None:
    """readiness atlas mutations sorted by partition_id then mutation_version."""
    run_full_pipeline()
    atlas = json.loads(PATHS["atlas"].read_text(encoding="utf-8"))
    keys = [(m["partition_id"], m["mutation_version"]) for m in atlas["mutations"]]
    assert keys == sorted(keys)


def test_t8d9473_8a3f2e1b_totals_bucket_counts() -> None:
    """totals must count readiness_state buckets across atlas mutations."""
    run_full_pipeline()
    atlas = json.loads(PATHS["atlas"].read_text(encoding="utf-8"))
    muts = atlas["mutations"]
    totals = atlas["totals"]
    assert totals["mutation_count"] == len(muts)
    assert totals["ready_count"] == sum(1 for m in muts if m["readiness_state"] == "ready")
    assert totals["suppressed_count"] == sum(1 for m in muts if m["readiness_state"] == "suppressed")
    assert totals["detached_count"] == sum(1 for m in muts if m["readiness_state"] == "detached")


def test_t8d9473_8a3f2e1b_sqlite_row_count_floor() -> None:
    """mutation_ledger table must contain at least four reconciled rows."""
    run_full_pipeline()
    conn = sqlite3.connect(PATHS["sqlite"])
    try:
        count = conn.execute("SELECT COUNT(*) FROM mutation_ledger").fetchone()[0]
    finally:
        conn.close()
    assert count >= 4


def test_t8d9473_8a3f2e1b_emit_idempotent_sqlite_upsert() -> None:
    """repeated emit-readiness must not grow sqlite row count for same staging."""
    run_full_pipeline()
    conn = sqlite3.connect(PATHS["sqlite"])
    first = conn.execute("SELECT COUNT(*) FROM mutation_ledger").fetchone()[0]
    conn.close()
    proc = exec_chledger([
        "emit-readiness",
        "--staging", str(PATHS["staging"]),
        "--sqlite", str(PATHS["sqlite"]),
        "--atlas", str(PATHS["atlas"]),
    ])
    assert proc.returncode == 0
    conn = sqlite3.connect(PATHS["sqlite"])
    second = conn.execute("SELECT COUNT(*) FROM mutation_ledger").fetchone()[0]
    conn.close()
    assert first == second


def test_t8d9473_8a3f2e1b_emit_without_staging_errors() -> None:
    """emit-readiness must fail when staging file is missing."""
    rebuild_binary()
    wipe_workspace()
    result = subprocess.run(
        [
            str(BIN), "emit-readiness",
            "--staging", str(PATHS["staging"]),
            "--sqlite", str(PATHS["sqlite"]),
            "--atlas", str(PATHS["atlas"]),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0


def test_t8d9473_8a3f2e1b_config_bundle_digest_stable() -> None:
    """bundled config digest must be 64 hex chars."""
    assert len(config_bundle_digest()) == 64
    load_policy_bundle()


def test_t8d9473_8a3f2e1b_hidden_tb3_lag_suppression(monkeypatch: pytest.MonkeyPatch) -> None:
    """TB3_FIXTURE_ROOT hidden replica lag 121 must suppress ap partition."""
    if not HIDDEN_ROOT.is_dir():
        pytest.skip("hidden fixtures not mounted")
    monkeypatch.setenv("TB3_FIXTURE_ROOT", str(HIDDEN_ROOT))
    run_full_pipeline()
    pid = "events|month=2024-03|region=ap"
    rows = [json.loads(ln) for ln in PATHS["staging"].read_text(encoding="utf-8").splitlines() if ln.strip()]
    row = next(r for r in rows if r["partition_id"] == pid)
    assert row["replica_lag_max"] == 121
    assert row["readiness_state"] == "suppressed"


def test_t8d9473_8a3f2e1b_hidden_trap_differs_from_bundled(monkeypatch: pytest.MonkeyPatch) -> None:
    """hidden partition id must not appear in bundled reconcile refmath."""
    if not HIDDEN_ROOT.is_dir():
        pytest.skip("hidden fixtures not mounted")
    bundled = reference_reconcile_rows(
        Path("/app/fixtures/metadata"),
        Path("/app/fixtures/mutations"),
        Path("/app/fixtures/replicas"),
    )
    hidden = reference_reconcile_rows(
        HIDDEN_ROOT / "metadata",
        HIDDEN_ROOT / "mutations",
        HIDDEN_ROOT / "replicas",
    )
    assert len(hidden) == 1
    assert hidden[0]["readiness_state"] == "suppressed"
    bundled_ids = {r["partition_id"] for r in bundled}
    assert hidden[0]["partition_id"] not in bundled_ids


def test_t8d9473_8a3f2e1b_hidden_refmath_pipeline_match(monkeypatch: pytest.MonkeyPatch) -> None:
    """hidden TB3 pipeline output must match readiness_refmath rows."""
    if not HIDDEN_ROOT.is_dir():
        pytest.skip("hidden fixtures not mounted")
    monkeypatch.setenv("TB3_FIXTURE_ROOT", str(HIDDEN_ROOT))
    run_full_pipeline()
    meta, mut, rep = fixture_dirs()
    got = [json.loads(ln) for ln in PATHS["staging"].read_text(encoding="utf-8").splitlines() if ln.strip()]
    ref = reference_reconcile_rows(meta, mut, rep)
    assert got == ref

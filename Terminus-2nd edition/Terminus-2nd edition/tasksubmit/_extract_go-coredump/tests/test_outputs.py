"""Behavioral verifier for go-coredump-buildid-symbolization-indexer."""
from __future__ import annotations

import json
import sqlite3
import subprocess
from pathlib import Path

from coreidx_cli import (
    CLI_BIN,
    DEFAULT_CATALOG,
    STATE,
    SQLITE,
    SUMMARY,
    catalog_for,
    crash_dir,
    pipeline,
    rebuild,
    reset,
    run,
)
from coreidx_verifier_lib import reference_stage_rows

HIDDEN_ROOT = Path("/opt/verifier-fixtures/coreidx_hidden")
STAGING_PATH = "/app/state/crash_staging.jsonl"
ALT_STAGING_PATH = "/app/state/alt_staging.jsonl"
SQLITE_PATH = "/app/output/crash_index.sqlite"
SUMMARY_PATH = "/app/output/crash_summary.json"


def load_summary() -> dict:
    return json.loads(SUMMARY.read_text(encoding="utf-8"))


def load_staging() -> list[dict]:
    return [json.loads(line) for line in STATE.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_t1066c1_coreidx_binary_rebuilds():
    """Instruction pipeline step 1: verifier-rebuild.sh must produce /app/bin/coreidx."""
    rebuild()
    assert CLI_BIN.is_file()


def test_t1066c1_coreidx_ingest_export_produces_artifacts():
    """Instruction pipeline steps 2-3: ingest and export write staging, sqlite, and summary paths."""
    rebuild()
    pipeline()
    assert STATE.is_file() and SQLITE.is_file() and SUMMARY.is_file()


def test_t1066c1_coreidx_summary_has_groups_and_totals():
    """crash_summary.json contract: top-level groups and totals keys per sqlite_export_schema.md."""
    rebuild()
    pipeline()
    data = load_summary()
    assert "groups" in data and "totals" in data


def test_t1066c1_coreidx_group_total_matches_row_count():
    """totals.group_count must equal len(groups) per sqlite_export_schema.md."""
    rebuild()
    pipeline()
    data = load_summary()
    assert data["totals"]["group_count"] == len(data["groups"])


def test_t1066c1_coreidx_groups_sorted_lexicographic():
    """Export must sort crash groups by group_key lexicographically."""
    rebuild()
    pipeline()
    keys = [g["group_key"] for g in load_summary()["groups"]]
    assert keys == sorted(keys)


def test_t1066c1_coreidx_staging_order_timestamp_crash_id():
    """staging_pipeline.md: rows sorted by timestamp then crash_id tiebreak."""
    rebuild()
    pipeline()
    staged = load_staging()
    ref = reference_stage_rows(crash_dir(), catalog_for(crash_dir()))
    assert [s["crash_id"] for s in staged] == [r["crash_id"] for r in ref]


def test_t1066c1_coreidx_stripped_fallback_resolves_worker():
    """stripped_fallback.md: c-alpha-001 resolves main.worker with build_id A1B2C3D4E5F60718."""
    rebuild()
    pipeline()
    staged = {r["crash_id"]: r for r in load_staging()}
    assert staged["c-alpha-001"]["top_symbol"] == "main.worker"
    assert staged["c-alpha-001"]["build_id"] == "A1B2C3D4E5F60718"


def test_t1066c1_coreidx_duplicate_alpha_crashes_one_group():
    """dedupe_grouping.md: duplicate c-alpha crashes share one group_key."""
    rebuild()
    pipeline()
    alpha = [r for r in load_staging() if r["crash_id"].startswith("c-alpha")]
    assert len(alpha) == 2
    assert alpha[0]["group_key"] == alpha[1]["group_key"]


def test_t1066c1_coreidx_libhelper_mmap_tiebreak_symbol():
    """mmap_range_matching.md: c-bravo-lib frame resolves helper.run symbol."""
    rebuild()
    pipeline()
    staged = {r["crash_id"]: r for r in load_staging()}
    assert staged["c-bravo-lib"]["top_symbol"] == "helper.run"


def test_t1066c1_coreidx_half_open_boundary_resolves_crash():
    """mmap_range_matching.md: half-open interval lets c-charlie-edge resolve main.crash."""
    rebuild()
    pipeline()
    staged = {r["crash_id"]: r for r in load_staging()}
    assert staged["c-charlie-edge"]["top_symbol"] == "main.crash"


def test_t1066c1_coreidx_summary_build_ids_uppercase():
    """elf_buildid_notes.md: exported build_id values are uppercase hex without prefix."""
    rebuild()
    pipeline()
    for g in load_summary()["groups"]:
        if g["build_id"]:
            assert g["build_id"] == g["build_id"].upper()


def test_t1066c1_coreidx_sqlite_group_row_count():
    """sqlite_export_schema.md: crash_groups row count matches totals.group_count."""
    rebuild()
    pipeline()
    con = sqlite3.connect(SQLITE)
    count = con.execute("SELECT COUNT(*) FROM crash_groups").fetchone()[0]
    con.close()
    assert count == load_summary()["totals"]["group_count"]


def test_t1066c1_coreidx_sqlite_frame_row_count():
    """sqlite_export_schema.md: crash_frames rows cover every staged frame."""
    rebuild()
    pipeline()
    con = sqlite3.connect(SQLITE)
    n = con.execute("SELECT COUNT(*) FROM crash_frames").fetchone()[0]
    con.close()
    assert n == sum(len(s["frames"]) for s in load_staging())


def test_t1066c1_coreidx_staging_matches_independent_reference():
    """Independent reference engine must match staged crash_id, group_key, build_id, top_symbol."""
    rebuild()
    pipeline()
    staged = load_staging()
    ref = reference_stage_rows(crash_dir(), catalog_for(crash_dir()))
    assert len(staged) == len(ref)
    for got, exp in zip(staged, ref):
        assert got["crash_id"] == exp["crash_id"]
        assert got["group_key"] == exp["group_key"]
        assert got["build_id"] == exp["build_id"]
        assert got["top_symbol"] == exp["top_symbol"]


def test_t1066c1_coreidx_tb3_hidden_crash_ingested(monkeypatch):
    """staging_pipeline.md TB3 override: hidden bundle crash c-hidden-delta is ingested."""
    rebuild()
    hidden_crashes = HIDDEN_ROOT / "crashes"
    if not hidden_crashes.is_dir():
        import pytest

        pytest.skip("hidden fixtures not mounted")
    monkeypatch.setenv("TB3_CRASH_DIR", str(hidden_crashes))
    pipeline(hidden_crashes)
    assert any(r["crash_id"] == "c-hidden-delta" for r in load_staging())


def test_t1066c1_coreidx_tb3_hidden_group_key_reference(monkeypatch):
    """TB3 hidden bundle group_key must match independent reference for c-hidden-delta."""
    rebuild()
    hidden_crashes = HIDDEN_ROOT / "crashes"
    if not hidden_crashes.is_dir():
        import pytest

        pytest.skip("hidden fixtures not mounted")
    monkeypatch.setenv("TB3_CRASH_DIR", str(hidden_crashes))
    pipeline(hidden_crashes)
    ref = reference_stage_rows(hidden_crashes, catalog_for(hidden_crashes))
    assert load_staging()[0]["group_key"] == ref[0]["group_key"]


def test_t1066c1_coreidx_export_without_staging_errors():
    """cli_surface.md: export without prior ingest staging file must fail non-zero."""
    rebuild()
    reset()
    result = subprocess.run(
        [str(CLI_BIN), "export", "--staging", str(STATE), "--sqlite", str(SQLITE), "--summary", str(SUMMARY)],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "staging" in (result.stderr + result.stdout).lower() or not STATE.is_file()


def test_t1066c1_coreidx_cli_ingest_only_then_export():
    """cli_surface.md: ingest-only then export on alternate staging path is supported."""
    rebuild()
    crashes = crash_dir()
    alt_staging = Path(ALT_STAGING_PATH)
    if alt_staging.exists():
        alt_staging.unlink()
    run([str(CLI_BIN), "ingest", "--crash-dir", str(crashes), "--catalog", str(catalog_for(crashes)), "--staging", str(alt_staging)])
    run([str(CLI_BIN), "export", "--staging", str(alt_staging), "--sqlite", str(SQLITE), "--summary", str(SUMMARY)])
    assert load_summary()["totals"]["group_count"] >= 2


def test_t1066c1_coreidx_decoy_not_in_summary_output():
    """Instruction decoy rule: internal/decoy scalemillis helper must not appear in summary JSON."""
    rebuild()
    pipeline()
    raw = SUMMARY.read_text(encoding="utf-8")
    assert "scalemillis" not in raw.lower()


def test_t1066c1_coreidx_ingest_empty_directory_writes_empty_staging(tmp_path):
    """crash_bundle_format.md: ingest on empty crash directory writes zero-line staging file."""
    rebuild()
    empty = tmp_path / "empty"
    empty.mkdir()
    reset()
    result = subprocess.run(
        [str(CLI_BIN), "ingest", "--crash-dir", str(empty), "--catalog", str(DEFAULT_CATALOG), "--staging", str(STATE)],
        capture_output=True,
    )
    assert result.returncode == 0

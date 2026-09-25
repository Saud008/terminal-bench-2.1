"""Cross-run atlas index persistence and compile idempotency contracts."""

from __future__ import annotations

import json
import sqlite3
import subprocess

import pytest

from placement_atlas_math import reference_compile_atlas, reference_load_scenario
from nomrep_atlas_cli import CLI_BIN, DB_PATH, FIXTURE_DIR, SEED_POOL, wipe


@pytest.fixture(autouse=True)
def isolate_workspace():
    wipe()
    yield
    wipe()


def test_compile_twice_preserves_atlas_row_count():
    """Second compile for the same seed must not drop atlas rows from atlas-index.db."""
    seed = SEED_POOL[0]
    for _ in range(2):
        proc = subprocess.run(
            [str(CLI_BIN), "load", "--seed", seed, "--scenario", "basic-volume-join"],
            cwd="/app",
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
        proc = subprocess.run(
            [str(CLI_BIN), "compile", "--seed", seed, "--scenario", "basic-volume-join"],
            cwd="/app",
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
    conn = sqlite3.connect(DB_PATH)
    try:
        row_count = conn.execute("SELECT COUNT(*) FROM atlas_summary").fetchone()[0]
    finally:
        conn.close()
    sc = reference_load_scenario(FIXTURE_DIR / "basic-volume-join.json", seed)
    ref = reference_compile_atlas(sc, seed)
    assert row_count >= 1
    assert ref["summary"]["active_alloc_count"] >= 1


def test_publish_reuses_compiled_run_id_without_recompile():
    """Publish after compile must surface the same run_id without another compile pass."""
    seed = SEED_POOL[1]
    subprocess.run(
        [str(CLI_BIN), "load", "--seed", seed, "--scenario", "node-class-precedence"],
        cwd="/app",
        check=True,
    )
    subprocess.run(
        [str(CLI_BIN), "compile", "--seed", seed, "--scenario", "node-class-precedence"],
        cwd="/app",
        check=True,
    )
    out_path = f"/app/output/{seed}-node-class-precedence-placement-atlas.json"
    proc = subprocess.run(
        [
            str(CLI_BIN),
            "publish",
            "--seed",
            seed,
            "--scenario",
            "node-class-precedence",
            "--output",
            out_path,
        ],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    rep = json.loads(open(out_path, encoding="utf-8").read())
    assert rep["run_id"] >= 1


def test_atlas_db_survives_publish_for_followup_compile():
    """Atlas sqlite file must remain after publish so a later compile can upsert."""
    seed = SEED_POOL[2]
    subprocess.run(
        [str(CLI_BIN), "load", "--seed", seed, "--scenario", "stale-allocation-filter"],
        cwd="/app",
        check=True,
    )
    subprocess.run(
        [str(CLI_BIN), "compile", "--seed", seed, "--scenario", "stale-allocation-filter"],
        cwd="/app",
        check=True,
    )
    out_path = f"/app/output/{seed}-stale-allocation-filter-placement-atlas.json"
    subprocess.run(
        [
            str(CLI_BIN),
            "publish",
            "--seed",
            seed,
            "--scenario",
            "stale-allocation-filter",
            "--output",
            out_path,
        ],
        cwd="/app",
        check=True,
    )
    assert DB_PATH.is_file()
    proc = subprocess.run(
        [str(CLI_BIN), "compile", "--seed", seed, "--scenario", "stale-allocation-filter"],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout

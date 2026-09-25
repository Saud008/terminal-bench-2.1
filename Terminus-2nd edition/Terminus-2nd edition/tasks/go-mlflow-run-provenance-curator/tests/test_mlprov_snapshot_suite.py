"""Snapshot and bind persistence checks."""

from __future__ import annotations

import json
import sqlite3

import pytest
from mlprov_cli_support import (
    APP_ROOT,
    CLI_BIN,
    DB_PATH,
    FIXTURE_DIR,
    SEED_POOL,
    SNAP_PATH,
    invoke,
    run_curator,
    wipe,
)
from mlprov_contract_math import reference_curate, reference_load_scenario


@pytest.fixture(autouse=True)
def isolate_workspace():
    wipe()
    yield
    wipe()


def test_cli_binary_installed_at_usr_local():
    """The built mlprov binary must be installed at /usr/local/bin/mlprov."""
    assert CLI_BIN.is_file()



def test_fixture_catalog_on_disk():
    """Bundled scenario fixtures must remain available under /app/fixtures/scenarios."""
    assert FIXTURE_DIR.is_dir()
    assert (FIXTURE_DIR / "basic-lineage.json").is_file()



def test_snapshot_materializes_required_fields():
    """ingest must write seed, scenario, manifests, runs, and focus metadata into the staging snapshot."""
    seed = SEED_POOL[0]
    proc = invoke([str(CLI_BIN), "ingest", "--seed", seed, "--scenario", "basic-lineage"])
    assert proc.returncode == 0
    snap = json.loads(SNAP_PATH.read_text(encoding="utf-8"))
    assert snap["seed"] == seed
    assert snap["scenario"] == "basic-lineage"
    assert "ingest_seq" in snap and isinstance(snap["ingest_seq"], int)
    assert snap.get("focus_run_id")
    assert "dataset_manifests" in snap
    assert snap.get("runs")
    assert any(r.get("artifacts") for r in snap["runs"])



def test_snapshot_seq_advances_monotonically():
    """Repeated ingest for the same seed must increment ingest_seq in the staging snapshot."""
    seed = SEED_POOL[0]
    invoke([str(CLI_BIN), "ingest", "--seed", seed, "--scenario", "basic-lineage"])
    first = json.loads(SNAP_PATH.read_text(encoding="utf-8"))["ingest_seq"]
    invoke([str(CLI_BIN), "ingest", "--seed", seed, "--scenario", "basic-lineage"])
    second = json.loads(SNAP_PATH.read_text(encoding="utf-8"))["ingest_seq"]
    assert second == first + 1



def test_snapshot_lives_under_app_state():
    """The documented staging snapshot path must be /app/state/provenance-staging.json."""
    invoke([str(CLI_BIN), "ingest", "--seed", SEED_POOL[0], "--scenario", "basic-lineage"])
    assert SNAP_PATH.name == "provenance-staging.json"
    assert SNAP_PATH.parent == APP_ROOT / "state"
    assert SNAP_PATH.is_file()



def test_bind_writes_curation_runs_row():
    """curate bind must persist a curation_runs row in /app/work/provenance.db."""
    seed = SEED_POOL[0]
    run_curator(seed, "basic-lineage")
    assert DB_PATH.is_file()
    con = sqlite3.connect(DB_PATH)
    cur = con.execute("SELECT COUNT(*) FROM curation_runs")
    assert cur.fetchone()[0] == 1
    con.close()



def test_ancestry_chain_matches_contract_math():
    """lineage_chain must follow the root-first closure contract from the reference math."""
    seed = SEED_POOL[0]
    out = run_curator(seed, "basic-lineage")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = reference_load_scenario(FIXTURE_DIR / "basic-lineage.json", seed)
    ref = reference_curate(sc, seed)
    assert rep["lineage_chain"] == ref["lineage_chain"]



def test_closure_depth_matches_contract_math():
    """summary.lineage_depth must match the reference closure depth for deep lineage scenarios."""
    seed = SEED_POOL[1]
    out = run_curator(seed, "deep-lineage-bind")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = reference_load_scenario(FIXTURE_DIR / "deep-lineage-bind.json", seed)
    ref = reference_curate(sc, seed)
    assert rep["summary"]["lineage_depth"] == ref["summary"]["lineage_depth"]



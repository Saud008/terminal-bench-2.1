"""Named output path coverage for mlprov closure certificates."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from mlprov_cli_support import CLI_BIN, FIXTURE_DIR, SEED_POOL, run_curator, wipe
from mlprov_contract_math import reference_curate, reference_load_scenario


@pytest.fixture(autouse=True)
def isolate_workspace():
    wipe()
    yield
    wipe()


def test_hydrate_publishes_feature_run_snapshot_to_documented_state_path():
    """Hydrate must materialize the feature-run snapshot at /app/state/provenance-staging.json for closure math."""
    seed = SEED_POOL[0]
    staging_path = Path("/app/state/provenance-staging.json")
    proc = subprocess.run(
        [str(CLI_BIN), "ingest", "--seed", seed, "--scenario", "basic-lineage"],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    snap = json.loads(staging_path.read_text(encoding="utf-8"))
    assert snap["seed"] == seed
    assert snap["scenario"] == "basic-lineage"
    assert staging_path.is_file()


def test_publish_emits_eval_closure_certificate_beneath_documented_output_root():
    """Publish summary must write the eval closure certificate JSON under /app/output/ with lineage parity."""
    seed = SEED_POOL[0]
    out = run_curator(seed, "basic-lineage")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = reference_load_scenario(FIXTURE_DIR / "basic-lineage.json", seed)
    ref = reference_curate(sc, seed)
    assert out.is_file()
    assert str(out).startswith("/app/output/")
    assert rep["seed"] == seed
    assert rep["scenario"] == "basic-lineage"
    assert rep["lineage_chain"] == ref["lineage_chain"]


def test_publish_uses_standard_provenance_certificate_filename_suffix():
    """The closure workflow writes a provenance certificate whose filename stays under /app/output/ and ends with -provenance.json"""
    out = run_curator(SEED_POOL[1], "artifact-digest-tree")
    assert str(out).startswith("/app/output/")
    assert out.name.endswith("-provenance.json")

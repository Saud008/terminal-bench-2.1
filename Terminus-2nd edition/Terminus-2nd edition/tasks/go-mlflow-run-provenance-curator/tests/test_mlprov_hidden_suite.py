"""Hidden overlay checks."""

from __future__ import annotations

import json
import os
import shutil
import sqlite3
import tempfile
from pathlib import Path

import pytest
from mlprov_cli_support import (
    APP_ROOT,
    CLI_BIN,
    DB_PATH,
    FIXTURE_DIR,
    SEED_POOL,
    invoke,
    run_curator,
    wipe,
)
from mlprov_contract_math import (
    reference_curate,
    reference_load_scenario,
    reference_report,
)

_TB3_SCENARIO = {
    "scenario_name": "tb3-cross-bind",
    "experiment_id": "exp-fraud",
    "focus_run_id": "run-policy",
    "dataset_manifests": {
        "replay-buffer": {
            "version_hash": "rb-h7k2m",
            "row_count": 500000,
        }
    },
    "runs": [
        {
            "run_id": "run-sim",
            "parent_run_id": "",
            "params": {"source": "kafka"},
            "metrics": [],
            "artifacts": [{"rel_path": "env/config.json", "content": "{}"}],
            "dataset_pins": [],
        },
        {
            "run_id": "run-collect",
            "parent_run_id": "run-sim",
            "params": {"steps": "10000"},
            "metrics": [{"key": "episodes", "step": 1, "value": 200, "epoch": 0}],
            "artifacts": [{"rel_path": "buffer/shard-0.parquet", "content": "PAR0"}],
            "dataset_pins": [{"name": "replay-buffer", "version_hash": "rb-h7k2m"}],
        },
        {
            "run_id": "run-policy",
            "parent_run_id": "run-collect",
            "params": {"threshold": "0.82"},
            "metrics": [
                {"key": "auc", "step": 3, "value": 0.91, "epoch": 1},
                {"key": "precision", "step": 7, "value": 0.88, "epoch": 2},
            ],
            "artifacts": [
                {"rel_path": "policy/weights.npz", "content": "POLICY"},
                {"rel_path": "./policy/meta.json", "content": "{\"algo\":\"ppo\"}"},
            ],
            "dataset_pins": [
                {"name": "replay-buffer", "version_hash": "rb-h7k2m"},
            ],
        },
    ],
}


@pytest.fixture(autouse=True)
def isolate_workspace():
    wipe()
    yield
    wipe()


def test_full_cli_pipeline_matches_contract_math():
    """The full ingest, bind, and export pipeline must match the reference report field for field."""
    seed = SEED_POOL[2]
    out = run_curator(seed, "deep-lineage-bind")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = reference_load_scenario(FIXTURE_DIR / "deep-lineage-bind.json", seed)
    ref = reference_curate(sc, seed)
    expected = reference_report(seed, "deep-lineage-bind", sc["_focus"], rep["run_id"], ref)
    assert rep["focus_run_id"] == expected["focus_run_id"]
    assert rep["lineage_chain"] == expected["lineage_chain"]
    assert rep["artifact_digests"] == expected["artifact_digests"]
    assert rep["metric_epochs"] == expected["metric_epochs"]
    assert rep["dataset_bindings"] == expected["dataset_bindings"]
    assert rep["summary"] == expected["summary"]
    assert rep["audit_digest"] == expected["audit_digest"]



def test_fixture_catalog_end_to_end():
    """Bundled fixture scenarios must be sufficient to drive an end-to-end basic-lineage run."""
    assert list(FIXTURE_DIR.glob("*.json"))
    seed = SEED_POOL[0]
    rep = json.loads(run_curator(seed, "basic-lineage").read_text(encoding="utf-8"))
    assert rep["scenario"] == "basic-lineage"


def _tb3_dir() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="tb3-mlprov-"))
    (tmp / "tb3-cross-bind.json").write_text(
        json.dumps(_TB3_SCENARIO, indent=2) + "\n",
        encoding="utf-8",
    )
    return tmp



def test_hidden_overlay_lineage_and_pins():
    """Hidden trap via ephemeral TB3_FIXTURE_DIR overlay (not bundled in the agent image)."""
    seed = SEED_POOL[1]
    meta = _tb3_dir()
    try:
        out = run_curator(seed, "tb3-cross-bind", fixture_dir=meta)
        rep = json.loads(out.read_text(encoding="utf-8"))
        sc = reference_load_scenario(meta / "tb3-cross-bind.json", seed)
        ref = reference_curate(sc, seed)
        assert rep["lineage_chain"] == ref["lineage_chain"]
        assert rep["summary"]["binding_ok"] == ref["summary"]["binding_ok"]
    finally:
        shutil.rmtree(meta, ignore_errors=True)



def test_hidden_manifest_salt_suffix():
    """TB3_MANIFEST_SALT suffix applies to manifest pin hashes."""
    seed = SEED_POOL[0]
    meta = _tb3_dir()
    try:
        wipe()
        salt = "-salt9"
        env = {"TB3_MANIFEST_SALT": salt, "TB3_FIXTURE_DIR": str(meta)}
        invoke([str(CLI_BIN), "ingest", "--seed", seed, "--scenario", "tb3-cross-bind"], env=env)
        invoke([str(CLI_BIN), "curate", "bind", "--seed", seed, "--scenario", "tb3-cross-bind"], env=env)
        out = APP_ROOT / "output" / (seed + "-" + "tb3-cross-bind" + "-" + "provenance" + ".json")
        invoke(
            [str(CLI_BIN), "export", "summary", "--seed", seed, "--scenario", "tb3-cross-bind", "--output", str(out)],
            env=env,
        )
        rep = json.loads(out.read_text(encoding="utf-8"))
        sc = reference_load_scenario(meta / "tb3-cross-bind.json", seed)
        os.environ["TB3_MANIFEST_SALT"] = salt
        try:
            ref = reference_curate(sc, seed)
        finally:
            os.environ.pop("TB3_MANIFEST_SALT", None)
        assert rep["summary"]["binding_ok"] == ref["summary"]["binding_ok"]
        assert rep["audit_digest"] == ref["audit_digest"]
    finally:
        shutil.rmtree(meta, ignore_errors=True)



def test_hidden_overlay_audit_digest():
    """Hidden trap audit_digest for TB3_FIXTURE_DIR overlay scenarios."""
    seed = SEED_POOL[2]
    meta = _tb3_dir()
    try:
        out = run_curator(seed, "tb3-cross-bind", fixture_dir=meta)
        rep = json.loads(out.read_text(encoding="utf-8"))
        sc = reference_load_scenario(meta / "tb3-cross-bind.json", seed)
        ref = reference_curate(sc, seed)
        assert rep["audit_digest"] == ref["audit_digest"]
    finally:
        shutil.rmtree(meta, ignore_errors=True)



def test_sqlite_summary_row_matches_json():
    """The persisted provenance_summary row must agree with the exported summary flags and counts."""
    seed = SEED_POOL[0]
    out = run_curator(seed, "basic-lineage")
    rep = json.loads(out.read_text(encoding="utf-8"))
    con = sqlite3.connect(DB_PATH)
    row = con.execute(
        "SELECT binding_ok, epoch_monotonic_ok, lineage_depth, artifact_count FROM provenance_summary WHERE run_id = ?",
        (rep["run_id"],),
    ).fetchone()
    con.close()
    assert row[0] == int(rep["summary"]["binding_ok"])
    assert row[1] == int(rep["summary"]["epoch_monotonic_ok"])
    assert row[2] == rep["summary"]["lineage_depth"]
    assert row[3] == rep["summary"]["artifact_count"]



def test_bind_keeps_latest_scenario_only():
    """A second bind for the same seed must replace the older scenario row in curation_runs."""
    seed = SEED_POOL[0]
    run_curator(seed, "basic-lineage")
    run_curator(seed, "metric-epoch-order")
    con = sqlite3.connect(DB_PATH)
    row = con.execute(
        "SELECT scenario FROM curation_runs WHERE seed = ?",
        (seed,),
    ).fetchone()
    con.close()
    assert row is not None
    assert row[0] == "metric-epoch-order"



def test_focus_artifact_count_matches_contract_math():
    """summary.artifact_count must match the reference count for the focus run artifacts."""
    seed = SEED_POOL[1]
    out = run_curator(seed, "deep-lineage-bind")
    rep = json.loads(out.read_text(encoding="utf-8"))
    sc = reference_load_scenario(FIXTURE_DIR / "deep-lineage-bind.json", seed)
    ref = reference_curate(sc, seed)
    assert rep["summary"]["artifact_count"] == ref["summary"]["artifact_count"]

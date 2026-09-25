"""Manifest checkpoint ingest and enabled-model DAG traversal contracts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from sentinel_contract_math import (
    compute_lineage_scan as reference_lineage_scan,
)
from sentinel_contract_math import (
    load_scoped_manifest as reference_load_manifest,
)
from sentinel_runner import BUNDLE_ROOT, MANIFEST_SNAP, SEED_POOL, SESSION, wipe


@pytest.fixture(autouse=True)
def isolate_workspace():
    wipe()
    yield
    wipe()


def test_ingest_writes_manifest_checkpoint_for_seed():
    """dbtsent ingest must materialize the manifest checkpoint snapshot at /app/state/manifest-checkpoint.json for the requested seed and bundle."""
    seed = SEED_POOL[0]
    assert SESSION.ingest_manifest(seed, "core-lineage").returncode == 0
    snap = json.loads(MANIFEST_SNAP.read_text(encoding="utf-8"))
    assert snap["seed"] == seed
    assert snap["bundle"] == "core-lineage"
    assert MANIFEST_SNAP.is_file()


def test_full_pipeline_export_path_uses_freshness_report_suffix():
    """Completed ingest evaluate export must land under /app/output/ with -freshness-report.json suffix."""
    out = SESSION.run_full_sentinel(SEED_POOL[1], "freshness-mixed")
    assert str(out).startswith("/app/output/")
    assert out.name.endswith("-freshness-report.json")


def test_evaluate_persists_active_scan_in_freshness_scans_db():
    """evaluate scan must write the active scan row to /app/work/freshness-scans.db."""
    seed = SEED_POOL[0]
    assert SESSION.ingest_manifest(seed, "core-lineage").returncode == 0
    assert SESSION.evaluate_freshness(seed, "core-lineage").returncode == 0
    assert Path("/app/work/freshness-scans.db").is_file()


def test_reingest_increments_checkpoint_ingest_seq():
    """Repeated ingest for the same seed and bundle must increment ingest_seq by exactly one."""
    seed = SEED_POOL[2]
    assert SESSION.ingest_manifest(seed, "core-lineage").returncode == 0
    first = json.loads(MANIFEST_SNAP.read_text(encoding="utf-8"))
    assert SESSION.ingest_manifest(seed, "core-lineage").returncode == 0
    second = json.loads(MANIFEST_SNAP.read_text(encoding="utf-8"))
    assert second["ingest_seq"] == first["ingest_seq"] + 1


def test_checkpoint_models_use_seed_scoped_unique_ids():
    """Materialized checkpoint models must include seed-scoped unique_id suffixes."""
    seed = SEED_POOL[0]
    assert SESSION.ingest_manifest(seed, "core-lineage").returncode == 0
    snap = json.loads(MANIFEST_SNAP.read_text(encoding="utf-8"))
    assert all("-" in m["unique_id"] for m in snap["models"])


def test_enabled_dag_topo_skips_disabled_nodes():
    """model_order must list enabled models only in documented topological order."""
    seed = SEED_POOL[1]
    out = SESSION.run_full_sentinel(seed, "disabled-refs")
    rep = json.loads(out.read_text(encoding="utf-8"))
    raw = reference_load_manifest(BUNDLE_ROOT / "disabled-refs.json", seed)
    ref = reference_lineage_scan(raw, seed)
    assert rep["model_order"] == ref["model_order"]
    disabled = {m["unique_id"] for m in raw["_materialized"]["models"] if not m["enabled"]}
    assert not any(mid in disabled for mid in rep["model_order"])


def test_core_lineage_model_order_matches_reference():
    """Core-lineage bundle model_order must match independent enabled-model topo reference."""
    seed = SEED_POOL[0]
    out = SESSION.run_full_sentinel(seed, "core-lineage")
    rep = json.loads(out.read_text(encoding="utf-8"))
    raw = reference_load_manifest(BUNDLE_ROOT / "core-lineage.json", seed)
    ref = reference_lineage_scan(raw, seed)
    assert rep["model_order"] == ref["model_order"]


def test_exposure_closure_is_transitive_over_models():
    """Exposure refs must include transitive enabled-model dependencies, not direct deps only."""
    seed = SEED_POOL[2]
    out = SESSION.run_full_sentinel(seed, "exposure-depth")
    rep = json.loads(out.read_text(encoding="utf-8"))
    raw = reference_load_manifest(BUNDLE_ROOT / "exposure-depth.json", seed)
    ref = reference_lineage_scan(raw, seed)
    key = next(iter(rep["exposure_refs"]))
    assert rep["exposure_refs"][key] == ref["exposure_refs"][key]

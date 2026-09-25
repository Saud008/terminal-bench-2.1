"""dbtsent CLI guardrails and configuration surface contracts.

Tests drive dbtsent through subprocess invocation via sentinel_runner.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from sentinel_contract_math import load_scoped_manifest as reference_load_manifest
from sentinel_runner import APP_ROOT, BUNDLE_ROOT, SEED_POOL, SESSION, wipe


@pytest.fixture(autouse=True)
def isolate_workspace():
    wipe()
    yield
    wipe()


def test_catalog_documents_four_bundled_manifest_packs():
    """manifest-pack-catalog.md must list every bundled JSON pack under /app/fixtures/bundles/."""
    catalog = (APP_ROOT / "docs" / "manifest-pack-catalog.md").read_text(encoding="utf-8")
    for name in ("core-lineage", "freshness-mixed", "disabled-refs", "exposure-depth"):
        assert name in catalog
        assert (BUNDLE_ROOT / f"{name}.json").is_file()


def test_evaluate_scan_fails_when_checkpoint_missing():
    """evaluate scan must fail fast when ingest has not materialized the manifest checkpoint snapshot."""
    seed = SEED_POOL[0]
    proc = SESSION.evaluate_freshness(seed, "core-lineage")
    assert proc.returncode != 0


def test_ingest_materializes_instruction_checkpoint_path():
    """dbtsent ingest must write the manifest snapshot to /app/state/manifest-checkpoint.json file."""
    seed = SEED_POOL[3]
    checkpoint = Path("/app/state/manifest-checkpoint.json")
    assert SESSION.ingest_manifest(seed, "core-lineage").returncode == 0
    assert checkpoint.is_file()
    bundle = reference_load_manifest(BUNDLE_ROOT / "core-lineage.json", seed)
    assert bundle["pack_name"] == "core-lineage"


def test_export_alerts_writes_beneath_app_output():
    """export alerts must write caller-directed JSON beneath /app/output."""
    out = SESSION.run_full_sentinel(SEED_POOL[0], "core-lineage")
    assert str(out).startswith("/app/output/")
    assert out.is_file()


def test_export_alerts_rejects_unknown_bundle_name():
    """export alerts must reject bundle names that are absent from the staged checkpoint."""
    seed = SEED_POOL[1]
    assert SESSION.ingest_manifest(seed, "core-lineage").returncode == 0
    assert SESSION.evaluate_freshness(seed, "core-lineage").returncode == 0
    out = APP_ROOT / "output" / f"{seed}-missing-pack-freshness-report.json"
    proc = SESSION.export_alerts(seed, "missing-pack", out)
    assert proc.returncode != 0

"""Hidden TB3 overlay traps for freshness bias and scan-store replacement."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest
from sentinel_contract_math import (
    compute_lineage_scan as reference_lineage_scan,
)
from sentinel_contract_math import (
    load_scoped_manifest as reference_load_manifest,
)
from sentinel_runner import SEED_POOL, SESSION, wipe

_TB3_BUNDLE = {
    "bundle_name": "tb3-bias-overlay",
    "generated_at": "2026-04-01T08:00:00Z",
    "evaluated_at": "2026-04-01T10:00:00Z",
    "models": [
        {
            "unique_id": "model.analytics.tb3_root",
            "depends_on": ["source.analytics.tb3_src"],
            "enabled": True,
            "last_built_at": "2026-04-01T09:00:00Z",
        }
    ],
    "sources": [
        {
            "unique_id": "source.analytics.tb3_src",
            "loaded_at": "2026-04-01T09:40:00Z",
            "warn_after_minutes": 10,
            "error_after_minutes": 30,
        }
    ],
    "exposures": [
        {"unique_id": "exposure.analytics.tb3_view", "depends_on": ["model.analytics.tb3_root"]}
    ],
}


@pytest.fixture(autouse=True)
def isolate_workspace():
    wipe()
    yield
    wipe()


def _tb3_fixture_dir() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="tb3-dbtsent-"))
    (tmp / "tb3-bias-overlay.json").write_text(json.dumps(_TB3_BUNDLE, indent=2) + "\n", encoding="utf-8")
    return tmp


def test_overlay_freshness_bias_minutes_shift():
    """TB3_FRESHNESS_BIAS_MINUTES must shift freshness rows and audit_digest per hidden contract."""
    seed = SEED_POOL[3]
    meta = _tb3_fixture_dir()
    try:
        out = SESSION.run_full_sentinel(
            seed,
            "tb3-bias-overlay",
            bundle_dir=meta,
            extra_env={"TB3_FRESHNESS_BIAS_MINUTES": "15"},
        )
        rep = json.loads(out.read_text(encoding="utf-8"))
        raw = reference_load_manifest(meta / "tb3-bias-overlay.json", seed)
        os.environ["TB3_FRESHNESS_BIAS_MINUTES"] = "15"
        try:
            ref = reference_lineage_scan(raw, seed)
        finally:
            os.environ.pop("TB3_FRESHNESS_BIAS_MINUTES", None)
        assert rep["freshness"] == ref["freshness"]
        assert rep["audit_digest"] == ref["audit_digest"]
    finally:
        shutil.rmtree(meta, ignore_errors=True)


def test_overlay_exposure_needs_full_model_walk():
    """Exposure-depth hidden trap requires full transitive model closure, not direct deps only."""
    seed = SEED_POOL[2]
    out = SESSION.run_full_sentinel(seed, "exposure-depth")
    rep = json.loads(out.read_text(encoding="utf-8"))
    from sentinel_runner import BUNDLE_ROOT

    raw = reference_load_manifest(BUNDLE_ROOT / "exposure-depth.json", seed)
    ref = reference_lineage_scan(raw, seed)
    key = next(iter(rep["exposure_refs"]))
    assert rep["exposure_refs"][key] == ref["exposure_refs"][key]


def test_overlay_scan_store_replaces_active_row():
    """Re-running evaluate for the same seed must deactivate prior rows and bump scan_id."""
    seed = SEED_POOL[0]
    assert SESSION.ingest_manifest(seed, "core-lineage").returncode == 0
    assert SESSION.evaluate_freshness(seed, "core-lineage").returncode == 0
    first_path = SESSION.run_full_sentinel(seed, "freshness-mixed")
    r1 = json.loads(first_path.read_text(encoding="utf-8"))
    second_path = SESSION.run_full_sentinel(seed, "freshness-mixed")
    r2 = json.loads(second_path.read_text(encoding="utf-8"))
    assert r2["scan_id"] > r1["scan_id"]

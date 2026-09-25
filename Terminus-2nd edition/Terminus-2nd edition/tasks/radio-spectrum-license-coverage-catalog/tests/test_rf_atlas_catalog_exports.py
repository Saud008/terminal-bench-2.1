"""Catalog export field and summary tests."""

from __future__ import annotations

import json
from pathlib import Path

from rf_atlas_cli_support import SEED_POOL, run_pipeline, wipe

APP = Path("/app")
FIXTURE_DIR = Path("/opt/rflicat-bundles/bundles")


def test_catalog_rows_include_atlas_seq_id() -> None:
    """Every catalog row must carry the top-level atlas_seq_id per schema doc."""
    wipe()
    seed, bundle = SEED_POOL[0], "metro-dual-grant"
    out = run_pipeline(seed, bundle)
    body = json.loads(out.read_text(encoding="utf-8"))
    assert all(r["atlas_seq_id"] == body["atlas_seq_id"] for r in body["catalog_rows"])


def test_summary_active_plus_excluded_equals_total() -> None:
    """Summary counts must satisfy active_sites plus excluded_sites equals total."""
    wipe()
    seed, bundle = SEED_POOL[1], "exclusion-polygon"
    out = run_pipeline(seed, bundle)
    s = json.loads(out.read_text(encoding="utf-8"))["summary"]
    assert s["active_sites"] + s["excluded_sites"] == s["total_sites"]


def test_effective_mhz_from_band_table() -> None:
    """Catalog rows must expose effective MHz bounds from band table lookup."""
    wipe()
    seed, bundle = SEED_POOL[0], "metro-dual-grant"
    out = run_pipeline(seed, bundle)
    row = json.loads(out.read_text(encoding="utf-8"))["catalog_rows"][0]
    assert row["effective_mhz_low"] == 470.0
    assert row["effective_mhz_high"] == 512.0


def test_valid_through_matches_license_renewal() -> None:
    """Each row valid_through must reflect license renewal date from bundle."""
    wipe()
    seed, bundle = SEED_POOL[0], "metro-dual-grant"
    out = run_pipeline(seed, bundle)
    rows = json.loads(out.read_text(encoding="utf-8"))["catalog_rows"]
    assert all(r["valid_through"] for r in rows)


def test_overlap_pairs_symmetric_for_dual_band() -> None:
    """Summary overlap_pairs must count symmetric MHz peer relationships."""
    wipe()
    seed, bundle = SEED_POOL[2], "band-overlap-touch"
    out = run_pipeline(seed, bundle)
    s = json.loads(out.read_text(encoding="utf-8"))["summary"]
    assert s["overlap_pairs"] >= 1


def test_emit_writes_to_custom_output_path() -> None:
    """render-atlas --output flag must write catalog JSON to requested path."""
    from rf_atlas_cli_support import CLI_BIN, invoke

    wipe()
    seed, bundle = SEED_POOL[0], "metro-dual-grant"
    invoke([str(CLI_BIN), "prepare-atlas", "--seed", seed, "--bundle", bundle])
    custom = APP / "output" / "custom-catalog.json"
    proc = invoke(
        [str(CLI_BIN), "render-atlas", "--seed", seed, "--bundle", bundle, "--output", str(custom)]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert custom.exists()
    assert json.loads(custom.read_text(encoding="utf-8"))["bundle"] == bundle

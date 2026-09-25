"""Staging snapshot, ingest generation, and cross-run persistence tests."""

from __future__ import annotations

import json

from rf_atlas_cli_support import CLI_BIN, SEED_POOL, STAGING_PATH, invoke, wipe


def test_staging_carries_as_of_date() -> None:
    """Staging snapshot must carry bundle as_of_date for tenure evaluation."""
    wipe()
    seed, bundle = SEED_POOL[0], "renewal-cutoff"
    proc = invoke([str(CLI_BIN), "prepare-atlas", "--seed", seed, "--bundle", bundle])
    assert proc.returncode == 0
    snap = json.loads(STAGING_PATH.read_text(encoding="utf-8"))
    assert snap["as_of_date"] == "2026-06-01"


def test_staging_lists_all_transmitters() -> None:
    """prepare-atlas staging must list every transmitter from the bundle."""
    wipe()
    seed, bundle = SEED_POOL[1], "metro-dual-grant"
    proc = invoke([str(CLI_BIN), "prepare-atlas", "--seed", seed, "--bundle", bundle])
    assert proc.returncode == 0
    snap = json.loads(STAGING_PATH.read_text(encoding="utf-8"))
    assert len(snap["transmitters"]) == 2


def test_staging_includes_band_specs() -> None:
    """Staging snapshot must include band frequency specs from bundle input."""
    wipe()
    seed, bundle = SEED_POOL[2], "band-overlap-touch"
    proc = invoke([str(CLI_BIN), "prepare-atlas", "--seed", seed, "--bundle", bundle])
    assert proc.returncode == 0
    snap = json.loads(STAGING_PATH.read_text(encoding="utf-8"))
    assert len(snap["bands"]) == 2


def test_recompile_same_seed_new_bundle_bumps_generation() -> None:
    """Switching bundle under same seed must increment load_generation."""
    wipe()
    seed = SEED_POOL[3]
    invoke([str(CLI_BIN), "prepare-atlas", "--seed", seed, "--bundle", "metro-dual-grant"])
    invoke([str(CLI_BIN), "prepare-atlas", "--seed", seed, "--bundle", "renewal-cutoff"])
    snap = json.loads(STAGING_PATH.read_text(encoding="utf-8"))
    assert snap["load_generation"] == 2
    assert snap["bundle"] == "renewal-cutoff"


def test_staging_license_flattened_bbox() -> None:
    """Staging must flatten license territory into lat/lon bbox fields."""
    wipe()
    seed, bundle = SEED_POOL[0], "boundary-edge-sites"
    invoke([str(CLI_BIN), "prepare-atlas", "--seed", seed, "--bundle", bundle])
    snap = json.loads(STAGING_PATH.read_text(encoding="utf-8"))
    lic = snap["licenses"][0]
    assert "lat_min" in lic and "lon_max" in lic

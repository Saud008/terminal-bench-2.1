"""Core rflicat CLI and catalog contract tests."""

from __future__ import annotations

import json
from pathlib import Path

from rf_atlas_cli_support import (
    CLI_BIN,
    COVERAGE_PATH,
    FIXTURE_DIR,
    SEED_POOL,
    STAGING_PATH,
    invoke,
    run_pipeline,
    wipe,
)
from rf_atlas_contract_math import expected_after_first_compile, expected_atlas_seq_id

APP = Path("/app")


def test_cli_binary_exists() -> None:
    """Instruction requires rflicat CLI at /app/bin/rflicat after rebuild."""
    assert CLI_BIN.is_file()


def test_compile_inputs_writes_staging() -> None:
    """prepare-atlas must write staging snapshot with load_generation 1 per contract."""
    wipe()
    seed, bundle = SEED_POOL[0], "metro-dual-grant"
    proc = invoke([str(CLI_BIN), "prepare-atlas", "--seed", seed, "--bundle", bundle])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    snap = json.loads(STAGING_PATH.read_text(encoding="utf-8"))
    assert snap["load_generation"] == 1
    assert snap["seed"] == seed
    assert snap["bundle"] == bundle


def test_load_generation_increments_on_recompile() -> None:
    """Repeated prepare-atlas calls must bump load_generation in staging snapshot."""
    wipe()
    seed = SEED_POOL[1]
    for bundle in ("metro-dual-grant", "boundary-edge-sites"):
        proc = invoke([str(CLI_BIN), "prepare-atlas", "--seed", seed, "--bundle", bundle])
        assert proc.returncode == 0, proc.stderr + proc.stdout
    snap = json.loads(STAGING_PATH.read_text(encoding="utf-8"))
    assert snap["load_generation"] == 2


def test_run_coverage_writes_active_row() -> None:
    """render-atlas must record active seed and bundle in coverage state file."""
    wipe()
    seed, bundle = SEED_POOL[0], "metro-dual-grant"
    run_pipeline(seed, bundle)
    cov = json.loads(COVERAGE_PATH.read_text(encoding="utf-8"))
    assert cov["active"]["seed"] == seed
    assert cov["active"]["bundle"] == bundle
    assert cov["active"]["atlas_seq_id"].startswith("atl-")


def test_metro_dual_grant_catalog_matches_reference() -> None:
    """Full pipeline output must match independent rf_grant_math reference atlas."""
    wipe()
    seed, bundle = SEED_POOL[0], "metro-dual-grant"
    out = run_pipeline(seed, bundle)
    got = json.loads(out.read_text(encoding="utf-8"))
    exp = expected_after_first_compile(seed, bundle, FIXTURE_DIR / f"{bundle}.json")
    assert got["catalog_rows"] == exp["catalog_rows"]
    assert got["summary"] == exp["summary"]
    assert got["audit_digest"] == exp["audit_digest"]


def test_highest_priority_license_wins() -> None:
    """License coupler must pick highest-priority grant when sites overlap licenses."""
    wipe()
    seed, bundle = SEED_POOL[0], "metro-dual-grant"
    out = run_pipeline(seed, bundle)
    rows = json.loads(out.read_text(encoding="utf-8"))["catalog_rows"]
    midtown = next(r for r in rows if r["site_id"] == "tx-midtown")
    assert midtown["license_id"] == "lic-metro-a"
    assert midtown["holder"] == "MetroWave LLC"


def test_boundary_edge_site_included() -> None:
    """Geo fence must include transmitters on license bbox boundary edges."""
    wipe()
    seed, bundle = SEED_POOL[2], "boundary-edge-sites"
    out = run_pipeline(seed, bundle)
    rows = json.loads(out.read_text(encoding="utf-8"))["catalog_rows"]
    ids = {r["site_id"] for r in rows}
    assert "tx-north-edge" in ids


def test_exclusion_marks_site_excluded() -> None:
    """Carveout module must mark sites inside exclusion polygons as excluded."""
    wipe()
    seed, bundle = SEED_POOL[1], "exclusion-polygon"
    out = run_pipeline(seed, bundle)
    rows = json.loads(out.read_text(encoding="utf-8"))["catalog_rows"]
    silo = next(r for r in rows if r["site_id"] == "tx-silo")
    assert silo["excluded"] is True
    farm = next(r for r in rows if r["site_id"] == "tx-farm")
    assert farm["excluded"] is False


def test_renewal_cutoff_drops_expired() -> None:
    """Tenure gate must drop licenses past as_of_date renewal cutoff."""
    wipe()
    seed, bundle = SEED_POOL[3], "renewal-cutoff"
    out = run_pipeline(seed, bundle)
    body = json.loads(out.read_text(encoding="utf-8"))
    ids = {r["site_id"] for r in body["catalog_rows"]}
    assert "tx-active" in ids
    assert "tx-lapsed" not in ids
    assert body["summary"]["expired_dropped"] == 1


def test_catalog_row_sort_order() -> None:
    """Rollup emit must sort catalog rows by holder, band_id, then site_id."""
    wipe()
    seed, bundle = SEED_POOL[0], "metro-dual-grant"
    out = run_pipeline(seed, bundle)
    rows = json.loads(out.read_text(encoding="utf-8"))["catalog_rows"]
    keys = [(r["holder"], r["band_id"], r["site_id"]) for r in rows]
    assert keys == sorted(keys)


def test_band_overlap_peer_count_touching() -> None:
    """MHz peer module must count touching band overlaps per transmitter."""
    wipe()
    seed, bundle = SEED_POOL[2], "band-overlap-touch"
    out = run_pipeline(seed, bundle)
    rows = json.loads(out.read_text(encoding="utf-8"))["catalog_rows"]
    alpha = next(r for r in rows if r["site_id"] == "tx-alpha")
    beta = next(r for r in rows if r["site_id"] == "tx-beta")
    assert alpha["overlap_peer_count"] >= 1
    assert beta["overlap_peer_count"] >= 1


def test_atlas_seq_id_matches_generation() -> None:
    """Atlas sequence id must derive from seed, bundle, and load_generation."""
    wipe()
    seed, bundle = SEED_POOL[0], "metro-dual-grant"
    out = run_pipeline(seed, bundle)
    snap = json.loads(STAGING_PATH.read_text(encoding="utf-8"))
    body = json.loads(out.read_text(encoding="utf-8"))
    assert body["atlas_seq_id"] == expected_atlas_seq_id(seed, bundle, snap["load_generation"])

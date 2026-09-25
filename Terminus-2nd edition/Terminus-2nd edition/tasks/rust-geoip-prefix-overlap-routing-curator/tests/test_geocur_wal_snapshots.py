"""Feed-cache and reconcile ledger snapshot tests."""

from __future__ import annotations

import json

import pytest

from geocur_cli_paths import CLI_BIN, FEED_CACHE_PATH, FIXTURE_DIR, SEED_POOL, SNAP_PATH, invoke, wipe


@pytest.fixture(autouse=True)
def _reset_geocur_workspace():
    wipe()
    yield
    wipe()


def test_geocur_wal_path_is_instruction_contract():
    """Staging snapshot path must match /app/state/feed-normalize-cache.json."""
    assert FEED_CACHE_PATH == "/app/state/feed-normalize-cache.json"
    assert str(SNAP_PATH) == FEED_CACHE_PATH


def test_geocur_wal_generation_monotonic_on_recompile():
    """compile-feeds must bump load_generation on each ingest per feed-cache-schema."""
    seed = SEED_POOL[0]
    proc = invoke([str(CLI_BIN), "compile-feeds", "--seed", seed, "--bundle", "dual-feed-basic"])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    snap = json.loads(SNAP_PATH.read_text(encoding="utf-8"))
    assert snap["load_generation"] == 1
    proc2 = invoke([str(CLI_BIN), "compile-feeds", "--seed", seed, "--bundle", "nested-dup-key"])
    assert proc2.returncode == 0
    snap2 = json.loads(SNAP_PATH.read_text(encoding="utf-8"))
    assert snap2["load_generation"] == 2
    assert snap2["seed"] == seed


def test_geocur_wal_generation_global_across_seeds():
    """load_generation must continue across seed changes on the shared cache file."""
    seed_a = SEED_POOL[0]
    seed_b = SEED_POOL[1]
    proc = invoke([str(CLI_BIN), "compile-feeds", "--seed", seed_a, "--bundle", "dual-feed-basic"])
    assert proc.returncode == 0, proc.stderr + proc.stdout
    snap = json.loads(SNAP_PATH.read_text(encoding="utf-8"))
    assert snap["load_generation"] == 1
    assert snap["seed"] == seed_a
    proc2 = invoke([str(CLI_BIN), "compile-feeds", "--seed", seed_b, "--bundle", "dual-feed-basic"])
    assert proc2.returncode == 0, proc2.stderr + proc2.stdout
    snap2 = json.loads(SNAP_PATH.read_text(encoding="utf-8"))
    assert snap2["load_generation"] == 2
    assert snap2["seed"] == seed_b


def test_geocur_wal_stores_network_form_cidrs():
    """Staging records must store network-normalized CIDR strings."""
    seed = SEED_POOL[1]
    proc = invoke([str(CLI_BIN), "compile-feeds", "--seed", seed, "--bundle", "dual-feed-basic"])
    assert proc.returncode == 0
    snap = json.loads(SNAP_PATH.read_text(encoding="utf-8"))
    cidrs = {row["cidr"] for row in snap["records"]}
    assert "203.0.113.0/24" in cidrs


def test_geocur_wal_preserves_feed_provenance():
    """Each staged row keeps the source feed_id from the bundle."""
    seed = SEED_POOL[2]
    proc = invoke([str(CLI_BIN), "compile-feeds", "--seed", seed, "--bundle", "asn-conflict-lineage"])
    assert proc.returncode == 0
    snap = json.loads(SNAP_PATH.read_text(encoding="utf-8"))
    feeds = {row["feed_id"] for row in snap["records"]}
    assert feeds == {"geoip-lite", "routing-table"}


def test_geocur_reconcile_writes_merge_scoped_row():
    """run-reconcile must persist an active merge row with merge-prefixed reconcile_id."""
    seed = SEED_POOL[0]
    for step in (
        [str(CLI_BIN), "compile-feeds", "--seed", seed, "--bundle", "dual-feed-basic"],
        [str(CLI_BIN), "run-reconcile", "--seed", seed, "--bundle", "dual-feed-basic"],
    ):
        proc = invoke(step)
        assert proc.returncode == 0, proc.stderr + proc.stdout
    ledger = json.loads((SNAP_PATH.parent.parent / "work" / "overlap-generation.json").read_text(encoding="utf-8"))
    assert ledger["active"]["seed"] == seed
    assert ledger["active"]["reconcile_id"].startswith("merge-")


def test_geocur_reconcile_rebinds_active_bundle_for_seed():
    """A later reconcile for the same seed replaces the prior active bundle row."""
    seed = SEED_POOL[3]
    invoke([str(CLI_BIN), "compile-feeds", "--seed", seed, "--bundle", "dual-feed-basic"])
    invoke([str(CLI_BIN), "run-reconcile", "--seed", seed, "--bundle", "dual-feed-basic"])
    invoke([str(CLI_BIN), "compile-feeds", "--seed", seed, "--bundle", "contain-overlap"])
    invoke([str(CLI_BIN), "run-reconcile", "--seed", seed, "--bundle", "contain-overlap"])
    ledger = json.loads((SNAP_PATH.parent.parent / "work" / "overlap-generation.json").read_text(encoding="utf-8"))
    assert ledger["active"]["bundle"] == "contain-overlap"


def test_geocur_catalog_lists_documented_bundles():
    """Bundled fixture inventory includes overlap bundles cited in bundle-catalog."""
    names = sorted(p.stem for p in FIXTURE_DIR.glob("*.json"))
    assert "dual-feed-basic" in names
    assert "asn-conflict-lineage" in names

"""Atlas overlap export and summary contract tests."""

from __future__ import annotations

import json
import pytest

from geocur_cli_paths import CLI_BIN, FIXTURE_DIR, OUTPUT_DIR, SEED_POOL, invoke, run_pipeline, wipe
from geocur_atlas_expect import expect_overlap_report


@pytest.fixture(autouse=True)
def _reset_geocur_workspace():
    wipe()
    yield
    wipe()


def test_geocur_emit_honors_output_root():
    """emit-overlap writes caller reports under /app/output/."""
    seed = SEED_POOL[0]
    out = run_pipeline(seed, "dual-feed-basic")
    assert str(out).startswith(OUTPUT_DIR)


def test_geocur_emit_dual_feed_matches_expect():
    """emit-overlap report must match independent atlas math for dual-feed-basic."""
    seed = SEED_POOL[0]
    out = run_pipeline(seed, "dual-feed-basic")
    rep = json.loads(out.read_text(encoding="utf-8"))
    snap_seq = json.loads((out.parent.parent / "state" / "feed-normalize-cache.json").read_text(encoding="utf-8"))[
        "load_generation"
    ]
    exp = expect_overlap_report(seed, "dual-feed-basic", FIXTURE_DIR / "dual-feed-basic.json", snap_seq)
    assert rep["reconcile_id"] == exp["reconcile_id"]
    assert rep["overlap_rows"] == exp["overlap_rows"]
    assert rep["summary"] == exp["summary"]
    assert rep["audit_digest"] == exp["audit_digest"]


def test_geocur_emit_skips_reserved_space():
    """Reserved-range policy must drop RFC1918 and loopback prefixes from export."""
    seed = SEED_POOL[1]
    out = run_pipeline(seed, "reserved-mixed")
    rep = json.loads(out.read_text(encoding="utf-8"))
    cidrs = [r["cidr"] for r in rep["overlap_rows"]]
    assert all(not c.startswith("127.") for c in cidrs)
    assert all(not c.startswith("10.") for c in cidrs)
    assert rep["summary"]["reserved_dropped"] >= 2


def test_geocur_emit_duplicate_key_feed_id_winner():
    """Duplicate normalized prefix keys must prefer the lexicographically smaller feed_id."""
    seed = SEED_POOL[2]
    out = run_pipeline(seed, "nested-dup-key")
    rep = json.loads(out.read_text(encoding="utf-8"))
    row = next(r for r in rep["overlap_rows"] if r["cidr"] == "203.0.113.192/26")
    assert row["country"] == "MX"
    assert row["asn"] == 703
    assert row["winning_feed"] == "geoip-lite"
    assert sorted(row["asn_lineage"]) == ["b26", "b26-rt"]


def test_geocur_emit_asn_lineage_on_shared_prefix():
    """ASN conflict lineage must list both feed lineage ids on shared prefixes."""
    seed = SEED_POOL[3]
    out = run_pipeline(seed, "asn-conflict-lineage")
    rep = json.loads(out.read_text(encoding="utf-8"))
    row = next(r for r in rep["overlap_rows"] if r["cidr"] == "192.0.2.0/24")
    assert sorted(row["asn_lineage"]) == ["g-lite", "g-rt"]
    assert rep["summary"]["asn_conflicts"] >= 1


def test_geocur_emit_names_immediate_container():
    """Containment export must name the immediate normalized container prefix."""
    seed = SEED_POOL[0]
    out = run_pipeline(seed, "contain-overlap")
    rep = json.loads(out.read_text(encoding="utf-8"))
    inner = next(r for r in rep["overlap_rows"] if r["cidr"] == "172.16.10.0/24")
    assert inner["contained_by"] == "172.16.0.0/12"


def test_geocur_emit_row_order_stable():
    """Overlap rows must sort by country, asn, then cidr ascending."""
    seed = SEED_POOL[1]
    out = run_pipeline(seed, "dual-feed-basic")
    rep = json.loads(out.read_text(encoding="utf-8"))
    keys = [(r["country"], r["asn"], r["cidr"]) for r in rep["overlap_rows"]]
    assert keys == sorted(keys)


def test_geocur_emit_overlap_pair_counter():
    """Summary overlap_pairs must count cross-country or cross-asn containment pairs."""
    seed = SEED_POOL[2]
    out = run_pipeline(seed, "contain-overlap")
    rep = json.loads(out.read_text(encoding="utf-8"))
    assert rep["summary"]["overlap_pairs"] >= 1


def test_geocur_reconcile_id_changes_after_recompile():
    """Re-ingest must advance load_generation and change reconcile_id on re-reconcile."""
    seed = SEED_POOL[2]
    run_pipeline(seed, "dual-feed-basic")
    first = json.loads(
        (FIXTURE_DIR.parent.parent / "work" / "overlap-generation.json").read_text(encoding="utf-8")
    )["active"]["reconcile_id"]
    proc = invoke([str(CLI_BIN), "compile-feeds", "--seed", seed, "--bundle", "dual-feed-basic"])
    assert proc.returncode == 0
    proc = invoke([str(CLI_BIN), "run-reconcile", "--seed", seed, "--bundle", "dual-feed-basic"])
    assert proc.returncode == 0
    out = run_pipeline(seed, "dual-feed-basic")
    rep = json.loads(out.read_text(encoding="utf-8"))
    assert rep["reconcile_id"] != first

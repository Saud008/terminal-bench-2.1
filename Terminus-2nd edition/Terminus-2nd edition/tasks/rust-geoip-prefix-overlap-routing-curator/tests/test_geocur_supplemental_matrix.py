"""Supplemental bundle matrix and staging integrity traps."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from geocur_cli_paths import APP_ROOT, CLI_BIN, FIXTURE_DIR, SEED_POOL, invoke, run_pipeline, wipe
from geocur_atlas_expect import expect_overlap_report

SUPPLEMENTAL_ROOT = Path("/tests/hidden")


@pytest.fixture(autouse=True)
def _reset_geocur_workspace():
    wipe()
    yield
    wipe()


def test_geocur_supplemental_bundle_overlay_report():
    """Supplemental bundle overlay must produce the same report as independent math."""
    seed = SEED_POOL[1]
    out = run_pipeline(seed, "tb3-asn-salt", fixture_dir=SUPPLEMENTAL_ROOT)
    rep = json.loads(out.read_text(encoding="utf-8"))
    snap_seq = json.loads((APP_ROOT / "state" / "feed-normalize-cache.json").read_text(encoding="utf-8"))["load_generation"]
    exp = expect_overlap_report(
        seed,
        "tb3-asn-salt",
        SUPPLEMENTAL_ROOT / "bundles" / "tb3-asn-salt.json",
        snap_seq,
    )
    assert rep["overlap_rows"] == exp["overlap_rows"]
    assert rep["audit_digest"] == exp["audit_digest"]


def test_geocur_supplemental_asn_salt_suffix():
    """TB3_ASN_SALT env must suffix asn_lineage ids before atlas row sort."""
    seed = SEED_POOL[2]
    env = {"TB3_ASN_SALT": "-bench"}
    out = run_pipeline(seed, "tb3-asn-salt", fixture_dir=SUPPLEMENTAL_ROOT, env=env)
    rep = json.loads(out.read_text(encoding="utf-8"))
    snap_seq = json.loads((APP_ROOT / "state" / "feed-normalize-cache.json").read_text(encoding="utf-8"))["load_generation"]
    exp = expect_overlap_report(
        seed,
        "tb3-asn-salt",
        SUPPLEMENTAL_ROOT / "bundles" / "tb3-asn-salt.json",
        snap_seq,
        salt="-bench",
    )
    row = next(r for r in rep["overlap_rows"] if r["cidr"] == "198.18.0.0/15")
    assert row["asn_lineage"] == exp["overlap_rows"][0]["asn_lineage"]
    assert rep["audit_digest"] == exp["audit_digest"]


def test_geocur_supplemental_digest_requires_full_pipeline():
    """Export-only normalization fix must fail salted lineage digest trap."""
    seed = SEED_POOL[3]
    env = {"TB3_ASN_SALT": "-bench"}
    for step in (
        [str(CLI_BIN), "compile-feeds", "--seed", seed, "--bundle", "tb3-asn-salt"],
        [str(CLI_BIN), "run-reconcile", "--seed", seed, "--bundle", "tb3-asn-salt"],
    ):
        proc = invoke(step, env={**env, "TB3_FIXTURE_DIR": str(SUPPLEMENTAL_ROOT)})
        assert proc.returncode == 0
    out = APP_ROOT / "output" / "partial-export.json"
    proc = invoke(
        [
            str(CLI_BIN),
            "emit-overlap",
            "--seed",
            seed,
            "--bundle",
            "tb3-asn-salt",
            "--output",
            str(out),
        ],
        env={**env, "TB3_FIXTURE_DIR": str(SUPPLEMENTAL_ROOT)},
    )
    assert proc.returncode == 0
    rep = json.loads(out.read_text(encoding="utf-8"))
    snap_seq = json.loads((APP_ROOT / "state" / "feed-normalize-cache.json").read_text(encoding="utf-8"))["load_generation"]
    exp = expect_overlap_report(
        seed,
        "tb3-asn-salt",
        SUPPLEMENTAL_ROOT / "bundles" / "tb3-asn-salt.json",
        snap_seq,
        salt="-bench",
    )
    assert rep["audit_digest"] == exp["audit_digest"]


def test_geocur_wal_tamper_breaks_expect_rows():
    """Tampered feed-cache snapshot must not match independent atlas overlap rows."""
    seed = SEED_POOL[0]
    run_pipeline(seed, "dual-feed-basic")
    snap_path = APP_ROOT / "state" / "feed-normalize-cache.json"
    snap = json.loads(snap_path.read_text(encoding="utf-8"))
    snap["records"][0]["country"] = "ZZ"
    snap_path.write_text(json.dumps(snap, indent=2) + "\n", encoding="utf-8")
    out = APP_ROOT / "output" / "tampered-export.json"
    proc = invoke(
        [
            str(CLI_BIN),
            "emit-overlap",
            "--seed",
            seed,
            "--bundle",
            "dual-feed-basic",
            "--output",
            str(out),
        ]
    )
    assert proc.returncode == 0
    rep = json.loads(out.read_text(encoding="utf-8"))
    exp = expect_overlap_report(
        seed, "dual-feed-basic", FIXTURE_DIR / "dual-feed-basic.json", snap["load_generation"]
    )
    assert rep["overlap_rows"] != exp["overlap_rows"]


def test_geocur_supplemental_bundle_not_in_catalog():
    """tb3-asn-salt bundle must exist only under supplemental fixture overlay."""
    bundled = FIXTURE_DIR / "tb3-asn-salt.json"
    assert not bundled.exists()
    assert (SUPPLEMENTAL_ROOT / "bundles" / "tb3-asn-salt.json").exists()

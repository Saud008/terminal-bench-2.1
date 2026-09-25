"""Source freshness windows, disabled upstream alerts, and export parity contracts."""

from __future__ import annotations

import json

import pytest
from sentinel_contract_math import (
    build_alert_report as reference_alert_bundle,
)
from sentinel_contract_math import (
    compute_lineage_scan as reference_lineage_scan,
)
from sentinel_contract_math import (
    load_scoped_manifest as reference_load_manifest,
)
from sentinel_runner import BUNDLE_ROOT, SEED_POOL, SESSION, wipe


@pytest.fixture(autouse=True)
def isolate_workspace():
    wipe()
    yield
    wipe()


@pytest.mark.parametrize(
    "bundle",
    ["core-lineage", "freshness-mixed", "disabled-refs", "exposure-depth"],
)
def test_bundled_export_matches_independent_reference(bundle: str):
    """Each bundled manifest export must match independent freshness, closure, and alert math."""
    seed = SEED_POOL[1]
    out = SESSION.run_full_sentinel(seed, bundle)
    rep = json.loads(out.read_text(encoding="utf-8"))
    raw = reference_load_manifest(BUNDLE_ROOT / f"{bundle}.json", seed)
    ref = reference_lineage_scan(raw, seed)
    expected = reference_alert_bundle(seed, bundle, rep["scan_id"], ref)
    assert rep["freshness"] == expected["freshness"]
    assert rep["exposure_refs"] == expected["exposure_refs"]
    assert rep["summary"] == expected["summary"]
    assert rep["alerts"] == expected["alerts"]
    assert rep["audit_digest"] == expected["audit_digest"]


def test_freshness_mixed_emits_ok_warn_and_error_rows():
    """Freshness-mixed bundle must emit ok, warn, and error source rows per window docs."""
    seed = SEED_POOL[1]
    out = SESSION.run_full_sentinel(seed, "freshness-mixed")
    rep = json.loads(out.read_text(encoding="utf-8"))
    raw = reference_load_manifest(BUNDLE_ROOT / "freshness-mixed.json", seed)
    ref = reference_lineage_scan(raw, seed)
    assert rep["freshness"] == ref["freshness"]


def test_stale_source_counter_tracks_non_ok_rows():
    """Summary stale_source_count must equal the reference stale freshness tally."""
    seed = SEED_POOL[1]
    out = SESSION.run_full_sentinel(seed, "freshness-mixed")
    rep = json.loads(out.read_text(encoding="utf-8"))
    raw = reference_load_manifest(BUNDLE_ROOT / "freshness-mixed.json", seed)
    ref = reference_lineage_scan(raw, seed)
    assert rep["summary"]["stale_source_count"] == ref["summary"]["stale_source_count"]


def test_disabled_upstream_alerts_present_in_export():
    """Disabled-refs bundle must emit DISABLED_UPSTREAM alerts for enabled downstream models."""
    seed = SEED_POOL[2]
    out = SESSION.run_full_sentinel(seed, "disabled-refs")
    rep = json.loads(out.read_text(encoding="utf-8"))
    raw = reference_load_manifest(BUNDLE_ROOT / "disabled-refs.json", seed)
    ref = reference_lineage_scan(raw, seed)
    assert rep["alerts"] == ref["alerts"]
    assert any(a["alert_code"] == "DISABLED_UPSTREAM" for a in rep["alerts"])


def test_summary_flags_disabled_upstream_refs():
    """Summary disabled_ref_ok must be false when an enabled model depends on a disabled upstream."""
    seed = SEED_POOL[2]
    out = SESSION.run_full_sentinel(seed, "disabled-refs")
    rep = json.loads(out.read_text(encoding="utf-8"))
    assert rep["summary"]["disabled_ref_ok"] is False


def test_audit_digest_matches_canonical_hash():
    """Core bundle audit_digest must equal the reference canonical JSON hash."""
    seed = SEED_POOL[0]
    out = SESSION.run_full_sentinel(seed, "core-lineage")
    rep = json.loads(out.read_text(encoding="utf-8"))
    raw = reference_load_manifest(BUNDLE_ROOT / "core-lineage.json", seed)
    ref = reference_lineage_scan(raw, seed)
    expected = reference_alert_bundle(seed, "core-lineage", rep["scan_id"], ref)
    assert rep["audit_digest"] == expected["audit_digest"]


def test_export_consumes_positive_scan_id():
    """Evaluate scan must persist a positive scan_id consumed by export alerts."""
    seed = SEED_POOL[3]
    out = SESSION.run_full_sentinel(seed, "core-lineage")
    rep = json.loads(out.read_text(encoding="utf-8"))
    assert rep["scan_id"] > 0

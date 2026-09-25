"""Bundled k7cal behavioral tests."""

from __future__ import annotations

import json
import subprocess

from evac_cli_support import (
    APP,
    BIN,
    load_weave_ledger,
    pipeline,
    rebuild,
    scenario_root,
    wipe,
)
from evac_independent import reference_seal_bundle

SHA256_HEX_LEN = 64


def test_dual_zone_spread_expected():
    """Dual-zone spread scenario must emit alert bundles matching independent verifier math."""
    wipe()
    out = pipeline("dual-zone-spread", "run-dual")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_seal_bundle(scenario_root() / "dual-zone-spread", "run-dual")
    assert rep["bundles"] == ref["bundles"]


def test_weave_digest_present():
    """Weave stage must persist a 64-character weave_digest on the lane ledger."""
    wipe()
    pipeline("dual-zone-spread", "run-stg")
    stg = load_weave_ledger()
    assert stg["run_id"] == "run-stg"
    assert len(stg["weave_digest"]) == SHA256_HEX_LEN


def test_closure_detour_routing():
    """Closure detour scenario must route around closed segments per road-closure-routing-contract."""
    wipe()
    out = pipeline("closure-detour", "run-closure")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_seal_bundle(scenario_root() / "closure-detour", "run-closure")
    assert rep["bundles"] == ref["bundles"]


def test_shelter_quota_limit():
    """Shelter quota scenario must decrement remaining capacity per shelter-quota-contract."""
    wipe()
    out = pipeline("shelter-capacity-limit", "run-cap")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_seal_bundle(scenario_root() / "shelter-capacity-limit", "run-cap")
    assert rep["bundles"] == ref["bundles"]


def test_severity_tier_ramp_order():
    """Severity tier ramp must classify overlaps using severity-precedence-contract ranks."""
    wipe()
    out = pipeline("severity-tier-ramp", "run-sev")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_seal_bundle(scenario_root() / "severity-tier-ramp", "run-sev")
    assert [b["severity"] for b in rep["bundles"]] == [b["severity"] for b in ref["bundles"]]


def test_concave_bbox_trap_no_false_alert():
    """Concave bbox trap must not emit alerts when polygons do not truly intersect."""
    wipe()
    out = pipeline("concave-bbox-trap", "run-trap")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_seal_bundle(scenario_root() / "concave-bbox-trap", "run-trap")
    assert rep["bundles"] == ref["bundles"]


def test_multi_shelter_nearest():
    """Multi-shelter scenario must pick nearest shelters with available quota."""
    wipe()
    out = pipeline("multi-shelter-nearest", "run-near")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_seal_bundle(scenario_root() / "multi-shelter-nearest", "run-near")
    assert rep["bundles"] == ref["bundles"]


def test_export_includes_weave_digest():
    """Seal output must copy weave_digest from the persisted lane ledger."""
    wipe()
    out = pipeline("dual-zone-spread", "run-dig")
    rep = json.loads(out.read_text(encoding="utf-8"))
    stg = load_weave_ledger()
    assert rep["weave_digest"] == stg["weave_digest"]


def test_bundle_sort_severity_then_zone():
    """Bundles must sort by descending severity tier then ascending zone_id."""
    wipe()
    out = pipeline("severity-tier-ramp", "run-sort")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_seal_bundle(scenario_root() / "severity-tier-ramp", "run-sort")
    keys = [(b["severity"], b["zone_id"]) for b in rep["bundles"]]
    ref_keys = [(b["severity"], b["zone_id"]) for b in ref["bundles"]]
    assert keys == ref_keys


def test_summary_total_evacuees():
    """Summary total_evacuees must match independent assignment totals."""
    wipe()
    out = pipeline("dual-zone-spread", "run-sum")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_seal_bundle(scenario_root() / "dual-zone-spread", "run-sum")
    assert rep["summary"]["total_evacuees"] == ref["summary"]["total_evacuees"]


def test_seal_reads_staging_only():
    """Seal must fail or emit empty bundles when the lane ledger is corrupted."""
    wipe()
    pipeline("dual-zone-spread", "run-seal")
    APP.joinpath("state/evac-lane-ledger.json").write_text("{}", encoding="utf-8")
    out = APP / "output" / "seal-empty.json"
    proc = subprocess.run(
        [str(BIN), "seal", "--run-id", "run-seal", "--output", str(out)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0 or not out.exists() or json.loads(out.read_text()).get("bundles") == []


def test_bind_weave_seal_chain():
    """Bind, weave, and seal subcommands must chain for a bundled scenario."""
    wipe()
    out = pipeline("dual-zone-spread", "run-chain")
    assert out.exists()
    assert json.loads(out.read_text())["run_id"] == "run-chain"


def test_double_rebuild_idempotent():
    """Repeated cargo rebuild must leave the CLI runnable."""
    rebuild()
    rebuild()

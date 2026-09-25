"""Hidden k7cal traps via TB3 fixture root."""

from __future__ import annotations

import json
from pathlib import Path

from evac_cli_support import load_weave_ledger, pipeline, wipe
from evac_independent import reference_seal_bundle

HIDDEN = Path("/opt/verifier-fixtures/k7cal")


def test_hidden_alias_zones_expected():
    """TB3 alias zone ids must map to canonical bundle rows per alert-bundle-schema."""
    wipe()
    out = pipeline("tb3-alias-zones", "run-h1", env={"TB3_FIXTURE_DIR": str(HIDDEN)})
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_seal_bundle(HIDDEN / "tb3-alias-zones", "run-h1")
    assert rep["bundles"] == ref["bundles"]


def test_hidden_closure_bypass_routing():
    """Closed road segments must not provide shortest paths per road-closure-routing-contract."""
    wipe()
    out = pipeline("tb3-closure-bypass", "run-h2", env={"TB3_FIXTURE_DIR": str(HIDDEN)})
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_seal_bundle(HIDDEN / "tb3-closure-bypass", "run-h2")
    assert rep["bundles"] == ref["bundles"]


def test_hidden_weave_digest_roundtrip():
    """Seal output weave_digest must match the persisted lane ledger per lane-ledger-schema."""
    wipe()
    out = pipeline("tb3-alias-zones", "run-h3", env={"TB3_FIXTURE_DIR": str(HIDDEN)})
    rep = json.loads(out.read_text(encoding="utf-8"))
    stg = load_weave_ledger()
    assert rep["weave_digest"] == stg["weave_digest"]


def test_hidden_bundle_digest_stable():
    """bundle_digest must be deterministic across repeated seal runs for the same scenario."""
    wipe()
    out1 = pipeline("tb3-closure-bypass", "run-h4", env={"TB3_FIXTURE_DIR": str(HIDDEN)})
    wipe()
    out2 = pipeline("tb3-closure-bypass", "run-h4", env={"TB3_FIXTURE_DIR": str(HIDDEN)})
    d1 = json.loads(out1.read_text())["bundle_digest"]
    d2 = json.loads(out2.read_text())["bundle_digest"]
    assert d1 == d2

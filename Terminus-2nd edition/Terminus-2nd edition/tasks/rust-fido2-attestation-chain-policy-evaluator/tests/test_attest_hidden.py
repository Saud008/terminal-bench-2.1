"""Hidden fixture tests using TB3_REGISTRY_ROOT."""
from __future__ import annotations

import json
from pathlib import Path

from attest_cli_helpers import run_pipeline, wipe
from attest_verifier_math import reference_trust_report

HIDDEN = Path("/opt/verifier-fixtures/fido2")


def test_hidden_shadow_trust_with_overlay_registry() -> None:
    """Verify hidden TB3 fixture bundle trust report matches reference with overlay metadata registry."""
    wipe()
    env = {"TB3_REGISTRY_ROOT": str(HIDDEN)}
    out = run_pipeline("batch-hidden", "shadow-trust", "enterprise-strict", env=env)
    got = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_trust_report(
        "batch-hidden",
        HIDDEN / "transcript-bundles" / "shadow-trust.json",
        Path("/app/registry/policies/enterprise-strict.json"),
        HIDDEN / "authenticators" / "aaguid-registry.json",
    )
    assert got["summary"] == ref["summary"]
    assert got["decisions"] == ref["decisions"]


def test_hidden_unknown_aaguid_without_overlay_fails_partial() -> None:
    """Verify hidden bundle produces at least one trusted decision with overlay registry."""
    wipe()
    env = {"TB3_REGISTRY_ROOT": str(HIDDEN)}
    out = run_pipeline("batch-hidden", "shadow-trust", "enterprise-strict", env=env)
    got = json.loads(out.read_text(encoding="utf-8"))
    levels = {d["trust_level"] for d in got["decisions"]}
    assert "trusted" in levels

"""Hidden TB3 traps, decoy isolation, and partial-patch probes."""

from __future__ import annotations

import json

import pytest

from sarbctl_curator_contract import load_sarif_findings, physical_fingerprint, remap_uri
from sarbctl_runner import (
    APP,
    BASELINE,
    BASELINE_REV,
    CLI,
    DELTA_OUT,
    HIDDEN,
    PATCHES,
    PATCH_TARGETS,
    POLICY,
    REMAP,
    SARIF,
    invoke,
    sarbctl_curate,
    sarbctl_full_run,
    sarbctl_scan,
    wipe_state,
)


def test_run_subcommand_executes_scan_curate_emit(clean_workspace: None) -> None:
    """cli-surface.md run subcommand must produce delta and baseline revision artifacts."""
    proc = invoke(
        [
            str(CLI),
            "run",
            "--sarif",
            str(SARIF),
            "--policy",
            str(POLICY),
            "--remap",
            str(REMAP),
            "--baseline",
            str(BASELINE),
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert DELTA_OUT.is_file() and BASELINE_REV.is_file()


def test_tb3_gamma_backslash_remap_normalizes_uri(clean_workspace: None) -> None:
    """Hidden gamma scan must remap backslash CI share prefix to web/app.js."""
    assert str(HIDDEN).startswith("/opt/verifier-fixtures")
    sarbctl_full_run(
        HIDDEN / "scan.sarif.json",
        HIDDEN / "policy.json",
        HIDDEN / "remap.json",
        HIDDEN / "snapshot.json",
        env={"TB3_FIXTURE_DIR": str(HIDDEN)},
    )
    body = json.loads(DELTA_OUT.read_text(encoding="utf-8"))
    row = next(r for r in body["rows"] if r["finding_id"] == "g-101")
    assert row["uri"] == "web/app.js"


def test_tb3_gamma_drift_category_on_fingerprint_change(clean_workspace: None) -> None:
    """Hidden gamma baseline fingerprint mismatch must surface drift category."""
    sarbctl_full_run(
        HIDDEN / "scan.sarif.json",
        HIDDEN / "policy.json",
        HIDDEN / "remap.json",
        HIDDEN / "snapshot.json",
        env={"TB3_FIXTURE_DIR": str(HIDDEN)},
    )
    body = json.loads(DELTA_OUT.read_text(encoding="utf-8"))
    assert any(r["finding_id"] == "g-101" and r["category"] == "drift" for r in body["rows"])


def test_merge_decoy_module_not_on_emit_hot_path(clean_workspace: None) -> None:
    """internal/merge decoy edits must not change finding-delta.json output."""
    sarbctl_full_run(SARIF, POLICY, REMAP, BASELINE)
    before = DELTA_OUT.read_text(encoding="utf-8")
    decoy = APP / "internal" / "merge" / "decoy.go"
    original = decoy.read_text(encoding="utf-8")
    try:
        decoy.write_text(original + "\n// probe marker\n", encoding="utf-8")
        invoke(["go", "build", "-mod=readonly", "-o", str(CLI), "./cmd/sarbctl"])
        wipe_state()
        sarbctl_full_run(SARIF, POLICY, REMAP, BASELINE)
        assert DELTA_OUT.read_text(encoding="utf-8") == before
    finally:
        decoy.write_text(original, encoding="utf-8")
        invoke(["go", "build", "-mod=readonly", "-o", str(CLI), "./cmd/sarbctl"])


@pytest.mark.parametrize("patch_key,mode", [
    ("stage", "digest"),
    ("canonical", "delta"),
    ("remap", "delta"),
    ("emit", "delta"),
])
def test_partial_module_patch_changes_output(patch_key: str, mode: str, clean_workspace: None) -> None:
    """Probe: single-module regressions must alter staging digest or delta output."""
    import json as _json

    from sarbctl_runner import STAGING

    if mode == "delta":
        sarbctl_full_run(SARIF, POLICY, REMAP, BASELINE)
        saved = _json.loads(DELTA_OUT.read_text(encoding="utf-8"))
    else:
        sarbctl_scan(SARIF, POLICY, REMAP, BASELINE)
        saved = _json.loads(STAGING.read_text(encoding="utf-8"))["findings_digest"]
    patch_src = PATCHES / f"partial_{patch_key}.go"
    target = PATCH_TARGETS[patch_key]
    original = target.read_text(encoding="utf-8")
    try:
        target.write_text(patch_src.read_text(encoding="utf-8"), encoding="utf-8")
        invoke(["go", "build", "-mod=readonly", "-o", str(CLI), "./cmd/sarbctl"])
        wipe_state()
        if mode == "delta":
            sarbctl_full_run(SARIF, POLICY, REMAP, BASELINE)
            body = _json.loads(DELTA_OUT.read_text(encoding="utf-8"))
            if patch_key == "emit":
                assert body["delta_digest"] != saved["delta_digest"]
            else:
                assert body != saved
        else:
            sarbctl_scan(SARIF, POLICY, REMAP, BASELINE)
            digest = _json.loads(STAGING.read_text(encoding="utf-8"))["findings_digest"]
            assert digest != saved
    finally:
        target.write_text(original, encoding="utf-8")
        invoke(["go", "build", "-mod=readonly", "-o", str(CLI), "./cmd/sarbctl"])


def test_physical_fingerprint_includes_column_component(clean_workspace: None) -> None:
    """fingerprint-drift.md physical hash must incorporate start_line and start_column."""
    from sarbctl_curator_contract import canonical_rule_key

    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    remap_cfg = json.loads(REMAP.read_text(encoding="utf-8"))
    finding = next(f for f in load_sarif_findings(SARIF) if f["finding_id"] == "f-003")
    rk = canonical_rule_key(finding["tool"], finding["rule_id"], policy["rules_catalog"])
    uri = remap_uri(finding["uri"], remap_cfg)
    expected = physical_fingerprint(rk, uri, finding["start_line"], finding["start_column"])
    wipe_state()
    sarbctl_scan(SARIF, POLICY, REMAP, BASELINE)
    sarbctl_curate()
    rev = json.loads(BASELINE_REV.read_text(encoding="utf-8"))
    row = next(e for e in rev["entries"] if e["finding_id"] == "f-003")
    assert row["physical_fingerprint"] == expected
    columnless = physical_fingerprint(rk, uri, finding["start_line"], 0)
    assert row["physical_fingerprint"] != columnless

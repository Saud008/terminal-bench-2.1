"""Hidden TB3 traps and publish poison tests."""

from __future__ import annotations

import json

from conftest import (
    OUTPUT,
    OUTPUT_ATLAS_PATH,
    bundle_manifest,
    load_sealed,
    publish_cli,
    stage_cli,
    seal_digest_from_staging_file,
)
from conform_frame_oracle import oracle_stage_snapshot


def scan_snapshot(bundle_id: str) -> dict:
    proc = stage_cli(bundle_id)
    assert proc.returncode == 0, proc.stderr
    return load_sealed()


def test_tb3_df_minute_boundary_matches_oracle_snapshot() -> None:
    """Hidden bundle under /opt/verifier-fixtures/tb3-bundles/df-minute-boundary matches oracle."""
    manifest = bundle_manifest("df-minute-boundary")
    assert "/opt/verifier-fixtures" in str(manifest)
    staged = scan_snapshot("df-minute-boundary")
    ref = oracle_stage_snapshot(manifest)
    assert staged["edits"] == ref["edits"]
    assert staged["diagnostics"] == ref["diagnostics"]


def test_tb3_df_minute_boundary_no_false_drift() -> None:
    """TB3 drop-frame minute boundary edit must not emit false df_span_drift."""
    staged = scan_snapshot("df-minute-boundary")
    assert not any(f["category"] == "df_span_drift" for f in staged["diagnostics"])


def test_tb3_alias_missing_order_suppresses_orphan() -> None:
    """TB3 alias-missing-order emits offline_media_note after alias normalization."""
    manifest = bundle_manifest("alias-missing-order")
    assert "/opt/verifier-fixtures/tb3-bundles" in str(manifest)
    staged = scan_snapshot("alias-missing-order")
    ref = oracle_stage_snapshot(manifest)
    assert staged["diagnostics"] == ref["diagnostics"]
    assert any(f["category"] == "offline_media_note" for f in staged["diagnostics"])
    assert not any(f["category"] == "alias_orphan" for f in staged["diagnostics"])


def test_tb3_alias_missing_order_publish_atlas() -> None:
    """TB3 publish writes conform-atlas.json without publish_reopen_trap diagnostics."""
    out = OUTPUT / "conform-atlas.json"
    stage_cli("alias-missing-order")
    proc = publish_cli("alias-missing-order", out)
    assert proc.returncode == 0
    assert str(out) == OUTPUT_ATLAS_PATH
    atlas = json.loads(out.read_text(encoding="utf-8"))
    assert atlas["bundle_id"] == "alias-missing-order"
    assert not any(f.get("category") == "publish_reopen_trap" for f in atlas["diagnostics"])


def test_publish_reopen_trap_absent_on_clean_publish() -> None:
    """Publish stage must not append publish_reopen_trap when reading staging only."""
    out = OUTPUT / "conform-atlas.json"
    stage_cli("clean-conform")
    publish_cli("clean-conform", out)
    atlas = json.loads(out.read_text(encoding="utf-8"))
    assert not any(f.get("category") == "publish_reopen_trap" for f in atlas["diagnostics"])


def test_seal_digest_stable_across_restage() -> None:
    """seal_digest remains stable when re-staging the same bundle fingerprint."""
    stage_cli("df-cross-cut")
    first = load_sealed()["seal_digest"]
    stage_cli("df-cross-cut")
    second = load_sealed()["seal_digest"]
    assert first == second
    assert first == seal_digest_from_staging_file()

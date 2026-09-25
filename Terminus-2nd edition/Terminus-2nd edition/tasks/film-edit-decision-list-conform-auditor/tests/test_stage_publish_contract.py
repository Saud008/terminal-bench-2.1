"""Ingest stage and export publish CLI contract tests."""

from __future__ import annotations

import json

from conftest import (
    CLI,
    OUTPUT,
    OUTPUT_ATLAS_PATH,
    STATE_RUN_SEQ,
    STATE_SEALED,
    bundle_manifest,
    load_sealed,
    publish_cli,
    stage_cli,
    seal_digest_from_staging_file,
)
from conform_frame_oracle import oracle_stage_snapshot, oracle_publish_atlas


def test_cli_installed_on_path() -> None:
    """CLI is installed at /usr/local/bin/edl-conform-audit per instruction.md."""
    assert CLI.is_file()
    assert CLI.stat().st_mode & 0o111


def test_stage_missing_bundle_exits_2() -> None:
    """stage exits 2 when the bundle manifest path is absent."""
    missing = bundle_manifest("clean-conform").with_name("missing-bundle.json")
    from conftest import run

    proc = run([str(CLI), "stage", "--bundle", str(missing)])
    assert proc.returncode == 2


def test_publish_without_stage_exits_3() -> None:
    """publish exits 3 before /app/state/edl-conform-sealed.json exists for the bundle."""
    out = OUTPUT / "conform-atlas.json"
    proc = publish_cli("clean-conform", out)
    assert proc.returncode == 3


def test_stage_writes_edl_conform_staging() -> None:
    """stage writes /app/state/edl-conform-sealed.json with bundle_id and seal_digest."""
    proc = stage_cli("clean-conform")
    assert proc.returncode == 0, proc.stderr
    assert STATE_SEALED == "/app/state/edl-conform-sealed.json"
    meta = load_sealed()
    assert meta["bundle_id"] == "clean-conform"
    assert "seal_digest" in meta
    assert "edits" in meta and "diagnostics" in meta


def test_stage_edits_include_frame_fields() -> None:
    """staged edits include resolved reel and frame span fields."""
    stage_cli("clean-conform")
    edits = load_sealed()["edits"]
    assert edits
    assert {"edit", "reel", "resolved_reel", "rec_span_frames", "src_span_frames"} <= set(edits[0])


def test_stage_handle_exceeds_reel_diagnostic() -> None:
    """handle-overflow bundle stages handle_exceeds_reel diagnostics."""
    stage_cli("handle-overflow")
    diagnostics = load_sealed()["diagnostics"]
    assert any(r["category"] == "handle_exceeds_reel" for r in diagnostics)


def test_seal_digest_includes_diagnostic_bytes() -> None:
    """seal_digest hashes edits and diagnostics per conform-workflow.md."""
    stage_cli("handle-overflow")
    meta = load_sealed()
    assert meta["seal_digest"] == seal_digest_from_staging_file()


def test_clean_conform_matches_oracle_stage() -> None:
    """Bundled clean-conform staging matches the independent independent oracle."""
    manifest = bundle_manifest("clean-conform")
    stage_cli("clean-conform")
    staged = load_sealed()
    ref = oracle_stage_snapshot(manifest)
    assert staged["edits"] == ref["edits"]
    assert staged["diagnostics"] == ref["diagnostics"]
    assert staged["seal_digest"] == ref["seal_digest"]


def test_publish_atlas_schema() -> None:
    """publish writes /app/output/conform-atlas.json with bundle_id, edits, and diagnostics."""
    out = OUTPUT / "conform-atlas.json"
    stage_cli("clean-conform")
    proc = publish_cli("clean-conform", out)
    assert proc.returncode == 0, proc.stderr
    assert str(out) == OUTPUT_ATLAS_PATH
    atlas = json.loads(out.read_text(encoding="utf-8"))
    assert atlas["bundle_id"] == "clean-conform"
    assert "diagnostics" in atlas and "edits" in atlas


def test_publish_matches_oracle_atlas() -> None:
    """publish atlas for df-cross-cut matches oracle stage and publish oracle output."""
    manifest = bundle_manifest("df-cross-cut")
    stage_cli("df-cross-cut")
    staged = load_sealed()
    ref_snap = oracle_stage_snapshot(manifest)
    assert staged["edits"] == ref_snap["edits"]
    assert staged["diagnostics"] == ref_snap["diagnostics"]
    out = OUTPUT / "conform-atlas.json"
    publish_cli("df-cross-cut", out)
    atlas = json.loads(out.read_text(encoding="utf-8"))
    ref_atlas = oracle_publish_atlas(ref_snap)
    assert atlas == ref_atlas


def test_run_seq_stable_on_repeat_stage() -> None:
    """Re-staging the same bundle fingerprint keeps run_seq stable in /app/state/run-seq.json."""
    stage_cli("clean-conform")
    first = load_sealed()["run_seq"]
    stage_cli("clean-conform")
    second = load_sealed()["run_seq"]
    assert first == second
    assert STATE_RUN_SEQ == "/app/state/run-seq.json"


def test_instruction_named_output_paths_exist() -> None:
    """Pytest covers every instruction output path: staging, atlas, and run-seq state files."""
    from pathlib import Path

    stage_cli("clean-conform")
    assert Path(STATE_SEALED).is_file()
    assert Path(STATE_RUN_SEQ).is_file()
    out = OUTPUT / "conform-atlas.json"
    pub = publish_cli("clean-conform", out)
    assert pub.returncode == 0
    assert Path(OUTPUT_ATLAS_PATH).is_file()


def test_alias_reverse_resolves_source_reel() -> None:
    """Bidirectional alias resolution maps vault_id EDL reels to alias source keys."""
    manifest = bundle_manifest("alias-reverse")
    stage_cli("alias-reverse")
    staged = load_sealed()
    ref = oracle_stage_snapshot(manifest)
    assert staged["edits"] == ref["edits"]
    assert not any(f["category"] == "alias_orphan" for f in staged["diagnostics"])


def test_missing_suppress_offline_media_note() -> None:
    """Missing inventory emits offline_media_note instead of alias_orphan after alias resolution."""
    manifest = bundle_manifest("missing-suppress")
    stage_cli("missing-suppress")
    staged = load_sealed()
    ref = oracle_stage_snapshot(manifest)
    assert staged["diagnostics"] == ref["diagnostics"]
    assert any(f["category"] == "offline_media_note" for f in staged["diagnostics"])
    assert not any(f["category"] == "alias_orphan" for f in staged["diagnostics"])

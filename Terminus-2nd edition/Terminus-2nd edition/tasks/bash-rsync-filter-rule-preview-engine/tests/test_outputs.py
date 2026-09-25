"""Bundled rsyncprev behavioral tests."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from rsyncprev_cli_support import COMPILED, run_pipeline, wipe
from rsyncprev_contract_math import reference_preview


def test_export_stage_writes_atlas():
    """export stage must emit rsync_filter_preview_atlas.json via subprocess CLI."""
    wipe()
    out = run_pipeline("media-sync", "run-export-stage")
    assert out.is_file()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["path_verdicts"]


def test_cli_binary_exists():
    """CLI contract requires rsyncprev usage text when invoked without subcommands."""
    proc = subprocess.run(["/app/bin/rsyncprev"], capture_output=True, text=True)
    assert proc.returncode != 0
    assert "rsyncprev" in (proc.stderr + proc.stdout)


def test_media_sync_matches_reference_preview():
    """media-sync fixture manifest preview must match independent reference math."""
    wipe()
    out = run_pipeline("media-sync", "run-media")
    got = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_preview(Path("/app/fixtures/trees/media-sync/manifest.json"), "run-media")
    assert got == ref


def test_receiver_drift_matches_reference_preview():
    """receiver-drift fixture must reconcile sender and receiver paths per contracts."""
    wipe()
    out = run_pipeline("receiver-drift", "run-rd")
    got = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_preview(Path("/app/fixtures/trees/receiver-drift/manifest.json"), "run-rd")
    assert got == ref


def test_docs_cascade_matches_reference_preview():
    """docs-cascade fixture must honor cascade overlay rules from manifest."""
    wipe()
    out = run_pipeline("docs-cascade", "run-docs")
    got = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_preview(Path("/app/fixtures/trees/docs-cascade/manifest.json"), "run-docs")
    assert got == ref


def test_staging_file_written():
    """compile stage must write filter-compiled.json before preview export."""
    wipe()
    run_pipeline("media-sync", "run-stage")
    assert COMPILED.is_file()


def test_first_match_index_for_cache_rule():
    """first-match contract applies to cache/tmp.bin under media-sync rules."""
    wipe()
    out = run_pipeline("media-sync", "run-first")
    rows = json.loads(out.read_text(encoding="utf-8"))["path_verdicts"]
    row = next(r for r in rows if r["path"] == "cache/tmp.bin")
    assert row["matched_rule_index"] == 0


def test_cascade_depth_includes_root_layer():
    """cascade depth for albums/live/set1.flac must include ancestor overlay layers."""
    wipe()
    out = run_pipeline("media-sync", "run-depth")
    rows = json.loads(out.read_text(encoding="utf-8"))["path_verdicts"]
    leaf = next(r for r in rows if r["path"] == "albums/live/set1.flac")
    assert leaf["cascade_depth"] >= 3


def test_protected_delete_risk_present():
    """delete-risk contract marks configs/legacy.yml protected under receiver-drift."""
    wipe()
    out = run_pipeline("receiver-drift", "run-protect")
    rows = json.loads(out.read_text(encoding="utf-8"))["path_verdicts"]
    protected = next(r for r in rows if r["path"] == "configs/legacy.yml")
    assert protected["delete_risk"] == "protected"


def test_candidate_delete_risk_present():
    """receiver-only drift paths may surface candidate delete_risk rows."""
    wipe()
    out = run_pipeline("receiver-drift", "run-candidate")
    rows = json.loads(out.read_text(encoding="utf-8"))["path_verdicts"]
    cand = [r for r in rows if r["delete_risk"] == "candidate"]
    assert cand


def test_preview_rows_sorted_by_path():
    """atlas schema requires path_verdicts sorted by path ascending."""
    wipe()
    out = run_pipeline("docs-cascade", "run-sort")
    rows = json.loads(out.read_text(encoding="utf-8"))["path_verdicts"]
    paths = [r["path"] for r in rows]
    assert paths == sorted(paths)

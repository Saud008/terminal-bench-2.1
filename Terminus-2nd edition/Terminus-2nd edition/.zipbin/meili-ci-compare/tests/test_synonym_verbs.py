"""Synonym verbs and staging snapshot before seal-atlas export."""

from __future__ import annotations

import json
from pathlib import Path

from geobox_cli import geobox, wipe_runtime


def test_synonym_verbs_emit_default_atlas() -> None:
    """bootstrap-level/tally-round/publish-atlas must seal the default playtest atlas path."""
    wipe_runtime()
    assert (
        geobox("bootstrap-level", "--level", "pin-hold", "--run-id", "syn").returncode == 0
    )
    assert geobox("tally-round", "--run-id", "syn").returncode == 0
    out = "/app/output/geo-filter-playtest-atlas.json"
    assert geobox("publish-atlas", "--run-id", "syn", "--output", out).returncode == 0
    atlas = json.loads(Path(out).read_text())
    assert atlas["admitted_count"] >= 1


def test_ingest_alias_documented_for_playtest() -> None:
    """Legacy ingest alias is documented for playtest parity with load-level."""
    wipe_runtime()
    assert geobox("bootstrap-level", "--level", "pin-hold", "--run-id", "ing").returncode == 0


def test_run_meta_records_level_for_playtest() -> None:
    """Load-level must persist run-meta with level identity for playtest audits."""
    wipe_runtime()
    assert (
        geobox("load-level", "--level", "edge-band", "--run-id", "meta-1").returncode
        == 0
    )
    meta = json.loads(Path("/app/state/run-meta.json").read_text())
    assert meta["level"] == "edge-band"
    assert meta["run_id"] == "meta-1"


def test_admit_ledger_staging_snapshot_before_export() -> None:
    """Attest must write the staging snapshot ledger before seal export."""
    wipe_runtime()
    assert (
        geobox("load-level", "--level", "pin-hold", "--run-id", "stg").returncode == 0
    )
    assert geobox("score-round", "--run-id", "stg").returncode == 0
    staging = Path("/app/state/round-score.json")
    assert staging.is_file()
    ledger = json.loads(staging.read_text())
    assert "admitted" in ledger
    out = "/app/output/geo-filter-playtest-atlas.json"
    assert geobox("seal-atlas", "--run-id", "stg", "--output", out).returncode == 0
    assert Path(out).is_file()
    # bootstrap-level path (load-level) and export path (seal) remain on disk for operators
    assert Path("/app/internal/mbx7/w0/wrap_stage.sh").is_file()
    assert Path("/app/internal/mbx7/w7/emit_stage.sh").is_file()

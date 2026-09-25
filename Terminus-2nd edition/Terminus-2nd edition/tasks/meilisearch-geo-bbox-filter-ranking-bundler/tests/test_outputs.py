"""Primary playfield puzzle checks for the paris-core level."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from geobox_authority import atlas_digest, load_level, reference_evaluate
from geobox_cli import drive_score_round, wipe_runtime


def test_geoboxplay_binary_resolves_under_app_bin() -> None:
    """Playfield planner binary must resolve under /app/bin."""
    assert Path("/app/bin/geoboxplay").is_file()
    assert (
        subprocess.run(
            ["/app/bin/geoboxplay"], capture_output=True, check=False
        ).returncode
        != 0
    )


def test_paris_core_playtest_atlas_matches_authority() -> None:
    """Paris-core sealed playtest atlas must match rulecard authority math."""
    wipe_runtime()
    atlas = drive_score_round("paris-core", "paris-run")
    inv = load_level(Path("/app/fixtures/levels/paris-core/inventory.json"))
    ref = reference_evaluate(inv)
    assert atlas["admitted_count"] == ref["admitted_count"]
    assert {row["doc_id"] for row in atlas["admitted"]} == {
        row["doc_id"] for row in ref["admitted"]
    }
    assert {row["doc_id"]: row["deny_reason"] for row in atlas["denied"]} == {
        row["doc_id"]: row["deny_reason"] for row in ref["denied"]
    }
    assert atlas["atlas_digest"] == atlas_digest(ref["admitted"])
    sealed = Path("/app/output/geo-filter-playtest-atlas.json")
    assert "PAR-LOUVRE" in sealed.read_text(encoding="utf-8")
    assert json.loads(sealed.read_text(encoding="utf-8"))["admitted_count"] == ref[
        "admitted_count"
    ]
    assert "PAR-PINNED" in {row["doc_id"] for row in atlas["denied"]}

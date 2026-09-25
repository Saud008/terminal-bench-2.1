"""Staging artifacts for whslot score and draft phases."""
from __future__ import annotations

import json
from pathlib import Path

from whslot_refmath import expected_sku_rank_board
from whslot_driver import FIXTURE_ROOT, invoke, run_pipeline


def test_velocity_order_board_matches_reference(fresh_wsr_yard) -> None:
    """velocity-order scenario sku-score-board must match zone-biased reference ranks."""
    run_pipeline("velocity-order")
    body = json.loads(Path("/app/work/sku-score-board.json").read_text(encoding="utf-8"))
    assert body["ranks"] == expected_sku_rank_board(FIXTURE_ROOT, "velocity-order")


def test_score_skus_writes_board_snapshot(fresh_wsr_yard) -> None:
    """score-skus stage must materialize /app/work/sku-score-board.json staging artifact."""
    invoke(["latch-yard", "--scenario", "clean-replen", "--fixture-dir", str(FIXTURE_ROOT)])
    assert invoke(["score-skus"]).returncode == 0
    assert Path("/app/work/sku-score-board.json").is_file()


def test_draft_wave_writes_wave_draft_json(fresh_wsr_yard) -> None:
    """draft-wave stage must write /app/work/wave-draft.json planned rows snapshot."""
    invoke(["latch-yard", "--scenario", "clean-replen", "--fixture-dir", str(FIXTURE_ROOT)])
    invoke(["score-skus"])
    assert invoke(["draft-wave"]).returncode == 0
    assert Path("/app/work/wave-draft.json").is_file()


def test_crew_bind_sets_wave_latch_pass(fresh_wsr_yard) -> None:
    """crew-bind must set wave_latch_pass gate file before atlas export is allowed."""
    invoke(["latch-yard", "--scenario", "clean-replen", "--fixture-dir", str(FIXTURE_ROOT)])
    invoke(["score-skus"])
    invoke(["draft-wave"])
    invoke(["crew-bind"])
    gate = json.loads(Path("/app/state/wave-latch-pass.json").read_text(encoding="utf-8"))
    assert gate["wave_latch_pass"] > 0


def test_full_pipeline_emits_slot_replen_atlas(fresh_wsr_yard) -> None:
    """End-to-end pipeline must create /app/output/slot-replen-atlas.json export file."""
    run_pipeline("clean-replen")
    assert Path("/app/output/slot-replen-atlas.json").is_file()


def test_draft_wave_runs_without_prior_score_board(fresh_wsr_yard) -> None:
    """draft-wave remains callable after latch-yard even when score-skus was skipped."""
    invoke(["latch-yard", "--scenario", "clean-replen", "--fixture-dir", str(FIXTURE_ROOT)])
    assert invoke(["draft-wave"]).returncode == 0

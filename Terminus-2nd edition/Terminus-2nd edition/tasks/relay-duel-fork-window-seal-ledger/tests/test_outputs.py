"""End-to-end duelctl arena pipeline behavioral tests."""

from __future__ import annotations

import json
import subprocess

from duel_admit_runner import (
    ARENA_ID,
    ARTIFACTS,
    FIXTURE_ROOT,
    TB3_FIXTURE_DIR,
    fetch_sqlite_rows,
    invoke_duelctl,
    reset_arena_workspace,
    run_arena_pipeline,
)
from duel_ledger_refmath import reference_arena_sqlite


def test_t700598_duelctl_challenge_flow_sqlite_matches_reference() -> None:
    """Answered CHALLENGE/RESIGN match produces SQLite rows matching reference math."""
    reset_arena_workspace()
    run_arena_pipeline("challenge-accept-resign")
    assert ARTIFACTS["sqlite"].is_file()
    got = fetch_sqlite_rows(ARTIFACTS["sqlite"])
    ref, _ = reference_arena_sqlite(ARENA_ID, "challenge-accept-resign", FIXTURE_ROOT)
    assert got == ref
    assert got[0]["disposition"] == "completed"


def test_t700598_duelctl_forked_fork_tag_keeps_one_billed_branch() -> None:
    """Forked fork-tag branches score only the answered lane per lane-fork-contract."""
    reset_arena_workspace()
    run_arena_pipeline("forked-lane-join")
    got = fetch_sqlite_rows(ARTIFACTS["sqlite"])
    ref, _ = reference_arena_sqlite(ARENA_ID, "forked-lane-join", FIXTURE_ROOT)
    assert got == ref
    assert len(got) == 1


def test_t700598_duelctl_forfeit_before_accept_exports_zero_rows() -> None:
    """Early FORFEIT suppresses SQLite export when no 2xx answer occurred."""
    reset_arena_workspace()
    run_arena_pipeline("forfeit-before-accept")
    got = fetch_sqlite_rows(ARTIFACTS["sqlite"])
    ref, _ = reference_arena_sqlite(ARENA_ID, "forfeit-before-accept", FIXTURE_ROOT)
    assert got == ref == []


def test_t700598_duelctl_hold_ring_no_ledger_rows() -> None:
    """180/183-only matches never materialize match-ledger.sqlite rows."""
    reset_arena_workspace()
    run_arena_pipeline("hold-only")
    assert fetch_sqlite_rows(ARTIFACTS["sqlite"]) == []


def test_t700598_duelctl_skew_shifts_rush_score_band() -> None:
    """clock_skew_ms moves answer timestamp into rush score window."""
    reset_arena_workspace()
    run_arena_pipeline("clock-skew-window")
    got = fetch_sqlite_rows(ARTIFACTS["sqlite"])
    ref, _ = reference_arena_sqlite(ARENA_ID, "clock-skew-window", FIXTURE_ROOT)
    assert got == ref
    assert got[0]["score_band"] == "rush"


def test_t700598_duelctl_retransmit_dedupe_single_row() -> None:
    """Duplicate 200 retransmits collapse to one SQLite row."""
    reset_arena_workspace()
    run_arena_pipeline("retransmit-storm")
    got = fetch_sqlite_rows(ARTIFACTS["sqlite"])
    ref, _ = reference_arena_sqlite(ARENA_ID, "retransmit-storm", FIXTURE_ROOT)
    assert got == ref
    assert len(got) == 1


def test_t700598_duelctl_repeat_pipeline_stable_sqlite_bytes() -> None:
    """Second pipeline pass yields identical match-ledger.sqlite bytes after workspace reset."""
    reset_arena_workspace()
    run_arena_pipeline("cross-run-stable-bytes")
    first = ARTIFACTS["sqlite"].read_bytes()
    reset_arena_workspace()
    run_arena_pipeline("cross-run-stable-bytes")
    assert ARTIFACTS["sqlite"].read_bytes() == first


def test_t700598_duelctl_export_seal_nonzero() -> None:
    """seal-ledger emits match-publish-seal.json with populated match_seal."""
    reset_arena_workspace()
    run_arena_pipeline("challenge-accept-resign")
    assert ARTIFACTS["seal"].is_file()
    seal = json.loads(ARTIFACTS["seal"].read_text(encoding="utf-8"))
    assert seal["match_seal"]
    assert seal["row_count"] >= 1


def test_t700598_duelctl_score_windows_report_written() -> None:
    """score-windows stage writes score-window-report.json with rated matches."""
    reset_arena_workspace()
    run_arena_pipeline("challenge-accept-resign")
    report = json.loads(ARTIFACTS["score"].read_text(encoding="utf-8"))
    assert report["rated_count"] >= 1


def test_t700598_duelctl_staging_seal_after_compile() -> None:
    """fold-branches stamps match_seal on match-buffer staging artifact."""
    reset_arena_workspace()
    run_arena_pipeline("challenge-accept-resign")
    staging = json.loads(ARTIFACTS["staging"].read_text(encoding="utf-8"))
    assert staging["match_seal"]


def test_t700598_duelctl_ingest_only_creates_staging_file() -> None:
    """admit-log alone materializes match-buffer.json under /app/state."""
    reset_arena_workspace()
    proc = invoke_duelctl(["admit-log", "--arena", ARENA_ID, "--scenario", "challenge-accept-resign"])
    assert proc.returncode == 0
    assert isinstance(proc, subprocess.CompletedProcess)
    assert ARTIFACTS["staging"].is_file()


def test_t700598_duelctl_sqlite_rows_sorted_lexicographically() -> None:
    """ledger_rows appear in duel_id then branch_key ascending order."""
    reset_arena_workspace()
    run_arena_pipeline("challenge-accept-resign")
    keys = [(r["duel_id"], r["branch_key"]) for r in fetch_sqlite_rows(ARTIFACTS["sqlite"])]
    assert keys == sorted(keys)


def test_t700598_duelctl_duration_seconds_positive_for_completed() -> None:
    """Completed calls record positive duration_sec between answer and RESIGN."""
    reset_arena_workspace()
    run_arena_pipeline("challenge-accept-resign")
    rows = fetch_sqlite_rows(ARTIFACTS["sqlite"])
    assert rows[0]["duration_sec"] > 0


def test_t700598_duelctl_tb3_forfeit_poison_matches_reference() -> None:
    """Off-catalog forfeit poison requires TB3 admit-log sort and precedence."""
    reset_arena_workspace()
    run_arena_pipeline("hidden-forfeit-poison", TB3_FIXTURE_DIR)
    got = fetch_sqlite_rows(ARTIFACTS["sqlite"])
    ref, _ = reference_arena_sqlite(ARENA_ID, "hidden-forfeit-poison", TB3_FIXTURE_DIR)
    assert got == ref


def test_t700598_duelctl_tb3_score_boundary_inclusive_end() -> None:
    """Hidden score boundary honors inclusive score window end minute."""
    reset_arena_workspace()
    run_arena_pipeline("hidden-score-boundary", TB3_FIXTURE_DIR)
    got = fetch_sqlite_rows(ARTIFACTS["sqlite"])
    ref, _ = reference_arena_sqlite(ARENA_ID, "hidden-score-boundary", TB3_FIXTURE_DIR)
    assert got == ref


def test_t700598_duelctl_rush_or_calm_band_on_rated_row() -> None:
    """Rated rows always carry rush or calm tier labels."""
    reset_arena_workspace()
    run_arena_pipeline("clock-skew-window")
    tier = fetch_sqlite_rows(ARTIFACTS["sqlite"])[0]["score_band"]
    assert tier in ("rush", "calm")


def test_t700598_duelctl_fork_staging_retains_two_branches() -> None:
    """Forked scenario staging tracks at least two branch keys before match-ledger export."""
    reset_arena_workspace()
    run_arena_pipeline("forked-lane-join")
    staging = json.loads(ARTIFACTS["staging"].read_text(encoding="utf-8"))
    assert len(staging.get("matches", {})) >= 2


def test_t700598_duelctl_seal_row_count_matches_reference() -> None:
    """match-publish-seal row_count equals golden export row count."""
    reset_arena_workspace()
    run_arena_pipeline("challenge-accept-resign")
    seal = json.loads(ARTIFACTS["seal"].read_text(encoding="utf-8"))
    _, ref_seal = reference_arena_sqlite(ARENA_ID, "challenge-accept-resign", FIXTURE_ROOT)
    assert seal["row_count"] == ref_seal["row_count"]

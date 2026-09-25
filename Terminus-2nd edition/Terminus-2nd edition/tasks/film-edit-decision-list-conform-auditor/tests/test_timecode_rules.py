"""Drop-frame, pull-down, and FCM header frame math tests."""

from __future__ import annotations

from conftest import bundle_manifest, load_sealed, stage_cli
from conform_frame_oracle import oracle_stage_snapshot, tc_to_frames


def test_df_cross_cut_fcm_matches_drop_frame_map() -> None:
    """df-cross-cut EDL FCM DROP FRAME header matches tc_map drop_frame true."""
    manifest = bundle_manifest("df-cross-cut")
    proc = stage_cli("df-cross-cut")
    assert proc.returncode == 0, proc.stderr
    ref = oracle_stage_snapshot(manifest)
    assert ref["tc_profile"]["drop_frame"] is True


def test_clean_conform_fcm_matches_non_drop_map() -> None:
    """clean-conform EDL FCM NON-DROP FRAME header matches tc_map drop_frame false."""
    manifest = bundle_manifest("clean-conform")
    proc = stage_cli("clean-conform")
    assert proc.returncode == 0, proc.stderr
    ref = oracle_stage_snapshot(manifest)
    assert ref["tc_profile"]["drop_frame"] is False


def test_drop_frame_minute_boundary_frames() -> None:
    """SMPTE drop-frame math at a minute boundary matches timecode-map-contract.md."""
    assert tc_to_frames("00:59:58:00", 30, True) == 107832
    assert tc_to_frames("01:00:03:00", 30, True) == 107982
    assert tc_to_frames("01:00:03:00", 30, True) - tc_to_frames("00:59:58:00", 30, True) == 150


def test_non_drop_linear_frames() -> None:
    """Non-drop bundles use linear frame index per timecode-map-contract.md."""
    assert tc_to_frames("01:00:00:00", 30, False) == 108000
    assert tc_to_frames("01:00:05:00", 30, False) - tc_to_frames("01:00:00:00", 30, False) == 150


def test_df_cross_cut_record_source_spans_match() -> None:
    """df-cross-cut record and source spans match under drop-frame conversion."""
    manifest = bundle_manifest("df-cross-cut")
    stage_cli("df-cross-cut")
    staged = load_sealed()
    ref = oracle_stage_snapshot(manifest)
    assert staged["edits"][0]["rec_span_frames"] == staged["edits"][0]["src_span_frames"]
    assert staged["edits"] == ref["edits"]


def test_pulldown_trap_budget_matches_oracle_snapshot() -> None:
    """23976 pull-down handle budgets match pull-down-handles.md scaling."""
    manifest = bundle_manifest("pulldown-trap")
    stage_cli("pulldown-trap")
    staged = load_sealed()
    ref = oracle_stage_snapshot(manifest)
    assert staged["edits"][0]["handle_budget_frames"] == ref["edits"][0]["handle_budget_frames"]
    assert not any(f["category"] == "telecine_pull_drift" for f in ref["diagnostics"])


def test_handle_exceeds_reel_diagnostic_present() -> None:
    """handle-overflow bundle emits handle_exceeds_reel and df_span_drift diagnostics."""
    manifest = bundle_manifest("handle-overflow")
    stage_cli("handle-overflow")
    staged = load_sealed()
    ref = oracle_stage_snapshot(manifest)
    assert any(f["category"] == "handle_exceeds_reel" for f in ref["diagnostics"])
    assert staged["diagnostics"] == ref["diagnostics"]


def test_df_cross_cut_no_df_span_drift_when_conformed() -> None:
    """Conformed df-cross-cut edits produce no df_span_drift diagnostics."""
    stage_cli("df-cross-cut")
    staged = load_sealed()
    assert not any(f["category"] == "df_span_drift" for f in staged["diagnostics"])

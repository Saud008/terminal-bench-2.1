"""Blackout precedence, ad cues, and feed substitution contracts."""
from __future__ import annotations

import json
from pathlib import Path

from bcast_synd_refmath import reference_conflicts, reference_plan
from bcast_synd_cli import (
    CONFLICT_JSON,
    FIXTURE_ROOT,
    PLAN_JSON,
    SCENARIO_AD,
    SCENARIO_BLACKOUT,
    SCENARIO_FEED,
    SCENARIO_MULTI,
    run_pipeline,
    wipe_state,
)


def test_regional_blackout_wins_over_rights_window():
    """Blackout precedence contract must block air slots before rights windows apply."""
    wipe_state()
    run_pipeline(SCENARIO_BLACKOUT)
    plan = json.loads(PLAN_JSON.read_text(encoding="utf-8"))
    ref = reference_plan(FIXTURE_ROOT, SCENARIO_BLACKOUT)
    assert plan["entries"] == ref["entries"]
    assert any(row["status"] == "blackout" for row in plan["entries"])


def test_break_cues_survive_feed_line_swap():
    """Ad marker preservation must keep break cues when feed substitution remaps program_id."""
    wipe_state()
    run_pipeline(SCENARIO_AD)
    compile_log = json.loads(Path("/app/work/window-compile-log.json").read_text(encoding="utf-8"))
    ref = reference_plan(FIXTURE_ROOT, SCENARIO_AD)
    assert compile_log["marker_audit"] == ref["marker_audit"]


def test_feed_specific_program_substitution():
    """Feed substitution contract selects alternate program_id per feed map."""
    wipe_state()
    run_pipeline(SCENARIO_FEED)
    syndicated = json.loads(PLAN_JSON.read_text(encoding="utf-8"))
    assert syndicated["entries"] == reference_plan(FIXTURE_ROOT, SCENARIO_FEED)["entries"]


def test_multi_feed_syndication_rows_cover_each_line():
    """Multi-feed scenarios must emit one syndication row per scheduled program."""
    wipe_state()
    run_pipeline(SCENARIO_MULTI)
    body = json.loads(PLAN_JSON.read_text(encoding="utf-8"))
    assert body["entries"] == reference_plan(FIXTURE_ROOT, SCENARIO_MULTI)["entries"]


def test_blackout_block_kind_present_in_conflict_ledger():
    """Conflict report must list blackout_block when blackout precedence fires."""
    wipe_state()
    run_pipeline(SCENARIO_BLACKOUT)
    entries = json.loads(PLAN_JSON.read_text(encoding="utf-8"))["entries"]
    ledger = json.loads(CONFLICT_JSON.read_text(encoding="utf-8"))
    ref_kinds = {item["kind"] for item in reference_conflicts(FIXTURE_ROOT, SCENARIO_BLACKOUT, entries)}
    assert "blackout_block" in ref_kinds
    assert "blackout_block" in {item["kind"] for item in ledger["conflicts"]}

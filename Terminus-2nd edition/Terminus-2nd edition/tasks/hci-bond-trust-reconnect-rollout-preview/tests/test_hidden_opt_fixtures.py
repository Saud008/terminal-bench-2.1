"""Evaluation-only overlay scenarios read through TB3_SCENARIO_DIR, not the public fixtures tree."""

from __future__ import annotations

from pathlib import Path

from fleet_cutover_harness import OVERLAY_FIXTURE_DIR, run_cutover_preview, wipe_run_state
from bond_eligibility_oracle import compute_audit_digest, evaluate_fleet, load_fleet_scenario


def _overlay_env() -> dict[str, str]:
    return {"TB3_SCENARIO_DIR": OVERLAY_FIXTURE_DIR}


def test_overlay_fixtures_directory_is_installed_and_not_under_public_fixtures() -> None:
    """The evaluation overlay must exist at /opt and stay outside the public fixtures tree."""
    assert Path(OVERLAY_FIXTURE_DIR).is_dir()
    assert not str(Path(OVERLAY_FIXTURE_DIR)).startswith("/app/fixtures")


def test_resume_cleared_flag_overrides_a_stale_token_in_the_overlay_scenario() -> None:
    """hidden-resume-cleared-override: a stale token with resume_cleared true must stay eligible."""
    wipe_run_state()
    atlas = run_cutover_preview(
        "hidden-resume-cleared-override", "overlay-resume", env=_overlay_env()
    )
    inv = load_fleet_scenario(Path("/opt/verifier-fixtures/hciroll/hidden-resume-cleared-override/inventory.json"))
    ref = evaluate_fleet(inv)
    assert atlas["eligible_count"] == ref["eligible_count"]
    assert atlas["ineligible_count"] == ref["ineligible_count"]
    assert atlas["audit_digest"] == compute_audit_digest(ref["eligible"], ref["ineligible"])
    assert "AA:BB:CC:DD:EE:H1" in {r["mac"] for r in atlas["eligible"]}


def test_debounce_window_collapses_rapid_probes_in_the_overlay_scenario() -> None:
    """hidden-storm-debounce-window: probes inside one debounce window must count once."""
    wipe_run_state()
    atlas = run_cutover_preview(
        "hidden-storm-debounce-window", "overlay-storm", env=_overlay_env()
    )
    inv = load_fleet_scenario(Path("/opt/verifier-fixtures/hciroll/hidden-storm-debounce-window/inventory.json"))
    ref = evaluate_fleet(inv)
    assert atlas["eligible_count"] == ref["eligible_count"]
    assert atlas["ineligible_count"] == ref["ineligible_count"]
    assert "AA:BB:CC:DD:EE:H2" in {r["mac"] for r in atlas["eligible"]}


def test_cycle_power_plan_never_blocks_in_the_overlay_scenario() -> None:
    """hidden-power-cycle-always-ok: a cycle power plan must never trip the power-sequence gate."""
    wipe_run_state()
    atlas = run_cutover_preview(
        "hidden-power-cycle-always-ok", "overlay-power", env=_overlay_env()
    )
    reasons = {r["mac"]: r["reason"] for r in atlas["ineligible"]}
    assert "AA:BB:CC:DD:EE:H3" not in reasons

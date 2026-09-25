"""Fleet cutover rollout pipeline checks — CLI presence, end-to-end wiring, ledger persistence."""

from __future__ import annotations

import subprocess
from pathlib import Path

from fleet_cutover_harness import CLI, run_cutover_preview, wipe_run_state
from bond_eligibility_oracle import (
    compute_audit_digest,
    evaluate_fleet,
    load_fleet_scenario,
    reference_audit_digest,
)


def test_t54a45e_hciroll_dispatcher_resolves_for_fleet_cutover() -> None:
    """The hciroll dispatcher must be installed under /app/bin for fleet cutover previews."""
    assert CLI.is_file()
    proc = subprocess.run([str(CLI)], capture_output=True, text=True)
    assert proc.returncode != 0


def test_t54a45e_scan_compile_publish_pipeline_produces_rollout_atlas() -> None:
    """scan, compile, and publish chained together must produce a rollout atlas matching independent math."""
    wipe_run_state()
    atlas = run_cutover_preview("basic-reconnect", "pipeline-check")
    inv = load_fleet_scenario(Path("/app/fixtures/scenarios/basic-reconnect/inventory.json"))
    ref = evaluate_fleet(inv)
    assert atlas["eligible_count"] == ref["eligible_count"]
    assert atlas["ineligible_count"] == ref["ineligible_count"]
    expected = reference_audit_digest(ref["eligible"], ref["ineligible"])
    assert atlas["audit_digest"] == expected
    assert expected == compute_audit_digest(ref["eligible"], ref["ineligible"])


def test_t54a45e_reconnect_ledger_persists_across_publish_calls() -> None:
    """The reconnect ledger written by compile must remain on disk after publish runs."""
    wipe_run_state()
    run_cutover_preview("basic-reconnect", "ledger-persist")
    assert Path("/app/state/reconnect-ledger.json").is_file()

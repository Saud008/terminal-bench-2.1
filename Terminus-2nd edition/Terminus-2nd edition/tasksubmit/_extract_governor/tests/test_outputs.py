"""G-026 holdfairctl queue fairness smoke tests — ingest mount and export atlas stages."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from libhold_exec import (
    ATLAS_JSON,
    CLI_BIN,
    FIXTURE_ROOT,
    ROLLUP_JSON,
    SCENARIO_CLEAN,
    SCENARIO_STABLE,
    run_hold_pipeline,
    read_json,
    reset_hold_state,
)
from libhold_sim import build_rollup_snapshot, simulate_hold_assignments


class TestHoldGovExecutable:
    def test_binary_on_path(self):
        """holdfairctl binary is installed under /app/bin."""
        assert CLI_BIN.is_file()

    def test_missing_subcommand_exits_nonzero(self):
        """CLI without a subcommand must fail fast."""
        proc = subprocess.run([str(CLI_BIN)], capture_output=True, text=True, check=False)
        assert proc.returncode != 0


class TestHoldGovRollupStage:
    def test_queue_rollup_digest_matches_simulator(self):
        """compose-rollup writes rollup_fingerprint matching libhold_sim."""
        reset_hold_state()
        run_hold_pipeline(SCENARIO_CLEAN)
        body = read_json(ROLLUP_JSON)
        ref = build_rollup_snapshot(FIXTURE_ROOT, SCENARIO_CLEAN)
        assert body["rollup_fingerprint"] == ref["rollup_fingerprint"]
        assert body["patron_count"] == ref["patron_count"]

    def test_rollup_records_engine_name(self):
        """Rollup JSON records holdfairctl engine metadata."""
        reset_hold_state()
        run_hold_pipeline(SCENARIO_CLEAN)
        body = read_json(ROLLUP_JSON)
        assert body["engine"] == "holdfairctl"
        assert body["hold_request_count"] >= 1


class TestHoldGovFairnessAtlas:
    def test_clean_scenario_matches_reference_rows(self):
        """Fair assignments for clean-queue match independent simulator rows."""
        reset_hold_state()
        run_hold_pipeline(SCENARIO_CLEAN)
        atlas = read_json(ATLAS_JSON)
        ref = simulate_hold_assignments(FIXTURE_ROOT, SCENARIO_CLEAN)
        assert atlas["run_stamp"] == ref["run_stamp"]
        assert atlas["assignments"] == ref["assignments"]

    def test_assignment_rows_carry_branch_and_copy(self):
        """Each assignment row includes branch_id, copy_id, and request_id."""
        reset_hold_state()
        run_hold_pipeline(SCENARIO_CLEAN)
        atlas = read_json(ATLAS_JSON)
        for row in atlas["assignments"]:
            assert row["branch_id"]
            assert row["copy_id"]
            assert row["request_id"]

    def test_queue_positions_monotonic(self):
        """Atlas assignments remain sorted by queue_pos ascending."""
        reset_hold_state()
        run_hold_pipeline(SCENARIO_CLEAN)
        positions = [row["queue_pos"] for row in read_json(ATLAS_JSON)["assignments"]]
        assert positions == sorted(positions)


class TestHoldGovReconcileCounters:
    def test_reconcile_pass_advances_between_runs(self):
        """reconcile_pass increments when rank-fair-holds runs again."""
        reset_hold_state()
        run_hold_pipeline(SCENARIO_CLEAN)
        first = read_json(Path("/app/state/reconcile-pass.json"))
        run_hold_pipeline(SCENARIO_CLEAN)
        second = read_json(Path("/app/state/reconcile-pass.json"))
        assert second["reconcile_pass"] == first["reconcile_pass"] + 1

    def test_reconcile_log_emits_run_seal(self):
        """reconcile-log.json carries a run_stamp after rank-fair-holds."""
        reset_hold_state()
        run_hold_pipeline(SCENARIO_CLEAN)
        log = read_json(Path("/app/work/reconcile-log.json"))
        assert log.get("run_stamp")


class TestHoldGovPublishGate:
    def test_atlas_publish_requires_prior_reconcile(self):
        """write-assignment-atlas fails when reconcile_pass is zero."""
        reset_hold_state()
        proc = subprocess.run(
            [str(CLI_BIN), "write-assignment-atlas", "--scenario", SCENARIO_CLEAN],
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode != 0


@pytest.mark.parametrize("scenario", [SCENARIO_STABLE])
def test_pass_seal_stable_on_repeat(scenario: str):
    """Stable scenario reruns emit identical run_stamp values."""
    reset_hold_state()
    run_hold_pipeline(scenario)
    first = read_json(ATLAS_JSON)["run_stamp"]
    run_hold_pipeline(scenario)
    second = read_json(ATLAS_JSON)["run_stamp"]
    assert first == second

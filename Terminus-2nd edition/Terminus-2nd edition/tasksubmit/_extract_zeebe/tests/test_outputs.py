"""Behavioral verifier for zeebe-bpmn-replay job activation export."""

from __future__ import annotations

import json
import subprocess
import threading
from pathlib import Path

import pytest
from reference_zeebe import reference_export, reference_snapshot

APP = Path("/app")
SCENARIOS = APP / "fixtures" / "scenarios"
OUTPUT = APP / "output" / "job-activation-export.json"
SNAPSHOT = APP / "state" / "incident-snapshot.json"
RESET = APP / "scripts" / "reset-state.sh"
CLI = "/usr/local/bin/zeebe-bpmn-replay"
HIDDEN_OVERLAP_FIXTURE = Path("/opt/verifier-fixtures/zeebe-bpmn/boundary-incident-overlap.json")
HIDDEN_OVERLAY_TRAP_FIXTURE = Path("/opt/verifier-fixtures/zeebe-bpmn/idempotent-overlay-trap.json")

_BUILD_LOCK = threading.RLock()

CATALOG = [
    "01-baseline.json",
    "02-incident-barrier.json",
    "03-boundary-ordering.json",
    "04-deadline-clock.json",
    "05-variable-merge.json",
    "06-idempotent-replay.json",
    "07-merged.json",
]


def run(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=str(cwd or APP),
        capture_output=True,
        text=True,
        check=False,
    )


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr


def _build_unlocked() -> subprocess.CompletedProcess[str]:
    return run(["go", "build", "-mod=readonly", "-o", CLI, "./cmd/zeebe-bpmn-replay"])


def build() -> subprocess.CompletedProcess[str]:
    with _BUILD_LOCK:
        return _build_unlocked()


def cli_export(scenario: Path, out: Path) -> subprocess.CompletedProcess[str]:
    out.parent.mkdir(parents=True, exist_ok=True)
    return run([CLI, "export", "--scenario", str(scenario), "--output", str(out)])


@pytest.fixture(autouse=True)
def _setup() -> None:
    reset()
    with _BUILD_LOCK:
        proc = _build_unlocked()
    assert proc.returncode == 0, proc.stderr


class TestZeebeBpmnReplay:
    def test_export_baseline_matches_reference(self) -> None:
        """CLI export matches reference for 01-baseline.json."""
        self._assert_export_matches(SCENARIOS / "01-baseline.json")

    def test_export_incident_barrier_matches_reference(self) -> None:
        """CLI export matches reference for 02-incident-barrier.json."""
        self._assert_export_matches(SCENARIOS / "02-incident-barrier.json")

    def test_export_boundary_ordering_matches_reference(self) -> None:
        """CLI export matches reference for 03-boundary-ordering.json."""
        self._assert_export_matches(SCENARIOS / "03-boundary-ordering.json")

    def test_export_deadline_clock_matches_reference(self) -> None:
        """CLI export matches reference for 04-deadline-clock.json."""
        self._assert_export_matches(SCENARIOS / "04-deadline-clock.json")

    def test_export_variable_merge_matches_reference(self) -> None:
        """CLI export matches reference for 05-variable-merge.json."""
        self._assert_export_matches(SCENARIOS / "05-variable-merge.json")

    def test_export_idempotent_replay_matches_reference(self) -> None:
        """CLI export matches reference for 06-idempotent-replay.json."""
        self._assert_export_matches(SCENARIOS / "06-idempotent-replay.json")

    def test_export_merged_matches_reference(self) -> None:
        """CLI export matches reference for 07-merged.json."""
        self._assert_export_matches(SCENARIOS / "07-merged.json")

    def _assert_export_matches(self, scenario: Path) -> None:
        out = APP / "output" / f"export-{scenario.name}"
        proc = cli_export(scenario, out)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        cli = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_export(scenario)
        assert cli == ref

    def test_staging_snapshot_matches_reference(self) -> None:
        """Staging snapshot at /app/state/incident-snapshot.json matches reference ingest."""
        scenario = SCENARIOS / "07-merged.json"
        out = APP / "output" / "snapshot-check.json"
        proc = cli_export(scenario, out)
        assert proc.returncode == 0, proc.stderr
        assert SNAPSHOT.is_file(), "incident-snapshot.json missing"
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        ref = reference_snapshot(scenario)
        assert snap == ref

    def test_final_snapshot_staging_written_false(self) -> None:
        """Final persisted incident-snapshot.json keeps staging_written false."""
        scenario = SCENARIOS / "07-merged.json"
        out = APP / "output" / "ack-order.json"
        proc = cli_export(scenario, out)
        assert proc.returncode == 0, proc.stderr
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        assert snap["staging_written"] is False

    def test_canonical_instruction_output_paths(self) -> None:
        """Merged export writes /app/output/job-activation-export.json and /app/state/incident-snapshot.json"""
        scenario = SCENARIOS / "07-merged.json"
        export_path = Path("/app/output/job-activation-export.json")
        snapshot_path = Path("/app/state/incident-snapshot.json")
        proc = cli_export(scenario, export_path)
        assert proc.returncode == 0, proc.stderr
        assert export_path.is_file(), "job-activation-export.json missing"
        assert snapshot_path.is_file(), "incident-snapshot.json missing"
        cli = json.loads(export_path.read_text(encoding="utf-8"))
        ref = reference_export(scenario)
        assert cli == ref
        assert json.loads(snapshot_path.read_text(encoding="utf-8")) == reference_snapshot(scenario)

    def test_incident_barrier_uses_marker_persisted_gate(self) -> None:
        """Incident barrier scenario reports incident_marker_persisted on the shipped CLI build."""
        scenario = SCENARIOS / "02-incident-barrier.json"
        out = APP / "output" / "barrier-gate.json"
        proc = cli_export(scenario, out)
        assert proc.returncode == 0, proc.stderr
        cli = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_export(scenario)
        assert cli["activation_sequence"][0]["barrier"] == "incident_marker_persisted"
        assert cli["activation_sequence"][0]["activated_at_ms"] == ref["activation_sequence"][0]["activated_at_ms"]

    def test_idempotent_replay_skips_duplicate_activation(self) -> None:
        """Idempotent replay scenario skips duplicate activations on the shipped CLI build."""
        scenario = SCENARIOS / "06-idempotent-replay.json"
        out = APP / "output" / "dedup-check.json"
        proc = cli_export(scenario, out)
        assert proc.returncode == 0, proc.stderr
        cli = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_export(scenario)
        assert cli["duplicate_activations_skipped"] == ref["duplicate_activations_skipped"]
        assert cli["duplicate_activations_skipped"] >= 1

    def test_deadline_clock_source_process_on_clock_scenario(self) -> None:
        """Deadline clock scenario derives deadlines from process clock on the shipped CLI build."""
        scenario = SCENARIOS / "04-deadline-clock.json"
        out = APP / "output" / "deadline-clock.json"
        proc = cli_export(scenario, out)
        assert proc.returncode == 0, proc.stderr
        cli = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_export(scenario)
        assert cli["deadline_clock_source"] == "process"
        assert cli["activation_sequence"][0]["deadline_ms"] == ref["activation_sequence"][0]["deadline_ms"]

    def test_catalog_scenarios_all_export_success(self) -> None:
        """Every catalog scenario exports successfully from the shipped CLI build."""
        for name in CATALOG:
            scenario = SCENARIOS / name
            out = APP / "output" / f"catalog-{name}"
            proc = cli_export(scenario, out)
            assert proc.returncode == 0, f"{name}: {proc.stderr}"

    def test_tb3_boundary_incident_overlap(self) -> None:
        """TB3 overlap fixture requires incident marker barrier and boundary ordering together."""
        assert HIDDEN_OVERLAP_FIXTURE.is_file(), "hidden overlap fixture missing under /opt/verifier-fixtures/"
        out = APP / "output" / "tb3-overlap.json"
        proc = cli_export(HIDDEN_OVERLAP_FIXTURE, out)
        assert proc.returncode == 0, proc.stderr
        cli = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_export(HIDDEN_OVERLAP_FIXTURE)
        assert cli == ref

    def test_tb3_idempotent_overlay_trap(self) -> None:
        """TB3 overlay trap requires dedup skip and protected output-mapping merge."""
        assert HIDDEN_OVERLAY_TRAP_FIXTURE.is_file(), "hidden overlay fixture missing under /opt/verifier-fixtures/"
        out = APP / "output" / "tb3-overlay-trap.json"
        proc = cli_export(HIDDEN_OVERLAY_TRAP_FIXTURE, out)
        assert proc.returncode == 0, proc.stderr
        cli = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_export(HIDDEN_OVERLAY_TRAP_FIXTURE)
        assert cli == ref
        assert cli["duplicate_activations_skipped"] == 1
        assert cli["variable_snapshot"]["resolved_outputs"]["packed_units"] == 4

    def test_missing_scenario_exit_two(self, tmp_path: Path) -> None:
        """Missing scenario path returns exit code 2."""
        proc = cli_export(tmp_path / "missing.json", OUTPUT)
        assert proc.returncode == 2

    def test_unknown_command_exit_two(self) -> None:
        """Unknown CLI subcommand returns exit code 2 per cli-errors.md."""
        proc = run([CLI, "replay", "--scenario", str(SCENARIOS / "01-baseline.json"), "--output", str(OUTPUT)])
        assert proc.returncode == 2
        assert "unknown command" in proc.stderr

    def test_malformed_scenario_exit_three(self, tmp_path: Path) -> None:
        """Invalid scenario JSON returns exit code 3."""
        bad = tmp_path / "bad.json"
        bad.write_text("{not-json", encoding="utf-8")
        proc = cli_export(bad, OUTPUT)
        assert proc.returncode == 3

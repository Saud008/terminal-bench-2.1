"""
Milestone 1: heartbeat contract, timeout wheel grace, query reset gate.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from reference_cadence import reference_replay

APP = Path("/app")
CLI = Path("/usr/local/bin/cadence-replay")
SCENARIOS = APP / "fixtures" / "scenarios"
OUTPUT = APP / "output" / "workflow-replay-report.json"
STATE = APP / "state" / "cadence-task-state.json"
RESET = APP / "scripts" / "reset-state.sh"

M1_SCENARIOS = [
    "01-heartbeat-order.json",
    "02-timeout-grace.json",
    "03-query-reset-gate.json",
]

MODULES = {
    "recorder": APP / "internal/heartbeat/recorder.go",
    "wheel": APP / "internal/timeout/wheel.go",
    "reset": APP / "internal/query/reset.go",
    "extend": APP / "internal/visibility/extend.go",
}


def _reset() -> None:
    subprocess.run(["bash", str(RESET)], check=True)


def _build() -> None:
    proc = subprocess.run(
        ["go", "build", "-mod=readonly", "-o", str(CLI), "./cmd/cadence-replay"],
        cwd=APP,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout


def _replay(scenario: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            str(CLI),
            "replay",
            "--scenario",
            str(scenario),
            "--output",
            str(OUTPUT),
            "--state",
            str(STATE),
        ],
        capture_output=True,
        text=True,
    )


@pytest.fixture(autouse=True)
def _setup() -> None:
    _reset()
    _build()


class TestMilestone1:
    """Heartbeat, timeout grace, and query reset gate requirements."""

    def test_build_compiles(self) -> None:
        """Go tree must compile."""
        assert CLI.is_file()

    @pytest.mark.parametrize("scenario_file", M1_SCENARIOS)
    def test_replay_matches_reference(self, scenario_file: str) -> None:
        """CLI replay report matches independent Cadence reference FSM."""
        scenario = SCENARIOS / scenario_file
        proc = _replay(scenario)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        cli = json.loads(OUTPUT.read_text(encoding="utf-8"))
        ref = reference_replay(scenario)
        assert cli == ref

    def test_stale_heartbeat_does_not_extend_visibility(self) -> None:
        """Stale lower-seq heartbeat must not push visibility_deadline_ms forward."""
        scenario = SCENARIOS / "01-heartbeat-order.json"
        proc = _replay(scenario)
        assert proc.returncode == 0, proc.stderr
        report = json.loads(OUTPUT.read_text(encoding="utf-8"))
        assert report["last_progress_seq"] == 4
        assert report["visibility_deadline_ms"] == 6000

    def test_timeout_honors_heartbeat_grace(self) -> None:
        """Timeout check within grace of last heartbeat must not mark timed_out."""
        scenario = SCENARIOS / "02-timeout-grace.json"
        proc = _replay(scenario)
        assert proc.returncode == 0, proc.stderr
        report = json.loads(OUTPUT.read_text(encoding="utf-8"))
        assert report["timed_out"] is False

    def test_reset_query_requires_progress(self) -> None:
        """Reset-workflow query with insufficient progress must be rejected."""
        scenario = SCENARIOS / "03-query-reset-gate.json"
        proc = _replay(scenario)
        assert proc.returncode == 0, proc.stderr
        report = json.loads(OUTPUT.read_text(encoding="utf-8"))
        reset = next(r for r in report["query_results"] if r["query_id"] == "reset-q1")
        assert reset["accepted"] is False

    def test_visibility_decoy_only_fix_still_fails(self) -> None:
        """Patching visibility extend helper alone must not fix heartbeat contract tests."""
        partial = Path(__file__).resolve().parent / "partial"
        saved = {k: p.read_bytes() for k, p in MODULES.items()}
        shutil.copy2(partial / "broken_recorder.go", MODULES["recorder"])
        shutil.copy2(partial / "extend_fixed.go", MODULES["extend"])
        _build()
        proc = _replay(SCENARIOS / "01-heartbeat-order.json")
        assert proc.returncode == 0
        report = json.loads(OUTPUT.read_text(encoding="utf-8"))
        ref = reference_replay(SCENARIOS / "01-heartbeat-order.json")
        for path, blob in saved.items():
            MODULES[path].write_bytes(blob)
        _build()
        assert report != ref

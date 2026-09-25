"""
Milestone 2: sticky partition refresh, history duplicate cursor, merged replay.
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
HIDDEN = Path("/opt/verifier-fixtures")

M2_SCENARIOS = [
    "04-sticky-refresh.json",
    "05-duplicate-event-id.json",
    "06-merged-stall.json",
]

MODULES = {
    "map": APP / "internal/sticky/map.go",
    "reader": APP / "internal/history/reader.go",
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


class TestMilestone2:
    """Sticky map, history reader, and merged stall requirements."""

    def test_build_compiles(self) -> None:
        """Go tree must compile."""
        assert CLI.is_file()

    @pytest.mark.parametrize("scenario_file", M2_SCENARIOS)
    def test_replay_matches_reference(self, scenario_file: str) -> None:
        """CLI replay report matches independent Cadence reference FSM."""
        scenario = SCENARIOS / scenario_file
        proc = _replay(scenario)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        cli = json.loads(OUTPUT.read_text(encoding="utf-8"))
        ref = reference_replay(scenario)
        assert cli == ref

    def test_sticky_poll_uses_live_generation(self) -> None:
        """Decision poll after sticky map bump must not mark task lost."""
        scenario = SCENARIOS / "04-sticky-refresh.json"
        proc = _replay(scenario)
        assert proc.returncode == 0, proc.stderr
        report = json.loads(OUTPUT.read_text(encoding="utf-8"))
        assert report["decision_task_lost"] is False
        assert report["sticky_partition"] == "cadence-history-2"

    def test_duplicate_event_id_cursor_by_seq(self) -> None:
        """Duplicate event_id must not jump history_cursor_seq to raw event_id."""
        scenario = SCENARIOS / "05-duplicate-event-id.json"
        proc = _replay(scenario)
        assert proc.returncode == 0, proc.stderr
        report = json.loads(OUTPUT.read_text(encoding="utf-8"))
        assert report["duplicate_events_skipped"] == 1
        assert report["history_cursor_seq"] == 3

    def test_hidden_sticky_mid_run(self) -> None:
        """Hidden sticky generation change mid-run must replay cleanly."""
        scenario = HIDDEN / "hidden-sticky-mid-run.json"
        assert scenario.is_file(), f"missing hidden fixture {scenario}"
        proc = _replay(scenario)
        assert proc.returncode == 0, proc.stderr
        cli = json.loads(OUTPUT.read_text(encoding="utf-8"))
        ref = reference_replay(scenario)
        assert cli == ref

    def test_sticky_only_partial_fix_fails_merged(self) -> None:
        """Fixing sticky map alone must not pass merged stall scenario."""
        partial = Path(__file__).resolve().parent / "partial"
        saved = {k: p.read_bytes() for k, p in MODULES.items()}
        # Sticky stays fixed (golden map from solve2); history reverted to broken.
        shutil.copy2(partial / "broken_reader.go", MODULES["reader"])
        _build()
        proc = _replay(SCENARIOS / "06-merged-stall.json")
        assert proc.returncode == 0
        report = json.loads(OUTPUT.read_text(encoding="utf-8"))
        ref = reference_replay(SCENARIOS / "06-merged-stall.json")
        for path, blob in saved.items():
            MODULES[path].write_bytes(blob)
        _build()
        assert report != ref
        assert report["history_cursor_seq"] != ref["history_cursor_seq"]

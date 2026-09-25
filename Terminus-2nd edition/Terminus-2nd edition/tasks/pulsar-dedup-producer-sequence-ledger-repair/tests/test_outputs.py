"""Behavioral verifier for pulsar-dedup-replay export."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest

from reference_replay import reference_export, reference_snapshot

APP = Path("/app")
SCENARIOS = APP / "fixtures" / "scenarios"
OUTPUT = APP / "output" / "sequence-ledger-export.json"
SNAPSHOT = APP / "state" / "dedup-snapshot.json"
RESET = APP / "scripts" / "reset-state.sh"
CLI = "/usr/local/bin/pulsar-dedup-replay"
PARTIAL = Path(__file__).resolve().parent / "partial"
HIDDEN = Path(__file__).resolve().parent / "hidden_fixtures"

CATALOG = [
    "01-baseline.json",
    "02-dual-topic.json",
    "03-window-duplicate.json",
    "04-epoch-reset.json",
    "05-batch-partial.json",
    "06-replay-same-id.json",
    "07-merged.json",
]

MODULES = {
    "key": APP / "internal/sequence/key.go",
    "window": APP / "internal/sequence/window.go",
    "epoch": APP / "internal/ingest/epoch.go",
    "batch": APP / "internal/batch/publish.go",
    "counter": APP / "internal/replay/counter.go",
    "export": APP / "internal/export/ledger.go",
    "run": APP / "internal/replay/run.go",
    "apply": APP / "internal/sequence/apply.go",
}

ALL_CORE = ["key", "window", "epoch", "batch", "counter", "export", "run"]


def install_broken_except(fixed: dict[str, str]) -> dict[str, bytes]:
    """Install broken module variants except named fixed modules."""
    variants = {name: "broken" for name in ALL_CORE}
    variants.update(fixed)
    return install_modules(variants)


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


def build() -> subprocess.CompletedProcess[str]:
    return run(["go", "build", "-mod=readonly", "-o", CLI, "./cmd/pulsar-dedup-replay"])


def cli_export(scenario: Path, out: Path) -> subprocess.CompletedProcess[str]:
    out.parent.mkdir(parents=True, exist_ok=True)
    return run([CLI, "export", "--scenario", str(scenario), "--output", str(out)])


def install_modules(variants: dict[str, str]) -> dict[str, bytes]:
    saved = {name: MODULES[name].read_bytes() for name in variants}
    for name, variant in variants.items():
        src = PARTIAL / f"{name}_{variant}.go"
        assert src.is_file(), f"missing partial {src}"
        shutil.copy2(src, MODULES[name])
    proc = build()
    assert proc.returncode == 0, proc.stderr
    return saved


def restore_modules(saved: dict[str, bytes]) -> None:
    for name, blob in saved.items():
        MODULES[name].write_bytes(blob)
    proc = build()
    assert proc.returncode == 0, proc.stderr


@pytest.fixture(autouse=True)
def _setup() -> None:
    reset()
    proc = build()
    assert proc.returncode == 0, proc.stderr


class TestPulsarDedupReplay:
    @pytest.mark.parametrize("scenario_file", CATALOG)
    def test_export_matches_reference(self, scenario_file: str) -> None:
        """CLI export matches independent reference for each catalog scenario."""
        scenario = SCENARIOS / scenario_file
        out = APP / "output" / f"export-{scenario_file}"
        proc = cli_export(scenario, out)
        assert proc.returncode == 0, proc.stderr + proc.stdout
        cli = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_export(scenario)
        assert cli == ref

    def test_staging_snapshot_matches_reference(self) -> None:
        """Staging snapshot at /app/state/dedup-snapshot.json matches reference replay."""
        scenario = SCENARIOS / "07-merged.json"
        out = APP / "output" / "snapshot-check.json"
        proc = cli_export(scenario, out)
        assert proc.returncode == 0, proc.stderr
        assert SNAPSHOT.is_file(), "dedup-snapshot.json missing"
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        ref = reference_snapshot(scenario)
        assert snap == ref

    def test_export_barrier_after_broker_persist(self) -> None:
        """Export must not run before broker ack persistence completes."""
        scenario = SCENARIOS / "05-batch-partial.json"
        out = APP / "output" / "barrier-check.json"
        proc = cli_export(scenario, out)
        assert proc.returncode == 0, proc.stderr
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        assert snap["export_before_ack"] is False
        report = json.loads(out.read_text(encoding="utf-8"))
        assert report["export_barrier_ok"] is True

    def test_hidden_dual_producer_trap(self) -> None:
        """Hidden scenario requires producer|topic keying across two topics."""
        scenario = HIDDEN / "dual-producer-trap.json"
        out = APP / "output" / "hidden-trap.json"
        proc = cli_export(scenario, out)
        assert proc.returncode == 0, proc.stderr
        cli = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_export(scenario)
        assert cli == ref

    def test_partial_key_only_export_still_wrong(self) -> None:
        """Fixed stream keying alone leaves export wrong on merged scenario."""
        saved = install_broken_except({"key": "fixed"})
        try:
            scenario = SCENARIOS / "07-merged.json"
            out = APP / "output" / "partial-key.json"
            proc = cli_export(scenario, out)
            assert proc.returncode == 0, proc.stderr
            cli = json.loads(out.read_text(encoding="utf-8"))
            assert cli != reference_export(scenario)
        finally:
            restore_modules(saved)

    def test_partial_apply_decoy_only_still_wrong(self) -> None:
        """Decoy apply helper fix must not pass export on dual-topic scenario."""
        saved = install_modules(
            {name: "broken" for name in ALL_CORE} | {"apply": "fixed"}
        )
        try:
            scenario = SCENARIOS / "02-dual-topic.json"
            out = APP / "output" / "partial-apply.json"
            proc = cli_export(scenario, out)
            assert proc.returncode == 0, proc.stderr
            cli = json.loads(out.read_text(encoding="utf-8"))
            assert cli != reference_export(scenario)
        finally:
            restore_modules(saved)

    def test_partial_counter_only_fails_replay_scenario(self) -> None:
        """Counter-only patch must still fail merged export checks."""
        saved = install_broken_except({"counter": "fixed"})
        try:
            scenario = SCENARIOS / "07-merged.json"
            out = APP / "output" / "partial-counter.json"
            proc = cli_export(scenario, out)
            assert proc.returncode == 0, proc.stderr
            cli = json.loads(out.read_text(encoding="utf-8"))
            assert cli != reference_export(scenario)
        finally:
            restore_modules(saved)

    def test_missing_scenario_exit_two(self, tmp_path: Path) -> None:
        """Missing scenario path returns exit code 2."""
        proc = cli_export(tmp_path / "missing.json", OUTPUT)
        assert proc.returncode == 2

    def test_malformed_scenario_exit_three(self, tmp_path: Path) -> None:
        """Invalid scenario JSON returns exit code 3."""
        bad = tmp_path / "bad.json"
        bad.write_text('{"tenant":""}\n', encoding="utf-8")
        proc = cli_export(bad, OUTPUT)
        assert proc.returncode == 3

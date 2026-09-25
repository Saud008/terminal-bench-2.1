"""Behavioral verifier for temporal-signal-replay export."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from contextlib import contextmanager
from pathlib import Path

import pytest

from reference_replay import procedural_scenario, reference_export, reference_export_from_dict, reference_snapshot

APP = Path("/app")
SCENARIOS = APP / "fixtures" / "scenarios"
OUTPUT = APP / "output" / "signal-history-export.json"
SNAPSHOT = APP / "state" / "signal-snapshot.json"
CLI = "/usr/local/bin/temporal-signal-replay"
PARTIAL = Path(__file__).resolve().parent / "partial"
HIDDEN_DIR = Path("/opt/verifier-fixtures/scenarios")
GOLDEN = Path(__file__).resolve().parent / "verifier-golden"

CATALOG = [
    "01-baseline.json",
    "02-version-pin.json",
    "03-semver-gate.json",
    "04-duplicate-replay.json",
    "05-pre-migration.json",
    "06-heartbeat-server.json",
    "07-merged.json",
    "08-combined-trap.json",
    "09-ack-order-trap.json",
    "10-chained-trap.json",
]

PROC_SEEDS = ("temporal-matrix-5", "temporal-matrix-13", "temporal-matrix-37")

MODULES = {
    "dispatch": APP / "internal/router/dispatch.go",
    "gate": APP / "internal/version/gate.go",
    "export": APP / "internal/export/history.go",
    "dedup": APP / "internal/dedup/ledger.go",
    "ack": APP / "internal/handler/ack.go",
    "clock": APP / "internal/heartbeat/clock.go",
    "staging": APP / "internal/staging/snapshot.go",
}

PROTECTED_SHA256: dict[str, str] = {}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _populate_hashes() -> None:
    for name in CATALOG:
        PROTECTED_SHA256[name] = _sha(SCENARIOS / name)


_populate_hashes()


def run(cmd: list[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PATH": "/usr/local/go/bin:/usr/local/bin:" + os.environ.get("PATH", "")}
    return subprocess.run(
        cmd,
        cwd=str(cwd or APP),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


def build() -> subprocess.CompletedProcess[str]:
    return run(["go", "build", "-mod=readonly", "-o", CLI, "./cmd/temporal-signal-replay"])


def cli_export(scenario: Path, out: Path) -> subprocess.CompletedProcess[str]:
    out.parent.mkdir(parents=True, exist_ok=True)
    return run([CLI, "export", "--scenario", str(scenario), "--output", str(out)])


def install_modules(variants: dict[str, str]) -> dict[str, bytes]:
    proc = run(["bash", "/app/scripts/verifier-rebuild.sh"])
    assert proc.returncode == 0, proc.stderr
    saved = {name: MODULES[name].read_bytes() for name in variants}
    for name, variant in variants.items():
        src = PARTIAL / f"{name}_{variant}.go"
        assert src.is_file(), f"missing partial {src}"
        shutil.copy2(src, MODULES[name])
    proc = build()
    assert proc.returncode == 0, proc.stderr
    return saved


def restore_modules(saved: dict[str, bytes]) -> None:
    proc = run(["bash", "/app/scripts/verifier-rebuild.sh"])
    assert proc.returncode == 0, proc.stderr


@contextmanager
def _single_golden_module(module: str):
    golden = GOLDEN / f"golden_{module}.go"
    assert golden.is_file(), f"missing golden {golden}"
    proc = run(["bash", "/app/scripts/verifier-rebuild.sh"])
    assert proc.returncode == 0, proc.stderr
    saved = {name: path.read_bytes() for name, path in MODULES.items()}
    shutil.copy2(golden, MODULES[module])
    proc = build()
    assert proc.returncode == 0, proc.stderr
    try:
        yield
    finally:
        for name, blob in saved.items():
            MODULES[name].write_bytes(blob)
        proc = run(["bash", "/app/scripts/verifier-rebuild.sh"])
        assert proc.returncode == 0, proc.stderr


class TestTemporalSignalReplay:
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

    def test_protected_fixture_integrity(self) -> None:
        """Guards public scenario bytes via PROTECTED_SHA256 digests."""
        for name in CATALOG:
            assert _sha(SCENARIOS / name) == PROTECTED_SHA256[name], name

    def test_staging_snapshot_matches_reference(self) -> None:
        """Staging snapshot at /app/state/signal-snapshot.json matches reference ingest."""
        scenario = SCENARIOS / "08-combined-trap.json"
        out = APP / "output" / "snapshot-check.json"
        proc = cli_export(scenario, out)
        assert proc.returncode == 0, proc.stderr
        assert SNAPSHOT.is_file(), "signal-snapshot.json missing"
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        ref = reference_snapshot(scenario)
        assert snap == ref

    def test_final_snapshot_staging_written_false(self) -> None:
        """Final persisted signal-snapshot.json must keep staging_written false per handler-ack-order."""
        scenario = SCENARIOS / "07-merged.json"
        out = APP / "output" / "ack-order.json"
        proc = cli_export(scenario, out)
        assert proc.returncode == 0, proc.stderr
        snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        assert snap["staging_written"] is False

    def test_ack_order_export_not_signal_id_sorted(self) -> None:
        """Export history_events must follow ack order, not lexicographic signal_id."""
        scenario = SCENARIOS / "09-ack-order-trap.json"
        out = APP / "output" / "ack-order-trap.json"
        proc = cli_export(scenario, out)
        assert proc.returncode == 0, proc.stderr
        cli = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_export(scenario)
        assert cli == ref
        ids = [row["signal_id"] for row in cli["history_events"]]
        assert ids == ["z-last", "a-first"]

    def test_hidden_version_pin_trap(self) -> None:
        """Verifier-only scenario requires pinned routing, semver gate, dedup, and server heartbeat."""
        scenario = HIDDEN_DIR / "version-pin-trap.json"
        assert scenario.is_file()
        out = APP / "output" / "hidden-trap.json"
        proc = cli_export(scenario, out)
        assert proc.returncode == 0, proc.stderr
        cli = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_export(scenario)
        assert cli == ref

    def test_hidden_migration_semver_trap(self) -> None:
        """Verifier-only scenario combines pre-migration, semver block, dedup, and ack order."""
        scenario = HIDDEN_DIR / "migration-semver-trap.json"
        assert scenario.is_file()
        out = APP / "output" / "hidden-migration.json"
        proc = cli_export(scenario, out)
        assert proc.returncode == 0, proc.stderr
        cli = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_export(scenario)
        assert cli == ref
        assert [e["signal_id"] for e in cli["history_events"]] == ["legacy", "z9", "a1"]

    def test_hidden_semver_order_trap(self) -> None:
        """Hidden scenario combines pin routing, semver gate, dedup, ack order, and heartbeat."""
        scenario = HIDDEN_DIR / "hidden-semver-order-trap.json"
        assert scenario.is_file()
        out = APP / "output" / "hidden-semver-order.json"
        proc = cli_export(scenario, out)
        assert proc.returncode == 0, proc.stderr
        cli = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_export(scenario)
        assert cli == ref
        assert cli["heartbeat_clock_source"] == "server"
        assert [e["signal_id"] for e in cli["history_events"]] == ["z9", "a1", "dup"]

    def test_chained_trap_ack_order_and_dedup(self) -> None:
        """Chained public scenario requires ack order, dedup skip, semver block, and server heartbeat."""
        scenario = SCENARIOS / "10-chained-trap.json"
        out = APP / "output" / "chained-trap.json"
        proc = cli_export(scenario, out)
        assert proc.returncode == 0, proc.stderr
        cli = json.loads(out.read_text(encoding="utf-8"))
        ref = reference_export(scenario)
        assert cli == ref
        assert cli["duplicate_skipped"] == 1
        assert [e["signal_id"] for e in cli["history_events"]] == ["z-last", "dup", "a-first"]

    def test_procedural_seed_matches_reference(self) -> None:
        """VERIFIER_SEED procedural scenario must match independent reference export."""
        seed = os.environ.get("VERIFIER_SEED", "temporal-signal-seed")
        sc = procedural_scenario(seed)
        work = APP / "data" / f"proc-{seed}.json"
        work.parent.mkdir(parents=True, exist_ok=True)
        work.write_text(json.dumps(sc, indent=2) + "\n", encoding="utf-8")
        out = APP / "output" / f"proc-{seed}.json"
        proc = cli_export(work, out)
        assert proc.returncode == 0, proc.stderr
        cli = json.loads(out.read_text(encoding="utf-8"))
        assert cli == reference_export_from_dict(sc)

    @pytest.mark.parametrize("seed", PROC_SEEDS)
    def test_procedural_matrix_matches_reference(self, seed: str) -> None:
        """Independent procedural seeds must match reference export bytes."""
        sc = procedural_scenario(seed)
        work = APP / "data" / f"proc-{seed}.json"
        work.parent.mkdir(parents=True, exist_ok=True)
        work.write_text(json.dumps(sc, indent=2) + "\n", encoding="utf-8")
        out = APP / "output" / f"proc-matrix-{seed}.json"
        proc = cli_export(work, out)
        assert proc.returncode == 0, proc.stderr
        cli = json.loads(out.read_text(encoding="utf-8"))
        assert cli == reference_export_from_dict(sc)

    def test_partial_dispatch_only_export_still_wrong(self) -> None:
        """Fixed routing alone leaves export wrong on merged scenario."""
        saved = install_modules({"dispatch": "fixed", "export": "broken"})
        try:
            scenario = SCENARIOS / "07-merged.json"
            out = APP / "output" / "partial-dispatch.json"
            proc = cli_export(scenario, out)
            assert proc.returncode == 0, proc.stderr
            snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
            ref_snap = reference_snapshot(scenario)
            assert snap["routed_version"] == ref_snap["routed_version"]
            cli = json.loads(out.read_text(encoding="utf-8"))
            assert cli != reference_export(scenario)
        finally:
            restore_modules(saved)

    def test_partial_export_only_routing_still_wrong(self) -> None:
        """Export-only fix fails when dispatch and dedup stay broken."""
        saved = install_modules(
            {"dispatch": "broken", "dedup": "broken", "export": "fixed"}
        )
        try:
            scenario = SCENARIOS / "02-version-pin.json"
            out = APP / "output" / "partial-export.json"
            proc = cli_export(scenario, out)
            assert proc.returncode == 0, proc.stderr
            cli = json.loads(out.read_text(encoding="utf-8"))
            assert cli != reference_export(scenario)
        finally:
            restore_modules(saved)

    def test_partial_dedup_only_fails_duplicate_scenario(self) -> None:
        """Dedup-only patch must still fail merged export checks."""
        saved = install_modules({"dedup": "fixed", "export": "broken"})
        try:
            scenario = SCENARIOS / "04-duplicate-replay.json"
            out = APP / "output" / "partial-dedup.json"
            proc = cli_export(scenario, out)
            assert proc.returncode == 0, proc.stderr
            cli = json.loads(out.read_text(encoding="utf-8"))
            assert cli != reference_export(scenario)
        finally:
            restore_modules(saved)

    def test_partial_gate_only_fails_semver_scenario(self) -> None:
        """Semver gate fix alone leaves export migration filter wrong."""
        saved = install_modules({"gate": "fixed", "export": "broken"})
        try:
            scenario = SCENARIOS / "03-semver-gate.json"
            out = APP / "output" / "partial-gate.json"
            proc = cli_export(scenario, out)
            assert proc.returncode == 0, proc.stderr
            cli = json.loads(out.read_text(encoding="utf-8"))
            assert cli != reference_export(scenario)
        finally:
            restore_modules(saved)

    def test_partial_ack_only_staging_written_wrong(self) -> None:
        """Ack fix alone still fails when broken staging marks staging_written true."""
        saved = install_modules({"ack": "fixed", "export": "broken"})
        try:
            scenario = SCENARIOS / "09-ack-order-trap.json"
            out = APP / "output" / "partial-ack.json"
            proc = cli_export(scenario, out)
            assert proc.returncode == 0, proc.stderr
            snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
            # Broken staging persists staging_written true even when ack no longer mid-writes.
            assert snap["staging_written"] is True
            cli = json.loads(out.read_text(encoding="utf-8"))
            assert cli != reference_export(scenario)
        finally:
            restore_modules(saved)

    def test_partial_clock_only_heartbeat_wrong(self) -> None:
        """Clock fix alone cannot satisfy export when other modules stay broken."""
        saved = install_modules({"clock": "fixed", "export": "broken"})
        try:
            scenario = SCENARIOS / "06-heartbeat-server.json"
            out = APP / "output" / "partial-clock.json"
            proc = cli_export(scenario, out)
            assert proc.returncode == 0, proc.stderr
            cli = json.loads(out.read_text(encoding="utf-8"))
            assert cli != reference_export(scenario)
        finally:
            restore_modules(saved)

    def test_partial_staging_only_snapshot_flag_wrong(self) -> None:
        """Staging fix alone leaves export history and dedup wrong on chained trap."""
        saved = install_modules({"staging": "fixed", "export": "broken"})
        try:
            scenario = SCENARIOS / "10-chained-trap.json"
            out = APP / "output" / "partial-staging.json"
            proc = cli_export(scenario, out)
            assert proc.returncode == 0, proc.stderr
            snap = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
            assert snap["staging_written"] is False
            cli = json.loads(out.read_text(encoding="utf-8"))
            assert cli != reference_export(scenario)
        finally:
            restore_modules(saved)

    @pytest.mark.parametrize("module", ["dispatch", "gate", "dedup", "export", "ack", "clock", "staging"])
    def test_single_golden_module_insufficient(self, module: str) -> None:
        """Each single golden module patch alone leaves most catalog scenarios failing."""
        with _single_golden_module(module):
            mismatches = 0
            for name in CATALOG:
                scenario = SCENARIOS / name
                out = APP / "output" / f"golden-only-{name}"
                if cli_export(scenario, out).returncode != 0:
                    mismatches += 1
                    continue
                cli = json.loads(out.read_text(encoding="utf-8"))
                if cli != reference_export(scenario):
                    mismatches += 1
            assert mismatches >= 5, (
                f"single module {module} left too few mismatches ({mismatches}/{len(CATALOG)})"
            )

    def test_decoy_wrap_only_patch_still_fails(self) -> None:
        """Decoy router wrap helper cannot fix export behavior."""
        proc = run(["bash", "/app/scripts/verifier-rebuild.sh"])
        assert proc.returncode == 0, proc.stderr
        wrap = APP / "internal/router/wrap.go"
        saved = wrap.read_text(encoding="utf-8")
        try:
            wrap.write_text(
                'package router\nfunc MergeRouteTable(a, b map[string]string) map[string]string { return a }\n'
            )
            proc = build()
            assert proc.returncode == 0, proc.stderr
            scenario = SCENARIOS / "08-combined-trap.json"
            out = APP / "output" / "decoy-wrap.json"
            proc = cli_export(scenario, out)
            assert proc.returncode == 0, proc.stderr
            cli = json.loads(out.read_text(encoding="utf-8"))
            assert cli != reference_export(scenario)
        finally:
            wrap.write_text(saved, encoding="utf-8")
            run(["bash", "/app/scripts/verifier-rebuild.sh"])

    def test_verifier_seed_mutation(self) -> None:
        """VERIFIER_SEED mutation appends a signal to reduce static overfitting."""
        for mod in ("dispatch", "gate", "ack", "dedup", "clock", "export", "staging"):
            shutil.copy2(GOLDEN / f"golden_{mod}.go", MODULES[mod])
        proc = build()
        assert proc.returncode == 0, proc.stderr
        seed = os.environ.get("VERIFIER_SEED", "temporal-signal-seed")
        bump = int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:4], 16) % 5
        base = json.loads((SCENARIOS / "01-baseline.json").read_text(encoding="utf-8"))
        base["signals"].append(
            {
                "signal_id": f"mut{bump}",
                "name": "mutated",
                "target_version": base["pinned_version"],
                "server_time_ms": 100 + bump,
            }
        )
        work = APP / "data" / f"mut-{bump}.json"
        work.parent.mkdir(parents=True, exist_ok=True)
        work.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
        out = APP / "output" / "mutated.json"
        proc = cli_export(work, out)
        assert proc.returncode == 0, proc.stderr
        cli = json.loads(out.read_text(encoding="utf-8"))
        assert cli == reference_export(work)

    def test_missing_scenario_exit_two(self, tmp_path: Path) -> None:
        """Missing scenario path returns exit code 2."""
        proc = cli_export(tmp_path / "missing.json", OUTPUT)
        assert proc.returncode == 2

    def test_malformed_scenario_exit_three(self, tmp_path: Path) -> None:
        """Invalid scenario JSON returns exit code 3."""
        bad = tmp_path / "bad.json"
        bad.write_text('{"workflow_id":""}\n', encoding="utf-8")
        proc = cli_export(bad, OUTPUT)
        assert proc.returncode == 3

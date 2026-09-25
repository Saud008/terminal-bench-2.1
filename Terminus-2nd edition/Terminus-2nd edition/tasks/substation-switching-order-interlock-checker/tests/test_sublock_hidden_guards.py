"""Hidden overlay scenarios and guard rails."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from step_contract import load_yard_fixture, reference_simulate_steps

TB3_ROOT = Path("/opt/verifier-fixtures/sublock")
TB3_SCENARIOS = TB3_ROOT / "scenarios"


def _tb3_pipeline(seed: str, scenario: str, output_path: str) -> dict:
    env = os.environ.copy()
    env["TB3_SCENARIO_DIR"] = str(TB3_ROOT)
    bin_path = "/app/bin/relayctl"
    subprocess.run(
        [bin_path, "compile-yard", "--seed", seed, "--scenario", scenario],
        check=True,
        env=env,
    )
    subprocess.run(
        [
            bin_path,
            "verify-order",
            "--seed",
            seed,
            "--scenario",
            scenario,
            "--output",
            output_path,
        ],
        check=True,
        env=env,
    )
    return json.loads(Path(output_path).read_text(encoding="utf-8"))


class TestSublockHiddenOverlays:
    def test_bus_lockout_blocks_attached_breaker(self, seed_pool: list[str]):
        """TB3 overlay rejects breaker action when bus-level lockout is active."""
        rep = _tb3_pipeline(seed_pool[0], "tb3-lockout-bypass", "/app/output/hidden-lockout.json")
        snap = json.loads(Path("/app/var/sub/yard.snapshot").read_text(encoding="utf-8"))
        sf = load_yard_fixture(TB3_SCENARIOS / "tb3-lockout-bypass.json")
        ref = reference_simulate_steps(sf, snap)
        assert "lockout_active" in rep["steps"][0]["reason_codes"]
        assert rep["steps"] == ref["steps"]

    def test_ring_isolation_overlay(self, seed_pool: list[str]):
        """TB3 ring overlay matches reference energization and interlock simulation."""
        rep = _tb3_pipeline(seed_pool[1], "tb3-energize-ring", "/app/output/hidden-ring.json")
        snap = json.loads(Path("/app/var/sub/yard.snapshot").read_text(encoding="utf-8"))
        sf = load_yard_fixture(TB3_SCENARIOS / "tb3-energize-ring.json")
        ref = reference_simulate_steps(sf, snap)
        assert rep["steps"] == ref["steps"]


class TestSublockGuards:
    def test_verify_without_compile_fails(self, seed_pool: list[str]):
        """verify-order without prior compile-yard exits non-zero."""
        proc = subprocess.run(
            [
                "/app/bin/relayctl",
                "verify-order",
                "--seed",
                seed_pool[0],
                "--scenario",
                "basic-isolation",
                "--output",
                "/app/output/no-compile.json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode != 0

    def test_seed_mismatch_rejected(self, seed_pool: list[str]):
        """verify-order rejects seed that does not match yard.snapshot."""
        subprocess.run(
            [
                "/app/bin/relayctl",
                "compile-yard",
                "--seed",
                seed_pool[0],
                "--scenario",
                "basic-isolation",
            ],
            check=True,
        )
        proc = subprocess.run(
            [
                "/app/bin/relayctl",
                "verify-order",
                "--seed",
                "wrong-seed",
                "--scenario",
                "basic-isolation",
                "--output",
                "/app/output/bad-seed.json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode != 0

    def test_decoy_derate_module_absent_from_report(self, seed_pool: list[str]):
        """Decoy derate module does not leak into verify-order JSON output."""
        out_path = "/app/output/guard-decoy.json"
        subprocess.run(
            [
                "/app/bin/relayctl",
                "compile-yard",
                "--seed",
                seed_pool[0],
                "--scenario",
                "basic-isolation",
            ],
            check=True,
        )
        subprocess.run(
            [
                "/app/bin/relayctl",
                "verify-order",
                "--seed",
                seed_pool[0],
                "--scenario",
                "basic-isolation",
                "--output",
                out_path,
            ],
            check=True,
        )
        blob = Path(out_path).read_text(encoding="utf-8").lower()
        assert "weather" not in blob
        assert "derate" not in blob

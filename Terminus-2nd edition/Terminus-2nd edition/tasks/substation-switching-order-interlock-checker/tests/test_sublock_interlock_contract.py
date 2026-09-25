"""Interlock constraint contract rows."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from step_contract import load_yard_fixture, reference_simulate_steps


def _pipeline(seed: str, scenario: str, output_path: str) -> dict:
    bin_path = "/app/bin/relayctl"
    subprocess.run([bin_path, "compile-yard", "--seed", seed, "--scenario", scenario], check=True)
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
    )
    return json.loads(Path(output_path).read_text(encoding="utf-8"))


class TestInterlockContracts:
    def test_parallel_open_guard(self, seed_pool: list[str]):
        """parallel_path_guard blocks open when isolating energized section."""
        rep = _pipeline(seed_pool[0], "parallel-path", "/app/output/contract-parallel.json")
        snap = json.loads(Path("/app/var/sub/yard.snapshot").read_text(encoding="utf-8"))
        sf = load_yard_fixture(Path("/app/fixtures/scenarios/parallel-path.json"))
        ref = reference_simulate_steps(sf, snap)
        assert "open_parallel_risk" in rep["steps"][0]["reason_codes"]
        assert rep["steps"] == ref["steps"]

    def test_dual_source_ring_isolation(self, seed_pool: list[str]):
        """Dual-source ring scenario matches reference interlock simulation."""
        rep = _pipeline(seed_pool[2], "dual-source-ring", "/app/output/contract-ring.json")
        snap = json.loads(Path("/app/var/sub/yard.snapshot").read_text(encoding="utf-8"))
        sf = load_yard_fixture(Path("/app/fixtures/scenarios/dual-source-ring.json"))
        ref = reference_simulate_steps(sf, snap)
        assert rep["steps"] == ref["steps"]

    def test_summary_unsafe_counter(self, seed_pool: list[str]):
        """summary.unsafe_count equals count of unsafe step rows."""
        rep = _pipeline(seed_pool[1], "dual-source-ring", "/app/output/contract-summary.json")
        unsafe = sum(1 for row in rep["steps"] if not row["safe"])
        assert rep["summary"]["unsafe_count"] == unsafe
        assert rep["summary"]["total_steps"] == len(rep["steps"])

    def test_reason_codes_sorted(self, seed_pool: list[str]):
        """Each step reason_codes list is sorted and deduplicated."""
        rep = _pipeline(seed_pool[0], "dual-source-ring", "/app/output/contract-reasons.json")
        for row in rep["steps"]:
            codes = row["reason_codes"]
            assert codes == sorted(set(codes))

    def test_post_step_bus_list_sorted(self, seed_pool: list[str]):
        """energized_buses after each step is lex-sorted."""
        rep = _pipeline(seed_pool[1], "energize-propagation", "/app/output/contract-buses.json")
        for row in rep["steps"]:
            assert row["energized_buses"] == sorted(row["energized_buses"])

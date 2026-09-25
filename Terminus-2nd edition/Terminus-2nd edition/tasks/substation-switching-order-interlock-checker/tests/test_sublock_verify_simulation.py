"""verify-order step simulation vs independent reference_simulate_steps math."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from step_contract import load_yard_fixture, loto_ticket_id, reference_simulate_steps


def _run_verify(seed: str, scenario: str, output_path: str) -> dict:
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


class TestSublockVerifySimulation:
    def test_output_under_app_output(self, seed_pool: list[str]):
        """verify-order writes JSON under /app/output per unsafe-diagnostic-emit.md."""
        out_path = "/app/output/sim-lockout.json"
        rep = _run_verify(seed_pool[0], "lockout-blocks-close", out_path)
        assert out_path.startswith("/app/output")
        assert rep["summary"]["total_steps"] >= 1

    def test_lockout_close_unsafe(self, seed_pool: list[str]):
        """Lockout tag blocks close and matches reference step rows."""
        out_path = "/app/output/sim-lockout2.json"
        rep = _run_verify(seed_pool[1], "lockout-blocks-close", out_path)
        snap = json.loads(Path("/app/var/sub/yard.snapshot").read_text(encoding="utf-8"))
        sf = load_yard_fixture(Path("/app/fixtures/scenarios/lockout-blocks-close.json"))
        ref = reference_simulate_steps(sf, snap)
        assert rep["steps"][0]["safe"] is False
        assert "lockout_active" in rep["steps"][0]["reason_codes"]
        assert rep["steps"] == ref["steps"]

    def test_step_index_gap_flags_out_of_order(self, seed_pool: list[str]):
        """Non-contiguous step_index emits out_of_order per switching-step-contract.md."""
        out_path = "/app/output/sim-order.json"
        rep = _run_verify(seed_pool[0], "step-order-trap", out_path)
        snap = json.loads(Path("/app/var/sub/yard.snapshot").read_text(encoding="utf-8"))
        sf = load_yard_fixture(Path("/app/fixtures/scenarios/step-order-trap.json"))
        ref = reference_simulate_steps(sf, snap)
        assert "out_of_order" in rep["steps"][0]["reason_codes"]
        assert rep["steps"] == ref["steps"]

    def test_cumulative_energization_chain(self, seed_pool: list[str]):
        """Multi-hop close steps propagate energization cumulatively across the chain."""
        out_path = "/app/output/sim-energize.json"
        rep = _run_verify(seed_pool[3], "energize-propagation", out_path)
        snap = json.loads(Path("/app/var/sub/yard.snapshot").read_text(encoding="utf-8"))
        sf = load_yard_fixture(Path("/app/fixtures/scenarios/energize-propagation.json"))
        ref = reference_simulate_steps(sf, snap)
        assert rep["steps"] == ref["steps"]
        assert "bus-s2" in rep["summary"]["final_energized_buses"]

    def test_audit_digest_matches_reference(self, seed_pool: list[str]):
        """audit_digest binds summary counters to ordered step indices."""
        out_path = "/app/output/sim-digest.json"
        rep = _run_verify(seed_pool[2], "lockout-blocks-close", out_path)
        snap = json.loads(Path("/app/var/sub/yard.snapshot").read_text(encoding="utf-8"))
        sf = load_yard_fixture(Path("/app/fixtures/scenarios/lockout-blocks-close.json"))
        ref = reference_simulate_steps(sf, snap)
        assert rep["audit_digest"] == ref["audit_digest"]

    def test_loto_ticket_matches_load_seq(self, seed_pool: list[str]):
        """loto.ticket id derives from seed, scenario, and monotonic load_seq."""
        out_path = "/app/output/sim-ticket.json"
        seed = seed_pool[3]
        _run_verify(seed, "basic-isolation", out_path)
        snap = json.loads(Path("/app/var/sub/yard.snapshot").read_text(encoding="utf-8"))
        ticket = json.loads(Path("/app/var/sub/loto.ticket").read_text(encoding="utf-8"))
        assert ticket["ticket_id"] == loto_ticket_id(seed, "basic-isolation", snap["load_seq"])

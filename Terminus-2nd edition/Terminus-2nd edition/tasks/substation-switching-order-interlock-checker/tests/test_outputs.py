"""G-026 pytest entrypoint — suite uses interlock_contract.step_contract."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

for _sub in ("harness", "interlock_contract", ""):
    _p = f"/app/scripts/{_sub}" if _sub else "/app/scripts"
    if _p not in sys.path:
        sys.path.insert(0, _p)

from step_contract import load_yard_fixture, reference_simulate_steps


def test_g026_sublock_installed():
    """relayctl binary is installed at /app/bin/relayctl per cli-surface contract."""
    assert Path("/app/bin/relayctl").exists()


def test_g026_verify_lockout_reference():
    """verify-order lockout scenario matches independent reference_simulate_steps math."""
    seed = json.loads(Path("/app/fixtures/seeds.json").read_text(encoding="utf-8"))["seeds"][0]
    bin_path = "/app/bin/relayctl"
    subprocess.run([bin_path, "compile-yard", "--seed", seed, "--scenario", "lockout-blocks-close"], check=True)
    out_path = "/app/output/verify-report.json"
    subprocess.run(
        [
            bin_path,
            "verify-order",
            "--seed",
            seed,
            "--scenario",
            "lockout-blocks-close",
            "--output",
            out_path,
        ],
        check=True,
    )
    rep = json.loads(Path(out_path).read_text(encoding="utf-8"))
    snap = json.loads(Path("/app/var/sub/yard.snapshot").read_text(encoding="utf-8"))
    sf = load_yard_fixture(Path("/app/fixtures/scenarios/lockout-blocks-close.json"))
    ref = reference_simulate_steps(sf, snap)
    assert rep["steps"] == ref["steps"]

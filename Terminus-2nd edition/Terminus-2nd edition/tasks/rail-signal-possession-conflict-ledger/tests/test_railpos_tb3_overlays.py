"""TB3 verifier overlay probes for hidden scenarios and runtime overrides."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

for _sub in ("harness", "yard_math", ""):
    _p = f"/app/scripts/{_sub}" if _sub else "/app/scripts"
    if _p not in sys.path:
        sys.path.insert(0, _p)

from interval_checker import reference_ledger
from railpos_cli_paths import SEED_POOL, SNAP_PATH, run_pipeline, wipe

TB3_ROOT = Path("/opt/verifier-fixtures/railpos")
TB3_SCENARIOS = TB3_ROOT / "scenarios"


@pytest.fixture(autouse=True)
def _reset_railpos_workspace():
    wipe()
    yield
    wipe()


def test_r7k2_tb3_fork_closure_hidden_scenario():
    """TB3_SCENARIO_DIR hidden tb3-fork-reach must match oracle conflict ledger."""
    seed = SEED_POOL[0]
    env = {"TB3_SCENARIO_DIR": str(TB3_ROOT)}
    out = run_pipeline(seed, "tb3-fork-reach", fixture_dir=TB3_SCENARIOS, env=env)
    rep = json.loads(out.read_text(encoding="utf-8"))
    snap_seq = json.loads(SNAP_PATH.read_text(encoding="utf-8"))["load_seq"]
    ref = reference_ledger(
        seed,
        "tb3-fork-reach",
        TB3_SCENARIOS / "tb3-fork-reach.json",
        snap_seq,
    )
    assert rep["conflict_groups"] == ref["conflict_groups"]
    assert rep["audit_digest"] == ref["audit_digest"]


def test_r7k2_tb3_override_salt_closure_suppression():
    """tb3-override-zone requires zone-based override suppression on middle block."""
    seed = SEED_POOL[1]
    env = {"TB3_SCENARIO_DIR": str(TB3_ROOT)}
    out = run_pipeline(seed, "tb3-override-zone", fixture_dir=TB3_SCENARIOS, env=env)
    rep = json.loads(out.read_text(encoding="utf-8"))
    snap_seq = json.loads(SNAP_PATH.read_text(encoding="utf-8"))["load_seq"]
    ref = reference_ledger(
        seed,
        "tb3-override-zone",
        TB3_SCENARIOS / "tb3-override-zone.json",
        snap_seq,
    )
    assert rep["summary"]["override_suppressed"] >= 2
    assert rep["conflict_groups"] == ref["conflict_groups"]


def test_r7k2_tb3_closure_salt_participant_keys():
    """TB3_ZONE_SALT must suffix participant ids in emit rows per trackgraph-zone-contract.md."""
    seed = SEED_POOL[2]
    salt = "-tb3"
    env = {"TB3_SCENARIO_DIR": str(TB3_ROOT), "TB3_ZONE_SALT": salt}
    out = run_pipeline(seed, "tb3-fork-reach", fixture_dir=TB3_SCENARIOS, env=env)
    rep = json.loads(out.read_text(encoding="utf-8"))
    snap_seq = json.loads(SNAP_PATH.read_text(encoding="utf-8"))["load_seq"]
    ref = reference_ledger(
        seed,
        "tb3-fork-reach",
        TB3_SCENARIOS / "tb3-fork-reach.json",
        snap_seq,
        salt=salt,
    )
    assert rep["conflict_groups"] == ref["conflict_groups"]

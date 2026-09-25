"""Placement buffer staging snapshot contract tests for nomrep load (ingest-equivalent stage)."""

from __future__ import annotations

import json
import subprocess

import pytest

from placement_atlas_math import reference_load_scenario, reference_scope_alloc
from nomrep_atlas_cli import BUFFER_PATH, CLI_BIN, SEED_POOL, wipe


@pytest.fixture(autouse=True)
def isolate_workspace():
    wipe()
    yield
    wipe()


def test_buffer_load_seq_advances_on_repeat_load():
    """Second load for the same seed must bump load_seq per placement-buffer-schema.md."""
    seed = SEED_POOL[2]
    for _ in range(2):
        proc = subprocess.run(
            [str(CLI_BIN), "load", "--seed", seed, "--scenario", "basic-volume-join"],
            cwd="/app",
            capture_output=True,
            text=True,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
    snap = json.loads(BUFFER_PATH.read_text(encoding="utf-8"))
    assert snap["load_seq"] == 2


def test_buffer_scopes_focus_alloc_with_seed_salt():
    """Focus alloc id in buffer must use seed-scoped allocation ids."""
    seed = SEED_POOL[0]
    subprocess.run(
        [str(CLI_BIN), "load", "--seed", seed, "--scenario", "node-class-precedence"],
        cwd="/app",
        check=True,
    )
    snap = json.loads(BUFFER_PATH.read_text(encoding="utf-8"))
    assert snap["focus_alloc_id"] == reference_scope_alloc(seed, "alloc-gpu-a")


def test_buffer_records_stale_cutoff_from_bundle():
    """Buffer must copy stale_cutoff_index from the scenario bundle."""
    seed = SEED_POOL[1]
    subprocess.run(
        [str(CLI_BIN), "load", "--seed", seed, "--scenario", "stale-allocation-filter"],
        cwd="/app",
        check=True,
    )
    snap = json.loads(BUFFER_PATH.read_text(encoding="utf-8"))
    assert snap["stale_cutoff_index"] == 420


def test_buffer_hydrates_every_allocation_row():
    """Buffer allocations length must match scenario allocation count after scope."""
    seed = SEED_POOL[3]
    sc = reference_load_scenario(
        __import__("pathlib").Path("/app/fixtures/scenarios/reschedule-attempt-chain.json"),
        seed,
    )
    subprocess.run(
        [str(CLI_BIN), "load", "--seed", seed, "--scenario", "reschedule-attempt-chain"],
        cwd="/app",
        check=True,
    )
    snap = json.loads(BUFFER_PATH.read_text(encoding="utf-8"))
    assert len(snap["allocations"]) == len(sc["allocations"])

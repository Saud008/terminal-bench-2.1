"""Signal aspect and adjacent protected-zone trap tests."""

from __future__ import annotations

import json
import sys

import pytest

for _sub in ("harness", "yard_math", ""):
    _p = f"/app/scripts/{_sub}" if _sub else "/app/scripts"
    if _p not in sys.path:
        sys.path.insert(0, _p)

from interval_checker import reference_ledger
from railpos_cli_paths import (
    FIXTURE_DIR,
    SEED_POOL,
    SNAP_PATH,
    run_pipeline,
    wipe,
)


@pytest.fixture(autouse=True)
def _reset_railpos_workspace():
    wipe()
    yield
    wipe()


def test_r7k2_signal_adjacent_protected_zone():
    """restrict on middle block must conflict with reservation using adjacent protected zone."""
    seed = SEED_POOL[0]
    out = run_pipeline(seed, "signal-adjacent")
    rep = json.loads(out.read_text(encoding="utf-8"))
    snap_seq = json.loads(SNAP_PATH.read_text(encoding="utf-8"))["load_seq"]
    ref = reference_ledger(seed, "signal-adjacent", FIXTURE_DIR / "signal-adjacent.json", snap_seq)
    assert rep["summary"]["signal_blocked"] >= 1
    assert rep["conflict_groups"] == ref["conflict_groups"]


def test_r7k2_signal_reason_token_present():
    """signal_restrict reason must appear when aspect blocks reservation."""
    seed = SEED_POOL[1]
    out = run_pipeline(seed, "signal-adjacent")
    rep = json.loads(out.read_text(encoding="utf-8"))
    reasons = {r for row in rep["conflict_groups"] for r in row["reasons"]}
    assert "signal_restrict" in reasons


def test_r7k2_possession_train_reason_on_chain():
    """linear-chain must emit possession_train conflict between head possession and tail train."""
    seed = SEED_POOL[2]
    out = run_pipeline(seed, "linear-chain")
    rep = json.loads(out.read_text(encoding="utf-8"))
    train_rows = [r for r in rep["conflict_groups"] if "possession_train" in r["reasons"]]
    assert len(train_rows) >= 1


def test_r7k2_blocks_sorted_by_kilometer_in_rows():
    """blocks field in each conflict row must sort by kilometer then block_id."""
    seed = SEED_POOL[3]
    out = run_pipeline(seed, "diamond-fork")
    rep = json.loads(out.read_text(encoding="utf-8"))
    km = {b["block_id"]: b["kilometer"] for b in json.loads((FIXTURE_DIR / "diamond-fork.json").read_text())["blocks"]}
    for row in rep["conflict_groups"]:
        keys = [(km.get(b, 0.0), b) for b in row["blocks"]]
        assert keys == sorted(keys)


def test_r7k2_window_clip_half_open():
    """conflict window_start and window_end must clip overlapping half-open intervals."""
    seed = SEED_POOL[4]
    out = run_pipeline(seed, "linear-chain")
    rep = json.loads(out.read_text(encoding="utf-8"))
    row = next(r for r in rep["conflict_groups"] if "possession_train" in r["reasons"])
    assert row["window_start"] == 60
    assert row["window_end"] == 180

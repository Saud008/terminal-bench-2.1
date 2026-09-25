"""Trackgraph zone and possession conflict emit contract tests."""

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


def test_r7k2_emit_linear_chain_matches_reference():
    """linear-chain possession on head must conflict with tail reservation via zone reachability."""
    seed = SEED_POOL[0]
    out = run_pipeline(seed, "linear-chain")
    rep = json.loads(out.read_text(encoding="utf-8"))
    snap_seq = json.loads(SNAP_PATH.read_text(encoding="utf-8"))["load_seq"]
    ref = reference_ledger(seed, "linear-chain", FIXTURE_DIR / "linear-chain.json", snap_seq)
    assert rep["possession_id"] == ref["possession_id"]
    assert rep["conflict_groups"] == ref["conflict_groups"]
    assert rep["summary"] == ref["summary"]
    assert rep["audit_digest"] == ref["audit_digest"]


def test_r7k2_emit_diamond_fork_closure():
    """diamond-fork wing possessions must conflict with combine-point reservation."""
    seed = SEED_POOL[1]
    out = run_pipeline(seed, "diamond-fork")
    rep = json.loads(out.read_text(encoding="utf-8"))
    snap_seq = json.loads(SNAP_PATH.read_text(encoding="utf-8"))["load_seq"]
    ref = reference_ledger(seed, "diamond-fork", FIXTURE_DIR / "diamond-fork.json", snap_seq)
    assert rep["conflict_groups"] == ref["conflict_groups"]
    assert rep["summary"]["total_conflicts"] >= 1


def test_r7k2_half_open_touching_endpoints_no_conflict():
    """Touching half-open endpoints must not create possession_overlap rows."""
    seed = SEED_POOL[2]
    out = run_pipeline(seed, "half-open-edge")
    rep = json.loads(out.read_text(encoding="utf-8"))
    snap_seq = json.loads(SNAP_PATH.read_text(encoding="utf-8"))["load_seq"]
    ref = reference_ledger(seed, "half-open-edge", FIXTURE_DIR / "half-open-edge.json", snap_seq)
    assert rep["summary"]["possession_pairs"] == 0
    assert rep["conflict_groups"] == ref["conflict_groups"]


def test_r7k2_crisis_override_suppresses_conflict():
    """priority-0 override must suppress possession versus reservation overlap."""
    seed = SEED_POOL[3]
    out = run_pipeline(seed, "crisis-override")
    rep = json.loads(out.read_text(encoding="utf-8"))
    snap_seq = json.loads(SNAP_PATH.read_text(encoding="utf-8"))["load_seq"]
    ref = reference_ledger(seed, "crisis-override", FIXTURE_DIR / "crisis-override.json", snap_seq)
    assert rep["summary"]["override_suppressed"] == ref["summary"]["override_suppressed"]
    assert rep["conflict_groups"] == ref["conflict_groups"]


def test_r7k2_group_key_sorted_participants():
    """group_key and participants must use lexicographically sorted ids."""
    seed = SEED_POOL[4]
    out = run_pipeline(seed, "multi-possession-group")
    rep = json.loads(out.read_text(encoding="utf-8"))
    for row in rep["conflict_groups"]:
        assert row["participants"] == sorted(row["participants"])
        assert row["group_key"] == "|".join(row["participants"])


def test_r7k2_conflict_groups_sorted_by_group_key():
    """conflict_groups array must sort by group_key ascending."""
    seed = SEED_POOL[0]
    out = run_pipeline(seed, "multi-possession-group")
    rep = json.loads(out.read_text(encoding="utf-8"))
    keys = [r["group_key"] for r in rep["conflict_groups"]]
    assert keys == sorted(keys)


def test_r7k2_possession_pairs_counter():
    """summary possession_pairs counts possession-versus-possession overlaps only."""
    seed = SEED_POOL[1]
    out = run_pipeline(seed, "multi-possession-group")
    rep = json.loads(out.read_text(encoding="utf-8"))
    snap_seq = json.loads(SNAP_PATH.read_text(encoding="utf-8"))["load_seq"]
    ref = reference_ledger(seed, "multi-possession-group", FIXTURE_DIR / "multi-possession-group.json", snap_seq)
    assert rep["summary"]["possession_pairs"] == ref["summary"]["possession_pairs"]


def test_r7k2_zone_map_transitive_on_chain():
    """zone_map must include transitive blocks on a three-block chain."""
    seed = SEED_POOL[2]
    run_pipeline(seed, "linear-chain")
    snap = json.loads(SNAP_PATH.read_text(encoding="utf-8"))
    zone = snap["zone_map"]["blk-a7"]
    assert "blk-c9" in zone


def test_r7k2_audit_digest_matches_reference():
    """audit_digest must match independent reference remapped hash."""
    seed = SEED_POOL[3]
    out = run_pipeline(seed, "diamond-fork")
    rep = json.loads(out.read_text(encoding="utf-8"))
    snap_seq = json.loads(SNAP_PATH.read_text(encoding="utf-8"))["load_seq"]
    ref = reference_ledger(seed, "diamond-fork", FIXTURE_DIR / "diamond-fork.json", snap_seq)
    assert rep["audit_digest"] == ref["audit_digest"]

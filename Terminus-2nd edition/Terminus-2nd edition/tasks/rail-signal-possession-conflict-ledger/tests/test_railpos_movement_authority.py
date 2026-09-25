"""Movement authority and five-layer audit marker tests."""

from __future__ import annotations

import json
import sys

import pytest

for _sub in ("harness", "yard_math", ""):
    _p = f"/app/scripts/{_sub}" if _sub else "/app/scripts"
    if _p not in sys.path:
        sys.path.insert(0, _p)

from railpos_cli_paths import SEED_POOL, run_pipeline, wipe


@pytest.fixture(autouse=True)
def _reset_railpos_workspace():
    wipe()
    yield
    wipe()


def test_r7k2_summary_exposes_override_suppressed_counter():
    """Layer 4 override suppression must increment summary override_suppressed per two-phase-safety-audit.md."""
    seed = SEED_POOL[3]
    out = run_pipeline(seed, "crisis-override")
    rep = json.loads(out.read_text(encoding="utf-8"))
    assert "override_suppressed" in rep["summary"]
    assert rep["summary"]["override_suppressed"] >= 1


def test_r7k2_diamond_fork_uses_fork_reachability():
    """diamond-fork conflicts must use junction fork reachability not exact block equality."""
    seed = SEED_POOL[1]
    out = run_pipeline(seed, "diamond-fork")
    rep = json.loads(out.read_text(encoding="utf-8"))
    assert rep["summary"]["total_conflicts"] >= 1
    blocks = {b for row in rep["conflict_groups"] for b in row["blocks"]}
    assert "blk-n4" in blocks

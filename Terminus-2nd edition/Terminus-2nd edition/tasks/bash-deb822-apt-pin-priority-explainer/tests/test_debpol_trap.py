"""Hidden debpol trap tests."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from aptpol_contract_math import contract_report
from aptpol_runner import APP, CLI, GRAPH, build_and_report, invoke, wipe


def _overlay(scenario: str) -> Path:
    tmp = APP / "work" / "tb3-root"
    if tmp.exists():
        shutil.rmtree(tmp)
    src = Path("/opt/verifier-fixtures/debpol/scenarios") / scenario
    dst = tmp / scenario
    shutil.copytree(src, dst)
    return tmp


def test_t30c695_q24():
    """Hidden overlay from /opt/verifier-fixtures/debpol/scenarios."""
    wipe()
    root = _overlay("tb3-pin-trap")
    scenario_dir = root / "tb3-pin-trap"
    out = build_and_report("tb3-pin-trap", "run-hidden", scenario_root=root)
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = contract_report(scenario_dir, "run-hidden")
    assert rep["install_candidates"] == ref["install_candidates"]


def test_t30c695_q25():
    """TB3 overlay preserves multi uri from /opt/verifier-fixtures/debpol/scenarios."""
    wipe()
    root = _overlay("tb3-pin-trap")
    env = {"TB3_SCENARIO_ROOT": str(root)}
    proc = invoke(
        [str(CLI), "build-policy", "--scenario", "tb3-pin-trap", "--run-id", "run-h2"],
        env=env,
    )
    assert proc.returncode == 0
    uris = json.loads(GRAPH.read_text(encoding="utf-8"))["origins"][0]["URIs"]
    assert "mirror.example" in uris

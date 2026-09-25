"""Hidden shadedrift TB3 trap tests."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from shadedrift_contract_math import read_tsv_rows, reference_report
from shadedrift_runner import APP, CLI, invoke, pipeline, wipe

POLICY = APP / "config" / "shadedrift.json"


def _overlay(scenario: str) -> Path:
    tmp = APP / "work" / "tb3-root"
    if tmp.exists():
        shutil.rmtree(tmp)
    src = Path("/opt/verifier-fixtures/shadedrift/scenarios") / scenario
    dst = tmp / scenario
    shutil.copytree(src, dst)
    return tmp


def test_tdl19_tb3_rework_boundary_hidden():
    """Hidden tb3-rework-boundary overlay matches reference drift rows."""
    wipe()
    root = _overlay("tb3-rework-boundary")
    out = pipeline("tb3-rework-boundary", "run-tb3-a", scenario_root=root)
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_report(root / "tb3-rework-boundary", "run-tb3-a", POLICY)
    assert rep["drift_rows"] == ref["drift_rows"]


def test_tdl20_tb3_recipe_precedence_hidden():
    """Hidden tb3-recipe-precedence overlay matches reference drift rows."""
    wipe()
    root = _overlay("tb3-recipe-precedence")
    out = pipeline("tb3-recipe-precedence", "run-tb3-b", scenario_root=root)
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_report(root / "tb3-recipe-precedence", "run-tb3-b", POLICY)
    assert rep["drift_rows"] == ref["drift_rows"]


def test_tdl21_tb3_end_inclusive_reading_on_boundary():
    """Boundary reading inside inclusive rework_end keeps rework_applied true."""
    wipe()
    root = _overlay("tb3-rework-boundary")
    scenario_dir = root / "tb3-rework-boundary"
    boundary_key = read_tsv_rows(scenario_dir / "readings.tsv")[-1]["reading_id"]
    out = pipeline("tb3-rework-boundary", "run-tb3-c", scenario_root=root)
    rep = json.loads(out.read_text(encoding="utf-8"))
    boundary = next(r for r in rep["drift_rows"] if r["reading_id"] == boundary_key)
    assert boundary["rework_applied"] is True


def test_tdl22_tb3_overlay_ingest_env():
    """TB3_SCENARIO_ROOT overlay allows ingest-scenario on hidden fixtures."""
    wipe()
    root = _overlay("tb3-recipe-precedence")
    proc = invoke(
        [str(CLI), "ingest-scenario", "--scenario", "tb3-recipe-precedence", "--run-id", "run-tb3-d"],
        env={"TB3_SCENARIO_ROOT": str(root)},
    )
    assert proc.returncode == 0

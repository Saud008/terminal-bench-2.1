"""Hidden TB3 fixture probes — different failure modes than bundled shifts."""

from __future__ import annotations

import json
import os
from pathlib import Path

from wtcda_refmath import reference_safety
from wtcda_subprocess import CLI_BIN, invoke, wipe

TB3_ROOT = Path("/opt/verifier-fixtures/wtcdctl/plant_shifts")


def _run_tb3(shift: str, plant: str) -> dict:
    os.environ["TB3_FIXTURE_DIR"] = str(TB3_ROOT.parent)
    wipe()
    proc = invoke(
        [str(CLI_BIN), "load-shift-dose", "--plant", plant, "--shift", shift],
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    out = Path("/app/output/tb3-safety.json")
    proc2 = invoke(
        [str(CLI_BIN), "export-breach-atlas", "--plant", plant, "--output", str(out)],
    )
    assert proc2.returncode == 0, proc2.stderr + proc2.stdout
    return json.loads(out.read_text(encoding="utf-8"))


def test_wtcda_p23() -> None:
    """TB3 four-minute outage exceeds forward-fill window — minute dose drops vs naive fill-all."""
    got = _run_tb3("tb3-long-outage", "plant-tb3-outage")
    exp = reference_safety(
        "plant-tb3-outage",
        "tb3-long-outage",
        TB3_ROOT / "tb3-long-outage.json",
    )
    assert got["summary"]["breach_count"] == exp["summary"]["breach_count"]
    assert got["breach_atlas_seal"] == exp["breach_atlas_seal"]


def test_wtcda_p24() -> None:
    """TB3 shift applies only chief-operator override; denylisted supervisor factor ignored."""
    got = _run_tb3("tb3-deny-poison", "plant-tb3-deny")
    exp = reference_safety(
        "plant-tb3-deny",
        "tb3-deny-poison",
        TB3_ROOT / "tb3-deny-poison.json",
    )
    assert got["rows"] == exp["rows"]

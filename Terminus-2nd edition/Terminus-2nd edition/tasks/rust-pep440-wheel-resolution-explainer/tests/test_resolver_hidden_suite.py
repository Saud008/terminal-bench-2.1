"""Hidden fixture tests — different failure mode than bundled."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from resolver_cli_support import load_snapshot, pipeline, wipe
from resolver_contract_math import reference_report


def _overlay(scenario: str) -> None:
    tmp = Path("/tmp/whres-overlay")
    if tmp.exists():
        shutil.rmtree(tmp)
    src = Path("/opt/verifier-fixtures/whres/scenarios") / scenario
    shutil.copytree(src, tmp / scenario)
    os.environ["WHRES_SCENARIO_ROOT"] = str(tmp)


def test_hidden_arm_arch_wheel_tag():
    """Hidden marker-and-trap scenario matches reference under verifier-fixtures overlay."""
    wipe()
    assert Path("/opt/verifier-fixtures/whres/scenarios/marker-and-trap").is_dir()
    _overlay("marker-and-trap")
    out = pipeline("marker-and-trap", "run-h1")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_report(Path(os.environ["WHRES_SCENARIO_ROOT"]) / "marker-and-trap", "run-h1")
    assert rep["candidates"] == ref["candidates"]


def test_hidden_post_release_wins():
    """Hidden post-release-trap selects flux-core 1.0.post1 over plain 1.0."""
    wipe()
    assert Path("/opt/verifier-fixtures/whres/scenarios/post-release-trap").is_dir()
    _overlay("post-release-trap")
    out = pipeline("post-release-trap", "run-h2")
    rep = json.loads(out.read_text(encoding="utf-8"))
    row = next(c for c in rep["candidates"] if c["package"] == "flux-core")
    assert row["selected_version"] == "1.0.post1"


def test_hidden_aarch64_target_in_snapshot():
    """Hidden marker-and-trap records aarch64 target_arch in snapshot."""
    wipe()
    assert Path("/opt/verifier-fixtures/whres/scenarios/marker-and-trap").is_dir()
    _overlay("marker-and-trap")
    pipeline("marker-and-trap", "run-h3")
    assert load_snapshot()["target_arch"] == "aarch64"

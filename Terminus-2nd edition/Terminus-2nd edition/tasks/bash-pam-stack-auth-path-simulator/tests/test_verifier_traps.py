"""Hidden fixture tests — different failure mode than bundled."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from pamtrace_harness import APP, run_pipeline, wipe
from pamtrace_independent_math import reference_expected_trace


def _overlay_hidden(scenario: str) -> Path:
    tmp = APP / "work" / "tb3-scenario-root"
    if tmp.exists():
        shutil.rmtree(tmp)
    src = Path("/opt/verifier-fixtures/pamtrace/scenarios") / scenario
    dst_root = tmp / "fixtures" / "scenarios"
    dst = dst_root / scenario
    shutil.copytree(src, dst)
    return dst_root.parent.parent


def test_pt_hidden_tb3_requisite_immediate_abort():
    wipe()
    root = _overlay_hidden("tb3-requisite-trap")
    scenario_dir = root / "fixtures" / "scenarios" / "tb3-requisite-trap"
    # symlink-style: copy scenario into fixtures path for load
    target = APP / "fixtures" / "scenarios" / "tb3-requisite-trap"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(scenario_dir, target)
    out = run_pipeline("tb3-requisite-trap", "run-h1", service="sshd", subject="ivy")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_expected_trace(scenario_dir, "run-h1", "tb3-requisite-trap", "sshd", "ivy")
    assert rep["reason"] == "requisite_failure"
    assert len(rep["steps"]) == len(ref["steps"])
    assert rep["verdict"] == "auth_err"


def test_pt_hidden_nested_group_admin_closure():
    wipe()
    root = _overlay_hidden("tb3-group-nested")
    scenario_dir = root / "fixtures" / "scenarios" / "tb3-group-nested"
    target = APP / "fixtures" / "scenarios" / "tb3-group-nested"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(scenario_dir, target)
    out = run_pipeline("tb3-group-nested", "run-h2", service="sudo", subject="jack")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_expected_trace(scenario_dir, "run-h2", "tb3-group-nested", "sudo", "jack")
    assert "admins" in rep["subject_groups"]
    assert rep["subject_groups"] == ref["subject_groups"]
    assert rep["verdict"] == ref["verdict"]

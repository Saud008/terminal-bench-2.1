"""G-026 fsplatlas subprocess tests with independent splice reference helpers.

Verifier probes document separate ingest (load-capture), reflection-buffer snapshot,
and export (publish-verdict) lanes for the splice acceptance atlas pipeline.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from splice_refmath import load_json, reference_pipeline

APP = Path("/app")
CLI = APP / "bin" / "fsplatlas"
RESET = APP / "scripts" / "reset-workspace.sh"
FIXTURE_ROOT = APP / "fixtures"
PLAN_DIR = APP / "state" / "capture-cache"
EVENT_DIR = APP / "work" / "reflection-buffer"
BIND_DIR = APP / "work" / "topology-snapshot"


def invoke(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False, env=merged)


def wipe() -> None:
    proc = invoke(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def fixture_root(env: dict | None = None) -> Path:
    if env and env.get("TB3_TRACE_ROOT"):
        return Path(env["TB3_TRACE_ROOT"])
    return FIXTURE_ROOT


def run_pipeline(run_id: str, env: dict | None = None) -> Path:
    _ = fixture_root(env)
    steps = [
        [str(CLI), "load-capture", "--run-id", run_id],
        [str(CLI), "scan-reflections", "--run-id", run_id],
        [str(CLI), "correlate-span", "--run-id", run_id],
    ]
    for step in steps:
        proc = invoke(step, env=env)
        assert proc.returncode == 0, proc.stderr + proc.stdout
    out = APP / "output" / f"{run_id}-splice-atlas.json"
    proc = invoke([str(CLI), "publish-verdict", "--run-id", run_id, "--output", str(out)], env=env)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return out


@pytest.fixture(autouse=True)
def _clean():
    wipe()
    yield
    wipe()


def test_cli_binary_exists():
    """Instruction requires fsplatlas installed at /app/bin/fsplatlas."""
    assert CLI.is_file()


def test_load_writes_capture_cache_run00():
    """load-capture must write capture-cache JSON with manifest loss_threshold_db."""
    proc = invoke([str(CLI), "load-capture", "--run-id", "run-00"])
    assert proc.returncode == 0, proc.stderr
    cache_doc = json.loads((PLAN_DIR / "run-00.json").read_text(encoding="utf-8"))
    manifest = load_json(FIXTURE_ROOT / "traces" / "run-00" / "trace_manifest.json")
    assert cache_doc["loss_threshold_db"] == manifest["loss_threshold_db"]


def test_capture_cache_path_under_state():
    """Instruction cites /app/state/capture-cache/ as the plan materialization path."""
    invoke([str(CLI), "load-capture", "--run-id", "run-00"])
    cache_root = "/app/state/capture-cache/"
    assert (Path(cache_root) / "run-00.json").is_file()


def test_instruction_path_roots_literal():
    """Covers instruction paths /app/output and /app/state/capture-cache/."""
    output_root = "/app/output"
    cache_root = "/app/state/capture-cache/"
    out = run_pipeline("run-00")
    assert str(out).startswith(output_root)
    invoke([str(CLI), "load-capture", "--run-id", "run-00"])
    assert (Path(cache_root) / "run-00.json").is_file()


def test_scan_reflections_count_run00():
    """scan-reflections plus publish-verdict must match independent event_count reference."""
    run_pipeline("run-00")
    expected = reference_pipeline(FIXTURE_ROOT, "run-00")
    atlas = json.loads((APP / "output" / "run-00-splice-atlas.json").read_text(encoding="utf-8"))
    assert atlas["event_count"] == expected["event_count"]


def test_output_written_under_app_output():
    """publish-verdict must write acceptance JSON under /app/output."""
    out = run_pipeline("run-00")
    assert str(out).startswith("/app/output")
    assert out.is_file()


def test_full_pipeline_run01_audit_digest():
    """audit_digest must follow acceptance-atlas-fields contract for run-01."""
    expected = reference_pipeline(FIXTURE_ROOT, "run-01")
    out = run_pipeline("run-01")
    atlas = json.loads(out.read_text(encoding="utf-8"))
    assert atlas["audit_digest"] == expected["audit_digest"]


def test_full_pipeline_run02_accepted_segments():
    """Accepted segment count must match connector budget and splice plan reference."""
    expected = reference_pipeline(FIXTURE_ROOT, "run-02")
    out = run_pipeline("run-02")
    atlas = json.loads(out.read_text(encoding="utf-8"))
    assert atlas["accepted_segment_count"] == expected["accepted_segment_count"]


def test_full_pipeline_run03_rejected_segments():
    """Rejected segments must surface when measured loss exceeds planned budget."""
    expected = reference_pipeline(FIXTURE_ROOT, "run-03")
    out = run_pipeline("run-03")
    atlas = json.loads(out.read_text(encoding="utf-8"))
    assert atlas["rejected_segment_count"] == expected["rejected_segment_count"]


def test_tb3_hidden_trace_root():
    """TB3_TRACE_ROOT hidden fixture must change event_count versus bundled runs."""
    env = {"TB3_TRACE_ROOT": "/opt/verifier-fixtures/fsplatlas"}
    expected = reference_pipeline(Path(env["TB3_TRACE_ROOT"]), "tb3-tight-threshold")
    out = run_pipeline("tb3-tight-threshold", env=env)
    atlas = json.loads(out.read_text(encoding="utf-8"))
    assert atlas["event_count"] == expected["event_count"]
    assert atlas["audit_digest"] == expected["audit_digest"]


def test_tb3_loss_threshold_override():
    """TB3_LOSS_THRESHOLD_DB override must alter duplicate suppression counts."""
    env = {"TB3_LOSS_THRESHOLD_DB": "0.08"}
    expected = reference_pipeline(FIXTURE_ROOT, "run-00", threshold_override=0.08)
    out = run_pipeline("run-00", env=env)
    atlas = json.loads(out.read_text(encoding="utf-8"))
    assert atlas["suppressed_duplicate_count"] == expected["suppressed_duplicate_count"]


def test_tb3_reflection_tolerance_override():
    """TB3_REFLECTION_TOLERANCE_M override must change reflection folding behavior."""
    env = {"TB3_REFLECTION_TOLERANCE_M": "3.0"}
    expected = reference_pipeline(FIXTURE_ROOT, "run-01", tol_override=3.0)
    out = run_pipeline("run-01", env=env)
    atlas = json.loads(out.read_text(encoding="utf-8"))
    assert atlas["suppressed_duplicate_count"] == expected["suppressed_duplicate_count"]


def test_output_suffix_splice_atlas():
    """publish-verdict output path must end with -splice-atlas.json suffix."""
    out = run_pipeline("run-00")
    assert out.name.endswith("-splice-atlas.json")


def test_capture_cache_trace_id_run02():
    """load-capture must preserve trace_id from trace_manifest.json."""
    invoke([str(CLI), "load-capture", "--run-id", "run-02"])
    cache_doc = json.loads((PLAN_DIR / "run-02.json").read_text(encoding="utf-8"))
    manifest = load_json(FIXTURE_ROOT / "traces" / "run-02" / "trace_manifest.json")
    assert cache_doc["trace_id"] == manifest["trace_id"]


def test_reflection_buffer_header_suppressed_count():
    """reflection-buffer header must record suppressed_duplicate_count."""
    run_pipeline("run-01")
    hdr = json.loads((EVENT_DIR / "run-01.jsonl").read_text(encoding="utf-8").splitlines()[0])
    assert "suppressed_duplicate_count" in hdr


def test_topology_snapshot_segment_order():
    """topology-snapshot segments must be sorted by segment_id ascending."""
    run_pipeline("run-00")
    bind = json.loads((BIND_DIR / "run-00.json").read_text(encoding="utf-8"))
    ids = [s["segment_id"] for s in bind["segments"]]
    assert ids == sorted(ids)


def test_segment_binding_containment_run00():
    """correlate-span must bind events using spatial segment containment rules."""
    expected = reference_pipeline(FIXTURE_ROOT, "run-00")
    run_pipeline("run-00")
    atlas = json.loads((APP / "output" / "run-00-splice-atlas.json").read_text(encoding="utf-8"))
    assert atlas["segments"][0]["bound_event_count"] == expected["segments"][0]["bound_event_count"]


def test_connector_budget_applied_run02():
    """connector inventory pair_loss_db must appear in segment connector_loss_db."""
    expected = reference_pipeline(FIXTURE_ROOT, "run-02")
    run_pipeline("run-02")
    atlas = json.loads((APP / "output" / "run-02-splice-atlas.json").read_text(encoding="utf-8"))
    assert atlas["segments"][1]["connector_loss_db"] == expected["segments"][1]["connector_loss_db"]


def test_decoy_module_not_in_help():
    """backscatter decoy module must not appear on fsplatlas CLI surface."""
    proc = invoke([str(CLI)])
    assert proc.returncode != 0
    assert "backscatter" not in (proc.stderr + proc.stdout).lower() or "usage" in proc.stderr


def test_cross_run_reset_generation():
    """reset-workspace must reset load_generation counter on fresh load-capture."""
    run_pipeline("run-00")
    wipe()
    invoke([str(CLI), "load-capture", "--run-id", "run-00"])
    cache_doc = json.loads((PLAN_DIR / "run-00.json").read_text(encoding="utf-8"))
    assert cache_doc["load_generation"] == 1


def test_run_catalog_count():
    """Bundled run_catalog.json must list at least four OTDR capture runs."""
    catalog = json.loads((FIXTURE_ROOT / "run_catalog.json").read_text(encoding="utf-8"))
    assert len(catalog["runs"]) >= 4


def test_cache_splices_preserved_run03():
    """load-capture must retain every splice row from splice_plan.json."""
    invoke([str(CLI), "load-capture", "--run-id", "run-03"])
    cache_doc = json.loads((PLAN_DIR / "run-03.json").read_text(encoding="utf-8"))
    plan = load_json(FIXTURE_ROOT / "plans" / "run-03" / "splice_plan.json")
    assert len(cache_doc["splices"]) == len(plan["splices"])


def test_topology_snapshot_suppressed_duplicate_count():
    """topology-snapshot must propagate suppressed_duplicate_count from reflection buffer."""
    expected = reference_pipeline(FIXTURE_ROOT, "run-01")
    run_pipeline("run-01")
    bind = json.loads((BIND_DIR / "run-01.json").read_text(encoding="utf-8"))
    assert bind["suppressed_duplicate_count"] == expected["suppressed_duplicate_count"]

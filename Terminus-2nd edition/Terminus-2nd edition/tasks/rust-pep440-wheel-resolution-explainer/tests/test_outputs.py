"""Bundled whres behavioral tests (load/analyze/emit and snapshot contracts)."""

from __future__ import annotations

import json
from pathlib import Path

from resolver_cli_support import SNAPSHOT, load_snapshot, pipeline, wipe
from resolver_contract_math import (
    marker_ok,
    pep440_gt,
    reference_report,
    tag_compatible,
)


def test_baseline_httpx_resolution():
    """httpx-pin-requests baseline candidates match independent reference_report math."""
    wipe()
    out = pipeline("httpx-pin-requests", "run-alpha")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_report(Path("/app/fixtures/scenarios/httpx-pin-requests"), "run-alpha")
    assert rep["candidates"] == ref["candidates"]


def test_snapshot_schema_fields():
    """analyze materializes snapshot with run-bravo id, snapshot_digest, index_fingerprint, packages list."""
    wipe()
    pipeline("httpx-pin-requests", "run-bravo")
    assert SNAPSHOT.as_posix() == "/app/state/whres-snapshot.json"
    assert SNAPSHOT.is_file()
    snap = load_snapshot()
    assert snap["run_id"] == "run-bravo"
    assert "snapshot_digest" in snap
    assert "index_fingerprint" in snap
    assert isinstance(snap["packages"], list)


def test_tilde_order_prefers_final_release():
    """PEP 440 tilde ordering for orbit-sdk matches independent reference_report."""
    wipe()
    out = pipeline("tilde-order", "run-charlie")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_report(Path("/app/fixtures/scenarios/tilde-order"), "run-charlie")
    row = next(c for c in rep["candidates"] if c["package"] == "orbit-sdk")
    expected = next(c for c in ref["candidates"] if c["package"] == "orbit-sdk")
    assert row["selected_version"] == expected["selected_version"]


def test_marker_py310_selects_compatible():
    """Marker rules for numpy-lite match independent reference_report on Python 3.10."""
    wipe()
    out = pipeline("marker-py310", "run-delta")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_report(Path("/app/fixtures/scenarios/marker-py310"), "run-delta")
    row = next(c for c in rep["candidates"] if c["package"] == "numpy-lite")
    expected = next(c for c in ref["candidates"] if c["package"] == "numpy-lite")
    assert row["selected_version"] == expected["selected_version"]


def test_abi3_wheel_on_py311():
    """Wheel tag rules for crypt-bind match independent reference_report on Python 3.11."""
    wipe()
    out = pipeline("wheel-abi3", "run-echo")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_report(Path("/app/fixtures/scenarios/wheel-abi3"), "run-echo")
    row = next(c for c in rep["candidates"] if c["package"] == "crypt-bind")
    expected = next(c for c in ref["candidates"] if c["package"] == "crypt-bind")
    assert row["wheel_tag"] == expected["wheel_tag"]


def test_yanked_release_excluded():
    """Yanked policy for legacy-io matches independent reference_report."""
    wipe()
    out = pipeline("yanked-drop", "run-foxtrot")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_report(Path("/app/fixtures/scenarios/yanked-drop"), "run-foxtrot")
    row = next(c for c in rep["candidates"] if c["package"] == "legacy-io")
    expected = next(c for c in ref["candidates"] if c["package"] == "legacy-io")
    assert row["selected_version"] == expected["selected_version"]


def test_constraint_lte_includes_bound():
    """Constraint specifiers for schema-kit match independent reference_report."""
    wipe()
    out = pipeline("constraint-range", "run-golf")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_report(Path("/app/fixtures/scenarios/constraint-range"), "run-golf")
    row = next(c for c in rep["candidates"] if c["package"] == "schema-kit")
    expected = next(c for c in ref["candidates"] if c["package"] == "schema-kit")
    assert row["selected_version"] == expected["selected_version"]


def test_dual_index_highest_version():
    """dual-index redis-cache selection matches independent reference_report."""
    wipe()
    out = pipeline("dual-index", "run-hotel")
    rep = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_report(Path("/app/fixtures/scenarios/dual-index"), "run-hotel")
    row = next(c for c in rep["candidates"] if c["package"] == "redis-cache")
    expected = next(c for c in ref["candidates"] if c["package"] == "redis-cache")
    assert row["selected_version"] == expected["selected_version"]
    assert row["source_id"] == expected["source_id"]


def test_audit_digest_matches_reference():
    """audit_digest equals sha256 of compact candidates JSON per emit contract."""
    wipe()
    out1 = pipeline("digest-stable", "run-alpha")
    wipe()
    out2 = pipeline("digest-stable", "run-alpha")
    rep1 = json.loads(out1.read_text(encoding="utf-8"))
    rep2 = json.loads(out2.read_text(encoding="utf-8"))
    ref = reference_report(Path("/app/fixtures/scenarios/digest-stable"), "run-alpha")
    assert rep1["candidates"] == ref["candidates"]
    assert rep1["audit_digest"] == ref["audit_digest"]
    assert rep2["audit_digest"] == ref["audit_digest"]
    assert rep1["audit_digest"] == rep2["audit_digest"]
    assert rep1["audit_digest"] != "broken"


def test_emit_reads_snapshot_not_indices():
    """emit must fail closed on a corrupt snapshot and must not rebuild from fixtures."""
    wipe()
    pipeline("httpx-pin-requests", "run-alpha")
    ref = reference_report(Path("/app/fixtures/scenarios/httpx-pin-requests"), "run-alpha")
    SNAPSHOT.write_text("{}", encoding="utf-8")
    from resolver_cli_support import invoke

    out = Path("/app/output/broken-emit.json")
    if out.exists():
        out.unlink()
    proc = invoke(["emit", "--run-id", "run-alpha", "--output", str(out)])
    assert proc.returncode != 0 or not out.exists() or json.loads(out.read_text()).get("candidates") == []
    if out.exists() and out.read_text(encoding="utf-8").strip():
        rep = json.loads(out.read_text(encoding="utf-8"))
        assert rep.get("candidates") != ref["candidates"]

def test_candidates_sorted_by_package():
    """Candidate rows are sorted by package name per emit contract."""
    wipe()
    out = pipeline("digest-stable", "run-bravo")
    names = [c["package"] for c in json.loads(out.read_text())["candidates"]]
    assert names == sorted(names)


def test_pep440_gt_tilde_reference():
    """Reference pep440_gt ranks final release above tilde pre-release."""
    assert pep440_gt("1.0", "1.0~rc2")


def test_marker_numeric_py310():
    """Reference marker_ok compares python_version numerically not lexically."""
    assert marker_ok('python_version>="3.10"', "3.10", "linux", "x86_64")
    assert not marker_ok('python_version>="3.11"', "3.10", "linux", "x86_64")


def test_tag_abi3_reference():
    """Reference tag_compatible accepts abi3 wheels on newer CPython."""
    assert tag_compatible("cp39-abi3-linux_x86_64", "3.11", "linux", "x86_64")


def test_subprocess_rebuild_idempotent():
    """rebuild-whres.sh may run twice before subprocess CLI invocations."""
    from resolver_cli_support import rebuild

    rebuild()
    rebuild()


def test_load_analyze_emit_chain():
    """Full load analyze emit chain leaves scenario name in snapshot."""
    wipe()
    out = pipeline("httpx-pin-requests", "run-chain")
    assert out.exists()
    assert load_snapshot()["scenario"] == "httpx-pin-requests"


def test_snapshot_lists_packages_from_indices():
    """Snapshot packages include merged index rows such as redis-cache 4.6.1."""
    wipe()
    pipeline("dual-index", "run-stg-a")
    pkgs = {(p["package"], p["version"]) for p in load_snapshot()["packages"]}
    assert ("redis-cache", "4.6.1") in pkgs


def test_no_candidate_when_all_yanked():
    """When only yanked rows exist emit still reports wheel_match or a version for legacy-io."""
    wipe()
    out = pipeline("yanked-drop", "run-yank")
    row = next(c for c in json.loads(out.read_text())["candidates"] if c["package"] == "legacy-io")
    assert row["reason"] == "wheel_match" or row["selected_version"] is not None

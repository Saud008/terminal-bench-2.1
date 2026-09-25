"""Cross-module timetable contract probes.

Verifier contract covers load-roster ingest stage, materialize-graph snapshot,
allocate-slots pass, and publish-atlas export stage (Case 6 pipeline).
"""
from __future__ import annotations

import json
from pathlib import Path

from ttalloc_refmath import (
    graph_fingerprint,
    load_bundle,
    reference_assignments,
)
from ttalloc_driver import (
    ATLAS_JSON,
    CLI_BIN,
    CONFLICT_JSON,
    FIXTURE_ROOT,
    GRAPH_JSON,
    SCENARIO_CAP,
    SCENARIO_CLEAN,
    SCENARIO_IDEM,
    SCENARIO_LAB,
    SCENARIO_MULTI,
    SCENARIO_SPLIT,
    SCENARIO_STABLE,
    SCENARIO_TEACHER,
    run_pipeline,
    wipe_state,
)


def test_ttalloc_cap_constraint_graph_snapshot_written():
    """Verifier contract: constraint graph snapshot written."""
    wipe_state()
    import subprocess

    root = str(FIXTURE_ROOT)
    for step in (
        [str(CLI_BIN), "load-roster", "--scenario", SCENARIO_CLEAN, "--fixture-dir", root],
        [str(CLI_BIN), "materialize-graph", "--scenario", SCENARIO_CLEAN],
    ):
        proc = subprocess.run(step, cwd="/app", capture_output=True, text=True, check=False)
        assert proc.returncode == 0, proc.stderr + proc.stdout
    graph = json.loads(GRAPH_JSON.read_text(encoding="utf-8"))
    assert graph.get("graph_fingerprint")
    assert graph.get("nodes")
    assert graph.get("edges")


def test_ttalloc_cap_graph_fingerprint_matches_reference():
    """Verifier contract: graph fingerprint matches reference."""
    wipe_state()
    run_pipeline(SCENARIO_CLEAN)
    graph = json.loads(GRAPH_JSON.read_text(encoding="utf-8"))
    bundle = load_bundle(FIXTURE_ROOT, SCENARIO_CLEAN)
    assert graph["graph_fingerprint"] == graph_fingerprint(bundle)


def test_ttalloc_cap_lab_section_uses_lab_room():
    """Verifier contract: lab section uses lab room."""
    wipe_state()
    run_pipeline(SCENARIO_LAB)
    atlas = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    ref = reference_assignments(FIXTURE_ROOT, SCENARIO_LAB)
    assert atlas["assignments"] == ref["assignments"]


def test_ttalloc_cap_allocation_pass_increments():
    """Verifier contract: allocation pass increments."""
    wipe_state()
    run_pipeline(SCENARIO_CLEAN)
    first = json.loads(Path("/app/state/allocation-pass.json").read_text(encoding="utf-8"))
    run_pipeline(SCENARIO_CLEAN)
    second = json.loads(Path("/app/state/allocation-pass.json").read_text(encoding="utf-8"))
    assert second["allocation_pass"] == first["allocation_pass"] + 1


def test_ttalloc_cap_atlas_engine_is_ttalloc():
    """Verifier contract: atlas engine is ttalloc."""
    wipe_state()
    run_pipeline(SCENARIO_CLEAN)
    atlas = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    assert atlas["engine"] == "ttalloc"


def test_ttalloc_cap_stable_order_matches_reference():
    """Verifier contract: stable order matches reference."""
    wipe_state()
    run_pipeline(SCENARIO_STABLE)
    atlas = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    ref = reference_assignments(FIXTURE_ROOT, SCENARIO_STABLE)
    assert atlas["assignments"] == ref["assignments"]


def test_ttalloc_cap_publish_blocked_without_allocate():
    """Verifier contract: publish blocked without allocate."""
    wipe_state()
    import subprocess

    proc = subprocess.run(
        [CLI_BIN, "publish-atlas", "--scenario", SCENARIO_CLEAN],
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0


def test_ttalloc_cap_graph_includes_lab_edges():
    """Verifier contract: graph includes lab edges."""
    wipe_state()
    run_pipeline(SCENARIO_LAB)
    graph = json.loads(GRAPH_JSON.read_text(encoding="utf-8"))
    kinds = {e["kind"] for e in graph.get("edges", [])}
    assert "lab_requirement" in kinds


def test_ttalloc_cap_conflict_report_empty_on_clean():
    """Verifier contract: conflict report empty on clean."""
    wipe_state()
    run_pipeline(SCENARIO_CLEAN)
    report = json.loads(CONFLICT_JSON.read_text(encoding="utf-8"))
    assert report["conflicts"] == []


def test_ttalloc_cap_steady_rerun_atlas_bytes():
    """Verifier contract: steady rerun atlas bytes."""
    wipe_state()
    run_pipeline(SCENARIO_IDEM)
    first = ATLAS_JSON.read_bytes()
    run_pipeline(SCENARIO_IDEM)
    second = ATLAS_JSON.read_bytes()
    assert first == second


def test_ttalloc_cap_split_group_same_slot():
    """Verifier contract: split group same slot."""
    wipe_state()
    run_pipeline(SCENARIO_SPLIT)
    atlas = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    ref = reference_assignments(FIXTURE_ROOT, SCENARIO_SPLIT)
    assert atlas["assignments"] == ref["assignments"]


def test_ttalloc_cap_capacity_edge_sum():
    """Verifier contract: capacity edge sum."""
    wipe_state()
    run_pipeline(SCENARIO_CAP)
    atlas = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    ref = reference_assignments(FIXTURE_ROOT, SCENARIO_CAP)
    assert atlas["assignments"] == ref["assignments"]


def test_ttalloc_cap_teacher_conflict_reported():
    """Verifier contract: teacher conflict reported."""
    wipe_state()
    run_pipeline(SCENARIO_TEACHER)
    atlas = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    report = json.loads(CONFLICT_JSON.read_text(encoding="utf-8"))
    ref = reference_assignments(FIXTURE_ROOT, SCENARIO_TEACHER)
    assert atlas["assignments"] == ref["assignments"]
    kinds = {c["kind"] for c in report["conflicts"]}
    assert "teacher_double_book" not in kinds


def test_ttalloc_cap_multi_lab_assignments():
    """Verifier contract: multi lab assignments."""
    wipe_state()
    run_pipeline(SCENARIO_MULTI)
    atlas = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    ref = reference_assignments(FIXTURE_ROOT, SCENARIO_MULTI)
    assert atlas["assignments"] == ref["assignments"]


def test_ttalloc_cap_assignments_sorted_stable():
    """Verifier contract: assignments sorted stable."""
    wipe_state()
    run_pipeline(SCENARIO_CAP)
    atlas = json.loads(ATLAS_JSON.read_text(encoding="utf-8"))
    scores = [row["score"] for row in atlas["assignments"]]
    assert scores == sorted(scores, reverse=True)

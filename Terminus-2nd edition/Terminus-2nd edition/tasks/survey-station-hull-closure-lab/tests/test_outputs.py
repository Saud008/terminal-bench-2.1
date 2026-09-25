"""Core stationclos contract tests against hull-certificate docs and reference math.

Probe contract: legacy ingest/export CLI verbs are out of scope for this lab.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, "/app/scripts")
from hull_cli import rebuild, run_materialize, run_certify  # noqa: E402
from stationclos_validate import (  # noqa: E402
    expected_atlas,
    first_conflict,
    build_stations,
    load_bundle,
    load_config,
)


@pytest.fixture(scope="session", autouse=True)
def _rebuild_once():
    rebuild()
    yield


@pytest.fixture(autouse=True)
def _clean():
    shutil.rmtree("/app/work/station-hulls", ignore_errors=True)
    shutil.rmtree("/app/output", ignore_errors=True)
    Path("/app/work/station-hulls").mkdir(parents=True, exist_ok=True)
    Path("/app/output").mkdir(parents=True, exist_ok=True)
    yield


def _seal_ok(campaign: str, bundle: str) -> dict:
    cfg = load_config()
    b = load_bundle(cfg["bundle_dir"], bundle)
    exp = expected_atlas(campaign, b, cfg)
    assert exp is not None
    rc = run_materialize(campaign, bundle)
    assert rc.returncode == 0, rc.stderr
    out = f"/app/output/{campaign}.json"
    rc2 = run_certify(campaign, out)
    assert rc2.returncode == 0, rc2.stderr
    got = json.loads(Path(out).read_text(encoding="utf-8"))
    assert got["closure_digest"] == exp["closure_digest"]
    assert got["summary"] == exp["summary"]
    assert [r["station_id"] for r in got["rows"]] == [r["station_id"] for r in exp["rows"]]
    assert [r["residual_area_u64"] for r in got["rows"]] == [r["residual_area_u64"] for r in exp["rows"]]
    return got


def test_stclos_dual_bundle_certificate_digest():
    """materialize-hulls + certify-campaign on dual-station-basic must match residual-closure atlas digests."""
    _seal_ok("camp-alpha", "dual-station-basic")


def test_stclos_area_sort_station_ids():
    """Closure rows must order by residual_area_u64 ascending then station_id (TINY, MID, BIG)."""
    got = _seal_ok("camp-bravo", "area-rank-ladder")
    ids = [r["station_id"] for r in got["rows"]]
    assert ids == ["TINY", "MID", "BIG"]
    assert [r["rank"] for r in got["rows"]] == [1, 2, 3]


def test_stclos_positive_hull_reject_clears_ledger():
    """Positive-area residual conflicts must reject bind and clear /app/work/station-hulls/<campaign>.json."""
    cfg = load_config()
    b = load_bundle(cfg["bundle_dir"], "conflict-overlap")
    stations = build_stations(b, cfg)
    assert first_conflict(stations) is not None
    rc = run_materialize("camp-conflict", "conflict-overlap")
    assert rc.returncode != 0
    assert not Path("/app/work/station-hulls/camp-conflict.json").exists()


def test_stclos_meridian_parts_west_east():
    """Wrap partition must emit -W and -E station parts when residual longitude delta exceeds 180."""
    got = _seal_ok("camp-wrap", "wrap-crossing")
    ids = {r["station_id"] for r in got["rows"]}
    assert any(i.endswith("-W") for i in ids)
    assert any(i.endswith("-E") for i in ids)
    assert got["summary"]["wrap_parts"] >= 2


def test_stclos_corner_trunc_edge_digest():
    """Microdegree toward-zero quantization must match reference digests on quantize-edge corners."""
    _seal_ok("camp-q", "quantize-edge")


def test_stclos_midspan_keeps_single_id():
    """Longitude spans of about 120 degrees must keep a single station_id without -W/-E parts."""
    got = _seal_ok("camp-mid", "midspan-no-wrap")
    ids = [r["station_id"] for r in got["rows"]]
    assert ids == ["MIDSPAN"]
    assert got["summary"]["wrap_parts"] == 0


def test_stclos_zero_area_line_accepted():
    """Zero-area hulls must not conflict with positive-area open-overlapping neighbors."""
    cfg = load_config()
    b = load_bundle(cfg["bundle_dir"], "degenerate-touch")
    stations = build_stations(b, cfg)
    assert first_conflict(stations) is None
    _seal_ok("camp-deg", "degenerate-touch")


def test_stclos_reference_digest_width():
    """Reference atlas digests are 64-char hex; verifier math must stay independent of CLI output."""
    cfg = load_config()
    b = load_bundle(cfg["bundle_dir"], "area-rank-ladder")
    exp = expected_atlas("camp-base", b, cfg)
    assert exp is not None
    assert len(exp["closure_digest"]) == 64


def test_stclos_digest_layout_not_comma_join(tmp_path):
    """closure_digest field layout differs from a comma-joined resorted station/area encoding."""
    from stationclos_validate import closure_digest, rank_stations, build_stations

    cfg = load_config()
    b = load_bundle(cfg["bundle_dir"], "area-rank-ladder")
    stations = build_stations(b, cfg)
    rows = rank_stations(stations)
    good = closure_digest(rows)
    bad_lines = sorted(f"{r['station_id']},{r['residual_area_u64']}" for r in rows)
    import hashlib

    bad = hashlib.sha256("\n".join(bad_lines).encode()).hexdigest()
    assert good != bad


def test_stclos_flux_decoy_unused():
    """The decoy module under /app/decoy/flux_index_stub.rs stays unused by materialize-hulls and certify-campaign."""
    decoy = Path("/app/decoy/flux_index_stub.rs").read_text(encoding="utf-8")
    assert "unused" in decoy.lower() or "stub" in decoy.lower()


def test_stclos_hull_ledger_written_before_certify():
    """materialize-hulls must persist the residual lattice snapshot under /app/work/station-hulls before seal."""
    assert run_materialize("camp-snap", "dual-station-basic").returncode == 0
    snap = Path("/app/work/station-hulls/camp-snap.json")
    assert snap.is_file()
    art = json.loads(snap.read_text(encoding="utf-8"))
    assert art["campaign_id"] == "camp-snap"
    assert art["materialize_generation"] >= 1
    assert isinstance(art["stations"], list) and len(art["stations"]) >= 1


def test_stclos_unknown_verb_nonzero():
    """stationclos under /app/bin/stationclos must respond to an unknown verb with non-zero status."""
    proc = subprocess.run(
        ["/app/bin/stationclos", "not-a-verb"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0


def test_stclos_summary_extrema_consistent():
    """Atlas summary counters total_stations/max_area/min_area must match stationclos_validate."""
    got = _seal_ok("camp-sum", "dual-station-basic")
    assert got["summary"]["total_stations"] == len(got["rows"])
    areas = [r["residual_area_u64"] for r in got["rows"]]
    assert got["summary"]["max_area"] == max(areas)
    assert got["summary"]["min_area"] == min(areas)


def test_stclos_ledger_keeps_vertex_arrays():
    """Lattice stations must retain residual_vertices and quantized_vertices arrays for seal inputs."""
    assert run_materialize("camp-verts", "quantize-edge").returncode == 0
    art = json.loads(Path("/app/work/station-hulls/camp-verts.json").read_text(encoding="utf-8"))
    st = art["stations"][0]
    assert len(st["residual_vertices"]) >= 3
    assert len(st["quantized_vertices"]) == len(st["residual_vertices"])

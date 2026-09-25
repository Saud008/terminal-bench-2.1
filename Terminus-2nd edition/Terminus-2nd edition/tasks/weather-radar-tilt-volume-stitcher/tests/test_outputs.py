"""Bundled vrstctl stitched volume report contract tests."""

from __future__ import annotations

import json
import os
import random
import shutil
import tempfile
from pathlib import Path

from stitch_volume_verifier import (
    RND_ELEV_TRAP,
    RND_STATION_TRAP,
    SUBPROC_SAMPLE,
    assert_report_matches,
    bundle_root,
    reference_from_bundle_dir,
    read_buffer_meta,
    run_stitch,
    scrub_var,
)

OUT = "/app/output/"
BUFFER = "/app/var/gate-buffer-{token}.ndjson"


def test_t76e206_gate_buffer_staging_snapshot():
    """Staging snapshot gate-buffer NDJSON row count matches tilt gate inventory."""
    run_stitch("dual-tilt-basic", "ppi-snap")
    meta = read_buffer_meta("ppi-snap")
    assert meta["row_count"] == 8


def test_t76e206_radar_ppi_dual_tilt_report():
    """Dual-tilt PPI bundle report matches independent reference builder."""
    out = run_stitch("dual-tilt-basic", "ppi-dual")
    body = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_from_bundle_dir(bundle_root() / "dual-tilt-basic", "ppi-dual")
    assert_report_matches(body, ref)


def test_t76e206_radar_gate_buffer_ndjson_rows():
    """Stitch materializes gate-buffer NDJSON rows under /app/var."""
    run_stitch("dual-tilt-basic", "ppi-stg")
    meta = read_buffer_meta("ppi-stg")
    assert meta["row_count"] == 8
    lines = Path(BUFFER.format(token="ppi-stg")).read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 8


def test_t76e206_radar_buffer_meta_fingerprint():
    """Gate-buffer meta sidecar records ledger_fingerprint and run_token."""
    run_stitch("dual-tilt-basic", "ppi-meta")
    meta = read_buffer_meta("ppi-meta")
    assert meta["run_token"] == "ppi-meta"
    assert "ledger_fingerprint" in meta


def test_t76e206_radar_elevation_sequence_numeric():
    """Tilt fusion orders elevations numerically not lexically by scan label."""
    out = run_stitch("elevation-order-trap", "ppi-elev")
    body = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_from_bundle_dir(bundle_root() / "elevation-order-trap", "ppi-elev")
    assert body["elevation_sequence"] == [0.5, 1.5]
    assert_report_matches(body, ref)


def test_t76e206_radar_azimuth_bridge_coverage():
    """Azimuth coverage uses bridged centideg across 360 degree wrap."""
    out = run_stitch("azimuth-wrap-trap", "ppi-wrap")
    body = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_from_bundle_dir(bundle_root() / "azimuth-wrap-trap", "ppi-wrap")
    assert body["azimuth_coverage_centideg"] == 250
    assert_report_matches(body, ref)


def test_t76e206_radar_calibration_add_sign():
    """Calibration table adds offset_dbz to raw reflectivity."""
    out = run_stitch("calibration-sign-trap", "ppi-cal")
    body = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_from_bundle_dir(bundle_root() / "calibration-sign-trap", "ppi-cal")
    assert_report_matches(body, ref)


def test_t76e206_radar_quality_mask_exclusion():
    """Masked gates stay excluded from mean_calibrated_dbz totals."""
    out = run_stitch("mask-suppress-trap", "ppi-mask")
    body = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_from_bundle_dir(bundle_root() / "mask-suppress-trap", "ppi-mask")
    assert body["valid_gate_total"] == 6
    assert_report_matches(body, ref)


def test_t76e206_radar_coverage_fraction_sparse():
    """Coverage fraction uses manifest inventory on sparse ray bundles."""
    out = run_stitch("sparse-tilt-trap", "ppi-sparse")
    body = json.loads(out.read_text(encoding="utf-8"))
    ref = reference_from_bundle_dir(bundle_root() / "sparse-tilt-trap", "ppi-sparse")
    assert body["coverage_fraction"] == 0.5
    assert_report_matches(body, ref)


def test_t76e206_radar_report_dest_under_output():
    """Caller --dest must land under /app/output stitched report path."""
    dest = Path(f"{OUT}ppi-dest.json")
    out = run_stitch("dual-tilt-basic", "ppi-dest", dest=dest)
    assert str(out).startswith(OUT)


def test_t76e206_radar_report_digest_stable():
    """report_digest stable across repeated stitch with same token."""
    scrub_var()
    d1 = json.loads(run_stitch("dual-tilt-basic", "ppi-dig").read_text())["report_digest"]
    scrub_var()
    d2 = json.loads(run_stitch("dual-tilt-basic", "ppi-dig").read_text())["report_digest"]
    assert d1 == d2


def test_t76e206_radar_site_bind_snapshot():
    """Site bind JSON snapshot written to /app/var/site-bind during stitch."""
    run_stitch("dual-tilt-basic", "ppi-bind")
    assert Path("/app/var/site-bind-ppi-bind.json").is_file()


def test_t76e206_radar_subprocess_rebuild_path():
    """Cargo rebuild plus subprocess stitch writes /app/output/subproc-check.json."""
    dest = Path(SUBPROC_SAMPLE)
    out = run_stitch("dual-tilt-basic", "ppi-sub", dest=dest)
    assert out.name == "subproc-check.json"


def test_t76e206_radar_station_id_echo():
    """Report station_id echoes bundle station manifest identifier."""
    body = json.loads(run_stitch("dual-tilt-basic", "ppi-sta").read_text())
    assert body["station_id"] == "KMUX"


def test_t76e206_radar_included_rows_match_total():
    """valid_gate_total equals included rows in gate-buffer NDJSON."""
    run_stitch("dual-tilt-basic", "ppi-inc")
    lines = Path(BUFFER.format(token="ppi-inc")).read_text(encoding="utf-8").strip().splitlines()
    included = sum(1 for line in lines if json.loads(line)["included"])
    body = json.loads(Path(f"{OUT}ppi-inc.json").read_text())
    assert body["valid_gate_total"] == included


def test_t76e206_radar_mean_calibrated_positive():
    """mean_calibrated_dbz positive on dual-tilt reflectivity calibration bundle."""
    body = json.loads(run_stitch("dual-tilt-basic", "ppi-mean").read_text())
    assert body["mean_calibrated_dbz"] > 10.0


def test_t76e206_radar_tilt_count_matches_scans():
    """tilt_count equals number of tilt scans in sorted bundle."""
    body = json.loads(run_stitch("dual-tilt-basic", "ppi-tcnt").read_text())
    assert body["tilt_count"] == 2


def test_t76e206_radar_elevation_sequence_monotone():
    """elevation_sequence strictly non-decreasing after numeric sort."""
    seq = json.loads(run_stitch("dual-tilt-basic", "ppi-mon").read_text())["elevation_sequence"]
    assert seq == sorted(seq)


def test_t76e206_radar_randomized_station_suffix():
    """Anti-hardcoding randomized station suffix echoes in report station_id."""
    rng = random.Random(31415)
    suffix = rng.randint(100, 999)
    root = bundle_root() / "dual-tilt-basic"
    meta = json.loads((root / "bundle.json").read_text(encoding="utf-8"))
    expected = f"KMUX{suffix:03d}"
    meta["station"]["station_id"] = expected
    token = f"ppi-rnd{suffix}"
    tmp = Path(tempfile.mkdtemp(prefix="vrst-rnd-"))
    try:
        bundle_dir = tmp / RND_STATION_TRAP
        bundle_dir.mkdir()
        (bundle_dir / "bundle.json").write_text(json.dumps(meta), encoding="utf-8")
        os.environ["VRST_FIXTURE_ROOT"] = str(tmp)
        body = json.loads(run_stitch(RND_STATION_TRAP, token).read_text())
        assert body["station_id"] == expected
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        os.environ.pop("VRST_FIXTURE_ROOT", None)


def test_t76e206_radar_randomized_elevation_offset():
    """Anti-hardcoding randomized elevation angles still sort numerically by tilt_rank."""
    rng = random.Random(27182)
    low = round(rng.uniform(0.2, 0.8), 2)
    high = round(low + rng.uniform(0.5, 1.5), 2)
    root = bundle_root() / "dual-tilt-basic"
    meta = json.loads((root / "bundle.json").read_text(encoding="utf-8"))
    meta["tilt_scans"][0]["elevation_deg"] = high
    meta["tilt_scans"][1]["elevation_deg"] = low
    tmp = Path(tempfile.mkdtemp(prefix="vrst-elev-"))
    try:
        bundle_dir = tmp / RND_ELEV_TRAP
        bundle_dir.mkdir()
        (bundle_dir / "bundle.json").write_text(json.dumps(meta), encoding="utf-8")
        os.environ["VRST_FIXTURE_ROOT"] = str(tmp)
        body = json.loads(run_stitch(RND_ELEV_TRAP, "ppi-relev").read_text())
        assert body["elevation_sequence"] == [low, high]
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        os.environ.pop("VRST_FIXTURE_ROOT", None)

"""Stitch volume verifier contract — vrstctl subprocess driver and contract math."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

APP = Path("/app")
BIN = APP / "bin" / "vrstctl"
BUNDLES = APP / "fixtures" / "bundles"
HIDDEN_TRAP_ROOT = "/opt/verifier-fixtures/vrst"
HIDDEN_PHASE_TRAP = "/opt/verifier-fixtures/vrst/phase-wrap-trap"
HIDDEN_OFFSET_TRAP = "/opt/verifier-fixtures/vrst/offset-channel-trap"
SITE_BIND_SAMPLE = "/app/var/site-bind-ppi-bind.json"
RND_STATION_TRAP = "rnd-station-trap"
RND_ELEV_TRAP = "rnd-elev-trap"
SUBPROC_SAMPLE = "/app/output/subproc-check.json"


def bundle_root() -> Path:
    override = os.environ.get("VRST_FIXTURE_ROOT")
    return Path(override) if override else BUNDLES


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=True, capture_output=True, text=True)


def cargo_rebuild() -> None:
    _run(["bash", str(APP / "scripts" / "rebuild-vrstctl.sh")])


def scrub_var() -> None:
    _run(["bash", str(APP / "scripts" / "reset-var.sh")])


def run_stitch(bundle: str, token: str, dest: Path | None = None) -> Path:
    dest = dest or APP / "output" / f"{token}.json"
    scrub_var()
    cargo_rebuild()
    _run([str(BIN), "stitch", "--bundle", bundle, "--token", token, "--dest", str(dest)])
    return dest


def read_buffer_meta(token: str) -> dict:
    path = APP / "var" / f"gate-buffer-{token}.meta.json"
    return json.loads(path.read_text(encoding="utf-8"))


def assert_report_matches(actual: dict[str, Any], expected: dict[str, Any]) -> None:
    assert actual["bundle_id"] == expected["bundle_id"]
    assert actual["station_id"] == expected["station_id"]
    assert actual["elevation_sequence"] == expected["elevation_sequence"]
    assert actual["tilt_count"] == expected["tilt_count"]
    assert actual["valid_gate_total"] == expected["valid_gate_total"]
    assert abs(actual["mean_calibrated_dbz"] - expected["mean_calibrated_dbz"]) < 0.02
    assert abs(actual["coverage_fraction"] - expected["coverage_fraction"]) < 0.0001
    assert actual["azimuth_coverage_centideg"] == expected["azimuth_coverage_centideg"]
    assert actual["report_digest"] == expected["report_digest"]


def _round2(v: float) -> float:
    return round(v + 0.0, 2)


def _round4(v: float) -> float:
    return round(v + 0.0, 4)


def _order_tilts(tilts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(tilts, key=lambda t: float(t["elevation_deg"]))


def _bridge_azimuth(raw: int, prev_raw: int | None) -> int:
    if prev_raw is not None and raw < prev_raw:
        return raw + 36000
    return raw


def _calibrate(raw_dbz: float, channel: str, table: dict[str, float]) -> float:
    return _round2(raw_dbz + float(table.get(channel, 0.0)))


def _included(mask: int) -> bool:
    return mask == 0


def build_gate_rows(meta: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    tilts = _order_tilts(meta["tilt_scans"])
    offsets = meta["station"]["calibration_offsets_dbz"]
    for tilt in tilts:
        prev: int | None = None
        for ray in tilt["rays"]:
            bridged = _bridge_azimuth(int(ray["azimuth_centideg"]), prev)
            prev = int(ray["azimuth_centideg"])
            for gate in ray["gates"]:
                mask = int(gate["quality_mask"])
                rows.append(
                    {
                        "scan_label": tilt["scan_id"],
                        "tilt_deg": float(tilt["elevation_deg"]),
                        "azimuth_centideg": int(ray["azimuth_centideg"]),
                        "bridged_azimuth_centideg": bridged,
                        "range_bin": int(gate["range_bin"]),
                        "raw_dbz": float(gate["dbz"]),
                        "calibrated_dbz": _calibrate(float(gate["dbz"]), tilt["channel"], offsets),
                        "quality_mask": mask,
                        "included": _included(mask),
                    }
                )
    return rows


def _azimuth_coverage(rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    bridged = [int(r["bridged_azimuth_centideg"]) for r in rows]
    return max(bridged) - min(bridged)


def _coverage_fraction(valid_total: int, tilt_count: int, manifest: dict[str, Any]) -> float:
    expected = int(manifest["expected_ray_count"]) * int(manifest["expected_gate_bins"]) * tilt_count
    if expected == 0:
        return 0.0
    return _round4(valid_total / expected)


def build_reference_report(token: str, meta: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    tilts = _order_tilts(meta["tilt_scans"])
    elevation_sequence = [float(t["elevation_deg"]) for t in tilts]
    included = [r for r in rows if r["included"]]
    valid_gate_total = len(included)
    mean_calibrated_dbz = (
        _round2(sum(r["calibrated_dbz"] for r in included) / valid_gate_total)
        if valid_gate_total
        else 0.0
    )
    coverage_fraction = _coverage_fraction(valid_gate_total, len(tilts), meta["manifest"])
    digest_body = json.dumps(
        {
            "station_id": meta["station"]["station_id"],
            "valid_gate_total": valid_gate_total,
            "mean_calibrated_dbz": mean_calibrated_dbz,
            "coverage_fraction": coverage_fraction,
        },
        separators=(",", ":"),
    )
    report_digest = hashlib.sha256(digest_body.encode()).hexdigest()
    return {
        "run_token": token,
        "bundle_id": meta["bundle_id"],
        "station_id": meta["station"]["station_id"],
        "elevation_sequence": elevation_sequence,
        "tilt_count": len(tilts),
        "valid_gate_total": valid_gate_total,
        "mean_calibrated_dbz": mean_calibrated_dbz,
        "coverage_fraction": coverage_fraction,
        "azimuth_coverage_centideg": _azimuth_coverage(rows),
        "report_digest": report_digest,
    }


def reference_from_bundle_dir(bundle_dir: Path, token: str) -> dict[str, Any]:
    meta = json.loads((bundle_dir / "bundle.json").read_text(encoding="utf-8"))
    rows = build_gate_rows(meta)
    return build_reference_report(token, meta, rows)

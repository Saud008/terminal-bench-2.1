"""G-026 wcspfit subprocess tests with independent astrometry calc helpers."""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
from pathlib import Path

import pytest

APP_ROOT = Path("/app")
CLI = APP_ROOT / "bin" / "wcspfit"
RESET = APP_ROOT / "scripts" / "reset-workspace.sh"
HDR_ROOT = APP_ROOT / "fixtures" / "headers"
WCS_DIR = APP_ROOT / "state" / "wcs-cache"
DET_DIR = APP_ROOT / "work" / "detection-buffer"
XM_DIR = APP_ROOT / "work" / "xmatch-buffer"
MASK_EXCLUDE = 0x02


def invoke(cmd: list[str], env: dict | None = None) -> subprocess.CompletedProcess[str]:
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    return subprocess.run(
        cmd, cwd=str(APP_ROOT), capture_output=True, text=True, check=False, env=run_env
    )


def wipe() -> None:
    proc = invoke(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def bundle_dir(name: str, env: dict | None = None) -> Path:
    root = Path(env["TB3_HEADER_DIR"]) if env and env.get("TB3_HEADER_DIR") else HDR_ROOT
    return root / name


def parse_cards(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        key = line[:8].strip()
        rest = line[8:].strip()
        if rest.startswith("="):
            rest = rest[1:].strip()
        if rest.startswith("'") and rest.endswith("'"):
            rest = rest[1:-1]
        out[key] = rest
    return out


def load_wcs_from_header(hdr_path: Path) -> dict:
    cards = parse_cards(hdr_path.read_text(encoding="utf-8"))
    return {
        "header_epoch": float(cards.get("EPOCH", "2000")),
        "ctype": [cards.get("CTYPE1", "RA---TAN"), cards.get("CTYPE2", "DEC--TAN")],
        "crval": [float(cards["CRVAL1"]), float(cards["CRVAL2"])],
        "crpix": [float(cards["CRPIX1"]), float(cards["CRPIX2"])],
        "cd": [
            [float(cards["CD1_1"]), float(cards["CD1_2"])],
            [float(cards["CD2_1"]), float(cards["CD2_2"])],
        ],
    }


def pix_to_sky(wcs: dict, x: float, y: float) -> tuple[float, float]:
    xi = x - wcs["crpix"][0]
    eta = y - wcs["crpix"][1]
    ra = wcs["crval"][0] + wcs["cd"][0][0] * xi + wcs["cd"][0][1] * eta
    dec = wcs["crval"][1] + wcs["cd"][1][0] * xi + wcs["cd"][1][1] * eta
    return ra, dec


def sep_arcsec(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    r = math.pi / 180.0
    a1, d1, a2, d2 = ra1 * r, dec1 * r, ra2 * r, dec2 * r
    cos_d = math.sin(d1) * math.sin(d2) + math.cos(d1) * math.cos(d2) * math.cos(a1 - a2)
    cos_d = max(-1.0, min(1.0, cos_d))
    return math.degrees(math.acos(cos_d)) * 3600.0


def read_catalog(path: Path) -> dict[str, tuple[float, float, float, int]]:
    out: dict[str, tuple[float, float, float, int]] = {}
    for line in path.read_text(encoding="utf-8").splitlines()[1:]:
        sid, ra, dec, epoch, mask = line.split(",")
        out[sid] = (float(ra), float(dec), float(epoch), int(mask))
    return out


def read_detections(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines()[1:]:
        sid, x, y, flux, mask = line.split(",")
        rows.append(
            {
                "source_id": sid,
                "x_pixel": float(x),
                "y_pixel": float(y),
                "flux": float(flux),
                "mask_bit": int(mask),
            }
        )
    return rows


def reference_matches(
    wcs: dict,
    catalog: dict[str, tuple[float, float, float, int]],
    detections: list[dict],
    tol_arcsec: float,
) -> list[dict]:
    matches: list[dict] = []
    for det in detections:
        cat = catalog.get(det["source_id"])
        if not cat:
            continue
        ra_c, dec_c, _epoch, cat_mask = cat
        pra, pdec = pix_to_sky(wcs, det["x_pixel"], det["y_pixel"])
        sep = sep_arcsec(pra, pdec, ra_c, dec_c)
        if sep <= tol_arcsec:
            masked = bool(
                (det["mask_bit"] & MASK_EXCLUDE) or (cat_mask & MASK_EXCLUDE)
            )
            matches.append(
                {
                    "source_id": det["source_id"],
                    "separation_arcsec": sep,
                    "delta_ra_arcsec": (pra - ra_c) * 3600.0,
                    "delta_dec_arcsec": (pdec - dec_c) * 3600.0,
                    "masked": masked,
                }
            )
    matches.sort(key=lambda m: m["source_id"])
    return matches


def audit_digest(atlas: dict) -> str:
    ids = sorted(m["source_id"] for m in atlas["matches"])
    body = json.dumps(
        {
            "match_count": atlas["match_count"],
            "active_count": atlas["active_count"],
            "source_ids": ids,
            "run_id": atlas["run_id"],
        },
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(body.encode()).hexdigest()


def reference_atlas(run_id: str, matches: list[dict]) -> dict:
    active = [m for m in matches if not m["masked"]]
    if active:
        rms_ra = math.sqrt(sum(m["delta_ra_arcsec"] ** 2 for m in active) / len(active))
        rms_dec = math.sqrt(sum(m["delta_dec_arcsec"] ** 2 for m in active) / len(active))
    else:
        rms_ra = rms_dec = 0.0
    atlas = {
        "run_id": run_id,
        "match_count": len(matches),
        "active_count": len(active),
        "rms_ra_arcsec": rms_ra,
        "rms_dec_arcsec": rms_dec,
        "matches": matches,
        "audit_digest": "",
    }
    atlas["audit_digest"] = audit_digest(atlas)
    return atlas


def run_pipeline(run_id: str, bundle: str, *, env: dict | None = None) -> Path:
    bdir = bundle_dir(bundle, env)
    hdr = bdir / "image.hdr"
    cat = bdir / "catalog.csv"
    det = bdir / "detections.csv"
    for step in (
        [str(CLI), "parse-header", "--run-id", run_id, "--header", str(hdr)],
        [
            str(CLI),
            "buffer-detections",
            "--run-id",
            run_id,
            "--catalog",
            str(cat),
            "--detections",
            str(det),
        ],
        [str(CLI), "crossmatch", "--run-id", run_id],
    ):
        proc = invoke(step, env=env)
        assert proc.returncode == 0, proc.stderr + proc.stdout
    out = APP_ROOT / "output" / f"{run_id}-residual-atlas.json"
    proc = invoke(
        [str(CLI), "profile-residuals", "--run-id", run_id, "--output", str(out)],
        env=env,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    return out


@pytest.fixture(autouse=True)
def _clean():
    wipe()
    yield
    wipe()


def test_t5a4c8e_cli_binary_exists():
    """Verifier checks wcspfit is installed at /app/bin/wcspfit per instruction."""
    assert CLI.is_file()


def test_t5a4c8e_parse_header_cache_schema_field00():
    """parse-header writes /app/state/wcs-cache/<run-id>.json with WCS fields from header cards."""
    run_id = "t-hdr-00"
    hdr = bundle_dir("field-00") / "image.hdr"
    proc = invoke([str(CLI), "parse-header", "--run-id", run_id, "--header", str(hdr)])
    assert proc.returncode == 0, proc.stderr
    wcs_cache = json.loads((WCS_DIR / f"{run_id}.json").read_text(encoding="utf-8"))
    ref = load_wcs_from_header(hdr)
    assert wcs_cache["ctype"] == ref["ctype"]
    assert wcs_cache["crval"] == ref["crval"]
    assert wcs_cache["crpix"] == ref["crpix"]
    assert wcs_cache["wcs_revision"] == 1


def test_t5a4c8e_wcs_cache_snapshot_schema():
    """wcs-cache snapshot JSON schema lists required WCS keys after parse-header."""
    run_id = "t-snap-schema"
    hdr = bundle_dir("field-02") / "image.hdr"
    proc = invoke([str(CLI), "parse-header", "--run-id", run_id, "--header", str(hdr)])
    assert proc.returncode == 0, proc.stderr
    snap = json.loads((WCS_DIR / f"{run_id}.json").read_text(encoding="utf-8"))
    for key in ("run_id", "header_epoch", "ctype", "crval", "crpix", "cd", "wcs_revision"):
        assert key in snap


def test_t5a4c8e_cli_ingest_only_patch_leaves_atlas_incomplete():
    """ingest-only partial fix cannot pass profile-residuals export without crossmatch buffer."""
    run_id = "t-ingest-only"
    bdir = bundle_dir("field-00")
    hdr, cat, det = bdir / "image.hdr", bdir / "catalog.csv", bdir / "detections.csv"
    proc = invoke([str(CLI), "parse-header", "--run-id", run_id, "--header", str(hdr)])
    assert proc.returncode == 0, proc.stderr
    proc = invoke(
        [
            str(CLI),
            "buffer-detections",
            "--run-id",
            run_id,
            "--catalog",
            str(cat),
            "--detections",
            str(det),
        ]
    )
    assert proc.returncode == 0, proc.stderr
    out = APP_ROOT / "output" / f"{run_id}-residual-atlas.json"
    proc = invoke(
        [str(CLI), "profile-residuals", "--run-id", run_id, "--output", str(out)]
    )
    assert proc.returncode != 0 or not out.is_file()


def test_t5a4c8e_wcs_cache_directory_contract():
    """Instruction cache path /app/state/wcs-cache/ receives JSON after parse-header."""
    run_id = "t-wcs-dir"
    hdr = bundle_dir("field-00") / "image.hdr"
    proc = invoke([str(CLI), "parse-header", "--run-id", run_id, "--header", str(hdr)])
    assert proc.returncode == 0, proc.stderr
    wcs_cache_path = WCS_DIR / f"{run_id}.json"
    assert str(wcs_cache_path).startswith("/app/state/wcs-cache/")
    assert wcs_cache_path.is_file()


def test_t5a4c8e_output_directory_contract():
    """profile-residuals writes caller output under /app/output/ with -residual-atlas.json suffix."""
    run_id = "t-out-dir"
    out = run_pipeline(run_id, "field-00")
    assert str(out).startswith("/app/output/")
    assert out.is_file()


def test_t5a4c8e_wcs_revision_increments():
    """Repeated parse-header for same run id increments wcs_revision per wcs-cache-schema.md."""
    run_id = "t-gen"
    hdr = bundle_dir("field-01") / "image.hdr"
    invoke([str(CLI), "parse-header", "--run-id", run_id, "--header", str(hdr)])
    invoke([str(CLI), "parse-header", "--run-id", run_id, "--header", str(hdr)])
    wcs_cache = json.loads((WCS_DIR / f"{run_id}.json").read_text(encoding="utf-8"))
    assert wcs_cache["wcs_revision"] == 2


def test_t5a4c8e_pixel_to_sky_independent_field01():
    """Crossmatch delta_ra_arcsec matches independent TAN pixel-to-sky linearization."""
    run_id = "t-pix"
    bdir = bundle_dir("field-01")
    run_pipeline(run_id, "field-01")
    ref_wcs = load_wcs_from_header(bdir / "image.hdr")
    det = read_detections(bdir / "detections.csv")[0]
    ra, dec = pix_to_sky(ref_wcs, det["x_pixel"], det["y_pixel"])
    xm = (XM_DIR / f"{run_id}.jsonl").read_text(encoding="utf-8").strip().splitlines()
    first_match = json.loads(xm[1])
    assert abs(first_match["delta_ra_arcsec"] - (ra - read_catalog(bdir / "catalog.csv")[det["source_id"]][0]) * 3600) < 0.05


def test_t5a4c8e_buffer_detections_jsonl_header():
    """buffer-detections writes JSONL under /app/work/detection-buffer/ with header wcs_revision."""
    run_id = "t-stage"
    bdir = bundle_dir("field-02")
    invoke([str(CLI), "parse-header", "--run-id", run_id, "--header", str(bdir / "image.hdr")])
    invoke(
        [
            str(CLI),
            "buffer-detections",
            "--run-id",
            run_id,
            "--catalog",
            str(bdir / "catalog.csv"),
            "--detections",
            str(bdir / "detections.csv"),
        ]
    )
    lines = (DET_DIR / f"{run_id}.jsonl").read_text(encoding="utf-8").splitlines()
    hdr = json.loads(lines[0])
    assert hdr["wcs_revision"] >= 1
    assert len(lines) > 1


def test_t5a4c8e_crossmatch_count_field02():
    """crossmatch match_count and active_count align with geodesy calc crossmatch."""
    run_id = "t-xm-02"
    bdir = bundle_dir("field-02")
    ref_wcs = load_wcs_from_header(bdir / "image.hdr")
    cat = read_catalog(bdir / "catalog.csv")
    det = read_detections(bdir / "detections.csv")
    target = reference_matches(ref_wcs, cat, det, 2.5)
    run_pipeline(run_id, "field-02")
    atlas = json.loads((APP_ROOT / "output" / f"{run_id}-residual-atlas.json").read_text())
    assert atlas["match_count"] == len(target)
    assert atlas["active_count"] == sum(1 for m in target if not m["masked"])


def test_t5a4c8e_masked_source_excluded_from_rms_field03():
    """Masked sources do not contribute to RMS fields per mask-bit-exclude-contract.md."""
    run_id = "t-mask"
    bdir = bundle_dir("field-03")
    ref_wcs = load_wcs_from_header(bdir / "image.hdr")
    cat = read_catalog(bdir / "catalog.csv")
    det = read_detections(bdir / "detections.csv")
    target = reference_atlas(run_id, reference_matches(ref_wcs, cat, det, 2.5))
    out = run_pipeline(run_id, "field-03")
    atlas = json.loads(out.read_text(encoding="utf-8"))
    assert atlas["active_count"] == target["active_count"]
    assert abs(atlas["rms_ra_arcsec"] - target["rms_ra_arcsec"]) < 0.02
    assert abs(atlas["rms_dec_arcsec"] - target["rms_dec_arcsec"]) < 0.02


def test_t5a4c8e_residual_atlas_digest_field00():
    """audit_digest matches SHA256 over sorted source_ids per residual-atlas-fields.md."""
    run_id = "t-dig"
    out = run_pipeline(run_id, "field-00")
    atlas = json.loads(out.read_text(encoding="utf-8"))
    assert atlas["audit_digest"] == audit_digest(atlas)


def test_t5a4c8e_full_pipeline_field00():
    """End-to-end pipeline on field-00 bundle matches calc atlas digest."""
    run_id = "t-full-00"
    bdir = bundle_dir("field-00")
    ref_wcs = load_wcs_from_header(bdir / "image.hdr")
    target = reference_atlas(
        run_id,
        reference_matches(
            ref_wcs,
            read_catalog(bdir / "catalog.csv"),
            read_detections(bdir / "detections.csv"),
            2.5,
        ),
    )
    out = run_pipeline(run_id, "field-00")
    atlas = json.loads(out.read_text(encoding="utf-8"))
    assert atlas["match_count"] == target["match_count"]
    assert atlas["audit_digest"] == target["audit_digest"]


def test_t5a4c8e_full_pipeline_field01():
    """End-to-end pipeline on field-01 bundle produces target match row count."""
    run_id = "t-full-01"
    bdir = bundle_dir("field-01")
    ref_wcs = load_wcs_from_header(bdir / "image.hdr")
    target = reference_atlas(
        run_id,
        reference_matches(
            ref_wcs,
            read_catalog(bdir / "catalog.csv"),
            read_detections(bdir / "detections.csv"),
            2.5,
        ),
    )
    out = run_pipeline(run_id, "field-01")
    atlas = json.loads(out.read_text(encoding="utf-8"))
    assert len(atlas["matches"]) == target["match_count"]


def test_t5a4c8e_tb3_hidden_header_overlay():
    """TB3_HEADER_DIR overlay bundles resolve hidden header fixtures for crossmatch."""
    run_id = "t-tb3-hdr"
    env = {"TB3_HEADER_DIR": "/opt/verifier-fixtures/wcspfit/headers"}
    bdir = bundle_dir("tb3-epoch-shift", env)
    ref_wcs = load_wcs_from_header(bdir / "image.hdr")
    target = reference_atlas(
        run_id,
        reference_matches(
            ref_wcs,
            read_catalog(bdir / "catalog.csv"),
            read_detections(bdir / "detections.csv"),
            2.5,
        ),
    )
    out = run_pipeline(run_id, "tb3-epoch-shift", env=env)
    atlas = json.loads(out.read_text(encoding="utf-8"))
    assert atlas["match_count"] == target["match_count"]
    assert atlas["audit_digest"] == target["audit_digest"]


def test_t5a4c8e_tb3_match_arcsec_override():
    """TB3_MATCH_ARCSEC overrides default arcsecond tolerance from sphere-crossmatch-policy.md."""
    run_id = "t-tb3-tol"
    env = {"TB3_MATCH_ARCSEC": "0.5"}
    bdir = bundle_dir("field-00")
    ref_wcs = load_wcs_from_header(bdir / "image.hdr")
    target = reference_atlas(
        run_id,
        reference_matches(
            ref_wcs,
            read_catalog(bdir / "catalog.csv"),
            read_detections(bdir / "detections.csv"),
            0.5,
        ),
    )
    out = run_pipeline(run_id, "field-00", env=env)
    atlas = json.loads(out.read_text(encoding="utf-8"))
    assert atlas["match_count"] == target["match_count"]


def test_t5a4c8e_wcs_cache_crval_not_swapped_field02():
    """CRVAL1 and CRVAL2 must not be swapped when extracted from FITS header cards."""
    run_id = "t-crval"
    hdr = bundle_dir("field-02") / "image.hdr"
    invoke([str(CLI), "parse-header", "--run-id", run_id, "--header", str(hdr)])
    wcs_cache = json.loads((WCS_DIR / f"{run_id}.json").read_text(encoding="utf-8"))
    ref = load_wcs_from_header(hdr)
    assert wcs_cache["crval"] == ref["crval"]


def test_t5a4c8e_separation_uses_arcsecond_tolerance():
    """Crossmatch tolerance is interpreted in arcseconds not degrees."""
    run_id = "t-tol"
    bdir = bundle_dir("field-01")
    ref_wcs = load_wcs_from_header(bdir / "image.hdr")
    cat = read_catalog(bdir / "catalog.csv")
    det = read_detections(bdir / "detections.csv")
    target_n = len(reference_matches(ref_wcs, cat, det, 2.5))
    run_pipeline(run_id, "field-01")
    atlas = json.loads((APP_ROOT / "output" / f"{run_id}-residual-atlas.json").read_text())
    assert atlas["match_count"] == target_n


def test_t5a4c8e_catalog_mask_propagates_field03():
    """catalog mask_flags propagate into detection buffer catalog_mask column."""
    run_id = "t-cmask"
    bdir = bundle_dir("field-03")
    invoke([str(CLI), "parse-header", "--run-id", run_id, "--header", str(bdir / "image.hdr")])
    invoke(
        [
            str(CLI),
            "buffer-detections",
            "--run-id",
            run_id,
            "--catalog",
            str(bdir / "catalog.csv"),
            "--detections",
            str(bdir / "detections.csv"),
        ]
    )
    lines = (DET_DIR / f"{run_id}.jsonl").read_text(encoding="utf-8").splitlines()[1:]
    rows = [json.loads(ln) for ln in lines]
    cat = read_catalog(bdir / "catalog.csv")
    for row in rows:
        assert row["catalog_mask"] == cat[row["source_id"]][3]


def test_t5a4c8e_match_row_source_rank_deterministic():
    """Residual atlas matches sort by source_id for deterministic atlas write."""
    run_id = "t-order"
    out = run_pipeline(run_id, "field-02")
    atlas = json.loads(out.read_text(encoding="utf-8"))
    ids = [m["source_id"] for m in atlas["matches"]]
    assert ids == sorted(ids)


def test_t5a4c8e_output_suffix_residual_atlas():
    """Output filenames end with -residual-atlas.json per instruction."""
    run_id = "t-suffix"
    out = run_pipeline(run_id, "field-00")
    assert out.name.endswith("-residual-atlas.json")


def test_t5a4c8e_decoy_module_not_in_binary_help():
    """plate-model decoy module is not exposed as a wcspfit subcommand."""
    proc = invoke([str(CLI)])
    assert proc.returncode != 0
    assert "plate" not in (proc.stderr + proc.stdout).lower()


def test_t5a4c8e_cross_run_persistence_reset():
    """reset-workspace clears wcs-cache so wcs_revision restarts at 1 after wipe."""
    run_id = "t-persist"
    run_pipeline(run_id, "field-00")
    wipe()
    run_pipeline(run_id, "field-00")
    wcs_cache = json.loads((WCS_DIR / f"{run_id}.json").read_text(encoding="utf-8"))
    assert wcs_cache["wcs_revision"] == 1


def test_t5a4c8e_bundled_catalog_fixture_count():
    """bundle_catalog.json lists at least four randomized header bundles."""
    catalog = json.loads((APP_ROOT / "fixtures" / "bundle_catalog.json").read_text())
    assert len(catalog["bundles"]) >= 4


def test_t5a4c8e_independent_geodesy_sep_small_angle():
    """Great-circle separation helper matches small-angle arcsecond expectation."""
    sep = sep_arcsec(180.0, 45.0, 180.0001, 45.0)
    assert 0.2 < sep < 0.5

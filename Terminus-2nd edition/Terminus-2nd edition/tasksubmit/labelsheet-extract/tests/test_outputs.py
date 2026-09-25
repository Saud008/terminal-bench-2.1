"""Behavioral verifier for host-local sheetd mark sheet imposition admission ops."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest
from PIL import Image
from reference_sheet import OversizedError, reference_impose, reference_sample

APP = Path("/app")
CLI = "/app/bin/sheetd"
FIXTURES = APP / "fixtures"
MARKS = FIXTURES / "marks"
CATALOG = FIXTURES / "catalog.json"
OUTPUT = APP / "output"
RESET = APP / "scripts/reset-state.sh"

CATALOG_DATA = json.loads(CATALOG.read_text(encoding="utf-8"))
SEEDS = json.loads((FIXTURES / "seeds.json").read_text(encoding="utf-8"))
IMPOSE_SEEDS = SEEDS["seeds"]
CATALOG_SEED = SEEDS["catalog_seed"]
OVERSIZE_SEED = SEEDS["oversize_seed"]

PROTECTED = [
    "fixtures/catalog.json",
    "fixtures/seeds.json",
    "fixtures/marks/arrow_f0.png",
    "fixtures/marks/arrow_f1.png",
    "fixtures/marks/banner_wide.png",
    "fixtures/marks/banner_oversize.png",
    "fixtures/marks/blade_tall.png",
    "fixtures/marks/coin_small.png",
    "fixtures/marks/edge_sample.png",
    "fixtures/marks/gem_square.png",
    "docs/sheet-contract.md",
    "docs/sheet-ops-workflow.md",
    "docs/sheet-runtime-paths.md",
    "docs/ledger-schema.md",
    "docs/exit-codes.md",
]


def _sha256(rel: str) -> str:
    return hashlib.sha256((APP / rel).read_bytes()).hexdigest()


PROTECTED_SHA256 = {rel: _sha256(rel) for rel in PROTECTED}


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(APP), capture_output=True, text=True, check=False)


def reset() -> None:
    proc = run(["bash", str(RESET)])
    assert proc.returncode == 0, proc.stderr or proc.stdout


def impose_cli(set_name: str, seed: int) -> tuple[Path, Path]:
    sheet_out = OUTPUT / f"sheet-{set_name}-{seed}.png"
    ledger_out = OUTPUT / f"ledger-{set_name}-{seed}.json"
    proc = run(
        [
            CLI,
            "impose",
            "--catalog",
            str(CATALOG),
            "--marks",
            str(MARKS),
            "--set",
            set_name,
            "--seed",
            str(seed),
            "--sheet-out",
            str(sheet_out),
            "--ledger-out",
            str(ledger_out),
        ]
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    return sheet_out, ledger_out


def sample_cli(
    sheet: Path, ledger: Path, mark: str, frame: int, u: float, v: float
) -> dict:
    proc = run(
        [
            CLI,
            "sample",
            "--sheet",
            str(sheet),
            "--ledger",
            str(ledger),
            "--mark",
            mark,
            "--frame",
            str(frame),
            "--u",
            str(u),
            "--v",
            str(v),
        ]
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    return json.loads(proc.stdout.strip())


@pytest.fixture(autouse=True)
def _reset_output() -> None:
    reset()


def test_fixture_integrity() -> None:
    """Protected docs and mark bytes must remain unchanged."""
    for rel, expected in PROTECTED_SHA256.items():
        assert _sha256(rel) == expected


@pytest.mark.parametrize("set_name", ["core-marks"])
@pytest.mark.parametrize("seed", IMPOSE_SEEDS)
def test_ledger_matches_reference(set_name: str, seed: int) -> None:
    """Ledger JSON including checksum must match the independent reference compositor."""
    _, ledger_out = impose_cli(set_name, seed)
    got = json.loads(ledger_out.read_text(encoding="utf-8"))
    _, expected = reference_impose(CATALOG, MARKS, set_name, seed)
    assert got == expected


@pytest.mark.parametrize("seed", IMPOSE_SEEDS)
def test_sheet_pixels_match_reference(seed: int) -> None:
    """Imposed sheet PNG pixels must match the reference compositor."""
    sheet_out, _ = impose_cli("core-marks", seed)
    expected_sheet, _ = reference_impose(CATALOG, MARKS, "core-marks", seed)
    got = Image.open(sheet_out).convert("RGBA")
    assert list(got.getdata()) == list(expected_sheet.getdata())


def test_duplicate_mark_frames_present() -> None:
    """Both arrow frames must survive imposition under the same mark id."""
    _, ledger_out = impose_cli("core-marks", CATALOG_SEED)
    ledger = json.loads(ledger_out.read_text(encoding="utf-8"))
    arrow_frames = sorted(
        s["frame"] for s in ledger["marks"] if s["mark_id"] == "arrow"
    )
    assert arrow_frames == [0, 1]


def _rotated_content_dims(png_name: str) -> tuple[int, int]:
    """Post-rotation content size for a catalog mark file (90 deg CW)."""
    img = Image.open(MARKS / png_name)
    return img.height, img.width


def test_rotated_blade_dimensions() -> None:
    """Rotated blade must occupy swapped padded slot dimensions."""
    expected_w, expected_h = _rotated_content_dims("blade_tall.png")
    _, ledger_out = impose_cli("core-marks", CATALOG_SEED)
    ledger = json.loads(ledger_out.read_text(encoding="utf-8"))
    blade = next(s for s in ledger["marks"] if s["mark_id"] == "blade")
    pad = ledger["gutter_px"]
    assert blade["content_w"] == expected_w
    assert blade["content_h"] == expected_h
    assert blade["press_rotate"] is True
    assert blade["u1"] - blade["u0"] == pytest.approx(expected_w / ledger["sheet_width"])
    assert blade["v1"] - blade["v0"] == pytest.approx(expected_h / ledger["sheet_height"])
    assert blade["sheet_x"] + expected_w + 2 * pad <= ledger["sheet_width"]


@pytest.mark.parametrize(
    "u,v",
    [
        (0.0, 0.0),
        (1.0, 0.0),
        (0.0, 1.0),
        (1.0, 1.0),
    ],
)
def test_edge_sample_samples_match_reference(u: float, v: float) -> None:
    """Bilinear sample at sample-window corners must match the reference sampler."""
    sheet_out, ledger_out = impose_cli("core-marks", CATALOG_SEED)
    ledger = json.loads(ledger_out.read_text(encoding="utf-8"))
    got = sample_cli(sheet_out, ledger_out, "edge", 0, u, v)
    ref = reference_sample(sheet_out, ledger, "edge", 0, u, v)
    assert got == ref
    assert any(c > 0 for c in got["rgba"][:3])


def test_scale_trap_ledger(seed: int = CATALOG_SEED) -> None:
    """Scalable banner dimensions must follow seed scale policy."""
    _, ledger_out = impose_cli("scale-trap", seed)
    got = json.loads(ledger_out.read_text(encoding="utf-8"))
    _, expected = reference_impose(CATALOG, MARKS, "scale-trap", seed)
    assert got == expected
    banner = next(s for s in got["marks"] if s["mark_id"] == "banner")
    scale = 1 + (seed % CATALOG_DATA["scale_mod"])
    base = Image.open(MARKS / "banner_wide.png")
    assert banner["content_w"] == base.width * scale
    assert banner["content_h"] == base.height * scale


def test_oversized_mark_exits_two() -> None:
    """Oversized scaled marks must abort with exit code 2."""
    proc = run(
        [
            CLI,
            "impose",
            "--catalog",
            str(CATALOG),
            "--marks",
            str(MARKS),
            "--set",
            "oversize-trap",
            "--seed",
            str(OVERSIZE_SEED),
            "--sheet-out",
            str(OUTPUT / "oversize.png"),
            "--ledger-out",
            str(OUTPUT / "oversize.json"),
        ]
    )
    assert proc.returncode == 2, proc.stderr or proc.stdout
    with pytest.raises(OversizedError):
        reference_impose(CATALOG, MARKS, "oversize-trap", OVERSIZE_SEED)


def test_checksum_changes_with_key_order_independent_body() -> None:
    """Checksum must be stable regardless of JSON key order in written files."""
    _, ledger_out = impose_cli("core-marks", CATALOG_SEED)
    ledger = json.loads(ledger_out.read_text(encoding="utf-8"))
    body = {k: v for k, v in ledger.items() if k != "checksum"}
    from reference_sheet import ledger_checksum

    assert ledger["checksum"] == ledger_checksum(body)


def test_sample_json_shape() -> None:
    """Sample emits JSON with rgba channel array."""
    sheet_out, ledger_out = impose_cli("core-marks", CATALOG_SEED)
    got = sample_cli(sheet_out, ledger_out, "coin", 0, 0.5, 0.5)
    assert got["mark_id"] == "coin"
    assert got["frame"] == 0
    assert len(got["rgba"]) == 4


def _hidden_seed() -> int:
    """Load verifier-fixtures hidden seed (TB3_VERIFIER_FIXTURES overlay)."""
    root = Path(
        os.environ.get(
            "TB3_VERIFIER_FIXTURES",
            str(Path(__file__).resolve().parent / "verifier-fixtures"),
        )
    )
    payload = json.loads((root / "hidden-seed.json").read_text(encoding="utf-8"))
    return int(payload["hidden_seed"])


def test_hidden_seed_ledger_matches_reference() -> None:
    """Hidden verifier-fixtures seed must match the independent reference compositor."""
    seed = _hidden_seed()
    _, ledger_out = impose_cli("core-marks", seed)
    got = json.loads(ledger_out.read_text(encoding="utf-8"))
    _, expected = reference_impose(CATALOG, MARKS, "core-marks", seed)
    assert got == expected


def test_hidden_seed_edge_sample_matches_reference() -> None:
    """Hidden TB3 seed edge sheet samples must match the reference sampler."""
    seed = _hidden_seed()
    sheet_out, ledger_out = impose_cli("core-marks", seed)
    ledger = json.loads(ledger_out.read_text(encoding="utf-8"))
    got = sample_cli(sheet_out, ledger_out, "edge", 0, 0.0, 1.0)
    ref = reference_sample(sheet_out, ledger, "edge", 0, 0.0, 1.0)
    assert got == ref


def test_staging_snapshot_mark_count() -> None:
    """Staging snapshot mark_count must equal exported ledger mark rows."""
    _, ledger_out = impose_cli("core-marks", CATALOG_SEED)
    ledger = json.loads(ledger_out.read_text(encoding="utf-8"))
    staging_path = OUTPUT / "sheet-staging-snapshot.json"
    assert staging_path.is_file()
    staging = json.loads(staging_path.read_text(encoding="utf-8"))
    assert staging["mark_count"] == len(ledger["marks"])
    assert staging["stage"] == "sheet-staging"
    assert staging["seed"] == CATALOG_SEED


def test_ingest_catalog_export_ledger_roundtrip() -> None:
    """Ingest catalog impose must export ledger checksum aligned with reference."""
    _, ledger_out = impose_cli("core-marks", CATALOG_SEED)
    exported = json.loads(ledger_out.read_text(encoding="utf-8"))
    _, expected = reference_impose(CATALOG, MARKS, "core-marks", CATALOG_SEED)
    assert exported["checksum"] == expected["checksum"]
    assert exported["sheet_width"] == expected["sheet_width"]
    assert len(exported["marks"]) == len(expected["marks"])


def test_gem_sample_window_inner_content_not_gutter() -> None:
    """Gem sample-window span must describe inner content width, not padded gutter."""
    _, ledger_out = impose_cli("core-marks", CATALOG_SEED)
    ledger = json.loads(ledger_out.read_text(encoding="utf-8"))
    gem = next(s for s in ledger["marks"] if s["mark_id"] == "gem")
    pad = ledger["gutter_px"]
    assert gem["u1"] - gem["u0"] == pytest.approx(gem["content_w"] / ledger["sheet_width"])
    assert gem["sheet_x"] >= 0
    assert gem["content_w"] + 2 * pad <= ledger["sheet_width"]


def test_coin_center_sample_opaque() -> None:
    """Coin center sample must return an opaque interior sample."""
    sheet_out, ledger_out = impose_cli("core-marks", CATALOG_SEED)
    got = sample_cli(sheet_out, ledger_out, "coin", 0, 0.5, 0.5)
    assert got["rgba"][3] == 255


def test_scale_trap_seed_eleven_matches_reference() -> None:
    """Scale-trap set at seed 11 must match the independent reference compositor."""
    seed = 11
    _, ledger_out = impose_cli("scale-trap", seed)
    got = json.loads(ledger_out.read_text(encoding="utf-8"))
    _, expected = reference_impose(CATALOG, MARKS, "scale-trap", seed)
    assert got == expected


def test_sample_missing_mark_exits_one() -> None:
    """Sample of an unknown mark must exit with code 1."""
    sheet_out, ledger_out = impose_cli("core-marks", CATALOG_SEED)
    proc = run(
        [
            CLI,
            "sample",
            "--sheet",
            str(sheet_out),
            "--ledger",
            str(ledger_out),
            "--mark",
            "missing-mark",
            "--frame",
            "0",
            "--u",
            "0.5",
            "--v",
            "0.5",
        ]
    )
    assert proc.returncode == 1

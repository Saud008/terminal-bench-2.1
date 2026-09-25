"""Behavioral verifier for atlaspack pack + probe."""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest
from PIL import Image

from reference_atlas import OversizedError, reference_pack, reference_probe

APP = Path("/app")
CLI = "/usr/local/bin/atlaspack"
FIXTURES = APP / "fixtures"
SPRITES = FIXTURES / "sprites"
CATALOG = FIXTURES / "catalog.json"
OUTPUT = APP / "output"
RESET = APP / "scripts/reset-state.sh"

CATALOG_DATA = json.loads(CATALOG.read_text(encoding="utf-8"))
SEEDS = json.loads((FIXTURES / "seeds.json").read_text(encoding="utf-8"))
PACK_SEEDS = SEEDS["seeds"]
CATALOG_SEED = SEEDS["catalog_seed"]
OVERSIZE_SEED = SEEDS["oversize_seed"]

PROTECTED = [
    "fixtures/catalog.json",
    "fixtures/seeds.json",
    "fixtures/sprites/arrow_f0.png",
    "fixtures/sprites/arrow_f1.png",
    "fixtures/sprites/banner_wide.png",
    "fixtures/sprites/blade_tall.png",
    "fixtures/sprites/coin_small.png",
    "fixtures/sprites/edge_probe.png",
    "fixtures/sprites/gem_square.png",
    "docs/atlas-contract.md",
    "docs/manifest-schema.md",
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


def pack_cli(set_name: str, seed: int) -> tuple[Path, Path]:
    atlas_out = OUTPUT / f"atlas-{set_name}-{seed}.png"
    manifest_out = OUTPUT / f"manifest-{set_name}-{seed}.json"
    proc = run(
        [
            CLI,
            "pack",
            "--catalog",
            str(CATALOG),
            "--sprites",
            str(SPRITES),
            "--set",
            set_name,
            "--seed",
            str(seed),
            "--atlas-out",
            str(atlas_out),
            "--manifest-out",
            str(manifest_out),
        ]
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout
    return atlas_out, manifest_out


def probe_cli(
    atlas: Path, manifest: Path, glyph: str, frame: int, u: float, v: float
) -> dict:
    proc = run(
        [
            CLI,
            "probe",
            "--atlas",
            str(atlas),
            "--manifest",
            str(manifest),
            "--glyph",
            glyph,
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
    """Protected docs and sprite bytes must remain unchanged."""
    for rel, expected in PROTECTED_SHA256.items():
        assert _sha256(rel) == expected


@pytest.mark.parametrize("set_name", ["core-glyphs"])
@pytest.mark.parametrize("seed", PACK_SEEDS)
def test_manifest_matches_reference(set_name: str, seed: int) -> None:
    """Manifest JSON including checksum must match the independent reference packer."""
    _, manifest_out = pack_cli(set_name, seed)
    got = json.loads(manifest_out.read_text(encoding="utf-8"))
    _, expected = reference_pack(CATALOG, SPRITES, set_name, seed)
    assert got == expected


@pytest.mark.parametrize("seed", PACK_SEEDS)
def test_atlas_pixels_match_reference(seed: int) -> None:
    """Packed atlas PNG pixels must match the reference compositor."""
    atlas_out, _ = pack_cli("core-glyphs", seed)
    expected_atlas, _ = reference_pack(CATALOG, SPRITES, "core-glyphs", seed)
    got = Image.open(atlas_out).convert("RGBA")
    assert list(got.getdata()) == list(expected_atlas.getdata())


def test_duplicate_glyph_frames_present() -> None:
    """Both arrow frames must survive packing under the same glyph id."""
    _, manifest_out = pack_cli("core-glyphs", CATALOG_SEED)
    manifest = json.loads(manifest_out.read_text(encoding="utf-8"))
    arrow_frames = sorted(
        s["frame"] for s in manifest["sprites"] if s["glyph_id"] == "arrow"
    )
    assert arrow_frames == [0, 1]


def _rotated_content_dims(png_name: str) -> tuple[int, int]:
    """Post-rotation content size for a catalog sprite file (90 deg CW)."""
    img = Image.open(SPRITES / png_name)
    return img.height, img.width


def test_rotated_blade_dimensions() -> None:
    """Rotated blade must occupy swapped padded slot dimensions."""
    expected_w, expected_h = _rotated_content_dims("blade_tall.png")
    _, manifest_out = pack_cli("core-glyphs", CATALOG_SEED)
    manifest = json.loads(manifest_out.read_text(encoding="utf-8"))
    blade = next(s for s in manifest["sprites"] if s["glyph_id"] == "blade")
    pad = manifest["padding_px"]
    assert blade["content_w"] == expected_w
    assert blade["content_h"] == expected_h
    assert blade["rotate"] is True
    assert blade["u1"] - blade["u0"] == pytest.approx(expected_w / manifest["atlas_width"])
    assert blade["v1"] - blade["v0"] == pytest.approx(expected_h / manifest["atlas_height"])
    assert blade["atlas_x"] + expected_w + 2 * pad <= manifest["atlas_width"]


@pytest.mark.parametrize(
    "u,v",
    [
        (0.0, 0.0),
        (1.0, 0.0),
        (0.0, 1.0),
        (1.0, 1.0),
    ],
)
def test_edge_probe_samples_match_reference(u: float, v: float) -> None:
    """Bilinear probe at UV corners must match the reference sampler."""
    atlas_out, manifest_out = pack_cli("core-glyphs", CATALOG_SEED)
    manifest = json.loads(manifest_out.read_text(encoding="utf-8"))
    got = probe_cli(atlas_out, manifest_out, "edge", 0, u, v)
    ref = reference_probe(atlas_out, manifest, "edge", 0, u, v)
    assert got == ref
    assert any(c > 0 for c in got["rgba"][:3])


def test_scale_trap_manifest(seed: int = CATALOG_SEED) -> None:
    """Scalable banner dimensions must follow seed scale policy."""
    _, manifest_out = pack_cli("scale-trap", seed)
    got = json.loads(manifest_out.read_text(encoding="utf-8"))
    expected_atlas, expected = reference_pack(CATALOG, SPRITES, "scale-trap", seed)
    assert got == expected
    banner = next(s for s in got["sprites"] if s["glyph_id"] == "banner")
    scale = 1 + (seed % CATALOG_DATA["scale_mod"])
    base = Image.open(SPRITES / "banner_wide.png")
    assert banner["content_w"] == base.width * scale
    assert banner["content_h"] == base.height * scale


def test_oversized_sprite_exits_two() -> None:
    """Oversized scaled sprites must abort with exit code 2."""
    proc = run(
        [
            CLI,
            "pack",
            "--catalog",
            str(CATALOG),
            "--sprites",
            str(SPRITES),
            "--set",
            "oversize-trap",
            "--seed",
            str(OVERSIZE_SEED),
            "--atlas-out",
            str(OUTPUT / "oversize.png"),
            "--manifest-out",
            str(OUTPUT / "oversize.json"),
        ]
    )
    assert proc.returncode == 2, proc.stderr or proc.stdout
    with pytest.raises(OversizedError):
        reference_pack(CATALOG, SPRITES, "oversize-trap", OVERSIZE_SEED)


def test_checksum_changes_with_key_order_independent_body() -> None:
    """Checksum must be stable regardless of JSON key order in written files."""
    _, manifest_out = pack_cli("core-glyphs", CATALOG_SEED)
    manifest = json.loads(manifest_out.read_text(encoding="utf-8"))
    body = {k: v for k, v in manifest.items() if k != "checksum"}
    from reference_atlas import manifest_checksum

    assert manifest["checksum"] == manifest_checksum(body)


def test_probe_json_shape() -> None:
    """Probe emits JSON with rgba channel array."""
    atlas_out, manifest_out = pack_cli("core-glyphs", CATALOG_SEED)
    got = probe_cli(atlas_out, manifest_out, "coin", 0, 0.5, 0.5)
    assert got["glyph_id"] == "coin"
    assert got["frame"] == 0
    assert len(got["rgba"]) == 4

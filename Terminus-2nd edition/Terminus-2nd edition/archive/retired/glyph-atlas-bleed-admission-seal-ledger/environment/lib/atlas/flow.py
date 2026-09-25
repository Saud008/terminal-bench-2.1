"""Pack / probe admission flow (ingest → stage → export)."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from atlas import catalog as catalog_mod
from atlas import compose as compose_mod
from atlas import manifest as manifest_mod
from atlas import pack as pack_mod
from atlas import seed as seed_mod
from atlas import validate as validate_mod
from atlas.staging_bridge import write_staging_snapshot


def run_pack(
    catalog_path: Path,
    sprites_dir: Path,
    set_name: str,
    seed: int,
    atlas_out: Path,
    manifest_out: Path,
) -> None:
    catalog = catalog_mod.load_catalog(catalog_path)
    pad = seed_mod.padding_px(catalog, seed)
    entries = catalog_mod.load_entries(catalog, set_name)
    prepared = catalog_mod.prepare_sprites(catalog, entries, sprites_dir, seed, pad)
    validate_mod.ensure_fits(catalog, prepared)
    layout = pack_mod.layout_sprites(prepared, catalog["atlas_width"], catalog["atlas_height"])
    write_staging_snapshot(seed, set_name, len(layout))
    atlas = compose_mod.compose_atlas(
        layout, catalog["atlas_width"], catalog["atlas_height"], pad
    )
    atlas_out.parent.mkdir(parents=True, exist_ok=True)
    atlas.save(atlas_out)
    manifest = manifest_mod.build_manifest(catalog, layout, seed, pad)
    manifest_mod.write_manifest(manifest_out, manifest)


def run_probe(
    atlas_path: Path,
    manifest_path: Path,
    glyph_id: str,
    frame: int,
    u: float,
    v: float,
) -> dict:
    manifest = manifest_mod.read_manifest(manifest_path)
    entry = next(
        (
            s
            for s in manifest["sprites"]
            if s["glyph_id"] == glyph_id and s["frame"] == frame
        ),
        None,
    )
    if entry is None:
        raise KeyError(f"{glyph_id}:{frame}")
    img = Image.open(atlas_path).convert("RGBA")
    raw = img.tobytes()
    color = compose_mod.sample_bilinear(
        raw,
        manifest["atlas_width"],
        manifest["atlas_height"],
        entry["u0"],
        entry["v0"],
        entry["u1"],
        entry["v1"],
        u,
        v,
    )
    return {
        "glyph_id": glyph_id,
        "frame": frame,
        "u": u,
        "v": v,
        "rgba": color,
    }


def emit_probe_json(result: dict) -> None:
    print(json.dumps(result, separators=(",", ":")))

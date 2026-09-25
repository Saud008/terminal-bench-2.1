"""Impose / sample admission flow (ingest → stage → export)."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from sheet import catalog as catalog_mod
from sheet import compose as compose_mod
from sheet import ledger as ledger_mod
from sheet import impose as impose_mod
from sheet import seed as seed_mod
from sheet import validate as validate_mod
from sheet.staging_bridge import write_staging_snapshot


def run_impose(
    catalog_path: Path,
    marks_dir: Path,
    set_name: str,
    seed: int,
    sheet_out: Path,
    ledger_out: Path,
) -> None:
    catalog = catalog_mod.load_catalog(catalog_path)
    pad = seed_mod.gutter_px(catalog, seed)
    entries = catalog_mod.load_entries(catalog, set_name)
    prepared = catalog_mod.prepare_marks(catalog, entries, marks_dir, seed, pad)
    validate_mod.ensure_fits(catalog, prepared)
    layout = impose_mod.layout_marks(prepared, catalog["sheet_width"], catalog["sheet_height"])
    write_staging_snapshot(seed, set_name, len(layout))
    sheet = compose_mod.compose_sheet(
        layout, catalog["sheet_width"], catalog["sheet_height"], pad
    )
    sheet_out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(sheet_out)
    ledger = ledger_mod.build_ledger(catalog, layout, seed, pad)
    ledger_mod.write_ledger(ledger_out, ledger)


def run_sample(
    sheet_path: Path,
    ledger_path: Path,
    mark_id: str,
    frame: int,
    u: float,
    v: float,
) -> dict:
    ledger = ledger_mod.read_ledger(ledger_path)
    entry = next(
        (
            s
            for s in ledger["marks"]
            if s["mark_id"] == mark_id and s["frame"] == frame
        ),
        None,
    )
    if entry is None:
        raise KeyError(f"{mark_id}:{frame}")
    img = Image.open(sheet_path).convert("RGBA")
    raw = img.tobytes()
    color = compose_mod.sample_bilinear(
        raw,
        ledger["sheet_width"],
        ledger["sheet_height"],
        entry["u0"],
        entry["v0"],
        entry["u1"],
        entry["v1"],
        u,
        v,
    )
    return {
        "mark_id": mark_id,
        "frame": frame,
        "u": u,
        "v": v,
        "rgba": color,
    }


def emit_sample_json(result: dict) -> None:
    print(json.dumps(result, separators=(",", ":")))

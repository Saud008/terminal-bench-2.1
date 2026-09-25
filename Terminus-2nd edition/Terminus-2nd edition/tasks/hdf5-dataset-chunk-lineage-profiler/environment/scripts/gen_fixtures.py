"""Generate S5 bundle fixtures for chunkline task."""
from __future__ import annotations

import hashlib
import json
import math
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def chunks_per_axis(dims: list[int], chunk_dims: list[int]) -> list[int]:
    return [math.ceil(d / c) for d, c in zip(dims, chunk_dims)]


def filter_chain_digest(filters: list[str]) -> str:
    return hashlib.sha256("|".join(filters).encode()).hexdigest()

def write_idx(path: Path, ndims: int, chunks: list) -> None:
    buf = bytearray()
    buf += b"S5IX"
    buf += struct.pack("<I", ndims)
    buf += struct.pack("<I", len(chunks))
    for origin, fid, payload, masked in chunks:
        for o in origin:
            buf += struct.pack("<Q", o)
        buf += struct.pack("<III", fid, payload, masked)
    path.write_bytes(buf)


def main() -> None:
    base = ROOT / "fixtures" / "basic"
    (base / "indexes").mkdir(parents=True, exist_ok=True)
    (base / "masks").mkdir(parents=True, exist_ok=True)
    cat = {
        "version": 1,
        "root": "/",
        "datasets": [
            {
                "path": "/obs/temp",
                "dims": [4, 3],
                "chunk_dims": [2, 3],
                "filters": ["shuffle", "gzip"],
                "fill_value": -999.0,
                "mask_rel": "masks/temp.mask",
                "attrs": {"scale": 0.5, "units": "K"},
                "parent_chain": [
                    {"path": "/obs", "attrs": {"units": "C", "calibration": "lab"}}
                ],
            }
        ],
    }
    (base / "catalog.s5cat").write_text(json.dumps(cat, indent=2), encoding="utf-8")
    _ = filter_chain_digest(cat["datasets"][0]["filters"])
    _ = chunks_per_axis(cat["datasets"][0]["dims"], cat["datasets"][0]["chunk_dims"])
    (base / "masks" / "temp.mask").write_bytes(bytes([0b00000100]))
    write_idx(
        base / "indexes" / "obs_temp.s5idx",
        2,
        [([0, 0], 42, 100, 1), ([2, 0], 42, 120, 0)],
    )

    tb3 = ROOT / "verifier-fixtures" / "tb3_shadow"
    (tb3 / "indexes").mkdir(parents=True, exist_ok=True)
    (tb3 / "masks").mkdir(parents=True, exist_ok=True)
    cat3 = {
        "version": 1,
        "root": "/",
        "datasets": [
            {
                "path": "/grid/field",
                "dims": [4, 4],
                "chunk_dims": [2, 2],
                "filters": ["gzip", "shuffle"],
                "fill_value": 0.0,
                "mask_rel": "masks/field.mask",
                "attrs": {"scale": 2.0, "units": "Pa"},
                "parent_chain": [
                    {
                        "path": "/grid",
                        "attrs": {"scale": 10.0, "units": "hPa", "frame": "ECMWF"},
                    },
                    {"path": "/grid/field", "attrs": {"units": "kPa"}},
                ],
            }
        ],
    }
    (tb3 / "catalog.s5cat").write_text(json.dumps(cat3, indent=2), encoding="utf-8")
    (tb3 / "masks" / "field.mask").write_bytes(bytes([0b00001010]))
    write_idx(
        tb3 / "indexes" / "grid_field.s5idx",
        2,
        [
            ([0, 0], 7, 200, 2),
            ([0, 2], 7, 210, 2),
            ([2, 0], 7, 220, 2),
            ([2, 2], 7, 230, 2),
        ],
    )
    print("fixtures written")


if __name__ == "__main__":
    main()

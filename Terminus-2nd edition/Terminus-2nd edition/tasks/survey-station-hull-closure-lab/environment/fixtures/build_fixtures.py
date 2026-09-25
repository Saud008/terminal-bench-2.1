#!/usr/bin/env python3
"""Build seeded survey campaign bundles for triangclos."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def write_bundle(path: Path, body: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("/app/fixtures/campaigns"))
    args = parser.parse_args()
    out = args.out_dir

    write_bundle(
        out / "dual-station-basic.json",
        {
            "bundle_name": "dual-station-basic",
            "stations": [
                {
                    "station_id": "STA-A",
                    "vertices": [
                        [10.0, 20.0],
                        [10.4, 20.0],
                        [10.4, 20.3],
                        [10.0, 20.3],
                        [10.0, 20.0],
                    ],
                },
                {
                    "station_id": "STA-B",
                    "vertices": [
                        [12.0, 21.0],
                        [12.5, 21.0],
                        [12.5, 21.4],
                        [12.0, 21.4],
                        [12.0, 21.0],
                    ],
                },
            ],
        },
    )

    write_bundle(
        out / "area-rank-ladder.json",
        {
            "bundle_name": "area-rank-ladder",
            "stations": [
                {
                    "station_id": "BIG",
                    "vertices": [
                        [0.0, 0.0],
                        [1.0, 0.0],
                        [1.0, 1.0],
                        [0.0, 1.0],
                        [0.0, 0.0],
                    ],
                },
                {
                    "station_id": "MID",
                    "vertices": [
                        [3.0, 0.0],
                        [3.4, 0.0],
                        [3.4, 0.4],
                        [3.0, 0.4],
                        [3.0, 0.0],
                    ],
                },
                {
                    "station_id": "TINY",
                    "vertices": [
                        [5.0, 0.0],
                        [5.1, 0.0],
                        [5.1, 0.1],
                        [5.0, 0.1],
                        [5.0, 0.0],
                    ],
                },
            ],
        },
    )

    write_bundle(
        out / "conflict-overlap.json",
        {
            "bundle_name": "conflict-overlap",
            "stations": [
                {
                    "station_id": "L1",
                    "vertices": [
                        [0.0, 0.0],
                        [1.0, 0.0],
                        [1.0, 1.0],
                        [0.0, 1.0],
                        [0.0, 0.0],
                    ],
                },
                {
                    "station_id": "L2",
                    "vertices": [
                        [0.5, 0.5],
                        [1.5, 0.5],
                        [1.5, 1.5],
                        [0.5, 1.5],
                        [0.5, 0.5],
                    ],
                },
            ],
        },
    )

    write_bundle(
        out / "wrap-crossing.json",
        {
            "bundle_name": "wrap-crossing",
            "stations": [
                {
                    "station_id": "WRAP1",
                    "vertices": [
                        [170.0, 0.0],
                        [-170.0, 0.0],
                        [-170.0, 0.5],
                        [-175.0, 1.0],
                        [-170.0, 1.5],
                        [170.0, 1.5],
                        [175.0, 1.0],
                        [170.0, 0.0],
                    ],
                }
            ],
        },
    )

    write_bundle(
        out / "quantize-edge.json",
        {
            "bundle_name": "quantize-edge",
            "stations": [
                {
                    "station_id": "Q1",
                    "vertices": [
                        [1.00004, 2.00004],
                        [1.00014, 2.00004],
                        [1.00014, 2.00014],
                        [1.00004, 2.00014],
                        [1.00004, 2.00004],
                    ],
                }
            ],
        },
    )

    # Longitude span ~120: must NOT wrap (>180 only). Shipping threshold 90 false-wraps.
    write_bundle(
        out / "midspan-no-wrap.json",
        {
            "bundle_name": "midspan-no-wrap",
            "stations": [
                {
                    "station_id": "MIDSPAN",
                    "vertices": [
                        [0.0, 0.0],
                        [120.0, 0.0],
                        [120.0, 1.0],
                        [0.0, 1.0],
                        [0.0, 0.0],
                    ],
                }
            ],
        },
    )

    # Positive-area rectangle plus zero-area vertical line that open-overlaps.
    # Shipping conflict gate rejects; correct gate accepts (degenerate never conflicts).
    write_bundle(
        out / "degenerate-touch.json",
        {
            "bundle_name": "degenerate-touch",
            "stations": [
                {
                    "station_id": "POLY",
                    "vertices": [
                        [0.0, 0.0],
                        [1.0, 0.0],
                        [1.0, 1.0],
                        [0.0, 1.0],
                        [0.0, 0.0],
                    ],
                },
                {
                    "station_id": "LINE",
                    "vertices": [
                        [0.5, 0.0],
                        [0.5, 0.0],
                        [0.5, 1.0],
                        [0.5, 1.0],
                        [0.5, 0.0],
                    ],
                },
            ],
        },
    )


if __name__ == "__main__":
    main()

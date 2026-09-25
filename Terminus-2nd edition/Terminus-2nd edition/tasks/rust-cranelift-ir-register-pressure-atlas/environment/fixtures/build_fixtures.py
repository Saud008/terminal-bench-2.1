#!/usr/bin/env python3
"""Build seeded neutron-spectrometer ring bundles for fluxpress."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def write_bundle(path: Path, body: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path("/app/fixtures/rings"))
    args = parser.parse_args()
    out = args.out_dir

    write_bundle(
        out / "basic-dual.json",
        {
            "bundle_name": "basic-dual",
            "aperture_budget": 3,
            "dwell_width_kev": 10.0,
            "background_anchors": [
                {"energy_kev": 0.0, "counts": 2.0},
                {"energy_kev": 50.0, "counts": 2.0},
            ],
            "channels": [
                {"channel_id": "CH-A", "energy_kev": 12.5, "measured_counts": 40.0, "width_kev": 4.0},
                {"channel_id": "CH-B", "energy_kev": 30.0, "measured_counts": 25.0, "width_kev": 4.0},
            ],
            "veto_windows": [],
        },
    )

    write_bundle(
        out / "veto-kill.json",
        {
            "bundle_name": "veto-kill",
            "aperture_budget": 2,
            "dwell_width_kev": 8.0,
            "background_anchors": [
                {"energy_kev": 0.0, "counts": 1.0},
                {"energy_kev": 50.0, "counts": 1.0},
            ],
            "channels": [
                {"channel_id": "CH-X", "energy_kev": 22.0, "measured_counts": 10.0, "width_kev": 2.0},
                {"channel_id": "CH-Y", "energy_kev": 40.0, "measured_counts": 12.0, "width_kev": 2.0},
            ],
            "veto_windows": [{"veto_id": "V1", "lo_kev": 20.0, "hi_kev": 25.0}],
        },
    )

    write_bundle(
        out / "occupancy-peak.json",
        {
            "bundle_name": "occupancy-peak",
            "aperture_budget": 2,
            "dwell_width_kev": 10.0,
            "background_anchors": [
                {"energy_kev": 0.0, "counts": 0.0},
                {"energy_kev": 100.0, "counts": 0.0},
            ],
            "channels": [
                {"channel_id": "CH-1", "energy_kev": 10.0, "measured_counts": 5.0, "width_kev": 10.0},
                {"channel_id": "CH-2", "energy_kev": 12.0, "measured_counts": 6.0, "width_kev": 10.0},
                {"channel_id": "CH-3", "energy_kev": 14.0, "measured_counts": 7.0, "width_kev": 10.0},
            ],
            "veto_windows": [],
        },
    )

    write_bundle(
        out / "quantize-edge.json",
        {
            "bundle_name": "quantize-edge",
            "aperture_budget": 5,
            "dwell_width_kev": 5.0,
            "background_anchors": [
                {"energy_kev": 0.0, "counts": 1.0},
                {"energy_kev": 10.0, "counts": 3.0},
                {"energy_kev": 20.0, "counts": 1.0},
            ],
            "channels": [
                {"channel_id": "CH-Q1", "energy_kev": 12.5005, "measured_counts": 50.0, "width_kev": 3.0005},
                {"channel_id": "CH-Q2", "energy_kev": 7.4995, "measured_counts": 20.0, "width_kev": 2.4995},
            ],
            "veto_windows": [],
        },
    )

    write_bundle(
        out / "rank-ladder.json",
        {
            "bundle_name": "rank-ladder",
            "aperture_budget": 5,
            "dwell_width_kev": 6.0,
            "background_anchors": [
                {"energy_kev": 0.0, "counts": 0.0},
                {"energy_kev": 50.0, "counts": 0.0},
            ],
            "channels": [
                {"channel_id": "CH-LOW", "energy_kev": 5.0, "measured_counts": 10.0, "width_kev": 2.0},
                {"channel_id": "CH-MID", "energy_kev": 15.0, "measured_counts": 25.0, "width_kev": 2.0},
                {"channel_id": "CH-HIGH", "energy_kev": 25.0, "measured_counts": 40.0, "width_kev": 2.0},
            ],
            "veto_windows": [],
        },
    )

    write_bundle(
        out / "mid-budget.json",
        {
            "bundle_name": "mid-budget",
            "aperture_budget": 2,
            "dwell_width_kev": 10.0,
            "background_anchors": [
                {"energy_kev": 0.0, "counts": 0.0},
                {"energy_kev": 50.0, "counts": 0.0},
            ],
            "channels": [
                {"channel_id": "CH-P", "energy_kev": 10.0, "measured_counts": 5.0, "width_kev": 10.0},
                {"channel_id": "CH-Q", "energy_kev": 15.0, "measured_counts": 5.0, "width_kev": 10.0},
            ],
            "veto_windows": [],
        },
    )


if __name__ == "__main__":
    main()

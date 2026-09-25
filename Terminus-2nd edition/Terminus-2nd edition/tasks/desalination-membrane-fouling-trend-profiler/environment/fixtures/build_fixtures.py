#!/usr/bin/env python3
"""Build seeded RO train fixture directories for rotrace."""

from __future__ import annotations

import argparse
import csv
import io
import json
import random
from pathlib import Path


def csv_write(header: list[str], rows: list[list]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow(header)
    for row in rows:
        writer.writerow(row)
    return buf.getvalue()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=77104)
    parser.add_argument("--out-dir", type=Path, default=Path("/app/fixtures/ro-trains"))
    args = parser.parse_args()
    rng = random.Random(args.seed)
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    def batch_id(prefix: str = "MBR") -> str:
        return f"{prefix}-{rng.randint(1000, 9999)}"

    scenarios = []
    for idx, name in enumerate(
        ["ro-train-alpha", "ro-train-bravo", "ro-train-charlie", "ro-train-delta", "ro-train-echo"]
    ):
        bid = batch_id()
        scenario_dir = out / name
        scenario_dir.mkdir(parents=True, exist_ok=True)
        (scenario_dir / "train.meta.json").write_text(
            json.dumps(
                {
                    "train_id": f"RO-{name}-{rng.randint(10, 99)}",
                    "unit_id": f"UNIT-{rng.randint(10, 99)}",
                    "membrane_id": f"MEM-{rng.randint(10000, 99999)}",
                    "scenario": name,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (scenario_dir / "membrane_batches.json").write_text(
            json.dumps(
                {
                    "batches": [
                        {
                            "batch_id": bid,
                            "parent_batch_id": None,
                            "alpha": round(rng.uniform(0.9, 1.5), 2),
                            "beta": round(rng.uniform(0.7, 1.1), 2),
                            "p_base": round(rng.uniform(2.0, 3.5), 2),
                            "t_ref": 25.0,
                            "q_ref": round(rng.uniform(100.0, 130.0), 1),
                            "active_from_hour": 0,
                            "active_until_hour": 72 + idx * 12,
                        }
                    ]
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (scenario_dir / "cleaning.csv").write_text(
            csv_write(
                ["hour_index", "event_type", "cleaned_on"],
                [[24 + idx * 12, "rinse", f"2026-04-{10 + idx:02d}"]],
            ),
            encoding="utf-8",
        )
        readings = []
        for h in range(0, 72, 12):
            readings.append(
                [
                    h,
                    bid,
                    round(rng.uniform(3.5, 5.5), 2),
                    round(rng.uniform(33.0, 37.0), 1),
                    round(rng.uniform(95.0, 125.0), 1),
                    round(rng.uniform(22.0, 28.0), 1),
                    "ok",
                    0.0,
                ]
            )
        (scenario_dir / "readings.csv").write_text(
            csv_write(
                [
                    "hour_index",
                    "batch_id",
                    "pressure_bar",
                    "salinity_ppt",
                    "flow_m3h",
                    "temperature_c",
                    "sensor_flags",
                    "cal_offset_ppt",
                ],
                readings,
            ),
            encoding="utf-8",
        )
        scenarios.append(name)

    catalog = {"seed": args.seed, "bundles": scenarios}
    (out.parent / "bundle_catalog.json").write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(scenarios)} scenarios under {out}")


if __name__ == "__main__":
    main()

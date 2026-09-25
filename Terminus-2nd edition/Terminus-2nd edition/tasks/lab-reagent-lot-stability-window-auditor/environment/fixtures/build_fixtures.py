#!/usr/bin/env python3
"""Build seeded reagent session bundle fixtures for reagentwin."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path


def cert_digest(lot_id: str, as_of: str, assay: str) -> str:
    body = f"{lot_id}:{as_of}:{assay}".encode()
    return hashlib.sha256(body).hexdigest()[:16]


def write_bundle(path: Path, body: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=7719)
    parser.add_argument("--out-dir", type=Path, default=Path("/app/fixtures/lab_sessions"))
    args = parser.parse_args()
    rng = random.Random(args.seed)
    out = args.out_dir

    def lot_id(prefix: str) -> str:
        return f"{prefix}-{rng.randint(1000, 9999)}"

    as_of = "2026-03-15"

    lid_a = lot_id("LOT")
    lid_b = lot_id("LOT")
    write_bundle(
        out / "dual-lot-basic.json",
        {
            "bundle_name": "dual-lot-basic",
            "as_of_date": as_of,
            "lots": [
                {
                    "lot_id": lid_a,
                    "aliases": [lid_a.lower(), lid_a.replace("-", "")],
                    "assay_code": "ELISA-A",
                    "base_expiry": "2026-12-31",
                    "cold_chain_days": 30,
                    "stability_bonus_days": 14,
                    "cert_hint": cert_digest(lid_a, as_of, "ELISA-A"),
                },
                {
                    "lot_id": lid_b,
                    "aliases": [],
                    "assay_code": "ELISA-B",
                    "base_expiry": "2027-06-30",
                    "cold_chain_days": 21,
                    "stability_bonus_days": 7,
                    "cert_hint": cert_digest(lid_b, as_of, "ELISA-B"),
                },
            ],
            "telemetry": [
                {
                    "lot_alias": lid_a.lower(),
                    "minute_index": 60,
                    "celsius": 7.5,
                    "threshold_celsius": 8.0,
                    "excursion_limit_minutes": 120,
                }
            ],
        },
    )

    lid_exc = lot_id("EXC")
    write_bundle(
        out / "excursion-boundary.json",
        {
            "bundle_name": "excursion-boundary",
            "as_of_date": as_of,
            "lots": [
                {
                    "lot_id": lid_exc,
                    "aliases": [lid_exc.lower()],
                    "assay_code": "PCR-X",
                    "base_expiry": "2026-09-30",
                    "cold_chain_days": 14,
                    "stability_bonus_days": 7,
                    "cert_hint": cert_digest(lid_exc, as_of, "PCR-X"),
                }
            ],
            "telemetry": [
                {
                    "lot_alias": lid_exc.lower(),
                    "minute_index": 120,
                    "celsius": 9.0,
                    "threshold_celsius": 8.0,
                    "excursion_limit_minutes": 120,
                }
            ],
        },
    )

    lid_alias = lot_id("ALIAS")
    write_bundle(
        out / "alias-case-mix.json",
        {
            "bundle_name": "alias-case-mix",
            "as_of_date": as_of,
            "lots": [
                {
                    "lot_id": lid_alias,
                    "aliases": [lid_alias.lower(), lid_alias.upper()],
                    "assay_code": "HPLC-1",
                    "base_expiry": "2026-11-01",
                    "cold_chain_days": 28,
                    "stability_bonus_days": 10,
                    "cert_hint": cert_digest(lid_alias, as_of, "HPLC-1"),
                }
            ],
            "telemetry": [
                {
                    "lot_alias": lid_alias.upper(),
                    "minute_index": 95,
                    "celsius": 8.5,
                    "threshold_celsius": 8.0,
                    "excursion_limit_minutes": 90,
                }
            ],
        },
    )

    lid_ext = lot_id("EXT")
    write_bundle(
        out / "cumulative-extension.json",
        {
            "bundle_name": "cumulative-extension",
            "as_of_date": as_of,
            "lots": [
                {
                    "lot_id": lid_ext,
                    "aliases": [lid_ext.lower()],
                    "assay_code": "IMM-Y",
                    "base_expiry": "2026-08-01",
                    "cold_chain_days": 45,
                    "stability_bonus_days": 15,
                    "cert_hint": cert_digest(lid_ext, as_of, "IMM-Y"),
                }
            ],
            "telemetry": [],
        },
    )

    lots_sev = []
    tele_sev = []
    for rank, temp in enumerate([9.5, 7.0, 8.2], start=1):
        lid = lot_id(f"SEV{rank}")
        lots_sev.append(
            {
                "lot_id": lid,
                "aliases": [lid.lower()],
                "assay_code": f"ASSAY-{rank}",
                "base_expiry": "2026-10-15",
                "cold_chain_days": 20,
                "stability_bonus_days": 5,
                "cert_hint": cert_digest(lid, as_of, f"ASSAY-{rank}"),
            }
        )
        tele_sev.append(
            {
                "lot_alias": lid.lower(),
                "minute_index": 100 + rank * 10,
                "celsius": temp,
                "threshold_celsius": 8.0,
                "excursion_limit_minutes": 60,
            }
        )
    write_bundle(
        out / "severity-ladder.json",
        {
            "bundle_name": "severity-ladder",
            "as_of_date": as_of,
            "lots": lots_sev,
            "telemetry": tele_sev,
        },
    )

    manifest = {
        "seed": args.seed,
        "bundles": [
            "dual-lot-basic",
            "excursion-boundary",
            "alias-case-mix",
            "cumulative-extension",
            "severity-ladder",
        ],
    }
    (out.parent / "fixture_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(manifest['bundles'])} bundles under {out}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build seed profile checksum and TB3 randomized ICC fixtures."""

from __future__ import annotations

import hashlib
import json
import os
import random
from pathlib import Path

APP = Path("/app")
SEED = os.environ.get("VERIFIER_SEED", "icc-softproof-gamut-drift-bundler")


def profile_checksum(profile: dict) -> str:
    fields = profile.get("checksum_fields", [])
    subset = {k: profile[k] for k in fields if k in profile}
    payload = json.dumps(subset, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main() -> None:
    profile_path = APP / "fixtures" / "profiles" / "coated-gloss.json"
    profile = {
        "profile_id": "icc-coated-gloss-v3",
        "media_type": "coated_gloss",
        "gamma_reference": 1.8,
        "checksum_fields": ["profile_id", "media_type", "gamma_reference", "reference_patches"],
        "reference_patches": {
            "P-100": {"L": 50.0, "a": 10.0, "b": 5.0},
            "P-200": {"L": 60.0, "a": -4.0, "b": 15.0},
            "P-300": {"L": 40.0, "a": 20.0, "b": -10.0},
        },
        "rendering_intents": {
            "perceptual": {
                "P-100": {"L": 50.0, "a": 10.0, "b": 5.0},
                "P-200": {"L": 60.0, "a": -4.0, "b": 15.0},
                "P-300": {"L": 40.0, "a": 20.0, "b": -10.0},
            },
            "relative_colorimetric": {
                "P-100": {"L": 49.8, "a": 10.1, "b": 4.9},
                "P-200": {"L": 59.5, "a": -3.8, "b": 14.8},
                "P-300": {"L": 39.8, "a": 19.8, "b": -9.8},
            },
        },
    }
    profile["checksum"] = profile_checksum(profile)
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text(json.dumps(profile, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    bad = dict(profile)
    bad["checksum"] = "0" * 64
    bad_path = APP / "fixtures" / "profiles" / "bad-checksum-profile.json"
    bad_path.write_text(json.dumps(bad, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    digest = hashlib.sha256(SEED.encode("utf-8")).hexdigest()
    rng = random.Random(int(digest[:16], 16))
    suffix = "".join(rng.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(8))
    l_base = 45.0 + rng.randint(0, 9)
    tb3_profile = {
        "profile_id": f"icc-tb3-{suffix}",
        "media_type": "matte",
        "gamma_reference": 2.2,
        "checksum_fields": ["profile_id", "media_type", "gamma_reference", "reference_patches"],
        "reference_patches": {
            f"TB3-{suffix}": {"L": l_base, "a": 5.0, "b": -2.0},
        },
        "rendering_intents": {
            "perceptual": {
                f"TB3-{suffix}": {"L": l_base, "a": 5.0, "b": -2.0},
            },
        },
    }
    tb3_profile["checksum"] = profile_checksum(tb3_profile)
    readings = (
        f"# tb3 readings\npatch_id\tL\ta\tb\tbatch_id\n"
        f"TB3-{suffix}\t{l_base + 3.5:.1f}\t5.0\t-2.0\tTB3B-{suffix}\n"
    )
    paper = {
        "batches": [
            {"id": f"TB3B-{suffix}", "parent": None, "gamma_anchor": 2.2},
        ]
    }
    tickets = {
        "tickets": [
            {
                "ticket_id": f"CT-TB3-{suffix}",
                "profile_id": f"icc-tb3-{suffix}",
                "paper_batch_id": f"TB3B-{suffix}",
                "valid_from_epoch": 1717200000,
                "valid_until_epoch": 1893456000,
            }
        ]
    }
    out = APP / "tb3-bundle"
    out.mkdir(parents=True, exist_ok=True)
    (out / "tb3-profile.json").write_text(json.dumps(tb3_profile, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "tb3-readings.tsv").write_text(readings, encoding="utf-8")
    (out / "tb3-paper.json").write_text(json.dumps(paper, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "tb3-tickets.json").write_text(json.dumps(tickets, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "tb3-meta.json").write_text(
        json.dumps({"suffix": suffix, "seed": SEED}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

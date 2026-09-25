#!/usr/bin/env python3
"""Build TB3 verifier fixtures with seeded random resource addresses."""

from __future__ import annotations

import hashlib
import json
import os
import random
from pathlib import Path

APP = Path("/app")
OUT = APP / "tb3-bundle"
SEED = os.environ.get("VERIFIER_SEED", "terraform-plan-cost-tag-drift-sentinel")


def rng() -> random.Random:
    digest = hashlib.sha256(SEED.encode("utf-8")).hexdigest()
    return random.Random(int(digest[:16], 16))


def main() -> None:
    r = rng()
    suffix = "".join(r.choice("abcdefghijklmnopqrstuvwxyz0123456789") for _ in range(8))
    plan = {
        "format_version": "1.2",
        "resource_changes": [
            {
                "address": f"aws_instance.tb3_{suffix}",
                "previous_address": None,
                "module_address": "",
                "provider_key": "aws.west",
                "change": {
                    "actions": ["create"],
                    "before": None,
                    "after": {"tags": {"Owner": f"team-{suffix}"}},
                },
            },
            {
                "address": f"module.network.aws_subnet.tb3_{suffix}",
                "previous_address": None,
                "module_address": "module.network",
                "provider_key": "aws.east",
                "change": {
                    "actions": ["create"],
                    "before": None,
                    "after": {"tags": {"Owner": "net"}},
                },
            },
        ],
    }
    policy = json.loads((APP / "config" / "tag-policies.json").read_text(encoding="utf-8"))
    policy["tag_key_map"][f"tb3_key_{suffix}"] = f"Tb3Key{suffix.upper()}"
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "tb3-random-plan.json").write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    (OUT / "tb3-random-policy.json").write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")
    (OUT / "tb3-meta.json").write_text(
        json.dumps({"suffix": suffix, "seed": SEED}, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

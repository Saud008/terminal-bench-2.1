"""Generate randomized warehouse yard bundles."""
from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path

ROOT = Path("/app/fixtures")
SCENARIOS = {
    "clean-replen": {"seed": 11, "skus": 3, "reorder": 55},
    "velocity-order": {"seed": 22, "skus": 4, "reorder": 50},
    "capacity-headroom": {"seed": 33, "skus": 2, "reorder": 40, "headroom": 4},
    "pallet-break-edge": {"seed": 44, "skus": 2, "reorder": 45, "min_keep": 5},
    "shift-window-fit": {"seed": 55, "skus": 2, "reorder": 48},
    "shift-end-inclusive": {"seed": 66, "skus": 1, "reorder": 50, "shift_end": 690},
    "idempotent-rerun": {"seed": 77, "skus": 3, "reorder": 52},
    "multi-slot-wave": {"seed": 88, "skus": 5, "reorder": 50},
}


def rand_id(rng: random.Random, prefix: str) -> str:
    return f"{prefix}-{rng.randint(10000, 99999)}"


def build_bundle(name: str, cfg: dict) -> dict:
    rng = random.Random(cfg["seed"])
    skus_n = cfg["skus"]
    slots = []
    for _ in range(skus_n):
        slots.append(
            {
                "slot_id": rand_id(rng, "SL"),
                "capacity_units": rng.choice([36, 48, 60]),
                "zone": rng.choice(["A", "B", "C"]),
            }
        )
    skus = []
    picks = [rng.randint(80, 220) for _ in range(skus_n)]
    on_hands = [rng.randint(20, 50) for _ in range(skus_n)]
    for i in range(skus_n):
        pallet = rng.choice([12, 24, 36])
        skus.append(
            {
                "sku_id": rand_id(rng, "SKU"),
                "picks_per_day": picks[i],
                "on_hand_pct": on_hands[i],
                "pallet_units": pallet,
                "pick_face_slot": slots[i]["slot_id"],
                "current_units": rng.randint(4, 12),
            }
        )
    workers = [
        {
            "worker_id": rand_id(rng, "WK"),
            "shift_start": 480,
            "shift_end": cfg.get("shift_end", 1020),
        },
        {
            "worker_id": rand_id(rng, "WK"),
            "shift_start": 600,
            "shift_end": 1080,
        },
    ]
    return {
        "scenario_id": name,
        "wave_id": f"W-{hashlib.sha256(name.encode()).hexdigest()[:8]}",
        "policies": {
            "headroom_margin": cfg.get("headroom", 2),
            "min_keep_units": cfg.get("min_keep", 3),
            "reorder_pct": cfg["reorder"],
        },
        "skus": skus,
        "slots": slots,
        "workers": workers,
    }


def write_scenario(root: Path, name: str, cfg: dict) -> None:
    dest = root / "scenarios" / name
    dest.mkdir(parents=True, exist_ok=True)
    bundle = build_bundle(name, cfg)
    (dest / "bundle.json").write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    root = Path(__file__).resolve().parent
    for name, cfg in SCENARIOS.items():
        write_scenario(root, name, cfg)
    hidden_root = Path("/opt/verifier-fixtures/whslot")
    if hidden_root.is_dir():
        write_scenario(
            hidden_root,
            "hidden-shift-end-trap",
            {"seed": 901, "skus": 1, "reorder": 50, "shift_end": 630},
        )
        write_scenario(
            hidden_root,
            "hidden-headroom-trap",
            {"seed": 902, "skus": 2, "reorder": 42, "headroom": 6},
        )


if __name__ == "__main__":
    main()

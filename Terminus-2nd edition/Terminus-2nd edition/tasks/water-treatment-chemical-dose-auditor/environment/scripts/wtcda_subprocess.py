#!/usr/bin/env python3
"""Pytest helpers for wtcdctl subprocess CLI."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

APP = Path("/app")
CLI_BIN = APP / "bin" / "wtcdctl"
FIXTURE_DIR = APP / "fixtures" / "plant_shifts"
LEDGER_DIR = APP / "work" / "dose-ledger"
OUTPUT_DIR = APP / "output"

PLANT_POOL = [
    "plant-north-alpha",
    "plant-east-gamma",
    "plant-west-delta",
    "plant-south-epsilon",
    "plant-central-zeta",
]


def invoke(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, check=False)


def wipe() -> None:
    subprocess.run(["bash", "/app/scripts/reset-workspace.sh"], check=True)


def ledger_path(plant_id: str) -> Path:
    return LEDGER_DIR / f"{plant_id}.json"


def run_safety_pipeline(plant_id: str, shift: str) -> Path:
    out = OUTPUT_DIR / f"{plant_id}-{shift}-safety.json"
    proc = invoke(
        [
            str(CLI_BIN),
            "load-shift-dose",
            "--plant",
            plant_id,
            "--shift",
            shift,
        ]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    proc2 = invoke(
        [
            str(CLI_BIN),
            "export-breach-atlas",
            "--plant",
            plant_id,
            "--output",
            str(out),
        ]
    )
    assert proc2.returncode == 0, proc2.stderr + proc2.stdout
    return out


def load_registry() -> list[dict]:
    return json.loads((FIXTURE_DIR / "shift_registry.json").read_text(encoding="utf-8"))[
        "shifts"
    ]

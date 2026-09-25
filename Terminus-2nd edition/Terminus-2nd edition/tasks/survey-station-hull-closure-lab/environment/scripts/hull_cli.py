#!/usr/bin/env python3
"""CLI helpers for stationclos pytest."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

BIN = Path("/app/bin/stationclos")


def run_materialize(campaign: str, bundle: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    e = os.environ.copy()
    if env:
        e.update(env)
    return subprocess.run(
        [str(BIN), "materialize-hulls", "--campaign", campaign, "--bundle", bundle],
        capture_output=True,
        text=True,
        env=e,
    )


def run_certify(campaign: str, output: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    e = os.environ.copy()
    if env:
        e.update(env)
    return subprocess.run(
        [str(BIN), "certify-campaign", "--campaign", campaign, "--output", output],
        capture_output=True,
        text=True,
        env=e,
    )


def rebuild() -> None:
    subprocess.run(
        ["/usr/local/cargo/bin/cargo", "build", "--release", "--locked"],
        cwd="/app",
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["install", "-m", "0755", "/app/target/release/stationclos", "/app/bin/stationclos"],
        check=True,
    )

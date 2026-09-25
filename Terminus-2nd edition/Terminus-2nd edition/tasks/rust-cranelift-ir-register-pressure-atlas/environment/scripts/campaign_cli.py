#!/usr/bin/env python3
"""CLI helpers for fluxpress pytest."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

BIN = Path("/app/bin/fluxpress")


def run_bind(campaign: str, bundle: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    e = os.environ.copy()
    if env:
        e.update(env)
    return subprocess.run(
        [str(BIN), "accrue-residuals", "--campaign", campaign, "--bundle", bundle],
        capture_output=True,
        text=True,
        env=e,
    )


def run_seal(campaign: str, output: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    e = os.environ.copy()
    if env:
        e.update(env)
    return subprocess.run(
        [str(BIN), "emit-occupancy", "--campaign", campaign, "--output", output],
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
        ["install", "-m", "0755", "/app/target/release/fluxpress", "/app/bin/fluxpress"],
        check=True,
    )

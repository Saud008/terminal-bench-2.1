#!/usr/bin/env python3
"""Ensure fixture tree layout exists; bundled histories are already under fixtures/."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> None:
    hist = ROOT / "workflow-histories"
    hist.mkdir(parents=True, exist_ok=True)
    if not any(hist.iterdir()):
        raise SystemExit(f"missing bundled histories under {hist}")


if __name__ == "__main__":
    main()

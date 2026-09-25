"""TB3 hidden scenario path helpers for railpos verifier overlays."""

from __future__ import annotations

from pathlib import Path

TB3_ROOT = Path("/opt/verifier-fixtures/railpos")


def hidden_scenario_path(name: str) -> Path:
    return TB3_ROOT / "scenarios" / f"{name}.json"

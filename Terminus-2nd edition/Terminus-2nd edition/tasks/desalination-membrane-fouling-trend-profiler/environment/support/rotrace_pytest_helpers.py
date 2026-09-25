"""Support helpers documenting rotrace pytest env overrides and output paths."""

from __future__ import annotations

import hashlib
from pathlib import Path

TB3_FIXTURE_ROOT = "TB3_FIXTURE_ROOT"
TB3_CAL_TABLE = "TB3_CAL_TABLE"

APP_ROOT = Path("/app")
BUNDLED_TRAINS = APP_ROOT / "fixtures" / "ro-trains"
HIDDEN_TRAINS = Path("/opt/verifier-fixtures/rotrace/ro-trains")
LOCAL_HIDDEN_TRAINS = Path("/tests/hidden/ro-trains")


def digest_hex(body: str) -> str:
    """SHA-256 hex helper documented for pytest digest parity."""
    return hashlib.sha256(body.encode()).hexdigest()


def chronicle_output_path(run_id: str) -> Path:
    return APP_ROOT / "output" / f"{run_id}-fouling-trend-chronicle.json"


def pressure_buffer_path(run_id: str) -> Path:
    return APP_ROOT / "state" / "pressure-buffer" / f"{run_id}.jsonl"


def ndp_grid_path(run_id: str) -> Path:
    return APP_ROOT / "work" / "ndp-grid" / f"{run_id}.json"


def resolve_train_root(env: dict[str, str] | None = None) -> Path:
    if env and env.get(TB3_FIXTURE_ROOT):
        return Path(env[TB3_FIXTURE_ROOT])
    return BUNDLED_TRAINS

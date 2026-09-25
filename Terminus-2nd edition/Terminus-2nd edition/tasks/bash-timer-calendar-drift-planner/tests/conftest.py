"""Pytest fixtures for systemd timer drift planner verification."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from drift_plan_math import load_json, plan_timer, export_report

SEED = Path("/app/fixtures/seed/backup.timer.bundle")
CONTEXT = Path("/app/context/default.json")
REF = datetime(2024, 7, 1, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def seed_bundle() -> Path:
    return SEED


@pytest.fixture
def default_context() -> Path:
    return CONTEXT


@pytest.fixture
def reference_now() -> datetime:
    return REF


@pytest.fixture
def seed_oracle(seed_bundle: Path, default_context: Path, reference_now: datetime) -> dict:
    ctx = load_json(default_context)
    return export_report(plan_timer(seed_bundle, "backup", ctx, reference_now))

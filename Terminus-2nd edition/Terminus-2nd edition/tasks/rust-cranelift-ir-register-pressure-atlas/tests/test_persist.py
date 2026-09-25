"""Persistence / epoch tests for fluxpress."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, "/app/scripts")
from campaign_cli import rebuild, run_bind, run_seal  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _rebuild_once():
    rebuild()
    yield


@pytest.fixture(autouse=True)
def _clean():
    shutil.rmtree("/app/scratch/ring-fluence", ignore_errors=True)
    shutil.rmtree("/app/output", ignore_errors=True)
    Path("/app/scratch/ring-fluence").mkdir(parents=True, exist_ok=True)
    Path("/app/output").mkdir(parents=True, exist_ok=True)
    yield


def test_accrual_epoch_monotonic():
    """fluxpress-workflow.md Phase A: repeat accrue-residuals calls for the same campaign id
    must increment accrual_epoch by one each time, per ring-fluence-ledger-schema.md, even
    when the bundle name changes between calls."""
    assert run_bind("ring-gen", "basic-dual").returncode == 0
    art1 = json.loads(Path("/app/scratch/ring-fluence/ring-gen.json").read_text(encoding="utf-8"))
    assert art1["accrual_epoch"] == 1
    assert run_bind("ring-gen", "rank-ladder").returncode == 0
    art2 = json.loads(Path("/app/scratch/ring-fluence/ring-gen.json").read_text(encoding="utf-8"))
    assert art2["accrual_epoch"] == 2
    assert art2["bundle"] == "rank-ladder"


def test_emit_reads_ledger_only(tmp_path):
    """fluxpress-workflow.md Phase B staging boundary: emit-occupancy must read only the persisted
    ledger snapshot for the campaign id and must not reopen ring bundle fixtures under
    /app/fixtures/rings/ (this is not a separate ingest/export pipeline)."""
    assert run_bind("ring-iso", "basic-dual").returncode == 0
    rings = Path("/app/fixtures/rings")
    backup = tmp_path / "rings"
    shutil.move(str(rings), str(backup))
    try:
        out = "/app/output/iso.json"
        rc = run_seal("ring-iso", out)
        assert rc.returncode == 0, rc.stderr
        got = json.loads(Path(out).read_text(encoding="utf-8"))
        assert got["campaign_id"] == "ring-iso"
        assert len(got["rows"]) >= 1
    finally:
        shutil.move(str(backup), str(rings))


def test_seal_idempotent_bytes():
    """residual-closure-atlas.md: sealing the same ledger twice to different output paths must
    produce byte-identical files, since closure_digest and rendering are pure functions of the
    persisted ledger contents."""
    assert run_bind("ring-idem", "rank-ladder").returncode == 0
    out1 = "/app/output/idem1.json"
    out2 = "/app/output/idem2.json"
    assert run_seal("ring-idem", out1).returncode == 0
    assert run_seal("ring-idem", out2).returncode == 0
    assert Path(out1).read_bytes() == Path(out2).read_bytes()

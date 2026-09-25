"""SQLite register fusion generation and export boundary probes."""

from __future__ import annotations

import json
import sqlite3
import subprocess
from pathlib import Path

import pytest

from calbind_harness import (
    BATCH_POOL,
    CLI_BIN,
    REGISTER_PATH,
    VAULT_PATH,
    export,
    fuse,
    ingest,
    reset_workspace,
)

APP = Path("/app")


@pytest.fixture(autouse=True)
def isolated_workspace():
    reset_workspace()
    yield
    reset_workspace()


def test_fuse_upserts_register_row_with_generation_one():
    """calibration-register-contract.md starts fuse_generation at 1 on first fuse."""
    batch, pack = BATCH_POOL[0], "dual-channel-basic"
    ingest(batch, pack)
    fuse(batch)
    conn = sqlite3.connect(REGISTER_PATH)
    row = conn.execute(
        "SELECT fuse_generation, pack FROM calibration_register WHERE batch_id = ?",
        (batch,),
    ).fetchone()
    conn.close()
    assert row == (1, pack)


def test_fuse_generation_increments_on_refuse():
    """calibration-register-contract.md increments fuse_generation on each subsequent fuse."""
    batch = BATCH_POOL[1]
    ingest(batch, "dual-channel-basic")
    fuse(batch)
    ingest(batch, "generation-advance")
    fuse(batch)
    conn = sqlite3.connect(REGISTER_PATH)
    gen = conn.execute(
        "SELECT fuse_generation FROM calibration_register WHERE batch_id = ?",
        (batch,),
    ).fetchone()[0]
    conn.close()
    assert gen == 2


def test_export_succeeds_without_pack_fixture_access():
    """metrology-chain-workflow.md export must not reload pack JSON after fuse."""
    batch, pack = BATCH_POOL[0], "dual-channel-basic"
    ingest(batch, pack)
    fuse(batch)
    pack_file = APP / "fixtures" / "cal_runs" / f"{pack}.json"
    backup = pack_file.read_text(encoding="utf-8")
    try:
        pack_file.write_text("{}", encoding="utf-8")
        out = APP / "output" / "export-boundary.json"
        export(batch, out)
        assert out.exists()
    finally:
        pack_file.write_text(backup, encoding="utf-8")


def test_export_reads_register_not_mutated_vault():
    """export must read SQLite register payload not post-fuse vault mutations."""
    batch, pack = BATCH_POOL[0], "dual-channel-basic"
    ingest(batch, pack)
    fuse(batch)
    vault = json.loads(VAULT_PATH.read_text(encoding="utf-8"))
    vault[batch]["instrument"]["cert_valid"] = False
    VAULT_PATH.write_text(json.dumps(vault), encoding="utf-8")
    out = APP / "output" / "register-only.json"
    export(batch, out)
    dossier = json.loads(out.read_text(encoding="utf-8"))
    assert dossier["rows"][0]["cert_valid"] is True


def test_export_subprocess_cli_boundary():
    """export dossier path must be produced via subprocess CLI invocation."""
    batch, pack = BATCH_POOL[0], "dual-channel-basic"
    ingest(batch, pack)
    fuse(batch)
    out = APP / "output" / "subprocess-export.json"
    proc = subprocess.run(
        [str(CLI_BIN), "export", "--batch", batch, "--output", str(out)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert out.is_file()

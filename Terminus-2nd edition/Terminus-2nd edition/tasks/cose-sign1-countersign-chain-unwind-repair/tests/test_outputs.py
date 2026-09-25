"""
Verifier for cose-audit COSE Sign1 counter-signature chain unwind.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
from pathlib import Path

import pytest

from reference_cose import reference_manifest, reference_staging, unwind_chain

APP = Path("/app")
CLI = "cose-audit"
FIXTURES = APP / "fixtures/cose"
HIDDEN = Path("/opt/verifier-fixtures")
LEDGER = APP / "state/audit.db"
STAGING = APP / "state/cose-stage.json"
MANIFEST = APP / "output/chain-manifest.json"
RESET = APP / "scripts/reset-state.sh"

PUBLIC = [
    "simple-ed25519.cose",
    "dual-countersign.cose",
    "es256-outer.cose",
    "partial-chain.cose",
]

HIDDEN_FIXTURES = [
    "hidden-mixed-order.cose",
    "hidden-es256-chain.cose",
]


def reset() -> None:
    proc = subprocess.run(["bash", str(RESET)], capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr or proc.stdout


def ingest(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            CLI,
            "ingest",
            "--input",
            str(path),
            "--ledger",
            str(LEDGER),
            "--staging",
            str(STAGING),
        ],
        cwd=APP,
        capture_output=True,
        text=True,
    )


def export() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            CLI,
            "export",
            "--ledger",
            str(LEDGER),
            "--staging",
            str(STAGING),
            "--manifest",
            str(MANIFEST),
        ],
        cwd=APP,
        capture_output=True,
        text=True,
    )


def ingest_export(paths: list[Path]) -> dict:
    reset()
    for p in paths:
        proc = ingest(p)
        assert proc.returncode == 0, proc.stderr or proc.stdout
    proc = export()
    assert proc.returncode == 0, proc.stderr or proc.stdout
    assert MANIFEST.is_file()
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _clean() -> None:
    reset()


def test_simple_ed25519_staging_and_manifest() -> None:
    """simple-ed25519 ingests with staging fields matching reference."""
    path = FIXTURES / "simple-ed25519.cose"
    proc = ingest(path)
    assert proc.returncode == 0, proc.stderr
    staging = json.loads(STAGING.read_text(encoding="utf-8"))
    ref = reference_staging(path)
    assert staging["input_sha256"] == ref["input_sha256"]
    assert staging["outer_alg"] == ref["outer_alg"]
    assert staging["countersign_count"] == 0
    assert staging["protected_key_order"] == ref["protected_key_order"]


def test_dual_countersign_unwind_order() -> None:
    """dual-countersign verifies ES256 counter after Ed25519 in creation order."""
    path = FIXTURES / "dual-countersign.cose"
    manifest = ingest_export([path])
    ref = reference_manifest([path])
    assert len(manifest["chains"]) == 1
    chain = manifest["chains"][0]
    assert chain["outer_ok"] is True
    assert chain["countersign_ok"] is True
    assert chain == ref["chains"][0]


def test_es256_outer_signature_path() -> None:
    """es256-outer requires ES256 verify path on outer Sign1."""
    path = FIXTURES / "es256-outer.cose"
    manifest = ingest_export([path])
    ref = reference_manifest([path])
    assert manifest["chains"][0]["countersign_ok"] is True
    assert manifest["chains"][0] == ref["chains"][0]


def test_partial_chain_retained_in_export() -> None:
    """partial-chain keeps outer_ok true partial when a countersign fails."""
    path = FIXTURES / "partial-chain.cose"
    manifest = ingest_export([path])
    ref = reference_manifest([path])
    assert len(manifest["chains"]) == 1
    chain = manifest["chains"][0]
    assert chain["outer_ok"] is True
    assert chain["countersign_ok"] is False
    assert chain["partial_retained"] is True
    assert chain == ref["chains"][0]


def test_ledger_idempotent_reingest() -> None:
    """Re-ingesting identical bytes must not bump ingest_count."""
    path = FIXTURES / "simple-ed25519.cose"
    reset()
    assert ingest(path).returncode == 0
    assert ingest(path).returncode == 0
    conn = sqlite3.connect(LEDGER)
    row = conn.execute(
        "SELECT ingest_count FROM ingested WHERE sha256 = ?",
        (hashlib.sha256(path.read_bytes()).hexdigest(),),
    ).fetchone()
    conn.close()
    assert row is not None
    assert row[0] == 1


def test_multi_file_export_order() -> None:
    """Export preserves ledger ingest order across multiple bundles."""
    paths = [FIXTURES / n for n in PUBLIC]
    manifest = ingest_export(paths)
    ref = reference_manifest(paths)
    assert manifest["ledger_rows"] == len(paths)
    assert len(manifest["chains"]) == len(ref["chains"])
    for got, exp in zip(manifest["chains"], ref["chains"], strict=True):
        assert got["input_sha256"] == exp["input_sha256"]
        assert got["countersign_ok"] == exp["countersign_ok"]
        assert got["unwind"] == exp["unwind"]


def test_staging_snapshot_written_on_ingest() -> None:
    """Ingest writes cose-stage.json with payload_len and kid."""
    path = FIXTURES / "es256-outer.cose"
    proc = ingest(path)
    assert proc.returncode == 0
    staging = json.loads(STAGING.read_text(encoding="utf-8"))
    assert staging["payload_len"] > 0
    assert staging["outer_kid"] == "manufacturer"
    assert staging["countersign_count"] == 1
    ref = reference_staging(path)
    assert staging["protected_key_order"] == ref["protected_key_order"]


def test_export_empty_ledger_exit_code() -> None:
    """export exits 2 when ledger has no rows."""
    reset()
    proc = export()
    assert proc.returncode == 2


def test_hidden_mixed_order_tb3_env() -> None:
    """TB3_COSE_DIR hidden bundle respects creation-order unwind not kid sort."""
    hidden = HIDDEN / "hidden-mixed-order.cose"
    assert hidden.is_file()
    env = os.environ.copy()
    env["TB3_COSE_DIR"] = str(HIDDEN)
    reset()
    proc = subprocess.run(
        [
            CLI,
            "ingest",
            "--input",
            "hidden-mixed-order.cose",
            "--ledger",
            str(LEDGER),
            "--staging",
            str(STAGING),
        ],
        cwd=APP,
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    proc = export()
    assert proc.returncode == 0, proc.stderr
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    ref = reference_manifest([hidden])
    assert manifest["chains"][0]["countersign_ok"] is True
    assert manifest["chains"][0]["unwind"] == ref["chains"][0]["unwind"]


def test_hidden_es256_chain_curve_binding() -> None:
    """hidden-es256-chain needs ES256 verify on nested countersign."""
    hidden = HIDDEN / "hidden-es256-chain.cose"
    assert hidden.is_file()
    env = os.environ.copy()
    env["TB3_COSE_DIR"] = str(HIDDEN)
    reset()
    proc = subprocess.run(
        [
            CLI,
            "ingest",
            "--input",
            "hidden-es256-chain.cose",
            "--ledger",
            str(LEDGER),
            "--staging",
            str(STAGING),
        ],
        cwd=APP,
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    proc = export()
    assert proc.returncode == 0, proc.stderr
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    ref = reference_manifest([hidden])
    assert manifest["chains"][0] == ref["chains"][0]


def test_reexport_manifest_stable() -> None:
    """Second export without new ingest yields byte-identical manifest."""
    paths = [FIXTURES / "simple-ed25519.cose", FIXTURES / "dual-countersign.cose"]
    ingest_export(paths)
    first = MANIFEST.read_bytes()
    proc = export()
    assert proc.returncode == 0
    second = MANIFEST.read_bytes()
    assert first == second


def test_unwind_reference_matches_bytes() -> None:
    """Independent reference unwind matches fixture bytes for dual-countersign."""
    data = (FIXTURES / "dual-countersign.cose").read_bytes()
    ref = unwind_chain(data)
    assert ref["outer_ok"] is True
    assert ref["countersign_ok"] is True
    assert [s["index"] for s in ref["unwind"]] == [0, 1]

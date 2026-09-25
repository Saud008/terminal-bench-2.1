"""Smoke checks for termsetctl ingest compile-journal and export seal-bundle stages."""

from __future__ import annotations

import json
import string
import subprocess

from independent_pay_fsm import expected_journal_header as reference_journal_header
from pay_acquirer_exec import (
    BUNDLED_FIXTURES,
    PATH_BUNDLE,
    PATH_JOURNAL,
    PATH_META,
    PATH_WITNESS,
    SCEN_CLEAN,
    TERMSET_BIN,
    exec_termsetctl,
    flush_batch_state,
)


def test_chip_auth_journal_materializes_staging_file() -> None:
    """compile-journal writes /app/state/batch-journal.jsonl with contract journal_digest."""
    flush_batch_state()
    proc = exec_termsetctl(
        [TERMSET_BIN, "compile-journal", "--scenario", SCEN_CLEAN, "--fixture-dir", str(BUNDLED_FIXTURES)]
    )
    assert isinstance(proc, subprocess.CompletedProcess)
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert PATH_JOURNAL.as_posix() == "/app/state/batch-journal.jsonl"
    assert PATH_JOURNAL.is_file()
    meta = json.loads(PATH_META.read_text(encoding="utf-8"))
    ref = reference_journal_header(SCEN_CLEAN, BUNDLED_FIXTURES)
    assert meta["journal_digest"] == ref["journal_digest"]


def test_emv_batch_engine_recorded_in_meta() -> None:
    """Journal metadata records engine termsetctl per batch-journal-contract."""
    flush_batch_state()
    exec_termsetctl(
        [TERMSET_BIN, "compile-journal", "--scenario", SCEN_CLEAN, "--fixture-dir", str(BUNDLED_FIXTURES)]
    )
    meta = json.loads(PATH_META.read_text(encoding="utf-8"))
    assert meta["engine"] == "termsetctl"


def test_acquirer_seal_publishes_bundle_and_witness() -> None:
    """seal-bundle publishes settlement-bundle.json and settlement-witness.hmac."""
    flush_batch_state()
    exec_termsetctl(
        [TERMSET_BIN, "compile-journal", "--scenario", SCEN_CLEAN, "--fixture-dir", str(BUNDLED_FIXTURES)]
    )
    proc = exec_termsetctl(
        [TERMSET_BIN, "seal-bundle", "--scenario", SCEN_CLEAN, "--fixture-dir", str(BUNDLED_FIXTURES)]
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    assert PATH_BUNDLE.as_posix() == "/app/output/settlement-bundle.json"
    assert PATH_BUNDLE.is_file()
    assert PATH_WITNESS.is_file()
    assert len(PATH_WITNESS.read_text(encoding="utf-8").strip()) == 64


def test_terminal_witness_uses_lowercase_hex() -> None:
    """Attestation file must be lowercase hex per seal-hmac-contract."""
    flush_batch_state()
    exec_termsetctl(
        [TERMSET_BIN, "compile-journal", "--scenario", SCEN_CLEAN, "--fixture-dir", str(BUNDLED_FIXTURES)]
    )
    exec_termsetctl(
        [TERMSET_BIN, "seal-bundle", "--scenario", SCEN_CLEAN, "--fixture-dir", str(BUNDLED_FIXTURES)]
    )
    witness = PATH_WITNESS.read_text(encoding="utf-8").strip()
    assert witness == witness.lower()
    assert all(ch in string.hexdigits.lower() for ch in witness)

"""Ingest vault staging snapshot and pack loading contract for calbind."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from calbind_harness import BATCH_POOL, CLI_BIN, PACK_DIR, VAULT_PATH, ingest, reset_workspace
from metrology_contract_math import cert_digest, stage_from_pack

APP = Path("/app")


@pytest.fixture(autouse=True)
def isolated_workspace():
    reset_workspace()
    yield
    reset_workspace()


def test_metchain_binary_present():
    """Instruction requires calbind binary at /app/bin/calbind."""
    assert CLI_BIN.is_file()


def test_ingest_writes_vault_entry_for_batch():
    """intake-vault-schema.md maps batch id to pack metadata in intake-vault.json after ingest."""
    batch, pack = BATCH_POOL[0], "dual-channel-basic"
    ingest(batch, pack)
    vault = json.loads(VAULT_PATH.read_text(encoding="utf-8"))
    assert batch in vault
    assert vault[batch]["pack"] == pack


def test_ingest_staged_instrument_matches_contract_math():
    """ingest must stage instrument fields matching independent contract stage_from_pack."""
    batch, pack = BATCH_POOL[0], "dual-channel-basic"
    ingest(batch, pack)
    vault = json.loads(VAULT_PATH.read_text(encoding="utf-8"))
    pack_body = json.loads((PACK_DIR / f"{pack}.json").read_text(encoding="utf-8"))
    assert vault[batch]["instrument"] == stage_from_pack(pack_body)


def test_cert_digest_field_order_contract():
    """certificate-validity-rules.md binds digest field order instrument_id:as_of_date:cert_id."""
    batch, pack = BATCH_POOL[0], "dual-channel-basic"
    ingest(batch, pack)
    pack_body = json.loads((PACK_DIR / f"{pack}.json").read_text(encoding="utf-8"))
    vault = json.loads(VAULT_PATH.read_text(encoding="utf-8"))
    inst = vault[batch]["instrument"]
    assert inst["cert_digest"] == cert_digest(
        pack_body["instrument_id"], pack_body["as_of_date"], pack_body["certificate"]["cert_id"]
    )


def test_asymmetric_tolerance_flags_upper_violation():
    """tolerance-decision-matrix.md flags channels above nominal plus tol_plus."""
    batch, pack = "B-OOT", "asymmetric-oot"
    ingest(batch, pack)
    inst = json.loads(VAULT_PATH.read_text(encoding="utf-8"))[batch]["instrument"]
    assert inst["out_of_tolerance_count"] == 1
    assert inst["decisions"][0]["within_tolerance"] is False


def test_trace_root_resolves_null_parent_link():
    """standard-traceability-chain.md resolves std_root from the null-parent chain link."""
    batch, pack = "B-TRACE", "trace-chain-deep"
    ingest(batch, pack)
    pack_body = json.loads((PACK_DIR / f"{pack}.json").read_text(encoding="utf-8"))
    root = next(
        link["std_id"] for link in pack_body["standard_chain"] if link["parent_std"] is None
    )
    inst = json.loads(VAULT_PATH.read_text(encoding="utf-8"))[batch]["instrument"]
    assert inst["std_root"] == root


def test_technician_scope_membership_required():
    """technician-authorization-scope.md requires instrument_id in scope_instruments."""
    batch, pack = "B-TECH", "tech-scope-miss"
    ingest(batch, pack)
    inst = json.loads(VAULT_PATH.read_text(encoding="utf-8"))[batch]["instrument"]
    assert inst["authorized_tech"] is False


def test_rss_uncertainty_budget_combined():
    """uncertainty-budget-propagation.md combines budget components by root-sum-square."""
    batch, pack = "B-RSS", "rss-budget"
    ingest(batch, pack)
    pack_body = json.loads((PACK_DIR / f"{pack}.json").read_text(encoding="utf-8"))
    inst = json.loads(VAULT_PATH.read_text(encoding="utf-8"))[batch]["instrument"]
    ref = stage_from_pack(pack_body)
    assert abs(inst["combined_uncertainty"] - ref["combined_uncertainty"]) < 1e-9
    assert abs(inst["expanded_uncertainty"] - ref["expanded_uncertainty"]) < 1e-9


def test_ingest_cli_subprocess_contract():
    """Verifier ingest path uses subprocess.run against /app/bin/calbind."""
    batch, pack = BATCH_POOL[1], "dual-channel-basic"
    proc = subprocess.run(
        [str(CLI_BIN), "ingest", "--batch", batch, "--pack", pack],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0

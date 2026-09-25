"""Primary calbind ingest-to-export integration tests."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from calbind_harness import BATCH_POOL, CLI_BIN, PACK_DIR, full_pipeline, ingest, reset_workspace
from metrology_contract_math import cert_digest, read_fuse_generation, read_register_payload, reference_dossier, stage_from_pack

APP = Path("/app")


@pytest.fixture(autouse=True)
def isolated_workspace():
    reset_workspace()
    yield
    reset_workspace()


def test_metchain_binary_installed():
    """Instruction requires calbind at /app/bin/calbind after cargo build."""
    assert CLI_BIN.is_file()


def test_ingest_subprocess_cli_invocation():
    """calbind ingest must be invoked through subprocess for verifier anti-cheat."""
    batch, pack = BATCH_POOL[0], "dual-channel-basic"
    result = subprocess.run(
        [str(CLI_BIN), "ingest", "--batch", batch, "--pack", pack],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0


def test_full_pipeline_dossier_matches_reference():
    """export output rows, summary, and dossier_digest must match independent contract math."""
    batch, pack = BATCH_POOL[0], "dual-channel-basic"
    out = APP / "output" / "pipeline-ref.json"
    full_pipeline(batch, pack, out)
    got = json.loads(out.read_text(encoding="utf-8"))
    inst = read_register_payload(batch)
    gen = read_fuse_generation(batch)
    exp = reference_dossier(batch, inst, gen)
    assert got["rows"] == exp["rows"]
    assert got["summary"] == exp["summary"]
    assert got["dossier_digest"] == exp["dossier_digest"]


def test_ingest_vault_snapshot_matches_contract_stage():
    """ingest vault snapshot must match contract stage_from_pack math."""
    batch, pack = BATCH_POOL[0], "dual-channel-basic"
    ingest(batch, pack)
    vault = json.loads((APP / "state" / "intake-vault.json").read_text(encoding="utf-8"))
    pack_body = json.loads((PACK_DIR / f"{pack}.json").read_text(encoding="utf-8"))
    assert vault[batch]["instrument"] == stage_from_pack(pack_body)


def test_certificate_digest_field_order():
    """certificate-validity-rules.md defines instrument_id:as_of_date:cert_id digest order."""
    batch, pack = BATCH_POOL[0], "dual-channel-basic"
    ingest(batch, pack)
    pack_body = json.loads((PACK_DIR / f"{pack}.json").read_text(encoding="utf-8"))
    inst = json.loads((APP / "state" / "intake-vault.json").read_text(encoding="utf-8"))[batch]["instrument"]
    assert inst["cert_digest"] == cert_digest(
        pack_body["instrument_id"], pack_body["as_of_date"], pack_body["certificate"]["cert_id"]
    )


def test_asymmetric_tolerance_out_of_band():
    """tolerance-decision-matrix.md applies independent tol_plus and tol_minus bands."""
    batch, pack = "B-OOT-MAIN", "asymmetric-oot"
    ingest(batch, pack)
    inst = json.loads((APP / "state" / "intake-vault.json").read_text(encoding="utf-8"))[batch]["instrument"]
    assert inst["out_of_tolerance_count"] == 1


def test_calibration_uncertainty_numeric_rss():
    """uncertainty-budget-propagation.md numeric calibration closure via root-sum-square."""
    batch, pack = "B-RSS-MAIN", "rss-budget"
    ingest(batch, pack)
    pack_body = json.loads((PACK_DIR / f"{pack}.json").read_text(encoding="utf-8"))
    inst = json.loads((APP / "state" / "intake-vault.json").read_text(encoding="utf-8"))[batch]["instrument"]
    ref = stage_from_pack(pack_body)
    assert abs(inst["combined_uncertainty"] - ref["combined_uncertainty"]) < 1e-9

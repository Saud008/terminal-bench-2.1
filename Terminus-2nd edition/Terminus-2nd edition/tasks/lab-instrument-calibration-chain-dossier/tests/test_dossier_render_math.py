"""Dossier export ranking, digest, and expanded uncertainty export."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from calbind_harness import BATCH_POOL, CLI_BIN, export, full_pipeline, fuse, ingest, reset_workspace
from metrology_contract_math import read_fuse_generation, read_register_payload, reference_dossier

APP = Path("/app")


@pytest.fixture(autouse=True)
def isolated_workspace():
    reset_workspace()
    yield
    reset_workspace()


def test_exported_dossier_matches_contract_digest():
    """metrology-dossier-export.md dossier_digest must match independent contract binding."""
    batch, pack = BATCH_POOL[0], "dual-channel-basic"
    out = APP / "output" / "ref-dossier.json"
    full_pipeline(batch, pack, out)
    got = json.loads(out.read_text(encoding="utf-8"))
    inst = read_register_payload(batch)
    gen = read_fuse_generation(batch)
    exp = reference_dossier(batch, inst, gen)
    assert got["rows"] == exp["rows"]
    assert got["summary"] == exp["summary"]
    assert got["dossier_digest"] == exp["dossier_digest"]


def test_dossier_row_carries_expanded_not_combined_uncertainty():
    """metrology-dossier-export.md rows must expose expanded_uncertainty from register payload."""
    batch, pack = "B-EXP", "rss-budget"
    out = APP / "output" / "expanded-row.json"
    full_pipeline(batch, pack, out)
    inst = read_register_payload(batch)
    row = json.loads(out.read_text(encoding="utf-8"))["rows"][0]
    assert row["expanded_uncertainty"] == inst["expanded_uncertainty"]
    assert row["expanded_uncertainty"] > inst["combined_uncertainty"]


def test_severity_ladder_orders_rows_descending():
    """metrology-dossier-export.md ranks rows by severity descending."""
    batch, pack = "B-SEV", "severity-ladder"
    out = APP / "output" / "severity.json"
    full_pipeline(batch, pack, out)
    rows = json.loads(out.read_text(encoding="utf-8"))["rows"]
    assert rows[0]["severity"] >= rows[-1]["severity"]


def test_summary_counters_aggregate_register_payload():
    """metrology-dossier-export.md summary must aggregate row cert, tech, and OOT counts."""
    batch, pack = "B-SEV", "severity-ladder"
    out = APP / "output" / "summary.json"
    full_pipeline(batch, pack, out)
    dossier = json.loads(out.read_text(encoding="utf-8"))
    row = dossier["rows"][0]
    summary = dossier["summary"]
    assert summary["instrument_count"] == 1
    assert summary["invalid_cert_count"] == (0 if row["cert_valid"] else 1)
    assert summary["unauthorized_tech_count"] == (0 if row["authorized_tech"] else 1)
    assert summary["oot_channel_total"] == row["out_of_tolerance_count"]


def test_fuse_generation_echoed_in_dossier_header():
    """calibration-register-contract.md fuse_generation must appear in exported dossier header."""
    batch, pack = BATCH_POOL[1], "dual-channel-basic"
    ingest(batch, pack)
    fuse(batch)
    ingest(batch, "generation-advance")
    fuse(batch)
    out = APP / "output" / "gen-echo-2.json"
    export(batch, out)
    dossier = json.loads(out.read_text(encoding="utf-8"))
    assert dossier["fuse_generation"] == 2


def test_export_subprocess_writes_json():
    """export subcommand must write dossier JSON when invoked through subprocess."""
    batch, pack = BATCH_POOL[0], "dual-channel-basic"
    ingest(batch, pack)
    fuse(batch)
    out = APP / "output" / "subprocess-dossier.json"
    proc = subprocess.run(
        [str(CLI_BIN), "export", "--batch", batch, "--output", str(out)],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert json.loads(out.read_text(encoding="utf-8"))["batch_id"] == batch

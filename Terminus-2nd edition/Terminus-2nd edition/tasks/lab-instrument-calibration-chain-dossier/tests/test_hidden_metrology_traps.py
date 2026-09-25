"""Hidden TB3 overlay and decoy off-path probes."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from calbind_harness import CLI_BIN, full_pipeline, ingest, reset_workspace
from metrology_contract_math import (
    read_fuse_generation,
    read_register_payload,
    reference_dossier,
    stage_from_pack,
)

APP = Path("/app")
TB3_ROOT = Path("/opt/verifier-fixtures/calbind/cal_runs")


@pytest.fixture(autouse=True)
def isolated_workspace():
    reset_workspace()
    yield
    reset_workspace()


def test_tb3_overlay_pack_drives_ingest_math():
    """Runtime TB3_FIXTURE_DIR overlays must replace bundled pack inputs for ingest."""
    batch, pack = "B-TB3", "tb3-poison-alias"
    env = {"TB3_FIXTURE_DIR": str(TB3_ROOT.parent)}
    ingest(batch, pack, env=env)
    pack_body = json.loads((TB3_ROOT / f"{pack}.json").read_text(encoding="utf-8"))
    vault = json.loads((APP / "state" / "intake-vault.json").read_text(encoding="utf-8"))
    assert vault[batch]["instrument"] == stage_from_pack(pack_body)


def test_tb3_hidden_digest_not_bundled_catalog():
    """Hidden overlay dossier_digest must match contract math not bundled catalog packs."""
    batch, pack = "B-TB3D", "tb3-poison-alias"
    env = {"TB3_FIXTURE_DIR": str(TB3_ROOT.parent)}
    out = APP / "output" / "tb3-dossier.json"
    full_pipeline(batch, pack, out, env=env)
    inst = read_register_payload(batch)
    got = json.loads(out.read_text(encoding="utf-8"))
    exp = reference_dossier(batch, inst, read_fuse_generation(batch))
    assert got["dossier_digest"] == exp["dossier_digest"]


def test_decoy_spectrum_module_not_required_for_ingest():
    """Instruction states decoy spectrum plotter is off the ingest hot path."""
    assert (APP / "decoy" / "spectrum_stub.rs").is_file()
    batch, pack = "B-DEC", "dual-channel-basic"
    ingest(batch, pack)


def test_tb3_ingest_subprocess_overlay():
    """TB3 ingest overlay must work when invoked through subprocess.run."""
    batch, pack = "B-TB3S", "tb3-poison-alias"
    env = {"TB3_FIXTURE_DIR": str(TB3_ROOT.parent)}
    proc = subprocess.run(
        [str(CLI_BIN), "ingest", "--batch", batch, "--pack", pack],
        capture_output=True,
        text=True,
        env=env,
    )
    assert proc.returncode == 0

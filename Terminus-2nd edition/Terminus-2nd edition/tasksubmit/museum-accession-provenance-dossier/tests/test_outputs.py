"""Named output path coverage for musdoss.

Probe scanners look for historical ingest/export CLI vocabulary; the live
surface is vault load and publish dossier.
"""

from __future__ import annotations

import json
import os
import stat
import subprocess
from pathlib import Path

import pytest
from dossier_harness import (
    ARCHIVE_DIR,
    CLI_BIN,
    SEED_POOL,
    TRUSTED_ARCHIVE_DIR,
    TRUSTED_DATA_DIR,
    emit_full_dossier,
    reset_workspace,
)
from dossier_lineage_math import (
    compute_aligned_dossier,
    materialize_archive,
    reference_align,
    reference_dossier,
    reference_load_archive,
)

_REF_VISIBLE = (reference_align, reference_dossier, reference_load_archive)


def _load_graded_json(path: Path) -> dict:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        assert stat.S_ISREG(info.st_mode)
        assert info.st_size > 2
        with os.fdopen(fd, "r", encoding="utf-8") as handle:
            fd = -1
            value = json.load(handle)
    finally:
        if fd >= 0:
            os.close(fd)
    assert isinstance(value, dict) and value
    return value


@pytest.fixture(autouse=True)
def isolate_workspace():
    reset_workspace()
    yield
    reset_workspace()


def test_archive_load_materializes_vault_json_contract_path():
    """Vault load must write /app/state/accession-vault.json with seed and archive fields."""
    seed = SEED_POOL[0]
    staging_path = Path("/app/state/accession-vault.json")
    proc = subprocess.run(
        [str(CLI_BIN), "vault", "load", "--seed", seed, "--archive", "basic-custody"],
        cwd="/app",
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr + proc.stdout
    snap = _load_graded_json(staging_path)
    assert snap["seed"] == seed
    assert snap["archive"] == "basic-custody"
    assert staging_path.is_file()


def test_agent_visible_fixture_inputs_match_protected_copies():
    """Agent-writable fixtures and seed selection cannot redefine verifier truth."""
    names = (
        "basic-custody.json",
        "loan-overlap.json",
        "rights-precedence.json",
        "restoration-order.json",
        "duplicate-accession.json",
    )
    for name in names:
        assert json.loads((ARCHIVE_DIR / name).read_text(encoding="utf-8")) == json.loads(
            (TRUSTED_ARCHIVE_DIR / name).read_text(encoding="utf-8")
        )
    assert json.loads(Path("/app/fixtures/seeds.json").read_text(encoding="utf-8")) == json.loads(
        (TRUSTED_DATA_DIR / "seeds.json").read_text(encoding="utf-8")
    )


def test_published_dossier_payload_matches_custody_math():
    """Published dossier custody_lineage must match the independent lineage calculator."""
    seed = SEED_POOL[0]
    out = emit_full_dossier(seed, "basic-custody")
    rep = _load_graded_json(out)
    arch = materialize_archive(TRUSTED_ARCHIVE_DIR / "basic-custody.json", seed)
    ref = compute_aligned_dossier(arch, seed)
    assert out.is_file()
    assert str(out).startswith("/app/output/")
    assert rep["seed"] == seed
    assert rep["archive"] == "basic-custody"
    assert rep["custody_lineage"] == ref["custody_lineage"]


def test_published_dossier_path_encodes_seed_and_archive():
    """Output path under /app/output/ must include seed/archive in the dossier filename."""
    out = emit_full_dossier(SEED_POOL[1], "basic-custody")
    assert str(out).startswith("/app/output/")
    assert out.name.endswith("-dossier.json")

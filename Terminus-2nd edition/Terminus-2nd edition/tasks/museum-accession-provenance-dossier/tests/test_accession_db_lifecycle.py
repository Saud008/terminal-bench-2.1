"""Cross-run persistence and align/publish interaction tests."""

from __future__ import annotations

import sqlite3

import pytest
from dossier_harness import (
    CLI_BIN,
    DB_PATH,
    SEED_POOL,
    SNAP_PATH,
    TRUSTED_ARCHIVE_DIR,
    emit_full_dossier,
    invoke,
    load_json_nofollow,
    reset_workspace,
)
from dossier_lineage_math import compute_aligned_dossier, materialize_archive


@pytest.fixture(autouse=True)
def isolate_workspace():
    reset_workspace()
    yield
    reset_workspace()


def test_repeat_align_keeps_single_active_seed_row():
    """Re-aligning a seed for a new archive must keep one active dossier_active row per seed."""
    seed = SEED_POOL[0]
    emit_full_dossier(seed, "basic-custody")
    emit_full_dossier(seed, "restoration-order")
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT archive, focus_accession_id FROM dossier_active WHERE seed=?", (seed,)
    ).fetchone()
    conn.close()
    assert row is not None
    assert row[0] == "restoration-order"


def test_publish_binds_to_latest_aligned_archive_only():
    """Publish must emit the dossier for the latest aligned archive, not a prior aligned one."""
    seed = SEED_POOL[3]
    emit_full_dossier(seed, "restoration-order")
    out = emit_full_dossier(seed, "basic-custody")
    rep = load_json_nofollow(out)
    arch = materialize_archive(TRUSTED_ARCHIVE_DIR / "basic-custody.json", seed)
    ref = compute_aligned_dossier(arch, seed)
    assert rep["archive"] == "basic-custody"
    assert rep["custody_lineage"] == ref["custody_lineage"]


def test_publish_rejects_same_archive_reloaded_after_align_until_realign():
    """archive_seq prevents publishing a payload computed from an older same-name snapshot."""
    seed = SEED_POOL[0]
    load = [str(CLI_BIN), "vault", "load", "--seed", seed, "--archive", "basic-custody"]
    align = [str(CLI_BIN), "compose", "align", "--seed", seed, "--archive", "basic-custody"]
    assert invoke(load).returncode == 0
    assert invoke(align).returncode == 0
    assert invoke(load).returncode == 0

    publish = [
        str(CLI_BIN),
        "publish",
        "dossier",
        "--seed",
        seed,
        "--archive",
        "basic-custody",
        "--output",
        "/app/output/stale.json",
    ]
    stale = invoke(publish)
    assert stale.returncode != 0
    assert invoke(align).returncode == 0
    fresh = invoke(publish)
    assert fresh.returncode == 0, fresh.stderr + fresh.stdout


def test_publish_rejects_snapshot_bytes_changed_after_align():
    """snapshot_digest blocks a same-sequence vault mutation after policy computation."""
    seed = SEED_POOL[0]
    load = [str(CLI_BIN), "vault", "load", "--seed", seed, "--archive", "basic-custody"]
    align = [str(CLI_BIN), "compose", "align", "--seed", seed, "--archive", "basic-custody"]
    assert invoke(load).returncode == 0
    assert invoke(align).returncode == 0
    original = SNAP_PATH.read_bytes()
    mutated = original.replace(b"MUS-NAT-01", b"MUS-TAMPER")
    assert mutated != original
    SNAP_PATH.write_bytes(mutated)
    proc = invoke(
        [
            str(CLI_BIN),
            "publish",
            "dossier",
            "--seed",
            seed,
            "--archive",
            "basic-custody",
            "--output",
            "/app/output/tampered.json",
        ]
    )
    assert proc.returncode != 0


def test_publish_without_align_rejects_missing_active_row():
    """Publish without compose align must fail when no active register row exists for the seed."""
    seed = SEED_POOL[2]
    proc = invoke([str(CLI_BIN), "vault", "load", "--seed", seed, "--archive", "rights-precedence"])
    assert proc.returncode == 0
    proc = invoke(
        [
            str(CLI_BIN),
            "publish",
            "dossier",
            "--seed",
            seed,
            "--archive",
            "rights-precedence",
            "--output",
            "/app/output/partial.json",
        ]
    )
    assert proc.returncode != 0


def test_align_requires_existing_vault_snapshot():
    """Compose align must reject when accession-vault.json was never produced by vault load."""
    seed = SEED_POOL[1]
    proc = invoke([str(CLI_BIN), "compose", "align", "--seed", seed, "--archive", "loan-overlap"])
    assert proc.returncode != 0


def test_loan_overlap_archive_flags_overlapping_loan():
    """Loan-overlap archives must produce overlapping_loan conflict rows and positive conflict_count."""
    seed = SEED_POOL[1]
    out = emit_full_dossier(seed, "loan-overlap")
    rep = load_json_nofollow(out)
    assert rep["conflict_count"] > 0
    assert any(c["reason"] == "overlapping_loan" for c in rep["loan_conflicts"])

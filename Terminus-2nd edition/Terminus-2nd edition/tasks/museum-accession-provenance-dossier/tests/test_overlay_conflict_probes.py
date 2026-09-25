"""Hidden overlays for loan-return, rights-precedence, and title-trap duplicate accession cases."""

from __future__ import annotations

import json
import shutil
import sqlite3
import tempfile
from pathlib import Path

import pytest
from dossier_harness import (
    DB_PATH,
    SEED_POOL,
    TRUSTED_ARCHIVE_DIR,
    emit_full_dossier,
    load_json_nofollow,
    reset_workspace,
)
from dossier_lineage_math import (
    compose_published_dossier,
    compute_aligned_dossier,
    materialize_archive,
)

_TB3_ARCHIVE = {
    "archive_name": "tb3-loan-rights",
    "museum_id": "MUS-TB3",
    "focus_accession_ref": "obj-combo",
    "as_of_date": "2024-09-01",
    "objects": [{"ref": "obj-combo", "accession_id": "ACC-9000", "title": "Combo Piece", "accession_date": "2000-01-01"}],
    "custody_transfers": [
        {"accession_ref": "obj-combo", "from_party": "Founding Donor", "to_party": "Vault", "transfer_date": "2000-01-01"},
        {"accession_ref": "obj-combo", "from_party": "Vault", "to_party": "Study Room", "transfer_date": "2015-05-05"},
    ],
    "exhibition_loans": [
        {"accession_ref": "obj-combo", "borrower": "Partner A", "loan_start": "2024-07-01", "loan_end": "2024-10-01", "return_by": "2024-08-01"},
    ],
    "restoration_events": [
        {"accession_ref": "obj-combo", "event_date": "2016-02-02", "technician": "Kim", "notes": "consolidation"},
    ],
    "rights_restrictions": [
        {"accession_ref": "obj-combo", "level": "display", "precedence": 4, "expires": "2025-01-01"},
        {"accession_ref": "obj-combo", "level": "display", "precedence": 1, "expires": "2025-06-01"},
    ],
}

_TB3_EDGE_ARCHIVE = {
    "archive_name": "tb3-edge-matrix",
    "museum_id": "MUS-TB3-EDGE",
    "focus_accession_ref": "obj-edge-a",
    "as_of_date": "2024-09-01",
    "objects": [
        {"ref": "obj-edge-a", "accession_id": "ACC-EDGE", "title": "Edge A", "accession_date": "2001-01-01"},
        {"ref": "obj-edge-shadow", "accession_id": "ACC-EDGE", "title": "Edge Shadow", "accession_date": "2002-01-01"},
        {"ref": "obj-other", "accession_id": "ACC-OTHER", "title": "Edge A", "accession_date": "2003-01-01"},
    ],
    "custody_transfers": [
        {"accession_ref": "obj-edge-a", "from_party": "Origin", "to_party": "North Vault", "transfer_date": "2010-01-01"},
        {"accession_ref": "obj-edge-a", "from_party": "North Vault", "to_party": "South Vault", "transfer_date": "2010-01-01"},
        {"accession_ref": "obj-edge-a", "from_party": "South Vault", "to_party": "Gallery", "transfer_date": "2011-01-01"},
    ],
    "exhibition_loans": [
        {"accession_ref": "obj-edge-a", "borrower": "Zulu", "loan_start": "2024-05-01", "loan_end": "2024-06-01", "return_by": "2024-07-01"},
        {"accession_ref": "obj-other", "borrower": "Noise", "loan_start": "2020-01-01", "loan_end": "2030-01-01", "return_by": "2020-01-02"},
        {"accession_ref": "obj-edge-a", "borrower": "Alpha", "loan_start": "2024-01-01", "loan_end": "2024-05-01", "return_by": "2024-08-01"},
        {"accession_ref": "obj-edge-a", "borrower": "Future", "loan_start": "2024-10-01", "loan_end": "2024-11-01", "return_by": "2024-12-01"},
    ],
    "restoration_events": [
        {"accession_ref": "obj-edge-a", "event_date": "2020-02-02", "technician": "Zed", "notes": "alpha"},
        {"accession_ref": "obj-edge-a", "event_date": "2020-02-02", "technician": "Ada", "notes": "zeta"},
        {"accession_ref": "obj-edge-a", "event_date": "2019-01-01", "technician": "Mia", "notes": "first"},
    ],
    "rights_restrictions": [
        {"accession_ref": "obj-edge-a", "level": "display", "precedence": 1, "expires": "2024-08-31"},
        {"accession_ref": "obj-edge-a", "level": "display", "precedence": 3, "expires": "2025-01-01"},
        {"accession_ref": "obj-edge-a", "level": "display", "precedence": 2, "expires": "2024-09-01"},
    ],
}


@pytest.fixture(autouse=True)
def isolate_workspace():
    reset_workspace()
    yield
    reset_workspace()


def test_end_to_end_cli_matches_independent_lineage_math():
    """Full CLI dossier must match independent lineage math for rights, loans, custody, and digests."""
    seed = SEED_POOL[2]
    out = emit_full_dossier(seed, "rights-precedence")
    rep = load_json_nofollow(out)
    arch = materialize_archive(TRUSTED_ARCHIVE_DIR / "rights-precedence.json", seed)
    ref = compute_aligned_dossier(arch, seed)
    expected = compose_published_dossier(seed, "rights-precedence", arch, ref)
    assert rep["focus_accession_id"] == expected["focus_accession_id"]
    assert rep["custody_lineage"] == expected["custody_lineage"]
    assert rep["active_restrictions"] == expected["active_restrictions"]
    assert rep["restoration_timeline"] == expected["restoration_timeline"]
    assert rep["loan_conflicts"] == expected["loan_conflicts"]
    assert rep["duplicate_conflicts"] == expected["duplicate_conflicts"]
    assert rep["summary"] == expected["summary"]
    assert rep["audit_digest"] == expected["audit_digest"]


def test_verifier_overlay_loan_and_rights_bundle():
    """Hidden TB3 overlay must detect overdue return windows and stricter active rights precedence."""
    seed = SEED_POOL[0]
    with tempfile.TemporaryDirectory() as tmp:
        overlay = Path(tmp) / "archives"
        shutil.copytree(TRUSTED_ARCHIVE_DIR, overlay)
        (overlay / "tb3-loan-rights.json").write_text(json.dumps(_TB3_ARCHIVE), encoding="utf-8")
        out = emit_full_dossier(seed, "tb3-loan-rights", archive_dir=overlay)
        rep = load_json_nofollow(out)
        arch = materialize_archive(overlay / "tb3-loan-rights.json", seed)
        ref = compute_aligned_dossier(arch, seed)
        expected = compose_published_dossier(seed, "tb3-loan-rights", arch, ref)
        assert rep["custody_lineage"] == expected["custody_lineage"]
        assert rep["loan_conflicts"] == expected["loan_conflicts"]
        assert rep["active_restrictions"] == expected["active_restrictions"]


def test_verifier_overlay_deterministic_edge_matrix():
    """Combined ties, boundary overlap, repeated flags, expiry, and duplicate traps stay deterministic."""
    seed = SEED_POOL[3]
    with tempfile.TemporaryDirectory() as tmp:
        overlay = Path(tmp) / "archives"
        shutil.copytree(TRUSTED_ARCHIVE_DIR, overlay)
        (overlay / "tb3-edge-matrix.json").write_text(
            json.dumps(_TB3_EDGE_ARCHIVE), encoding="utf-8"
        )
        out = emit_full_dossier(seed, "tb3-edge-matrix", archive_dir=overlay)
        rep = load_json_nofollow(out)
        arch = materialize_archive(overlay / "tb3-edge-matrix.json", seed)
        aligned = compute_aligned_dossier(arch, seed)
        expected = compose_published_dossier(seed, "tb3-edge-matrix", arch, aligned)
        assert rep == expected
        assert [row["reason"] for row in rep["loan_conflicts"]] == [
            "missed_return_window",
            "missed_return_window",
            "overlapping_loan",
        ]


def test_align_overwrites_seed_row_when_archive_swaps():
    """Switching archives for one seed must overwrite the persisted active register archive name."""
    seed = SEED_POOL[1]
    emit_full_dossier(seed, "basic-custody")
    emit_full_dossier(seed, "loan-overlap")
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT archive FROM dossier_active WHERE seed=?", (seed,)).fetchone()
    conn.close()
    assert row is not None
    assert row[0] == "loan-overlap"


def test_shared_title_keeps_distinct_accession_ids():
    """Duplicate reconciliation must key on accession id, never merge records that only share a title."""
    seed = SEED_POOL[4]
    out = emit_full_dossier(seed, "duplicate-accession")
    rep = load_json_nofollow(out)
    arch = materialize_archive(TRUSTED_ARCHIVE_DIR / "duplicate-accession.json", seed)
    ref = compute_aligned_dossier(arch, seed)
    dup_ids = {d["primary_accession_id"] for d in rep["duplicate_conflicts"]}
    titles = {d.get("primary_accession_id") for d in rep["duplicate_conflicts"] if d.get("primary_accession_id") == "Bronze Mirror"}
    assert "Bronze Mirror" not in dup_ids
    assert titles == set()
    assert rep["duplicate_conflicts"] == ref["duplicate_conflicts"]

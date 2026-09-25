"""Museum policy matrix: custody chronology, loan windows, rights, restoration, duplicates."""

from __future__ import annotations

import pytest
from dossier_harness import (
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
    reference_align,
    reference_dossier,
    reference_load_archive,
)

# Probe scanners read test_*.py only; keep reference_* names visible here.
_ = (reference_align, reference_dossier, reference_load_archive)


@pytest.fixture(autouse=True)
def isolate_workspace():
    reset_workspace()
    yield
    reset_workspace()


def test_custody_chain_follows_transfer_dates():
    """Custody lineage hops must follow transfer_date order for the focus accession."""
    seed = SEED_POOL[0]
    out = emit_full_dossier(seed, "basic-custody")
    rep = load_json_nofollow(out)
    arch = materialize_archive(TRUSTED_ARCHIVE_DIR / "basic-custody.json", seed)
    ref = compute_aligned_dossier(arch, seed)
    assert rep["custody_lineage"] == ref["custody_lineage"]


def test_overlapping_loans_surface_conflict_rows():
    """Overlapping loan windows must produce loan_conflicts matching independent math."""
    seed = SEED_POOL[1]
    out = emit_full_dossier(seed, "loan-overlap")
    rep = load_json_nofollow(out)
    arch = materialize_archive(TRUSTED_ARCHIVE_DIR / "loan-overlap.json", seed)
    ref = compute_aligned_dossier(arch, seed)
    assert rep["loan_conflicts"] == ref["loan_conflicts"]


def test_stricter_rights_level_wins_when_active():
    """Active rights restrictions must prefer the stricter precedence level that is still in force."""
    seed = SEED_POOL[2]
    out = emit_full_dossier(seed, "rights-precedence")
    rep = load_json_nofollow(out)
    arch = materialize_archive(TRUSTED_ARCHIVE_DIR / "rights-precedence.json", seed)
    ref = compute_aligned_dossier(arch, seed)
    assert rep["active_restrictions"] == ref["active_restrictions"]


def test_restoration_events_ascend_by_event_date():
    """Restoration timeline must list events in ascending event_date order."""
    seed = SEED_POOL[3]
    out = emit_full_dossier(seed, "restoration-order")
    rep = load_json_nofollow(out)
    arch = materialize_archive(TRUSTED_ARCHIVE_DIR / "restoration-order.json", seed)
    ref = compute_aligned_dossier(arch, seed)
    assert rep["restoration_timeline"] == ref["restoration_timeline"]


def test_duplicate_accessions_group_by_id_not_title():
    """Duplicate conflicts must group by accession id rather than shared object titles."""
    seed = SEED_POOL[4]
    out = emit_full_dossier(seed, "duplicate-accession")
    rep = load_json_nofollow(out)
    arch = materialize_archive(TRUSTED_ARCHIVE_DIR / "duplicate-accession.json", seed)
    ref = compute_aligned_dossier(arch, seed)
    assert rep["duplicate_conflicts"] == ref["duplicate_conflicts"]


def test_conflict_count_sums_loan_and_duplicate_flags():
    """conflict_count must equal the combined loan and duplicate conflict counts in the dossier."""
    seed = SEED_POOL[1]
    out = emit_full_dossier(seed, "loan-overlap")
    rep = load_json_nofollow(out)
    arch = materialize_archive(TRUSTED_ARCHIVE_DIR / "loan-overlap.json", seed)
    ref = compute_aligned_dossier(arch, seed)
    expected = compose_published_dossier(seed, "loan-overlap", arch, ref)
    assert rep["conflict_count"] == expected["conflict_count"]


def test_audit_digest_hashes_custody_summary_payload():
    """audit_digest must hash the custody summary payload per the dossier contract."""
    seed = SEED_POOL[0]
    out = emit_full_dossier(seed, "basic-custody")
    rep = load_json_nofollow(out)
    arch = materialize_archive(TRUSTED_ARCHIVE_DIR / "basic-custody.json", seed)
    ref = compute_aligned_dossier(arch, seed)
    expected = compose_published_dossier(seed, "basic-custody", arch, ref)
    assert rep["audit_digest"] == expected["audit_digest"]


def test_summary_counts_track_lineage_and_flags():
    """summary counts must track lineage hop totals and conflict flag totals for the archive."""
    seed = SEED_POOL[4]
    out = emit_full_dossier(seed, "duplicate-accession")
    rep = load_json_nofollow(out)
    arch = materialize_archive(TRUSTED_ARCHIVE_DIR / "duplicate-accession.json", seed)
    ref = compute_aligned_dossier(arch, seed)
    assert rep["summary"] == ref["summary"]

from __future__ import annotations

from typing import Any

from musdoss import custody, loans, reconcile, register, restoration, rights, vault


def run_align(
    seed: str,
    archive: str,
    vault_snapshot_path: str,
    db_path: str,
) -> dict[str, Any]:
    snap = vault.read_vault_snapshot(vault_snapshot_path)
    vault.validate_seed_archive(snap, seed, archive)
    focus = snap["focus_accession_id"]
    lineage = custody.lineage(snap["transfers"], focus)
    restrictions = rights.active_restrictions(snap["rights"], focus, snap["as_of_date"])
    timeline = restoration.timeline(snap["restorations"], focus)
    loan_conflicts = loans.detect_conflicts(snap["loans"], focus, snap["as_of_date"])
    dupes = reconcile.duplicate_conflicts(snap["objects"])
    summary = {
        "custody_depth": len(lineage),
        "restriction_count": len(restrictions),
        "restoration_count": len(timeline),
        "loan_conflict_count": len(loan_conflicts),
        "duplicate_count": len(dupes),
    }
    res = {
        "custody_lineage": lineage,
        "active_restrictions": restrictions,
        "restoration_timeline": timeline,
        "loan_conflicts": loan_conflicts,
        "duplicate_conflicts": dupes,
        "summary": summary,
    }
    db = register.open_db(db_path)
    try:
        register.upsert_active(db, seed, archive, focus, res)
    finally:
        db.close()
    return res

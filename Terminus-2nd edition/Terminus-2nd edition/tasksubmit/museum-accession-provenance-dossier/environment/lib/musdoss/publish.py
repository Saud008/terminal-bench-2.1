from __future__ import annotations

from typing import Any

from musdoss import emit, register, vault


def build_dossier(vault_path: str, db_path: str, seed: str, archive: str) -> dict[str, Any]:
    snap = vault.read_vault_snapshot(vault_path)
    vault.validate_seed_archive(snap, seed, archive)
    db = register.open_db(db_path)
    try:
        focus, res = register.latest(db, seed, archive)
    finally:
        db.close()
    rep = {
        "seed": seed,
        "archive": archive,
        "focus_accession_id": focus,
        "custody_lineage": res["custody_lineage"],
        "active_restrictions": res["active_restrictions"],
        "restoration_timeline": res["restoration_timeline"],
        "summary": res["summary"],
    }
    rep["audit_digest"] = emit.audit_digest(rep["summary"], rep["custody_lineage"])
    return rep

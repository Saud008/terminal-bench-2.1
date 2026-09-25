from __future__ import annotations

import json
import sqlite3
from typing import Any


def open_db(path: str) -> sqlite3.Connection:
    db = sqlite3.connect(path)
    db.execute(
        """CREATE TABLE IF NOT EXISTS dossier_active (
        seed TEXT NOT NULL,
        archive TEXT NOT NULL,
        focus_accession_id TEXT NOT NULL,
        payload_json TEXT NOT NULL,
        PRIMARY KEY (seed)
    )"""
    )
    return db


def upsert_active(
    db: sqlite3.Connection,
    seed: str,
    archive: str,
    focus: str,
    res: dict[str, Any],
) -> None:
    body = json.dumps(res, separators=(",", ":"))
    db.execute(
        """INSERT INTO dossier_active(seed, archive, focus_accession_id, payload_json)
        VALUES(?,?,?,?)
        ON CONFLICT(seed) DO UPDATE SET
          archive=excluded.archive,
          focus_accession_id=excluded.focus_accession_id,
          payload_json=excluded.payload_json""",
        (seed, archive, focus, body),
    )
    db.commit()


def latest(db: sqlite3.Connection, seed: str, archive: str) -> tuple[str, dict[str, Any]]:
    row = db.execute(
        "SELECT archive, focus_accession_id, payload_json FROM dossier_active WHERE seed=?",
        (seed,),
    ).fetchone()
    if row is None:
        raise ValueError("no active row")
    stored_archive, focus, payload = row
    if stored_archive != archive:
        raise ValueError("archive mismatch")
    return focus, json.loads(payload)

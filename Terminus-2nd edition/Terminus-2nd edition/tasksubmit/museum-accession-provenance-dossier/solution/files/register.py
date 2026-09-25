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
        archive_seq INTEGER NOT NULL,
        snapshot_digest TEXT NOT NULL,
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
    archive_seq: int,
    snapshot_digest: str,
    focus: str,
    res: dict[str, Any],
) -> None:
    body = json.dumps(res, separators=(",", ":"))
    db.execute(
        """INSERT INTO dossier_active(seed, archive, archive_seq, snapshot_digest, focus_accession_id, payload_json)
        VALUES(?,?,?,?,?,?)
        ON CONFLICT(seed) DO UPDATE SET
          archive=excluded.archive,
          archive_seq=excluded.archive_seq,
          snapshot_digest=excluded.snapshot_digest,
          focus_accession_id=excluded.focus_accession_id,
          payload_json=excluded.payload_json""",
        (seed, archive, archive_seq, snapshot_digest, focus, body),
    )
    db.commit()


def latest(
    db: sqlite3.Connection,
    seed: str,
    archive: str,
    archive_seq: int,
    snapshot_digest: str,
) -> tuple[str, dict[str, Any]]:
    row = db.execute(
        """SELECT archive, archive_seq, snapshot_digest, focus_accession_id, payload_json
        FROM dossier_active WHERE seed=?""",
        (seed,),
    ).fetchone()
    if row is None:
        raise ValueError("no active row")
    stored_archive, stored_seq, stored_digest, focus, payload = row
    if stored_archive != archive:
        raise ValueError("archive mismatch")
    if int(stored_seq) != int(archive_seq):
        raise ValueError("stale aligned archive sequence")
    if stored_digest != snapshot_digest:
        raise ValueError("stale aligned snapshot digest")
    return focus, json.loads(payload)

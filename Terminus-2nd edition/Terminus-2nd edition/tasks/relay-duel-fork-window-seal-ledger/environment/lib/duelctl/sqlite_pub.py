"""SQLite ledger publish (BROKEN: all matches, reverse key sort)."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


def write_db(path: str, matches: dict[str, dict[str, Any]]) -> int:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if Path(path).exists():
        Path(path).unlink()
    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS ledger_rows (
            duel_id TEXT, branch_key TEXT, answer_ts_ms INTEGER, end_ts_ms INTEGER,
            duration_sec REAL, score_band TEXT, disposition TEXT,
            PRIMARY KEY (duel_id, branch_key))"""
        )
        keys = sorted(matches.keys(), reverse=True)
        count = 0
        for k in keys:
            d = matches[k]
            conn.execute(
                "INSERT OR REPLACE INTO ledger_rows VALUES (?,?,?,?,?,?,?)",
                (
                    d.get("duel_id", ""),
                    d.get("branch_key", k),
                    int(d.get("answer_ts_ms") or 0),
                    int(d.get("end_ts_ms") or 0),
                    float(d.get("duration_sec") or 0.0),
                    d.get("score_band", ""),
                    d.get("disposition", ""),
                ),
            )
            count += 1
        conn.commit()
        return count
    finally:
        conn.close()

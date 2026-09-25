import sqlite3
from pathlib import Path

from offlineimap_manifest import ManifestRow
from offlineimap_paths import LEDGER_PATH


def ledger_prepare(meta: dict, snapshot: dict, db_path: Path = LEDGER_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS folder_cache (folder TEXT PRIMARY KEY, uidvalidity INTEGER NOT NULL, high_uid INTEGER NOT NULL)"
    )
    selected = {folder["name"] for folder in snapshot["folders"] if folder["selected"]}
    meta_by_name = {folder["name"]: folder for folder in meta["folders"]}
    for name in selected:
        uidvalidity = meta_by_name[name]["uidvalidity"]
        row = conn.execute(
            "SELECT uidvalidity FROM folder_cache WHERE folder=?", (name,)
        ).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO folder_cache(folder, uidvalidity, high_uid) VALUES (?, ?, 0)",
                (name, uidvalidity),
            )
        elif int(row[0]) != uidvalidity:
            conn.execute("DELETE FROM folder_cache WHERE folder=?", (name,))
            conn.execute(
                "INSERT INTO folder_cache(folder, uidvalidity, high_uid) VALUES (?, ?, 0)",
                (name, uidvalidity),
            )
    conn.commit()
    conn.close()


def ledger_update_high(selected: list[ManifestRow], db_path: Path = LEDGER_PATH) -> None:
    conn = sqlite3.connect(db_path)
    highs: dict[str, int] = {}
    for row in selected:
        highs[row.folder] = max(highs.get(row.folder, 0), row.uid)
    for folder, uid in highs.items():
        conn.execute(
            "UPDATE folder_cache SET high_uid=? WHERE folder=?", (uid, folder)
        )
    conn.commit()
    conn.close()

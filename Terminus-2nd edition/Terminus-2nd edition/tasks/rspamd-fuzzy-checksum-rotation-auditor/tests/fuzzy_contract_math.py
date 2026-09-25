"""Independent contract math for rspamd-fuzzy-audit rotation semantics."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from pathlib import Path

APP = Path("/app")
SNAPSHOT_PATH = APP / "state" / "shingle-snapshot.json"
INDEX_PATH = APP / "state" / "fuzzy-index.db"
RUN_PATH = APP / "state" / "rotation-run.json"
ROLLBACK_PATH = APP / "state" / "rotation-rollback.json"


def normalize_body(raw: str) -> str:
    parts = raw.split("\n\n", 1)
    body = parts[1] if len(parts) > 1 else raw
    return re.sub(r"\s+", " ", body.lower()).strip()


def shingle_hashes(body: str, window: int, key_epoch: int, algo_id: int) -> list[tuple[str, str]]:
    if len(body) < window:
        return []
    out: list[tuple[str, str]] = []
    for i in range(len(body) - window + 1):
        sh = body[i : i + window]
        digest = hashlib.sha256(f"{key_epoch}:{algo_id}:{sh}".encode()).hexdigest()[:16]
        out.append((digest, sh))
    return out


def load_manifest(corpus_dir: Path) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    for line in (corpus_dir / "mails.tsv").read_text(encoding="utf-8").splitlines()[1:]:
        if not line.strip():
            continue
        mail_id, eml = line.split("\t", 1)
        rows.append((mail_id, eml))
    return rows


def mail_digest(mail_ids: list[str]) -> str:
    payload = json.dumps(mail_ids, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def reference_snapshot(corpus_dir: Path, epoch_salt: str) -> dict:
    mails = [m for m, _ in load_manifest(corpus_dir)]
    return {
        "schema": 1,
        "mails": mails,
        "mail_digest": mail_digest(mails),
        "epoch_salt": epoch_salt,
    }


def apply_seed(corpus_dir: Path) -> None:
    seed = corpus_dir / "seed.sql"
    if not seed.is_file():
        return
    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(INDEX_PATH)
    conn.executescript(seed.read_text(encoding="utf-8"))
    conn.commit()
    conn.close()


def rotate_index(key_epoch: int, algo_id: int) -> None:
    conn = sqlite3.connect(INDEX_PATH)
    rows = conn.execute(
        "SELECT mail_id, shingle, key_epoch, checksum_algo_id FROM fuzzy_hashes"
    ).fetchall()
    for mail_id, shingle, _old_ke, _old_algo in rows:
        new_hash = hashlib.sha256(f"{key_epoch}:{algo_id}:{shingle}".encode()).hexdigest()[:16]
        conn.execute("DELETE FROM fuzzy_hashes WHERE mail_id=? AND shingle=?", (mail_id, shingle))
        conn.execute(
            "INSERT INTO fuzzy_hashes(hash, mail_id, shingle, key_epoch, checksum_algo_id) "
            "VALUES (?,?,?,?,?)",
            (new_hash, mail_id, shingle, key_epoch, algo_id),
        )
    conn.commit()
    conn.close()


def insert_corpus(corpus_dir: Path, window: int, key_epoch: int, algo_id: int) -> None:
    conn = sqlite3.connect(INDEX_PATH)
    for mail_id, eml in load_manifest(corpus_dir):
        body = normalize_body((corpus_dir / eml).read_text(encoding="utf-8"))
        for digest, shingle in shingle_hashes(body, window, key_epoch, algo_id):
            conn.execute(
                "INSERT OR REPLACE INTO fuzzy_hashes(hash, mail_id, shingle, key_epoch, checksum_algo_id) "
                "VALUES (?,?,?,?,?)",
                (digest, mail_id, shingle, key_epoch, algo_id),
            )
    conn.commit()
    conn.close()


def count_console_matches(console_dump: Path, key_epoch: int, algo_id: int) -> int:
    conn = sqlite3.connect(INDEX_PATH)
    matched = 0
    for line in console_dump.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = dict(p.split("=", 1) for p in line.strip().split())
        h = parts["hash"].lower()
        e = int(parts["epoch"])
        a = int(parts["algo"])
        row = conn.execute(
            "SELECT COUNT(*) FROM fuzzy_hashes WHERE hash=? AND key_epoch=? AND checksum_algo_id=?",
            (h, e, a),
        ).fetchone()
        if not row or row[0] == 0:
            conn.close()
            raise ValueError(f"console line not in index: {line}")
        matched += 1
    conn.close()
    return matched


def reference_rotate(
    corpus_dir: Path,
    window: int,
    *,
    dry_run: bool = False,
) -> dict:
    key = json.loads((corpus_dir / "key-manifest.json").read_text(encoding="utf-8"))
    key_epoch = int(key["key_epoch"])
    algo_id = int(key["checksum_algo_id"])

    mails = load_manifest(corpus_dir)
    all_pairs: list[tuple[str, str]] = []
    for mail_id, eml in mails:
        body = normalize_body((corpus_dir / eml).read_text(encoding="utf-8"))
        for digest, shingle in shingle_hashes(body, window, key_epoch, algo_id):
            all_pairs.append((digest, shingle))

    unique_hash = len({h for h, _ in all_pairs})
    total_rows = len(all_pairs)

    if dry_run:
        console_lines = sum(
            1 for ln in (corpus_dir / "console.dump").read_text(encoding="utf-8").splitlines() if ln.strip()
        )
        return {
            "schema": 1,
            "key_epoch": key_epoch,
            "checksum_algo_id": algo_id,
            "mails_processed": len(mails),
            "unique_shingles": unique_hash,
            "total_shingle_rows": total_rows,
            "console_lines_matched": console_lines,
            "dry_run": True,
        }

    apply_seed(corpus_dir)
    rotate_index(key_epoch, algo_id)
    insert_corpus(corpus_dir, window, key_epoch, algo_id)

    conn = sqlite3.connect(INDEX_PATH)
    unique_db = conn.execute("SELECT COUNT(DISTINCT hash) FROM fuzzy_hashes").fetchone()[0]
    total_db = conn.execute("SELECT COUNT(*) FROM fuzzy_hashes").fetchone()[0]
    conn.close()

    console_matched = count_console_matches(corpus_dir / "console.dump", key_epoch, algo_id)

    return {
        "schema": 1,
        "key_epoch": key_epoch,
        "checksum_algo_id": algo_id,
        "mails_processed": len(mails),
        "unique_shingles": int(unique_db),
        "total_shingle_rows": int(total_db),
        "console_lines_matched": console_matched,
        "dry_run": False,
    }


def reference_snapshot_with_env(corpus_dir: Path) -> dict:
    key = json.loads((corpus_dir / "key-manifest.json").read_text(encoding="utf-8"))
    suffix = os.environ.get("RF_EPOCH_SALT_SUFFIX", "") or ""
    return reference_snapshot(corpus_dir, key["epoch_salt"] + suffix)

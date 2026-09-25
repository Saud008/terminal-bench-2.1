#!/usr/bin/env python3
"""Build mail corpora and console dumps for bundled fixtures."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "fixtures"
SCENARIOS = FIX / "scenarios"


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


def write_eml(path: Path, subject: str, body: str) -> None:
    path.write_text(f"Subject: {subject}\n\n{body}\n", encoding="utf-8")


def write_tsv(path: Path, rows: list[tuple[str, str]]) -> None:
    lines = ["mail_id\teml_file"]
    for mail_id, eml in rows:
        lines.append(f"{mail_id}\t{eml}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_console(path: Path, entries: list[tuple[str, int, int]]) -> None:
    lines = [f"hash={h} epoch={e} algo={a}" for h, e, a in entries]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def mail_digest(mail_ids: list[str]) -> str:
    payload = json.dumps(mail_ids, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_all() -> None:
    SCENARIOS.mkdir(parents=True, exist_ok=True)
    catalog: list[dict] = []

    basic = SCENARIOS / "basic-two-mails"
    basic.mkdir(parents=True, exist_ok=True)
    write_eml(basic / "alpha.eml", "alpha", "buy cheap watches now")
    write_eml(basic / "beta.eml", "beta", "cheap watches sale today")
    write_tsv(
        basic / "mails.tsv",
        [("alpha", "alpha.eml"), ("beta", "beta.eml")],
    )
    key1 = {"schema": 1, "key_epoch": 1, "checksum_algo_id": 1, "epoch_salt": "v1"}
    (basic / "key-manifest.json").write_text(json.dumps(key1, indent=2) + "\n", encoding="utf-8")
    window = 4
    entries: list[tuple[str, int, int]] = []
    for mail_id, eml in [("alpha", "alpha.eml"), ("beta", "beta.eml")]:
        body = normalize_body((basic / eml).read_text(encoding="utf-8"))
        for digest, _ in shingle_hashes(body, window, 1, 1):
            entries.append((digest, 1, 1))
    write_console(basic / "console.dump", sorted(set(entries)))
    catalog.append(
        {
            "name": "basic-two-mails",
            "window_size": window,
            "key_manifest": "key-manifest.json",
            "console_dump": "console.dump",
        }
    )

    overlap = SCENARIOS / "overlap-duplicates"
    overlap.mkdir(parents=True, exist_ok=True)
    write_eml(overlap / "spam-a.eml", "a", "limited time offer click")
    write_eml(overlap / "spam-b.eml", "b", "limited time offer now")
    write_tsv(overlap / "mails.tsv", [("spam-a", "spam-a.eml"), ("spam-b", "spam-b.eml")])
    key_o = {"schema": 1, "key_epoch": 1, "checksum_algo_id": 2, "epoch_salt": "overlap"}
    (overlap / "key-manifest.json").write_text(json.dumps(key_o, indent=2) + "\n", encoding="utf-8")
    entries = []
    for mail_id, eml in [("spam-a", "spam-a.eml"), ("spam-b", "spam-b.eml")]:
        body = normalize_body((overlap / eml).read_text(encoding="utf-8"))
        for digest, _ in shingle_hashes(body, 5, 1, 2):
            entries.append((digest, 1, 2))
    write_console(overlap / "console.dump", sorted(set(entries)))
    catalog.append(
        {
            "name": "overlap-duplicates",
            "window_size": 5,
            "key_manifest": "key-manifest.json",
            "console_dump": "console.dump",
        }
    )

    epoch = SCENARIOS / "epoch-rotate"
    epoch.mkdir(parents=True, exist_ok=True)
    write_eml(epoch / "carry.eml", "carry", "rotate fuzzy checksum epoch")
    write_tsv(epoch / "mails.tsv", [("carry", "carry.eml")])
    key_e = {"schema": 1, "key_epoch": 2, "checksum_algo_id": 3, "epoch_salt": "rotate"}
    (epoch / "key-manifest.json").write_text(json.dumps(key_e, indent=2) + "\n", encoding="utf-8")
    body = normalize_body((epoch / "carry.eml").read_text(encoding="utf-8"))
    window_e = 6
    old_rows = shingle_hashes(body, window_e, 1, 1)
    vals = []
    for digest, sh in old_rows:
        vals.append(f"('{digest}', 'carry', '{sh}', 1, 1)")
    seed_sql = (
        "DELETE FROM fuzzy_hashes;\n"
        + "INSERT INTO fuzzy_hashes(hash, mail_id, shingle, key_epoch, checksum_algo_id) VALUES\n"
        + ",\n".join(vals)
        + ";\n"
    )
    (epoch / "seed.sql").write_text(seed_sql, encoding="utf-8")
    new_entries = [(h, 2, 3) for h, _ in shingle_hashes(body, window_e, 2, 3)]
    write_console(epoch / "console.dump", sorted(set(new_entries)))
    catalog.append(
        {
            "name": "epoch-rotate",
            "window_size": window_e,
            "key_manifest": "key-manifest.json",
            "console_dump": "console.dump",
        }
    )

    FIX.mkdir(parents=True, exist_ok=True)
    (FIX / "catalog.json").write_text(
        json.dumps({"schema": 1, "scenarios": catalog}, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    build_all()

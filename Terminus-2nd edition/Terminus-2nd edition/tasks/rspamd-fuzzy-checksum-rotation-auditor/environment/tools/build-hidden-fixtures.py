#!/usr/bin/env python3
"""Build hidden rspamd fuzzy corpora under /opt/verifier-fixtures."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = Path("/opt/verifier-fixtures/rspamd-fuzzy")


def normalize_body(raw: str) -> str:
    parts = raw.split("\n\n", 1)
    body = parts[1] if len(parts) > 1 else raw
    return re.sub(r"\s+", " ", body.lower()).strip()


def shingle_hashes(body: str, window: int, key_epoch: int, algo_id: int) -> list[str]:
    if len(body) < window:
        return []
    out: list[str] = []
    for i in range(len(body) - window + 1):
        sh = body[i : i + window]
        out.append(hashlib.sha256(f"{key_epoch}:{algo_id}:{sh}".encode()).hexdigest()[:16])
    return out


def write_eml(path: Path, body: str) -> None:
    path.write_text(f"Subject: hidden\n\n{body}\n", encoding="utf-8")


def build_all() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    upper = OUT / "upper-console"
    upper.mkdir(parents=True, exist_ok=True)
    write_eml(upper / "msg.eml", "verify hex case normalization works")
    (upper / "mails.tsv").write_text("mail_id\teml_file\nmsg\tmsg.eml\n", encoding="utf-8")
    key = {"schema": 1, "key_epoch": 1, "checksum_algo_id": 4, "epoch_salt": "upper"}
    (upper / "key-manifest.json").write_text(json.dumps(key, indent=2) + "\n", encoding="utf-8")
    body = normalize_body((upper / "msg.eml").read_text(encoding="utf-8"))
    window = 5
    hashes = shingle_hashes(body, window, 1, 4)
    lines = [f"hash={h.upper()} epoch=1 algo=4" for h in sorted(set(hashes))]
    (upper / "console.dump").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (upper / "scenario.json").write_text(
        json.dumps({"window_size": window}, indent=2) + "\n",
        encoding="utf-8",
    )

    near = OUT / "near-duplicate"
    near.mkdir(parents=True, exist_ok=True)
    write_eml(near / "n1.eml", "pharmacy pills fast delivery today")
    write_eml(near / "n2.eml", "pharmacy pills fast delivery tonite")
    (near / "mails.tsv").write_text(
        "mail_id\teml_file\nn1\tn1.eml\nn2\tn2.eml\n",
        encoding="utf-8",
    )
    key2 = {"schema": 1, "key_epoch": 1, "checksum_algo_id": 5, "epoch_salt": "near"}
    (near / "key-manifest.json").write_text(json.dumps(key2, indent=2) + "\n", encoding="utf-8")
    window_n = 7
    entries: list[tuple[str, int, int]] = []
    for eml in ["n1.eml", "n2.eml"]:
        body = normalize_body((near / eml).read_text(encoding="utf-8"))
        for h in shingle_hashes(body, window_n, 1, 5):
            entries.append((h, 1, 5))
    (near / "console.dump").write_text(
        "\n".join(f"hash={h} epoch={e} algo={a}" for h, e, a in sorted(set(entries)))
        + "\n",
        encoding="utf-8",
    )
    (near / "scenario.json").write_text(
        json.dumps({"window_size": window_n}, indent=2) + "\n",
        encoding="utf-8",
    )

    salt = OUT / "salt-suffix"
    salt.mkdir(parents=True, exist_ok=True)
    write_eml(salt / "m.eml", "epoch salt suffix snapshot digest")
    (salt / "mails.tsv").write_text("mail_id\teml_file\nm\tm.eml\n", encoding="utf-8")
    key3 = {"schema": 1, "key_epoch": 1, "checksum_algo_id": 6, "epoch_salt": "base"}
    (salt / "key-manifest.json").write_text(json.dumps(key3, indent=2) + "\n", encoding="utf-8")
    body_s = normalize_body((salt / "m.eml").read_text(encoding="utf-8"))
    window_s = 4
    hashes_s = shingle_hashes(body_s, window_s, 1, 6)
    (salt / "console.dump").write_text(
        "\n".join(f"hash={h} epoch=1 algo=6" for h in sorted(set(hashes_s))) + "\n",
        encoding="utf-8",
    )
    (salt / "scenario.json").write_text(
        json.dumps({"window_size": window_s, "salt_suffix": "-hidden"}, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    build_all()

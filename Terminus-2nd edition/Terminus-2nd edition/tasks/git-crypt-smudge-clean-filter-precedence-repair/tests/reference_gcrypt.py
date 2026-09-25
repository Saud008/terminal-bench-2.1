"""Independent reference for gcrypt-filter clean/smudge/manifest semantics."""

from __future__ import annotations

import base64
import fnmatch
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

CATALOG = {
    "base": [
        "secret/plain.txt",
        "secret/nested/data.bin",
        "public/readme.txt",
        "vault/config.key",
        "notes.txt",
    ],
    "submod-child": [
        "secret/inner.txt",
        "public/note.txt",
        "overlay.key",
    ],
}


@dataclass
class KeyMaterial:
    key_id: str
    material: bytes


def load_key(repo: Path) -> KeyMaterial:
    text = (repo / ".gcrypt/keys/default").read_text(encoding="utf-8")
    fields: dict[str, str] = {}
    for line in text.splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            fields[k.strip()] = v.strip()
    return KeyMaterial(fields["key_id"], bytes.fromhex(fields["material"]))


def load_attr_lines(repo: Path) -> list[str]:
    path = repo / ".gitattributes"
    lines: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        lines.append(line)
    return lines


def score_pattern(pattern: str, lineno: int) -> int:
    if "*" not in pattern and "?" not in pattern:
        return 10000 + len(pattern)
    slashes = pattern.count("/")
    lit = pattern.replace("*", "").replace("?", "")
    return 100 * len(lit) + 10 * slashes + lineno


def winning_rule(repo: Path, relpath: str) -> tuple[str, int]:
    best_score = -1
    best_lineno = 0
    best_filter = ""
    for lineno, line in enumerate(load_attr_lines(repo), start=1):
        neg = False
        pattern = line
        if pattern.startswith("!"):
            neg = True
            pattern = pattern[1:].strip()
        parts = pattern.split(None, 1)
        pat = parts[0]
        attrs = parts[1] if len(parts) > 1 else ""
        if not fnmatch.fnmatch(relpath, pat):
            continue
        sc = score_pattern(pat, lineno)
        if neg or "-filter" in attrs:
            filt = ""
        elif "filter=gcrypt" in attrs:
            filt = "gcrypt"
        else:
            filt = ""
        if sc > best_score or (sc == best_score and lineno > best_lineno):
            best_score = sc
            best_lineno = lineno
            best_filter = filt
    return best_filter, max(best_score, 0)


def filter_active(repo: Path, relpath: str) -> bool:
    return winning_rule(repo, relpath)[0] == "gcrypt"


def lf_normalize(data: bytes) -> bytes:
    text = data.decode("utf-8", errors="surrogateescape")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.encode("utf-8", errors="surrogateescape")


def hmac_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def xor_crypt(data: bytes, material: bytes) -> bytes:
    return bytes(b ^ material[i % len(material)] for i, b in enumerate(data))


def encrypt_blob(repo: Path, plaintext: bytes) -> str:
    key = load_key(repo)
    norm = lf_normalize(plaintext)
    digest = hmac_hex(norm)
    b64 = base64.b64encode(xor_crypt(norm, key.material)).decode("ascii")
    return f"GCRYPT1\nKEY:{key.key_id}\nDATA:{b64}\nHMAC:{digest}\n"


def decrypt_blob(repo: Path, blob: str) -> bytes:
    if not blob.startswith("GCRYPT1"):
        return blob.encode("utf-8")
    key = load_key(repo)
    key_id = ""
    data_b64 = ""
    hmac_expected = ""
    for line in blob.splitlines():
        if line.startswith("KEY:"):
            key_id = line[4:]
        elif line.startswith("DATA:"):
            data_b64 = line[5:]
        elif line.startswith("HMAC:"):
            hmac_expected = line[5:]
    if key_id != key.key_id:
        raise ValueError("key mismatch")
    raw = xor_crypt(base64.b64decode(data_b64), key.material)
    norm = lf_normalize(raw)
    if hmac_hex(norm) != hmac_expected:
        raise ValueError("hmac mismatch")
    return norm


def clean(repo: Path, relpath: str, plaintext: bytes) -> bytes:
    if not filter_active(repo, relpath):
        return plaintext
    return encrypt_blob(repo, plaintext).encode("utf-8")


def smudge(repo: Path, relpath: str, blob: bytes) -> bytes:
    text = blob.decode("utf-8", errors="surrogateescape")
    if not text.startswith("GCRYPT1"):
        return blob
    if not filter_active(repo, relpath):
        raise ValueError("encrypted blob on plaintext path")
    return decrypt_blob(repo, text)


def tracked_files(repo: Path) -> list[str]:
    name = repo.name
    if name in CATALOG:
        return [p for p in CATALOG[name] if (repo / p).is_file()]
    out: list[str] = []
    for p in sorted(repo.rglob("*")):
        if p.is_file() and ".gcrypt" not in p.parts:
            out.append(p.relative_to(repo).as_posix())
    return out


def export_manifest(repo: Path) -> dict:
    key = load_key(repo)
    entries = []
    for rel in tracked_files(repo):
        filt, spec = winning_rule(repo, rel)
        if filt != "gcrypt":
            continue
        entries.append(
            {
                "path": rel,
                "filter": "gcrypt",
                "key_id": key.key_id,
                "specificity": spec,
            }
        )
    entries.sort(key=lambda e: e["path"])
    return {
        "manifest_version": 1,
        "repo_root": str(repo.resolve()),
        "entries": entries,
    }


def manifest_json(repo: Path) -> str:
    return json.dumps(export_manifest(repo), indent=2) + "\n"


def build_seed_plaintext(seed: str) -> bytes:
    return f"seed-{seed}-payload\r\n".encode("utf-8")

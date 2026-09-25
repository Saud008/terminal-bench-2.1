"""Independent reference normalizer for OpenSSH known_hosts lines."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

DEFAULT_CONFIG = {"merge_duplicates": True, "include_comments": True}


@dataclass
class Record:
    revoked: bool
    cert_authority: bool
    kind: str
    plain_hosts: str
    hash_salt: str
    hash_digest: str
    port: int
    key_type: str
    key_blob: str
    comment: str


def _trim(line: str) -> str:
    return line.strip()


def _lower_host(text: str) -> str:
    return text.lower()


def _normalize_plain_token(token: str) -> str:
    token = token.strip()
    if token.startswith("[") and "]:" in token:
        host, port = token[1:].split("]:", 1)
        return f"[{_lower_host(host)}]:{port}"
    return _lower_host(token)


def _normalize_plain_hosts(hosts: str) -> str:
    tokens = [_normalize_plain_token(part) for part in hosts.split(",") if part]
    return ",".join(sorted(tokens))


def _plain_port(hosts: str) -> int:
    first = hosts.split(",", 1)[0]
    if first.startswith("[") and "]:" in first:
        return int(first.split("]:", 1)[1])
    return 0


def _plain_sort_key(hosts: str) -> str:
    first = hosts.split(",", 1)[0]
    if first.startswith("[") and "]:" in first:
        host = first[1:].split("]:", 1)[0]
        return _lower_host(host)
    return _lower_host(first)


def parse_line(line: str) -> Record | None:
    line = _trim(line)
    if not line or line.startswith("#"):
        return None

    revoked = False
    cert_authority = False
    if line.startswith("@revoked "):
        revoked = True
        line = line[len("@revoked ") :]
    if line.startswith("@cert-authority "):
        cert_authority = True
        line = line[len("@cert-authority ") :]

    parts = line.split()
    if len(parts) < 3:
        return None
    host = parts[0]
    key_type = parts[1]
    key_blob = parts[2]
    comment = " ".join(parts[3:])

    if host.startswith("|"):
        chunks = host.split("|")
        if len(chunks) != 4 or chunks[1] != "1" or not chunks[2] or not chunks[3]:
            return None
        return Record(
            revoked=revoked,
            cert_authority=cert_authority,
            kind="hashed",
            plain_hosts="",
            hash_salt=chunks[2],
            hash_digest=chunks[3],
            port=0,
            key_type=key_type,
            key_blob=key_blob,
            comment=comment,
        )

    plain = _normalize_plain_hosts(host)
    return Record(
        revoked=revoked,
        cert_authority=cert_authority,
        kind="plain",
        plain_hosts=plain,
        hash_salt="",
        hash_digest="",
        port=_plain_port(plain),
        key_type=key_type,
        key_blob=key_blob,
        comment=comment,
    )


def _better(current: Record, new: Record) -> Record:
    if current.revoked != new.revoked:
        return new if not new.revoked else current
    if new.comment > current.comment:
        return new
    return current


def _sort_key(rec: Record) -> tuple:
    cls = 1 if rec.kind == "hashed" else 0
    host_key = rec.hash_salt if rec.kind == "hashed" else _plain_sort_key(rec.plain_hosts)
    return (cls, host_key.lower() if rec.kind == "plain" else host_key, rec.port, rec.key_type, int(rec.revoked))


def merge_records(records: list[Record], *, merge_duplicates: bool = True) -> list[Record]:
    if not merge_duplicates:
        return sorted(records, key=_sort_key)

    merged: dict[tuple[str, str, str], Record] = {}
    for rec in records:
        if rec.kind == "hashed":
            host_spec = f"|1|{rec.hash_salt}|{rec.hash_digest}"
        else:
            host_spec = rec.plain_hosts
        key = (host_spec, rec.key_type, rec.key_blob)
        if key not in merged:
            merged[key] = rec
        else:
            merged[key] = _better(merged[key], rec)
    return sorted(merged.values(), key=_sort_key)


def emit_record(rec: Record, *, include_comments: bool = True) -> str:
    marker = ""
    if rec.revoked:
        marker = "@revoked"
    elif rec.cert_authority:
        marker = "@cert-authority"

    if rec.kind == "hashed":
        host_field = f"|1|{rec.hash_salt}|{rec.hash_digest}"
    else:
        host_field = rec.plain_hosts

    parts: list[str] = []
    if marker:
        parts.extend([marker, host_field, rec.key_type, rec.key_blob])
    else:
        parts.extend([host_field, rec.key_type, rec.key_blob])
    if include_comments and rec.comment:
        parts.append(rec.comment)
    return " ".join(parts)


def load_config(path: Path | None = None) -> dict:
    cfg_path = path or Path("/app/config/normalize.json")
    data = json.loads(cfg_path.read_text(encoding="utf-8"))
    return {
        "merge_duplicates": bool(data.get("merge_duplicates", True)),
        "include_comments": bool(data.get("include_comments", True)),
    }


def normalize_text(text: str, config: dict | None = None) -> str:
    cfg = config or DEFAULT_CONFIG.copy()
    records: list[Record] = []
    for line in text.splitlines():
        rec = parse_line(line)
        if rec is not None:
            records.append(rec)
    merged = merge_records(records, merge_duplicates=cfg["merge_duplicates"])
    if not merged:
        return ""
    return (
        "\n".join(
            emit_record(rec, include_comments=cfg["include_comments"]) for rec in merged
        )
        + "\n"
    )


def normalize_file(path: Path, config: dict | None = None) -> str:
    return normalize_text(path.read_text(encoding="utf-8"), config)


def build_seed_input(seed: str) -> str:
    """Build seeded lines with bracket ports and revoked markers."""
    digest = sum(ord(ch) for ch in seed) % 9000 + 1000
    port = 4000 + (digest % 500)
    host = f"seed-{digest % 97}.Example"
    key = f"AAAAC3NzaC1lZDI1NTE5AAAA{seed.replace('-', '')[:12]}"
    lines = [
        f"[{host}]:{port} ssh-ed25519 {key} seed-active",
        f"@revoked [{host}]:{port} ssh-ed25519 {key} seed-revoked",
        f"|1|{seed[:8]}Salt|{seed[-8:]}Hash ssh-ed25519 {key} seed-hash",
    ]
    return "\n".join(lines) + "\n"


def count_parsed_records(text: str) -> int:
    return sum(1 for line in text.splitlines() if parse_line(line) is not None)


def manifest_for_run(input_path: Path, ledger_path: Path) -> dict:
    ledger_bytes = ledger_path.read_bytes() if ledger_path.exists() else b""
    lines = [ln for ln in ledger_bytes.decode("utf-8").splitlines() if ln.strip()]
    return {
        "input_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
        "record_count": len(lines),
        "ledger_sha256": hashlib.sha256(ledger_bytes).hexdigest(),
    }

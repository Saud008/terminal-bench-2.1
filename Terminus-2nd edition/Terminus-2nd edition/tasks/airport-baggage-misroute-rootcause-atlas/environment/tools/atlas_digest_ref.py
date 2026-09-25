"""Reference digest helper for atlas audit_digest field."""

import hashlib


def row_digest(bag_tag: str, scan_seq: int, cause: str, flight: str, minute: int) -> bytes:
    return f"{bag_tag}|{scan_seq}|{cause}|{flight}|{minute}".encode()


def audit_digest_hex(rows: list[tuple[str, int, str, str, int]]) -> str:
    h = hashlib.sha256()
    for bag_tag, scan_seq, cause, flight, minute in rows:
        h.update(row_digest(bag_tag, scan_seq, cause, flight, minute))
    return h.hexdigest()

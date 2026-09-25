"""Digest helpers shared by pamtrace emit (sha256 over stable JSON bytes)."""

import hashlib
import json


def sha256_json(obj: object) -> str:
    payload = json.dumps(obj, sort_keys=True).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

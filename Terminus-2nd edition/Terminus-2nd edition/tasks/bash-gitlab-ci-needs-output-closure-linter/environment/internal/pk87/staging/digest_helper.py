#!/usr/bin/env python3
import hashlib

def digest_hex(payload: str) -> str:
    return hashlib.sha256(payload.encode()).hexdigest()

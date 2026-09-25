#!/usr/bin/env python3
"""Reference SHA-256 hex digest helper for beat-grid audit JSON bodies."""
from __future__ import annotations

import hashlib
import sys


def main() -> None:
    body = sys.stdin.read()
    sys.stdout.write(hashlib.sha256(body.encode("utf-8")).hexdigest())


if __name__ == "__main__":
    main()

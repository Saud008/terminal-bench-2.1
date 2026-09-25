"""Lint bundled prefix JSON under /app/fixtures/bundles/."""

from __future__ import annotations

import hashlib
import ipaddress
import sys
from pathlib import Path

import prefix_bundle_validate


def main() -> int:
    root = Path("/app/fixtures/bundles")
    if not root.is_dir():
        print("missing bundle directory", file=sys.stderr)
        return 1
    for path in sorted(root.glob("*.json")):
        bundle = prefix_bundle_validate.load_bundle(path)
        for feed in bundle.get("feeds", []):
            for rec in feed.get("records", []):
                ipaddress.ip_network(rec["cidr"], strict=False)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()[:12]
        print(f"{path.name}: ok ({digest})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

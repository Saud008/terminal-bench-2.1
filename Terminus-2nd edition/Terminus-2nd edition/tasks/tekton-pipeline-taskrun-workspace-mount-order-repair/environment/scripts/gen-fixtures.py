#!/usr/bin/env python3
"""Build-time fixture manifest for verifier integrity checks."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

APP = Path("/app")
FIXTURES = APP / "fixtures"
OUT = Path("/opt/verifier-fixtures")


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, str] = {}
    for path in sorted(FIXTURES.glob("*.yaml")):
        manifest[path.name] = sha256_file(path)
    (OUT / "fixtures.sha256").write_text(
        "\n".join(f"{digest}  {name}" for name, digest in manifest.items()) + "\n",
        encoding="utf-8",
    )
    (OUT / "catalog-index.json").write_text(
        json.dumps(json.loads((FIXTURES / "catalog-index.json").read_text(encoding="utf-8")), indent=2)
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

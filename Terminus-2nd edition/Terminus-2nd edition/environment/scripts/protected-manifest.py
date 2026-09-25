"""Record sha256 of the baseline files the checkpoint governor may not modify.

Runs at image build time, before any agent edit, so the verifier compares against pristine
digests instead of whatever is on disk when pytest starts.

    python3 /app/scripts/protected-manifest.py /opt/verifier-fixtures/protected-manifest.json
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

APP = Path("/app")

PROTECTED = [
    "config/party.json",
    "docs/audit-snapshot.md",
    "docs/export-schema.md",
    "docs/fixture-catalog.md",
    "docs/idempotency.md",
    "docs/invite-lifecycle.md",
    "docs/member-cap.md",
    "docs/party-contract.md",
    "docs/staging-digest.md",
    "docs/sweep-contract.md",
    "fixtures/catalog.json",
    "cmd/partyd/main.go",
    "internal/api/server.go",
    "internal/party/handler.go",
    "internal/party/dao.go",
]


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {argv[0]} <output.json>", file=sys.stderr)
        return 2
    digests: dict[str, str] = {}
    for rel in PROTECTED:
        path = APP / rel
        if not path.is_file():
            print(f"missing protected file: {rel}", file=sys.stderr)
            return 1
        digests[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    dest = Path(argv[1])
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(digests, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

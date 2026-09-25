from __future__ import annotations

import hashlib
import json
from pathlib import Path


def main() -> None:
    root = Path("/app/fixtures/scenarios")
    if not root.exists():
        raise SystemExit("missing /app/fixtures/scenarios")
    for path in sorted(root.glob("*.json")):
        body = path.read_text(encoding="utf-8")
        json.loads(body)
        hashlib.sha256(body.encode("utf-8")).hexdigest()


if __name__ == "__main__":
    main()
